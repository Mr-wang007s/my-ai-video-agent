---
name: script-breakdown
description: MovieAgent 式分层 CoT 剧本拆解指南。当需要将完整剧本/小说进行三层分层拆解（Sub-Scripts → Scenes → Shots）时，应使用此 Skill。封装了 screenwriterCoT、ScenePlanningCoT、ShotPlotCreateCoT 三组完整 Prompt 模板。
---

# 分层 CoT 剧本拆解

基于 MovieAgent 论文的核心方法论，提供将故事文本通过三层独立 CoT 推理逐步拆解为可执行镜头的完整 Prompt 模板和工作流。

## 核心原则

1. **分层独立**：每层由独立的 Agent 执行，不共享上下文（`use_history=False`）
2. **CoT 强制推理**：每层必须先输出 `Internal Chain-of-Thought`，再输出结构化结果
3. **逐步嵌套**：输出为三层嵌套 JSON（Sub-Script → Scene Annotation → Shot Annotation）
4. **保留原文**：分层过程不修改原始剧本文本，仅做结构化拆解

## 三层拆解流水线

```
Step 4a: Screenwriter Agent  → 剧本 → Sub-Scripts (≤20个章节/幕)
Step 4b: Scene Planner Agent → 逐个 Sub-Script → Scenes
Step 4c: Shot Creator Agent  → 逐个 Scene → Shots (含边界框/双版本描述)
```

---

## Layer 1: screenwriterCoT（编剧拆解）

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
```

### User Prompt 模板

```
Script Synopsis: {movie_script}
Character: {character_list}
```

### 输出写入

写入 `script_breakdown.json` 的根层级（`Relationships`、`Internal Chain-of-Thought`、`Sub-Script`）。

---

## Layer 2: ScenePlanningCoT（场景规划）

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
```

### User Prompt 模板

```
Given the following inputs:
- Script Synopsis: "{sub_script_plot}"
- Character Relationships: {character_relationships}
```

### 执行方式

**逐个 Sub-Script 循环调用**：

```
for each sub_script in script_breakdown["Sub-Script"]:
    result = scene_planner_agent(sub_script["Plot"], relationships)
    sub_script["Scene Annotation"] = result
```

### 输出写入

嵌套写入每个 Sub-Script 的 `Scene Annotation` 字段。

---

## Layer 3: ShotPlotCreateCoT（镜头创建）

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
      "Involving Characters": {
        "Character A": [x1, y1, x2, y2],
        "Character B": [x1, y1, x2, y2]
      },
      "Plot/Visual Description": "Detailed visual description (≥30 words) with character names, actions, environment details",
      "Coarse Plot": "Brief description without character names (≤20 words) for image generation",
      "image_prompt": "English prompt for DALL-E 3, no character names, pure scene/visual description",
      "video_prompt": "Seedance 2.0 prompt with @Image references for character consistency",
      "audio_prompt": "Chinese audio prompt: sound effects + dialogue with emotion + BGM",
      "Emotional Enhancement": "How this shot enhances the emotional arc",
      "Shot Type": "Wide shot | Medium shot | Close-up | Extreme close-up | Over-shoulder shot | POV shot | Bird-eye view | Low-angle shot | Dutch angle",
      "Camera Movement": "Static | Pan left | Pan right | Tilt up | Tilt down | Zoom in | Zoom out | Slow dolly-in | Tracking shot",
      "Duration": 5,
      "Subtitles": {
        "Character A": "Dialogue text in original language"
      },
      "seedance_mode": "i2v | multimodal",
      "ratio": "16:9"
    }
  }
}

## CONSTRAINTS

### Character Positioning (Bounding Boxes)
- Coordinates are normalized [0, 1] for [x1, y1, x2, y2]
- Maximum 3 characters per shot (ideally 1-2)
- Horizontal spacing between characters: gap ≤ 0.5 of frame width
- Bounding boxes MUST NOT overlap
- Single character: centered, box width ~0.3-0.5
- Two characters: left (0.05-0.45) and right (0.55-0.95)

