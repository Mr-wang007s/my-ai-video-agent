---
name: export-render
description: "导出与质量审查。最终交付物的质量保障——多维度审查、制作指南导出、资产清单生成、成本预估。涵盖 Step 5（export-guide）。"
team:
  enabled: true
  pattern: review
  coordinator: post-supervisor
  roles:
    - name: post-supervisor
      type: coordinator
      expertise: "Post-production supervision, deliverable quality"
      system_prompt: |
        You supervise the final export process:
        1. Run structure-auditor to verify JSON integrity
        2. Run prompt-auditor to check all prompts
        3. Run rhythm-auditor to validate pacing
        4. Collect all audit reports
        5. If all pass, generate the final export files
        6. If any fail, report issues for resolution
      responsibilities:
        - Orchestrate multi-dimension quality review
        - Generate export files after all audits pass
        - Produce cost estimate and asset checklist
    - name: structure-auditor
      type: reviewer
      expertise: "Three-layer JSON structure, CoT completeness"
      system_prompt: |
        Audit script_breakdown.json structure:
        1. All Sub-Scripts have Scene Annotation
        2. All Scenes have Shot Annotation
        3. All 3 layers of CoT are complete (5+4+6 steps)
        4. Required fields present on every Shot
        5. Schema compliance with schemas/script_breakdown.schema.json
      responsibilities:
        - Three-layer nesting integrity
        - CoT step count and content verification
        - Required field presence
    - name: prompt-auditor
      type: reviewer
      expertise: "Prompt format compliance, character consistency"
      system_prompt: |
        Audit all prompts across the entire breakdown:
        1. image_prompt: English, no character names, full appearance, style prefix
        2. video_prompt: @Image count matches image_paths, correct ordering
        3. audio_prompt: Chinese, has all 4 layers (ambient+sfx+dialogue+bgm)
        4. Character appearance text identical across all shots
        5. Duration is 4/5/10/15
      responsibilities:
        - Cross-shot character appearance text comparison
        - Prompt format compliance
        - @Image reference validation
    - name: rhythm-auditor
      type: reviewer
      expertise: "Pacing, duration distribution, genre alignment"
      system_prompt: |
        Audit narrative rhythm:
        1. Duration distribution matches genre expectations
        2. Shot type variety within each scene
        3. Emotional curve follows the genre template
        4. No consecutive shots with identical shot type
        5. Total duration within target range (60-300s per episode)
      responsibilities:
        - Duration distribution analysis
        - Shot variety check
        - Emotional curve validation
  coordination:
    merge_strategy: sequential-pipeline
    review_required: true
---

# Export & Quality Review Skill (export-render)

> 最终交付物的质量保障——多维度审查、制作指南导出、资产清单生成、成本预估。

## 1. Core Principles

1. **Quality Gate Before Export**: No export files are generated until all three quality audits pass. The breakdown must be verified structurally, linguistically, and rhythmically before any deliverables are produced.
2. **Multi-Dimensional Audit**: Three independent reviewers audit the `script_breakdown.json` in parallel — structure integrity, prompt compliance, and narrative rhythm — ensuring no single dimension is overlooked.
3. **User-Friendly Output**: All export deliverables are designed for direct use by a human operator working across Gemini (images), Kling/Seedance (video), and CapCut/剪映 (assembly). Prompts are cleaned, organized by shot order, and ready to copy-paste.

## 2. Quality Review Dimensions (3 Parallel Audits)

The three auditors run **in parallel** — they are independent of each other and examine different dimensions of the same `script_breakdown.json`.

### 2.1 Structure Audit (structure-auditor)

Verifies the three-layer JSON structure and CoT completeness.

**Checks:**

