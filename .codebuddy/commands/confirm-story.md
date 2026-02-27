---
name: confirm-story
description: "Step 2: 确认漫剧内容 — AI 生成故事梗概，用户确认后锁定方向"
---

## 前置条件

- 已通过 `/init-project` 创建项目，有可用的 `project_id`
- 项目状态为 `draft`

## 执行步骤

1. **获取项目信息**：
   ```bash
   python scripts/db_manager.py --action get_project --data '{"project_id": "{project_id}"}'
   ```

2. **获取用户主题**：如果用户未在本次消息中提供主题/大纲，询问用户：
   - 故事主题是什么？
   - 有没有更详细的大纲？（可选）
   - 有没有特别想要的角色？（可选）

3. **生成故事梗概**：基于用户主题，创作以下内容并展示给用户：
   - **故事概要**：3-5 句话概括整个故事的起承转合
   - **主要角色**：2-4 个角色，每个角色一句话描述
   - **场景规划**：3-8 个场景，每个场景标题 + 一句话描述
   - **预估时长**：基于场景数量估算

4. **等待用户确认**：明确询问用户：
   > 以上故事大纲是否满意？可以修改任何部分。确认后我将进入编剧阶段。

5. **用户确认后**，写入 `projects/{project_id}/story_brief.json`：
   ```json
   {
     "project_id": "{project_id}",
     "theme": "用户原始主题",
     "synopsis": "故事概要",
     "characters": [
       {"name": "角色名", "description": "描述", "role": "protagonist"}
     ],
     "scenes_plan": [
       {"id": "S01", "title": "场景标题", "description": "简述"}
     ],
     "estimated_duration": 120,
     "confirmed_at": "2025-01-01T00:00:00"
   }
   ```

6. **更新状态**：
   ```bash
   python scripts/db_manager.py --action update_status --data '{"project_id": "{project_id}", "status": "confirmed"}'
   ```

7. **提示下一步**：告知用户可以使用 `/write-script` 进入编剧阶段。

## 注意事项

- 这一步的核心是**用户确认**，不能跳过确认直接进入编剧
- 如果用户要求修改，重新生成梗概并再次确认
- story_brief.json 是后续所有步骤的起点
