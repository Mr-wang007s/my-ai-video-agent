---
name: storyboard-design
description: 漫剧分镜设计与镜头语言指南。当需要将剧本场景拆解为具体镜头、设计运镜方式、生成文生图 Prompt 和音效 Prompt 时，应使用此 Skill。
---

# 分镜设计

提供从剧本到分镜的转化方法论，包括镜头语言、构图法则、运镜设计、文生图 Prompt 生成和**音效 Prompt 设计**（适配 Seedance 2.0 音视频联合生成）。

## 分镜设计流程

### 1. 剧本分析

读取 `projects/{project_id}/script.json`，对每个场景进行拆解：
- 识别关键画面节点
- 确定镜头数量（每场景 2-5 个镜头）
- 标注需要突出表现的内容（角色情绪、动作、环境）
- **标注每个镜头的音频需求**（对白、音效、BGM）

### 2. 镜头类型选择

| 类型 | 英文 | 用途 | 使用场景 |
|------|------|------|----------|
| 远景 | wide | 展示环境/氛围 | 场景开头、空间关系 |
| 中景 | medium | 展示人物互动 | 对话、日常动作 |
| 近景 | close-up | 突出表情/细节 | 情感爆发、关键道具 |
| 大特写 | extreme-close-up | 极致细节 | 眼神、嘴唇、物品 |
| 过肩 | over-shoulder | 对话视角 | 两人对话 |
| 主观 | pov | 代入感 | 角色视角 |
| 俯拍 | bird-eye | 全局/压迫感 | 群像、孤独感 |
| 仰拍 | low-angle | 力量/威严 | 英雄、反派 |

### 3. 运镜设计

| 运镜 | 英文 | 效果 | 适用场景 |
|------|------|------|----------|
| 静止 | static | 稳定/沉静 | 对话、沉思 |
| 左摇 | pan-left | 环境展示 | 跟随视线 |
| 右摇 | pan-right | 环境展示 | 跟随运动 |
| 上摇 | tilt-up | 仰视/揭示 | 建筑、人物登场 |
| 下摇 | tilt-down | 俯视/发现 | 细节揭示 |
| 推镜 | zoom-in | 聚焦/紧张 | 关键时刻 |
| 拉镜 | zoom-out | 揭示全貌 | 场景收尾 |
| 推轨 | dolly | 跟随运动 | 行走、追逐 |
| 跟拍 | tracking | 动态跟随 | 动作场面 |

Seedance 2.0 具备**导演级运镜控制**，可通过 Prompt 自然描述运镜方式。

### 4. Prompt 生成规范

每个镜头生成两种 Prompt：

#### 4a. 文生图 Prompt（prompt 字段，英文）

用于生成静态分镜图：

```
{style_prefix}, {shot_type_description}, {character.prompt_template}, {action_description}, {environment_description}, {lighting}, {mood}, {camera_angle}
```

**示例**：
```
manga style, wide shot, nighttime cityscape seen through office window, a young man with short messy black hair and thin-framed glasses sitting at desk looking tired, warm interior light contrasting cool blue city lights, melancholy atmosphere, cinematic composition
```

#### 4b. 视频生成 Prompt（video_prompt 字段）

用于 Seedance 2.0 图生视频，重点描述**动态变化**和 **@ 引用**：

```
@Image1 作为首帧，{动态动作描述}，{运镜描述}，{光影变化}
```

**示例**：
```
@Image1 作为首帧，镜头从窗外城市远景缓缓推进到室内人物，窗帘微微飘动，光影柔和变化
```

#### 4c. 音效 Prompt（audio_prompt 字段，中文）

用于 Seedance 2.0 音视频联合生成：

```
{环境音效}, {动作音效}, {角色台词+语气}, {BGM描述}
```

**示例**：
```
深夜安静的办公室，空调低沉嗡嗡声，远处城市车流微弱声，淡淡忧伤的钢琴旋律缓缓响起
```

**Negative Prompt 标准模板**：
```
low quality, blurry, deformed, extra fingers, bad anatomy, disfigured, poorly drawn face, mutation, mutated, ugly, watermark, text
```

### 5. 音效设计指南

根据镜头类型设计 audio_prompt：

| 镜头类型 | audio_prompt 策略 |
|----------|------------------|
| 远景空镜 | 环境音 + 氛围 BGM，无对白 |
| 中景对话 | 角色台词 + 语气 + 轻微环境音 |
| 近景特写 | 强化情绪音效（心跳、呼吸）+ 台词 |
| 动作镜头 | 动作音效为主 + 紧张 BGM |
| 转场镜头 | 渐弱音效 + 过渡 BGM |

**对白写入 audio_prompt 的格式**：
```
{性别/年龄描述}{语气描述}说：'{台词内容}'
```

示例：
- `年轻男性疲惫地说：'又加班到这么晚'`
- `年轻女性温柔地说：'谢谢你一直陪着我'`
- `成熟男性旁白声：'那一年，改变了一切'`

### 6. Seedance 2.0 时长对齐

Seedance 2.0 支持 **4/5/10/15 秒**四档时长，分镜设计时每个镜头的 `duration` 必须为这四个值之一：

| 镜头场景 | 推荐时长 |
|----------|---------|
| 快速切换/表情反应 | 4s |
| 标准镜头/对话/空镜 | 5s |
| 长对话/动作/全景展示 | 10s |
| 关键情节/复杂互动/长镜头 | 15s |

## 输出格式

分镜输出为 JSON，严格遵循 `schemas/storyboard.schema.json`：

```json
{
  "id": "sb001",
  "project_id": "proj001",
  "script_id": "scr001",
  "shots": [
    {
      "id": "SH001",
      "scene_id": "S01",
      "shot_type": "wide",
      "camera_movement": "zoom-in",
      "prompt": "英文 Prompt（用于生成分镜图）",
      "video_prompt": "@Image1 作为首帧，动态描述（用于 Seedance 2.0）",
      "audio_prompt": "音效描述（中文，用于 Seedance 2.0 音视频联合生成）",
      "negative_prompt": "标准 negative prompt",
      "characters": ["char_liming"],
      "dialogue_text": "对应的对白文本",
      "duration": 5,
      "transition": "fade",
      "seedance_mode": "i2v",
      "ratio": "16:9"
    }
  ]
}
```

## 构图法则

- **三分法**：主体放在三等分线交点
- **对角线**：动态感，用于动作场面
- **中心构图**：庄重/对称，用于正面特写
- **留白**：给字幕和情绪留空间（漫剧重要）

## 数据存储

完成的分镜 JSON 写入 `projects/{project_id}/storyboard.json`。
