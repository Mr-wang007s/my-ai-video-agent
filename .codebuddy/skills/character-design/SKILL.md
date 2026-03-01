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

## 3. `<TOK>` 外观描述规范

`best.txt` 使用 `<TOK>` 占位符格式描述角色外观，是角色视觉一致性的核心锚点。

### 格式

```
<TOK> has long blonde hair in a braid, wearing a sparkling blue dress, ice blue eyes, fair skin, elegant posture
```

### 构建规则

- 以 `<TOK>` 开头（占位符，在 `image_prompt` 中替换为完整外观描述）
- 使用英文描述
- 包含以下要素（按重要性排序）：
  1. 标志特征（眼镜、疤痕、特殊饰品）——放在最前面
  2. 发型和发色
  3. 服装（使用 `wardrobe.default` 方案）
  4. 眼睛颜色/特征
  5. 肤色
  6. 体型/身高
  7. 姿态/气质
- 使用具体的、不可变的特征描述
- **避免**模糊词汇（如 "handsome"、"beautiful"、"pretty"）
- 单行文本，不换行
- 每个 `visual_identifiers` 中的特征都必须出现在描述中

### 示例

```
<TOK> has short messy black hair, thin-framed glasses, wearing a white dress shirt with loosened tie, dark brown eyes, average build, slight dark circles under eyes
```

```
<TOK> wears a purple cape over a dark dress, has auburn hair in twin braids, green eyes, freckles across nose, warm smile
```

```
<TOK> has long platinum blonde hair in a single braid draped over left shoulder, wearing a flowing ice-blue dress with snowflake crystal patterns, ice blue eyes, fair porcelain skin, tall slender build, regal graceful posture
```

### `<TOK>` 在 Prompt 中的使用

- **image_prompt 中**：去掉 `<TOK>` 前缀，直接嵌入外观描述文字
- **禁止**在 `image_prompt` 中使用角色名（对应 MovieAgent 的 Coarse Plot 思路）
- 不同镜头中同一角色的描述文字**必须完全一致**（逐字匹配）
- 描述必须**完整复制，禁止缩写或改写**

---

## 4. character_list/ 资产库结构

每个角色在 `character_list/` 下有独立的资产目录：

```
projects/{project_id}/character_list/
├── {CharName}/
│   ├── best.png       ← 最佳参考图（用户在 Gemini 等平台手动生成后放入）
│   ├── best.txt       ← <TOK> 外观描述（必须，英文，由 AI 生成）
│   ├── photo_1.png    ← 正面视角参考图
│   ├── photo_2.png    ← 3/4 侧面视角
│   ├── photo_3.png    ← 侧面轮廓
│   ├── photo_4.png    ← 3/4 背面视角（新增）
│   ├── photo_5.png    ← 面部特写 + 表情
│   ├── photo_6.png    ← 全身 + 动作姿态
│   └── photo_7.png    ← 表情变化图（新增：喜/怒/哀/惊）
├── {CharName2}/
│   └── ...
```

### 命名规则

- 目录名使用角色英文名或拼音（如 `Elsa`、`XiaoWang`），不含空格
- `best.txt` 为**必须**文件（AI 自动生成）
- `best.png` 为**推荐**文件（用户在 Gemini 手动生成后放入）
- `photo_N.png` 按序号命名（N=1,2,3...），推荐 5-7 张
- 多角度参考图风格必须与 `best.png` 一致

### best.png 质量要求

- 必须清晰展示所有 `visual_identifiers` 中列出的特征
- 分辨率不低于 1024x1024
- 干净背景（纯色或简单渐变）
- 角色正面或略偏 3/4 视角
- 展示 `wardrobe.default` 着装
- 展示 `signature_pose`（推荐）或自然站姿

---

## 5. 参考图 Prompt 模板

以下模板供用户在 Gemini / DALL-E 等平台手动生成角色参考图。

### best.png Prompt 模板

```
{style} style, {shot_type} portrait, {appearance_description_without_TOK}, {signature_pose}, clean background, high quality, high resolution, character reference sheet
```

**示例**：
```
manga style, half-body portrait, long platinum blonde hair in a single braid draped over left shoulder, wearing a flowing ice-blue dress with snowflake crystal patterns, ice blue eyes, fair porcelain skin, tall slender build, regal graceful posture, hands raised with ice crystals forming between fingers, clean background, high quality, high resolution, character reference sheet
```

### 多角度 photo_N.png Prompt 模板

