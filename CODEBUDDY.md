# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

## Commands

### Environment Setup
```bash
pip install -r scripts/requirements.txt
```
Install Python dependencies (requests, python-dotenv, openai, ffmpeg-python, Pillow). FFmpeg binary must also be in PATH for video composition (Step 6).

### Initialize Database
```bash
python scripts/db_manager.py --action init_db
```
Creates SQLite tables (projects, scripts, storyboards, characters, assets, generations) in `data.db`. Use `--data '{"force": true}'` to drop and recreate all tables.

### Verify Skills
```bash
ls .codebuddy/skills/
```
Should list 10 Skill directories: `script-parser`, `script-scene`, `character-design`, `character-acting`, `shot-director`, `shot-rhythm`, `prompt-image`, `prompt-video`, `prompt-audio`, `export-render`.

## Architecture

### Overview

This is an AI manga drama (漫剧) automated production pipeline based on MovieAgent architecture. It converts novel/screenplay text into short-form video through a 6-step pipeline. The system uses a **Skills + Rules + Agent Teams** architecture: the main AI conversation loads domain-specific Skills on demand, spawns Agent Teams for complex parallel/review tasks, and performs all data I/O through file system operations (Read/Write/Bash).

### Pipeline Flow (6 Steps)

```
/init-project → /import-script → /extract-characters → /design-characters
→ /break-script → /export-guide
```

State machine: `draft → imported → characters_extracted → characters_designed → script_broken → exported`. Each step validates the current state before proceeding, and updates it via `Write: projects/{id}/status.json` upon completion.

### Core Data Flow — File-Based Routing

All pipeline artifacts live under `projects/{project_id}/`. Steps communicate exclusively through JSON files in this directory — there is no in-memory state passing:

- **Step 2** produces `raw_script.txt` + `script_synopsis.json` (story summary, character list, relationships)
- **Step 3a** produces `characters.json` (all characters with appearance descriptions, design status)
- **Step 3b** produces `character_list/{CharName}/` asset directories (best.png, best.txt, multi-angle photos)
- **Step 4** produces `script_breakdown.json` — the **central artifact** — a three-layer nested JSON (Sub-Script → Scene → Shot)
- **Step 5** produces `exports/` with production guide (Markdown), cost estimate, and per-shot instruction sheets

Project IDs use format `YYYYMMDD_HHMMSS_别名` (e.g., `20260228_080847_冰雪奇缘2漫剧版`).

### Three-Layer CoT Decomposition (Step 4 — The Core)

Step 4 implements MovieAgent's key innovation: three independent Chain-of-Thought reasoning passes that transform a screenplay into executable shot descriptions:

1. **Layer 1 (screenwriterCoT)**: Full script → ≤20 Sub-Scripts (chapters/acts). Each must include 5-step CoT reasoning (narrative structure → character extraction → temporal segmentation → validation → division rationale).
2. **Layer 2 (ScenePlanningCoT)**: Each Sub-Script → Scenes (with 4-step CoT). Loop iterates over all Sub-Scripts independently.
3. **Layer 3 (ShotPlotCreateCoT)**: Each Scene → Shots (with 6-step CoT). Double loop: Sub-Script × Scene. Each Shot gets dual descriptions (`Coarse Plot` without character names for image generation, `Plot/Visual Description` with names for video) and triple prompts (`image_prompt` in English for DALL-E, `video_prompt` with @Image references for Seedance, `audio_prompt` in Chinese for joint audio-video generation).

Each layer uses independent context (`use_history=False`) — no accumulated conversation history between calls. The `cot-reasoning` rule enforces that CoT fields are never empty or skipped.

### Skills + Rules + Agent Teams Dispatch System

The `pipeline-dispatch` rule (alwaysApply) maps each pipeline step to required Skills and Agent Teams.

**10 Skills** organized in 5 modules (loaded via `use_skill()` before executing a step):

| Module | Skill | Team | Description |
|--------|-------|------|-------------|
| Script | `script-parser` | — | Screenplay parsing, synopsis extraction, Layer 1 screenwriterCoT |
| | `script-scene` | Team A (parallel) | Layer 2 ScenePlanningCoT, lighting/color/transition design |
| Character | `character-design` | — | `<TOK>` format, Visual ID Card, wardrobe system, reference image generation |
| | `character-acting` | Team C (specialization) | Personality, expression/body language vocabulary, voice design |
| Shot | `shot-director` | Team B (multi-modal) | Layer 3 ShotPlotCreateCoT, 18 shot types, 20+ camera movements |
| | `shot-rhythm` | — | Duration formula, genre rhythm templates, emotion curves |
| Prompt | `prompt-image` | Team D (review) | image_prompt construction, style prefixes, platform adaptation |
| | `prompt-video` | Team E (review) | video_prompt + @Image references, dynamic vocabulary |
| | `prompt-audio` | — | audio_prompt construction, environment sounds, BGM matrix |
| Export | `export-render` | Team F (review) | Three-auditor quality gate, cost estimation, production guide |

