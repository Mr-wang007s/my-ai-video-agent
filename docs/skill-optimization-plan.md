# Skill 优化设计方案

> 综合工程师、制片人、导演、视觉设计、演员五个专业视角的审查意见，重新设计模块化 Skill 体系。

---

## 零、MCP 在当前阶段的作用评估

### 结论：MCP 是轻量辅助，非核心瓶颈——从 Skill 中移除 MCP 调用指引

### 评估分析

当前 MCP Server（`manga-agent`）暴露 16 个工具，逐一评估：

| MCP Tool | 实际功能 | CodeBuddy 原生替代 | 评估 |
|----------|---------|-------------------|------|
| `project_init_db` | 初始化 SQLite 表 | `Bash: python scripts/db_manager.py --action init_db` | **可替代** |
| `project_create` | 创建项目 + 目录 | `Bash: mkdir` + `Write: JSON` | **可替代** |
| `project_list` | 查询项目列表 | `Read: data.db` 或 Bash 查询 | **可替代** |
| `project_get` | 查询单个项目 | 同上 | **可替代** |
| `project_update_status` | 更新状态字段 | `Bash: sqlite3` 或脚本调用 | **可替代** |
| `project_summary` | 聚合统计 | Bash 查询 | **可替代** |
| `script_import` | 编码检测 + 复制 txt | `Read` + `Write`（CodeBuddy 原生支持编码） | **可替代** |
| `script_stats` | 文本统计 | LLM 直接计算或 `Bash: wc` | **可替代** |
| `script_text` | 读取文本 | `Read` 工具直接读取 | **完全冗余** |
| `character_save` | 写入 characters 表 | `Bash: sqlite3` 或直接写 JSON 文件 | **可替代** |
| `character_list` | 查询角色列表 | 同上 | **可替代** |
| `asset_save` | 写入 assets 表 | `Bash: sqlite3` | **可替代** |
| `asset_list` | 查询资产列表 | 同上 | **可替代** |
| `generation_log` | 写入日志表 | `Bash: sqlite3` | **可替代** |
| `export_storyboard_markdown` | 导出 Markdown | `export_storyboard.py` 本身只是字符串拼接，LLM 也能做 | **可替代** |

### 核心发现

**当前 MCP 工具做的全部是「数据搬运」**——读写 SQLite、复制文件、拼接字符串。这些操作：

1. **CodeBuddy 原生工具都能做**：`Read`/`Write`/`Bash` 覆盖所有 I/O 操作
2. **无 AI 推理**：MCP 工具内部没有调用任何 LLM/AI 模型，纯 Python CRUD
3. **pipeline 的核心价值全在 Skill**：三层 CoT 拆解、角色设计、Prompt 生成——这些全由 LLM 在主对话中通过 Skill 指导完成
4. **MCP 启动有成本**：需要 Python 环境、依赖安装、stdio 通信开销

### 决策

| 项目 | 处理方式 |
|------|---------|
| MCP Server 代码 | **保留但不在 Skill 中引用**——作为可选的工程化接口 |
| Skill 中的 MCP 调用指引 | **全部移除**——Skill 只聚焦领域知识和 Prompt 模板 |
| `pipeline-dispatch` rule 中的 MCP 映射 | **简化**——仅保留状态机流转，去掉 MCP tool 指定 |
| 数据操作 | **改用文件系统 + JSON**——`projects/{id}/` 目录是天然的数据库 |

### Skill 的本质角色重新定义

Skill = **LLM 的领域知识包**（Prompt 模板 + 专业词汇 + 质量标准 + 决策规则）

Skill **不应该**包含：
- 具体的 MCP tool 调用代码
- 数据库操作指引
- 文件系统操作步骤
- 工程化实现细节

Skill **应该**包含：
- System/User Prompt 模板
- 专业领域词汇表（镜头/运镜/情绪/色彩...）
- 质量标准和校验规则
- 输入/输出的数据 Schema
- 决策树和选择矩阵

---

## 一、现有问题诊断

### 工程师视角 (Engineer)
| 问题 | 严重程度 | 说明 |
|------|---------|------|
| Skill/Rule 边界混淆 | **高** | `character-consistency` 同时存在于 skills 和 rules，职责重叠 |
| 模块边界模糊 | **高** | `script-breakdown` 和 `storyboard-design` 内容高度交叉（都涉及 Shot 设计） |
| 平台耦合 | **中** | `seedance-video` 绑定单一平台，但 prompt 工程是通用能力 |
| 缺少通用 prompt 模块 | **中** | image_prompt / video_prompt / audio_prompt 的构造规范散落在 3 个 skill 中 |
| 缺少输出/导出优化 | **低** | 导出阶段无专用 skill 指导最终交付物质量 |
| 数据合约不明确 | **中** | skill 之间的输入/输出接口缺少显式定义 |

### 制片人视角 (Producer)
| 问题 | 严重程度 | 说明 |
|------|---------|------|
| 缺少质量关卡 | **高** | 各步骤之间缺少明确的验收标准和质量检查点 |
| 成本控制分散 | **中** | 成本意识仅在 rule 中，未融入 skill 的生成决策 |
| 缺少预览/审批环节 | **高** | 三层拆解直接输出，无预览和修订循环 |
| 资产管理不完整 | **中** | 仅覆盖角色资产，缺少场景/道具/特效的资产管理 |
| 并行工作机会未挖掘 | **低** | Layer 2 各 Sub-Script 可并行，但未有专门优化 |

