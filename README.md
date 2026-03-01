# AI 漫剧自动化制作流水线

基于 MovieAgent 架构的 AI 漫剧（短剧视频）自动化制作系统。将小说/剧本文本通过 6 步流水线转化为可直接用于视频生成平台的完整分镜制作方案。

## 系统架构

```
小说/剧本文本
    │
    ▼
┌─────────────────────────────────────────────┐
│  Step 1: /init-project     创建项目          │
│  Step 2: /import-script    导入剧本          │
│  Step 3a: /extract-characters 提取角色       │
│  Step 3b: /design-characters  设计角色       │
│  Step 4: /break-script     三层CoT分镜拆解   │  ◄── 核心步骤
│  Step 5: /export-guide     导出制作指南      │
└─────────────────────────────────────────────┘
    │
    ▼
分镜制作包 (image_prompt / video_prompt / audio_prompt)
    │
    ▼
手动操作: Gemini(生图) → 可灵/Seedance(生视频) → 剪映(合成)
```

**核心特点**：

- **三层 CoT 推理**：编剧层(5步) → 场景层(4步) → 镜头层(6步)，每层独立推理，结果可审计
- **角色一致性**：`<TOK>` 格式外观描述 + Seedance @Image 参考图机制，确保角色在所有镜头中视觉一致
- **10 Skills + 6 Agent Teams**：领域知识模块化，复杂步骤自动调度并行 Agent 团队协作
- **文件驱动**：所有数据通过 `projects/{id}/` 下的 JSON 文件流转，无内存状态依赖

## 快速开始

### 前置条件

