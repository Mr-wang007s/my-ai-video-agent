-- AI 漫剧流水线数据库初始化脚本
-- 注意：此脚本使用 CREATE TABLE IF NOT EXISTS，更新表结构时需先 DROP 旧表

-- 如需完全重建，取消以下注释：
-- DROP TABLE IF EXISTS generations;
-- DROP TABLE IF EXISTS assets;
-- DROP TABLE IF EXISTS characters;
-- DROP TABLE IF EXISTS storyboards;
-- DROP TABLE IF EXISTS scripts;
-- DROP TABLE IF EXISTS projects;

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    style TEXT DEFAULT 'manga',
    status TEXT DEFAULT 'draft',
    config TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scripts (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    title TEXT,
    synopsis TEXT,
    scenes TEXT NOT NULL,
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS storyboards (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    script_id TEXT REFERENCES scripts(id),
    shots TEXT NOT NULL,
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS characters (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    name TEXT NOT NULL,
    description TEXT,
    appearance TEXT,
    reference_images TEXT,
    style_keywords TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    type TEXT NOT NULL CHECK(type IN ('image','video','audio','reference','lora')),
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generations (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    stage TEXT NOT NULL CHECK(stage IN ('script','storyboard','image','video','audio','compose','import','extract','design','breakdown')),
    input_params TEXT,
    output_path TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending','running','success','failed')),
    error TEXT,
    cost REAL DEFAULT 0,
    duration_ms INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 镜头生成状态表（断点续传）
CREATE TABLE IF NOT EXISTS shot_status (
    id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    sub_script TEXT NOT NULL DEFAULT '',
    scene TEXT NOT NULL DEFAULT '',
    shot TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    video_path TEXT DEFAULT '',
    image_path TEXT DEFAULT '',
    error TEXT DEFAULT '',
    attempts INTEGER DEFAULT 0,
    last_attempt_at TEXT,
    PRIMARY KEY (id, project_id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX IF NOT EXISTS idx_shot_status_project ON shot_status(project_id);
CREATE INDEX IF NOT EXISTS idx_shot_status_status ON shot_status(project_id, status);