### 导演视角 (Director)
| 问题 | 严重程度 | 说明 |
|------|---------|------|
| 缺少"导演构想"层 | **高** | 从剧本到分镜缺少整体视觉构想（Visual Concept）阶段 |
| 镜头语法词汇贫乏 | **中** | 仅 9 种镜头类型 + 9 种运镜，远不够表达丰富的电影语言 |
| 情绪节奏过于机械 | **中** | 固定 4 阶段(20/40/25/15%)不适用于所有题材 |
| 缺少转场设计 | **中** | 转场仅有 cut/fade/dissolve/wipe，缺少叙事性转场（match cut 等） |
| 缺少场景氛围设计 | **中** | Layer 2 的 Scene Description 过于简略，缺少 mise-en-scene 指导 |
| 缺少题材适配 | **中** | 不同题材（动作/言情/悬疑/喜剧）应有不同的镜头策略 |

### 视觉设计视角 (Visual Designer)
| 问题 | 严重程度 | 说明 |
|------|---------|------|
| 缺少全局美术风格定义 | **高** | 无项目级 art style guide，风格一致性靠隐式约定 |
| image_prompt 质量不足 | **高** | 当前模板过于简单，缺少构图/光影/色彩的系统指导 |
| 平台差异未处理 | **中** | Gemini / DALL-E / SD / 可灵各平台的 prompt 风格差异大 |
| 角色设计维度单一 | **中** | 仅有外观描述，缺少表情库、动作库、签名姿势 |
| 色彩体系缺失 | **中** | 无项目级调色方案，各镜头色调可能不一致 |
| negative prompt 过于通用 | **低** | 所有镜头共用同一个 negative prompt 模板 |

### 演员视角 (Actor)
| 问题 | 严重程度 | 说明 |
|------|---------|------|
| 角色只有"皮"没有"魂" | **高** | 仅有视觉外观（<TOK>），缺少性格、习惯、情感模式 |
| 对白缺少表演指导 | **高** | audio_prompt 只有简单情绪标签，缺少节奏/停顿/重音 |
| 缺少角色弧线追踪 | **中** | Layer 1 的 Character Arc Blueprint 未贯穿到 Layer 3 |
| 肢体语言词汇贫乏 | **中** | 动作描述偏通用，缺少角色个性化的肢体表达 |
| 角色互动设计缺失 | **中** | 多角色同框时仅有空间位置（bounding box），无互动动态 |
| 语音设计过于基础 | **低** | voice_type 仅 6 种，不足以区分同类型角色 |

---

## 二、优化后的 Skill 体系（10 个 Skill）

### 按核心功能分组

```
                        ┌─────────────────────────────────────────────┐
                        │          漫剧制作流水线 Skill 体系            │
                        └─────────────────────────────────────────────┘

 ┌─────────── script 剧本模块 ─────┐  ┌────────── character 角色模块 ───┐
 │  1. script-parser               │  │  3. character-design            │
 │  2. script-scene                │  │  4. character-acting            │
 └─────────────────────────────────┘  └─────────────────────────────────┘

 ┌─────────── shot 分镜模块 ───────┐  ┌────────── prompt 生成模块 ──────┐
 │  5. shot-director               │  │  7. prompt-image                │
 │  6. shot-rhythm                 │  │  8. prompt-video                │
 └─────────────────────────────────┘  │  9. prompt-audio                │
                                      └─────────────────────────────────┘
                  ┌─────────── export 工程模块 ────┐
                  │  10. export-render              │
                  └────────────────────────────────┘
```

---

### Skill 1: `script-parser`（剧本解析） <sub>script 模块</sub>

> 从原始文本到结构化剧本数据的智能解析引擎

**替代**: 现 `manga-script` + `script-breakdown` Layer 1

**职责**:
- 文本预处理（编码检测、格式清理、字数统计）
- 故事摘要提取（MovieScript，150-500 词）
- 角色列表与关系图谱提取
- 题材/风格自动判断
- Layer 1 screenwriterCoT 执行（Script → Sub-Scripts）
- Character Arc Blueprint 生成
- `script_synopsis.json` + `script_breakdown.json` 根层级输出

**输入**: `raw_script.txt`（用户提供的 .txt 文件）

**输出**:
- `script_synopsis.json`（摘要 + 角色列表 + 关系）
- `script_breakdown.json` 根层级（Relationships + CoT + Sub-Scripts + Character Arc Blueprint）

**Pipeline Steps**: Step 2 (import-script) + Step 4a (Layer 1 breakdown)

**关键改进**:
- 合并"导入解析"和"编剧拆解"到同一 skill，因为它们共享相同的输入（原始文本）和领域知识（叙事结构分析）
- Layer 1 screenwriterCoT 的 System Prompt 模板完整保留
- 新增: **题材识别矩阵**——根据文本特征自动推荐镜头策略和情绪模板
- 新增: **Character Arc Blueprint 质量标准**——每个主角必须有≥3个情绪状态节点
- **移除**: MCP tool 调用指引（`script_import`/`script_text` 等）——数据 I/O 由主对话的原生工具完成

**CoT 要求**: Layer 1 的 5 步 CoT 完整保留（遵循 cot-reasoning rule）

---

### Skill 2: `script-scene`（场景建筑师） <sub>script 模块</sub>

> 将 Sub-Script 转化为电影级场景设计，包含空间、光影、氛围的完整 mise-en-scene

**替代**: 现 `script-breakdown` Layer 2 + `storyboard-design` 的场景级内容

