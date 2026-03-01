---
name: shot-director
description: "镜头导演。Layer 3 核心引擎——将场景转化为精确的可执行镜头序列。通过 ShotPlotCreateCoT 生成完整 Shot Annotation，包含双版本描述和三版本 Prompt。"
team:
  enabled: true
  pattern: multi-modal
  coordinator: shot-coordinator
  roles:
    - name: shot-coordinator
      type: coordinator
      expertise: "Shot breakdown orchestration, multi-specialist dispatch"
      system_prompt: |
        You are the shot production coordinator for Layer 3 (ShotPlotCreateCoT).
        Your workflow:
        1. Read script_breakdown.json Scene list
        2. For each Scene, create a task for shot-designer
        3. shot-designer produces shot structure (types, composition, bounding boxes,
           Plot/Visual Description, Coarse Plot, Duration)
        4. Dispatch prompt generation to 3 specialists IN PARALLEL:
           - image-prompter: generates image_prompt for all shots in scene
           - video-prompter: generates video_prompt + seedance_mode for all shots
           - audio-prompter: generates audio_prompt for all shots
        5. Merge specialist outputs into the Shot Annotation
        6. Send to shot-reviewer for quality check
        7. Write approved Shot Annotation into script_breakdown.json
      responsibilities:
        - Orchestrate the Scene -> Shot pipeline
        - Dispatch parallel prompt generation tasks
        - Merge multi-modal results
        - Track progress via TaskList
    - name: shot-designer
      type: specialist
      expertise: "ShotPlotCreateCoT core: shot decomposition, composition, bounding boxes"
      skill_ref: shot-director
      system_prompt: |
        You are a professional cinematographer. For the given Scene, execute
        ShotPlotCreateCoT to produce the shot structure.
        Output per shot: Involving Characters (with bounding boxes),
        Plot/Visual Description, Coarse Plot, Emotional Enhancement,
        Shot Type, Camera Movement, Duration, Subtitles.
        Do NOT generate image_prompt, video_prompt, or audio_prompt.
      responsibilities:
        - Execute 6-step CoT reasoning
        - Design shot sequence (types, framing, composition)
        - Calculate bounding boxes
        - Calculate Duration using the formula
        - Output shot skeleton (without prompts)
    - name: image-prompter
      type: specialist
      expertise: "image_prompt construction, character appearance embedding"
      skill_ref: prompt-image
      system_prompt: |
        You are an image prompt specialist. Generate image_prompt for each shot.
        Rules: English only, no character names, full appearance from TOK description,
        include style prefix + shot type + scene + appearance + lighting + mood + composition.
      responsibilities:
        - Generate image_prompt for each shot
        - Ensure character appearance consistency (exact text match)
        - Apply composition rules
    - name: video-prompter
      type: specialist
      expertise: "video_prompt construction, @Image references, seedance_mode"
      skill_ref: prompt-video
      system_prompt: |
        You are a video prompt specialist. Generate video_prompt and seedance_mode.
        Rules: @Image numbering (character refs first, keyframe last),
        count must equal image_paths length, focus on dynamic changes.
      responsibilities:
        - Generate video_prompt with correct @Image references
        - Determine seedance_mode (multimodal/i2v/t2v)
        - Plan image_paths array
        - Ensure action continuity between shots
    - name: audio-prompter
      type: specialist
      expertise: "audio_prompt construction, dialogue performance"
      skill_ref: prompt-audio
      system_prompt: |
        You are an audio design specialist. Generate audio_prompt for each shot.
        Format: ambient_sounds, action_sfx, dialogue_with_performance, bgm.
        Dialogue: {gender/age}{emotion}说：'{text}'
      responsibilities:
        - Generate audio_prompt for each shot
        - Match dialogue emotion to character arc
        - Design layered audio
    - name: rhythm-checker
      type: specialist
      expertise: "Duration validation, pacing analysis"
      skill_ref: shot-rhythm
      system_prompt: |
        Review shot sequence for Duration calculation correctness,
        shot type variety, pacing vs emotional curve, total scene duration.
      responsibilities:
        - Validate Duration calculations
        - Check shot type variety
        - Verify pacing against genre template
    - name: shot-reviewer
      type: reviewer
      expertise: "Shot quality, CoT completeness, prompt consistency"
      system_prompt: |
        Quality check each Shot:
        1. CoT 6 steps with substantive content
        2. Plot/Visual Description >= 30 words
        3. Coarse Plot <= 20 words, no character names
        4. image_prompt English, no names, full appearance
        5. video_prompt @Image count matches
        6. audio_prompt Chinese, ambient+dialogue+BGM
        7. Bounding boxes [0,1], no overlap, max 3 chars
        8. Duration is 4/5/10/15
      responsibilities:
        - Validate all Shot fields
        - Check cross-shot consistency
        - Approve or reject with feedback
  coordination:
    merge_strategy: coordinator-merge
    review_required: true
    max_parallel: 3
