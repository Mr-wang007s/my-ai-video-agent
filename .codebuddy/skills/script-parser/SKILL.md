---
name: script-parser
description: "剧本解析与编剧拆解。将原始文本导入、解析为 script_synopsis.json，并通过 Layer 1 screenwriterCoT 拆解为 Sub-Scripts。涵盖 Step 2（导入剧本）和 Step 4a（编剧拆解）。"
team:
  enabled: false
---

# 剧本解析与编剧拆解

从原始文本到结构化剧本数据的智能解析引擎。合并"导入解析"（Step 2）和"编剧拆解"（Step 4a）到同一 Skill，因为它们共享相同的输入（原始文本）和领域知识（叙事结构分析）。

## 核心原则

1. **文本忠实**：分层过程不修改原始剧本文本，仅做结构化拆解。摘要保留核心冲突和所有主要角色关键行为，不添加原文中没有的情节。
2. **分层独立**：Layer 1 screenwriterCoT 使用独立上下文执行，不与其他层共享历史（`use_history=False`）。
3. **CoT 强制推理**：Layer 1 必须先输出 `Internal Chain-of-Thought`（5 步），再输出结构化结果。
4. **题材感知**：通过题材识别矩阵自动推荐镜头策略和情绪模板，影响下游 Layer 2/3 的创作方向。
5. **角色弧线完整性**：Character Arc Blueprint 确保每个主角跨越完整故事有≥3 个情绪状态节点。

---

## Step 2: 剧本导入与解析

### 2.1 文本预处理

导入用户提供的 `.txt` 文件后：

1. 检测文件编码（支持 UTF-8、GBK、GB2312）
2. 清理格式（去除多余空行、特殊字符）
3. 统计字数，评估内容长度
4. 保存原始文本到 `projects/{project_id}/raw_script.txt`

### 2.2 故事摘要提取

从完整文本中提取核心叙事摘要（MovieScript 字段）：

**提取策略**：
- **短文本**（<5000字）：直接提取核心情节线
- **中等文本**（5000-50000字）：按章节提取关键情节，压缩为 150-500 词摘要
- **长文本**（>50000字）：分段提取 -> 合并 -> 精炼为 150-500 词摘要

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

### 2.3 角色提取

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

### 2.4 题材识别矩阵

根据文本特征自动判断故事类型，并推荐镜头策略和情绪模板，影响下游 Layer 2/3 创作方向：

| 文本特征 | 推断类型 | 推荐画面风格 | 镜头策略 | 情绪模板 |
|----------|---------|-------------|---------|---------|
| 修仙/武侠元素、功法、境界 | 奇幻 | manga / anime | 大量全景+动作镜头，特效密集 | 铺垫(20%)沉稳 -> 修炼/战斗(50%)渐强 -> 突破/对决(20%)爆发 -> 感悟(10%)回落 |
| 现代都市/办公/商战场景 | 都市 | manga / realistic | 中景对话为主，穿插特写表情 | 日常(15%)平缓 -> 冲突酝酿(35%)渐紧 -> 爆发/反转(30%)高峰 -> 和解/留白(20%)舒缓 |
| 校园/青春/恋爱元素 | 校园 | manga / anime | 近景特写多，柔光滤镜感 | 相遇(20%)清新 -> 靠近(30%)甜蜜渐升 -> 误解/分离(30%)低谷 -> 重逢(20%)温暖 |
| 悬疑/推理/犯罪元素 | 悬疑 | comic / manga | 暗调光影，大量特写+主观镜头 | 谜面(25%)压抑 -> 调查(35%)紧张递进 -> 真相(25%)震撼爆发 -> 余波(15%)沉思 |
| 科技/太空/未来设定 | 科幻 | anime / comic | 广角全景展示世界观+科技特写 | 世界观(20%)宏大 -> 冒险(35%)紧凑 -> 危机(30%)极度紧张 -> 新秩序(15%)开阔 |
| 古装/宫廷/朝堂元素 | 古装 | manga / realistic | 对称构图，仪式感远景+心理特写 | 布局(25%)沉稳 -> 博弈(35%)暗流涌动 -> 翻盘(25%)剧烈 -> 定局(15%)唏嘘 |

