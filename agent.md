# AI 漫剧自动化生产流水线

基于 Seedance 2.0 音视频联合生成的 AI 漫剧（Manga Drama）全链路自动化生产系统。

## 用户工作流（5 步流程）

```
Step 1: /init-project     → 初始化项目（创建项目、配置参数）
Step 2: /confirm-story     → 确认漫剧内容（用户提供主题/大纲，AI 生成故事梗概，用户确认）
Step 3: /write-script      → 编剧 + 分镜（基于确认的内容，生成 script.json + storyboard.json）
Step 4: /design-characters → 角色设计（基于剧本，生成 characters.json + 角色参考图）
Step 5: /generate-video    → 生成视频片段（基于分镜+编剧+角色，文生图+图生视频）
```

**核心设计**：每一步都需要用户确认后再进入下一步，确保创作方向可控。

## 流水线详细架构

### Step 1: 初始化项目 (`/init-project`)

- **执行者**：Director
- **输入**：项目名称、风格、时长等配置
- **操作**：
  1. 调用 `db_manager.py --action create_project` 创建项目
  2. 自动生成 `projects/{project_id}/` 目录结构
  3. 返回 project_id
- **产出**：项目目录 + 数据库记录
- **状态**：`draft`

### Step 2: 确认漫剧内容 (`/confirm-story`)

- **执行者**：Director + 用户协作
- **输入**：project_id + 用户提供的主题/大纲
- **操作**：
  1. AI 根据主题生成故事梗概（3-5 句话概括整个故事）
  2. 列出主要角色清单（名称 + 一句话描述）
  3. 估算场景数量和时长
  4. **等待用户确认或修改**
- **产出**：`projects/{project_id}/story_brief.json`（确认后的故事大纲）
- **状态**：`draft` → `confirmed`

### Step 3: 编剧 + 分镜 (`/write-script`)

- **执行者**：Screenwriter Agent
- **输入**：project_id（读取 story_brief.json）
- **操作**：
  1. 基于确认的故事大纲创作完整剧本
  2. 设计分镜表（镜头类型、运镜、Prompt、audio_prompt）
  3. 将数据写入数据库
- **产出**：
  - `projects/{project_id}/script.json` — 完整剧本
  - `projects/{project_id}/storyboard.json` — 分镜表
- **状态**：`confirmed` → `scripted`

### Step 4: 角色设计 (`/design-characters`)

- **执行者**：Visual-Artist Agent
- **输入**：project_id（读取 script.json）
- **操作**：
  1. 从剧本中提取角色信息
  2. 设计每个角色的外观描述、prompt_template
  3. 生成角色参考图（调用 image_generate.py）
  4. 将参考图路径写入角色数据
- **产出**：
  - `projects/{project_id}/characters.json` — 角色数据
  - `projects/{project_id}/images/characters/` — 角色参考图
- **状态**：`scripted` → `designed`

### Step 5: 生成视频片段 (`/generate-video`)

- **执行者**：Visual-Artist Agent
- **输入**：project_id（读取 storyboard.json + characters.json）
- **操作**：
  1. 为每个镜头生成分镜图（文生图）
  2. 基于分镜图 + 角色参考图生成视频片段（Seedance 2.0）
  3. 利用 @引用语法保持角色一致性
  4. 音视频联合生成（视频自带音轨）
  5. 产出视频清单（含音频质量标记）
- **产出**：
  - `projects/{project_id}/images/` — 分镜图
  - `projects/{project_id}/videos/` — 视频片段（带音轨）
  - `projects/{project_id}/video_manifest.json` — 视频清单
- **状态**：`designed` → `generating` → `generated`

### 后续步骤（可选）

| 步骤 | 命令 | 说明 |
|------|------|------|
| 音频修补 | 手动触发 | 仅当 video_manifest.json 中存在 needs_tts_override 时 |
| 最终合成 | 手动触发 | 将所有视频片段拼接为成片 + 字幕 |

