---
name: extract-characters
description: "Step 3a: 提取角色 — 从剧本自动提取所有角色信息，写入 characters.json，不生成图片"
---

## 前置条件

- 项目状态为 `imported`（`/import-script` 已完成）
- `projects/{project_id}/script_synopsis.json` 已存在
- `projects/{project_id}/raw_script.txt` 已存在

## 执行步骤

1. **验证前置条件**：
   ```bash
   python scripts/db_manager.py --action get_project --data '{"project_id": "{project_id}"}'
   ```
   确认状态为 `imported`。

2. **读取输入**：
   ```
   Read: projects/{project_id}/script_synopsis.json
   Read: projects/{project_id}/raw_script.txt
   ```

3. **提取角色信息**：Director 直接执行（纯文本分析），对 Character 列表中的每个角色，从原文提取：
   - **名称**：原文中使用的称呼
   - **描述**：性格、背景、在故事中的作用（中文）
   - **外观描述**：从文本推断的发型、服装、体型、显著特征等（中文）
   - **角色关系**：与其他角色的关系列表
   - **配音设置**：根据角色性别/年龄推断 voice_type、speed、emotion_default
   - **风格关键词**：用于图像生成的英文标签

4. **写入 characters.json**：

   遵循 `schemas/character_list.schema.json`：

   ```json
   {
     "project_id": "{project_id}",
     "extracted_from": "script_synopsis.json",
     "extracted_at": "ISO timestamp",
     "characters": [
       {
         "name": "小王",
         "description": "28岁的程序员，性格内向但正义感强...",
         "appearance_description": "短发，戴黑框眼镜，经常穿格子衬衫...",
         "tok_description": "",
         "relationships": [
           {"character": "小李", "relation": "同事兼好友"}
         ],
         "design_status": "extracted",
         "asset_dir": "",
         "voice": {"voice_type": "young_male", "speed": 1.0, "emotion_default": "neutral"},
         "style_keywords": ["programmer", "glasses", "casual"]
       }
     ]
   }
   ```

   **所有角色 `design_status` 初始为 `extracted`**。

5. **更新状态**：
   ```bash
   python scripts/db_manager.py --action update_status --data '{"project_id": "{project_id}", "status": "characters_extracted"}'
   ```

6. **向用户展示结果**：
   - 角色清单表格（名称、描述、外观特征、关系）
   - 总角色数
   - 区分主要/次要角色

7. **提示下一步**：
   - 使用 `/design-characters {角色名}` 逐个设计角色外观
   - 使用 `/design-characters` 查看所有角色设计状态
   - 使用 `/design-characters all` 批量设计所有角色
   - 建议先设计主要角色，次要角色按需设计

## 注意事项

- **不消耗图像 API**：此步骤纯文本分析，不生成任何图片
- 外观描述可能不完整（小说中未详细描述的角色），用户可在设计时补充
- 角色关系来自 `script_synopsis.json` 的 `Relationships` + 原文补充
- 如果原文缺乏外观描述，设置基本描述并在 `appearance_description` 中标注"待用户补充"
