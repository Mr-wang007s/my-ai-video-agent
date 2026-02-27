---
name: manga-script
description: 剧本导入与解析指南。当需要从完整小说/剧本文本中提取故事摘要和角色列表、生成 script_synopsis.json 时，应使用此 Skill。
---

# 剧本导入与解析

提供从完整小说/剧本文本中提取故事摘要、角色列表和关系图谱的方法论，输出 MovieAgent 兼容的 `script_synopsis.json` 格式。

## 剧本导入流程

### 1. 文本预处理

导入用户提供的 `.txt` 文件后：

1. 检测文件编码（支持 UTF-8、GBK、GB2312）
2. 清理格式（去除多余空行、特殊字符）
3. 统计字数，评估内容长度
4. 保存原始文本到 `projects/{project_id}/raw_script.txt`

### 2. 故事摘要提取

从完整文本中提取核心叙事摘要（MovieScript 字段）：

**提取策略**：
- **短文本**（<5000字）：直接提取核心情节线
- **中等文本**（5000-50000字）：按章节提取关键情节，压缩为 150-500 词摘要
- **长文本**（>50000字）：分段提取 → 合并 → 精炼为 150-500 词摘要

**摘要要求**：
- 150-500 词（英文或对应中文长度）
- 保留核心冲突和主要转折点
- 包含所有主要角色的出场和关键行为
- 按时间线顺序叙述
- 不添加原文中没有的情节

**Prompt 模板**：
```
请阅读以下小说/剧本文本，提取核心故事摘要。

要求：
1. 摘要长度：150-500词
2. 按时间线顺序叙述主要情节
3. 保留所有主要角色的关键行为
4. 保留核心冲突和主要转折点
5. 不添加原文中没有的情节
6. 使用第三人称叙事

文本内容：
{raw_script_content}
```

### 3. 角色提取

从文本中识别所有有名字的角色：

**提取维度**：
- 角色名称（原文中使用的称呼）
- 出场频率（判断主要/次要角色）
- 角色关系

**Prompt 模板**：
```
请从以下文本中提取所有有名字的角色，并分析角色关系。

要求：
1. 列出所有有明确名字的角色
2. 区分主要角色和次要角色（根据出场频率和剧情重要性）
3. 分析角色之间的关系（亲属、朋友、对手、师徒等）
4. 关系格式："角色A - 角色B": "关系描述"

文本内容：
{raw_script_content}
```

### 4. 类型和风格判断

自动判断故事类型和适合的画面风格：

| 文本特征 | 推断类型 | 推荐风格 |
|----------|---------|---------|
| 修仙/武侠元素 | 奇幻 | manga / anime |
| 现代都市/办公场景 | 都市 | manga / realistic |
| 校园/青春 | 校园 | manga / anime |
| 悬疑/推理 | 悬疑 | comic / manga |
| 科技/太空 | 科幻 | anime / comic |

## 输出格式

### script_synopsis.json

严格遵循 `schemas/script_synopsis.schema.json`：

```json
{
  "MovieScript": "故事摘要（150-500词）...",
  "Character": ["角色A", "角色B", "角色C"],
  "Relationships": {
    "角色A - 角色B": "关系描述",
    "角色A - 角色C": "关系描述"
  },
  "raw_script_path": "raw_script.txt",
  "title": "故事标题",
  "genre": "故事类型",
  "extracted_at": "2026-02-27T10:00:00Z"
}
```

### 注意事项

- `Character` 数组只包含角色名（字符串），不包含描述
- `MovieScript` 是纯叙事文本，不是结构化数据
- `Relationships` 的键格式为 "角色A - 角色B"（用 " - " 连接）
- `title` 如果原文有标题则提取，否则由 AI 根据内容命名

## 与下游流程的关系

### → /extract-characters（Step 3a）

`script_synopsis.json` 中的 `Character` 列表 + `raw_script.txt` 原文用于提取每个角色的详细信息，输出 `characters.json`。

### → /break-script（Step 4）

`script_synopsis.json` 中的 `MovieScript` + `Character` 直接作为 screenwriterCoT 的输入，进行 Sub-Script 拆解。

## 数据存储

- 原始文本：`projects/{project_id}/raw_script.txt`
- 提取摘要：`projects/{project_id}/script_synopsis.json`

## 使用 import_script.py

导入脚本通过 Python 执行：

```bash
python scripts/import_script.py --action import --project_id {project_id} --script_path "{用户提供的.txt路径}"
```

脚本功能：
1. 读取 .txt 文件（自动检测编码）
2. 复制到 `projects/{project_id}/raw_script.txt`
3. 调用 LLM 提取摘要 + 角色列表
4. 输出 `script_synopsis.json`
5. 更新项目状态为 `imported`
