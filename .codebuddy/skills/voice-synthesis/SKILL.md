---
name: voice-synthesis
description: 语音合成技术指南。当需要为漫剧角色生成 TTS 配音（Seedance 原生音频不佳时的 Override）、控制情感语音、实现多角色配音时，应使用此 Skill。
---

# 语音合成

提供 TTS 配音的技术方案，用于 Seedance 2.0 原生音频不满足要求时的替换。

## 适用场景

Seedance 2.0 原生音轨包含环境音效、BGM 和角色配音。**独立 TTS 仅在以下情况使用**：
1. 对白发音不清晰
2. 需要精确控制某句台词的语气和节奏
3. 角色音色与设定严重不符
4. 需要特定方言或口音
5. 长段旁白需要专业播音腔

## TTS 引擎选型

| 引擎 | 优势 | 成本 | 推荐场景 |
|------|------|------|----------|
| 火山引擎 TTS | 中文语音质量高，音色丰富 | ~0.01 元/千字 | 首选，中文漫剧 TTS Override |
| Azure TTS | 多语言、SSML 控制精细 | ~0.1 元/千字 | 多语言、精细控制 |
| ElevenLabs | 音色克隆、情感表现力强 | 较高 | 英文或特殊音色 |

## 调用方式

通过 MCP tool `speech_generate`（`manga-agent` server）调用：

```
mcp: speech_generate(
     text="我决定辞职了。",
     voice="young_male",
     output_dir="projects/{project_id}/audio",
     engine="volc", speed=1.0, emotion="determined")
```

### 视频音轨替换
生成 TTS 后，用 `video_compose` 替换原视频音轨：
```
mcp: video_compose(config_json='{"mode": "replace_audio", "video_path": "videos/s1.mp4", "audio_path": "audio/s1_tts.mp3", "output_path": "videos/s1_override.mp4"}')
```

### 日志记录
```
mcp: generation_log(project_id="...", stage="tts", status="success")
```

## 角色音色映射

每个角色在 `characters.json` 中定义 `voice` 字段：

```json
{
  "voice": {
    "voice_type": "young_male",
    "speed": 1.0,
    "emotion_default": "neutral"
  }
}
```

### 预定义音色

| voice_type | 描述 | 适用角色 |
|-----------|------|----------|
| narrator | 男性旁白 | 叙述者 |
| young_male | 年轻男性 | 男主角（18-30） |
| young_female | 年轻女性 | 女主角（18-30） |
| mature_male | 成熟男性 | 长辈、Boss |
| mature_female | 成熟女性 | 女性长辈 |
| child | 儿童 | 小孩角色 |

## 情感控制

### 情绪-语音参数映射

| 情绪 | 语速调整 | 音量调整 | 语调 |
|------|---------|---------|------|
| neutral | 1.0x | 正常 | 平稳 |
| happy | 1.1x | 稍高 | 上扬 |
| sad | 0.85x | 稍低 | 低沉 |
| angry | 1.15x | 高 | 强烈起伏 |
| surprised | 1.2x | 高 | 急促上扬 |
| fearful | 1.1x | 低 | 颤抖 |
| determined | 1.0x | 稍高 | 沉稳有力 |

### 对白类型处理

| 类型 | 处理方式 |
|------|----------|
| 角色对话 | 使用角色专属音色 + 情绪参数 |
| 内心独白 | 使用角色音色 + 降速 20% + 轻声 |
| 旁白叙述 | 使用 narrator 音色 + 均匀语速 |
| 呐喊/吼叫 | 高音量 + 快速 |

## TTS Override 工作流程

1. 读取 `projects/{project_id}/video_manifest.json`
2. 筛选 `needs_tts_override: true` 的镜头
3. 读取 `projects/{project_id}/script.json` 获取对应对白
4. 匹配 `characters.json` 中的音色设置
5. 逐条生成 TTS 音频
6. 使用 FFmpeg 替换对应视频的音轨
7. 输出到 `projects/{project_id}/audio/`

## 输出规范

- 音频格式：MP3（默认）或 WAV
- 采样率：16kHz 以上
- 文件命名：`{scene_id}_{dialogue_index}_{character_id}.mp3`
- 生成清单文件 `projects/{project_id}/audio/manifest.json`

## 成本与限制

遵循 `.codebuddy/rules/api-usage.md` 中的成本控制策略。TTS 仅作为 Override 手段使用，整体调用量大幅减少。
