# 质量标准

> 综合三层 CoT 推理、Prompt 规范、角色一致性、叙事节奏的完整质量检查清单。所有检查项适用于 `/break-script` 和 `/export-guide` 阶段。

## 一、CoT 推理质量（核心）

### 三层嵌套 JSON 结构校验
- [ ] `script_breakdown.json` 包含 `Relationships` + `Internal Chain-of-Thought` + `Character Arc Blueprint` + `Sub-Script` 四个顶层键
- [ ] 每个 Sub-Script 包含 `Scene Annotation`（含 CoT + Scene 列表）
- [ ] 每个 Scene 包含 `Shot Annotation`（含 CoT + Shot 列表）
- [ ] 三层嵌套的层级关系正确（Sub-Script → Scene → Shot）
- [ ] 每个 Shot 包含全部必填字段：`Shot Type`、`Camera Movement`、`Duration`、`image_prompt`、`video_prompt`、`audio_prompt`、`Involving Characters`、`Plot/Visual Description`、`Coarse Plot`、`Subtitles`

### CoT 推理完整性
- [ ] Layer 1 CoT 包含 5 个必填步骤，每步 ≥ 2 句实质性分析
  - Step 1: Core Narrative Structure
  - Step 2: Key Character Information
  - Step 3: Temporal Segmentation
  - Step 4: Sub-Script Breakdown Criteria
  - Step 5: Division Rationale
- [ ] Layer 2 CoT 包含 4 个必填步骤，每步 ≥ 2 句（Step 4 ≥ 2 句/场景）
  - Step 1: Narrative Structure
  - Step 2: Key Scene Elements
  - Step 3: Scene Boundaries
  - Step 4: Cinematic Elements for Each Scene
- [ ] Layer 3 CoT 包含 6 个必填步骤
  - Step 1: Break Down Scene into Key Shots（≥ 2 句）
  - Step 2: Shot Composition and Framing（≥ 2 句）
  - Step 3: Character Positioning & Bounding Boxes（≥ 1 句/角色）
  - Step 4: Emotional Impact（≥ 2 句）
  - Step 5: Camera Techniques and Movements（≥ 2 句）
  - Step 6: Dialogue & Subtitle Accuracy（≥ 1 句/对白行）
- [ ] 每个 CoT 步骤有实质性分析内容（非空字符串、非 `{}`、非占位符）
- 遵循 `.codebuddy/rules/cot-reasoning.md` 的完整规则

### Character Arc Blueprint 质量
- [ ] 覆盖所有主要角色
- [ ] 每个主角 ≥ 3 个情绪状态节点（跨不同 Sub-Script）
- [ ] 相邻情绪节点有实质性变化（角色需发展）
- [ ] 每个节点同时描述情绪状态和叙事功能
- [ ] 至少覆盖 Beginning 和 End 阶段的 Sub-Script

## 二、Prompt 规范

### image_prompt（英文，用于 Gemini / DALL-E / SD 文生图）
- [ ] 必须使用英文
- [ ] 必须包含风格前缀（如 `manga style,` `anime style,`），整个项目内一致
- [ ] **禁止**包含角色名（使用外观描述替代，对应 Coarse Plot 思路）
- [ ] 必须包含角色完整外观描述（来自 `<TOK>` 描述去掉 `<TOK>` 前缀，**完整复制，禁止缩写或改写**）
- [ ] 同一角色在所有 Shot 中的外观描述文本**逐字一致**（byte-level match）
- [ ] 格式遵循：`{style_prefix}, {shot_type}, {scene_description}, {FULL_character_appearance}, {lighting}, {mood}, {composition_rule}`
- [ ] 使用 negative prompt 排除常见缺陷

