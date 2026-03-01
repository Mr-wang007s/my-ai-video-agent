#!/usr/bin/env python3
"""分镜导出模块 — 从 script_breakdown.json 生成 Markdown 制作指南和 CSV Prompt 表格。

导出的文档供人类在 Gemini（图片）、可灵（视频）、剪映（合成）等平台手动操作时使用。
"""

import csv
import io
import json
import os
import re
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
PROJECTS_DIR = PROJECT_ROOT / "projects"


def _clean_video_prompt(prompt: str) -> str:
    """清理 video_prompt 中的 @ImageN 引用语法，转为可读文本。

    例: "@Image1 作为Elsa外观参考。@Image2 作为首帧，角色微微抬头"
    转: "[Elsa外观参考] 角色微微抬头"
    """
    if not prompt:
        return ""
    # 匹配 @ImageN 后面跟随的描述
    cleaned = re.sub(
        r'@Image\d+\s*作为(.+?)(?:。|$)',
        lambda m: f"[{m.group(1).strip()}] " if "首帧" not in m.group(1) else "",
        prompt
    )
    # 清理多余空格
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    # 如果清理后变空了，返回原文（去掉 @ImageN 前缀）
    if not cleaned:
        cleaned = re.sub(r'@Image\d+\s*', '', prompt).strip()
    return cleaned


