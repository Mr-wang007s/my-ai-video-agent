---
name: prompt-image
description: "图像提示词工程。为图像生成平台（Gemini / DALL-E / SD）构造高质量 image_prompt，确保角色外观一致性和画面构图质量。"
team:
  enabled: true
  pattern: review
  coordinator: art-director
  roles:
    - name: art-director
      type: coordinator
      expertise: "Visual art direction, style consistency"
      system_prompt: |
        You are the art director. When generating image prompts:
        1. Generate prompts following the prompt-image Skill rules
        2. Send to consistency-checker for review
        3. Iterate if issues found
        Ensure style prefix consistency across all shots.
      responsibilities:
        - Generate image_prompts using full Skill knowledge
        - Maintain style prefix consistency across all shots
        - Ensure composition variety
    - name: consistency-checker
      type: reviewer
      expertise: "Character appearance consistency, prompt format compliance"
      system_prompt: |
        Review image_prompts for:
        1. Character appearance text is IDENTICAL across shots (byte-level match)
        2. No character names appear anywhere
        3. Style prefix is consistent
        4. Composition rules are appropriate for shot type
        5. Negative prompt is included and genre-appropriate
        Report specific issues with shot IDs.
      responsibilities:
        - Byte-level comparison of character descriptions across shots
        - Format compliance checking
        - Style consistency validation
  coordination:
    merge_strategy: sequential-pipeline
    review_required: true
---

# 图像提示词工程

为图像生成平台（Gemini / DALL-E / SD）构造高质量 image_prompt，确保角色外观一致性和画面构图质量。本 Skill 覆盖角色参考图生成（Step 3b）和分镜关键帧生成（Step 4c）两个阶段。

## 在流水线中的位置

| 步骤 | 用途 | 输入 | 输出 |
|------|------|------|------|
| Step 3b: 角色设计 | 生成角色参考图 Prompt | `characters.json` 中的外观描述 | 角色卡 Prompt（供用户在 Gemini 手动生成 best.png） |
| Step 4c: 镜头创建 | 生成每镜关键帧 Prompt | Shot 数据 + 角色外观 + Scene Annotation | `image_prompt` 字段写入 `script_breakdown.json` |
| Step 5: 导出指南 | 输出用户可复制的 Prompt 列表 | `script_breakdown.json` | 制作指南文档 |

## 1. image_prompt 构造公式

每个 image_prompt 按以下公式组装：

```
{style_prefix}, {shot_type}, {scene_description}, {FULL_character_appearance}, {lighting}, {mood}, {composition_rule}, {quality_tags}
```

### 字段说明

| 字段 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `style_prefix` | 是 | 风格前缀，同一项目内保持一致 | `manga style, cel shading,` |
| `shot_type` | 是 | 镜头类型（英文） | `medium shot`, `close-up`, `wide shot` |
| `scene_description` | 是 | 场景环境描述 | `night castle balcony overlooking snow-covered mountains` |
| `FULL_character_appearance` | 是（有角色时） | 完整角色外观描述（见第 3 节规则） | 见下方 GOOD 示例 |
| `lighting` | 是 | 光影描述 | `moonlight`, `warm sunset`, `dim candlelight` |
| `mood` | 是 | 氛围/情绪 | `ethereal atmosphere`, `tense mood`, `warm and cozy` |
| `composition_rule` | 推荐 | 构图规则（见第 4 节） | `rule of thirds`, `centered composition` |
| `quality_tags` | 推荐 | 质量标签 | `high quality, detailed, 4k` |

## 2. 风格前缀体系

项目初始化时确定风格前缀，**整个项目内所有 image_prompt 必须使用同一前缀**。

| 风格 | 前缀文本 | 适用题材 | 视觉特点 |
|------|---------|---------|---------|
| 日式漫画 | `manga style, cel shading,` | 校园、奇幻、少年热血 | 清晰轮廓线、平涂色块、夸张表情 |
| 日式动画 | `anime style, vibrant colors,` | 动作、冒险、魔法 | 鲜艳配色、动态光影、精致细节 |
| 半写实 | `semi-realistic, detailed,` | 都市、悬疑、历史 | 接近真实比例、细腻纹理、自然光影 |
| 水彩 | `watercolor style, soft edges,` | 文艺、治愈、回忆 | 柔和边缘、渐变色彩、留白意境 |
| 赛博朋克 | `cyberpunk style, neon lights,` | 科幻、未来、赛博 | 霓虹色调、金属质感、高对比度 |

