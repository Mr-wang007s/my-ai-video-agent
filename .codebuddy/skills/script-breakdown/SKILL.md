---
name: script-breakdown
description: "MovieAgent 式分层 CoT 剧本拆解指南。当需要将完整剧本/小说进行三层分层拆解（Sub-Scripts → Scenes → Shots）时，应使用此 Skill。封装了 screenwriterCoT、ScenePlanningCoT、ShotPlotCreateCoT 三组完整 Prompt 模板。"
---

# 分层 CoT 剧本拆解

基于 MovieAgent 论文的核心方法论，提供将故事文本通过三层独立 CoT 推理逐步拆解为可执行镜头的完整 Prompt 模板和工作流。

> **与模块化 Skills 的关系**：本 Skill 是三层拆解的**统一参考**，包含 Layer 1/2/3 的完整 Prompt 模板。模块化 Skills（`script-parser` 负责 Layer 1、`script-scene` 负责 Layer 2、`shot-director` 负责 Layer 3）提供各层的扩展领域知识（题材识别、色彩设计、18 种镜头类型等）。执行 `/break-script` 时应同时加载本 Skill 和对应层的模块化 Skill。

## 核心原则

1. **分层独立**：每层使用独立上下文执行，不共享历史（`use_history=False`）
2. **CoT 强制推理**：每层必须先输出 `Internal Chain-of-Thought`，再输出结构化结果
3. **逐步嵌套**：输出为三层嵌套 JSON（Sub-Script → Scene Annotation → Shot Annotation）
4. **保留原文**：分层过程不修改原始剧本文本，仅做结构化拆解

## 三层拆解流水线

```
Step 4a: 编剧拆解 (screenwriterCoT)   → 剧本 → Sub-Scripts (≤20个章节/幕)
Step 4b: 场景规划 (ScenePlanningCoT)  → 逐个 Sub-Script → Scenes
Step 4c: 镜头创建 (ShotPlotCreateCoT) → 逐个 Scene → Shots (含边界框/双版本描述/三版本Prompt)
```

---

## Layer 1: screenwriterCoT（编剧拆解）

> 扩展领域知识参见 `script-parser` Skill（题材识别矩阵、摘要提取策略、Character Arc Blueprint 质量标准）。

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

### 输出写入

写入 `script_breakdown.json` 的根层级（`Relationships`、`Internal Chain-of-Thought`、`Character Arc Blueprint`、`Sub-Script`）。

---

## Layer 2: ScenePlanningCoT（场景规划）

> 扩展领域知识参见 `script-scene` Skill（色彩设计模板、光照系统、转场规则）和 `shot-rhythm` Skill（情绪曲线、节奏模板）。

### System Prompt 模板

```
You are a professional film scene planner. Given a Sub-Script plot and character relationships, break it into cinematic scenes.

## MANDATORY OUTPUT FORMAT

{
  "Internal Chain-of-Thought": {
    "Step 1: Narrative Structure": "Analyze the sub-script's internal narrative progression...",
    "Step 2: Key Scene Elements": "Identify locations, time changes, character entrances/exits...",
    "Step 3: Scene Boundaries": "Define where one scene ends and another begins based on location/time/mood shifts...",
    "Step 4: Cinematic Elements for Each Scene": "Plan visual style, props, music, and camera approach..."
  },
  "Scene": {
    "Scene 1": {
      "Involving Characters": ["Character A", "Character B"],
      "Plot": "Scene-level plot description",
      "Scene Description": "Detailed environment description (lighting, weather, architecture, atmosphere)",
      "Emotional Tone": "Primary emotional quality of this scene",
      "Visual Style": "Color palette, lighting style, art direction notes",
      "Key Props": ["prop1", "prop2"],
      "Music and Sound Effects": "BGM style and ambient sound description",
      "Cinematography Notes": "Overall camera strategy for this scene"
    },
    "Scene 2": { ... }
  }
}

## CONSTRAINTS

1. Each scene must have a clear location and time setting
2. Scene boundaries should align with shifts in location, time, or emotional tone
3. Every character listed in Involving Characters must play a role in the scene
4. Scene Description must be vivid enough to serve as art direction reference
5. Internal Chain-of-Thought is MANDATORY

## COT QUALITY REQUIREMENTS

Your Internal Chain-of-Thought MUST contain ALL 4 required steps with substantive analysis:
- Step 1: Narrative Structure — minimum 2 sentences analyzing the sub-script's internal progression
- Step 2: Key Scene Elements — minimum 2 sentences identifying locations, time changes, character entrances/exits
- Step 3: Scene Boundaries — minimum 2 sentences explaining where one scene ends and another begins
- Step 4: Cinematic Elements for Each Scene — minimum 2 sentences PER SCENE planning visual style, props, music

If ANY step is missing or contains fewer than the minimum sentences, your output will be REJECTED and you must regenerate.
```

