# AI 漫剧自动化生产流水线

基于 MovieAgent 核心架构（分层 CoT 拆解）+ Seedance 2.0 音视频联合生成的 AI 漫剧全链路自动化生产系统。

## 用户工作流（7 步流程）

```
Step 1: /init-project          → 初始化项目（创建项目、配置参数）
Step 2: /import-script         → 导入剧本（接收 .txt 小说/剧本，提取摘要和角色列表）
Step 3a: /extract-characters   → 提取角色（从剧本自动提取所有角色信息，写入 characters.json）
Step 3b: /design-characters    → 角色设计（按需逐个设计角色，生成 character_list/ 资产库）
Step 4: /break-script          → 分层拆解（MovieAgent 式三层 CoT：Sub-Scripts → Scenes → Shots）
Step 5: /generate-video        → 生成视频（基于 Shot 分镜 + 角色资产库，逐镜头生成）
Step 6: /compose-final         → 合成成片（视频拼接、字幕烧录、BGM 混合）
```

**核心设计**：
- 每步完成后等待用户确认，确保创作方向可控
- MovieAgent 分层 CoT 强制推理，每层输出 Internal Chain-of-Thought
- 角色按需设计，未出场的可以先不生成，节省 API 成本

## 流水线详细架构

### Step 1: 初始化项目 (`/init-project`)

- **执行者**：Director
- **输入**：项目名称、风格、时长等配置
- **操作**：调用 `db_manager.py --action create_project` 创建项目 + 目录结构
- **产出**：项目目录 `projects/{project_id}/`（含 character_list/、final/ 等子目录）
- **状态**：`draft`

### Step 2: 导入剧本 (`/import-script`)

- **执行者**：Director
- **输入**：project_id + .txt 剧本/小说文件路径
- **操作**：
  1. 调用 `import_script.py --action import` 读取文件（自动检测编码 UTF-8/GBK/GB2312）
  2. 复制为 `raw_script.txt`，统一 UTF-8 编码
  3. 基于内容提取故事摘要（MovieScript）、角色列表（Character）、关系图（Relationships）
- **产出**：`raw_script.txt` + `script_synopsis.json`
- **状态**：`draft` → `imported`

### Step 3a: 提取角色 (`/extract-characters`)

- **执行者**：Director（直接执行，不调子 Agent）
- **输入**：project_id（读取 script_synopsis.json + raw_script.txt）
- **操作**：纯文本分析，提取所有角色的名称、描述、关系、外观特征
- **产出**：`characters.json`（角色清单，不生成图片）
- **状态**：`imported` → `characters_extracted`

### Step 3b: 角色设计 (`/design-characters`)

- **执行者**：Character Designer Agent
- **三种调用方式**：
  - `/design-characters` — 列出所有角色及设计状态
  - `/design-characters 小王` — 设计指定角色
  - `/design-characters all` — 批量设计所有未设计角色
- **操作**：为每个角色生成 MovieAgent 格式的 `character_list/{角色名}/` 资产目录
- **资产目录结构**：
  ```
  character_list/{CharName}/
  ├── best.png       # 最佳参考图（正面半身）
  ├── best.txt       # <TOK> 外观描述
  ├── photo_1.png    # 多角度参考图
  ├── photo_1.txt    # 对应描述
  └── audio.wav      # 声音参考（可选）
  ```
- **状态**：`characters_extracted` → `characters_designing`

### Step 4: 分层拆解 (`/break-script`)

- **执行者**：三步串行子 Agent 调用
  1. **Screenwriter Agent**（Step 4a）：剧本 → Sub-Scripts（≤20个章节/幕）
  2. **Scene Planner Agent**（Step 4b）：每个 Sub-Script → Scenes
  3. **Shot Creator Agent**（Step 4c）：每个 Scene → Shots（含双版本描述、三种 Prompt）
- **每步 CoT**：强制输出 Internal Chain-of-Thought，不允许跳过推理
- **可选督导**：Script Supervisor Agent 在每步后审查质量
- **产出**：`script_breakdown.json`（三层嵌套：Sub-Script → Scene → Shot）
- **状态**：→ `script_broken`

### Step 5: 生成视频 (`/generate-video`)

- **执行者**：Visual Artist Agent
- **输入**：`script_breakdown.json` + `character_list/` 资产库
- **操作**：遍历 Sub-Script → Scene → Shot，逐镜头生成：
  1. 关键帧图片（DALL-E 3，使用 image_prompt）
  2. 视频片段（Seedance 2.0，使用 video_prompt + @Image 角色参考）
- **文件命名**：`Sub-Script_1|Scene_1|Shot_1.mp4`
- **产出**：`images/shots/` + `videos/` + `video_manifest.json`
- **状态**：`script_broken` → `generating` → `generated`

### Step 6: 合成成片 (`/compose-final`)

- **执行者**：Editor Agent
- **操作**：
  1. 从 script_breakdown.json 提取有序 Shot 列表
  2. 按转场规则拼接（同场景=切、跨场景=淡入淡出、跨幕=黑屏）
  3. 烧录字幕、混合 BGM
- **产出**：`final/final_video.mp4`
- **状态**：`generated` → `composing` → `completed`

## Agent 协作架构

Agent 之间不直接通信，通过 `projects/{project_id}/` 目录下的 JSON 文件交换数据：