**职责**:
- Layer 2 ScenePlanningCoT 执行（Sub-Script → Scenes）
- 场景空间设计（环境、建筑、天气、时间）
- **光影设计**（光源方向、色温、明暗对比、光影情绪）
- **色彩方案**（场景主色调、辅色、强调色，参考色彩心理学）
- 道具与布景规划（Key Props 升级为完整布景清单）
- 场景间转场设计（叙事性转场：match cut, J-cut, L-cut, smash cut）
- 情绪基调定义（从 Scene 粒度细化到 beat 粒度）
- Visual Style 定义（每个场景的美术方向笔记）

**输入**: `script_breakdown.json`（含 Sub-Scripts）+ `characters.json`

**输出**: 每个 Sub-Script 的 `Scene Annotation`（嵌套写入 `script_breakdown.json`）

**Pipeline Steps**: Step 4b (Layer 2 breakdown)

**关键改进**:
- **新增光影设计体系**:

| 情绪 | 光影方案 | 色温 | 示例 |
|------|---------|------|------|
| 温暖/幸福 | 柔光，黄金时段 | 暖色 (3000-4000K) | 夕阳下的重逢 |
| 紧张/危机 | 硬光，高对比 | 冷色 (5500-7000K) | 审讯室/对峙 |
| 神秘/魔幻 | 侧光/逆光，环境光 | 冷暖混合 | 魔法场景 |
| 悲伤/孤独 | 低调光，大面积阴影 | 冷色偏蓝 | 雨中独行 |
| 日常/中性 | 散射光，自然 | 中性 (5000K) | 教室/办公室 |

- **新增转场设计词汇**:

| 转场 | 英文 | 效果 | 使用场景 |
|------|------|------|----------|
| 直切 | Cut | 标准，快节奏 | 同场景内 |
| 淡入淡出 | Fade | 时间流逝 | 场景切换 |
| 溶解 | Dissolve | 柔和过渡 | 回忆/梦境 |
| 匹配切 | Match cut | 视觉连接 | 物体/动作呼应 |
| J-cut | J-cut | 先闻其声 | 预知下一场景 |
| 闪白 | Whiteout | 强烈冲击 | 爆炸/觉醒 |
| 跳切 | Jump cut | 时间压缩 | 同角色不同时间 |

- **新增色彩方案模板**: 每场景输出 `color_palette: {primary, secondary, accent}` 字段

**CoT 要求**: Layer 2 的 4 步 CoT 完整保留，新增 Step 5: Lighting & Color Design

---

### Skill 3: `character-design`（角色设计） <sub>character 模块</sub>

> 角色视觉身份的完整定义，从外观到参考图生成的全链路

**替代**: 现 `character-consistency` 的设计部分

**职责**:
- 角色信息提取（从剧本文本中识别角色及其外观/性格）
- `characters.json` 构建（完整的角色数据结构）
- `<TOK>` 外观描述构建（best.txt）
- `character_list/` 目录规范和管理
- 角色参考图 Prompt 生成（供用户在 Gemini/DALL-E 手动生成）
- **角色视觉识别系统** (Character Visual Identity):
  - 签名姿势（Signature Pose）
  - 标志性表情（Signature Expression）
  - 体型/比例定义
  - 服装设计体系（日常/正式/战斗等不同场景的着装方案）
- 多角色视觉区分（确保角色在画面中可识别、不混淆）
- bounding box 规范

**输入**: `raw_script.txt` + `script_synopsis.json`

**输出**:
- `characters.json`（完整角色信息）
- `character_list/{CharName}/best.txt`（<TOK> 描述）
- 用户操作指引：Gemini Prompt（用于生成 best.png + multi-angle photos）

**Pipeline Steps**: Step 3a (extract-characters) + Step 3b (design-characters)

**关键改进**:
- **新增角色视觉识别卡 (Character Visual ID Card)**:

```json
{
  "name": "Elsa",
  "tok_description": "<TOK> has long platinum blonde hair in a single braid ...",
  "signature_pose": "hands raised with ice crystals forming between fingers",
  "signature_expression": "serene confidence with a hint of melancholy",
  "body_proportions": "tall, slender, graceful, regal posture",
  "wardrobe": {
    "default": "flowing ice-blue dress with snowflake patterns",
    "casual": "light blue blouse with white pants",
    "battle": "crystalline armor with cape of frost"
  },
  "visual_identifiers": ["ice crystal motifs", "blue color palette", "braid over left shoulder"],
  "distinguishing_features": "pointed ears from her winter crown, always bare feet on ice"
}
```

- **新增参考图质量标准**: best.png 必须清晰展示所有 `visual_identifiers`
- **新增多角度参考图规范**: 增加 3/4 背面视角 + 表情变化图

---

### Skill 4: `character-acting`（角色表演） <sub>character 模块</sub>

> 角色的内在灵魂——性格、情感、表演指导、对白演绎

**替代**: 现 `voice-synthesis` + 角色行为相关内容的升级

**职责**:
- **角色性格档案** (Character Profile):
  - 性格特质（MBTI 或简化模型）
  - 说话风格（用词习惯、口头禅、语速特征）
  - 情感反应模式（遇到压力→沉默？爆发？冷静？）
  - 关系动态（对不同角色的态度差异）
- **表演指导** (Performance Direction):
  - 面部微表情词汇（30+ 表情描述词）
  - 肢体语言词汇（40+ 动作描述词，按角色性格分类）
  - 漫画式夸张表达（适合漫剧的夸张手法）
- **对白演绎** (Dialogue Performance):
  - 语气层次（不只是 happy/sad，而是细腻的情感光谱）
  - 潜台词表达（角色说的和想的不一样时的处理）
  - 对白节奏设计（停顿、重音、语速变化的标注）