### 风格选择指引

- 根据剧本题材选择最匹配的风格
- 同一项目中**禁止**混用不同风格前缀
- 如果剧本跨越多种氛围（如回忆与现实交替），使用同一前缀 + 不同 `lighting` 和 `mood` 区分

## 3. 角色外观嵌入规则

### 核心原则

角色外观描述是 image_prompt 中保障角色一致性的**关键手段**。

### `<TOK>` 描述提取

角色的外观描述存储在 `character_list/{CharName}/best.txt` 中，格式为：

```
<TOK> has long blonde hair in a braid, wearing a sparkling blue dress, ice blue eyes, fair skin, elegant posture
```

在 image_prompt 中使用时，**去掉 `<TOK>` 前缀**，保留完整描述：

```
a woman with long blonde hair in a braid, wearing a sparkling blue dress, ice blue eyes, fair skin, elegant posture
```

### 强制规则

1. **完整复制**：必须使用 `<TOK>` 描述的完整文本（去掉 `<TOK>` 前缀），**禁止缩写、概括、改写或省略任何部分**
2. **逐字一致**：同一角色在整个 `script_breakdown.json` 的所有 Shot 中，外观描述文本**必须逐字相同**（byte-level match）
3. **禁止角色名**：image_prompt 中**绝对禁止**出现角色名（对应 MovieAgent 的 Coarse Plot 思路），只使用外观描述
4. **每角色必含**：Shot 中每个可见角色都必须嵌入完整外观描述

### BAD vs GOOD 示例

**BAD** (too vague):
```
a woman in purple dress standing on a balcony
```
- 缺少发型发色、眼睛颜色、肤色、服装细节
- 无法在不同镜头间保持一致

**GOOD** (complete):
```
manga style, medium shot, night castle balcony, a woman with long blonde hair 
  in a braid wearing a flowing purple-white gradient dress with ice crystal patterns ice blue eyes 
  fair porcelain skin elegant regal posture standing alone gazing at mountains, moonlight, 
  ethereal atmosphere, rule of thirds
```
- 完整的外观描述（发型、发色、服装细节、眼睛颜色、肤色、姿态）
- 无角色名
- 包含风格前缀、镜头类型、场景、光影、氛围、构图

### 多角色 image_prompt 格式

当画面中有多个角色时，使用位置描述区分：

```
{style_prefix}, {shot_type}, {char_A_full_appearance} on the left, {char_B_full_appearance} on the right, {scene_description}, {lighting}, {mood}, {composition_rule}
```

示例：
```
anime style, vibrant colors, medium shot, a woman with long blonde hair in a braid 
  wearing a sparkling blue dress ice blue eyes fair skin elegant posture on the left, 
  a young woman with auburn hair in twin braids wearing a green bodice with black skirt 
  green eyes freckles warm smile on the right, inside a warm castle hallway with tapestries, 
  warm candlelight, joyful atmosphere, rule of thirds
```

规则：
- 每个角色都使用完整的 `<TOK>` 外观描述（去掉前缀）
- 使用 `on the left` / `on the right` / `in the center` 定位
- 每镜头最多 3 个角色（推荐 1-2 个）
- 位置描述需与 `Involving Characters` 中的边界框对应

## 4. 构图规则映射

根据镜头类型和叙事需要选择构图规则：

| 构图方式 | 英文 Prompt 文本 | 适用场景 | 说明 |
|---------|-----------------|---------|------|
| 三分法 | `rule of thirds composition` | 大多数镜头的默认构图 | 主体放在三等分线交点 |
| 中心构图 | `centered composition, symmetrical` | 正面特写、庄重/对称场面 | 主体居中，对称均衡 |
| 对角线 | `diagonal composition, dynamic` | 动作场面、追逐、冲突 | 对角线布局增加动态感 |
| 引导线 | `leading lines toward subject` | 走廊、道路、透视场景 | 线条引导视线至主体 |
| 框中框 | `frame within frame` | 窗户、门框、拱门场景 | 用环境元素框住主体 |

