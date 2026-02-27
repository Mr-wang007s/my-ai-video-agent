---
name: init-project
description: "Step 1: 初始化漫剧项目 — 创建项目、生成目录结构"
---

## 执行步骤

1. **收集项目信息**：向用户确认以下参数（如未提供则用默认值）：
   - `name`：项目名称（必填）
   - `description`：项目描述
   - `style`：画面风格（manga/anime/comic/realistic/watercolor/pixel，默认 manga）
   - `target_duration`：目标时长秒数（默认 120）
   - `resolution`：分辨率（默认 1080p）
   - `language`：语言（默认 zh）

2. **创建项目**：
   ```bash
   python scripts/db_manager.py --action create_project --data '{"name": "{name}", "description": "{description}", "style": "{style}", "config": {"target_duration": {duration}, "resolution": "{resolution}", "language": "{language}"}}'
   ```

3. **验证**：确认返回 `project_id` 且目录结构已创建：
   - `projects/{project_id}/images/characters/`
   - `projects/{project_id}/images/shots/`
   - `projects/{project_id}/videos/`
   - `projects/{project_id}/audio/`

4. **告知用户**：返回 project_id，提示用户下一步使用 `/confirm-story` 确认内容。

## 注意事项

- 项目初始状态为 `draft`
- project_id 为 8 位短 UUID，后续所有步骤都需要用到
