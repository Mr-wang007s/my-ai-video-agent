---
name: extract-characters
description: "Step 3a: 提取角色 — 从剧本自动提取所有角色信息，写入 characters.json，不生成图片"
---

## 前置条件

- 项目状态为 `imported`
- `projects/{project_id}/script_synopsis.json` 已存在

## 必须加载的 Skill

```
use_skill("manga-script")
```

## 执行步骤

1. **验证前置条件**：
   ```
   MCP tool: project_get(project_id)
   ```
   确认状态为 `imported`。

2. **读取输入**：
   ```
   Read: projects/{project_id}/script_synopsis.json
   Read: projects/{project_id}/raw_script.txt
   ```

3. **提取角色信息**：主对话直接执行（纯文本分析），对每个角色提取：
   - 名称、描述、外观描述、角色关系、配音设置、风格关键词
   - 所有角色 `design_status` 初始为 `extracted`

4. **写入 characters.json** 并保存到数据库：
   ```
   MCP tool: character_save(project_id, name, description, appearance, reference_images="[]", style_keywords="[]")
   ```
   对每个角色调用一次。同时写入 `projects/{project_id}/characters.json`。

5. **更新状态**：
   ```
   MCP tool: project_update_status(project_id, status="characters_extracted")
   ```

6. **向用户展示结果**并提示下一步：
   - `/design-characters {角色名}` 逐个设计
   - `/design-characters all` 批量设计

## 注意事项

- **不消耗图像 API**：纯文本分析
- 外观描述不完整时标注"待用户补充"
