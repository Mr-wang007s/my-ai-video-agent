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

### Verify MCP Server
```bash
python -c "import scripts.mcp_server as ms; print('Tools:', len(ms.mcp._tool_manager._tools))"
```
Should print "Tools: 15". The MCP server is the sole interface for all pipeline operations — never call Python scripts directly via bash.

### Run MCP Server (stdio)
```bash
python scripts/mcp_server.py
```
Launches the `manga-agent` MCP server over stdio. Configuration is in `.codebuddy/mcp.json`.

## Architecture

### Overview

This is an AI manga drama (漫剧) automated production pipeline based on MovieAgent architecture. It converts novel/screenplay text into short-form video through a 7-step pipeline. The system uses a **Skills + Rules + MCP** architecture where the main AI conversation loads domain-specific Skills on demand and executes all operations through a unified MCP server — there are no sub-agents.

### Pipeline Flow (7 Steps)

```
/init-project → /import-script → /extract-characters → /design-characters
→ /break-script → /generate-video → /compose-final
```

State machine: `draft → imported → characters_extracted → characters_designing → script_broken → generating → generated → composing → completed`. Each step validates the current state before proceeding, and updates it via `project_update_status` MCP tool upon completion.

### Core Data Flow — File-Based Routing

All pipeline artifacts live under `projects/{project_id}/`. Steps communicate exclusively through JSON files in this directory — there is no in-memory state passing:

- **Step 2** produces `raw_script.txt` + `script_synopsis.json` (story summary, character list, relationships)
- **Step 3a** produces `characters.json` (all characters with appearance descriptions, design status)
- **Step 3b** produces `character_list/{CharName}/` asset directories (best.png, best.txt, multi-angle photos)
- **Step 4** produces `script_breakdown.json` — the **central artifact** — a three-layer nested JSON (Sub-Script → Scene → Shot)
- **Step 5** produces `images/shots/`, `videos/`, `video_manifest.json`
- **Step 6** produces `final/` with the composed video

Project IDs use format `YYYYMMDD_HHMMSS_别名` (e.g., `20260228_080847_冰雪奇缘2漫剧版`).

### Three-Layer CoT Decomposition (Step 4 — The Core)

Step 4 implements MovieAgent's key innovation: three independent Chain-of-Thought reasoning passes that transform a screenplay into executable shot descriptions:

1. **Layer 1 (screenwriterCoT)**: Full script → ≤20 Sub-Scripts (chapters/acts). Each must include 5-step CoT reasoning (narrative structure → character extraction → temporal segmentation → validation → division rationale).
2. **Layer 2 (ScenePlanningCoT)**: Each Sub-Script → Scenes (with 4-step CoT). Loop iterates over all Sub-Scripts independently.
3. **Layer 3 (ShotPlotCreateCoT)**: Each Scene → Shots (with 6-step CoT). Double loop: Sub-Script × Scene. Each Shot gets dual descriptions (`Coarse Plot` without character names for image generation, `Plot/Visual Description` with names for video) and triple prompts (`image_prompt` in English for DALL-E, `video_prompt` with @Image references for Seedance, `audio_prompt` in Chinese for joint audio-video generation).

Each layer uses independent context (`use_history=False`) — no accumulated conversation history between calls. The `cot-reasoning` rule enforces that CoT fields are never empty or skipped.

### MCP Server (`scripts/mcp_server.py`)

Single unified MCP server exposing 15 tools across 5 categories. This is the **only** interface for all operations — bash calls to Python scripts are forbidden by the `pipeline-dispatch` rule.

| Category | Tools |
|----------|-------|
| Project | `project_init_db`, `project_create`, `project_list`, `project_get`, `project_update_status`, `project_summary` |
| Script | `script_import`, `script_stats`, `script_text` |
| Character | `character_save`, `character_list` |
| Asset | `asset_save`, `asset_list` |
| Logging | `generation_log` |
| Export | `export_storyboard_markdown` |

The server imports from 3 Python modules in `scripts/`: `db_manager`, `import_script`, `export_storyboard`. All modules output `{"status": "success/failed", ...}` JSON.

### Skills + Rules Dispatch System

The `pipeline-dispatch` rule (alwaysApply) maps each pipeline step to required Skills and MCP tools:

**6 Skills** (loaded via `use_skill()` before executing a step):
- `manga-script` — screenplay parsing, synopsis extraction, character identification
- `character-consistency` — `<TOK>` description format, character_list directory structure, Seedance @Image reference strategy
- `script-breakdown` — three-layer CoT prompt templates (Layer 1/2/3 system prompts)
- `storyboard-design` — shot types, camera movements, triple-prompt generation specs, duration alignment (4/5/10/15s)
- `seedance-video` — Seedance 2.0 API modes (t2v/i2v/multimodal), prompt optimization, audio-video joint generation
- `voice-synthesis` — TTS voice selection, emotion-speech mapping, audio replacement

**5 Rules** (in `.codebuddy/rules/`, auto-applied):
- `pipeline-dispatch` — step→skill→MCP mapping, state machine, dispatch principles
- `cot-reasoning` — mandatory CoT fields per layer, independent context enforcement
- `api-usage` — env var management, cost control (Seedance 50/day), exponential backoff retry
- `character-consistency` — asset directory validation, `<TOK>` format, image_prompt must not contain character names
- `narrative-rhythm` — duration alignment to Seedance tiers, transition rules (cut/fade/blackout)

### `script_breakdown.json` Schema

This is the pipeline's backbone. Three-layer nesting: `Sub-Script{N}` → `.Scene Annotation.Scene{N}` → `.Shot Annotation.Shot{N}`. Each Shot contains: `Involving Characters` (with normalized bounding boxes [x1,y1,x2,y2]), `Plot/Visual Description`, `Coarse Plot`, `image_prompt`, `video_prompt`, `audio_prompt`, `Shot Type`, `Camera Movement`, `Duration` (4/5/10/15), `Subtitles`, `seedance_mode` (i2v/multimodal/t2v). Schema is in `schemas/script_breakdown.schema.json`.

### Character Consistency via @Image

Seedance 2.0's multimodal mode accepts `@Image{N}` references in prompts. The pattern is: character reference images (`character_list/{Name}/best.png`) are placed first, then the keyframe image last. Example: `@Image1 作为Elsa外观参考。@Image2 作为首帧，角色微微抬头...`. Characters without designed assets fall back to text-only description in `image_prompt`.

### SQLite Database (`data.db`)

Schema in `scripts/init_db.sql`. Six tables: `projects` (status-driven state machine), `scripts`, `storyboards`, `characters` (per-project), `assets` (image/video/audio with metadata), `generations` (audit log for all API calls with cost tracking). All DB access goes through `db_manager.py` → MCP tools.

### Environment Variables

Required in `.env` (loaded by `python-dotenv`):
- `ARK_API_KEY` / `ARK_BASE_URL` / `SEEDANCE_MODEL` — Seedance 2.0 video generation (Step 5)
- `OPENAI_API_KEY` — DALL-E 3 image generation (Steps 3b, 5)
- `VOLC_TTS_APP_ID` / `VOLC_TTS_TOKEN` — Volcano TTS (optional, for voice override)
- `SD_API_URL` — Local Stable Diffusion (optional alternative to DALL-E)

Steps 1–3a require no API keys (pure LLM reasoning + local DB).