- [ ] `script_breakdown.json` contains `Relationships` + `Internal Chain-of-Thought` + `Sub-Script` top-level keys
- [ ] Every `Sub-Script{N}` contains `Scene Annotation` (with CoT + Scene list)
- [ ] Every `Scene{N}` contains `Shot Annotation` (with CoT + Shot list)
- [ ] Three-layer nesting hierarchy is correct (Sub-Script → Scene → Shot)
- [ ] Layer 1 CoT contains all 5 required steps:
  - Step 1: Core Narrative Structure
  - Step 2: Key Character Information
  - Step 3: Temporal Segmentation
  - Step 4: Sub-Script Breakdown Criteria
  - Step 5: Division Rationale
- [ ] Layer 2 CoT contains all 4 required steps:
  - Step 1: Narrative Structure
  - Step 2: Key Scene Elements
  - Step 3: Scene Boundaries
  - Step 4: Cinematic Elements for Each Scene
- [ ] Layer 3 CoT contains all 6 required steps:
  - Step 1: Break Down Scene into Key Shots
  - Step 2: Shot Composition and Framing
  - Step 3: Character Positioning & Bounding Boxes
  - Step 4: Emotional Impact
  - Step 5: Camera Techniques and Movements
  - Step 6: Dialogue & Subtitle Accuracy
- [ ] Every CoT step has substantive content (not empty strings, not `{}`)
- [ ] Every Shot has all required fields: `Shot Type`, `Camera Movement`, `Duration`, `image_prompt`, `video_prompt`, `audio_prompt`, `Involving Characters`, `Plot/Visual Description`, `Coarse Plot`, `Subtitles`
- [ ] Schema compliance with `schemas/script_breakdown.schema.json`

### 2.2 Prompt Audit (prompt-auditor)

Verifies prompt format compliance and character consistency across all shots.

**Checks:**

- [ ] **image_prompt** (every shot):
  - Written in English
  - Contains a style prefix (e.g., `manga style,`, `anime style,`)
  - Does **NOT** contain character names (uses appearance descriptions instead, per Coarse Plot strategy)
  - Contains full character appearance description (derived from `<TOK>` description minus the `<TOK>` prefix)
  - Includes negative prompt guidance for common defects
- [ ] **video_prompt** (every shot):
  - `@ImageN` reference count **equals** the `image_paths` array length
  - Character reference images come first, keyframe image is last
  - `@ImageN` numbering follows `image_paths` array order
  - Focuses on dynamic changes and camera movement (not repeating static descriptions)
- [ ] **audio_prompt** (every shot):
  - Written in Chinese
  - Contains all 4 layers: 环境音效 (ambient) + 动作音效 (SFX) + 对白 (dialogue with gender/tone) + BGM
  - Dialogue format: `{性别/年龄}{语气}说：'{台词}'`
- [ ] **Cross-shot character consistency**:
  - Same character's appearance text is **identical** (word-for-word) across all shots
  - Appearance description is complete (not abbreviated or paraphrased)
  - Only characters with `character_list/{Name}/` assets get `@Image` references in `video_prompt`
- [ ] **Duration** values are valid Seedance tiers: `4`, `5`, `10`, or `15` only
- [ ] **seedance_mode** is correctly assigned:
  - `multimodal` — when at least 1 designed character participates (has `best.png`)
  - `i2v` — scene-only / empty shot (no character reference images)
  - `t2v` — no images at all

### 2.3 Rhythm Audit (rhythm-auditor)

Verifies narrative pacing, duration distribution, and emotional curve.

**Checks:**

- [ ] **Duration distribution** matches genre expectations:
  - Short manga drama (60-120s): 12-24 shots
  - Standard manga drama (120-300s): 24-60 shots
  - Total duration falls within target range
- [ ] **Shot type variety** within each scene:
  - No more than 2 consecutive shots with identical shot type
  - Mix of wide/medium/close-up/action shots per scene
- [ ] **Emotional curve** follows genre template:
  - Setup (first ~20%): slow pace, wide shots, calm audio
  - Development (~20-60%): increasing pace, medium shots with close-up inserts
  - Climax (~60-85%): fast pace, close-ups and action shots, intense audio
  - Resolution (last ~15%): slowing pace, emotional payoff or cliffhanger
