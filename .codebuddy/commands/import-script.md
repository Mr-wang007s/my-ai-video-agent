---
name: import-script
description: "Step 2: 导入剧本 — 接收用户剧本 .txt 文件，自动提取摘要和角色列表"
---

## 前置条件

- 项目已创建（`/init-project` 完成），状态为 `draft`
- 用户提供了 `.txt` 格式的剧本/小说文件路径

## 必须加载的 Skill

```
use_skill("script-parser")
```

## 执行步骤

1. **获取参数**：
   - `project_id`：项目 ID
   - `script_path`：用户提供的 .txt 文件路径

2. **验证前置条件**：
   ```
   Read: projects/{project_id}/status.json
   ```
   确认项目存在且状态为 `draft`。

3. **导入剧本文件**：
   ```
   Read: {script_path}  ← 读取用户提供的 .txt 文件
   Write: projects/{project_id}/raw_script.txt  ← 复制原始文本
   ```

4. **统计脚本信息**：计算字数、段落数、对白行数等基本统计。

5. **提取摘要和角色**：基于 script-parser skill 知识，从文本中提取：
   - 故事摘要（MovieScript）
   - 角色列表（Character）
   - 角色关系（Relationships）
   ```
   Write: projects/{project_id}/script_synopsis.json
   ```

6. **更新状态**：
   ```
   Write: projects/{project_id}/status.json  ← {"status": "imported", "updated_at": "..."}
   ```

7. **向用户展示结果**并提示下一步：`/extract-characters`

## 注意事项

- 支持 UTF-8、GBK、GB2312 编码
- 原始文本完整保存在 `raw_script.txt` 中
- 所有数据通过文件系统读写，不依赖 MCP 或数据库
