---
name: character-design
description: "角色视觉设计。从剧本提取角色信息、构建 <TOK> 外观描述、生成参考图 Prompt、管理 character_list/ 资产库。涵盖 Step 3a（提取角色）和 Step 3b（设计角色）。"
team:
  enabled: false
---

# 角色视觉设计

从剧本文本中提取角色、构建完整视觉身份、生成参考图 Prompt、管理 `character_list/` 资产库。覆盖 Step 3a（角色提取）和 Step 3b（角色精细设计）。

**输入**: `raw_script.txt` + `script_synopsis.json`
**输出**: `characters.json`、`character_list/{CharName}/best.txt`、Gemini Prompt（供用户手动生成 best.png + 多角度参考图）

---

## 1. 角色提取（Step 3a: /extract-characters）

从 `script_synopsis.json` 中识别所有有名角色，写入 `characters.json`。

### 提取内容

| 字段 | 来源 | 说明 |
|------|------|------|
| `name` | 剧本人物表 / 对白标注 | 角色名称，需唯一 |
| `description` | 剧本描述 + AI 推断 | 性格、背景、故事作用 |
| `appearance_description` | 剧本原文外观描述 | 中文，发型发色/服装/体型/标志特征 |
| `relationships` | 人物关系梳理 | 与其他角色的关系列表 |
| `voice` | 对白推断 | 性别、语速、默认情绪 |
| `style_keywords` | 外观提炼 | 英文关键词，用于 Prompt 构建 |
| `design_status` | 固定值 | 初始为 `"extracted"` |

### 提取流程

1. **读取** `script_synopsis.json` 中的 `characters` 和 `story_summary`
2. **读取** `raw_script.txt` 扫描对白标注和角色描写段落
3. **识别**所有有名角色（含只出现一次的配角）
4. **推断**剧本未明确描述的外观细节（基于角色设定合理推断）
5. **梳理**角色间关系（从剧情互动和对白推断）
6. **写入** `projects/{project_id}/characters.json`

### 提取注意事项

- 只提取**有名字**的角色，旁白/群众演员不入库
- 外观描述力求具体：避免"漂亮的女孩"，应写"金色长发编成麻花辫、穿着蓝色渐变连衣裙的年轻女性"
- 如果剧本未描述某角色外观，基于角色身份/年龄/职业合理推断并标注 `[推断]`
- 同名角色需通过上下文消歧

---

## 2. 角色视觉识别系统（Character Visual Identity System）

每个角色在设计阶段需构建完整的**视觉识别卡（Visual ID Card）**，确保角色在多镜头间的可辨识性和视觉一致性。

### Character Visual ID Card Schema

```json
{
  "name": "Elsa",
  "tok_description": "<TOK> has long platinum blonde hair in a single braid draped over left shoulder, wearing a flowing ice-blue dress with snowflake crystal patterns, ice blue eyes, fair porcelain skin, tall slender build, regal graceful posture",
  "signature_pose": "hands raised with ice crystals forming between fingers",
  "signature_expression": "serene confidence with a hint of melancholy",
  "body_proportions": "tall, slender, graceful, regal posture",
  "wardrobe": {
    "default": "flowing ice-blue dress with snowflake patterns, translucent cape",
    "casual": "light blue blouse with white pants, hair loosely tied",
    "battle": "crystalline armor with cape of frost, hair flowing free"
  },
  "visual_identifiers": [
    "ice crystal motifs",
    "blue color palette",
    "braid over left shoulder"
  ],
  "distinguishing_features": "pointed ears from her winter crown, always bare feet on ice"
}
```

### 各字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 角色名，须与 `characters.json` 和 `character_list/` 目录名一致 |
| `tok_description` | string | 是 | `<TOK>` 格式英文外观描述，写入 `best.txt` |
| `signature_pose` | string | 是 | 标志性姿势，用于 best.png 和关键镜头 |
| `signature_expression` | string | 是 | 标志性表情，体现角色性格 |
| `body_proportions` | string | 是 | 体型/身高/比例描述 |
| `wardrobe` | object | 是 | 服装设计体系，至少包含 `default` |
| `visual_identifiers` | array | 是 | 视觉识别特征列表（颜色主题、标志性配饰等），用于快速辨识 |
| `distinguishing_features` | string | 否 | 独特特征（疤痕、胎记、特殊标记等） |

### Wardrobe 服装设计体系

为角色设计多套服装方案，适配不同场景：

| 场景键 | 用途 | 说明 |
|--------|------|------|
| `default` | **必填**，角色默认/最常见着装 | 大部分镜头使用此方案 |
| `casual` | 日常/休闲场景 | 非正式场合的着装 |
| `battle` | 战斗/冲突场景 | 动作戏的特殊着装 |
| `formal` | 正式/仪式场景 | 可按需添加更多场景键 |

**服装切换规则**：
- `<TOK>` 描述（best.txt）使用 `default` 着装
- 分镜拆解时，Scene 级别可指定服装方案
- 同一 Scene 内服装不变（除非有换装情节）
- 服装切换时需在 `image_prompt` 中替换对应服装描述

### Visual ID Card 构建流程

1. 基于 `characters.json` 中的 `appearance_description` 确定基础外观
2. 设计 `wardrobe` 各场景服装（`default` 必填）
3. 确定 `signature_pose` 和 `signature_expression`（从角色性格推导）
4. 提炼 `visual_identifiers`（3-5 个最显著的视觉标记）
5. 记录 `distinguishing_features`（独特的不可替代特征）
6. 构建 `tok_description`（综合以上信息）
7. 将 Visual ID Card 数据存入 `characters.json` 的对应角色条目

---

## 3. `best.txt` — 结构化角色参考手册（Character Reference Sheet）

`best.txt` 是角色视觉一致性的**核心锚点文件**，包含完整生图指令的**结构化参考手册**。基于电影摄影师的实际拍摄需求设计，覆盖所有可能的机位、情绪和光照条件。用户可直接复制其中的 Prompt 到 Gemini / DALL-E 生成对应图片。

### 3.1 文件结构（8 个段落）

