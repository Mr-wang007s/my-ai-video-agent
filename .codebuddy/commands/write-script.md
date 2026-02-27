---
name: write-script
description: "Step 3: 编剧 + 分镜 — 基于确认的故事大纲，生成完整剧本和分镜表"
---

## 前置条件

- 项目状态为 `confirmed`（已通过 `/confirm-story` 确认）
- `projects/{project_id}/story_brief.json` 已存在

## 执行步骤

1. **验证前置条件**：
   ```bash
   python scripts/db_manager.py --action get_project --data '{"project_id": "{project_id}"}'
   ```
   确认状态为 `confirmed`。

2. **Dispatch to Screenwriter Agent**：通过 Task 工具调用 screenwriter 子 Agent：

   ```
   Project: {project_id}
   Working directory: projects/{project_id}/

   Task: 基于 story_brief.json 中确认的故事大纲，创建完整剧本和分镜表。

   Input files:
   - projects/{project_id}/story_brief.json（已确认的故事大纲）

   Output files:
   - projects/{project_id}/script.json（完整剧本）
   - projects/{project_id}/storyboard.json（分镜表）

   要求：
   1. 使用 manga-script skill 的三幕式结构
   2. 使用 storyboard-design skill 的分镜设计方法
   3. script.json 必须符合 schemas/script.schema.json
   4. storyboard.json 必须符合 schemas/storyboard.schema.json
   5. 每个场景至少 2 个镜头
   6. 所有镜头必须有 audio_prompt（音效描述）
   7. 对白不超过 20 字/句
   8. 镜头时长对齐 Seedance 档位（4/5/10/15s）
   9. 总时长与 story_brief 的 estimated_duration 一致（±20%）
   ```

3. **验证产出**：
   - `script.json` 存在且 JSON 合法
   - `storyboard.json` 存在且 JSON 合法
   - 每个场景在分镜中有对应镜头
   - 所有镜头都有 audio_prompt

4. **写入数据库**：
   ```bash
   python scripts/db_manager.py --action save_script --data '{...}'
   python scripts/db_manager.py --action save_storyboard --data '{...}'
   python scripts/db_manager.py --action log_generation --data '{"project_id": "...", "stage": "script", ...}'
   python scripts/db_manager.py --action update_status --data '{"project_id": "...", "status": "scripted"}'
   ```

5. **向用户展示结果摘要**：
   - 场景数量和列表
   - 总镜头数
   - 预估总时长
   - 角色出场统计

6. **提示下一步**：告知用户可以使用 `/design-characters` 进入角色设计阶段。

## 注意事项

- Screenwriter 需要同时加载 manga-script 和 storyboard-design 两个 skill
- audio_prompt 使用中文描述，其他 prompt 使用英文
- 镜头的 seedance_mode 根据内容选择：t2v / i2v / multimodal