---

# 镜头导演（shot-director）

> Layer 3 的核心引擎——将场景转化为精确的可执行镜头序列。通过 ShotPlotCreateCoT 生成完整 Shot Annotation，包含双版本描述（Plot/Visual Description + Coarse Plot）和三版本 Prompt（image_prompt / video_prompt / audio_prompt）。

**适用阶段**：Step 4c（Layer 3 镜头创建）

**输入**：`script_breakdown.json`（含 Scene Annotation）+ `characters.json` + `character_list/`

**输出**：每个 Scene 的 `Shot Annotation`（嵌套写入 `script_breakdown.json`）

---

## 1. Core Principles

1. **CoT 先行**：每次 Shot 生成必须完成完整的 6 步 Internal Chain-of-Thought，任何步骤缺失或内容不足将导致输出被拒绝。
2. **双版本描述分离**：`Plot/Visual Description`（含角色名，详尽叙事）与 `Coarse Plot`（无角色名，纯视觉概括）服务不同下游——前者用于视频 prompt，后者用于图像生成。
3. **三模态并行**：image_prompt / video_prompt / audio_prompt 由三个独立专家并行生成，coordinator 负责合并。
4. **角色一致性至上**：同一角色的外观描述文本在整个 `script_breakdown.json` 中必须逐字一致，不可缩写、改写或遗漏。
5. **Duration 公式强制**：镜头时长必须通过公式计算后向上对齐到 Seedance 档位（4/5/10/15），禁止凭感觉指定。
6. **独立上下文**：每次 Layer 3 调用使用独立上下文（`use_history=False`），不累积历史消息。
7. **文件系统优先**：所有数据读写通过 CodeBuddy 原生工具（Read/Write），不依赖外部服务。

---

## 2. ShotPlotCreateCoT System Prompt 模板

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

---

## 3. User Prompt 模板

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

---

## 4. 执行方式：双层嵌套循环

**Sub-Script x Scene 双层循环**：逐个 Sub-Script → 逐个 Scene 调用 ShotPlotCreateCoT：

```
for each sub_script in script_breakdown["Sub-Script"]:
    for each scene in sub_script["Scene Annotation"]["Scene"]:
        # 1. shot-designer 生成 shot skeleton（含 CoT + 结构，无 prompt）
        shot_skeleton = shot_designer.execute(scene, character_assets)

        # 2. 三个 prompt 专家并行生成
        image_prompts  = image_prompter.generate(shot_skeleton, character_assets)   # 并行
        video_prompts  = video_prompter.generate(shot_skeleton, character_assets)   # 并行
        audio_prompts  = audio_prompter.generate(shot_skeleton, scene_emotion)      # 并行

        # 3. coordinator 合并结果
        merged_shots = coordinator.merge(shot_skeleton, image_prompts, video_prompts, audio_prompts)

        # 4. rhythm-checker 校验时长和节奏
        rhythm_report = rhythm_checker.validate(merged_shots)

        # 5. shot-reviewer 质量审查
        review_result = shot_reviewer.review(merged_shots)

        # 6. 写入 script_breakdown.json
        if review_result.approved:
            scene["Shot Annotation"] = merged_shots
```