- [ ] **Duration calculation compliance** (per `narrative-rhythm` rule):
  - Dialogue time = `Σ(characters × 0.2 + 1.0) + 0.5 × (sentence_count - 1)`
  - Action time = low(2s) | medium(4s) | high(6s)
  - Minimum duration = `max(dialogue_time, action_time) + 1s`
  - Duration rounded up to nearest Seedance tier (4/5/10/15)
- [ ] **No shot exceeds 15s** — if calculated minimum > 15s, the shot must be split
- [ ] **Transition rules** are correct:
  - Same-scene cuts: `cut`
  - Scene changes: `fade` or `dissolve`
  - Time jumps: `fade` + black screen
  - Climax/turning points: `wipe` (optional)

## 3. Audit Report Format

Each auditor produces a structured report:

```json
{
  "dimension": "structure|prompt|rhythm",
  "status": "pass|fail",
  "issues": [
    {
      "location": "Sub-Script 1.Scene 2.Shot 3",
      "type": "missing_cot_step|invalid_prompt_language|duration_mismatch|...",
      "severity": "error|warning",
      "detail": "Layer 2 CoT missing Step 3: Scene Boundaries",
      "fix": "Re-run Layer 2 CoT for Sub-Script 1 with all 4 required steps"
    }
  ],
  "statistics": {
    "total_checked": 45,
    "passed": 43,
    "failed": 2,
    "warnings": 1
  }
}
```

**Severity levels:**
- `error` — Must be fixed before export. Blocks the quality gate.
- `warning` — Recommended fix but does not block export. Logged for review.

## 4. Export Outputs

After all three audits pass, the following files are generated in `projects/{project_id}/exports/`:

### 4.1 `storyboard_guide.md` — Full Production Guide

Organized by Sub-Script → Scene → Shot, this is the primary deliverable for manual production.

**Per shot includes:**
- Shot metadata (shot_id, shot type, camera movement, duration, transition, characters)
- `image_prompt` — ready to copy into Gemini for keyframe generation
- `video_prompt` — cleaned version (with `@Image` references converted to readable text) for Kling/Seedance
- `audio_prompt` — Chinese description for dubbing/SFX reference in CapCut
- Visual description and subtitles

**Structure:**
```markdown
# {Project Name} - 分镜制作指南
## 角色参考 (character reference table)
## 使用说明 (platform instructions)
## Sub-Script 1: {Plot summary}
### Scene 1: {Description}
#### Shot 1 (S1_Sc1_Shot1)
| 属性 | 值 |
| 镜头类型 | Close-up |
| 运镜 | Slow zoom in |
| 时长 | 5s |
| 转场 | cut |
**Gemini 图片 Prompt**: > {image_prompt}
**可灵视频 Prompt**: > {cleaned video_prompt}
**音频描述**: > {audio_prompt}
**字幕**: {subtitles}
---
## 汇总
- 总镜头数 / 预估总时长
```

### 4.2 `asset_checklist.md` — Asset Generation Checklist

Lists every asset that needs to be generated, organized by type.

**Sections:**

#### Character Reference Images
```markdown
| # | 角色 | 资产目录 | 需要生成 | 状态 |
|---|------|---------|---------|------|
| 1 | Elsa | character_list/Elsa/ | best.png + 3-5 multi-angle photos | pending |
| 2 | Anna | character_list/Anna/ | best.png + 3-5 multi-angle photos | pending |
```

#### Keyframe Images (per shot)
```markdown
| # | Shot ID | image_prompt (摘要) | 输出路径 | 状态 |
|---|---------|-------------------|---------|------|
| 1 | S1_Sc1_Shot1 | manga style, a vast icy landscape... | images/shots/S1_Sc1_Shot1.png | pending |
```

#### Video Clips (per shot)
```markdown
| # | Shot ID | Duration | Seedance Mode | 依赖图片 | 状态 |
|---|---------|----------|--------------|---------|------|
| 1 | S1_Sc1_Shot1 | 5s | multimodal | S1_Sc1_Shot1.png + Elsa/best.png | pending |
```