```
================================================================================
CHARACTER REFERENCE SHEET — {角色中文名} ({英文名})
Project: {项目名} | Style: {画风} | Role: {角色定位}
Total Assets: best.png + 8 视角 + 3 表情图 + 3 动态姿势 = 15 张
================================================================================

## [TOK] CORE APPEARANCE DESCRIPTION           ← 核心外观锚点（<TOK> 格式）
## [STYLE] {STYLE} ART DIRECTION               ← 画风指令（6 维度美术方向）
## [BEST.PNG] MAIN REFERENCE PROMPT            ← 主参考图 Prompt（3/4 半身）
## [MULTI-ANGLE] 8 CAMERA POSITIONS            ← 8 张摄影机位 Prompt (photo_1~8)
## [EXPRESSION SHEET] 3 EMOTION BOARDS         ← 3 张表情图 Prompt (expr_1~3)
## [ACTION POSES] 3 DYNAMIC POSES              ← 3 张动态姿势 Prompt (pose_1~3)
## [NEGATIVE PROMPT]                           ← 负面提示词（画风专属扩展版）
## [WARDROBE VARIANTS]                         ← 服装变体 Prompt 片段（可直接替换）
## [GENERATION ORDER]                          ← 推荐生图顺序和分组指南
```

### 3.1.1 设计哲学 — 电影摄影师的需求模型

每个段落对应电影制作中的一类实际需求：

| 段落 | 对应电影需求 | 资产数量 | 摄影师用途 |
|------|-------------|---------|-----------|
| BEST.PNG | 角色海报 / 定妆照 | 1 | 所有镜头的外观基准 |
| MULTI-ANGLE | 覆盖核心机位 | 8 | 确保常用角度都有参考 |
| EXPRESSION | 覆盖完整情绪谱 | 3 | 指导演员表情演绎 |
| ACTION POSES | 覆盖关键动作 | 3 | 指导走位和动作设计 |
| **合计** | | **15** | |

> **精简原则**：光照条件和手部特写在漫剧制作中使用频率较低，改为在 Step 4 分镜阶段通过 Prompt 直接描述。机位从 10 精简至 8（移除正背面全身和俯视），保留最高频使用的角度。

### 3.2 `[TOK]` 核心外观描述

以 `<TOK>` 开头的英文单行描述，是所有 Prompt 的**外观锚点**。

**构建规则**：
- 以 `<TOK> is a` 或 `<TOK> has` 开头
- 使用英文，单行文本，不换行
- 包含年龄、种族/肤色特征（为 AI 生图提供精确参考）
- 按以下优先级排列要素：
  1. 年龄 + 性别 + 种族特征
  2. 发型发色（精确到方向、层次、纹理）
  3. 服装（使用 `wardrobe.default`，含材质/纽扣/口袋等细节）
  4. 标志配饰（工牌、眼镜、饰品等，含材质和位置）
  5. 眼睛（颜色 + 形状 + 特征，如黑眼圈、高光）
  6. 肤色 + 面部骨骼结构（颧骨、下颌线等）
  7. 体型/身高/体态
- 使用**具体的、可复现的**特征描述
- **避免**模糊词汇（handsome / beautiful / pretty / cool）
- 每个 `visual_identifiers` 中的特征都**必须**出现在描述中

**示例**：
```
<TOK> is a 35-year-old East Asian male with short neat jet-black hair, slightly tousled and swept to the right on top with clean-shaved sides, wearing a dark navy blue high-collar engineer uniform jacket with two rows of silver buttons and silver piping along the seams over a crisp white dress shirt with the top button open, a rectangular metallic ID badge engraved on the left chest pocket, dark brown intense deep-set angular anime eyes with visible dark circles and subtle fatigue lines underneath, light warm-toned skin with a sharp angular jawline and high cheekbones showing mild stress creases, medium-height slim athletic build with broad shoulders and upright disciplined military-like posture
```

### 3.3 `[STYLE]` 画风指令

从 `project.json` 的 `style` 字段读取画风，生成对应的**美术方向指令**。此段落定义了所有 Prompt 的视觉基调。

**必须包含的 6 个维度**：

| 维度 | 说明 | anime 示例 |
|------|------|-----------|
| Art style | 整体风格定义 | Japanese anime, clean lineart, cel-shading with soft gradients |
| Color palette | 角色专属色彩方案 | deep navy blue (uniform) / pure white (shirt) / jet black (hair) |
| Lighting | 默认光照方案 | dramatic rim lighting from above, subtle subsurface scattering |
| Line weight | 线条粗细定义 | medium-thick outlines, thinner interior detail lines |
| Eye style | 眼睛绘制风格 | anime-proportioned with sharp angular shape, dark brown iris with white highlights |
| Rendering | 渲染质量要求 | high-detail anime illustration, studio quality, no chibi |

**画风映射表**（根据 `project.json.style` 自动选择）：

| style 值 | Art style 关键词 | 额外修饰 |
|----------|-----------------|---------|
| `anime` | Japanese anime, clean lineart, cel-shading | anime cel-shading, no chibi |
| `manga` | black-and-white manga, screentone shading | high contrast, ink illustration |
| `comic` | Western comic book, bold outlines | dynamic lighting, vibrant colors |
| `realistic` | semi-realistic digital painting | photorealistic textures, subsurface scattering |
| `watercolor` | watercolor illustration, soft edges | wet-on-wet blending, paper texture |
| `pixel` | pixel art, limited palette | 16-bit style, clean pixel edges |

### 3.4 8 机位视角设计原理

从电影摄影师的实际拍摄需求出发，8 个机位覆盖漫剧中最高频使用的角度：

| # | 机位名称 | 文件名 | 构图 | 摄影用途 | 必须展示的特征 |
|---|---------|--------|------|---------|--------------|
| 1 | 正面全身 | photo_1 | Full Body Front | 建立镜头、角色入场 | 完整身材比例 + 鞋子 + 服装全貌 |
| 2 | 正面半身 | photo_2 | Medium Shot Front | 对话、反应镜头（最高频，80%镜头） | 胸部以上 + 手部自然位置 + 表情 |
| 3 | 3/4 左侧 | photo_3 | 3/4 Left Upper | 过肩镜头、双人对话 | 脸部立体轮廓 + 身体厚度 |
| 4 | 3/4 右侧 | photo_4 | 3/4 Right Upper | 反向过肩镜头（正反打切换） | 与左侧对称的轮廓 |
| 5 | 正侧面 | photo_5 | Side Profile | 对峙、沉思、行走 | 鼻梁线 + 下颌线 + 发型侧面 |
| 6 | 3/4 背面 | photo_6 | 3/4 Back | 角色远望、回头一瞥 | 后脑发型 + 服装背面 + 肩线 |
| 7 | 仰视 | photo_7 | Low Angle | 英雄感、权威感、气势 | 下巴线 + 制服纽扣 + 气场 |
| 8 | 面部极致特写 | photo_8 | ECU Face | 情绪爆发、决策瞬间 | 虹膜高光 + 毛孔 + 微表情 + 皮肤质感 |

> **移除的机位**：正背面全身（photo_7 旧）和俯视（photo_8 旧）在漫剧中使用频率最低，如需可在 Step 4 分镜阶段通过 Prompt 直接描述。

### 3.5 3 张表情图设计原理