**独立上下文原则**：每次调用使用独立上下文（`use_history=False`），不在 LLM 调用间累积历史消息。每次调用只发送 System Prompt + 当前 User Message。

---

## 5. 扩展镜头类型表（18 种）

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

### 镜头类型选择指南

- **开场**：大远景/远景 → 建立空间和氛围
- **对话**：中景/过肩/双人镜头轮换 → 保持视觉节奏
- **情感高潮**：近景/大特写 → 捕捉细微表情
- **动作场面**：中远景 + 跟拍 → 保持动态全貌
- **悬念/转折**：荷兰角/仰拍/剪影 → 制造不安感
- **过渡/喘息**：空镜/插入镜头 → 调节节奏

---

## 6. 扩展运镜词汇表（20+ 种）

| 运镜 | 英文 | 效果 | 动作词（用于 video_prompt） |
|------|------|------|---------------------------|
| 静止 | Static | 稳定 | holds still |
| 左摇 | Pan left | 扫视 | sweeps left |
| 右摇 | Pan right | 跟随 | follows right |
| 上摇 | Tilt up | 仰视 | tilts upward |
| 下摇 | Tilt down | 俯瞰 | tilts downward |
| 推镜 | Zoom in | 聚焦 | punches in |
| 拉镜 | Zoom out | 揭示 | pulls back |
| 慢推轨 | Slow dolly-in | 渐进紧张 | creeps forward |
| 快推轨 | Fast dolly-in | 冲击感 | rushes in |
| 跟拍 | Tracking | 动态跟随 | follows the action |
| 横移 | Truck/Crab | 平移揭示 | slides sideways |
| 环绕 | Orbit | 立体感 | circles around |
| 升降 | Crane/Boom | 视角变化 | rises/descends |
| 手持 | Handheld | 真实感 | shakes slightly |
| 甩镜 | Whip pan | 快速转场 | whips across |
| 360环绕 | 360 orbit | 戏剧性高潮 | spins around |
| 推拉结合 | Dolly zoom | 眩晕/震惊 | stretches perspective |
| 斜角移动 | Diagonal track | 不安定感 | moves diagonally |
| 弧形跟拍 | Arc tracking | 优雅揭示 | arcs around subject |
| 垂直升降 | Vertical crane | 宏大/渺小 | lifts vertically |

### 运镜选择指南

- **静态对话**：Static 或 Slow dolly-in → 保持观众注意力
- **追逐/动作**：Tracking 或 Handheld → 增强动感和紧迫感
- **揭示场景**：Pan / Tilt / Crane → 引导观众视线
- **情感高潮**：Dolly zoom / Slow dolly-in → 制造心理冲击
- **转场**：Whip pan / 360 orbit → 快速衔接不同空间
- **角色介绍**：Orbit / Arc tracking → 立体展示角色

---

## 7. 镜头组合模式（Shot Combination Patterns）

### 7.1 正反打（Shot/Reverse Shot）

用于**对话场景**，在两个角色间切换视角：

```
Shot A (角色1 说话，过肩/中景) → Shot B (角色2 回应，过肩/中景) → Shot A → Shot B → ...
```

**规则**：
- 遵循 180 度规则（摄影机始终在两人连线的同一侧）
- Shot A 和 Shot B 的构图左右镜像
- 每组正反打 2-4 个来回，避免过于机械
- 可穿插双人镜头（Two-shot）打破单调
- 情绪升级时：中景 → 近景 → 大特写递进

**Duration 建议**：每个 Shot 4-5s，对话密集时可用 10s

### 7.2 建立-推进（Establishing → Medium → Close → ECU）

用于**场景开场或情感递进**，从远到近逐步聚焦：

```
远景(建立空间) → 中景(引入人物) → 近景(捕捉情感) → 大特写(情感高潮)
```

**规则**：
- 第一个镜头必须是远景/大远景，建立空间关系
- 每次切换缩短景别一级，不可跳级（远景不可直接切大特写）
- 推进速度匹配情绪节奏：铺垫慢推，高潮快推
- 可在任意位置终止推进（不必到达大特写）

