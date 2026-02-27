#!/usr/bin/env python3
"""图像生成脚本 - 调用 SD/DALL-E API 根据 Prompt 生成分镜图片。

Usage:
    python scripts/image_generate.py --config '{"prompt": "...", "output_dir": "..."}'
    python scripts/image_generate.py --config-file path/to/config.json
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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SD_API_URL = os.getenv("SD_API_URL", "http://127.0.0.1:7860")
SD_API_KEY = os.getenv("SD_API_KEY", "")


def generate_image_dalle(prompt: str, output_dir: str, **kwargs) -> dict:
    """调用 OpenAI DALL-E API 生成图片。"""
    if not OPENAI_API_KEY:
        return {"status": "failed", "error": "Missing OPENAI_API_KEY in .env"}

    os.makedirs(output_dir, exist_ok=True)

    size = kwargs.get("size", "1024x1024")
    model = kwargs.get("model", "dall-e-3")
    quality = kwargs.get("quality", "standard")
    style = kwargs.get("style", "vivid")

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality,
            "style": style
        }

        logger.info(f"Calling DALL-E: prompt='{prompt[:50]}...', size={size}")

        resp = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=payload,
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()

        image_url = data["data"][0]["url"]
        image_name = f"dalle_{hashlib.md5(prompt.encode()).hexdigest()[:8]}_{int(time.time())}.png"
        output_path = os.path.join(output_dir, image_name)

        img_resp = requests.get(image_url, timeout=60)
        with open(output_path, "wb") as imgf:
            imgf.write(img_resp.content)

        logger.info(f"Image saved: {output_path}")
        return {
            "status": "success",
            "output_path": output_path,
            "revised_prompt": data["data"][0].get("revised_prompt", "")
        }

    except Exception as e:
        return {"status": "failed", "error": f"DALL-E generation failed: {str(e)}"}


def generate_image_sd(prompt: str, output_dir: str, **kwargs) -> dict:
    """调用 Stable Diffusion WebUI API 生成图片。"""
    os.makedirs(output_dir, exist_ok=True)

    negative_prompt = kwargs.get("negative_prompt", "low quality, blurry, deformed")
    width = kwargs.get("width", 1024)
    height = kwargs.get("height", 1024)
    steps = kwargs.get("steps", 30)
    cfg_scale = kwargs.get("cfg_scale", 7.0)
    seed = kwargs.get("seed", -1)

    try:
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "seed": seed
        }

        headers = {"Content-Type": "application/json"}
        if SD_API_KEY:
            headers["Authorization"] = f"Bearer {SD_API_KEY}"

        logger.info(f"Calling SD API: prompt='{prompt[:50]}...', {width}x{height}")

        resp = requests.post(
            f"{SD_API_URL}/sdapi/v1/txt2img",
            headers=headers,
            json=payload,
            timeout=120
        )
        resp.raise_for_status()
        data = resp.json()

        import base64
        image_data = base64.b64decode(data["images"][0])
        image_name = f"sd_{hashlib.md5(prompt.encode()).hexdigest()[:8]}_{int(time.time())}.png"
        output_path = os.path.join(output_dir, image_name)
        with open(output_path, "wb") as imgf:
            imgf.write(image_data)

        logger.info(f"Image saved: {output_path}")
        return {
            "status": "success",
            "output_path": output_path,
            "seed": data.get("parameters", {}).get("seed", seed)
        }

    except Exception as e:
        return {"status": "failed", "error": f"SD generation failed: {str(e)}"}


def main():
    parser = argparse.ArgumentParser(description="图像生成")
    parser.add_argument("--config", type=str, help="JSON 配置字符串")
    parser.add_argument("--config-file", type=str, help="JSON 配置文件路径")
    parser.add_argument("--engine", type=str, default="dalle", choices=["dalle", "sd"], help="图像引擎")
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
    if engine == "sd":
        result = generate_image_sd(
            prompt=config["prompt"],
            output_dir=config.get("output_dir", "assets/outputs"),
            **{k: v for k, v in config.items() if k not in ("prompt", "output_dir", "engine")}
        )
    else:
        result = generate_image_dalle(
            prompt=config["prompt"],
            output_dir=config.get("output_dir", "assets/outputs"),
            **{k: v for k, v in config.items() if k not in ("prompt", "output_dir", "engine")}
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