- **角色弧线追踪**:
  - 确保 Character Arc Blueprint 贯穿到每个 Shot 的表演
  - 跟踪角色情感状态随场景推进的变化
- **音色设计**:
  - 角色音色映射表（升级为更细化的音色矩阵）
  - 情绪-语音参数映射
  - audio_prompt 对白格式规范

**输入**: `characters.json` + `script_breakdown.json`（含 Character Arc Blueprint）

**输出**: 融入 Shot 级别的表演指导（enriched `Plot/Visual Description` + `audio_prompt`）

**Pipeline Steps**: Step 3a (extract, 性格提取) + Step 4c (Shot 表演指导) + Step 5 (export, 配音指导)

**关键改进**:
- **新增面部微表情词汇表**:

| 类别 | 描述词 |
|------|--------|
| 眼神 | 坚定凝视、回避目光、泪光闪烁、瞳孔放大(震惊)、半眯(怀疑)、深情注视 |
| 眉毛 | 紧蹙、挑眉、舒展、一侧挑起(质疑)、快速抖动(惊讶) |
| 嘴部 | 抿唇(隐忍)、嘴角上扬(含蓄笑)、微微张开(惊讶)、咬下唇(紧张)、颤抖(恐惧) |
| 整体 | 面部僵硬(压抑)、肌肉放松(释怀)、微红(羞涩)、苍白(恐惧)、泪痕(悲伤后) |

- **新增肢体语言词汇表**:

| 类别 | 描述词 |
|------|--------|
| 手部 | 双手交叉(防御)、手指互绞(焦虑)、单手托腮(思考)、握拳(愤怒/决心)、轻弹手指(不耐烦) |
| 站姿 | 挺胸(自信)、佝偻(沮丧)、双手叉腰(挑战)、倚靠(慵懒)、重心不稳(紧张) |
| 动态 | 猛然回头、缓步走来、冲上前、后退一步(惊讶)、原地踱步(焦虑) |

- **新增对白情感光谱**（替代简单的 happy/sad/angry）:

| 情感大类 | 细分层次 |
|---------|---------|
| 喜 | 微笑→欣喜→狂喜→感动落泪 |
| 怒 | 不悦→烦躁→愤怒→暴怒→冷怒(最危险) |
| 哀 | 惆怅→忧伤→悲痛→绝望→释然 |
| 惧 | 不安→紧张→恐惧→惊恐→颤栗 |
| 复合 | 苦笑、含泪微笑、恼羞成怒、强颜欢笑、故作镇定 |

---

### Skill 5: `shot-director`（镜头导演） <sub>shot 模块</sub>

> Layer 3 的核心引擎——将场景转化为精确的可执行镜头序列

**替代**: 现 `script-breakdown` Layer 3 + `storyboard-design` 的镜头级内容

**职责**:
- Layer 3 ShotPlotCreateCoT 执行（Scene → Shots）
- **扩展镜头类型体系**（从 9 种扩展到 18 种）
- **扩展运镜词汇**（从 9 种扩展到 20+ 种）
- Shot 构图设计（三分法、对角线、中心构图、引导线等）
- 角色空间排布与 bounding box 计算
- Duration 计算公式执行
- 双版本描述生成（Plot/Visual Description + Coarse Plot）
- seedance_mode 选择逻辑
- **镜头组合模式** (Shot Patterns):
  - 正反打 (Shot/Reverse shot) 模式
  - 建立-中-特 (Establishing-Medium-Close) 模式
  - 反应镜头 (Reaction shot) 模式
  - 蒙太奇 (Montage) 模式

**输入**: `script_breakdown.json`（含 Scene Annotation）+ `characters.json` + `character_list/`

**输出**: 每个 Scene 的 `Shot Annotation`（嵌套写入 `script_breakdown.json`）

**Pipeline Steps**: Step 4c (Layer 3 breakdown)

**关键改进**:
- **扩展镜头类型表**:

| 类型 | 英文 | 用途 | 情感效果 |
|------|------|------|---------|
| 大远景 | Extreme wide | 史诗/渺小感 | 孤独、壮阔 |
| 远景 | Wide shot | 建立空间 | 客观、开放 |
| 中远景 | Medium wide | 环境+人物 | 叙事 |
| 中景 | Medium shot | 人物互动 | 对话 |
| 中近景 | Medium close-up | 表情+手势 | 亲切 |
| 近景 | Close-up | 面部表情 | 情感共鸣 |
| 大特写 | Extreme close-up | 眼睛/道具 | 紧张、聚焦 |
| 过肩 | Over-shoulder | 对话视角 | 参与感 |
| 主观 | POV | 角色视角 | 代入感 |
| 俯拍 | High angle | 俯瞰/压迫 | 弱小、全局 |
| 仰拍 | Low angle | 仰视/威严 | 力量、英雄 |
| 荷兰角 | Dutch angle | 倾斜不安 | 混乱、紧张 |
| 双人镜头 | Two-shot | 关系展示 | 对比/连接 |
| 群像 | Group shot | 集体动态 | 社群感 |
| 插入镜头 | Insert | 细节展示 | 线索/伏笔 |
| 空镜 | Cutaway | 环境/过渡 | 呼吸/节奏 |
| 镜面 | Mirror shot | 内心映射 | 自我对话 |
| 剪影 | Silhouette | 轮廓/气氛 | 神秘、戏剧 |

- **扩展运镜词汇**:

| 运镜 | 英文 | 效果 | 动作词 |
|------|------|------|--------|
| 静止 | Static | 稳定 | holds still |
| 左摇 | Pan left | 扫视 | sweeps left |
| 右摇 | Pan right | 跟随 | follows right |
| 上摇 | Tilt up | 仰视 | tilts upward |
| 下摇 | Tilt down | 俯瞰 | tilts downward |
| 推镜 | Zoom in | 聚焦 | punches in |
| 拉镜 | Zoom out | 揭示 | pulls back |
| 慢推轨 | Slow dolly-in | 渐进 | creeps forward |
| 快推轨 | Fast dolly-in | 冲击 | rushes in |
| 跟拍 | Tracking | 动态 | follows the action |
| 横移 | Truck/Crab | 平移 | slides sideways |
| 环绕 | Orbit | 立体感 | circles around |
| 升降 | Crane/Boom | 视角变化 | rises/descends |
| 手持 | Handheld | 真实感 | shakes slightly |
| 甩镜 | Whip pan | 快速转场 | whips across |
| 360环绕 | 360 orbit | 戏剧性 | spins around |

- **新增镜头组合模式**:

```
正反打模式 (对话):     Shot A (角色1) → Shot B (角色2) → Shot A → Shot B
建立-推进模式:        远景(建立) → 中景(叙事) → 近景(情感) → 特写(高潮)
反应链模式:           动作镜头 → 反应镜头 → 反应镜头(其他角色)
蒙太奇模式:           短镜头1 → 短镜头2 → ... → 短镜头N (时间压缩)
```

**CoT 要求**: Layer 3 的 6 步 CoT 完整保留

---

### Skill 6: `shot-rhythm`（叙事节奏） <sub>shot 模块</sub>

> 全局节奏控制——情绪曲线、镜头韵律、时长对齐

**替代**: 现 `narrative-rhythm` rule 升级为 skill（原 rule 仅做约束，不提供方法论）

**职责**:
- **情绪曲线设计**（按题材适配，不再固定 4 阶段比例）
- Duration 计算公式（对白时间 + 动作时间 → Seedance 档位对齐）
- 场景内镜头节奏编排（开场→发展→高潮→过渡）
- 跨场景节奏设计（张弛交替、呼吸感）
- 超长对白拆分规则
- 整体时长控制（短篇 60-120s / 标准 120-300s）
- **题材节奏模板**:

| 题材 | 节奏特征 | 镜头倾向 | Duration 分布 |
|------|---------|---------|--------------|
| 言情 | 慢-中-慢 | 近景/特写多 | 5s 为主，情感高潮 10s |
| 动作 | 快-快-快 | 中远景+快切 | 4s 为主，动作 10-15s |
| 悬疑 | 慢蓄力→爆发 | 特写+荷兰角 | 5-10s，悬念揭晓 15s |
| 喜剧 | 快-顿-快 | 中景，timing 关键 | 4-5s，笑点延迟 10s |
| 奇幻 | 渐进壮阔 | 远景+升降运镜 | 5-10s，史诗场面 15s |

**输入**: 题材类型 + `script_breakdown.json`（完整三层结构）

**输出**: 节奏审查报告（Duration 分布统计 + 节奏建议 + 不合规镜头标记）

**Pipeline Steps**: Step 4c (Layer 3 的 Duration 决策) + Step 5 (导出前的节奏审查)

**关键改进**:
- 从"硬性规则"升级为"方法论 + 模板 + 审查工具"
- 新增 5 种题材节奏模板
- 新增节奏审查清单（可在导出前执行）
- 情绪曲线从固定比例改为可配置模板

---

### Skill 7: `prompt-image`（图像提示词） <sub>prompt 模块</sub>

> 为图像生成平台（Gemini / DALL-E / SD）构造高质量文生图 prompt

**替代**: 从 `storyboard-design` + `character-consistency` + `seedance-video` 中抽取 image_prompt 相关内容

**职责**:
- **image_prompt 构造公式**:
  ```
  {style_prefix}, {shot_type}, {scene_description}, {character_appearance_full}, 
  {lighting_from_scene}, {mood}, {composition_rule}, {quality_tags}
  ```
- **风格前缀体系**:

| 风格 | 前缀 | 适用题材 |
|------|------|---------|
| 日式漫画 | `manga style, cel shading,` | 校园、奇幻 |
| 日式动画 | `anime style, vibrant colors,` | 动作、冒险 |
| 半写实 | `semi-realistic, detailed,` | 都市、悬疑 |
| 水彩 | `watercolor style, soft edges,` | 文艺、治愈 |
| 赛博朋克 | `cyberpunk style, neon lights,` | 科幻 |

- **构图规则映射**:
  - 三分法 → `rule of thirds composition`
  - 中心构图 → `centered composition, symmetrical`
  - 对角线 → `diagonal composition, dynamic`
  - 引导线 → `leading lines toward subject`
  - 框中框 → `frame within frame`
- **角色外观嵌入规则**（从 `<TOK>` 去掉前缀，完整复制）
- **negative prompt 按题材定制**
- **平台适配层**:
  - Gemini: 自然语言描述，强调场景叙事
  - DALL-E 3: 详细描述，支持长 prompt
  - Stable Diffusion: 标签式，权重语法 `(keyword:1.2)`
- 角色参考图 prompt（供用户在生图平台生成角色卡）
- 关键帧 prompt（供用户生成每镜分镜图）

**输入**: Shot 数据（来自 `script_breakdown.json`）+ 角色外观（来自 `characters.json`）+ 场景设计（Scene Annotation）

**输出**: 每个 Shot 的 `image_prompt` 字段 + 用户操作指引

**Pipeline Steps**: Step 3b (角色参考图 prompt) + Step 4c (分镜关键帧 prompt) + Step 5 (导出指南)