#### Dialogue Lines (per character, for dubbing)
```markdown
| # | 角色 | Shot ID | 台词 | 语气 |
|---|------|---------|------|------|
| 1 | Elsa | S1_Sc2_Shot1 | "这是我的命运" | 坚定、略带忧伤 |
```

### 4.3 `cost_estimate.md` — Cost Estimation Report

Provides a detailed cost breakdown based on actual API pricing.

## 5. User Manual Operation Guide

### Step 1: Generate Character Reference Images (Gemini)

1. Open `storyboard_guide.md`, locate the **角色参考** table
2. For each character with `design_status: extracted`:
   - Copy the character's `appearance_description` 
   - Open Gemini (gemini.google.com), paste the description as an image generation prompt
   - Add style prefix: `"manga style, full body character reference sheet, front view and side view, white background, "`
   - Generate 3-5 variations, select the best one
   - Save as `projects/{project_id}/character_list/{CharName}/best.png`
   - Save additional angles as `photo_1.png` through `photo_5.png`
3. Write the `<TOK>` description in `best.txt`:
   - Format: `<TOK> a woman with long blonde hair in a braid, wearing a flowing purple-white gradient dress...`
   - Must be in English, must be comprehensive (all visual features)
4. Update `characters.json`: set `design_status` to `"designed"`, fill `tok_description` and `asset_dir`

### Step 2: Generate Keyframe Images (Gemini)

1. Open `storyboard_guide.md` or `storyboard_prompts.csv`
2. For each shot, locate the **Gemini 图片 Prompt** section
3. Copy the `image_prompt` exactly as-is into Gemini
4. Add the standard negative prompt to improve quality:
   ```
   Negative: low quality, blurry, deformed, extra fingers, bad anatomy, disfigured, poorly drawn face, mutation, mutated, ugly, watermark, text
   ```
5. Generate the image at 1024x1024 resolution
6. Save to `projects/{project_id}/images/shots/{shot_id}.png`
7. Verify character appearance matches the reference images before proceeding

**Tips for consistency:**
- Use the same style prefix across all shots within one episode
- Generate same-scene shots in one session to maintain background consistency
- If a character looks different from their reference, regenerate with more specific description

### Step 3: Generate Video Clips (Kling / Seedance)

1. Open `storyboard_guide.md` or `storyboard_prompts.csv`
2. For each shot:
   - **i2v mode** (scene-only shots): Upload keyframe image → paste cleaned `video_prompt` → set duration
   - **multimodal mode** (character shots): Upload character `best.png` files + keyframe image → paste `video_prompt` with `@Image` references → set duration
   - **t2v mode** (no images): Paste `video_prompt` text only → set duration
3. Set duration to match the `Duration` column (4/5/10/15 seconds)
4. Download generated video within 24 hours (URLs expire)
5. Save to `projects/{project_id}/videos/{shot_id}.mp4`

**Cost awareness:**
- Preview at 720p first, then regenerate at 1080p for final version
- Most shots work well at 5s — only use 10s/15s for action or emotional scenes
- Budget reference: 5s = ~3.67 yuan, 10s = ~7 yuan, 15s = ~10 yuan per clip

### Step 4: Assemble and Dub in CapCut (剪映)

1. Create a new project in 剪映 (9:16 portrait for short-form, 16:9 landscape for standard)
2. Import all video clips from `projects/{project_id}/videos/`
3. Arrange clips on the timeline in `shot_id` order (S1_Sc1_Shot1, S1_Sc1_Shot2, ...)
4. Add transitions between clips:
   - Same-scene: direct cut (no transition)
   - Scene change: fade/dissolve (0.3-0.5s)
   - Time jump: fade to black
5. Add subtitles from the **字幕** column for each shot
6. For audio/dubbing, reference the **音频描述** column:
   - Add BGM tracks matching the emotional curve
   - Record or generate dialogue with correct gender/tone
   - Add ambient sounds and SFX as described