从叙事情绪曲线出发，表情图不是简单的"喜怒哀乐"，而是覆盖角色在故事中的完整情绪谱：

| # | 表情图 | 文件名 | 格数 | 设计逻辑 |
|---|--------|--------|------|---------|
| 1 | 核心四情绪 | expr_1 | 2×2 = 4格 | 角色**最常出现**的 4 种情绪（含中性态）|
| 2 | 弧线六表情 | expr_2 | 2×3 = 6格 | 按 `character_arc` 时间线排列角色在**故事各阶段**的标志表情 |
| 3 | 完整十情绪 | expr_3 | 2×5 = 10格 | 覆盖**完整情绪谱**：中性/坚定/冷怒/爆发怒/恐惧/紧张/悲伤/释然/轻蔑/痛苦 |

**10 格完整情绪谱参考**（根据角色性格从以下 10 类中选取最合适的变体）：

| # | 情绪类型 | 面部肌肉动作 | 典型场景 |
|---|---------|-------------|---------|
| 1 | 中性/冷静 (Neutral) | 放松的眉毛、自然闭合的嘴唇、平视 | 基准态，大部分镜头 |
| 2 | 坚定/决心 (Determined) | 微蹙眉、抿紧嘴唇、瞳孔聚焦 | 做出决策 |
| 3 | 冷怒 (Cold Fury) | 眼神变冷变窄、咬肌绷紧、鼻翼微张 | 克制的愤怒 |
| 4 | 爆发怒 (Rage) | 眉毛上挑、牙齿外露、面部涨红 | 情绪失控 |
| 5 | 恐惧/震惊 (Fear/Shock) | 瞳孔放大、嘴微张、额头冒汗 | 突发危机 |
| 6 | 紧张/焦虑 (Stressed) | 额头皱纹加深、嘴唇干燥、太阳穴冒汗 | 压力场景 |
| 7 | 悲伤/压抑 (Grief) | 闭眼、眉头下压、嘴角下沉 | 内心挣扎 |
| 8 | 释然/温柔 (Relief/Tender) | 肩膀下沉放松、眼角柔和、嘴角微上扬 | 劫后余生 |
| 9 | 轻蔑/质疑 (Contempt/Doubt) | 一侧嘴角微挑、眉毛不对称 | 对话冲突 |
| 10 | 痛苦 (Pain) | 紧闭双眼、眉心挤压、咬紧牙关 | 受伤/内心撕裂 |

### 3.6 3 张动态姿势设计原理

覆盖角色在故事中最关键的动作状态：

| # | 姿势类型 | 文件名 | 构图 | 用途 |
|---|---------|--------|------|------|
| 1 | 标志站姿 | pose_1 | 全身 | 角色标识、海报、转场定格 |
| 2 | 行走/奔跑 | pose_2 | 全身 | 场景转换、紧急撤离 |
| 3 | 坐姿/操作 | pose_3 | 半身 | 指挥室、对话、疲惫 |

### 3.7 `<TOK>` 在下游 Prompt 中的使用

- **image_prompt 中**：去掉 `<TOK> is a` 前缀，直接嵌入外观描述文字
- **禁止**在 `image_prompt` 中使用角色名（对应 MovieAgent 的 Coarse Plot 思路）
- 不同镜头中同一角色的描述文字**必须完全一致**（逐字匹配）
- 描述必须**完整复制，禁止缩写或改写**
- 服装替换时，仅替换 `wearing ...` 到下一个逗号之间的片段，使用 `[WARDROBE VARIANTS]` 中的对应条目

---

## 4. character_list/ 资产库结构

每个角色在 `character_list/` 下有独立的资产目录，按 4 类分组：

```
projects/{project_id}/character_list/
├── {CharName}/
│   ├── best.txt        ← 结构化角色参考手册（必须，AI 自动生成，含全部 Prompt）
│   ├── best.png        ← 主参考图：3/4 半身 + 标志姿势 + 标志表情
│   │
│   │── [MULTI-ANGLE] 8 张摄影机位 ──────────────────────
│   ├── photo_1.png     ← 正面全身（建立镜头：完整服装 + 身材比例 + 鞋子）
│   ├── photo_2.png     ← 正面半身（对话镜头：最高频构图 80%，胸部以上 + 手部）
│   ├── photo_3.png     ← 3/4 左侧上半身（过肩镜头：脸部立体感 + 身体厚度）
│   ├── photo_4.png     ← 3/4 右侧上半身（反向过肩：正反打切换用）
│   ├── photo_5.png     ← 正侧面（对峙镜头：鼻梁线 + 下颌线 + 发型侧面）
│   ├── photo_6.png     ← 3/4 背面（远望/回头：后脑发型 + 服装背面 + 回头一瞥）
│   ├── photo_7.png     ← 仰视（英雄感：下巴线 + 纽扣特写 + 气场仰望）
│   ├── photo_8.png     ← 面部极致特写 ECU（情绪爆发：虹膜高光 + 微表情 + 毛孔）
│   │
│   │── [EXPRESSION] 3 张表情图 ──────────────────────────
│   ├── expr_1.png      ← 4格核心情绪（角色最常出现的 4 种情绪 + 中性态）
│   ├── expr_2.png      ← 6格弧线表情（character_arc 时间线排列）
│   ├── expr_3.png      ← 10格完整情绪谱（覆盖全部表演需求）
│   │
│   │── [ACTION] 3 张动态姿势 ───────────────────────────
│   ├── pose_1.png      ← 标志站姿（海报级：角色标识 + 气场）
│   ├── pose_2.png      ← 行走/奔跑（场景转换 + 紧急状态）
│   └── pose_3.png      ← 坐姿/操作（指挥 + 对话 + 疲惫状态）
│
├── {CharName2}/
│   └── ...
```

### 资产分级（优先生图顺序）

| 优先级 | 资产 | 数量 | 说明 |
|--------|------|------|------|
| **P0 必须** | best.txt + best.png | 2 | 没有这两个文件无法进入 Step 4 |
| **P1 核心** | photo_1~4 + photo_8 + expr_1 | 6 | 覆盖最高频机位 + 核心表情 |
| **P2 重要** | photo_5~7 + expr_2~3 + pose_1~2 | 7 | 覆盖剩余机位 + 弧线/完整表情 + 动态姿势 |
| **P3 完善** | pose_3 | 1 | 坐姿/操作参考 |

用户按优先级逐步生成，P0 完成即可进入下一步骤，P1~P3 在后续生图时提供更精确的参考。

### 命名规则

