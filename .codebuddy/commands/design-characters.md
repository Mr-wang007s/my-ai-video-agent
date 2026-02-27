---
name: design-characters
description: "Step 4: 角色设计 — 基于剧本设计角色外观并生成参考图"
---

## 前置条件

- 项目状态为 `scripted`（已通过 `/write-script` 完成编剧）
- `projects/{project_id}/script.json` 已存在

## 执行步骤

1. **验证前置条件**：
   ```bash
   python scripts/db_manager.py --action get_project --data '{"project_id": "{project_id}"}'
   ```
   确认状态为 `scripted`。

2. **Dispatch to Visual-Artist Agent**：通过 Task 工具调用 visual-artist 子 Agent：

   ```
   Project: {project_id}
   Working directory: projects/{project_id}/

   Task: 基于剧本设计所有角色的外观，并为每个角色生成参考图。

   Input files:
   - projects/{project_id}/script.json（完整剧本，含角色信息）
   - projects/{project_id}/story_brief.json（故事大纲，含角色描述）

   Output files:
   - projects/{project_id}/characters.json（角色数据）
   - projects/{project_id}/images/characters/（角色参考图）

   要求：
   1. 使用 character-consistency skill
   2. characters.json 必须符合 schemas/character.schema.json
   3. 每个角色必须有：
      - 完整 appearance 描述（gender/age_range/hair/eyes/build/clothing/accessories）
      - prompt_template（英文，用于所有分镜 Prompt 嵌入）
      - style_keywords（英文标签列表）
      - voice 配置（voice_type/speed/emotion_default）
   4. 每个角色生成一张参考图（正面全身），存入 images/characters/
   5. reference_images 字段指向生成的参考图路径
   6. 调用 image_generate.py 生成参考图：
      python scripts/image_generate.py --config '{"prompt": "...", "output_dir": "projects/{project_id}/images/characters", "engine": "dalle"}'
   ```

3. **验证产出**：
   - `characters.json` 存在且合法
   - 每个角色有 `prompt_template`（非空字符串）
   - 每个角色有 `reference_images`（至少 1 张图片路径，文件存在）
   - 图片文件实际存在且 > 0 bytes

4. **写入数据库**：
   ```bash
   # 为每个角色执行
   python scripts/db_manager.py --action save_character --data '{...}'
   python scripts/db_manager.py --action log_generation --data '{"project_id": "...", "stage": "character_design", ...}'
   python scripts/db_manager.py --action update_status --data '{"project_id": "...", "status": "designed"}'
   ```

5. **向用户展示结果**：
   - 角色列表（名称 + 外观关键词）
   - 角色参考图路径（用户可查看）

6. **提示下一步**：告知用户可以使用 `/generate-video` 开始生成视频片段。

## 注意事项

- 角色参考图质量直接影响后续视频一致性，如果质量不好要重新生成
- prompt_template 必须是英文，会被嵌入到每个分镜的图片/视频 Prompt 中
- 如果 OPENAI_API_KEY 未配置且不用 SD，参考图生成会失败