```
photo_1: "{style} style, front view, {appearance}, neutral standing pose, clean background, full body"
photo_2: "{style} style, 3/4 view from left, {appearance}, slight smile, clean background, upper body"
photo_3: "{style} style, side profile facing right, {appearance}, looking ahead, clean background, upper body"
photo_4: "{style} style, 3/4 back view, {appearance}, looking over shoulder, clean background, upper body"
photo_5: "{style} style, close-up face, {appearance}, {signature_expression}, clean background"
photo_6: "{style} style, full body, {appearance}, {signature_pose}, clean background, dynamic angle"
photo_7: "{style} style, expression sheet, 4 panels, {appearance}, showing happy/angry/sad/surprised expressions, clean background, character reference"
```

### Prompt 构建规则

- `{style}` 替换为项目统一画风（如 `manga`、`anime`、`semi-realistic`）
- `{appearance}` 替换为 `<TOK>` 描述去掉 `<TOK>` 前缀的完整文本
- `{signature_pose}` 和 `{signature_expression}` 从 Visual ID Card 获取
- **禁止**在 Prompt 中使用角色名
- 所有参考图使用相同的 `{style}` 前缀，确保画风一致
- 每张图添加 `clean background` 确保背景不干扰角色特征

### Negative Prompt（通用）

```
low quality, blurry, deformed, extra fingers, bad anatomy, disfigured, poorly drawn face, mutation, mutated, ugly, watermark, text, multiple characters
```

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

为单个角色构建完整的视觉身份并生成参考图 Prompt。

### 执行步骤

1. **更新状态**：将 `characters.json` 中该角色的 `design_status` 改为 `"designing"`
2. **构建 Visual ID Card**：
   - 基于 `appearance_description` 确定基础外观
   - 设计 `wardrobe` 各方案（`default` 必填，按需添加 `casual`/`battle`/`formal`）
   - 确定 `signature_pose`（从角色性格/能力推导）
   - 确定 `signature_expression`（从角色性格推导）
   - 提炼 `visual_identifiers`（3-5 个最显著的视觉标记）
   - 记录 `distinguishing_features`
   - 确定 `body_proportions`
3. **生成 `<TOK>` 描述**：综合 Visual ID Card 信息构建英文描述
4. **创建资产目录** `character_list/{CharName}/`
5. **写入 best.txt**：保存 `<TOK>` 描述
6. **生成 Gemini Prompt**：
   - 输出 best.png 的完整文生图 Prompt（使用模板）
   - 输出 photo_1 ~ photo_7 的多角度 Prompt（使用模板）
   - 输出通用 Negative Prompt
7. **更新 characters.json**：
   - 填入 `tok_description`、`asset_dir`
   - 填入 `signature_pose`、`signature_expression`、`body_proportions`
   - 填入 `wardrobe`、`visual_identifiers`、`distinguishing_features`
   - 设计状态改为 `"designed"`

### 数据 I/O

- **读取**：`Read` 工具读取 `characters.json`、`script_synopsis.json`
- **写入**：`Write` 工具写入 `best.txt`、更新 `characters.json`
- **目录创建**：`Bash` 工具创建 `character_list/{CharName}/`

---

## 10. 质量检查清单

### Step 3a 提取阶段

- [ ] `characters.json` 包含所有有名角色
- [ ] 每个角色有 `appearance_description`（外观描述非空且具体）
- [ ] `design_status` 初始为 `"extracted"`
- [ ] 角色关系 `relationships` 已梳理
- [ ] 无重复角色（同名消歧已处理）

### Step 3b 设计阶段

- [ ] `best.txt` 使用 `<TOK>` 开头的英文描述
- [ ] `best.txt` 描述具体、可重复（无模糊词汇如 "beautiful"、"handsome"）
- [ ] `best.txt` 包含所有 `visual_identifiers` 中的特征
- [ ] Visual ID Card 完整（`signature_pose`、`signature_expression`、`body_proportions` 非空）
- [ ] `wardrobe` 至少包含 `default` 方案
- [ ] `visual_identifiers` 包含 3-5 个显著视觉标记
- [ ] `characters.json` 中的 `design_status` 为 `"designed"`
- [ ] `asset_dir` 和 `tok_description` 已正确填入
- [ ] `character_list/{CharName}/` 目录已创建
- [ ] `best.txt` 已写入对应目录
- [ ] Gemini Prompt 已输出（best.png + 多角度 photo_1~7）

### 多角色一致性

- [ ] 同画面角色颜色主调不冲突
- [ ] 同画面角色发型有明显区别
- [ ] 同画面角色体型有可辨识差异
- [ ] `<TOK>` 描述在所有镜头中逐字一致
- [ ] `image_prompt` 中不含任何角色名

### 参考图质量（用户手动生成后检查）

- [ ] `best.png` 清晰展示所有 `visual_identifiers`
- [ ] `best.png` 使用 `wardrobe.default` 着装
- [ ] 多角度参考图与 `best.png` 画风一致
- [ ] 表情变化图（photo_7）覆盖主要情绪