**Duration 建议**：远景 5-10s → 中景 5s → 近景 4-5s → 大特写 4s

### 7.3 反应链（Action → Reaction → Reaction）

用于**关键事件发生后展示多角色反应**：

```
动作镜头(事件发生) → 反应镜头(角色A) → 反应镜头(角色B) → [反应镜头(角色C)]
```

**规则**：
- 动作镜头通常是中景/远景，展示事件全貌
- 反应镜头通常是近景/大特写，聚焦表情
- 反应顺序按重要性排列（最重要的角色最先/最后）
- 反应镜头 Duration 较短（4-5s），制造快速剪辑节奏
- 最后一个反应镜头可延长（情感落点）

**Duration 建议**：动作 5-10s → 反应 4s × N

### 7.4 蒙太奇（Montage: Short1 → Short2 → ... → ShortN）

用于**时间压缩或平行叙事**：

```
短镜头1(4s) → 短镜头2(4s) → 短镜头3(4s) → ... → 短镜头N(4s)
```

**规则**：
- 每个镜头 4-5s，快速切换
- 镜头间使用 `cut`（直切），不用渐变
- 镜头类型多样化（远景、近景、插入镜头交替）
- 统一视觉风格（色调、光线一致）
- BGM 主导节奏，对白极少或无
- 最后一个镜头可延长，作为蒙太奇的"着陆点"

**Duration 建议**：每个 4s，总计 N × 4s

### 模式选择指南

| 场景类型 | 推荐模式 | 理由 |
|----------|---------|------|
| 双人对话 | 正反打 | 自然的对话节奏 |
| 新场景开场 | 建立-推进 | 空间→人物→情感的自然引导 |
| 重大事件/揭示 | 反应链 | 展示事件的多面影响 |
| 时间流逝/回忆 | 蒙太奇 | 高效压缩时间 |
| 追逐/战斗 | 蒙太奇 + 反应链 | 快速剪辑 + 关键反应 |
| 独白/内心戏 | 建立-推进（反向） | 从特写拉到远景展示孤独 |

---

## 8. Team 执行流程

### 8.1 Per-Scene 任务流

```
shot-coordinator 创建任务: "Design shots for Scene N"
  └→ shot-designer 生成 shot skeleton（结构 + CoT，无 prompt）
     └→ shot-coordinator 创建 3 个并行任务:
        ├→ image-prompter: "Generate image_prompts for Scene N shots"
        ├→ video-prompter: "Generate video_prompts for Scene N shots"
        └→ audio-prompter: "Generate audio_prompts for Scene N shots"
     └→ 3 个任务全部完成: coordinator 合并 prompt 到 shot skeleton
        └→ rhythm-checker 校验 Duration 和节奏
           └→ shot-reviewer 最终质量审查
              └→ 审核通过: coordinator 写入 Shot Annotation 到 script_breakdown.json
              └→ 审核不通过: 返回具体问题，相关专家修正后重新审查（最多 2 次）
```

### 8.2 数据合并策略（Coordinator Merge）

1. **shot-designer** 输出 shot skeleton JSON（per Scene）：
   ```json
   {
     "Internal Chain-of-Thought": { ... },
     "Shot": {
       "Shot 1": {
         "Involving Characters": { ... },
         "Plot/Visual Description": "...",
         "Coarse Plot": "...",
         "Emotional Enhancement": "...",
         "Shot Type": "...",
         "Camera Movement": "...",
         "Duration": 5,
         "Subtitles": { ... }
       }
     }
   }
   ```

2. **每个 prompt 专家** 输出字段映射：
   ```json
   // image-prompter
   { "Shot 1": { "image_prompt": "..." }, "Shot 2": { "image_prompt": "..." } }

   // video-prompter
   { "Shot 1": { "video_prompt": "...", "seedance_mode": "multimodal", "image_paths": [...] }, ... }

   // audio-prompter
   { "Shot 1": { "audio_prompt": "..." }, ... }
   ```

