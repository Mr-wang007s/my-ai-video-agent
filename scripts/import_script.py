#!/usr/bin/env python3
"""剧本导入脚本 - 读取 .txt 剧本/小说文件，复制到项目目录，输出文本统计。

摘要提取和角色分析由 Agent 层（LLM）完成，本脚本仅负责：
1. 读取 .txt 文件（自动检测编码）
2. 复制到 projects/{project_id}/raw_script.txt
3. 输出文本统计信息（字数、段落数、行数）

Usage:
    python scripts/import_script.py --action import --project_id abc123 --script_path "path/to/novel.txt"
    python scripts/import_script.py --action stats --project_id abc123
"""

import argparse
import json
import os
import shutil
import sys
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
PROJECTS_DIR = PROJECT_ROOT / "projects"


def detect_encoding(file_path: str) -> str:
    """检测文件编码，依次尝试 UTF-8、GBK、GB2312、Latin-1。"""
    encodings = ["utf-8", "utf-8-sig", "gbk", "gb2312", "gb18030", "big5", "latin-1"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                f.read(4096)  # 试读前 4KB
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return "utf-8"  # fallback


def read_text_file(file_path: str) -> tuple[str, str]:
    """读取文本文件，返回 (内容, 编码)。"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    encoding = detect_encoding(file_path)
    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        content = f.read()

    logger.info(f"Read file: {file_path} (encoding={encoding}, length={len(content)})")
    return content, encoding


def compute_stats(text: str) -> dict:
    """计算文本统计信息。"""
    lines = text.split("\n")
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chars_no_space = len(text.replace(" ", "").replace("\n", "").replace("\r", ""))

    # 中文字符统计
    chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")

    return {
        "total_characters": len(text),
        "characters_no_whitespace": chars_no_space,
        "chinese_characters": chinese_chars,
        "lines": len(lines),
        "non_empty_lines": sum(1 for l in lines if l.strip()),
        "paragraphs": len(paragraphs),
        "words_estimate": chinese_chars + len(text.split()) if chinese_chars > 0 else len(text.split())
    }


def import_script(project_id: str, script_path: str) -> dict:
    """导入剧本文件到项目目录。"""
    # 验证项目目录
    project_dir = PROJECTS_DIR / project_id
    if not project_dir.exists():
        return {"status": "failed", "error": f"Project directory not found: {project_dir}"}

    # 验证源文件
    script_path = os.path.abspath(script_path)
    if not os.path.exists(script_path):
        return {"status": "failed", "error": f"Script file not found: {script_path}"}

    if not script_path.lower().endswith(".txt"):
        return {"status": "failed", "error": f"Only .txt files are supported, got: {script_path}"}

    try:
        # 读取文件
        content, encoding = read_text_file(script_path)

        if not content.strip():
            return {"status": "failed", "error": "Script file is empty"}

        # 复制到项目目录（统一 UTF-8 编码）
        raw_script_path = project_dir / "raw_script.txt"
        with open(raw_script_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Script copied to: {raw_script_path}")

        # 计算统计信息
        stats = compute_stats(content)

        result = {
            "status": "success",
            "project_id": project_id,
            "source_path": script_path,
            "source_encoding": encoding,
            "raw_script_path": str(raw_script_path),
            "relative_path": "raw_script.txt",
            "stats": stats,
            "imported_at": datetime.now().isoformat()
        }

        # 文本过长时发出提示
        if stats["characters_no_whitespace"] > 100000:
            result["warning"] = f"Large text ({stats['characters_no_whitespace']} chars). LLM summary extraction may need chunked processing."

        logger.info(f"Import complete: {stats['characters_no_whitespace']} chars, {stats['paragraphs']} paragraphs")
        return result

    except Exception as e:
        return {"status": "failed", "error": f"Import failed: {str(e)}"}


def get_stats(project_id: str) -> dict:
    """获取已导入剧本的统计信息。"""
    raw_script_path = PROJECTS_DIR / project_id / "raw_script.txt"
    if not raw_script_path.exists():
        return {"status": "failed", "error": f"No imported script found for project {project_id}"}

    content, encoding = read_text_file(str(raw_script_path))
    stats = compute_stats(content)

    return {
        "status": "success",
        "project_id": project_id,
        "raw_script_path": str(raw_script_path),
        "encoding": encoding,
        "stats": stats
    }


def get_text(project_id: str, max_chars: int = 0) -> dict:
    """读取已导入剧本的文本内容（可限制长度）。"""
    raw_script_path = PROJECTS_DIR / project_id / "raw_script.txt"
    if not raw_script_path.exists():
        return {"status": "failed", "error": f"No imported script found for project {project_id}"}

    content, _ = read_text_file(str(raw_script_path))
    total_length = len(content)

    if max_chars > 0 and len(content) > max_chars:
        content = content[:max_chars]
        truncated = True
    else:
        truncated = False

    return {
        "status": "success",
        "project_id": project_id,
        "text": content,
        "truncated": truncated,
        "total_length": total_length
    }


ACTIONS = {
    "import": lambda args: import_script(args.project_id, args.script_path),
    "stats": lambda args: get_stats(args.project_id),
    "text": lambda args: get_text(args.project_id, args.max_chars or 0),
}


def main():
    parser = argparse.ArgumentParser(description="剧本导入工具")
    parser.add_argument("--action", type=str, required=True, choices=list(ACTIONS.keys()),
                        help="操作类型: import=导入剧本, stats=查看统计, text=读取文本")
    parser.add_argument("--project_id", type=str, required=True, help="项目 ID")
    parser.add_argument("--script_path", type=str, default="", help="剧本文件路径（import 时必填）")
    parser.add_argument("--max_chars", type=int, default=0, help="最大读取字符数（text 时可选，0=全部）")
    args = parser.parse_args()

    if args.action == "import" and not args.script_path:
        parser.error("--script_path is required for import action")

    result = ACTIONS[args.action](args)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
