#!/usr/bin/env python3
"""TTS 语音合成脚本 - 调用 TTS API 将文本转为语音。

Usage:
    python scripts/tts_generate.py --config '{"text": "...", "voice": "...", "output_dir": "..."}'
    python scripts/tts_generate.py --config-file path/to/config.json
"""

import argparse
import json
import os
import sys
import time
import logging
import hashlib
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# 火山引擎 TTS
VOLC_TTS_APP_ID = os.getenv("VOLC_TTS_APP_ID", "")
VOLC_TTS_TOKEN = os.getenv("VOLC_TTS_TOKEN", "")
VOLC_TTS_API_URL = os.getenv("VOLC_TTS_API_URL", "https://openspeech.bytedance.com/api/v1/tts")

# Azure TTS (备用)
AZURE_TTS_KEY = os.getenv("AZURE_TTS_KEY", "")
AZURE_TTS_REGION = os.getenv("AZURE_TTS_REGION", "eastasia")

# 预定义角色音色映射
VOICE_MAP = {
    "narrator": {"voice_type": "zh_male_narration", "description": "男性旁白"},
    "young_male": {"voice_type": "zh_male_young", "description": "年轻男性"},
    "young_female": {"voice_type": "zh_female_young", "description": "年轻女性"},
    "mature_male": {"voice_type": "zh_male_mature", "description": "成熟男性"},
    "mature_female": {"voice_type": "zh_female_mature", "description": "成熟女性"},
    "child": {"voice_type": "zh_child", "description": "儿童"},
}


def generate_speech_volc(text: str, voice: str, output_dir: str, **kwargs) -> dict:
    """调用火山引擎 TTS API。"""
    if not VOLC_TTS_APP_ID or not VOLC_TTS_TOKEN:
        return {"status": "failed", "error": "Missing VOLC_TTS_APP_ID or VOLC_TTS_TOKEN in .env"}

    os.makedirs(output_dir, exist_ok=True)

    voice_config = VOICE_MAP.get(voice, {"voice_type": voice})
    speed = kwargs.get("speed", 1.0)
    emotion = kwargs.get("emotion", "neutral")

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer;{VOLC_TTS_TOKEN}"
        }

        payload = {
            "app": {"appid": VOLC_TTS_APP_ID},
            "user": {"uid": "manga-agent"},
            "audio": {
                "voice_type": voice_config["voice_type"],
                "encoding": "mp3",
                "speed_ratio": speed
            },
            "request": {
                "reqid": hashlib.md5(f"{text}{time.time()}".encode()).hexdigest(),
                "text": text,
                "operation": "query"
            }
        }

        logger.info(f"Calling Volc TTS: voice={voice}, text='{text[:30]}...', speed={speed}")

        resp = requests.post(VOLC_TTS_API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()

        if result.get("code") == 3000:
            import base64
            audio_data = base64.b64decode(result["data"])
            audio_name = f"tts_{hashlib.md5(text.encode()).hexdigest()[:8]}_{int(time.time())}.mp3"
            output_path = os.path.join(output_dir, audio_name)
            with open(output_path, "wb") as af:
                af.write(audio_data)
            logger.info(f"Audio saved: {output_path}")
            return {"status": "success", "output_path": output_path, "duration_ms": len(audio_data) // 32}
        else:
            return {"status": "failed", "error": f"TTS API error: {result}"}

    except Exception as e:
        return {"status": "failed", "error": f"TTS generation failed: {str(e)}"}


def generate_speech_azure(text: str, voice: str, output_dir: str, **kwargs) -> dict:
    """调用 Azure TTS API（备用）。"""
    if not AZURE_TTS_KEY:
        return {"status": "failed", "error": "Missing AZURE_TTS_KEY in .env"}

    os.makedirs(output_dir, exist_ok=True)

    azure_voice = kwargs.get("azure_voice", "zh-CN-XiaoxiaoNeural")
    speed = kwargs.get("speed", 1.0)

    try:
        token_url = f"https://{AZURE_TTS_REGION}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        token_resp = requests.post(token_url, headers={"Ocp-Apim-Subscription-Key": AZURE_TTS_KEY}, timeout=10)
        token = token_resp.text

        ssml = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>
            <voice name='{azure_voice}'>
                <prosody rate='{speed}'>
                    {text}
                </prosody>
            </voice>
        </speak>
        """

        tts_url = f"https://{AZURE_TTS_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
        }

        resp = requests.post(tts_url, headers=headers, data=ssml.encode("utf-8"), timeout=30)
        resp.raise_for_status()

        audio_name = f"tts_azure_{hashlib.md5(text.encode()).hexdigest()[:8]}_{int(time.time())}.mp3"
        output_path = os.path.join(output_dir, audio_name)
        with open(output_path, "wb") as af:
            af.write(resp.content)
        logger.info(f"Audio saved: {output_path}")
        return {"status": "success", "output_path": output_path}

    except Exception as e:
        return {"status": "failed", "error": f"Azure TTS failed: {str(e)}"}


def main():
    parser = argparse.ArgumentParser(description="TTS 语音合成")
    parser.add_argument("--config", type=str, help="JSON 配置字符串")
    parser.add_argument("--config-file", type=str, help="JSON 配置文件路径")
    parser.add_argument("--engine", type=str, default="volc", choices=["volc", "azure"], help="TTS 引擎")
    args = parser.parse_args()

    if args.config_file:
        with open(args.config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    elif args.config:
        config = json.loads(args.config)
    else:
        parser.error("Must provide --config or --config-file")
        return

    engine = config.get("engine", args.engine)
    if engine == "azure":
        result = generate_speech_azure(
            text=config["text"],
            voice=config.get("voice", "narrator"),
            output_dir=config.get("output_dir", "assets/outputs"),
            **{k: v for k, v in config.items() if k not in ("text", "voice", "output_dir", "engine")}
        )
    else:
        result = generate_speech_volc(
            text=config["text"],
            voice=config.get("voice", "narrator"),
            output_dir=config.get("output_dir", "assets/outputs"),
            **{k: v for k, v in config.items() if k not in ("text", "voice", "output_dir", "engine")}
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
