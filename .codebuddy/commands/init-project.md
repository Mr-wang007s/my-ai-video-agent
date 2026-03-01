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
   - `language`：语言（默认 zh）

2. **生成 project_id**：格式 `YYYYMMDD_HHMMSS_别名`（别名从项目名称生成）

3. **创建项目目录结构**：
   ```
   Write: projects/{project_id}/project.json  ← 包含 name, description, style, config, created_at
   Write: projects/{project_id}/status.json   ← {"status": "draft", "updated_at": "..."}
   ```
   确保以下子目录存在：
   - `projects/{project_id}/character_list/`
   - `projects/{project_id}/exports/`
   - `projects/{project_id}/images/shots/`
   - `projects/{project_id}/videos/`
   - `projects/{project_id}/final/`

4. **验证**：确认 `project.json` 和 `status.json` 写入成功，目录结构完整。

5. **告知用户**：返回 project_id，提示下一步：
   - 准备好剧本/小说 `.txt` 文件
   - 执行 `/import-script` 导入剧本

## 注意事项

- 项目初始状态为 `draft`
- project_id 格式为 `YYYYMMDD_HHMMSS_别名`，后续所有步骤都需要用到
- 步骤 1 不需要任何 API Key
- 所有数据通过文件系统读写，不依赖 MCP 或数据库