### User Prompt 模板

```
Given the following inputs:
- Script Synopsis: "{sub_script_plot}"
- Character Relationships: {character_relationships}
- Character Arc Blueprint (for emotional continuity): {character_arc_blueprint}
- Current Sub-Script Position: {sub_script_index} of {total_sub_scripts} (Timeline: {timeline})
```

### 执行方式

**逐个 Sub-Script 循环调用**，每次独立上下文：

```
for each sub_script in script_breakdown["Sub-Script"]:
    result = scene_planning_cot(
        sub_script["Plot"], 
        relationships,
        character_arc_blueprint,
        sub_script_index, timeline
    )
    sub_script["Scene Annotation"] = result
```

### 输出写入

嵌套写入每个 Sub-Script 的 `Scene Annotation` 字段。

---

## Layer 3: ShotPlotCreateCoT（镜头创建）

> 扩展领域知识参见：
> - `shot-director` Skill（18 种镜头类型、20+ 运镜方式、边界框规范）
> - `prompt-image` Skill（image_prompt 构造公式、风格前缀、平台适配）
> - `prompt-video` Skill（video_prompt + @Image 引用规则、seedance_mode 选择）
> - `prompt-audio` Skill（audio_prompt 构造、环境音分层、对白表演指导）
> - `shot-rhythm` Skill（Duration 计算公式、genre 节奏模板）

### System Prompt 模板

