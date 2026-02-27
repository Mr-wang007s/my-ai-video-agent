#!/usr/bin/env python3
"""视频合成脚本 - 使用 FFmpeg 将视频片段、音频、字幕合成为最终成片。

适配 Seedance 2.0：每个视频片段自带原生音轨，合成时需保留音频。

支持模式:
  - compose: 完整合成流程（拼接+音频处理+字幕）
  - replace_audio: 替换指定视频的音轨（TTS Override）
  - overlay_bgm: 在视频上叠加背景音乐

Usage:
    python scripts/video_compose.py --config '{"segments": [...], "output_path": "..."}'
    python scripts/video_compose.py --config-file path/to/config.json
"""

import argparse
import json
import os
import sys
import time
import logging
import subprocess
import tempfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def check_ffmpeg() -> bool:
    """检查 FFmpeg 是否可用。"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def concat_videos(video_paths: list, output_path: str) -> dict:
    """拼接多个视频片段（保留各自的原生音轨）。"""
    if not check_ffmpeg():
        return {"status": "failed", "error": "FFmpeg not found. Please install FFmpeg."}

    existing = [p for p in video_paths if os.path.exists(p)]
    if not existing:
        return {"status": "failed", "error": "No valid video files found"}

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    try:
        if len(existing) == 1:
            import shutil
            shutil.copy2(existing[0], output_path)
            return {"status": "success", "output_path": output_path}

        # 使用 concat demuxer，保留音频轨道
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            for vp in existing:
                f.write(f"file '{os.path.abspath(vp)}'\n")
            list_file = f.name

        # 先统一编码格式再拼接（Seedance 生成的视频编码可能不完全一致）
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-ac", "2",
            output_path
        ]

        logger.info(f"Concatenating {len(existing)} videos (with audio) -> {output_path}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        os.unlink(list_file)

        if result.returncode != 0:
            return {"status": "failed", "error": f"FFmpeg concat failed: {result.stderr[:500]}"}

        return {"status": "success", "output_path": output_path}

    except Exception as e:
        return {"status": "failed", "error": f"Video concat failed: {str(e)}"}


def replace_audio(video_path: str, audio_path: str, output_path: str) -> dict:
    """替换视频的音轨（用于 TTS Override）。"""
    if not os.path.exists(video_path):
        return {"status": "failed", "error": f"Video not found: {video_path}"}
    if not os.path.exists(audio_path):
        return {"status": "failed", "error": f"Audio not found: {audio_path}"}

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-map", "0:v",       # 保留原视频画面
            "-map", "1:a",       # 使用新的音频轨道
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]

        logger.info(f"Replacing audio: {video_path} + {audio_path} -> {output_path}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            return {"status": "failed", "error": f"FFmpeg audio replace failed: {result.stderr[:500]}"}

        return {"status": "success", "output_path": output_path}

    except Exception as e:
        return {"status": "failed", "error": f"Audio replace failed: {str(e)}"}


def overlay_bgm(video_path: str, bgm_path: str, output_path: str, bgm_volume: float = 0.3) -> dict:
    """在视频上叠加 BGM（混合原有音频和 BGM）。"""
    if not os.path.exists(video_path):
        return {"status": "failed", "error": f"Video not found: {video_path}"}
    if not os.path.exists(bgm_path):
        return {"status": "failed", "error": f"BGM not found: {bgm_path}"}

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", bgm_path,
            "-filter_complex",
            f"[0:a]volume=1.0[a0];[1:a]volume={bgm_volume}[a1];[a0][a1]amix=inputs=2:duration=first[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            output_path
        ]

        logger.info(f"Overlaying BGM (volume={bgm_volume}): {video_path} -> {output_path}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            return {"status": "failed", "error": f"FFmpeg BGM overlay failed: {result.stderr[:500]}"}

        return {"status": "success", "output_path": output_path}

    except Exception as e:
        return {"status": "failed", "error": f"BGM overlay failed: {str(e)}"}


def add_subtitles(video_path: str, subtitles: list, output_path: str) -> dict:
    """为视频添加字幕（硬字幕烧录）。

    Args:
        subtitles: [{"start": 0.0, "end": 3.0, "text": "..."}]
    """
    if not os.path.exists(video_path):
        return {"status": "failed", "error": f"Video not found: {video_path}"}

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".srt", delete=False, encoding="utf-8") as f:
            for i, sub in enumerate(subtitles, 1):
                start = _format_srt_time(sub["start"])
                end = _format_srt_time(sub["end"])
                f.write(f"{i}\n{start} --> {end}\n{sub['text']}\n\n")
            srt_file = f.name

        # 使用 Windows 兼容的路径格式
        srt_escaped = srt_file.replace("\\", "/").replace(":", "\\:")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"subtitles={srt_escaped}:force_style='FontSize=24,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Outline=2'",
            "-c:a", "copy",
            output_path
        ]

        logger.info(f"Adding {len(subtitles)} subtitles -> {output_path}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        os.unlink(srt_file)

        if result.returncode != 0:
            return {"status": "failed", "error": f"FFmpeg subtitle failed: {result.stderr[:500]}"}

        return {"status": "success", "output_path": output_path}

    except Exception as e:
        return {"status": "failed", "error": f"Subtitle addition failed: {str(e)}"}


def compose_full(config: dict) -> dict:
    """完整的合成流程：拼接视频(含音轨) → [可选BGM] → 添加字幕。"""
    mode = config.get("mode", "compose")

    # 处理非 compose 模式
    if mode == "replace_audio":
        return replace_audio(
            config["video_path"],
            config["audio_path"],
            config["output_path"]
        )
    elif mode == "overlay_bgm":
        return overlay_bgm(
            config["video_path"],
            config["bgm_path"],
            config["output_path"],
            config.get("bgm_volume", 0.3)
        )

    # compose 模式：完整合成
    output_dir = config.get("output_dir", "assets/outputs")
    os.makedirs(output_dir, exist_ok=True)

    final_output = config.get("output_path", os.path.join(output_dir, f"final_{int(time.time())}.mp4"))
    temp_files = []

    try:
        # Step 1: 拼接视频片段（Seedance 2.0 视频自带音轨，直接拼接）
        segments = config.get("segments", [])
        video_paths = [s["video_path"] for s in segments if "video_path" in s]

        if not video_paths:
            return {"status": "failed", "error": "No video segments provided"}

        concat_output = os.path.join(output_dir, f"_concat_{int(time.time())}.mp4")
        temp_files.append(concat_output)

        concat_result = concat_videos(video_paths, concat_output)
        if concat_result["status"] != "success":
            return concat_result

        current_video = concat_output

        # Step 2: 可选 BGM 叠加
        bgm_path = config.get("bgm_path")
        if bgm_path and os.path.exists(bgm_path):
            bgm_output = os.path.join(output_dir, f"_bgm_{int(time.time())}.mp4")
            temp_files.append(bgm_output)
            bgm_result = overlay_bgm(
                current_video, bgm_path, bgm_output,
                config.get("bgm_volume", 0.3)
            )
            if bgm_result["status"] != "success":
                return bgm_result
            current_video = bgm_output

        # Step 3: 添加字幕（如果有）
        subtitles = config.get("subtitles", [])
        if subtitles:
            sub_result = add_subtitles(current_video, subtitles, final_output)
            if sub_result["status"] != "success":
                return sub_result
        else:
            if current_video != final_output:
                import shutil
                shutil.copy2(current_video, final_output)

        # 清理临时文件
        for tf in temp_files:
            if os.path.exists(tf) and tf != final_output:
                os.unlink(tf)

        logger.info(f"Final video: {final_output}")
        return {"status": "success", "output_path": final_output}

    except Exception as e:
        for tf in temp_files:
            if os.path.exists(tf):
                os.unlink(tf)
        return {"status": "failed", "error": f"Composition failed: {str(e)}"}


def _format_srt_time(seconds: float) -> str:
    """将秒数转为 SRT 时间格式。"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    parser = argparse.ArgumentParser(description="视频合成（适配 Seedance 2.0 带音轨视频）")
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

    result = compose_full(config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
