#!/usr/bin/env python3
"""Seedance 2.0 视频生成脚本 - 调用火山方舟 Seedance 2.0 API。

支持模式：
  - 文生视频 (text-to-video): 纯文本 Prompt 生成视频
  - 图生视频 (image-to-video): 图片 + 文本 Prompt 生成视频
  - 多模态参考 (multimodal): 多图 + 多视频 + 多音频 + 文本

Seedance 2.0 核心特性：
  - 音视频联合生成（原生自带音效/配音，双声道立体声）
  - 多镜头叙事（跨场景角色/风格一致性）
  - @ 引用语法控制参考素材用途
  - 最长 15 秒输出，原生 1080p
  - 支持最多 9 图 + 3 视频 + 3 音频参考输入

Usage:
    python scripts/seedance_generate.py --config '{"mode": "t2v", "prompt": "...", "output_dir": "..."}'
    python scripts/seedance_generate.py --config '{"mode": "i2v", "image_paths": ["..."], "prompt": "...", "output_dir": "..."}'
    python scripts/seedance_generate.py --config-file path/to/config.json
"""

import argparse
import json
import os
import sys
import time
import logging
import hashlib
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# 火山方舟 API 配置
ARK_API_KEY = os.getenv("ARK_API_KEY", "")
ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
SEEDANCE_MODEL = os.getenv("SEEDANCE_MODEL", "doubao-seedance-2-0-pro-250224")


