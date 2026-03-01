#!/usr/bin/env python3
"""MovieAgent MCP Server — 统一暴露所有漫剧流水线工具。

通过 MCP stdio 协议暴露以下工具组：
  - 项目管理：init_db, create_project, list_projects, get_project, update_status, get_project_summary
  - 剧本导入：import_script, get_script_stats, get_script_text
  - 角色管理：save_character, list_characters
  - 资产管理：save_asset, list_assets
  - 生成记录：log_generation
  - 图像生成：generate_image
  - 视频生成：generate_video (Seedance 2.0)
  - TTS 语音：generate_speech
  - 视频合成：compose_video, replace_audio, add_subtitles

Usage (stdio):
    python scripts/mcp_server.py
"""

import json
import os
import sys
from pathlib import Path

# 确保能导入同目录下的模块
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from mcp.server.fastmcp import FastMCP

# 导入现有脚本的功能函数
from db_manager import (
    init_db, create_project, list_projects, get_project,
    update_project_status, save_script, save_storyboard,
    save_character, save_asset, list_assets, log_generation,
    get_project_summary, get_connection,
    upsert_shot_status, list_shots_by_status, batch_init_shots, check_daily_quota
)
from import_script import import_script, get_stats, get_text
from image_generate import generate_image_dalle, generate_image_sd, generate_image_seedream
from seedance_generate import generate_video as _seedance_generate
from tts_generate import generate_speech_volc, generate_speech_azure
from video_compose import compose_full, concat_videos, replace_audio, overlay_bgm, add_subtitles

# ─── 创建 MCP Server ───────────────────────────────────────────
mcp = FastMCP("manga-agent")

PROJECT_ROOT = Path(__file__).parent.parent
PROJECTS_DIR = PROJECT_ROOT / "projects"


