#!/usr/bin/env python3
"""MCP Server — 漫剧流水线工具（脚本分析 + 分镜导出）。

通过 MCP stdio 协议暴露以下工具组：
  - 项目管理：init_db, create_project, list_projects, get_project, update_status, get_project_summary
  - 剧本导入：import_script, get_script_stats, get_script_text
  - 角色管理：save_character, list_characters
  - 资产管理：save_asset, list_assets
  - 生成记录：log_generation
  - 分镜导出：export_storyboard_markdown, export_storyboard_csv

Usage (stdio):
    python scripts/mcp_server.py
"""

import json
import sys
from pathlib import Path

# 确保能导入同目录下的模块
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP

# 导入现有脚本的功能函数
from db_manager import (
    init_db, create_project, list_projects, get_project,
    update_project_status, save_script, save_storyboard,
    save_character, save_asset, list_assets, log_generation,
    get_project_summary, get_connection,
)
from import_script import import_script, get_stats, get_text
from export_storyboard import export_markdown, export_csv

# ─── 创建 MCP Server ───────────────────────────────────────────
mcp = FastMCP("manga-agent")

PROJECT_ROOT = Path(__file__).parent.parent
PROJECTS_DIR = PROJECT_ROOT / "projects"


# ═══════════════════════════════════════════════════════════════
# 项目管理工具
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
def project_init_db(force: bool = False) -> str:
    """初始化数据库表结构。force=True 时先删除所有表再重建。"""
    result = init_db(force=force)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def project_create(name: str, description: str = "", style: str = "manga", config: str = "{}") -> str:
    """创建新的漫剧项目。返回 project_id（格式：YYYYMMDD_HHMMSS_别名）。
    
    Args:
        name: 项目名称（如"冰雪奇缘2漫剧版"）
        description: 项目描述
        style: 视觉风格（manga/anime/realistic/watercolor）
        config: JSON 字符串，额外配置（如 {"target_duration": 120}）
    """
    data = {
        "name": name,
        "description": description,
        "style": style,
        "config": json.loads(config) if isinstance(config, str) else config
    }
    result = create_project(data)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def project_list() -> str:
    """列出所有项目。"""
    result = list_projects()
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
def project_get(project_id: str) -> str:
    """获取项目详情。"""
    result = get_project(project_id)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
def project_update_status(project_id: str, status: str) -> str:
    """更新项目状态。
    
    状态流转：draft → imported → characters_extracted → characters_designed
              → script_broken → exported
    """
    result = update_project_status(project_id, status)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def project_summary(project_id: str) -> str:
    """获取项目完整摘要（含角色/资产/生成记录统计）。"""
    result = get_project_summary(project_id)
    return json.dumps(result, ensure_ascii=False, default=str)


# ═══════════════════════════════════════════════════════════════
# 剧本导入工具
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
def script_import(project_id: str, script_path: str) -> str:
    """导入 .txt 剧本文件到项目目录。
    
    自动检测编码（UTF-8/GBK/GB2312等），复制到 projects/{project_id}/raw_script.txt，
    返回文本统计信息（字数、段落数、行数、中文字符数）。
    
    Args:
        project_id: 项目 ID
        script_path: 剧本 .txt 文件路径（绝对路径或相对于项目根目录）
    """
    result = import_script(project_id, script_path)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
def script_stats(project_id: str) -> str:
    """获取已导入剧本的统计信息。"""
    result = get_stats(project_id)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
def script_text(project_id: str, max_chars: int = 0) -> str:
    """读取已导入剧本的文本内容。
    
    Args:
        project_id: 项目 ID
        max_chars: 最大读取字符数（0=全部读取）
    """
    result = get_text(project_id, max_chars)
    return json.dumps(result, ensure_ascii=False, default=str)


