#!/usr/bin/env python3
"""SQLite 数据库管理脚本 - 项目/剧本/分镜/角色/资产/生成记录的 CRUD 操作。

Usage:
    python scripts/db_manager.py --action create_project --data '{"name": "test"}'
    python scripts/db_manager.py --action list_projects
    python scripts/db_manager.py --action init_db
"""

import argparse
import json
import os
import re
import sys
import uuid
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.db"))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(force: bool = False):
    """初始化数据库表结构。force=True 时先删除所有表再重建。"""
    sql_path = os.path.join(os.path.dirname(__file__), "init_db.sql")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()
    conn = get_connection()
    if force:
        tables = ["generations", "assets", "characters", "storyboards", "scripts", "projects"]
        for table in tables:
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        logger.info("All tables dropped (force rebuild)")
    conn.executescript(sql)
    conn.close()
    logger.info("Database initialized successfully")
    return {"status": "success", "message": f"Database initialized{' (force rebuild)' if force else ''}"}


def _generate_project_id(name: str) -> str:
    """生成可读的项目ID：YYYYMMDD_HHMMSS_别名。
    
    别名规则：
    - 中文/英文名称保留，空格和特殊字符转为下划线
    - 限制别名最长 30 字符
    - 如 "我的漫剧" → "20260228_143025_我的漫剧"
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 只保留中文、英文、数字、下划线、连字符
    alias = re.sub(r'[^\w\u4e00-\u9fff-]', '_', name)
    # 合并连续下划线，去除首尾下划线
    alias = re.sub(r'_+', '_', alias).strip('_')
    # 限制长度
    if len(alias) > 30:
        alias = alias[:30].rstrip('_')
    if not alias:
        alias = str(uuid.uuid4())[:6]
    return f"{timestamp}_{alias}"


def create_project(data: dict) -> dict:
    project_id = data.get("id") or _generate_project_id(data["name"])
    conn = get_connection()
    conn.execute(
        "INSERT INTO projects (id, name, description, style, status, config) VALUES (?, ?, ?, ?, ?, ?)",
        (project_id, data["name"], data.get("description", ""), data.get("style", "manga"),
         "draft", json.dumps(data.get("config", {})))
    )
    conn.commit()
    conn.close()

    # 创建项目工作目录
    project_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "projects", project_id)
    for sub in ["images/characters", "images/shots", "videos", "audio", "character_list", "final"]:
        os.makedirs(os.path.join(project_dir, sub), exist_ok=True)

    logger.info(f"Project created: {project_id}")
    return {"status": "success", "project_id": project_id}


def list_projects() -> dict:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
    conn.close()
    return {"status": "success", "projects": [dict(r) for r in rows]}


def get_project(project_id: str) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    if row:
        return {"status": "success", "project": dict(row)}
    return {"status": "failed", "error": f"Project not found: {project_id}"}


def update_project_status(project_id: str, status: str) -> dict:
    conn = get_connection()
    conn.execute(
        "UPDATE projects SET status = ?, updated_at = ? WHERE id = ?",
        (status, datetime.now().isoformat(), project_id)
    )
    conn.commit()
    conn.close()
    return {"status": "success"}


def save_script(data: dict) -> dict:
    script_id = data.get("id", str(uuid.uuid4())[:8])
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO scripts (id, project_id, title, synopsis, scenes, metadata) VALUES (?, ?, ?, ?, ?, ?)",
        (script_id, data["project_id"], data.get("title", ""), data.get("synopsis", ""),
         json.dumps(data["scenes"], ensure_ascii=False), json.dumps(data.get("metadata", {})))
    )
    conn.commit()
    conn.close()
    return {"status": "success", "script_id": script_id}


def save_storyboard(data: dict) -> dict:
    sb_id = data.get("id", str(uuid.uuid4())[:8])
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO storyboards (id, project_id, script_id, shots, metadata) VALUES (?, ?, ?, ?, ?)",
        (sb_id, data["project_id"], data.get("script_id", ""),
         json.dumps(data["shots"], ensure_ascii=False), json.dumps(data.get("metadata", {})))
    )
    conn.commit()
    conn.close()
    return {"status": "success", "storyboard_id": sb_id}


def save_character(data: dict) -> dict:
    char_id = data.get("id", str(uuid.uuid4())[:8])
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO characters (id, project_id, name, description, appearance, reference_images, style_keywords) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (char_id, data["project_id"], data["name"], data.get("description", ""),
         json.dumps(data.get("appearance", {}), ensure_ascii=False),
         json.dumps(data.get("reference_images", []), ensure_ascii=False),
         json.dumps(data.get("style_keywords", []), ensure_ascii=False))
    )
    conn.commit()
    conn.close()
    return {"status": "success", "character_id": char_id}


def save_asset(data: dict) -> dict:
    """保存资产记录（图片/视频/音频）。"""
    asset_id = data.get("id", str(uuid.uuid4())[:8])
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO assets (id, project_id, type, name, file_path, metadata) VALUES (?, ?, ?, ?, ?, ?)",
        (asset_id, data["project_id"], data["type"], data.get("name", ""),
         data["file_path"], json.dumps(data.get("metadata", {}), ensure_ascii=False))
    )
    conn.commit()
    conn.close()
    return {"status": "success", "asset_id": asset_id}


def list_assets(project_id: str, asset_type: str = None) -> dict:
    """列出项目的资产文件。"""
    conn = get_connection()
    if asset_type:
        rows = conn.execute(
            "SELECT * FROM assets WHERE project_id = ? AND type = ?",
            (project_id, asset_type)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM assets WHERE project_id = ?", (project_id,)
        ).fetchall()
    conn.close()
    return {"status": "success", "assets": [dict(r) for r in rows]}


def log_generation(data: dict) -> dict:
    gen_id = data.get("id", str(uuid.uuid4())[:8])
    conn = get_connection()
    conn.execute(
        "INSERT INTO generations (id, project_id, stage, input_params, output_path, status, error, cost, duration_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (gen_id, data["project_id"], data["stage"],
         json.dumps(data.get("input_params", {})), data.get("output_path", ""),
         data.get("status", "pending"), data.get("error", ""),
         data.get("cost", 0), data.get("duration_ms", 0))
    )
    conn.commit()
    conn.close()
    return {"status": "success", "generation_id": gen_id}


def get_project_summary(project_id: str) -> dict:
    """获取项目完整摘要（含统计信息）。"""
    conn = get_connection()
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        conn.close()
        return {"status": "failed", "error": f"Project not found: {project_id}"}

    scripts_count = conn.execute("SELECT COUNT(*) FROM scripts WHERE project_id = ?", (project_id,)).fetchone()[0]
    storyboards_count = conn.execute("SELECT COUNT(*) FROM storyboards WHERE project_id = ?", (project_id,)).fetchone()[0]
    characters_count = conn.execute("SELECT COUNT(*) FROM characters WHERE project_id = ?", (project_id,)).fetchone()[0]
    assets_count = conn.execute("SELECT COUNT(*) FROM assets WHERE project_id = ?", (project_id,)).fetchone()[0]
    generations_count = conn.execute("SELECT COUNT(*) FROM generations WHERE project_id = ?", (project_id,)).fetchone()[0]
    conn.close()

    return {
        "status": "success",
        "project": dict(project),
        "counts": {
            "scripts": scripts_count,
            "storyboards": storyboards_count,
            "characters": characters_count,
            "assets": assets_count,
            "generations": generations_count
        }
    }


ACTIONS = {
    "init_db": lambda d: init_db(force=d.get("force", False)),
    "create_project": create_project,
    "list_projects": lambda d: list_projects(),
    "get_project": lambda d: get_project(d["project_id"]),
    "get_project_summary": lambda d: get_project_summary(d["project_id"]),
    "update_status": lambda d: update_project_status(d["project_id"], d["status"]),
    "save_script": save_script,
    "save_storyboard": save_storyboard,
    "save_character": save_character,
    "save_asset": save_asset,
    "list_assets": lambda d: list_assets(d["project_id"], d.get("type")),
    "log_generation": log_generation,
}


def main():
    parser = argparse.ArgumentParser(description="数据库管理")
    parser.add_argument("--action", type=str, required=True, choices=list(ACTIONS.keys()))
    parser.add_argument("--data", type=str, default="{}", help="JSON 数据")
    args = parser.parse_args()

    data = json.loads(args.data)
    result = ACTIONS[args.action](data)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