- 目录名使用角色英文名或拼音（如 `Elsa`、`LinYuan`），不含空格
- `best.txt` 为**必须**文件（AI 自动生成，包含全部生图 Prompt）
- `best.png` 为**推荐**文件（用户复制 `[BEST.PNG]` Prompt 到 Gemini 手动生成后放入）
- `photo_N.png` 多视角参考图（复制 `[MULTI-ANGLE]` 段对应 Prompt 生成）
- `expr_N.png` 表情参考图（复制 `[EXPRESSION SHEET]` 段对应 Prompt 生成）
- `pose_N.png` 动态姿势图（复制 `[ACTION POSES]` 段对应 Prompt 生成）
- 所有参考图画风**必须一致**（由 `[STYLE]` 段统一控制）

### best.png 质量要求

- 必须清晰展示所有 `visual_identifiers` 中列出的特征
- 分辨率不低于 1024x1024
- 干净背景（纯色或简单渐变，推荐与角色色调互补的深色渐变）
- 角色正面或略偏 3/4 视角，半身构图（胸部以上）
- 展示 `wardrobe.default` 着装
- 展示 `signature_pose` + `signature_expression`
- 使用 `[STYLE]` 段定义的光照方案

### 表情图要求

- **expr_1（4格）**：覆盖角色**4 种核心情绪**，从 `emotional_reactions` 中选取最关键的 4 种
- **expr_2（6格）**：覆盖角色**完整情绪弧线**，按 `character_arc` 时间线排列
- **expr_3（10格）**：覆盖**完整情绪谱**，从 §3.5 的 10 类情绪中选取角色最合适的变体
- 每格表情须带**标签文字描述**（如 `NEUTRAL`, `COLD FURY`, `STRESSED` 等）
- 每格表情描述到**面部肌肉动作级别**（非抽象词）
- 所有格子中角色外观**必须一致**（同一服装、同一发型）
- 格子间用**清晰分隔线**区分

---

## 5. best.txt 各段落生成模板

以下模板定义了 `best.txt` 中每个段落的生成规则。AI 在执行 `/design-characters` 时，按模板逐段生成完整的 Character Reference Sheet。

### 5.1 `[BEST.PNG]` 主参考图 Prompt 模板

```
{style} style, high-detail character illustration, half-body portrait from chest up, {appearance_without_TOK}, {signature_pose}, {signature_expression}, {lighting_from_style}, solid clean gradient background in {complementary_dark_color}, masterpiece, best quality, ultra-detailed, sharp focus, {rendering_suffix}
```

**变量说明**：
| 变量 | 来源 | 说明 |
|------|------|------|
| `{style}` | `project.json.style` | 如 `anime`, `manga`, `comic` |
| `{appearance_without_TOK}` | `[TOK]` 段去掉 `<TOK> is a` 前缀 | 完整外观描述，逐字复制 |
| `{signature_pose}` | Visual ID Card | 标志姿势 |
| `{signature_expression}` | Visual ID Card | 标志表情 |
| `{lighting_from_style}` | `[STYLE]` 段的 Lighting 行 | 如 `dramatic rim lighting from above` |
| `{complementary_dark_color}` | 与角色主色调互补的深色 | 如角色深蓝 → 背景 `dark steel blue` |
| `{rendering_suffix}` | `[STYLE]` 段的 Rendering 行 | 如 `anime cel-shading` |

### 5.2 `[MULTI-ANGLE]` 8 机位 Prompt 模板（photo_1 ~ photo_8）

每张图遵循统一结构：`{style} + {机位指令} + {外观描述} + {机位专属修饰} + {背景} + {质量后缀}`

```
### photo_1 — FRONT FULL BODY (正面全身)
{style} style, full body front view, {appearance_without_TOK}, {trousers_and_shoes}, neutral standing pose with hands at sides, solid clean white background, masterpiece, best quality, {rendering_suffix}, character reference sheet

### photo_2 — FRONT MEDIUM SHOT (正面半身) ★ 最高频机位
{style} style, medium shot from waist up, front view, {appearance_without_TOK}, hands naturally at sides with one hand slightly raised, {signature_expression}, standard three-point lighting, solid clean light grey background, masterpiece, best quality, {rendering_suffix}

### photo_3 — 3/4 LEFT VIEW (左侧3/4身)
{style} style, upper body 3/4 view from the left, {appearance_without_TOK}, slight confident half-smile, dramatic side lighting from the right, solid clean light grey background, masterpiece, best quality, {rendering_suffix}

### photo_4 — 3/4 RIGHT VIEW (右侧3/4身)
{style} style, upper body 3/4 view from the right, {appearance_without_TOK}, calm neutral expression, dramatic side lighting from the left, solid clean medium grey background, masterpiece, best quality, {rendering_suffix}

### photo_5 — SIDE PROFILE (正侧面)
{style} style, side profile facing right, upper body, {appearance_hair_and_uniform_only}, {eye_color} eye in profile view, {jawline_description} and straight nose bridge, {skin_tone}, looking straight ahead with determined expression, solid clean white background, masterpiece, best quality, {rendering_suffix}

### photo_6 — 3/4 BACK VIEW (背面3/4)
{style} style, upper body 3/4 back view, {appearance_hair_back_detail}, {uniform_back_detail}, looking over left shoulder with one intense {eye_color} eye visible, {jawline_description} visible in profile, solid clean dark grey background, masterpiece, best quality, {rendering_suffix}

### photo_7 — LOW ANGLE / HEROIC (仰视) ★ 英雄感机位
{style} style, low angle view looking up at character, full body from below, {appearance_without_TOK}, chin prominently visible from below with {jawline_description}, {uniform_buttons_visible_from_below}, {trousers_and_shoes}, heroic imposing stance with legs apart, dramatic upward rim lighting, solid clean sky-tone gradient background, masterpiece, best quality, {rendering_suffix}

### photo_8 — EXTREME CLOSE-UP FACE (面部极致特写)
{style} style, extreme close-up face portrait filling entire frame, {appearance_hair_only}, {eye_full_detail_with_highlights}, individual eyelashes visible, {face_bone_structure}, skin pores and fine texture visible, {skin_tone}, {signature_expression}, dramatic chiaroscuro lighting with single strong key light, solid clean black background, masterpiece, best quality, ultra-detailed face, {rendering_suffix}
```

**8 机位关键规则**：
- photo_1 / photo_7 全身图必须包含**下装 + 鞋子描述**
- photo_2 正面半身是最高频镜头，需**最精细**的外观描述
- photo_4 右侧 3/4 与 photo_3 左侧 3/4 **光照方向镜像**
- photo_5 侧面只保留**该视角可见**的特征（省略被遮挡的配饰）
- photo_6 背面 3/4 需描述**回头一瞥**的动态感
- photo_7 仰视需描述**下巴线** + **纽扣从下方可见**，体现英雄/权威感
- photo_8 面部特写需增加**虹膜高光** + **皮肤毛孔** + **单根睫毛**级别细节