**6 Agent Teams** spawn when Skills define `team.enabled: true`. 4 coordination patterns:
- **parallel**: Same task distributed to N workers (Layer 2 per-SubScript)
- **specialization**: Different experts handle different aspects (character acting)
- **review**: Generate→review chain (prompt quality gates)
- **multi-modal**: Image/video/audio specialists work in parallel (Layer 3)

Team lifecycle: `use_skill()` → read team config → `TeamCreate` → spawn teammates → `TaskList` coordination → shutdown → `TeamDelete` → update status.

**Step → Skill → Team Mapping:**

| Step | Command | Skills | Team |
|------|---------|--------|------|
| 1 | `/init-project` | — | — |
| 2 | `/import-script` | `script-parser` | — |
| 3a | `/extract-characters` | `script-parser` + `character-design` + `character-acting` | character-acting Team C |
| 3b | `/design-characters` | `character-design` | — |
| 4a | `/break-script` (L1) | `script-parser` | — |
| 4b | `/break-script` (L2) | `script-scene` + `shot-rhythm` | script-scene Team A |
| 4c | `/break-script` (L3) | `shot-director` + `prompt-image` + `prompt-video` + `prompt-audio` + `shot-rhythm` | shot-director Team B |
| 5 | `/export-guide` | `export-render` | export-render Team F |

**6 Rules** (in `.codebuddy/rules/`, auto-applied):
- `pipeline-dispatch` — step→skill→team mapping, state machine, dispatch principles
- `cot-reasoning` — mandatory CoT fields per layer, independent context enforcement
- `api-usage` — env var management, cost control (Seedance 50/day), exponential backoff retry
- `character-consistency` — asset directory validation, `<TOK>` format, image_prompt must not contain character names
- `narrative-rhythm` — duration alignment to Seedance tiers, transition rules (cut/fade/blackout)
- `quality-standards` — CoT completeness, prompt specs, three-layer JSON validation

### `script_breakdown.json` Schema

This is the pipeline's backbone. Three-layer nesting: `Sub-Script{N}` → `.Scene Annotation.Scene{N}` → `.Shot Annotation.Shot{N}`. Each Shot contains: `Involving Characters` (with normalized bounding boxes [x1,y1,x2,y2]), `Plot/Visual Description`, `Coarse Plot`, `image_prompt`, `video_prompt`, `audio_prompt`, `Shot Type`, `Camera Movement`, `Duration` (4/5/10/15), `Subtitles`, `seedance_mode` (i2v/multimodal/t2v). Schema is in `schemas/script_breakdown.schema.json`.

### Character Consistency via @Image

Seedance 2.0's multimodal mode accepts `@Image{N}` references in prompts. The pattern is: character reference images (`character_list/{Name}/best.png`) are placed first, then the keyframe image last. Example: `@Image1 作为Elsa外观参考。@Image2 作为首帧，角色微微抬头...`. Characters without designed assets fall back to text-only description in `image_prompt`.

### SQLite Database (`data.db`)

Schema in `scripts/init_db.sql`. Six tables: `projects` (status-driven state machine), `scripts`, `storyboards`, `characters` (per-project), `assets` (image/video/audio with metadata), `generations` (audit log for all API calls with cost tracking). Database is optional — the pipeline uses file-based routing (`projects/{id}/*.json`) as primary data store. Legacy MCP server (`scripts/mcp_server.py`) and `db_manager.py` are retained for reference but not used by Skills or Commands.

### Environment Variables

Required in `.env` (loaded by `python-dotenv`):
- `ARK_API_KEY` / `ARK_BASE_URL` / `SEEDANCE_MODEL` — Seedance 2.0 video generation (Step 5)
- `OPENAI_API_KEY` — DALL-E 3 image generation (Steps 3b, 5)
- `VOLC_TTS_APP_ID` / `VOLC_TTS_TOKEN` — Volcano TTS (optional, for voice override)
- `SD_API_URL` — Local Stable Diffusion (optional alternative to DALL-E)

Steps 1–4 require no API keys (pure LLM reasoning + file I/O). API keys are only needed for actual image/video generation (post-export manual operations).