7. Fine-tune timing — ensure subtitles align with dialogue
8. Export final video

## 6. Cost Estimation Formula

### API Pricing Reference

| API | Tier | Unit Cost |
|-----|------|-----------|
| DALL-E 3 | 1024x1024 | 0.28 yuan |
| Seedance 2.0 | 4s / 1080p + audio | ~3.67 yuan |
| Seedance 2.0 | 5s / 1080p + audio | ~3.67 yuan |
| Seedance 2.0 | 10s / 1080p + audio | ~7.00 yuan |
| Seedance 2.0 | 15s / 1080p + audio | ~10.00 yuan |
| SD API (local) | any | 0 yuan |
| Volcano TTS | per 1k chars (override only) | ~0.01 yuan |

### Calculation Formula

```
Character Reference Image Cost:
  = character_count × reference_images_per_char × 0.28 yuan
  (typically 5 images per character: 1 best + 4 angles)

Keyframe Image Cost:
  = total_shots × 0.28 yuan

Total Image Cost:
  = Character Reference Cost + Keyframe Cost
  = (character_count × 5 + total_shots) × 0.28 yuan

Video Cost:
  = Σ (per shot) tier_price(duration)
  where tier_price(4s) = 3.67, tier_price(5s) = 3.67,
        tier_price(10s) = 7.00, tier_price(15s) = 10.00

Total Estimated Cost:
  = Total Image Cost + Video Cost
```

### Example Estimate

For a standard manga drama episode with 3 characters and 30 shots:
- Duration distribution: 20× 5s, 7× 10s, 3× 15s

```
Image Cost:
  Character refs: 3 × 5 × 0.28 = 4.20 yuan
  Keyframes:      30 × 0.28    = 8.40 yuan
  Subtotal:                    = 12.60 yuan

Video Cost:
  20 × 3.67 (5s)  = 73.40 yuan
  7 × 7.00 (10s)  = 49.00 yuan
  3 × 10.00 (15s) = 30.00 yuan
  Subtotal:        = 152.40 yuan

Total: 12.60 + 152.40 = 165.00 yuan
```

**Cost optimization tips:**
- Use local SD API instead of DALL-E for keyframes (saves ~8.40 yuan in above example)
- Preview videos at 720p before final 1080p generation
- Most dialogue shots work at 5s — reserve 10s/15s for action sequences only
- Seedance audio-video joint generation eliminates separate TTS costs

## 7. Team Execution Flow

```
┌──────────────────────────────────────────────────┐
│              post-supervisor (coordinator)         │
│                                                    │
│  1. Load script_breakdown.json + characters.json   │
│  2. Dispatch 3 auditors IN PARALLEL ───────────┐  │
│                                                 │  │
│  ┌─────────────────┐ ┌──────────────┐ ┌────────┴┐ │
│  │structure-auditor│ │prompt-auditor│ │rhythm-  │ │
│  │                 │ │              │ │auditor  │ │
│  │ JSON integrity  │ │ Prompt format│ │ Pacing  │ │
│  │ CoT completeness│ │ Char consist.│ │ Duration│ │
│  │ Field presence  │ │ @Image valid.│ │ Emotion │ │
│  └────────┬────────┘ └──────┬───────┘ └────┬────┘ │
│           │                 │              │       │
│  3. Collect all 3 audit reports ◄──────────┘       │
│                                                    │
│  4. Decision gate:                                 │
│     ├─ ALL PASS → Generate export files (4.1-4.3)  │
│     └─ ANY FAIL → Report issues to user            │
│        → User fixes → Re-run failed audits only    │
│                                                    │
│  5. Generate exports:                              │
│     ├─ storyboard_guide.md                         │
│     ├─ asset_checklist.md                           │
│     └─ cost_estimate.md                            │
│                                                    │
│  6. Update project status → "exported"             │
└──────────────────────────────────────────────────┘
```

### Execution Details

