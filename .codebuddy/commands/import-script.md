---
name: import-script
description: "Step 2: 导入剧本 — 接收用户剧本 .txt 文件，自动提取摘要和角色列表"
---

## 前置条件

- 项目已创建（`/init-project` 完成），状态为 `draft`
- 用户提供了 `.txt` 格式的剧本/小说文件路径

## 执行步骤

1. **获取参数**：
   - `project_id`：项目 ID
   - `script_path`：用户提供的 .txt 文件路径（绝对路径或相对路径）

2. **验证前置条件**：
   ```bash
   python scripts/db_manager.py --action get_project --data '{"project_id": "{project_id}"}'
   ```
   确认项目存在且状态为 `draft`。

3. **执行导入**：
   ```bash
   python scripts/import_script.py --action import --project_id {project_id} --script_path "{script_path}"
   ```

   脚本自动完成：
   - 读取 .txt 文件（自动检测编码 UTF-8/GBK/GB2312）
   - 复制到 `projects/{project_id}/raw_script.txt`
   - 输出文本统计（字数、段落数）

4. **提取摘要和角色**：使用 manga-script skill 知识，基于 raw_script.txt 内容：
   - 提取故事摘要（MovieScript，150-500词叙事文本）
   - 提取角色列表（Character，所有有名字的角色）
   - 分析角色关系（Relationships）
   - 判断故事标题和类型

5. **写入 script_synopsis.json**：
   ```json
   {
     "MovieScript": "故事摘要...",
     "Character": ["角色A", "角色B", "角色C"],
     "Relationships": {
       "角色A - 角色B": "关系描述"
     },
     "raw_script_path": "raw_script.txt",
     "title": "故事标题",
     "genre": "故事类型",
     "extracted_at": "ISO timestamp"
   }
   ```

   写入 `projects/{project_id}/script_synopsis.json`。

6. **更新状态**：
   ```bash
   python scripts/db_manager.py --action update_status --data '{"project_id": "{project_id}", "status": "imported"}'
   ```

7. **向用户展示结果**：
   - 故事标题和类型
   - 摘要内容
   - 提取的角色列表
   - 角色关系图
   - 原文字数统计

8. **等待用户确认**：如果用户觉得摘要不准确或遗漏了角色，可以手动修改 `script_synopsis.json`。

9. **提示下一步**：执行 `/extract-characters` 提取角色详细信息。

## 注意事项

- 支持 UTF-8、GBK、GB2312 编码
- 长文本（>50000字）会分段提取后合并
- 原始文本始终完整保存在 `raw_script.txt` 中
- 摘要提取使用 LLM，需要 API KEY 配置