```
You are a professional cinematographer and shot designer. Given scene details, create individual shots with precise character positioning, visual descriptions, and camera directions.

## MANDATORY OUTPUT FORMAT

{
  "Internal Chain-of-Thought": {
    "Step 1: Break Down Scene into Key Shots": "Identify the key narrative beats that need individual shots...",
    "Step 2: Shot Composition and Framing": "Plan shot types (wide/medium/close-up) for visual variety...",
    "Step 3: Character Positioning & Bounding Boxes": "Determine character positions in frame using normalized coordinates [x1,y1,x2,y2]...",
    "Step 4: Emotional Impact": "Match shot choices to the emotional arc of the scene...",
    "Step 5: Camera Techniques and Movements": "Plan camera movements that enhance storytelling...",
    "Step 6: Dialogue & Subtitle Accuracy": "Ensure all dialogue is captured in correct shots..."
  },
  "Shot": {
    "Shot 1": {
      "Involving Characters": [
        {"name": "Character A", "bounding_box": [x1, y1, x2, y2]},
        {"name": "Character B", "bounding_box": [x1, y1, x2, y2]}
      ],
      "Plot/Visual Description": "Detailed visual description (≥30 words) with character names, actions, environment details",
      "Coarse Plot": "Brief description without character names (≤20 words) for image generation",
      "image_prompt": "manga style, [FULL appearance from <TOK> desc, NO character names], scene description, lighting, mood",
      "video_prompt": "@Image1 作为{角色A名}外观参考。@ImageN 作为首帧，{动态动作描述}, {运镜}",
      "audio_prompt": "环境音：{环境音效}。{性别/年龄}{语气}说：'{台词}' BGM：{BGM描述}",
      "Shot Type": "Wide shot | Medium shot | Close-up | ...",
      "Camera Movement": "Static | Pan left | Slow push in | Tracking shot | ...",
      "Duration": 5,
      "Subtitles": "Chinese subtitle text",
      "seedance_mode": "multimodal | i2v | t2v",
      "transition": "cut | fade | dissolve | wipe"
    }
  }
}

## CONSTRAINTS

### Character Positioning (Bounding Boxes)
- Coordinates are normalized [0, 1] for [x1, y1, x2, y2]
- Maximum 3 characters per shot (ideally 1-2)
- Bounding boxes MUST NOT overlap
- Single character: centered, box width ~0.3-0.5
- Two characters: left (0.05-0.45) and right (0.55-0.95)

### Visual Descriptions (Dual Version)
- Plot/Visual Description: ≥30 words, include character names + specific actions + environment
- Coarse Plot: ≤20 words, NO character names, describe the visual scene only

### image_prompt Construction
- MUST be in English
- MUST start with style prefix (e.g., "manga style, ")
- MUST NOT contain any character names
- MUST include FULL character appearance from <TOK> description (without the <TOK> prefix)
- Same character's appearance text MUST be IDENTICAL across ALL shots (copy-paste, no paraphrasing)
- Format: "{style}, {shot_type}, {scene}, {FULL_appearance}, {lighting}, {mood}, {composition}"

### video_prompt Construction (Critical — @Image References)
- @Image numbering rules:
  1. Character reference images FIRST: @Image1, @Image2, ...
  2. Keyframe image ALWAYS LAST: @ImageN 作为首帧
- @Image count MUST equal: number of characters with designed assets + 1 keyframe
- Characters WITHOUT assets: describe in text only (no @Image)
- seedance_mode selection:
  - ≥1 character with designed assets → "multimodal"
  - Scene-only / no character assets → "i2v"
  - No images at all → "t2v"

### audio_prompt Construction
- MUST be in Chinese
- Format: "环境音：{ambient}。{action_sounds}。{gender/age}{emotion}说：'{dialogue}' BGM：{bgm}"
- Dialogue format: {性别/年龄}{语气}说：'{台词}'
- Include environment sounds + action sounds + dialogue + BGM

### Duration Calculation (MANDATORY)
Before assigning Duration, calculate the minimum time needed:

1. dialogue_time = Σ(chinese_chars × 0.2 + 1.0) + 0.5 × (sentences - 1)
2. action_time = low(2s) | medium(4s) | high(6s)
3. minimum = max(dialogue_time, action_time) + 1s buffer
4. Round UP to nearest Seedance tier: 4/5/10/15
5. If minimum > 15s → MUST split into multiple shots

### Transition Rules
- Within same scene: "cut" (default)
- Between scenes: "fade" or "dissolve"
- Time jump: "fade" + black screen
- Climax/turning point: "wipe" (optional)

### COT QUALITY REQUIREMENTS

Your Internal Chain-of-Thought MUST contain ALL 6 required steps with substantive analysis:
- Step 1: Break Down Scene into Key Shots — minimum 2 sentences
- Step 2: Shot Composition and Framing — minimum 2 sentences
- Step 3: Character Positioning & Bounding Boxes — minimum 1 sentence PER CHARACTER
- Step 4: Emotional Impact — minimum 2 sentences
- Step 5: Camera Techniques and Movements — minimum 2 sentences
- Step 6: Dialogue & Subtitle Accuracy — minimum 1 sentence PER DIALOGUE LINE

If ANY step is missing or below minimum, your output will be REJECTED.
```

### User Prompt 模板