### 构图选择建议

| 镜头类型 | 推荐构图 |
|---------|---------|
| 远景/全景 | 三分法、引导线 |
| 中景（对话） | 三分法、框中框 |
| 近景/特写 | 中心构图、三分法 |
| 动作镜头 | 对角线、引导线 |
| 过肩镜头 | 三分法 |
| 俯拍/仰拍 | 中心构图、对角线 |

### 构图多样性要求

- 连续镜头**避免**重复使用同一构图规则
- 每个 Scene 内至少使用 2 种不同构图
- art-director 在生成时需有意识地交替使用

## 5. Negative Prompt 体系

### 基础模板（所有题材通用）

```
low quality, blurry, deformed, extra fingers, bad anatomy, disfigured, poorly drawn face, mutation, mutated, ugly, watermark, text
```

### 按题材定制

| 题材 | 基础模板 + 追加内容 |
|------|-------------------|
| 校园/日常 | + `fantasy elements, armor, weapons, blood` |
| 奇幻/魔法 | + `modern clothing, cars, phones, realistic photo` |
| 都市/悬疑 | + `bright colors, cute style, chibi, fantasy creatures` |
| 动作/热血 | + `static pose, calm expression, pastel colors` |
| 治愈/文艺 | + `violence, blood, dark atmosphere, horror elements` |
| 科幻/赛博 | + `medieval, nature, pastoral, hand-drawn sketch` |
| 历史/古风 | + `modern technology, neon, cyberpunk, contemporary clothing` |

### 使用规则

- 每个 image_prompt 都**必须**附带 negative prompt
- negative prompt 在同一项目内保持一致（基于项目题材选择一次）
- 输出格式：在 prompt 后另起一行以 `Negative prompt:` 开头

## 6. 平台适配层

同一个镜头可能需要在不同平台生成图片。以下是各平台的 prompt 格式差异：

### Gemini

- **格式**：自然语言描述，完整句子
- **特点**：强调场景叙事，理解能力强
- **Prompt 写法**：直接使用标准 image_prompt 公式输出
- **示例**：
  ```
  manga style, cel shading, medium shot, a moonlit castle balcony where a woman with 
  long blonde hair in a braid wearing a flowing purple-white gradient dress with ice crystal 
  patterns ice blue eyes fair porcelain skin elegant regal posture gazes out at snow-covered 
  mountains, soft moonlight casting blue shadows, ethereal and melancholic atmosphere, 
  rule of thirds composition, high quality, detailed
  ```

### DALL-E 3

- **格式**：详细描述，支持长 prompt（最长 4000 字符）
- **特点**：对细节描述响应良好，可补充更多环境细节
- **Prompt 写法**：在标准公式基础上扩展场景细节和质量描述
- **示例**：
  ```
  manga style, cel shading, medium shot of a moonlit castle balcony. A woman with long 
  blonde hair in a braid wearing a flowing purple-white gradient dress with ice crystal 
  patterns ice blue eyes fair porcelain skin elegant regal posture stands at the stone 
  railing gazing at snow-covered mountains in the distance. The balcony has intricate 
  ice-like carvings on the pillars. Soft moonlight casts blue-tinted shadows across the 
  scene. Ethereal and melancholic atmosphere. Rule of thirds composition with the character 
  positioned at the left third. High quality, detailed illustration, 4k resolution.
  ```

### Stable Diffusion

- **格式**：标签式，逗号分隔关键词
- **特点**：支持权重语法 `(keyword:1.2)`，适合精确控制
- **Prompt 写法**：将公式各字段拆为独立标签，关键特征加权重
- **示例**：
  ```
  (manga style:1.3), cel shading, medium shot, moonlit castle balcony, (long blonde hair 
  in a braid:1.2), (flowing purple-white gradient dress:1.2), ice crystal patterns, 
  (ice blue eyes:1.1), fair porcelain skin, elegant regal posture, snow-covered mountains, 
  moonlight, ethereal atmosphere, rule of thirds, (high quality:1.2), detailed, 4k
  
  Negative prompt: low quality, blurry, deformed, extra fingers, bad anatomy, disfigured, 
  poorly drawn face, mutation, mutated, ugly, watermark, text, modern clothing, cars, 
  phones, realistic photo
  ```
