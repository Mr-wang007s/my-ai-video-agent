---
name: import-script
description: "Step 2: 导入剧本 — 接收用户剧本 .txt 文件，自动提取摘要和角色列表"
---

## 前置条件

- 项目已创建（`/init-project` 完成），状态为 `draft`
- 用户提供了 `.txt` 格式的剧本/小说文件路径

## 必须加载的 Skill

```
use_skill("manga-script")
```

## 执行步骤

1. **获取参数**：
   - `project_id`：项目 ID
   - `script_path`：用户提供的 .txt 文件路径

2. **验证前置条件**：
   ```
   MCP tool: project_get(project_id)
   ```
   确认项目存在且状态为 `draft`。

3. **执行导入**：
   ```
   MCP tool: script_import(project_id, script_path)
   ```
   自动完成：读取 .txt → 复制到 raw_script.txt → 输出统计

4. **获取文本**：
   ```
   MCP tool: script_text(project_id, max_length=50000)
   ```

5. **提取摘要和角色**：基于 manga-script skill 知识，从文本中提取：
   - 故事摘要（MovieScript）
   - 角色列表（Character）
   - 角色关系（Relationships）
   - 写入 `projects/{project_id}/script_synopsis.json`

6. **更新状态**：
   ```
   MCP tool: project_update_status(project_id, status="imported")
   ```

7. **记录日志**：
   ```
   MCP tool: generation_log(project_id, stage="import", status="success")
   ```

8. **向用户展示结果**并提示下一步：`/extract-characters`

## 注意事项

- 支持 UTF-8、GBK、GB2312 编码
- 原始文本完整保存在 `raw_script.txt` 中
