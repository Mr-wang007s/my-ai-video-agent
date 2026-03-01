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
from retry_util import with_retry, check_response, RetryableError

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SD_API_URL = os.getenv("SD_API_URL", "http://127.0.0.1:7860")
SD_API_KEY = os.getenv("SD_API_KEY", "")
ARK_API_KEY = os.getenv("ARK_API_KEY", "")
ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
SEEDREAM_MODEL = os.getenv("SEEDREAM_MODEL", "doubao-seedream-5-0-260128")


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
        @with_retry(max_retries=3, delays=(1, 3, 10))
        def _call_dalle():
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
            return check_response(resp).json()

        data = _call_dalle()
        image_url = data["data"][0]["url"]
        image_name = f"dalle_{hashlib.md5(prompt.encode()).hexdigest()[:8]}_{int(time.time())}.png"
        output_path = os.path.join(output_dir, image_name)

        @with_retry(max_retries=3, delays=(1, 3, 10))
        def _download_image():
            img_resp = requests.get(image_url, timeout=60)
            check_response(img_resp)
            return img_resp.content

        img_data = _download_image()
        with open(output_path, "wb") as imgf:
            imgf.write(img_data)

        logger.info(f"Image saved: {output_path}")
        return {
            "status": "success",
            "output_path": output_path,
            "revised_prompt": data["data"][0].get("revised_prompt", "")
        }

    except Exception as e:
        return {"status": "failed", "error": f"DALL-E generation failed: {str(e)}"}


def generate_image_seedream(prompt: str, output_dir: str, **kwargs) -> dict:
    """调用火山方舟 Seedream 5.0 API 生成图片（与 Seedance 共享 ARK 凭证）。"""
    if not ARK_API_KEY:
        return {"status": "failed", "error": "Missing ARK_API_KEY in .env"}

    os.makedirs(output_dir, exist_ok=True)

    size = kwargs.get("size", "2K")
    model = kwargs.get("model", SEEDREAM_MODEL)

    try:
        @with_retry(max_retries=3, delays=(1, 3, 10))
        def _call_seedream():
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ARK_API_KEY}"
            }
            payload = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "sequential_image_generation": "disabled",
                "response_format": "url",
                "stream": False,
                "watermark": False
            }
            logger.info(f"Calling Seedream: prompt='{prompt[:50]}...', size={size}, model={model}")
            resp = requests.post(
                f"{ARK_BASE_URL}/images/generations",
                headers=headers,
                json=payload,
                timeout=120
            )
            return check_response(resp).json()

        data = _call_seedream()
        image_url = data["data"][0]["url"]
        image_name = f"seedream_{hashlib.md5(prompt.encode()).hexdigest()[:8]}_{int(time.time())}.png"
        output_path = os.path.join(output_dir, image_name)

        @with_retry(max_retries=3, delays=(1, 3, 10))
        def _download_image():
            img_resp = requests.get(image_url, timeout=60)
            check_response(img_resp)
            return img_resp.content

        img_data = _download_image()
        with open(output_path, "wb") as imgf:
            imgf.write(img_data)

        logger.info(f"Image saved: {output_path}")
        return {
            "status": "success",
            "output_path": output_path,
            "model": model
        }

    except Exception as e:
        return {"status": "failed", "error": f"Seedream generation failed: {str(e)}"}


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
        @with_retry(max_retries=3, delays=(1, 3, 10))
        def _call_sd():
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
            return check_response(resp).json()

        data = _call_sd()
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
    parser.add_argument("--engine", type=str, default="seedream", choices=["seedream", "dalle", "sd"], help="图像引擎（默认 seedream）")
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
    extra = {k: v for k, v in config.items() if k not in ("prompt", "output_dir", "engine")}
    out_dir = config.get("output_dir", "assets/outputs")
    if engine == "sd":
        result = generate_image_sd(prompt=config["prompt"], output_dir=out_dir, **extra)
    elif engine == "dalle":
        result = generate_image_dalle(prompt=config["prompt"], output_dir=out_dir, **extra)
    else:
        result = generate_image_seedream(prompt=config["prompt"], output_dir=out_dir, **extra)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