1. **post-supervisor** reads `script_breakdown.json` and `characters.json` from `projects/{project_id}/`
2. **Three auditors are dispatched IN PARALLEL** — each receives the full breakdown and characters data
3. Each auditor produces an audit report (see Section 3 format)
4. **post-supervisor** collects all 3 reports:
   - If **all 3 pass**: proceed to export generation
   - If **any fail**: compile a unified issue list, report to user with fix suggestions
   - User applies fixes → only the failed audit dimensions are re-run (not all 3)
5. Export files are generated using the existing `export_storyboard.py` logic (Markdown + CSV) plus the new `asset_checklist.md` and `cost_estimate.md`
6. Project status is updated to `"exported"`

## 8. Quality Checklist (Comprehensive)

This checklist consolidates all quality checks from the three auditors plus the `quality-standards` rule. It serves as a final sign-off before export.

### Structure & CoT
- [ ] `script_breakdown.json` contains `Relationships` + `Internal Chain-of-Thought` + `Sub-Script` top-level keys
- [ ] Every Sub-Script has `Scene Annotation` (with CoT + Scene list)
- [ ] Every Scene has `Shot Annotation` (with CoT + Shot list)
- [ ] Three-layer nesting hierarchy is correct
- [ ] Layer 1 CoT: 5 steps, each with substantive content (>=2 sentences per step)
- [ ] Layer 2 CoT: 4 steps, each with substantive content (>=2 sentences per step; Step 4 >=2 sentences per scene)
- [ ] Layer 3 CoT: 6 steps, each with substantive content (Steps 1-2,4-5 >=2 sentences; Step 3 >=1 sentence per character; Step 6 >=1 sentence per dialogue line)
- [ ] No CoT step is empty, `{}`, or contains only template/placeholder text
- [ ] Every Shot has all required fields present

### Prompt Quality
- [ ] All `image_prompt` values are in English
- [ ] All `image_prompt` values have a style prefix (`manga style,`, `anime style,`, etc.)
- [ ] No `image_prompt` contains character names (uses full appearance description instead)
- [ ] All `image_prompt` values include complete character appearance from `<TOK>` description
- [ ] Same character's appearance text is word-for-word identical across all shots
- [ ] All `video_prompt` `@ImageN` counts match `image_paths` array lengths
- [ ] `@Image` ordering: character refs first, keyframe last
- [ ] All `audio_prompt` values are in Chinese
- [ ] All `audio_prompt` values contain 4 layers: ambient + SFX + dialogue + BGM
- [ ] Dialogue in `audio_prompt` follows format: `{性别/年龄}{语气}说：'{台词}'`
- [ ] All `Duration` values are valid Seedance tiers: 4, 5, 10, or 15
- [ ] `seedance_mode` correctly assigned per character participation

### Narrative Rhythm
- [ ] Total duration within target range (60-300s per episode)
- [ ] Shot count within range (8-60 per episode)
- [ ] No more than 2 consecutive shots with identical shot type
- [ ] Duration calculation matches dialogue/action timing formula
- [ ] No shot with calculated minimum > 15s (must be split)
- [ ] Emotional curve follows setup → development → climax → resolution arc
- [ ] Transitions correct: `cut` within scenes, `fade`/`dissolve` between scenes

### Character Consistency
- [ ] Every designed character has `character_list/{Name}/` directory spec
- [ ] `best.png` and `best.txt` documented for each designed character
- [ ] `best.txt` starts with `<TOK>` prefix, uses English
- [ ] Characters without assets do NOT get `@Image` references
- [ ] Character appearance descriptions are specific and repeatable (no vague words)
- [ ] Bounding boxes `[x1, y1, x2, y2]` are normalized [0,1] and non-overlapping
- [ ] Max 3 characters per shot (1-2 recommended)

### Visual Consistency
- [ ] Same scene: consistent background style, lighting direction, color tone
- [ ] Same episode: no significant art style jumps
- [ ] Consistent style prefix used across all shots in an episode