- **权重规则**：
  - 风格前缀：`(style:1.3)` — 确保风格主导
  - 角色关键特征（发色、服装）：`(feature:1.2)` — 强化一致性
  - 次要特征（肤色、姿态）：`(feature:1.1)` — 轻微强化
  - 场景元素：默认权重 1.0

## 7. 角色参考图 Prompt（Step 3b）

在角色设计阶段，为用户生成可直接在 Gemini 等平台使用的角色卡 Prompt。

### best.png Prompt 模板

```
{style_prefix} portrait, {FULL_appearance_description_without_TOK}, clean white background, 
high quality, high resolution, character reference sheet, full body visible
```

示例：
```
manga style, cel shading, portrait, a woman with long blonde hair in a braid wearing a 
sparkling blue dress ice blue eyes fair skin elegant posture, clean white background, 
high quality, high resolution, character reference sheet, full body visible
```

### 多角度 photo_N.png Prompt 模板

为每个角色生成 3-5 张不同角度的参考图，供角色一致性参考：

| 编号 | 角度 | Prompt 模板 |
|------|------|------------|
| photo_1 | 正面 | `{style_prefix} front view, {appearance}, neutral expression, clean background, high quality` |
| photo_2 | 3/4 侧 | `{style_prefix} 3/4 view, {appearance}, slight smile, clean background, high quality` |
| photo_3 | 侧面 | `{style_prefix} side profile, {appearance}, looking ahead, clean background, high quality` |
| photo_4 | 面部特写 | `{style_prefix} close-up face, {appearance}, showing emotion, clean background, high quality` |
| photo_5 | 全身 | `{style_prefix} full body, {appearance}, action pose, clean background, high quality` |

### 角色卡 Negative Prompt

```
multiple characters, crowded background, text, watermark, low quality, blurry, deformed, 
extra fingers, bad anatomy, inconsistent clothing, different hair color
```

## 8. 关键帧 Prompt（Step 4c）

在镜头创建阶段，为每个 Shot 生成 `image_prompt` 字段，写入 `script_breakdown.json`。

### 生成流程

1. 读取 Shot 的 `Involving Characters`，获取角色列表
2. 对每个角色，从 `characters.json` / `character_list/{Name}/best.txt` 提取 `<TOK>` 描述
3. 去掉 `<TOK>` 前缀，保留完整外观描述
4. 按构造公式组装 image_prompt
5. 附加 negative prompt

### 输入数据映射

| 公式字段 | 数据来源 |
|---------|---------|
| `style_prefix` | 项目初始化时确定，全局一致 |
| `shot_type` | Shot 的 `Shot Type` 字段 |
| `scene_description` | Scene Annotation 中的场景描述 |
| `FULL_character_appearance` | `character_list/{Name}/best.txt` 去掉 `<TOK>` |
| `lighting` | 从 Scene Annotation 推断（时间、地点、天气） |
| `mood` | 从 Shot 的 `Plot/Visual Description` 推断 |
| `composition_rule` | 根据 Shot Type + 叙事需要选择（见第 4 节） |
| `quality_tags` | `high quality, detailed` (默认) |

### 无角色镜头

空镜 / 场景建立镜头无需角色外观描述：

```
{style_prefix}, {shot_type}, {scene_description}, {lighting}, {mood}, {composition_rule}, {quality_tags}
```

示例：
```
anime style, vibrant colors, wide shot, vast frozen landscape with northern lights dancing 
across the sky, a distant ice palace glowing blue on the horizon, twilight, majestic and 
serene atmosphere, rule of thirds, high quality, detailed
```

## 9. 多角色 image_prompt 详细规范

### 双角色场景

```
{style_prefix}, {shot_type}, {char_A_FULL_appearance} on the left, {char_B_FULL_appearance} 
on the right, {scene_description}, {lighting}, {mood}, {composition_rule}
```

### 三角色场景