# ═══════════════════════════════════════════════════════════════
# 角色管理工具
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
def character_save(project_id: str, name: str, description: str = "",
                   appearance: str = "{}", reference_images: str = "[]",
                   style_keywords: str = "[]") -> str:
    """保存/更新角色信息到数据库。
    
    Args:
        project_id: 项目 ID
        name: 角色名
        description: 角色描述
        appearance: JSON 字符串，外观特征（如 {"hair": "blonde", "dress": "blue"}）
        reference_images: JSON 字符串，参考图片路径列表
        style_keywords: JSON 字符串，风格关键词列表
    """
    data = {
        "project_id": project_id,
        "name": name,
        "description": description,
        "appearance": json.loads(appearance) if isinstance(appearance, str) else appearance,
        "reference_images": json.loads(reference_images) if isinstance(reference_images, str) else reference_images,
        "style_keywords": json.loads(style_keywords) if isinstance(style_keywords, str) else style_keywords,
    }
    result = save_character(data)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def character_list(project_id: str) -> str:
    """列出项目的所有角色。"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM characters WHERE project_id = ?", (project_id,)
    ).fetchall()
    conn.close()
    return json.dumps({
        "status": "success",
        "characters": [dict(r) for r in rows]
    }, ensure_ascii=False, default=str)


# ═══════════════════════════════════════════════════════════════
# 资产管理工具
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
def asset_save(project_id: str, asset_type: str, name: str, file_path: str,
               metadata: str = "{}") -> str:
    """保存资产记录到数据库。
    
    Args:
        project_id: 项目 ID
        asset_type: 资产类型（image/reference/export）
        name: 资产名称
        file_path: 文件路径
        metadata: JSON 字符串，额外元数据
    """
    data = {
        "project_id": project_id,
        "type": asset_type,
        "name": name,
        "file_path": file_path,
        "metadata": json.loads(metadata) if isinstance(metadata, str) else metadata,
    }
    result = save_asset(data)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def asset_list(project_id: str, asset_type: str = "") -> str:
    """列出项目的资产文件。
    
    Args:
        project_id: 项目 ID
        asset_type: 可选过滤（image/reference/export），为空则列出全部
    """
    result = list_assets(project_id, asset_type or None)
    return json.dumps(result, ensure_ascii=False, default=str)


# ═══════════════════════════════════════════════════════════════
# 生成记录工具
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
def generation_log(project_id: str, stage: str, status: str = "success",
                   error: str = "", cost: float = 0, duration_ms: int = 0) -> str:
    """记录一次操作日志。
    
    Args:
        project_id: 项目 ID
        stage: 阶段（import/extract/design/breakdown/export）
        status: 状态（pending/running/success/failed）
        error: 错误信息
        cost: 费用（元）
        duration_ms: 耗时（毫秒）
    """
    data = {
        "project_id": project_id,
        "stage": stage,
        "status": status,
        "error": error,
        "cost": cost,
        "duration_ms": duration_ms,
    }
    result = log_generation(data)
    return json.dumps(result, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
# 分镜导出工具
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
def export_storyboard_markdown(project_id: str) -> str:
    """导出分镜制作指南（Markdown 格式）。
    
    从 script_breakdown.json 和 characters.json 生成人类可读的制作指南，
    包含每个镜头的 Prompt（适用于 Gemini/可灵/剪映）、运镜、时长等信息。
    
    输出到 projects/{project_id}/exports/storyboard_guide.md
    """
    result = export_markdown(project_id)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def export_storyboard_csv(project_id: str) -> str:
    """导出分镜 Prompt 表格（CSV 格式）。
    
    从 script_breakdown.json 提取所有镜头的 Prompt，生成可批量复制的 CSV 表格。
    适用于在 Gemini、可灵、剪映等平台批量操作。
    
    输出到 projects/{project_id}/exports/storyboard_prompts.csv
    """
    result = export_csv(project_id)
    return json.dumps(result, ensure_ascii=False)


# ─── 启动入口 ──────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