3. **Coordinator 深度合并**：
   ```python
   for shot_id in shot_skeleton["Shot"]:
       shot_skeleton["Shot"][shot_id].update(image_output[shot_id])
       shot_skeleton["Shot"][shot_id].update(video_output[shot_id])
       shot_skeleton["Shot"][shot_id].update(audio_output[shot_id])
   ```

4. **写入路径**：
   ```
   script_breakdown["Sub-Script"]["Sub-Script N"]["Scene Annotation"]["Scene"]["Scene M"]["Shot Annotation"]
   ```

### 8.3 外层并行（Outer Parallelism）

多个 Scene 可以同时处理（最多 3 个并发 Scene）。Coordinator 通过 TaskList 管理，创建类似 "Process Sub-Script 1 Scene 2" 的任务。

**并行约束**：
- 同一 Sub-Script 内的 Scene 可并行（它们共享角色资产但产出独立）
- 不同 Sub-Script 的 Scene 也可并行
- 角色外观描述文本在 coordinator 启动前统一提取，作为常量分发给所有 Scene

---

## 9. 质量审查清单

### CoT 完整性

- [ ] Internal Chain-of-Thought 包含全部 6 个步骤
- [ ] Step 1（Break Down Scene into Key Shots）≥ 2 句实质分析
- [ ] Step 2（Shot Composition and Framing）≥ 2 句实质分析
- [ ] Step 3（Character Positioning & Bounding Boxes）每角色 ≥ 1 句
- [ ] Step 4（Emotional Impact）≥ 2 句实质分析
- [ ] Step 5（Camera Techniques and Movements）≥ 2 句实质分析
- [ ] Step 6（Dialogue & Subtitle Accuracy）每对白行 ≥ 1 句

### Shot 结构字段

- [ ] Plot/Visual Description ≥ 30 词，含角色名 + 动作 + 环境
- [ ] Coarse Plot ≤ 20 词，**无角色名**
- [ ] Involving Characters 每角色有 [x1,y1,x2,y2] bounding box
- [ ] Bounding box 坐标归一化 [0,1]，无重叠，单镜头最多 3 角色
- [ ] Duration 为 4/5/10/15 之一，且经过公式计算
- [ ] Shot Type 来自 18 种扩展镜头类型表
- [ ] Camera Movement 来自 20+ 种扩展运镜词汇表
- [ ] Subtitles 包含该镜头中的所有对白（无遗漏、无错配）

### image_prompt

- [ ] 全英文
- [ ] **不含角色名**（仅用外观描述替代）
- [ ] 包含完整的角色外观描述（从 `<TOK>` 描述完整复制）
- [ ] 格式：`{style}, {shot_type}, {scene}, {appearance}, {lighting}, {mood}, {composition}`
- [ ] 同一角色在所有镜头中的外观描述文本逐字一致

### video_prompt

- [ ] @Image 编号连续且从 1 开始
- [ ] 角色参考图在前，首帧图在最后
- [ ] @Image 引用数量 == image_paths 数组长度
- [ ] 有已设计资产的角色必须有 @Image 引用
- [ ] 无资产角色仅用文字描述（无 @Image）
- [ ] 最后一个 @Image 标注为 "作为首帧"
- [ ] 描述动态变化和运镜，不重复静态信息

### audio_prompt

- [ ] 中文描述
- [ ] 包含环境音效（ambient_sounds）
- [ ] 包含动作音效（action_sfx）
- [ ] 对白格式：`{性别/年龄}{语气}说：'{台词}'`
- [ ] 包含 BGM 描述
- [ ] 对白情绪与角色弧线匹配

### seedance_mode

- [ ] 有已设计角色参与 → `multimodal`
- [ ] 仅场景图/空镜（无角色参考图）→ `i2v`
- [ ] 无任何图片 → `t2v`

### 跨镜头一致性

- [ ] 同一角色在所有镜头中的外观描述逐字一致
- [ ] 同一场景内背景风格、光照方向、色调一致
- [ ] 连续镜头间动作衔接自然（无跳变）
- [ ] 场景内镜头类型有变化（不全是同一种景别）
- [ ] Duration 分布合理（不全是同一时长）