**关键改进**:
- 独立为专用 skill，不再混杂在 storyboard-design 中
- 新增构图规则映射表
- 新增平台适配层（同一镜头为不同平台输出不同格式的 prompt）
- 新增风格前缀体系
- negative prompt 从通用模板改为按题材定制

---

### Skill 8: `prompt-video`（视频提示词） <sub>prompt 模块</sub>

> 为视频生成平台（可灵 / Seedance）构造高质量图生视频/文生视频 prompt

**替代**: 现 `seedance-video` 的平台解耦版

**职责**:
- **video_prompt 构造公式**:
  ```
  {character_reference_images}, {keyframe_image}, {dynamic_action}, {camera_movement}, {atmosphere_change}
  ```
- **@Image 引用规范** (从 character-consistency 收编):
  - 角色参考图在前，按 image_paths 数组顺序编号
  - 首帧图永远在最后一位
  - 校验: @Image 引用数量 == image_paths 长度
- **seedance_mode 决策树**:
  ```
  有已设计角色参与? → multimodal
  仅场景图/空镜?   → i2v
  无任何图片?      → t2v
  ```
- **动态描述词汇表** (升级版):

| 类别 | 基础动作 | 细化动作 |
|------|---------|---------|
| 面部 | 睁眼 | 缓缓睁开双眼，瞳孔逐渐聚焦 |
| 面部 | 微笑 | 嘴角缓缓上扬，眉眼间流露出温暖 |
| 手部 | 伸手 | 右手缓缓抬起，手指微微张开向前探出 |
| 身体 | 转身 | 身体以腰部为轴缓慢旋转180度 |
| 环境 | 风吹 | 微风拂过，发丝和裙摆向右轻轻飘动 |
| 光影 | 日出 | 暖光从画面右侧逐渐蔓延，阴影退缩 |

- **多角色同框动态**: 分别描述每个角色的动作，确保不冲突
- **动作承接规则**: 上一镜头结束动作 = 下一镜头起始状态
- **平台适配**:
  - 可灵: 中文 prompt，重点描述动态变化
  - Seedance: @Image 引用 + 动态描述
  - Runway/Pika: 英文 prompt，camera motion 关键词

**输入**: Shot 数据 + 角色资产状态 + 上一 Shot 的结束状态

**输出**: 每个 Shot 的 `video_prompt` + `seedance_mode` + `image_paths` 规划

**Pipeline Steps**: Step 4c (video_prompt 生成) + Step 5 (导出指南)

**关键改进**:
- 从平台绑定（seedance-video）解耦为通用 video prompt 能力
- 收编 @Image 引用规范（从 character-consistency 移出）
- 新增动态描述词汇的细化版
- 新增动作承接规则（镜头间连续性）
- 新增多平台适配

---

### Skill 9: `prompt-audio`（音频提示词） <sub>prompt 模块</sub>

> 音频设计的完整方法论——环境音、对白表演、BGM、音效

**替代**: 现 `voice-synthesis` 的全面升级

**职责**:
- **audio_prompt 构造公式**:
  ```
  {ambient_sounds}, {action_sfx}, {dialogue_with_performance}, {bgm_description}
  ```
- **环境音设计**:

| 场景类型 | 环境音层次 |
|---------|-----------|
| 室内/安静 | 钟表滴答 + 远处车声 + 空调嗡鸣 |
| 室外/自然 | 鸟鸣 + 风声 + 流水 + 脚步踩草 |
| 室外/城市 | 车流 + 人群嘈杂 + 偶尔喇叭 |
| 战斗/紧张 | 心跳加速 + 金属碰撞 + 呼吸急促 |
| 魔幻 | 能量嗡鸣 + 水晶共鸣 + 空灵回响 |

- **对白表演指导** (从 character-acting 获取):
  - 对白格式: `{性别/年龄}{详细语气}说：'{台词}'`
  - 语气词汇从简单标签升级为细腻描述
  - 停顿标注: `...` = 0.5s 停顿, `——` = 1s 停顿
  - 重音标注: `*重音词*`
- **BGM 选择矩阵**:

| 情绪阶段 | BGM 风格 | 乐器倾向 |
|---------|---------|---------|
| 铺垫 | 舒缓、轻柔 | 钢琴、弦乐 |
| 发展 | 渐进、层次增加 | 弦乐+鼓点 |
| 高潮 | 激烈、壮阔 | 管弦乐全奏 |
| 收尾 | 回落、余韵 | 独奏钢琴/吉他 |
| 悬疑 | 低频不和谐 | 电子音+弦乐颤音 |

- **音色映射表** (角色→音色):
  - 继承现有 6 种 voice_type
  - 新增: 沙哑老者、清冷御姐、慵懒少年、活泼萝莉
- **音量层次规范**: 对白(100%) > 动作音效(70%) > 环境音(40%) > BGM(30%)

**输入**: Shot 数据 + 角色 voice 配置 + 场景情绪基调

**输出**: 每个 Shot 的 `audio_prompt` + 配音操作指引

**Pipeline Steps**: Step 4c (audio_prompt 生成) + Step 5 (导出配音指南)

**关键改进**:
- 从"语音合成工具指南"升级为"完整音频设计方法论"
- 新增环境音分层设计
- 新增 BGM 选择矩阵
- 对白表演指导融入 character-acting 的情感细粒度
- 新增音量层次规范

---

### Skill 10: `export-render`（导出渲染） <sub>export 模块</sub>

> 最终交付物的质量保障——导出、审查、手动操作指引

**新增 Skill**（现有体系中缺失）