## Agent 协作与数据路由

Agent 之间不直接通信，通过 `projects/{project_id}/` 目录下的标准 JSON 文件交换数据：

```
projects/{project_id}/
├── story_brief.json       ← Step 2: Director 输出（用户确认的故事大纲）
├── script.json            ← Step 3: Screenwriter 输出
├── storyboard.json        ← Step 3: Screenwriter 输出
├── characters.json        ← Step 4: Visual-Artist 输出
├── images/
│   ├── characters/        ← Step 4: 角色参考图
│   └── shots/             ← Step 5: 分镜图
├── videos/                ← Step 5: 视频片段（带音轨）
├── video_manifest.json    ← Step 5: 视频清单
├── audio/                 ← 可选: Sound-Designer 输出
└── compose_config.json    ← 可选: Editor 输出
```

## 5 个 Agent

| Agent | 职责 | 关联步骤 |
|-------|------|---------|
| **Director** | 全局编排调度、用户交互、质量门禁 | Step 1-2 |
| **Screenwriter** | 剧本创作、分镜设计、audio_prompt | Step 3 |
| **Visual-Artist** | 角色设计、文生图、Seedance 视频生成 | Step 4-5 |
| **Sound-Designer** | 审查音频质量、TTS 替换（可选） | 后续 |
| **Editor** | 视频拼接、字幕烧录、成片输出（可选） | 后续 |

## 5 个 Skill

| Skill | 用途 |
|-------|------|
| **manga-script** | 漫剧剧本创作方法论：三幕式结构、对白规范 |
| **storyboard-design** | 分镜设计：镜头类型、运镜、三种 Prompt |
| **character-consistency** | 角色一致性：prompt_template、@引用语法 |
| **seedance-video** | Seedance 2.0：三种模式、Prompt 优化、音频 |
| **voice-synthesis** | TTS：音色、情绪-语音映射 |

## 4 条 Rules

| Rule | 核心约束 |
|------|---------|
| **api-usage** | API Key 环境变量管理；Seedance 日上限 50 次；指数退避重试 |
| **character-consistency** | @引用为首要手段；禁止省略 prompt_template |
| **narrative-rhythm** | 镜头时长对齐 Seedance 4/5/10/15s；转场规则 |
| **quality-standards** | 视频≥1080p；分镜图≥1024x1024；Prompt 英文 |

## 状态流转

```
draft → confirmed → scripted → designed → generating → generated → [composing → completed]
```

## Scripts（Python 执行层）

| 脚本 | 功能 |
|------|------|
| `db_manager.py` | SQLite CRUD（项目/剧本/分镜/角色/资产/日志） |
| `image_generate.py` | DALL-E 3 / SD WebUI 文生图 |
| `seedance_generate.py` | Seedance 2.0 音视频联合生成 |
| `tts_generate.py` | 火山引擎 / Azure TTS 语音合成 |
| `video_compose.py` | FFmpeg 视频合成 |

## 环境配置

| 变量 | 用途 | 必要性 |
|------|------|--------|
| `ARK_API_KEY` | Seedance 2.0 | 必须 |
| `OPENAI_API_KEY` | DALL-E 3 | 使用 DALL-E 时必须 |
| `VOLC_TTS_APP_ID` / `VOLC_TTS_TOKEN` | 火山 TTS | 仅 TTS Override 时需要 |
| `SD_API_URL` / `SD_API_KEY` | Stable Diffusion | 可选替代 DALL-E |

## 关键设计决策

1. **用户确认驱动**：每步完成后等待用户确认，不自动推进到下一步
2. **Seedance 2.0 音视频联合生成**：视频自带音轨，TTS 仅作 Override
3. **@引用语法保持角色一致性**：传入参考图 + `@Image1 作为{角色名}外观`
4. **JSON 文件数据路由**：Agent 间零耦合，通过文件系统交换
5. **SQLite 全记录**：所有 API 调用写入 generations 表