**使用方式**：
1. 在 Step 2 摘要提取时同步识别题材
2. 将识别结果写入 `script_synopsis.json` 的 `genre` 字段
3. 同时生成 `shot_strategy` 和 `emotion_template` 字段供下游参考
4. Layer 1 的 Sub-Script Timeline 标注应参考对应情绪模板的节奏分布

### 2.5 输出格式：script_synopsis.json

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
  "shot_strategy": "镜头策略描述（来自题材识别矩阵）",
  "emotion_template": "情绪模板描述（来自题材识别矩阵）",
  "extracted_at": "2026-02-27T10:00:00Z"
}
```

**注意事项**：
- `Character` 数组只包含角色名（字符串），不包含描述
- `MovieScript` 是纯叙事文本，不是结构化数据
- `Relationships` 的键格式为 "角色A - 角色B"（用 " - " 连接）
- `title` 如果原文有标题则提取，否则由 AI 根据内容命名
- `genre`、`shot_strategy`、`emotion_template` 来自题材识别矩阵

---

## Step 4a: Layer 1 screenwriterCoT（编剧拆解）

### System Prompt 模板

```
You are a professional screenwriter specialized in breaking down movie scripts into structured sub-scripts.

Your task: Given a Script Synopsis and Character list, break the story into sequential Sub-Scripts (chapters/acts).

## MANDATORY OUTPUT FORMAT

You MUST output a JSON object with the following structure:

{
  "Relationships": { "Character A - Character B": "Relationship description", ... },
  "Internal Chain-of-Thought": {
    "Step 1: Core Narrative Structure": "Analyze the overall narrative arc (setup, confrontation, resolution)...",
    "Step 2: Key Character Information": "Identify main/supporting characters and their motivations...",
    "Step 3: Temporal Segmentation": "Identify natural breaking points in the timeline...",
    "Step 4: Sub-Script Breakdown Criteria": "Each sub-script should represent a coherent narrative unit with ≥50 words...",
    "Step 5: Division Rationale": "Explain why each division point was chosen..."
  },
  "Character Arc Blueprint": {
    "Character A": {
      "Sub-Script 1": "Emotional state and narrative role at this stage",
      "Sub-Script N": "Emotional state and narrative role at this stage"
    },
    "Character B": { ... }
  },
  "Sub-Script": {
    "Sub-Script 1": {
      "Plot": "Detailed plot description (≥50 words, preserve original narrative)",
      "Involving Characters": ["Character A", "Character B"],
      "Timeline": "Beginning | Middle | Climax | End | Resolution",
      "Reason for Division": "Why this segment forms a natural unit"
    },
    "Sub-Script 2": { ... },
    ...
  }
}

## CONSTRAINTS

1. Total Sub-Scripts ≤ 20
2. Each Sub-Script Plot ≥ 50 words
3. Preserve original text — do NOT rephrase or summarize the script content
4. Timeline must follow chronological order
5. Every character in the Character list must appear in at least one Sub-Script
6. Relationships must cover all significant character pairs
7. Internal Chain-of-Thought is MANDATORY — you must think before outputting results
8. Character Arc Blueprint MUST cover every main character across every Sub-Script they appear in
9. Each arc entry must describe the character's emotional state and narrative function at that stage
```

### User Prompt 模板

```
Script Synopsis: {movie_script}
Character: {character_list}
```

### Character Arc Blueprint 质量标准

Character Arc Blueprint 是 Layer 1 的关键质量指标，确保角色发展在后续层级中得到一致体现：

| 规则 | 要求 | 校验方式 |
|------|------|---------|
| 主角覆盖 | 每个主要角色必须出现在 Blueprint 中 | 与 Character 列表交叉检查 |
| 情绪节点数 | 每个主角 ≥ 3 个情绪状态节点（跨不同 Sub-Script） | 计数每个角色的 Sub-Script 条目数 |
| 情绪变化 | 相邻节点的情绪状态不能完全相同（角色需要发展） | 逐对比较相邻条目文本 |
| 叙事功能 | 每个节点必须同时描述情绪状态和叙事功能 | 检查条目是否包含两个维度 |
| 弧线完整性 | 至少覆盖 Beginning 和 End 阶段的 Sub-Script | 检查首尾 Sub-Script 是否有条目 |

**校验失败处理**：
- 如果主角情绪节点 < 3，要求重新生成并补充缺失的弧线节点
- 最多重试 2 次，仍不合格则记录警告并继续

### 输出写入

写入 `projects/{project_id}/script_breakdown.json` 的根层级：
- `Relationships`：角色关系图
- `Internal Chain-of-Thought`：Layer 1 的 5 步推理过程
- `Character Arc Blueprint`：角色弧线蓝图
- `Sub-Script`：拆解后的章节/幕

---

## 数据流图

```
用户 .txt 文件
    │
    ▼