### Visual Descriptions
- Plot/Visual Description: ≥30 words, include character names + specific actions + environment
- Coarse Plot: ≤20 words, NO character names, describe the visual scene only
- image_prompt: English, professional photography/art direction terms, NO character names
- video_prompt: Include @Image references for character appearance consistency
- audio_prompt: Chinese, describe ambient sounds + dialogue with emotion + BGM

### Shot Design
- Duration must be one of: 4, 5, 10, 15 (seconds, matching Seedance 2.0)
- Vary shot types within a scene for visual rhythm
- seedance_mode: use "multimodal" when character reference images are available, "i2v" for scene-only shots
- Every dialogue line must be captured in the appropriate shot's Subtitles

### image_prompt Construction
Format: "{style}, {shot_type}, {scene_description}, {character_action_without_names}, {lighting}, {mood}, {composition}"
Example: "manga style, medium shot, dimly lit office interior, a young man with glasses rubbing his eyes tiredly at a desk, warm lamp light, melancholy atmosphere, rule of thirds composition"

### video_prompt Construction
Format: "@Image1 作为{角色名}外观参考。@Image2 作为首帧，{dynamic_action}, {camera_movement}, {lighting_changes}"
- @Image references map to character best.png in order
- Last @Image is the keyframe (generated from image_prompt)

### audio_prompt Construction
Format: "{ambient_sounds}, {action_sounds}, {character_dialogue_with_emotion}, {bgm_description}"
Dialogue format: "{gender/age}{emotion}说：'{text}'"
Example: "空旷的城堡大厅，冰晶凝结声，年轻女性惊异地说：'那个声音……我又听到了'，空灵的钢琴BGM"
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
- Character B: character_list/CharB/best.png (has assets: yes/no)
```

### 执行方式

**双层循环**：逐个 Sub-Script → 逐个 Scene 调用：

```
for each sub_script in script_breakdown["Sub-Script"]:
    for each scene in sub_script["Scene Annotation"]["Scene"]:
        result = shot_creator_agent(scene, character_assets)
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
  - character_list/ (已设计角色的资产目录)

Layer 1 (Screenwriter):
  Input:  MovieScript + Character list
  Output: Relationships + CoT + Sub-Scripts
  写入:   script_breakdown.json (根层级)

Layer 2 (Scene Planner):
  Input:  每个 Sub-Script 的 Plot + Relationships
  Output: CoT + Scenes (per Sub-Script)
  写入:   script_breakdown.json → Sub-Script.Scene Annotation

Layer 3 (Shot Creator):
  Input:  每个 Scene 的详情 + 角色资产状态
  Output: CoT + Shots (per Scene, 含边界框/三版本Prompt)
  写入:   script_breakdown.json → Sub-Script.Scene Annotation.Scene.Shot Annotation

最终输出：
  script_breakdown.json — 完整三层嵌套 JSON
```

## 质量检查清单

- [ ] 每个 Sub-Script 的 Plot ≥ 50 词
- [ ] 每个 Shot 的 Plot/Visual Description ≥ 30 词
- [ ] 每个 Shot 的 Coarse Plot ≤ 20 词且不含角色名
- [ ] 边界框坐标在 [0,1] 范围内，不重叠
- [ ] 每个镜头最多 3 个角色
- [ ] Duration 为 4/5/10/15 之一
- [ ] 所有对白都分配到了对应 Shot 的 Subtitles
- [ ] image_prompt 为英文，不含角色名
- [ ] video_prompt 含正确的 @Image 引用
- [ ] audio_prompt 为中文，包含环境音+对白+BGM
- [ ] CoT 推理过程完整，各步骤都有实质内容
- [ ] Timeline 按时间顺序排列
- [ ] 所有角色至少在一个 Sub-Script 中出现

## Schema 参考

输出严格遵循 `schemas/script_breakdown.schema.json` 定义。