```
{style_prefix}, {shot_type}, {char_A_FULL_appearance} on the left, {char_B_FULL_appearance} 
in the center, {char_C_FULL_appearance} on the right, {scene_description}, {lighting}, 
{mood}, {composition_rule}
```

### 位置与边界框对应规则

| 边界框位置 | 文本位置描述 |
|-----------|------------|
| x1 < 0.33 | `on the left` |
| 0.33 ≤ x1 < 0.66 | `in the center` |
| x1 ≥ 0.66 | `on the right` |
| 前景（框大） | `in the foreground` |
| 背景（框小） | `in the background` |

### 多角色注意事项

- 每个角色的外观描述**必须完整**，不可因多角色而省略
- 角色间用位置词分隔，避免描述混淆
- 确保位置描述与 `Involving Characters` 中的边界框坐标一致
- 画面中角色过多（>3）时，建议拆分镜头

## 10. Team 执行流程

### review 模式工作流

```
art-director                          consistency-checker
    │                                        │
    ├── 读取 Shot 数据 + 角色资产              │
    ├── 按公式生成所有 image_prompt            │
    ├── 发送给 consistency-checker ──────────→ │
    │                                        ├── 逐字比对角色描述一致性
    │                                        ├── 检查无角色名
    │                                        ├── 检查风格前缀一致
    │                                        ├── 检查构图多样性
    │                                        ├── 检查 negative prompt
    │                                        ├── 返回审核结果 ──────→ │
    ├── 收到审核结果                            │
    ├── 如有问题：修复并重新提交 ──────────────→ │
    ├── 如无问题：确认最终版本                    │
    └── 输出 image_prompt 列表                  │
```

### art-director 职责

1. 确定项目风格前缀（整个项目一致）
2. 为每个 Shot 按公式生成 image_prompt
3. 确保构图规则多样化（不连续重复）
4. 为 Step 3b 角色卡生成参考图 Prompt
5. 接收 consistency-checker 反馈并修正

### consistency-checker 审核清单

1. **角色外观一致性**：同一角色在所有 Shot 中的外观描述是否逐字相同
2. **角色名检查**：image_prompt 中是否出现任何角色名（如 "Elsa"、"Anna"）
3. **风格前缀一致性**：所有 image_prompt 是否使用同一风格前缀
4. **构图合理性**：构图规则是否适配镜头类型（见第 4 节映射表）
5. **Negative prompt 检查**：是否包含 negative prompt，是否匹配项目题材
6. **格式完整性**：公式各字段是否齐全

审核结果格式：
```
PASS: 所有 image_prompt 通过审核
---
FAIL: 以下问题需修复：
- Shot S1_Sc1_Shot2: 角色外观描述缺少 "ice blue eyes"（与 Shot S1_Sc1_Shot1 不一致）
- Shot S1_Sc2_Shot1: 出现角色名 "Elsa"，应替换为外观描述
- Shot S1_Sc2_Shot3: 连续第三次使用 rule of thirds，建议更换构图
```

## 11. 质量检查清单

### image_prompt 格式检查

- [ ] 使用英文
- [ ] 包含风格前缀（与项目一致）
- [ ] 包含镜头类型
- [ ] 包含场景环境描述
- [ ] 有角色时包含完整外观描述
- [ ] 包含光影描述
- [ ] 包含氛围/情绪
- [ ] 包含构图规则
- [ ] 附带 negative prompt

### 角色一致性检查

- [ ] 外观描述来自 `<TOK>` 描述去掉前缀
- [ ] 外观描述**完整复制**，未缩写或改写
- [ ] 同一角色在所有 Shot 中描述**逐字相同**
- [ ] image_prompt 中**无角色名**出现
- [ ] 多角色画面中每个角色都有完整描述

### 构图与风格检查

- [ ] 风格前缀在整个项目中一致
- [ ] 连续镜头构图有变化
- [ ] 每 Scene 至少 2 种构图
- [ ] 构图规则适配镜头类型
- [ ] negative prompt 匹配项目题材

### 平台兼容性检查

- [ ] Gemini 版本使用自然语言描述
- [ ] DALL-E 3 版本包含丰富细节
- [ ] Stable Diffusion 版本使用标签式 + 权重语法
- [ ] 各平台 prompt 的角色外观描述完全一致