def _parse_breakdown(project_dir: Path) -> dict:
    """读取并解析 script_breakdown.json。"""
    breakdown_path = project_dir / "script_breakdown.json"
    if not breakdown_path.exists():
        raise FileNotFoundError(f"script_breakdown.json not found in {project_dir}")
    with open(breakdown_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_characters(project_dir: Path) -> list:
    """读取 characters.json。"""
    chars_path = project_dir / "characters.json"
    if not chars_path.exists():
        return []
    with open(chars_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "characters" in data:
        return data["characters"]
    return []


def _load_project_config(project_dir: Path) -> dict:
    """尝试从项目目录名提取项目信息。"""
    dir_name = project_dir.name
    return {"project_id": dir_name, "name": dir_name}


def _iter_shots(breakdown: dict):
    """遍历 script_breakdown.json 的三层结构，yield 每个 shot 及其上下文。

    支持两种格式：
    - Schema 格式: breakdown["Sub-Script"]["Sub-Script 1"]["Scene Annotation"]["Scene"]["Scene 1"]...
    - 扁平格式: breakdown["Sub-Script 1"]["Scene Annotation"]["Scene 1"]... (legacy)

    Yields: (sub_script_key, sub_script_data, scene_key, scene_data, shot_key, shot_data)
    """
    # 获取 Sub-Script 容器：优先从 "Sub-Script" 键中取，否则从根层级取
    sub_scripts = breakdown.get("Sub-Script", {})
    if not sub_scripts:
        # Legacy/扁平格式：Sub-Script 键直接在根层级
        sub_scripts = {k: v for k, v in breakdown.items() if k.startswith("Sub-Script")}

    for key in sorted(sub_scripts.keys()):
        if not key.startswith("Sub-Script"):
            continue
        sub_data = sub_scripts[key]
        scene_annotation = sub_data.get("Scene Annotation", {})

        # 获取 Scene 容器：优先从 "Scene" 键中取，否则直接遍历
        scenes = scene_annotation.get("Scene", {})
        if not scenes:
            scenes = {k: v for k, v in scene_annotation.items() if k.startswith("Scene")}

        for sc_key in sorted(scenes.keys()):
            if not sc_key.startswith("Scene"):
                continue
            sc_data = scenes[sc_key]
            shot_annotation = sc_data.get("Shot Annotation", {})

            # 获取 Shot 容器：优先从 "Shot" 键中取，否则直接遍历
            shots = shot_annotation.get("Shot", {})
            if not shots:
                shots = {k: v for k, v in shot_annotation.items() if k.startswith("Shot")}

            for sh_key in sorted(shots.keys()):
                if not sh_key.startswith("Shot"):
                    continue
                sh_data = shots[sh_key]
                yield key, sub_data, sc_key, sc_data, sh_key, sh_data


def _format_characters_in_shot(involving: dict | list | str) -> str:
    """格式化 shot 中的角色信息。"""
    if isinstance(involving, dict):
        parts = []
        for name, bbox in involving.items():
            if isinstance(bbox, list) and len(bbox) == 4:
                parts.append(f"{name} [{','.join(f'{v:.2f}' for v in bbox)}]")
            else:
                parts.append(name)
        return "; ".join(parts)
    if isinstance(involving, list):
        return "; ".join(str(c) for c in involving)
    return str(involving) if involving else ""


def _make_shot_id(sub_key: str, scene_key: str, shot_key: str) -> str:
    """生成标准化 shot_id: S1_Sc1_Shot1。"""
    s_num = re.search(r'\d+', sub_key)
    sc_num = re.search(r'\d+', scene_key)
    sh_num = re.search(r'\d+', shot_key)
    return f"S{s_num.group() if s_num else '?'}_Sc{sc_num.group() if sc_num else '?'}_Shot{sh_num.group() if sh_num else '?'}"


# ═══════════════════════════════════════════════════════════════
# Markdown 导出
# ═══════════════════════════════════════════════════════════════

def export_markdown(project_id: str) -> dict:
    """导出 Markdown 格式的分镜制作指南。

    Returns:
        {"status": "success", "output_path": "...", "total_shots": N, "total_duration": Ns}
    """
    project_dir = PROJECTS_DIR / project_id
    if not project_dir.exists():
        return {"status": "failed", "error": f"Project directory not found: {project_id}"}

    try:
        breakdown = _parse_breakdown(project_dir)
    except FileNotFoundError as e:
        return {"status": "failed", "error": str(e)}

    characters = _load_characters(project_dir)
    info = _load_project_config(project_dir)

    lines = []
    total_shots = 0
    total_duration = 0

    # Header
    lines.append(f"# {info['name']} - 分镜制作指南\n")
    lines.append(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Character reference table
    if characters:
        lines.append("## 角色参考\n")
        lines.append("| 角色 | 外观描述 | 设计状态 | 参考图 |")
        lines.append("|------|---------|---------|--------|")
        for char in characters:
            name = char.get("name", "")
            appearance = char.get("appearance_description", char.get("tok_description", ""))
            if isinstance(appearance, dict):
                appearance = json.dumps(appearance, ensure_ascii=False)
            status = char.get("design_status", "")
            ref_path = f"character_list/{name}/best.png" if status == "designed" else "-"
            # Truncate long descriptions for table
            desc_short = (appearance[:80] + "...") if len(str(appearance)) > 80 else appearance
            lines.append(f"| {name} | {desc_short} | {status} | `{ref_path}` |")
        lines.append("")

    # Platform instructions
    lines.append("## 使用说明\n")
    lines.append("- **图片生成**: 复制「Gemini 图片 Prompt」到 Gemini 3 生成分镜关键帧图片")
    lines.append("- **视频生成**: 复制「可灵视频 Prompt」到可灵，上传关键帧图片进行图生视频")
    lines.append("- **音频参考**: 「音频描述」用于在剪映中配音/选择音效/BGM")
    lines.append("- **最终合成**: 在剪映中按镜头顺序排列视频，添加字幕和转场\n")
    lines.append("---\n")

    # Iterate through breakdown
    current_sub = None
    current_scene = None

    for sub_key, sub_data, sc_key, sc_data, sh_key, sh_data in _iter_shots(breakdown):
        # Sub-Script header
        if sub_key != current_sub:
            current_sub = sub_key
            sub_plot = sub_data.get("Plot", "")
            sub_plot_short = (sub_plot[:100] + "...") if len(sub_plot) > 100 else sub_plot
            lines.append(f"## {sub_key}: {sub_plot_short}\n")
            sub_chars = sub_data.get("Involving Characters", [])
            if sub_chars:
                if isinstance(sub_chars, list):
                    lines.append(f"**出场角色**: {', '.join(str(c) for c in sub_chars)}\n")

        # Scene header
        if sc_key != current_scene or sub_key != current_sub:
            current_scene = sc_key
            sc_plot = sc_data.get("Plot", sc_data.get("Description", ""))
            lines.append(f"### {sc_key}: {sc_plot[:80] if sc_plot else ''}\n")

        # Shot details
        total_shots += 1
        duration = sh_data.get("Duration", 5)
        total_duration += duration
        shot_id = _make_shot_id(sub_key, sc_key, sh_key)

        lines.append(f"#### {sh_key} (`{shot_id}`)\n")

        # Metadata table
        shot_type = sh_data.get("Shot Type", "")
        camera = sh_data.get("Camera Movement", "")
        transition = sh_data.get("Transition", sh_data.get("transition", "cut"))
        chars_str = _format_characters_in_shot(sh_data.get("Involving Characters", ""))

        lines.append("| 属性 | 值 |")
        lines.append("|------|---|")
        lines.append(f"| 镜头类型 | {shot_type} |")
        lines.append(f"| 运镜 | {camera} |")
        lines.append(f"| 时长 | {duration}s |")
        lines.append(f"| 转场 | {transition} |")
        if chars_str:
            lines.append(f"| 出场角色 | {chars_str} |")
        lines.append("")

        # Visual description
        visual_desc = sh_data.get("Plot/Visual Description", sh_data.get("Plot", ""))
        if visual_desc:
            lines.append(f"**视觉描述**: {visual_desc}\n")

        # Image prompt (for Gemini)
        image_prompt = sh_data.get("image_prompt", "")
        if image_prompt:
            lines.append("**Gemini 图片 Prompt** (复制到 Gemini):")
            lines.append(f"> {image_prompt}\n")

        # Video prompt (for Kling, cleaned)
        video_prompt = sh_data.get("video_prompt", "")
        if video_prompt:
            cleaned = _clean_video_prompt(video_prompt)
            lines.append("**可灵视频 Prompt** (复制到可灵):")
            lines.append(f"> {cleaned}\n")

        # Audio prompt (for CapCut reference)
        audio_prompt = sh_data.get("audio_prompt", "")
        if audio_prompt:
            lines.append("**音频描述** (剪映配音参考):")
            lines.append(f"> {audio_prompt}\n")

        # Subtitles
        subtitles = sh_data.get("Subtitles", sh_data.get("subtitles", ""))
        if subtitles:
            if isinstance(subtitles, list):
                subtitles = " / ".join(str(s) for s in subtitles)
            lines.append(f"**字幕**: {subtitles}\n")

        lines.append("---\n")

    # Summary footer
    lines.append(f"## 汇总\n")
    lines.append(f"- 总镜头数: {total_shots}")
    lines.append(f"- 预估总时长: {total_duration}s ({total_duration / 60:.1f}min)")
    lines.append(f"- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Write file
    exports_dir = project_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    output_path = exports_dir / "storyboard_guide.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Markdown exported: {output_path} ({total_shots} shots, {total_duration}s)")
    return {
        "status": "success",
        "output_path": str(output_path),
        "total_shots": total_shots,
        "total_duration": total_duration,
    }


# ═══════════════════════════════════════════════════════════════
# CSV 导出
# ═══════════════════════════════════════════════════════════════

def export_csv(project_id: str) -> dict:
    """导出 CSV 格式的分镜 Prompt 表格。

    Returns:
        {"status": "success", "output_path": "...", "total_shots": N}
    """
    project_dir = PROJECTS_DIR / project_id
    if not project_dir.exists():
        return {"status": "failed", "error": f"Project directory not found: {project_id}"}

    try:
        breakdown = _parse_breakdown(project_dir)
    except FileNotFoundError as e:
        return {"status": "failed", "error": str(e)}

    headers = [
        "shot_id", "sub_script", "scene", "shot_number",
        "shot_type", "camera_movement", "duration",
        "transition", "characters",
        "image_prompt", "video_prompt_clean", "audio_prompt",
        "subtitles", "visual_description",
    ]

    rows = []
    for sub_key, sub_data, sc_key, sc_data, sh_key, sh_data in _iter_shots(breakdown):
        shot_id = _make_shot_id(sub_key, sc_key, sh_key)
        sh_num = re.search(r'\d+', sh_key)

        subtitles = sh_data.get("Subtitles", sh_data.get("subtitles", ""))
        if isinstance(subtitles, list):
            subtitles = " | ".join(str(s) for s in subtitles)

        video_prompt_raw = sh_data.get("video_prompt", "")
        video_prompt_clean = _clean_video_prompt(video_prompt_raw)

        rows.append({
            "shot_id": shot_id,
            "sub_script": sub_key,
            "scene": sc_key,
            "shot_number": sh_num.group() if sh_num else "",
            "shot_type": sh_data.get("Shot Type", ""),
            "camera_movement": sh_data.get("Camera Movement", ""),
            "duration": sh_data.get("Duration", 5),
            "transition": sh_data.get("Transition", sh_data.get("transition", "cut")),
            "characters": _format_characters_in_shot(sh_data.get("Involving Characters", "")),
            "image_prompt": sh_data.get("image_prompt", ""),
            "video_prompt_clean": video_prompt_clean,
            "audio_prompt": sh_data.get("audio_prompt", ""),
            "subtitles": subtitles,
            "visual_description": sh_data.get("Plot/Visual Description", sh_data.get("Plot", "")),
        })

    # Write CSV with BOM for Excel compatibility
    exports_dir = project_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    output_path = exports_dir / "storyboard_prompts.csv"

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"CSV exported: {output_path} ({len(rows)} shots)")
    return {
        "status": "success",
        "output_path": str(output_path),
        "total_shots": len(rows),
    }


# ═══════════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="导出分镜制作指南")
    parser.add_argument("project_id", help="项目 ID")
    parser.add_argument("--format", choices=["markdown", "csv", "both"], default="both")
    args = parser.parse_args()

    results = []
    if args.format in ("markdown", "both"):
        results.append(export_markdown(args.project_id))
    if args.format in ("csv", "both"):
        results.append(export_csv(args.project_id))

    for r in results:
        print(json.dumps(r, ensure_ascii=False, indent=2))