- [CodeBuddy Code](https://cnb.cool/codebuddy/codebuddy-code) (CLI 工具)
- Python 3.10+
- FFmpeg (可选，用于视频合成)

### 安装

```bash
# 克隆项目
git clone <repo-url> my-ai-video-agent
cd my-ai-video-agent

# 安装 Python 依赖
pip install -r scripts/requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 初始化数据库（可选）
python scripts/db_manager.py --action init_db
```

### 环境变量

| 变量 | 用途 | 何时需要 |
|------|------|---------|
| `ARK_API_KEY` / `ARK_BASE_URL` | 火山方舟 (Seedance 视频生成) | Step 5 后手动生成 |
| `OPENAI_API_KEY` | DALL-E 图像生成 | Step 5 后手动生成 |
| `VOLC_TTS_APP_ID` / `VOLC_TTS_TOKEN` | 火山 TTS 语音合成 | 可选 |
| `SD_API_URL` | 本地 Stable Diffusion | 可选替代 DALL-E |

> Steps 1-4 为纯 LLM 推理 + 文件 I/O，**无需任何 API Key**。API Key 仅在导出后手动执行图片/视频生成时需要。

### 运行流水线

在 CodeBuddy Code 中依次执行命令：

```
/init-project          # 创建项目目录和配置
/import-script         # 导入剧本文本，生成剧情摘要
/extract-characters    # 提取角色，生成性格/外观/配音方案
/design-characters     # 设计角色视觉资产 (TOK描述 + 参考图提示)
/break-script          # 三层CoT拆解：Sub-Script → Scene → Shot
/export-guide          # 导出分镜制作指南和Prompt表
```

每一步会自动校验前置状态，状态流转为：

```
draft → imported → characters_extracted → characters_designed → script_broken → exported
```

## 项目结构

```
my-ai-video-agent/
├── .codebuddy/
│   ├── commands/          # 6 个流水线步骤定义
│   ├── rules/             # 6 条约束规则
│   │   ├── pipeline-dispatch.md    # 步骤→Skill→Team 调度
│   │   ├── cot-reasoning.md        # CoT 推理强制规则
│   │   ├── api-usage.md            # API 调用与成本控制
│   │   ├── character-consistency.md # 角色视觉一致性
│   │   ├── narrative-rhythm.md     # 叙事节奏约束
│   │   └── quality-standards.md    # 质量标准
│   └── skills/            # 10 个领域知识模块
│       ├── script-parser/     # 剧本解析 + Layer 1
│       ├── script-scene/      # 场景设计 + Layer 2
│       ├── character-design/  # 角色视觉设计
│       ├── character-acting/  # 角色表演设计
│       ├── shot-director/     # 镜头导演 + Layer 3
│       ├── shot-rhythm/       # 叙事节奏设计
│       ├── prompt-image/      # 文生图 Prompt 工程
│       ├── prompt-video/      # 图生视频 Prompt 工程
│       ├── prompt-audio/      # 音效/配音 Prompt 工程
│       └── export-render/     # 导出与质量审查
├── schemas/               # JSON Schema 定义
├── scripts/               # Python 工具脚本
│   ├── db_manager.py          # 数据库管理
│   ├── export_storyboard.py   # 分镜导出 (Markdown + CSV)
│   └── import_script.py       # 剧本导入
├── projects/              # 项目数据目录 (运行时生成)
│   └── {project_id}/
│       ├── project.json           # 项目配置
│       ├── status.json            # 状态机
│       ├── raw_script.txt         # 原始剧本
│       ├── script_synopsis.json   # 剧情摘要
│       ├── characters.json        # 角色档案
│       ├── character_list/        # 角色视觉资产
│       │   └── {CharName}/
│       │       ├── best.png       # 最佳参考图
│       │       └── best.txt       # <TOK> 描述
│       ├── script_breakdown.json  # 三层分镜数据 (核心产物)
│       └── exports/               # 导出文件
├── docs/                  # 文档
├── CODEBUDDY.md           # CodeBuddy 指令文件
└── .env.example           # 环境变量模板
```

## 核心概念

### 三层 CoT 分镜拆解

Step 4 (`/break-script`) 是系统核心，实现 MovieAgent 的三层 Chain-of-Thought 推理：

| 层级 | 输入 | 输出 | CoT 步骤 | Agent Team |
|------|------|------|---------|-----------|
| Layer 1 (编剧) | 完整剧本 | ≤20 个 Sub-Script | 5 步 | 无 |
| Layer 2 (场景) | 每个 Sub-Script | Scene 列表 | 4 步 | Team A (并行) |
| Layer 3 (镜头) | 每个 Scene | Shot 列表 + 三版 Prompt | 6 步 | Team B (多模态) |

每层使用**独立上下文**（`use_history=False`），不在 LLM 调用间累积历史，确保推理质量。

### script_breakdown.json

三层嵌套的核心数据结构：

```
Sub-Script{N}
  └── Scene Annotation
       └── Scene{N}
            └── Shot Annotation
                 └── Shot{N}
                      ├── image_prompt    (英文，文生图)
                      ├── video_prompt    (中文，图生视频)
                      ├── audio_prompt    (中文，音效配音)
                      ├── Duration        (4/5/10/15 秒)
                      ├── Shot Type       (18 种镜头类型)
                      ├── Camera Movement (20+ 种运镜)
                      └── Subtitles       (字幕对白)
```

### 角色一致性

通过三重机制保障同一角色在所有镜头中视觉一致：

1. **`<TOK>` 描述**：每个角色有固定的英文外观描述，在所有 `image_prompt` 中逐字复制
2. **参考图**：`character_list/{Name}/best.png` 作为角色视觉锚点
3. **@Image 引用**：Seedance 生成时通过 `@Image{N}` 关联角色参考图

### 镜头时长计算

Duration 通过公式强制计算，不凭感觉指定：

```
对白时间 = Σ(每句中文字数 × 0.2 + 1.0) + 句间间隔
动作时间 = 低(2s) | 中(4s) | 高(6s)
最低时长 = max(对白时间, 动作时间) + 1s
Duration = 向上对齐到 Seedance 档位 (4/5/10/15)
```

## Skills + Agent Teams 体系

### 10 Skills（领域知识模块）

| 模块 | Skill | 职责 |
|------|-------|------|
| Script | `script-parser` | 剧本解析、题材识别、Layer 1 CoT |
| | `script-scene` | Layer 2 场景设计、光影/色彩/转场 |
| Character | `character-design` | `<TOK>` 格式、Visual ID Card、服装系统 |
| | `character-acting` | 性格 MBTI、表情/肢体词汇、配音方案 |
| Shot | `shot-director` | Layer 3 CoT、18 种镜头、20+ 种运镜 |
| | `shot-rhythm` | Duration 公式、题材节奏模板、情绪曲线 |
| Prompt | `prompt-image` | 英文 image_prompt 构建、风格一致性 |
| | `prompt-video` | video_prompt + @Image 引用、动态描述 |
| | `prompt-audio` | 环境音 + 动作音效 + 对白表演 + BGM |
| Export | `export-render` | 三审质量关卡、成本估算、制作指南 |

### 6 Agent Teams（并行协作团队）

| Team | 模式 | 触发步骤 | 角色配置 |
|------|------|---------|---------|
| Team A | 并行 | Step 4b (Layer 2) | coordinator + 3 planners + reviewer |
| Team B | 多模态 | Step 4c (Layer 3) | coordinator + designer + 3 prompters + rhythm + reviewer |
| Team C | 专精 | Step 3a | casting-director + personality + expression + voice |
| Team D | 审核 | Step 4c | art-director + consistency-checker |
| Team E | 审核 | Step 4c | motion-director + reference-validator |
| Team F | 审核 | Step 5 | post-supervisor + 3 auditors |

## 导出产物

Step 5 (`/export-guide`) 生成的文件位于 `projects/{id}/exports/`：

| 文件 | 格式 | 用途 |
|------|------|------|
| `storyboard_guide.md` | Markdown | 人类可读的分镜制作指南，含每个镜头的 Prompt 和参数 |
| `storyboard_prompts.csv` | CSV | 扁平化 Prompt 表格，便于批量操作 |
| `cost_estimate.md` | Markdown | 成本估算（图片 + 视频 + 音频） |

### 导出后的手动操作

```
1. 生成角色参考图 → 复制 image_prompt 到 Gemini/DALL-E → 保存为 best.png
2. 生成分镜关键帧 → 复制 image_prompt 到 Gemini → 保存为 {shot_id}.png
3. 生成视频片段 → 在可灵/Seedance 中上传关键帧 + 角色参考图 → 粘贴 video_prompt
4. 最终合成 → 在剪映中按顺序排列视频 → 添加字幕/转场/BGM（参考 audio_prompt）
```

## 成本估算

以 120 秒标准漫剧（~24 个镜头）为例：

| 项目 | 单价 | 数量 | 小计 |
|------|------|------|------|
| 角色参考图 (DALL-E) | ~0.28 元 | ~15 张 | ~4.2 元 |
| 分镜关键帧 (DALL-E) | ~0.28 元 | 24 张 | ~6.7 元 |
| 视频生成 (Seedance 5s) | ~3.67 元 | 16 个 | ~58.7 元 |
| 视频生成 (Seedance 10s) | ~7 元 | 8 个 | ~56 元 |
| **合计** | | | **~126 元 (~$17)** |

> Steps 1-4 纯 LLM 推理，成本为 CodeBuddy Code 的 API 调用费用，不涉及额外付费 API。

## 技术栈

- **编排引擎**: CodeBuddy Code (Skills + Rules + Agent Teams)
- **数据格式**: JSON (文件驱动，无需外部数据库)
- **辅助脚本**: Python 3.10+ (导出、数据库管理)
- **图像生成**: DALL-E 3 / Gemini / Stable Diffusion (手动)
- **视频生成**: 可灵 / Seedance 2.0 (手动)
- **音频合成**: 火山 TTS / 剪映内置 (手动)
- **视频合成**: 剪映 / FFmpeg (手动)
