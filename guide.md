# AI 漫剧流水线 — 快速启动指南

## 第一步：环境准备

### 1.1 安装 Python 依赖

```bash
cd d:/codespace/my-ai-video-agent
pip install -r scripts/requirements.txt
```

### 1.2 安装 FFmpeg

视频合成脚本依赖 FFmpeg（Step 5 以及后续合成需要）：

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
| `OPENAI_API_KEY` | DALL-E 3 图像生成 | Step 4-5 |
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

## 第二步：5 步制作流程

环境准备好后，通过 5 个命令逐步推进漫剧制作。**每步完成后会展示结果等你确认，再进入下一步。**

### Step 1: `/init-project` — 初始化项目

对 AI 说：
```
/init-project
项目名：深夜便利店的奇妙邂逅
风格：manga
时长：120秒
```

- AI 创建项目，返回 `project_id`
- 自动生成目录结构

### Step 2: `/confirm-story` — 确认漫剧内容

对 AI 说：
```
/confirm-story
project_id: {上一步返回的 ID}
主题：一个加班到深夜的程序员，走进便利店，遇到了温暖的店员
```

- AI 生成故事梗概（概要 + 角色 + 场景规划）
- **你确认或修改后，AI 锁定方向**
- 产出：`story_brief.json`

### Step 3: `/write-script` — 编剧 + 分镜

对 AI 说：
```
/write-script
project_id: {project_id}
```

- AI 自动基于确认的大纲创作完整剧本和分镜
- 产出：`script.json` + `storyboard.json`
- 展示：场景列表、镜头数、总时长

### Step 4: `/design-characters` — 角色设计

对 AI 说：
```
/design-characters
project_id: {project_id}
```

- AI 设计角色外观并生成参考图
- 产出：`characters.json` + 参考图
- 展示：角色列表和参考图路径

> **需要 OPENAI_API_KEY**（或本地 SD）生成参考图

### Step 5: `/generate-video` — 生成视频片段

对 AI 说：
```
/generate-video
project_id: {project_id}
```

- AI 为每个镜头生成分镜图 + 视频片段（Seedance 2.0 音视频联合生成）
- 产出：分镜图 + 视频 + `video_manifest.json`
- 这是最耗时的步骤（每镜头约 2-5 分钟）

> **需要 ARK_API_KEY + OPENAI_API_KEY**

---

## 第三步：查看成果

项目所有素材位于 `projects/{project_id}/` 目录：

```
projects/{project_id}/
├── story_brief.json       # Step 2: 确认的故事大纲
├── script.json            # Step 3: 完整剧本
├── storyboard.json        # Step 3: 分镜表
├── characters.json        # Step 4: 角色数据
├── images/
│   ├── characters/        # Step 4: 角色参考图
│   └── shots/             # Step 5: 分镜图
├── videos/                # Step 5: 视频片段（带音轨）
└── video_manifest.json    # Step 5: 视频清单
```

查看项目状态：
```bash
python scripts/db_manager.py --action get_project --data '{"project_id": "你的项目ID"}'
```

## 状态流转

```
draft → confirmed → scripted → designed → generating → generated → [composing → completed]
  ↑        ↑           ↑          ↑            ↑            ↑
Step 1   Step 2     Step 3     Step 4       Step 5      Step 5完成
```

---

## 成本预估

| API | 单次成本 | 典型用量（10 镜头） | 小计 |
|-----|---------|---------------------|------|
| Seedance 2.0（5s） | ≈ ¥3.67 | 10-15 次 | ≈ ¥37-55 |
| DALL-E 3（1024x1024） | ≈ $0.04 | 12-17 张（含角色参考图） | ≈ $0.5-0.7 |
| 火山 TTS | 极低 | 0-5 句 | ≈ ¥0-1 |

**一部 10 镜头漫剧总成本约 ¥40-60**。

---

## 常见问题

### Q: 可以只跑到某一步就停下吗？
可以。每步独立执行，你可以在任何步骤停下。比如只跑到 Step 3 看剧本效果。

### Q: 角色在不同镜头间长得不一样？
Step 5 使用 Seedance 的 **multimodal 模式 + @引用语法**，传入 Step 4 的角色参考图保持一致。

### Q: 某个镜头想重新生成？
直接告诉 AI，例如：`重新生成项目 xxx 的第 3 个镜头，角色表情需要更夸张`。

### Q: 没有 API Key 能跑多远？
- Step 1-3 不需要任何 API Key（纯 AI 创作 + 本地数据库）
- Step 4 需要 OPENAI_API_KEY（或本地 SD）
- Step 5 需要 ARK_API_KEY + OPENAI_API_KEY