**职责**:
- **Markdown 制作指南导出** (现有 export_storyboard.py 的 skill 层面指导)
- **质量审查清单** (从 quality-standards rule 升级):
  - 三层 JSON 结构完整性校验
  - CoT 推理质量校验
  - image_prompt / video_prompt / audio_prompt 规范性校验
  - 角色一致性终审
  - 节奏合规性检查
- **用户手动操作指引** (核心输出):
  - Step-by-step: 在 Gemini 生成角色参考图
  - Step-by-step: 在 Gemini 生成每镜关键帧
  - Step-by-step: 在可灵生成视频片段
  - Step-by-step: 在剪映拼接 + 配音
- **资产清单生成**:
  - 待生成图片列表（角色参考图 + 关键帧）
  - 待生成视频列表（按镜头顺序）
  - 配音文本汇总（按角色分组）
- **成本预估**:
  - 基于 Shot 数量和 Duration 分布，预估总生成成本

**输入**: 完整 `script_breakdown.json` + `characters.json` + 项目配置

**输出**:
- `storyboard_guide.md`（完整制作指南）
- `storyboard_guide.csv`（表格版）
- `asset_checklist.md`（资产清单）
- `cost_estimate.md`（成本预估）

**Pipeline Steps**: Step 5 (export-guide)

---

## 三、Skill 映射总览

### 新旧 Skill 对照表

| 新 Skill | 模块 | 替代的旧 Skill | 主要变化 |
|----------|------|---------------|--------|
| `script-parser` | script | manga-script + script-breakdown(L1) | 合并导入和编剧拆解 |
| `script-scene` | script | script-breakdown(L2) + storyboard-design(场景) | 新增光影/色彩/转场体系 |
| `character-design` | character | character-consistency(设计部分) | 新增视觉识别卡、服装体系 |
| `character-acting` | character | voice-synthesis + 新增 | 全新的角色灵魂设计 |
| `shot-director` | shot | script-breakdown(L3) + storyboard-design(镜头) | 扩展镜头/运镜词汇 2x |
| `shot-rhythm` | shot | narrative-rhythm(rule→skill) | 新增题材模板、审查工具 |
| `prompt-image` | prompt | 从3个skill中抽取 | 独立模块+平台适配层 |
| `prompt-video` | prompt | seedance-video | 平台解耦+动态词汇升级 |
| `prompt-audio` | prompt | voice-synthesis(升级) | 完整音频设计方法论 |
| `export-render` | export | 新增 | 质量审查+操作指引+成本预估 |

### Pipeline Step → Skill 映射表

| Pipeline Step | 使用的 Skill |
|---------------|-------------|
| Step 1: /init-project | — (纯文件操作：创建项目目录 + 初始化 JSON) |
| Step 2: /import-script | `script-parser` |
| Step 3a: /extract-characters | `script-parser` + `character-design` + `character-acting` |
| Step 3b: /design-characters | `character-design` |
| Step 4a: Layer 1 分镜 | `script-parser` |
| Step 4b: Layer 2 分镜 | `script-scene` + `shot-rhythm` |
| Step 4c: Layer 3 分镜 | `shot-director` + `character-acting` + `prompt-image` + `prompt-video` + `prompt-audio` + `shot-rhythm` |
| Step 5: /export-guide | `export-render` |

### Rule 保留/调整说明

| Rule | 处理方式 | 说明 |
|------|---------|------|
| `pipeline-dispatch` | **精简并更新** | 移除 MCP tool 指定，仅保留 Step→Skill 映射 + 状态机 |
| `cot-reasoning` | **保留** | CoT 强制规则不变 |
| `api-usage` | **精简** | 仅保留成本控制策略，移除 MCP 并发控制部分 |
| `character-consistency` | **精简为校验规则** | 设计方法论移入 skill，rule 仅保留校验清单 |
| `narrative-rhythm` | **精简为约束规则** | 方法论移入 skill，rule 仅保留硬性约束（Duration 必须为 4/5/10/15） |
| `quality-standards` | **保留并更新** | 更新为对应新 skill 体系的质量标准 |

---

## 四、实施优先级

### Phase 1: 核心重构（高优先级）

| 顺序 | Skill | 理由 |
|------|-------|------|
| 1 | `script-parser` | 流水线入口，影响所有下游 |
| 2 | `character-design` | 角色是一致性的基础 |
| 3 | `shot-director` | Layer 3 是最核心的镜头生成引擎 |
| 4 | `prompt-image` | 直接决定用户手动生成的图片质量 |

### Phase 2: 能力增强（中优先级）

| 顺序 | Skill | 理由 |
|------|-------|------|
| 5 | `script-scene` | 场景设计质量影响整体视觉水平 |
| 6 | `prompt-video` | 视频生成 prompt 质量决定最终视频效果 |
| 7 | `prompt-audio` | 音频设计提升整体观感 |

### Phase 3: 体验完善（后续优先级）

| 顺序 | Skill | 理由 |
|------|-------|------|
| 8 | `character-acting` | 角色深度提升，锦上添花 |
| 9 | `shot-rhythm` | 节奏优化，进阶能力 |
| 10 | `export-render` | 导出优化，用户体验 |

---

## 五、数据流全景

