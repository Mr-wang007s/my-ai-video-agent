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

2. **初始化数据库**（首次使用时）：
   ```
   MCP tool: project_init_db()
   ```

3. **创建项目**：
   ```
   MCP tool: project_create(name, description, style, config='{"target_duration": N, "resolution": "1080p", "language": "zh"}')
   ```

4. **验证**：确认返回 `project_id`（格式 `YYYYMMDD_HHMMSS_别名`），且目录结构已创建：
   - `projects/{project_id}/images/characters/`
   - `projects/{project_id}/images/shots/`
   - `projects/{project_id}/videos/`
   - `projects/{project_id}/audio/`
   - `projects/{project_id}/character_list/`
   - `projects/{project_id}/final/`

5. **告知用户**：返回 project_id，提示下一步：
   - 准备好剧本/小说 `.txt` 文件
   - 执行 `/import-script` 导入剧本

## 注意事项

- 项目初始状态为 `draft`
- project_id 格式为 `YYYYMMDD_HHMMSS_别名`，后续所有步骤都需要用到