**背景颜色递进**：
```
白色(正面全身) → 浅灰(正面半身) → 浅灰(3/4左) → 中灰(3/4右) → 白色(侧面)
→ 深灰(背面3/4) → 天色渐变(仰视) → 黑色(特写)
```

### 5.3 `[EXPRESSION SHEET]` 3 张表情图 Prompt 模板（expr_1 ~ expr_3）

**expr_1 — 4 格核心情绪**：

```
{style} style, expression reference sheet, 2x2 grid layout with clear dividing lines and labels, same character in all 4 panels: {appearance_short}, TOP-LEFT: "{emotion_1_label}" — {emotion_1_muscle_detail}, TOP-RIGHT: "{emotion_2_label}" — {emotion_2_muscle_detail}, BOTTOM-LEFT: "{emotion_3_label}" — {emotion_3_muscle_detail}, BOTTOM-RIGHT: "{emotion_4_label}" — {emotion_4_muscle_detail}, solid clean white background, consistent standard lighting across all panels, masterpiece, best quality, {rendering_suffix}, character expression reference
```

**expr_2 — 6 格弧线表情**：

```
{style} style, expression reference sheet, 2x3 grid layout with clear dividing lines and labels, same character in all 6 panels: {appearance_short}, PANEL 1 "{arc_start_label}": {muscle_detail}, PANEL 2 "{arc_mid1_label}": {muscle_detail}, PANEL 3 "{arc_turning_label}": {muscle_detail}, PANEL 4 "{arc_mid2_label}": {muscle_detail}, PANEL 5 "{arc_climax_label}": {muscle_detail}, PANEL 6 "{arc_end_label}": {muscle_detail}, solid clean white background, consistent standard lighting, masterpiece, best quality, {rendering_suffix}, character expression reference
```

**expr_3 — 10 格完整情绪谱**：

```
{style} style, comprehensive expression reference sheet, 2x5 grid layout with clear dividing lines and labels, same character in all 10 panels: {appearance_short}, ROW 1 LEFT: "{NEUTRAL}" — {detail}, ROW 1 RIGHT: "{DETERMINED}" — {detail}, ROW 2 LEFT: "{COLD_FURY}" — {detail}, ROW 2 RIGHT: "{RAGE}" — {detail}, ROW 3 LEFT: "{FEAR}" — {detail}, ROW 3 RIGHT: "{STRESSED}" — {detail}, ROW 4 LEFT: "{GRIEF}" — {detail}, ROW 4 RIGHT: "{RELIEF}" — {detail}, ROW 5 LEFT: "{CONTEMPT}" — {detail}, ROW 5 RIGHT: "{PAIN}" — {detail}, solid clean white background, consistent standard lighting, masterpiece, best quality, {rendering_suffix}, character expression reference
```

**表情选取规则**：
- expr_1 的 4 格从 `emotional_reactions` 中选取**反差最大**的 4 种情绪
- expr_2 的 6 格按 `character_arc` 的时间线顺序排列：`starting_state → ... → turning_point → ... → ending_state`
- expr_3 的 10 格从 §3.5 的完整情绪谱中选取角色最合适的 10 种变体
- 每格表情描述需**具体到面部肌肉动作**（如 "narrowed eyes, clenched jaw muscles, flared nostrils"），**禁止**抽象词（如 "angry face"）

### 5.4 `[ACTION POSES]` 3 张动态姿势 Prompt 模板（pose_1 ~ pose_3）

```
### pose_1 — SIGNATURE POSE (标志站姿)
{style} style, full body character illustration, {appearance_without_TOK}, {trousers_and_shoes}, {signature_pose}, {signature_expression}, dramatic {lighting_from_style}, solid clean {complementary_dark_color} gradient background, masterpiece, best quality, dynamic composition, {rendering_suffix}

### pose_2 — WALKING / RUNNING (行走/奔跑)
{style} style, full body dynamic pose, {appearance_without_TOK}, {trousers_and_shoes}, {walking_or_running_action_for_character}, motion blur on limbs, fabric flowing with movement, determined expression, dramatic side lighting, solid clean dark gradient background, masterpiece, best quality, {rendering_suffix}

### pose_3 — SITTING / OPERATING (坐姿/操作)
{style} style, upper body seated pose, {appearance_without_TOK}, {sitting_action_for_character}, {sitting_expression}, overhead downward lighting, solid clean dark background with subtle ambient glow, masterpiece, best quality, {rendering_suffix}
```

**姿势定制规则**：
- pose_1 使用 Visual ID Card 的 `signature_pose`
- pose_2 根据角色**职业和剧情**定制（军人→急行军、学生→奔跑、老人→慢步行走）
- pose_3 根据角色**核心场景**定制（工程师→操作面板、指挥官→坐在指挥位、学生→伏案）

### 5.5 `[NEGATIVE PROMPT]` 模板

基础负面提示词 + 画风专属排除项：

```
low quality, blurry, deformed, extra fingers, bad anatomy, disfigured, poorly drawn face, mutation, mutated, ugly, watermark, text, multiple characters, {style_specific_negatives}, worst quality, jpeg artifacts, signature, username, extra limbs, missing limbs, fused fingers, too many fingers, long neck, cross-eyed, bad proportions, gross proportions, malformed limbs, extra arms, extra legs, poorly drawn hands
```

| style 值 | `{style_specific_negatives}` |
|----------|------------------------------|
| `anime` | `chibi, super deformed, realistic photo, 3d render` |
| `manga` | `color, gradient, 3d render, photograph` |
| `comic` | `manga style, anime style, photograph, 3d render` |
| `realistic` | `anime, cartoon, illustration, flat colors` |
| `watercolor` | `sharp edges, digital art, 3d render, photograph` |
| `pixel` | `smooth gradients, anti-aliasing, high resolution photograph` |

### 5.6 `[WARDROBE VARIANTS]` 服装变体模板

为角色的每套 `wardrobe` 方案生成**可直接替换的 Prompt 片段**。在分镜拆解（Step 4）中，通过替换 `wearing ...` 段落来切换服装。

```
### {WARDROBE_KEY} ({中文说明} — {使用场景})
wearing {完整服装描述，含材质/颜色/配饰/状态变化}
```

**必须包含的变体**：
- `DEFAULT`：必填，标准着装，大部分镜头使用
- 按剧情需要添加 `CRISIS` / `CASUAL` / `FORMAL` / `BATTLE` / `POST-CRISIS` 等