### video_prompt（用于可灵 / Seedance 图/文生视频）
- [ ] `@ImageN` 引用总数 **== `image_paths` 数组长度**
- [ ] 角色参考图在前，首帧图在最后
- [ ] `@Image` 编号与 `image_paths` 数组顺序完全对应
- [ ] 有已设计资产的角色**必须**有 `@Image` 引用
- [ ] 无资产角色仅用文字描述（无 `@Image` 引用）
- [ ] 最后一个 `@Image` 标注为 "作为首帧"
- [ ] 重点描述动态变化和运镜，**避免重复**图片中已有的静态信息
- [ ] 可以使用角色名

### audio_prompt（中文，配音/音效参考）
- [ ] 使用中文描述
- [ ] 四段式结构：环境音效 + 动作音效 + 对白（含性别/语气） + BGM
- [ ] 对白格式：`{性别/年龄}{详细语气}说：'{台词}'`
- [ ] 语气描述使用细腻描述而非简单标签（如"压抑着怒火说"而非"生气地说"）
- [ ] 对白情绪与角色弧线匹配
- [ ] BGM 描述与当前叙事阶段情绪匹配

### Negative Prompt 标准模板
```
low quality, blurry, deformed, extra fingers, bad anatomy, disfigured, poorly drawn face, mutation, mutated, ugly, watermark, text
```

## 三、角色一致性

### character_list/ 资产库
- [ ] 每个已设计角色有 `character_list/{CharName}/` 目录
- [ ] 目录中包含 `best.txt`（`<TOK>` 描述）
- [ ] `best.txt` 以 `<TOK>` 开头，使用英文描述，包含所有 `visual_identifiers`

### Seedance @Image 引用校验
- [ ] `seedance_mode` 正确匹配：
  - 有 ≥ 1 个已设计角色参与 → `multimodal`
  - 仅场景图/空镜 → `i2v`
  - 无任何图片 → `t2v`
- [ ] 每次 Seedance 调用的 `video_prompt` 中 @Image 引用数量 == image_paths 长度

### 边界框规范
- [ ] 坐标归一化 [0, 1]，格式 [x1, y1, x2, y2]
- [ ] 边界框不重叠
- [ ] 每镜头最多 3 个角色（推荐 1-2）

### 跨镜头一致性
- [ ] 同一角色在所有镜头中的外观描述逐字一致
- [ ] 同一场景内背景风格、光照方向、色调一致
- [ ] 连续镜头间动作衔接自然（无状态跳变）
- [ ] 不同场景间角色外观无跳变

## 四、叙事节奏

### Duration 规范
- [ ] 所有 Duration 值为 Seedance 合法档位：4、5、10 或 15
- [ ] Duration 经公式计算：
  ```
  对白时间 = Σ(中文字数 × 0.2 + 1.0) + 0.5 × (句数-1)
  动作时间 = 低(2s) | 中(4s) | 高(6s)
  最低时长 = max(对白时间, 动作时间) + 1s
  Duration = 向上对齐到 4/5/10/15
  ```
- [ ] 无计算最低时长 > 15s 但未拆分的镜头

### 镜头多样性
- [ ] 场景内镜头类型有变化，不超过 2 个连续相同类型
- [ ] Shot Type 来自 18 种扩展镜头类型表
- [ ] Camera Movement 来自 20+ 种扩展运镜词汇表

### 整体时长
- [ ] 总时长在目标范围内（短篇 60-120s，标准 120-300s）
- [ ] 镜头数在合理范围（8-60 个/话）

### 转场规则
- [ ] 同场景内：`cut`
- [ ] 场景切换：`fade` 或 `dissolve`
- [ ] 时间跳跃：`fade` + 黑屏
- [ ] 高潮/转折：`wipe`（可选）

## 五、画面一致性（用户手动生成时参考）

- [ ] 同一场景内背景风格、光照方向、色调保持一致
- [ ] 角色外观通过 `<TOK>` 描述 + `image_prompt` 中的完整外观描述保障一致性
- [ ] 同一话/集内整体画风无显著跳变
- [ ] 在 Gemini 生成时使用相同的风格前缀
- [ ] 建议同场景镜头在同一生成会话中生成，以维持背景一致性