[Step 2: 文本预处理]
    │  检测编码 → 清理格式 → 统计字数
    │  题材识别矩阵 → genre + shot_strategy + emotion_template
    ▼
projects/{project_id}/raw_script.txt
    │
    ├──► [Step 2: 摘要提取] ──► script_synopsis.json
    │       MovieScript + Character + Relationships
    │       + genre + shot_strategy + emotion_template
    │
    └──► [Step 2: 角色提取] ──► script_synopsis.json (Character + Relationships)
              │
              ▼
         → /extract-characters (Step 3a, 由 character-design Skill 处理)
              │
              ▼
[Step 4a: Layer 1 screenwriterCoT]
    │  输入: script_synopsis.json 中的 MovieScript + Character
    │  独立上下文执行 (use_history=False)
    │  5 步 CoT 推理
    ▼
projects/{project_id}/script_breakdown.json (根层级)
    │  Relationships + CoT + Character Arc Blueprint + Sub-Scripts
    │
    └──► → /break-script Layer 2 (Step 4b, 由 script-scene Skill 处理)
```

---

## 数据存储

所有数据 I/O 使用 CodeBuddy 原生 Read/Write 工具：

| 产物 | 路径 | 说明 |
|------|------|------|
| 原始文本 | `projects/{project_id}/raw_script.txt` | 用户提供的原始剧本文本 |
| 解析摘要 | `projects/{project_id}/script_synopsis.json` | 摘要 + 角色 + 关系 + 题材 |
| 编剧拆解 | `projects/{project_id}/script_breakdown.json` | Layer 1 输出（根层级） |

---

## 与下游流程的关系

### -> /extract-characters（Step 3a）
`script_synopsis.json` 中的 `Character` 列表 + `raw_script.txt` 原文用于提取每个角色的详细信息，输出 `characters.json`。

### -> /break-script Layer 2（Step 4b）
`script_breakdown.json` 中的 `Sub-Script` 列表逐个输入 ScenePlanningCoT，进行场景规划。`Character Arc Blueprint` 传递给 Layer 2 作为角色情绪参考。

### -> 题材信息传递
`script_synopsis.json` 中的 `shot_strategy` 和 `emotion_template` 被 Layer 2/3 参考，影响镜头类型选择和节奏设计。

---

## 质量检查清单

### Step 2 导入解析
- [ ] 文件编码正确检测并转换为 UTF-8
- [ ] raw_script.txt 内容完整，无乱码
- [ ] MovieScript 摘要 150-500 词，按时间线叙述
- [ ] Character 列表包含所有有名角色
- [ ] Relationships 覆盖所有重要角色对
- [ ] genre 题材识别合理，shot_strategy 和 emotion_template 已生成
- [ ] script_synopsis.json 符合 schema 规范

### Step 4a Layer 1 编剧拆解
- [ ] Internal Chain-of-Thought 包含完整 5 步推理
- [ ] 每步有实质性分析内容（≥2 句）
- [ ] Sub-Scripts 总数 ≤ 20
- [ ] 每个 Sub-Script Plot ≥ 50 词
- [ ] Timeline 按时间顺序标注
- [ ] 每个 Character 列表中的角色至少出现在一个 Sub-Script 中
- [ ] Character Arc Blueprint 覆盖所有主角
- [ ] 每个主角 ≥ 3 个情绪状态节点
- [ ] 相邻情绪节点有实质性变化
- [ ] script_breakdown.json 根层级结构正确