**每个变体描述需包含**：
- 服装主体（外套/衬衫/裤子）
- 服装状态（整齐/松散/脱下）
- 配饰变化（工牌位置、眼镜摘戴）
- 身体状态（汗渍、疲态等）
- 与 DEFAULT 的**可视差异点**（便于 AI 生图区分）

### 5.7 `[GENERATION ORDER]` 推荐生图顺序模板

此段落指引用户按**最优顺序**生成参考图，确保先有基准再有变体：

```
## [GENERATION ORDER] 推荐生图顺序

### 第一批（P0 必须 — 1 张）
1. best.png — 主参考图（所有后续图的画风基准）

### 第二批（P1 核心 — 6 张）
2. photo_1 — 正面全身
3. photo_2 — 正面半身（最高频）
4. photo_3 — 3/4 左侧
5. photo_4 — 3/4 右侧
6. photo_8 — 面部极致特写
7. expr_1 — 4格核心表情

### 第三批（P2 重要 — 7 张）
8. photo_5 — 正侧面
9. photo_6 — 背面3/4
10. photo_7 — 仰视（英雄感）
11. expr_2 — 6格弧线表情
12. expr_3 — 10格完整情绪谱
13. pose_1 — 标志站姿
14. pose_2 — 行走/奔跑

### 第四批（P3 完善 — 1 张）
15. pose_3 — 坐姿/操作

提示：每张图生成后请放入对应文件名。P0 完成即可进入 Step 4 (分镜拆解)。
```

### 5.8 Prompt 通用构建规则

- **禁止**在任何 Prompt 中使用角色名
- 所有 Prompt 以 `{style} style` 开头，确保画风统一
- 外观描述**逐字复制** `[TOK]` 段内容（去掉前缀），不做任何缩写
- 每张图添加 `solid clean {color} background` 确保背景不干扰角色特征
- 所有 Prompt 以 `masterpiece, best quality, {rendering_suffix}` 结尾
- 背景颜色按机位递进（见 §5.2 背景颜色递进表）
- 表情图统一使用**白色背景 + 标准光照**，确保格间一致性

---

## 6. 边界框（Bounding Box）规范

Shot 级镜头中的 `Involving Characters` 使用归一化边界框定位角色位置：

```json
{
  "Involving Characters": {
    "Elsa": [0.1, 0.06, 0.49, 1.0],
    "Anna": [0.58, 0.04, 0.95, 1.0]
  }
}
```

### 规则

- 坐标格式：`[x1, y1, x2, y2]`，值在 `[0, 1]` 范围内
- `(x1, y1)` 为左上角，`(x2, y2)` 为右下角
- 单角色：居中放置，宽度约 0.3-0.5
- 双角色：左侧 `(0.05-0.45)` + 右侧 `(0.55-0.95)`
- 三角色：左 `(0.02-0.30)` + 中 `(0.35-0.65)` + 右 `(0.70-0.98)`
- **不允许**边界框重叠
- 每镜头最多 3 个角色（推荐 1-2 个）
- 注意角色身高比例一致性（`body_proportions` 须反映在边界框高度中）

### 景别与边界框

| 景别 | y1 范围 | y2 范围 | 说明 |
|------|---------|---------|------|
| 全身 | 0.0-0.1 | 0.95-1.0 | 展示完整身体 |
| 半身 | 0.0-0.1 | 0.5-0.7 | 腰部以上 |
| 特写 | 0.0-0.1 | 0.3-0.5 | 面部或局部 |

---

## 7. 多角色视觉区分

在多角色画面中，必须确保角色可辨识、不混淆。

### 区分策略

1. **颜色主题分离**：每个角色有独立的颜色主调（从 `visual_identifiers` 提取），同画面角色颜色主调不应过近
2. **体型差异**：通过 `body_proportions` 建立差异（高/矮、壮/瘦）
3. **发型差异**：同画面角色发型应有明显区别（长/短、编辫/散发、颜色）
4. **服装差异**：同画面角色着装风格/颜色应有辨识度
5. **位置固定**：在同一 Scene 内，角色的左右位置应保持一致

### 多角色 image_prompt 格式

不含角色名，使用外观描述区分角色：

```
{style}, {shot_type}, {char_A_appearance} on the left, {char_B_appearance} on the right, {scene_description}
```

### 混淆风险检查

在设计阶段，检查以下情况并主动调整：
- 两个角色发色相同 → 通过发型/配饰区分
- 两个角色着装颜色接近 → 调整其中一方的 `wardrobe`
- 两个角色体型相似 → 通过标志特征（眼镜、帽子等）区分

---

## 8. characters.json Schema

`characters.json` 是角色数据的核心清单文件，存储于 `projects/{project_id}/characters.json`。

### 完整结构

```json
{
  "project_id": "20260228_080847_冰雪奇缘2漫剧版",
  "extracted_from": "script_synopsis.json",
  "extracted_at": "2026-02-28T08:10:00Z",
  "characters": [
    {
      "name": "Elsa",
      "description": "阿伦黛尔王国的女王，拥有强大的冰雪魔法力量，性格内敛但坚毅",
      "appearance_description": "金色长发编成辫子垂在左肩，穿着带有雪花结晶图案的冰蓝色渐变长裙，冰蓝色眼睛，白皙瓷器般的皮肤，高挑纤细身材",
      "tok_description": "<TOK> has long platinum blonde hair in a single braid draped over left shoulder, wearing a flowing ice-blue dress with snowflake crystal patterns, ice blue eyes, fair porcelain skin, tall slender build, regal graceful posture",
      "signature_pose": "hands raised with ice crystals forming between fingers",
      "signature_expression": "serene confidence with a hint of melancholy",
      "body_proportions": "tall, slender, graceful, regal posture",
      "wardrobe": {
        "default": "flowing ice-blue dress with snowflake crystal patterns, translucent cape",
        "casual": "light blue blouse with white pants, hair loosely tied",
        "battle": "crystalline armor with cape of frost, hair flowing free"
      },
      "visual_identifiers": ["ice crystal motifs", "blue color palette", "braid over left shoulder"],
      "distinguishing_features": "pointed ears from her winter crown, always bare feet on ice",
      "relationships": [
        { "character": "Anna", "relation": "姐妹" },
        { "character": "Kristoff", "relation": "妹妹的爱人" }
      ],
      "design_status": "designed",
      "asset_dir": "character_list/Elsa/",
      "voice": {
        "voice_type": "young_female",
        "speed": 1.0,
        "emotion_default": "calm"
      },
      "style_keywords": ["ice queen", "elegant", "blonde braid", "blue dress", "magical"]
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 必填 | Step 3a | Step 3b | 说明 |
|------|------|------|---------|---------|------|
| `name` | string | 是 | 填入 | — | 角色名，与 `character_list/` 目录名一致 |
| `description` | string | 是 | 填入 | — | 角色简介 |
| `appearance_description` | string | 是 | 填入 | 可细化 | 中文外观描述 |
| `tok_description` | string | 是* | 空 | 填入 | `<TOK>` 英文描述，Step 3b 填入 |
| `signature_pose` | string | 是* | 空 | 填入 | 标志姿势 |
| `signature_expression` | string | 是* | 空 | 填入 | 标志表情 |
| `body_proportions` | string | 是* | 空 | 填入 | 体型比例 |
| `wardrobe` | object | 是* | 空 | 填入 | 服装体系（至少含 `default`） |
| `visual_identifiers` | array | 是* | 空 | 填入 | 视觉识别特征列表 |
| `distinguishing_features` | string | 否 | 空 | 填入 | 独特特征 |
| `relationships` | array | 否 | 填入 | — | 角色关系 |
| `design_status` | enum | 是 | `"extracted"` | `"designed"` | 设计状态 |
| `asset_dir` | string | 是* | 空 | 填入 | 资产目录路径 |
| `voice` | object | 否 | 填入 | — | 配音设置 |
| `style_keywords` | array | 否 | 填入 | 可补充 | 风格关键词 |

*标注 `是*` 的字段在 Step 3a 为空，Step 3b 完成后必填。

### design_status 状态流转

```
extracted → designing → designed
                ↘ failed
