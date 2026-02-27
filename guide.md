# AI 漫剧流水线 — 快速启动指南

## 第一步：环境准备

### 1.1 安装 Python 依赖

```bash
cd d:/codespace/my-ai-video-agent
pip install -r scripts/requirements.txt
```

### 1.2 安装 FFmpeg

视频合成脚本依赖 FFmpeg（Step 6 需要）：

```bash
ffmpeg -version
```

Windows 安装：从 https://www.gyan.dev/ffmpeg/builds/ 下载 release build，解压后将 `bin/` 加入系统 PATH。

### 1.3 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 填入 API Key：

| 变量 | 用途 | 何时需要 |
|------|------|---------|
| `ARK_API_KEY` | Seedance 2.0 视频生成 | Step 5 |
| `OPENAI_API_KEY` | DALL-E 3 图像生成 | Step 3b/5 |
| `VOLC_TTS_APP_ID` / `VOLC_TTS_TOKEN` | TTS 配音 | 可选 |

### 1.4 初始化数据库

```bash
python scripts/db_manager.py --action init_db
```

### 1.5 验证环境

```bash
python scripts/db_manager.py --action list_projects
ffmpeg -version
```

---

## 第二步：7 步制作流程

环境准备好后，通过 7 个命令逐步推进漫剧制作。**每步完成后会展示结果等你确认，再进入下一步。**

### Step 1: `/init-project` — 初始化项目

对 AI 说：
```
/init-project
项目名：深夜便利店的奇妙邂逅
风格：manga
时长：120秒
```

- AI 创建项目，返回 `project_id`
- 自动生成目录结构（含 `character_list/`、`final/`）

### Step 2: `/import-script` — 导入剧本

对 AI 说：
```
/import-script
project_id: {上一步返回的 ID}
剧本文件: D:/novels/my_story.txt
```

- AI 读取 .txt 文件（支持 UTF-8/GBK/GB2312 编码）
- 复制为 `raw_script.txt`
- 自动提取故事摘要、角色列表、角色关系
- 产出：`raw_script.txt` + `script_synopsis.json`

### Step 3a: `/extract-characters` — 提取角色

对 AI 说：
```
/extract-characters
project_id: {project_id}
```

- AI 从剧本中提取所有角色的详细信息（名称、外观、关系）
- 产出：`characters.json`（纯文本分析，不消耗图像 API）
- 展示：角色列表和外观描述

### Step 3b: `/design-characters` — 角色设计

三种调用方式：

```
/design-characters                    # 列出所有角色及设计状态
/design-characters 小王               # 设计指定角色
/design-characters all                # 批量设计所有未设计角色
```

- 按需逐个设计，每个角色生成 `character_list/{角色名}/` 资产目录
- 包含：最佳参考图（best.png）+ 外观描述（best.txt）+ 多角度图 + 声音参考
- 不满意可重新生成

> **需要 OPENAI_API_KEY**（或本地 SD）生成参考图

### Step 4: `/break-script` — 分层拆解

对 AI 说：
```
/break-script
project_id: {project_id}
```

- MovieAgent 核心步骤：三层 CoT 分层拆解
  1. **编剧**：剧本 → Sub-Scripts（≤20 个章节）
  2. **场景规划**：每个 Sub-Script → Scenes
  3. **镜头创建**：每个 Scene → Shots（含 Prompt、字幕、运镜）
- 每层强制 Chain-of-Thought 推理
- 产出：`script_breakdown.json`（三层嵌套核心数据）

### Step 5: `/generate-video` — 生成视频

对 AI 说：
```
/generate-video
project_id: {project_id}
```

- 遍历 Sub-Script → Scene → Shot，逐镜头生成：
  - 关键帧图片（DALL-E 3）
  - 视频片段（Seedance 2.0 音视频联合生成）
- 使用 character_list 资产保持角色一致性
- 这是最耗时的步骤（每镜头约 2-5 分钟）

> **需要 ARK_API_KEY + OPENAI_API_KEY**

### Step 6: `/compose-final` — 合成成片

对 AI 说：
```
/compose-final
project_id: {project_id}
```

- 视频拼接 + 字幕烧录 + BGM 混合
- 产出：`final/final_video.mp4`

---

## 第三步：查看成果

项目所有素材位于 `projects/{project_id}/` 目录：

```
projects/{project_id}/
├── raw_script.txt           # Step 2: 导入的原始剧本
├── script_synopsis.json     # Step 2: 摘要 + 角色列表 + 关系
├── characters.json          # Step 3a: 角色清单（含外观描述）
├── character_list/          # Step 3b: 角色资产库
│   └── {CharName}/
│       ├── best.png + best.txt
│       ├── photo_N.png + photo_N.txt
│       └── audio.wav
├── script_breakdown.json    # Step 4: 三层嵌套分镜（核心产物）
├── images/shots/            # Step 5: 关键帧图片
├── videos/                  # Step 5: 视频片段
├── video_manifest.json      # Step 5: 视频清单
├── audio/                   # 可选: TTS Override
└── final/                   # Step 6: 最终成片
```

查看项目状态：
```bash
python scripts/db_manager.py --action get_project --data '{"project_id": "你的项目ID"}'
```

## 状态流转

```
draft → imported → characters_extracted → characters_designing → script_broken → generating → generated → composing → completed
  ↑        ↑              ↑                      ↑                    ↑             ↑            ↑           ↑           ↑
Step 1   Step 2        Step 3a              Step 3b               Step 4        Step 5      Step 5完成   Step 6     Step 6完成
```

---

## 成本预估

| API | 单次成本 | 典型用量（30 镜头） | 小计 |
|-----|---------|---------------------|------|
| Seedance 2.0（5s）| ≈ ¥3.67 | 30 次 | ≈ ¥110 |
| DALL-E 3（1024x1024）| ≈ $0.04 | 35-50 张（角色参考图+关键帧）| ≈ $1.5-2.0 |
| 火山 TTS | 极低 | 0-10 句 | ≈ ¥0-2 |

**一部 30 镜头漫剧总成本约 ¥120-130**。

---

## 常见问题

### Q: 可以只跑到某一步就停下吗？
可以。每步独立执行，你可以在任何步骤停下。比如只跑到 Step 4 看分镜效果。

### Q: 没有 API Key 能跑多远？
- Step 1-3a 不需要任何 API Key（纯 AI 创作 + 本地数据库）
- Step 3b 需要 OPENAI_API_KEY（或本地 SD）
- Step 5 需要 ARK_API_KEY + OPENAI_API_KEY

### Q: 角色在不同镜头间长得不一样？
Step 5 使用 Seedance 的 **multimodal 模式 + @引用语法**，传入 Step 3b 的角色参考图保持一致。

### Q: 角色设计不满意怎么办？
重新执行 `/design-characters 小王` 即可重新生成该角色的资产，不影响其他角色。

### Q: 某个镜头想重新生成？
直接告诉 AI，例如：`重新生成项目 xxx 的第 3 个镜头，角色表情需要更夸张`。

### Q: 支持什么格式的剧本？
目前支持 `.txt` 格式，自动检测 UTF-8、GBK、GB2312 等编码。建议使用 UTF-8 编码。

### Q: 长篇小说（>5万字）可以导入吗？
可以。系统会完整保存原文，LLM 提取摘要时会对超长文本分段处理。