```
raw_script.txt
      │
      ▼
┌──────────────┐     ┌──────────────┐
│ script-parser │────▶│ character-   │
│ (Step 2+4a)  │     │ design (3a/b)│
└──────┬───────┘     └──────┬───────┘
       │                    │
       │  script_breakdown  │  characters.json
       │  .json (L1)        │  character_list/
       │                    │
       ▼                    ▼
┌──────────────┐     ┌──────────────┐
│ script-scene │     │ character-   │
│              │     │ acting       │
│ (Step 4b)    │     │ (enrichment) │
└──────┬───────┘     └──────┬───────┘
       │                    │
       │  Scene Annotation  │  Performance data
       │                    │
       ▼                    │
┌──────────────────────────────────────────────┐
│              shot-director (Step 4c)          │
│                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │prompt-image  │ │prompt-video  │ │prompt-audio│ │
│  └─────────────┘ └─────────────┘ └────────────┘ │
│                                                 │
│  + shot-rhythm (节奏校验)                        │
└──────────────────┬───────────────────────────┘
                   │
                   │  完整 script_breakdown.json
                   ▼
            ┌──────────────┐
            │ export-render │
            │ (Step 5)     │
            └──────────────┘
                   │
                   ▼
            制作指南 + 资产清单 + 成本预估
```

---

## 六、Agent Team 集成设计

### 设计原则

1. **Team 定义内嵌于 Skill**：每个 Skill 的 YAML frontmatter 中包含完整的 team 定义，团队与领域知识共处
2. **Coordinator 模式**：每个 Team 有且仅有一个 Coordinator，负责任务分发、结果合并、质量关卡
3. **四种协作模式**：并行加速、专业分工、质量审核、多模态协作
4. **Reviewer 独立**：生成者和审核者永远分离，确保质量
5. **最多 2 次返工**：匹配 cot-reasoning 规则的重试策略

### Team Schema

在 SKILL.md 的 YAML frontmatter 中定义：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `team.enabled` | bool | 是 | 是否启用 Team |
| `team.pattern` | enum | 是 | parallel / specialization / review / multi-modal |
| `team.coordinator` | string | 是 | Coordinator 角色名 |
| `team.roles[]` | array | 是 | 角色定义列表 |
| `team.roles[].name` | string | 是 | 角色标识符（用作 agent name） |
| `team.roles[].type` | enum | 是 | coordinator / specialist / worker / reviewer |
| `team.roles[].expertise` | string | 是 | 一句话专长描述 |
| `team.roles[].skill_ref` | string | 否 | 引用的其他 Skill |
| `team.roles[].system_prompt` | string | 是 | Agent 的 System Prompt |
| `team.roles[].responsibilities` | array | 是 | 职责列表 |
| `team.coordination.merge_strategy` | enum | 是 | coordinator-merge / sequential-pipeline / parallel-collect |
| `team.coordination.review_required` | bool | 是 | 是否需要 Reviewer 审批 |
| `team.coordination.max_parallel` | int | 否 | 最大并行 Worker 数 |

### 6 个 Team 分配

| Skill | Team | 模式 | 角色数 | 核心场景 |
|-------|------|------|--------|---------|
| `script-scene` | Team A | parallel + review | 5 (coordinator + planner x3 + reviewer) | Layer 2 逐 Sub-Script 并行处理 |
| `shot-director` | Team B | multi-modal (全部4种) | 7 (coordinator + designer + 3 prompters + rhythm + reviewer) | Layer 3 多模态并行 Prompt 生成 |
| `character-acting` | Team C | specialization + review | 4 (casting-director + personality + voice + reviewer) | 角色多维度充实 |
| `prompt-image` | Team D | review | 2 (art-director + consistency-checker) | 图像 Prompt 一致性审核 |
| `prompt-video` | Team E | review | 2 (motion-director + reference-validator) | @Image 引用校验 |
| `export-render` | Team F | review | 4 (post-supervisor + 3 auditors) | 多维度质量终审 |

### 4 个无 Team 的 Skill

| Skill | 原因 |
|-------|------|
| `script-parser` | Layer 1 单次 LLM 调用，无并行机会 |
| `character-design` | 逐角色交互设计，需要用户参与 |
| `shot-rhythm` | 单次全局审查，不需多 agent |
| `prompt-audio` | 依赖 video_prompt 的顺序依赖 |

### TaskList 命名约定

```
[team-name] {layer}.{unit}: {description}
```

示例：
- `[script-scene] L2.SS3: Plan scenes for Sub-Script 3`
- `[shot-director] L3.SS1.Sc2: Design shots for Sub-Script 1 Scene 2`
- `[shot-director] L3.SS1.Sc2.prompts.image: Generate image_prompts`

### Team 生命周期

```
1. use_skill() → 加载 Skill 领域知识
2. 读取 SKILL.md team 定义 → 获取角色配置
3. TeamCreate → 创建 Team
4. spawn teammates → 按角色定义启动 Agent
5. Coordinator 通过 TaskList 协调 → 任务分发、结果合并
6. 所有任务完成 → shutdown teammates
7. TeamDelete → 清理资源
```

### `/break-script` 完整 Team 执行流

```
Step 4a (无 Team):
  script-parser → Layer 1 screenwriterCoT → script_breakdown.json 根层级

Step 4b (script-scene Team):
  TeamCreate → scene-coordinator + scene-planner x3 + scene-reviewer
  scene-coordinator 创建 N 个任务（每个 Sub-Script 一个）
  scene-planner 并行执行 ScenePlanningCoT
  scene-reviewer 校验跨场景连续性
  合并写入 script_breakdown.json
  TeamDelete

Step 4c (shot-director Team):
  TeamCreate → 7 角色
  shot-coordinator 遍历所有 Scene：
    1. shot-designer 生成镜头骨架
    2. image-prompter + video-prompter + audio-prompter 并行生成三版 Prompt
    3. rhythm-checker 校验 Duration
    4. shot-reviewer 终审
  合并写入 script_breakdown.json
  TeamDelete
```
