---
name: script-breakdown
description: MovieAgent 式分层 CoT 剧本拆解指南。当需要将完整剧本/小说进行三层分层拆解（Sub-Scripts → Scenes → Shots）时，应使用此 Skill。封装了 screenwriterCoT、ScenePlanningCoT、ShotPlotCreateCoT 三组完整 Prompt 模板。
---

# 分层 CoT 剧本拆解

基于 MovieAgent 论文的核心方法论，提供将故事文本通过三层独立 CoT 推理逐步拆解为可执行镜头的完整 Prompt 模板和工作流。

## 核心原则

1. **分层独立**：每层使用独立上下文执行，不共享历史（`use_history=False`）
2. **CoT 强制推理**：每层必须先输出 `Internal Chain-of-Thought`，再输出结构化结果
3. **逐步嵌套**：输出为三层嵌套 JSON（Sub-Script → Scene Annotation → Shot Annotation）
4. **保留原文**：分层过程不修改原始剧本文本，仅做结构化拆解

## 三层拆解流水线

```
Step 4a: 编剧拆解 (screenwriterCoT)   → 剧本 → Sub-Scripts (≤20个章节/幕)
Step 4b: 场景规划 (ScenePlanningCoT)  → 逐个 Sub-Script → Scenes
Step 4c: 镜头创建 (ShotPlotCreateCoT) → 逐个 Scene → Shots (含边界框/双版本描述)
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

**逐个 Sub-Script 循环调用**：

```
for each sub_script in script_breakdown["Sub-Script"]:
    result = scene_planning_cot(
        sub_script["Plot"], 
        relationships,
        character_arc_blueprint=script_breakdown.get("Character Arc Blueprint", {}),
        sub_script_index=index,
        timeline=sub_script["Timeline"]
    )
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

## COT QUALITY REQUIREMENTS

Your Internal Chain-of-Thought MUST contain ALL 6 required steps with substantive analysis:
- Step 1: Break Down Scene into Key Shots — minimum 2 sentences identifying key narrative beats
- Step 2: Shot Composition and Framing — minimum 2 sentences planning shot variety and composition rules
- Step 3: Character Positioning & Bounding Boxes — minimum 1 sentence PER CHARACTER describing their position rationale
- Step 4: Emotional Impact — minimum 2 sentences matching shot choices to the emotional arc
- Step 5: Camera Techniques and Movements — minimum 2 sentences explaining camera choices and their storytelling purpose
- Step 6: Dialogue & Subtitle Accuracy — minimum 1 sentence PER DIALOGUE LINE verifying placement and timing

If ANY step is missing or below minimum, your output will be REJECTED.

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
- Vary shot types within a scene for visual rhythm
- seedance_mode: use "multimodal" when character reference images are available, "i2v" for scene-only shots, "t2v" when no images at all
- Every dialogue line must be captured in the appropriate shot's Subtitles

### Duration Calculation (MANDATORY)

Before assigning Duration, you MUST calculate the minimum time needed:

1. **Dialogue time**: For each subtitle line:
   dialogue_seconds = chinese_character_count × 0.2 + 1.0 (pause)
   Total dialogue time = sum of all lines + 0.5s gaps between lines

2. **Action time**: 
   - Low complexity (static, talking): 2s
   - Medium complexity (walking, gesturing): 4s  
   - High complexity (fighting, running, magic effects): 6s

3. **Minimum duration** = max(dialogue_time, action_time) + 1s buffer

4. **Round UP** to nearest Seedance tier: 4 → 4, 5 → 5, 6-9 → 10, 10-14 → 10, 15+ → 15

5. If calculated minimum > 15s, you MUST split the shot into multiple shots

EXAMPLES:
- Shot with "姐姐，你又在这里了"(8 chars) + "你听不到吗？那个声音...它在召唤我。"(15 chars):
  Line 1: 8×0.2+1 = 2.6s, Line 2: 15×0.2+1 = 4.0s, gap: 0.5s → total 7.1s
  Action: low (2s) → min = max(7.1, 2) + 1 = 8.1s → Duration = 10

- Shot with no dialogue, magic explosion:
  Action: high (6s) → min = 6 + 1 = 7s → Duration = 10