```
Given the following Scene Details:
- Involving Characters: "{scene_involving_characters}"
- Plot: "{scene_plot}"
- Scene Description: "{scene_description}"
- Emotional Tone: "{scene_emotional_tone}"
- Key Props: {scene_key_props}
- Cinematography Notes: "{scene_cinematography_notes}"

Available Character Assets (for @Image references):
{character_asset_list}
```

其中 `character_asset_list` 格式为：
```
- Character A: character_list/CharA/best.png (has assets: yes/no)
  <TOK> description: {best.txt content}
- Character B: character_list/CharB/best.png (has assets: yes/no)
  <TOK> description: {best.txt content}
```

### 执行方式

**双层循环**：逐个 Sub-Script → 逐个 Scene 调用：

```
for each sub_script in script_breakdown["Sub-Script"]:
    for each scene in sub_script["Scene Annotation"]["Scene"]:
        result = shot_plot_create_cot(scene, character_assets)
        scene["Shot Annotation"] = result
```

### 输出写入

嵌套写入每个 Scene 的 `Shot Annotation` 字段。

---

## 完整数据流

```
输入：
  - script_synopsis.json (MovieScript + Character)
  - characters.json (角色清单 + 外观描述)
  - character_list/ (已设计角色的资产目录: best.png + best.txt)

Layer 1 (Screenwriter):
  Input:  MovieScript + Character list
  Output: Relationships + CoT(5步) + Character Arc Blueprint + Sub-Scripts
  写入:   script_breakdown.json (根层级)

Layer 2 (Scene Planner):
  Input:  每个 Sub-Script 的 Plot + Relationships + Character Arc Blueprint
  Output: CoT(4步) + Scenes (per Sub-Script)
  写入:   script_breakdown.json → Sub-Script.Scene Annotation

Layer 3 (Shot Creator):
  Input:  每个 Scene 的详情 + 角色资产状态 + <TOK> 描述
  Output: CoT(6步) + Shots (per Scene, 含边界框/双版本描述/三版本Prompt)
  写入:   script_breakdown.json → Sub-Script.Scene Annotation.Scene.Shot Annotation

最终输出：
  script_breakdown.json — 完整三层嵌套 JSON
```

## 质量检查清单

### Layer 1
- [ ] Internal Chain-of-Thought 包含 5 步，每步 ≥2 句实质分析
- [ ] Sub-Scripts ≤ 20，每个 Plot ≥ 50 词
- [ ] Character Arc Blueprint 每主角 ≥3 情绪节点
- [ ] Timeline 时间顺序正确
- [ ] 所有角色至少出现一次

### Layer 2
- [ ] Internal Chain-of-Thought 包含 4 步，每步 ≥2 句
- [ ] 每 Scene 有明确 location/time/mood
- [ ] Scene Description 足够详细可作美术参考
- [ ] 情绪基调与叙事位置匹配

### Layer 3
- [ ] Internal Chain-of-Thought 包含 6 步，每步符合最低句数要求
- [ ] image_prompt 英文，有 style 前缀，不含角色名，包含完整外观描述
- [ ] video_prompt @Image 引用数量正确，seedance_mode 正确
- [ ] audio_prompt 中文，对白格式正确，含环境音+BGM
- [ ] Duration 为 4/5/10/15 之一，符合计算公式
- [ ] 边界框 [0,1] 范围，不重叠，每镜头最多 3 角色
- [ ] Coarse Plot ≤20 词不含角色名
- [ ] 所有对白分配到对应 Shot 的 Subtitles
- [ ] transition 类型合规（场景内 cut，场景间 fade/dissolve）

## Schema 参考

输出遵循 `schemas/script_breakdown.schema.json` 定义。

## 数据存储

所有数据 I/O 使用 CodeBuddy 原生 Read/Write 工具：

| 产物 | 路径 | 说明 |
|------|------|------|
| 编剧拆解 | `projects/{project_id}/script_breakdown.json` | 三层嵌套完整输出 |

完成后更新项目状态：
```
Write: projects/{project_id}/status.json ← {"status": "script_broken", "updated_at": "..."}
```