```
projects/{project_id}/
├── raw_script.txt           ← Step 2: 导入的原始剧本
├── script_synopsis.json     ← Step 2: 摘要 + 角色列表 + 关系
├── characters.json          ← Step 3a: 角色清单（含外观描述 + 设计状态）
├── character_list/          ← Step 3b: MovieAgent 格式角色资产库
│   └── {CharName}/
│       ├── best.png + best.txt
│       ├── photo_N.png + photo_N.txt
│       └── audio.wav
├── script_breakdown.json    ← Step 4: 三层嵌套分镜（核心产物）
├── images/shots/            ← Step 5: 关键帧图片
├── videos/                  ← Step 5: 视频片段
├── video_manifest.json      ← Step 5: 视频清单
├── audio/                   ← 可选: TTS Override
└── final/                   ← Step 6: 最终成片
```

## 8 个 Agent

| Agent | 职责 | 关联步骤 |
|-------|------|---------|
| **Director** | 全局编排调度、用户交互、命令路由 | 全流程 |
| **Screenwriter** | 剧本拆解（Script → Sub-Scripts），CoT 推理 | Step 4a |
| **Scene Planner** | 场景规划（Sub-Script → Scenes），CoT 推理 | Step 4b |
| **Shot Creator** | 镜头创建（Scene → Shots），双版本描述 + 三种 Prompt | Step 4c |
| **Character Designer** | 单角色精细设计，生成 character_list 资产 | Step 3b |
| **Visual Artist** | 文生图 + Seedance 视频生成 | Step 5 |
| **Editor** | 视频拼接、字幕烧录、成片输出 | Step 6 |
| **Script Supervisor** | 质量督导，审查各步骤输出 | Step 4 后 |
| **Sound Designer** | TTS Override（可选）| 按需 |

## 6 个 Skill

| Skill | 用途 |
|-------|------|
| **script-breakdown** | 核心：MovieAgent 三步分层 CoT Prompt 模板（screenwriterCoT / ScenePlanningCoT / ShotPlotCreateCoT）|
| **manga-script** | 剧本导入：小说解析、摘要提取、角色识别策略 |
| **character-consistency** | 角色一致性：character_list 目录结构、`<TOK>` 描述、@引用 |
| **storyboard-design** | 分镜设计：双版本描述、三种 Prompt 生成规范 |
| **seedance-video** | Seedance 2.0：三种模式、Prompt 优化、音视频联合 |
| **voice-synthesis** | TTS：音色选择、情绪-语音映射 |

## 5 条 Rules

| Rule | 核心约束 |
|------|---------|
| **cot-reasoning** | 强制 CoT 推理：三层必填字段、禁止跳过推理、独立上下文 |
| **api-usage** | API Key 环境变量管理；Seedance 日上限 50 次；指数退避重试 |
| **character-consistency** | character_list 目录校验；best.png 必须存在；`<TOK>` 格式；image_prompt 禁含角色名 |
| **narrative-rhythm** | 镜头时长对齐 Seedance 4/5/10/15s；转场规则 |
| **quality-standards** | CoT 完整性检查；三层嵌套 JSON 校验；三版本 Prompt 规范 |

## 状态流转

```
draft → imported → characters_extracted → characters_designing → script_broken → generating → generated → composing → completed
  ↑        ↑              ↑                      ↑                    ↑             ↑            ↑           ↑           ↑
Step 1   Step 2        Step 3a              Step 3b               Step 4        Step 5      Step 5完成   Step 6     Step 6完成
```

## Scripts（Python 执行层）

| 脚本 | 功能 |
|------|------|
| `import_script.py` | 剧本导入（编码检测、文件复制、文本统计）|
| `db_manager.py` | SQLite CRUD（项目/剧本/分镜/角色/资产/日志）|
| `image_generate.py` | DALL-E 3 / SD WebUI 文生图 |
| `seedance_generate.py` | Seedance 2.0 音视频联合生成 |
| `tts_generate.py` | 火山引擎 / Azure TTS 语音合成 |
| `video_compose.py` | FFmpeg 视频合成 |

## 环境配置

| 变量 | 用途 | 必要性 |
|------|------|--------|
| `ARK_API_KEY` | Seedance 2.0 | Step 5 必须 |
| `OPENAI_API_KEY` | DALL-E 3 | Step 3b/5 必须 |
| `VOLC_TTS_APP_ID` / `VOLC_TTS_TOKEN` | 火山 TTS | 仅 TTS Override 时需要 |
| `SD_API_URL` / `SD_API_KEY` | Stable Diffusion | 可选替代 DALL-E |

## 关键设计决策

1. **MovieAgent 分层 CoT**：三层独立 Agent 调用，每次 `use_history=False`，避免长上下文污染
2. **角色按需设计**：extract（纯文本）→ design（按需逐个生成），节省 API 成本
3. **三层嵌套 JSON**：`script_breakdown.json` 替代扁平 `script.json + storyboard.json`，数据流更清晰
4. **双版本描述**：`Coarse Plot`（≤20词，无人名，给图像生成）+ `Plot/Visual Description`（≥30词，给视频生成）
5. **文件名即序列**：`Sub-Script_1|Scene_1|Shot_1.mp4` 确保正确排序
6. **JSON 文件数据路由**：Agent 间零耦合，通过文件系统交换
7. **SQLite 全记录**：所有 API 调用写入 generations 表