Duration must be one of: 4, 5, 10, 15 (seconds, matching Seedance 2.0 tiers)

### image_prompt Construction (Character Appearance MANDATORY)

Format: "{style}, {shot_type}, {scene_description}, {FULL_character_appearance}, {lighting}, {mood}, {composition}"

CRITICAL RULE — Character Appearance Consistency:
For EACH character visible in the shot, you MUST include their COMPLETE appearance description 
from the character assets. Copy the FULL text — do NOT abbreviate, summarize, or paraphrase.

BAD (too vague):  "a woman in purple dress standing on a balcony"
GOOD (complete):  "manga style, medium shot, night castle balcony, a woman with long blonde hair 
  in a braid wearing a flowing purple-white gradient dress with ice crystal patterns ice blue eyes 
  fair porcelain skin elegant regal posture standing alone gazing at mountains, moonlight, 
  ethereal atmosphere, rule of thirds"

The appearance description for each character MUST be IDENTICAL in every shot across the 
entire script_breakdown.json. Any variation breaks character consistency.

Never include character NAMES in image_prompt — use only visual descriptions.

### video_prompt Construction (CRITICAL — Character Consistency)

The @Image numbering MUST follow this EXACT pattern:
1. Character reference images come FIRST, numbered sequentially: @Image1, @Image2, ...
2. The keyframe image (generated from image_prompt) is ALWAYS the LAST @Image number

Format template:
"@Image1 作为{角色A名}外观参考。@Image2 作为{角色B名}外观参考。@ImageN 作为首帧，{dynamic_action}, {camera_movement}"

Example (single character, Elsa):
  image_paths: [character_list/Elsa/best.png, images/shots/S1_Sc1_Shot1.png]
  video_prompt: "@Image1 作为Elsa外观参考。@Image2 作为首帧，角色微微抬头，冰晶从手中飘出，镜头缓慢推近"

Example (two characters, Elsa + Anna):
  image_paths: [character_list/Elsa/best.png, character_list/Anna/best.png, images/shots/S1_Sc1_Shot2.png]
  video_prompt: "@Image1 作为Elsa外观参考。@Image2 作为Anna外观参考。@Image3 作为首帧，两人面对面交谈，Elsa表情困惑"

Example (no character assets, scene-only):
  image_paths: [images/shots/S1_Sc2_Shot2.png]
  video_prompt: "@Image1 作为首帧，鸟瞰城市灯火依次熄灭，镜头缓慢上升"

VALIDATION RULES:
- Count of @ImageN references MUST equal len(image_paths)
- Characters with designed assets (has assets: yes) MUST have @Image references
- Characters WITHOUT assets should be described in text only (no @Image)
- The last @Image is ALWAYS the keyframe, described as "作为首帧"

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

## MCP Tool 调用指引

本 Skill 涉及以下 MCP tools（`manga-agent` server）：

### 状态更新
```
mcp: project_update_status(project_id="...", status="script_broken")
```

### 生成日志记录
```
mcp: generation_log(project_id="...", stage="breakdown", status="success")
```

### 完整三层拆解流程

**Layer 1（编剧拆解）**：
1. 读取 `projects/{project_id}/script_synopsis.json` 
2. 用上方 screenwriterCoT System Prompt + User Prompt 调用 LLM
3. 将输出写入 `projects/{project_id}/script_breakdown.json`（根层级）

**Layer 2（场景规划）**：
1. 读取 `script_breakdown.json`
2. 对每个 Sub-Script，用 ScenePlanningCoT System Prompt + User Prompt 调用 LLM
3. 将输出嵌套写入 `Sub-Script.Scene Annotation`

**Layer 3（镜头创建）**：
1. 读取 `script_breakdown.json` + `characters.json` + `character_list/` 目录
2. 对每个 Scene，用 ShotPlotCreateCoT System Prompt + User Prompt 调用 LLM
3. 将输出嵌套写入 `Scene.Shot Annotation`

**最终步骤**：
```
mcp: project_update_status(project_id="...", status="script_broken")
mcp: generation_log(project_id="...", stage="breakdown", status="success")
```

注意：三层拆解的 LLM 调用由主对话直接执行（CoT 推理），不需要子 Agent。每层使用独立上下文（不累积历史）。