def _upload_file_to_ark(file_path: str) -> dict:
    """上传本地文件到火山方舟，获取 file_id 用于引用。

    Returns:
        {"file_id": "...", "url": "..."} or {"error": "..."}
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    headers = {"Authorization": f"Bearer {ARK_API_KEY}"}

    try:
        with open(file_path, "rb") as f:
            resp = requests.post(
                f"{ARK_BASE_URL}/files",
                headers=headers,
                files={"file": (os.path.basename(file_path), f)},
                data={"purpose": "video_generation"},
                timeout=60
            )
        resp.raise_for_status()
        data = resp.json()
        return {"file_id": data.get("id", ""), "url": data.get("url", "")}
    except Exception as e:
        return {"error": f"File upload failed: {str(e)}"}


def _build_content(config: dict) -> list:
    """根据配置构建 Seedance 2.0 API 的 content 数组。

    content 数组支持混合 text / image_url / video_url / audio_url 类型。
    通过 @ 引用语法在 text 中指定各素材用途。
    """
    content = []
    mode = config.get("mode", "t2v")

    # 添加图片引用（最多 9 张）
    image_paths = config.get("image_paths", [])
    if isinstance(image_paths, str):
        image_paths = [image_paths]

    for img_path in image_paths[:9]:
        if img_path.startswith("http"):
            content.append({"type": "image_url", "image_url": {"url": img_path}})
        elif os.path.exists(img_path):
            with open(img_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            ext = Path(img_path).suffix.lstrip(".").lower()
            mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(ext, "image/png")
            content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})

    # 添加视频引用（最多 3 个）
    video_refs = config.get("video_refs", [])
    for vid_path in video_refs[:3]:
        if vid_path.startswith("http"):
            content.append({"type": "video_url", "video_url": {"url": vid_path}})

    # 添加音频引用（最多 3 个）
    audio_refs = config.get("audio_refs", [])
    for aud_path in audio_refs[:3]:
        if aud_path.startswith("http"):
            content.append({"type": "audio_url", "audio_url": {"url": aud_path}})

    # 构建 Prompt 文本（含参数后缀和 @ 引用）
    prompt = config.get("prompt", "")
    duration = config.get("duration", 5)
    resolution = config.get("resolution", "1080p")
    ratio = config.get("ratio", "16:9")

    # 构建参数后缀
    param_suffix = f" --dur {duration} --rs {resolution} --rt {ratio}"

    # 可选参数
    if config.get("seed") is not None:
        param_suffix += f" --seed {config['seed']}"
    if config.get("fixed_camera"):
        param_suffix += " --cf true"
    if config.get("no_watermark"):
        param_suffix += " --wm false"

    # 音频提示词（音视频联合生成的关键）
    audio_prompt = config.get("audio_prompt", "")
    if audio_prompt:
        # 将音频提示词整合到 prompt 中
        prompt = f"{prompt}。音效描述：{audio_prompt}"

    full_text = prompt + param_suffix

    content.append({"type": "text", "text": full_text})

    return content


def generate_video(config: dict) -> dict:
    """调用 Seedance 2.0 API 生成视频。

    Args:
        config: 配置字典，支持以下字段：
            - mode: "t2v" | "i2v" | "multimodal" (默认 "t2v")
            - prompt: 视频生成提示词
            - audio_prompt: 音频/音效提示词（启用音视频联合生成）
            - image_paths: 图片路径列表（i2v/multimodal 模式）
            - video_refs: 视频参考 URL 列表（multimodal 模式）
            - audio_refs: 音频参考 URL 列表（multimodal 模式）
            - output_dir: 输出目录
            - duration: 时长（秒），可选 4/5/10/15，默认 5
            - resolution: "720p" | "1080p"，默认 "1080p"
            - ratio: "16:9" | "9:16" | "1:1" | "4:3" | "3:4" | "21:9"，默认 "16:9"
            - seed: 随机种子（可选）
            - fixed_camera: 是否固定镜头（可选）
            - no_watermark: 是否去水印（可选）
            - shot_id: 镜头 ID，用于输出文件命名（可选）

    Returns:
        dict: {"status": "success/failed", "output_path": "...", "video_url": "...", "has_audio": true, ...}
    """
    if not ARK_API_KEY:
        return {"status": "failed", "error": "Missing ARK_API_KEY in .env"}

    output_dir = config.get("output_dir", "assets/outputs")
    os.makedirs(output_dir, exist_ok=True)

    try:
        # 构建 content 数组
        content = _build_content(config)

        # 构建请求 payload
        payload = {
            "model": config.get("model", SEEDANCE_MODEL),
            "content": content
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ARK_API_KEY}"
        }

        logger.info(f"Calling Seedance 2.0 API: mode={config.get('mode', 't2v')}, "
                     f"prompt='{config.get('prompt', '')[:60]}...', "
                     f"duration={config.get('duration', 5)}s, "
                     f"has_audio_prompt={'audio_prompt' in config}")

        # 提交视频生成任务
        resp = requests.post(
            f"{ARK_BASE_URL}/video/generations",
            headers=headers,
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        task_data = resp.json()
        task_id = task_data.get("id", "") or task_data.get("task_id", "")

        if not task_id:
            return {"status": "failed", "error": f"No task_id returned: {task_data}"}

        # 轮询任务状态
        logger.info(f"Task submitted: {task_id}, polling status...")
        max_attempts = 180  # 最多等待 15 分钟（15s 视频需要更长生成时间）
        poll_interval = 5

        for attempt in range(max_attempts):
            time.sleep(poll_interval)

            try:
                status_resp = requests.get(
                    f"{ARK_BASE_URL}/video/generations/{task_id}",
                    headers={"Authorization": f"Bearer {ARK_API_KEY}"},
                    timeout=15
                )
                status_data = status_resp.json()
            except Exception as poll_err:
                logger.warning(f"  Poll error (attempt {attempt + 1}): {poll_err}")
                continue

            status = status_data.get("status", "")

            if status == "succeeded":
                # 提取视频 URL
                video_url = ""
                video_data = status_data.get("output", status_data.get("data", {}))
                if isinstance(video_data, dict):
                    video_url = video_data.get("video_url", "") or video_data.get("url", "")
                elif isinstance(video_data, list) and video_data:
                    video_url = video_data[0].get("url", "")

                if not video_url:
                    # 尝试从 content 中提取
                    content_items = status_data.get("content", [])
                    for item in content_items:
                        if item.get("type") == "video_url":
                            video_url = item.get("video_url", {}).get("url", "")
                            break

                if video_url:
                    # 下载视频（注意：URL 24 小时有效，必须及时下载）
                    shot_id = config.get("shot_id", "")
                    prompt_hash = hashlib.md5(config.get("prompt", "").encode()).hexdigest()[:8]
                    video_name = f"{shot_id + '_' if shot_id else ''}seedance_{prompt_hash}_{int(time.time())}.mp4"
                    output_path = os.path.join(output_dir, video_name)

                    video_resp = requests.get(video_url, timeout=120)
                    with open(output_path, "wb") as vf:
                        vf.write(video_resp.content)

                    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    logger.info(f"Video saved: {output_path} ({file_size_mb:.1f}MB)")

                    return {
                        "status": "success",
                        "output_path": output_path,
                        "video_url": video_url,
                        "task_id": task_id,
                        "has_audio": True,  # Seedance 2.0 默认生成自带音频
                        "duration": config.get("duration", 5),
                        "resolution": config.get("resolution", "1080p"),
                        "file_size_mb": round(file_size_mb, 2)
                    }

                return {"status": "failed", "error": "No video URL in response", "raw": str(status_data)[:500]}

            elif status in ("failed", "cancelled"):
                error_msg = status_data.get("error", {})
                if isinstance(error_msg, dict):
                    error_msg = error_msg.get("message", str(error_msg))
                return {"status": "failed", "error": f"Generation failed: {error_msg}", "task_id": task_id}

            if attempt % 6 == 0:
                logger.info(f"  Polling attempt {attempt + 1}/{max_attempts}, status: {status}")

        return {"status": "failed", "error": "Timeout: task did not complete in 15 minutes", "task_id": task_id}

    except requests.RequestException as e:
        return {"status": "failed", "error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"status": "failed", "error": f"Unexpected error: {str(e)}"}


def main():
    parser = argparse.ArgumentParser(description="Seedance 2.0 视频生成")
    parser.add_argument("--config", type=str, help="JSON 配置字符串")
    parser.add_argument("--config-file", type=str, help="JSON 配置文件路径")
    args = parser.parse_args()

    if args.config_file:
        with open(args.config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    elif args.config:
        config = json.loads(args.config)
    else:
        parser.error("Must provide --config or --config-file")
        return

    result = generate_video(config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