```

- `extracted`：Step 3a 完成，已提取基础信息
- `designing`：Step 3b 进行中
- `designed`：Step 3b 完成，`tok_description`/`asset_dir`/Visual ID Card 已填入
- `failed`：设计失败（可重试）

---

## 9. 角色设计流程（Step 3b: /design-characters）

为单个角色构建完整的视觉身份并生成结构化 Character Reference Sheet（`best.txt`），产出 15 张参考图的完整 Prompt 集。

### 前置数据读取

执行前必须读取以下文件：

| 文件 | 用途 |
|------|------|
| `project.json` | 读取 `style`（画风）、`title`（项目名）、`genre`（题材）|
| `characters.json` | 读取目标角色全部数据：`appearance_description`、`emotional_reactions`、`character_arc`、`personality` 等 |
| `script_synopsis.json` | 读取题材信息和场景列表，辅助确定色调、光照和动态姿势 |

### 执行步骤（12 步，4 个阶段）

#### Phase 1: 设计 Visual ID Card（步骤 1-6）

1. **更新状态**：将 `characters.json` 中该角色的 `design_status` 改为 `"designing"`

2. **设计服装体系 `wardrobe`**：
   - 基于 `appearance_description` 确定 `default` 着装
   - 基于剧情阶段设计额外服装变体（`crisis` / `casual` / `battle` 等）
   - 每套服装描述需包含：材质、颜色、纽扣/拉链状态、配饰位置、身体状态
   - **新增**：为全身图设计下装（裤子/裙子 + 鞋子），写入 `wardrobe` 的 `_lower` 后缀字段

3. **确定标志姿势和表情**：
   - `signature_pose`：从角色性格/职业/核心场景推导
   - `signature_expression`：从 `personality.core_traits` 和 `emotional_reactions` 推导
   - **新增** `action_poses`：设计 3 个动态姿势（标志站姿 / 行走奔跑 / 坐姿操作）

4. **提炼视觉识别特征 `visual_identifiers`**（3-5 个）：
   - 必须是**跨镜头可辨识**的特征（颜色主题、标志配饰、发型特征、体型特征）
   - 与同项目其他角色做**差异化检查**

5. **确定体型 `body_proportions`** 和 `distinguishing_features`

6. **构建 `<TOK>` 核心外观描述**：
   - 综合以上所有信息
   - 按 §3.2 的优先级排列
   - 确保所有 `visual_identifiers` 都出现在描述中

#### Phase 2: 生成结构化 best.txt（步骤 7-8）

7. **创建资产目录** `character_list/{CharName}/`

8. **生成 best.txt**（按 §3.1 的 8 段结构逐段生成）：

   ```
   ┌─ Header ──────────────────────────────────────────────────┐
   │ CHARACTER REFERENCE SHEET — {中文名} ({英文名})             │
   │ Project / Style / Role / Total Assets: 15 张               │
   ├─ §1 [TOK] ────────────────────────────────────────────────┤
   │ 从 Step 6 的 <TOK> 描述直接写入                             │
   ├─ §2 [STYLE] ──────────────────────────────────────────────┤
   │ 读取 project.json.style → 查画风映射表 → 填 6 个维度        │
   ├─ §3 [BEST.PNG] ───────────────────────────────────────────┤
   │ 套用 §5.1 模板                                             │
   ├─ §4 [MULTI-ANGLE] ────────────────────────────────────────┤
   │ 套用 §5.2 模板，逐张生成 photo_1 ~ photo_8（8 个机位）       │
   │ photo_1/7 需补充下装描述                                     │
   │ photo_7 需描述仰视透视                                      │
   ├─ §5 [EXPRESSION SHEET] ────────────────────────────────────┤
   │ expr_1: 从 emotional_reactions 选 4 种反差最大的情绪         │
   │ expr_2: 从 character_arc 按时间线排列 6 种表情              │
   │ expr_3: 从 §3.5 完整情绪谱选 10 种变体                      │
   │ 每格须写到面部肌肉动作级别                                   │
   ├─ §6 [ACTION POSES] ───────────────────────────────────────┤
   │ pose_1: 标志站姿（使用 signature_pose）                     │
   │ pose_2: 行走/奔跑（根据剧情定制）                            │
   │ pose_3: 坐姿/操作（根据职业/场景定制）                        │
   ├─ §7 [NEGATIVE PROMPT] ─────────────────────────────────────┤
   │ 基础词 + 画风专属排除项（查 §5.5 表）                        │
   ├─ §8 [WARDROBE VARIANTS] ───────────────────────────────────┤
   │ 为 wardrobe 中每个键生成可替换 Prompt 片段                   │
   ├─ §9 [GENERATION ORDER] ────────────────────────────────────┤
   │ 推荐生图顺序（P0→P1→P2→P3 四批次）                         │
   └───────────────────────────────────────────────────────────┘
   ```

#### Phase 3: 更新数据（步骤 9-10）

9. **更新 `characters.json`**：
   - 填入 `tok_description`（与 best.txt 的 `[TOK]` 段完全一致）
   - 填入 `signature_pose`、`signature_expression`、`body_proportions`
   - 填入 `wardrobe`、`visual_identifiers`、`distinguishing_features`
   - 填入 `asset_dir`: `character_list/{CharName}/`
   - 设计状态改为 `"designed"`

10. **更新 `status.json`**（如果是最后一个角色）

#### Phase 4: 输出用户指引（步骤 11-12）

11. **输出生图指南摘要**：
    - 告知用户 `best.txt` 已生成，包含 **15 张参考图的完整 Prompt**
    - 展示资产分级表（P0/P1/P2/P3 四个优先级）
    - **强调** P0（best.png）必须先完成，后续图以 best.png 为画风基准
    - 提示用户每张图生成后放入对应文件名

12. **展示各类资产的用途概览**：
    ```
    📐 8 机位视角 — 覆盖漫剧最高频拍摄角度
    😊 3 张表情图（4格+6格+10格）— 覆盖完整情绪谱
    🏃 3 张动态姿势 — 标志/行走/坐姿
    ```

### 数据 I/O

- **读取**：`Read` 工具读取 `project.json`、`characters.json`、`script_synopsis.json`
- **写入**：`Write` 工具写入 `best.txt`（完整 Reference Sheet）、更新 `characters.json`
- **目录创建**：`Bash` 工具创建 `character_list/{CharName}/`

### `/design-characters all` 批量模式

当用户执行 `/design-characters all` 时：
1. 遍历 `characters.json` 中所有 `design_status == "extracted"` 的角色
2. 对每个角色执行上述 12 步流程
3. 在设计第 2+ 个角色时，执行**多角色差异化检查**（§7）
4. 所有角色设计完成后，检查项目是否满足 `characters_designed` 状态条件
5. 满足则更新 `status.json` 为 `characters_designed`

---

## 10. 质量检查清单

### Step 3a 提取阶段

- [ ] `characters.json` 包含所有有名角色
- [ ] 每个角色有 `appearance_description`（外观描述非空且具体）
- [ ] `design_status` 初始为 `"extracted"`
- [ ] 角色关系 `relationships` 已梳理
- [ ] 无重复角色（同名消歧已处理）

### Step 3b — best.txt 结构完整性（8 段）

- [ ] `best.txt` 包含完整的 8 段结构（Header + TOK + STYLE + BEST.PNG + MULTI-ANGLE + EXPRESSION + ACTION + NEGATIVE + WARDROBE + GENERATION ORDER）
- [ ] Header 包含项目名 / 画风 / 角色定位 / Total Assets: 15 张
- [ ] `[TOK]` 段以 `<TOK> is a` 或 `<TOK> has` 开头
- [ ] `[TOK]` 段包含年龄 + 性别 + 种族特征
- [ ] `[TOK]` 段描述具体、可重复（无模糊词汇）
- [ ] `[TOK]` 段包含所有 `visual_identifiers` 中的特征
- [ ] `[STYLE]` 段包含 6 个维度（Art style / Color palette / Lighting / Line weight / Eye style / Rendering）
- [ ] `[STYLE]` 段的画风与 `project.json.style` 一致
- [ ] `[BEST.PNG]` Prompt 完整且以 `masterpiece, best quality` 结尾

### Step 3b — 8 机位视角

- [ ] `[MULTI-ANGLE]` 段包含 photo_1 ~ photo_8 共 8 张机位 Prompt
- [ ] photo_1 (正面全身) 包含下装 + 鞋子描述
- [ ] photo_2 (正面半身) 作为最高频机位，外观描述最精细
- [ ] photo_3 (3/4 左) 和 photo_4 (3/4 右) 光照方向镜像
- [ ] photo_5 (侧面) 仅描述该视角可见的特征
- [ ] photo_6 (背面 3/4) 包含回头一瞥动态
- [ ] photo_7 (仰视) 包含下巴线 + 仰视透视描述 + 下装鞋子
- [ ] photo_8 (面部 ECU) 包含虹膜高光 + 皮肤毛孔 + 睫毛细节

### Step 3b — 3 张表情图

- [ ] `[EXPRESSION SHEET]` 段包含 expr_1 (4格) + expr_2 (6格) + expr_3 (10格)
- [ ] expr_1 的 4 种情绪覆盖角色性格的**反差面**
- [ ] expr_2 的 6 种表情按 `character_arc` 时间线排列
- [ ] expr_3 的 10 种表情覆盖完整情绪谱（从 §3.5 的 10 类中选取）
- [ ] 每格表情描述到**面部肌肉动作**级别（非抽象词）
- [ ] 每格带**标签文字描述**

### Step 3b — 3 张动态姿势

- [ ] `[ACTION POSES]` 段包含 pose_1 (标志站姿) + pose_2 (行走/奔跑) + pose_3 (坐姿/操作)
- [ ] pose_1 使用 `signature_pose`
- [ ] pose_2 根据角色职业/剧情定制
- [ ] pose_3 根据角色核心场景定制

### Step 3b — 其他段落

- [ ] `[NEGATIVE PROMPT]` 包含画风专属排除项
- [ ] `[WARDROBE VARIANTS]` 至少包含 `DEFAULT` 变体
- [ ] 每个 `wardrobe` 键都有对应的可替换 Prompt 片段
- [ ] `[GENERATION ORDER]` 包含 P0→P3 四批次生图顺序

### Step 3b — 数据一致性

- [ ] `characters.json` 中的 `tok_description` 与 `best.txt` 的 `[TOK]` 段**逐字一致**
- [ ] Visual ID Card 完整（`signature_pose`、`signature_expression`、`body_proportions` 非空）
- [ ] `wardrobe` 至少包含 `default` 方案
- [ ] `visual_identifiers` 包含 3-5 个显著视觉标记
- [ ] `characters.json` 中的 `design_status` 为 `"designed"`
- [ ] `asset_dir` 指向正确的 `character_list/{CharName}/` 目录
- [ ] `best.txt` 已写入对应目录

### 多角色一致性

- [ ] 同画面角色颜色主调不冲突
- [ ] 同画面角色发型有明显区别
- [ ] 同画面角色体型有可辨识差异
- [ ] `<TOK>` 描述在所有镜头中逐字一致
- [ ] `image_prompt` 中不含任何角色名
- [ ] 所有角色的 `best.txt` 使用相同的 `{style} style` 前缀

### 参考图质量（用户手动生成后检查）

- [ ] `best.png` 清晰展示所有 `visual_identifiers`
- [ ] `best.png` 使用 `wardrobe.default` 着装
- [ ] 8 机位参考图与 `best.png` 画风一致
- [ ] 表情图 (expr_1) 4 格情绪区分明显、角色可辨识
- [ ] 表情图 (expr_2) 6 格表情覆盖角色弧线
- [ ] 表情图 (expr_3) 10 格覆盖完整情绪谱
- [ ] 动态姿势图 (pose_1~3) 角色比例和外观与 best.png 一致
- [ ] 所有参考图背景干净，不影响角色特征识别