def _check_quota(api_type: str, limit: int) -> dict:
    """检查今日 API 调用次数。"""
    try:
        conn = get_connection()
        today = __import__('datetime').date.today().isoformat()
        count = conn.execute(
            "SELECT COUNT(*) FROM generations WHERE stage = ? AND created_at >= ? AND status != 'failed'",
            (api_type, today)
        ).fetchone()[0]
        conn.close()
        return {"allowed": count < limit, "used": count, "limit": limit}
    except Exception:
        return {"allowed": True, "used": 0, "limit": limit}


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
        config: JSON 字符串，额外配置（如 {"target_duration": 120, "resolution": "1080p"}）
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
    
    状态流转：draft → imported → characters_extracted → characters_designing 
              → script_broken → generating → generated → composing → completed
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
        asset_type: 资产类型（image/video/audio）
        name: 资产名称（如 "S1_Sc1_Shot1"）
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
        asset_type: 可选过滤（image/video/audio），为空则列出全部
    """
    result = list_assets(project_id, asset_type or None)
    return json.dumps(result, ensure_ascii=False, default=str)


# ═══════════════════════════════════════════════════════════════
# 生成记录工具
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
def generation_log(project_id: str, stage: str, status: str = "success",
                   error: str = "", cost: float = 0, duration_ms: int = 0) -> str:
    """记录一次生成操作日志。
    
    Args:
        project_id: 项目 ID
        stage: 阶段（import/extract/design/breakdown/image/video/tts/compose）
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
# 图像生成工具
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
def image_generate(prompt: str, output_dir: str, engine: str = "seedream",
                   size: str = "1024x1024", quality: str = "standard",
                   style: str = "vivid") -> str:
    """调用 Seedream 5.0 / DALL-E / Stable Diffusion 生成图像。
    
    Args:
        prompt: 图像生成提示词（英文）
        output_dir: 输出目录
        engine: 引擎（seedream/dalle/sd，默认 seedream）
        size: 图像尺寸（1024x1024, 1024x1792, 1792x1024 等）
        quality: 质量（standard/hd，仅 DALL-E）
        style: 风格（vivid/natural，仅 DALL-E）
    """
    # 成本预检查
    quota = _check_quota("image", 100)
    if not quota["allowed"]:
        return json.dumps({"status": "failed", "error": f"Image daily quota exceeded: {quota['used']}/{quota['limit']}"}, ensure_ascii=False)

    if engine == "sd":
        result = generate_image_sd(prompt, output_dir, size=size)
    elif engine == "dalle":
        result = generate_image_dalle(prompt, output_dir, size=size, quality=quality, style=style)
    else:
        seedream_size = size if size != "1024x1024" else "2K"
        result = generate_image_seedream(prompt, output_dir, size=seedream_size)
    return json.dumps(result, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
# Seedance 2.0 视频生成工具
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
def video_generate(prompt: str, output_dir: str, mode: str = "t2v",
                   duration: int = 5, resolution: str = "1080p",
                   ratio: str = "16:9", audio_prompt: str = "",
                   image_paths: str = "[]", shot_id: str = "") -> str:
    """调用 Seedance 2.0 API 生成视频（音视频联合生成）。
    
    Args:
        prompt: 视频生成提示词
        output_dir: 输出目录
        mode: 模式（t2v=文生视频, i2v=图生视频, multimodal=多模态）
        duration: 时长秒数（4/5/10/15）
        resolution: 分辨率（720p/1080p）
        ratio: 宽高比（16:9/9:16/1:1/4:3/3:4/21:9）
        audio_prompt: 音频提示词（启用音视频联合生成）
        image_paths: JSON 字符串，图片路径列表（i2v/multimodal 模式必填）
        shot_id: 镜头 ID，用于输出文件命名
    """
    # 成本预检查
    quota = _check_quota("video", 50)
    if not quota["allowed"]:
        return json.dumps({"status": "failed", "error": f"Seedance daily quota exceeded: {quota['used']}/{quota['limit']}"}, ensure_ascii=False)

    config = {
        "mode": mode,
        "prompt": prompt,
        "output_dir": output_dir,
        "duration": duration,
        "resolution": resolution,
        "ratio": ratio,
        "shot_id": shot_id,
    }
    if audio_prompt:
        config["audio_prompt"] = audio_prompt
    paths = json.loads(image_paths) if isinstance(image_paths, str) else image_paths
    if paths:
        config["image_paths"] = paths

    result = _seedance_generate(config)
    return json.dumps(result, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
# TTS 语音合成工具
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
def speech_generate(text: str, voice: str, output_dir: str,
                    engine: str = "volc", speed: float = 1.0,
                    emotion: str = "neutral") -> str:
    """调用 TTS API 将文本转为语音。
    
    Args:
        text: 要合成的文本
        voice: 音色（narrator/young_male/young_female/mature_male/mature_female/child）
        output_dir: 输出目录
        engine: TTS 引擎（volc=火山引擎, azure=Azure TTS）
        speed: 语速（0.5~2.0）
        emotion: 情绪（neutral/happy/sad/angry/fearful/surprised/disgusted）
    """
    kwargs = {"speed": speed, "emotion": emotion}
    if engine == "azure":
        result = generate_speech_azure(text, voice, output_dir, **kwargs)
    else:
        result = generate_speech_volc(text, voice, output_dir, **kwargs)
    return json.dumps(result, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
# 视频合成工具
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
def video_compose(config_json: str) -> str:
    """视频合成（拼接+BGM+字幕）。
    
    Args:
        config_json: JSON 字符串，完整配置。支持三种模式：
            - compose: {"mode": "compose", "segments": [{"video_path": "..."}], "output_path": "...", "subtitles": [...]}
            - replace_audio: {"mode": "replace_audio", "video_path": "...", "audio_path": "...", "output_path": "..."}
            - overlay_bgm: {"mode": "overlay_bgm", "video_path": "...", "bgm_path": "...", "output_path": "...", "bgm_volume": 0.3}
    """
    config = json.loads(config_json) if isinstance(config_json, str) else config_json
    result = compose_full(config)
    return json.dumps(result, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
# 镜头状态管理工具（断点续传）
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
def shot_update_status(project_id: str, shot_id: str, status: str,
                       video_path: str = "", image_path: str = "",
                       error: str = "") -> str:
    """更新单个镜头的生成状态（断点续传）。
    
    Args:
        project_id: 项目 ID
        shot_id: 镜头 ID（格式：S{n}_Sc{n}_Shot{n}）
        status: 状态（pending/generating/success/failed）
        video_path: 生成的视频路径（success 时填写）
        image_path: 生成的关键帧图片路径
        error: 错误信息（failed 时填写）
    """
    data = {
        "project_id": project_id,
        "shot_id": shot_id,
        "status": status,
        "video_path": video_path,
        "image_path": image_path,
        "error": error,
    }
    result = upsert_shot_status(data)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def shot_list_pending(project_id: str) -> str:
    """列出项目中所有待生成的镜头（status 不为 success）。
    
    返回未完成镜头列表，用于断点续传时跳过已成功的镜头。
    """
    all_result = list_shots_by_status(project_id)
    if all_result["status"] != "success":
        return json.dumps(all_result, ensure_ascii=False)
    
    pending = [s for s in all_result["shots"] if s["status"] != "success"]
    return json.dumps({
        "status": "success",
        "pending_shots": pending,
        "total": all_result["total"],
        "completed": all_result["total"] - len(pending),
        "pending": len(pending),
        "summary": all_result.get("summary", {})
    }, ensure_ascii=False, default=str)


@mcp.tool()
def shot_batch_init(project_id: str, shots_json: str) -> str:
    """批量初始化镜头状态（从 script_breakdown.json 解析后调用）。
    
    Args:
        project_id: 项目 ID
        shots_json: JSON 字符串，镜头列表
            [{"shot_id": "S1_Sc1_Shot1", "sub_script": "Sub-Script 1", "scene": "Scene 1", "shot": "Shot 1"}, ...]
    """
    shots = json.loads(shots_json) if isinstance(shots_json, str) else shots_json
    result = batch_init_shots(project_id, shots)
    return json.dumps(result, ensure_ascii=False)


# ─── 启动入口 ──────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
