---
name: storyboard-design
description: 分镜设计与镜头语言指南。当需要将剧本场景拆解为具体镜头、设计运镜方式、生成三版本 Prompt（image_prompt / video_prompt / audio_prompt）时，应使用此 Skill。
---

# 分镜设计

提供从剧本到分镜的转化方法论，包括镜头语言、构图法则、运镜设计、三版本 Prompt 生成和音效设计（适配 MovieAgent 分层拆解 + Seedance 2.0 音视频联合生成）。

## 在 MovieAgent 流水线中的位置

分镜设计知识主要服务于 **Step 4c: 镜头创建（ShotPlotCreateCoT）**，具体体现在：

- **Shot Type 选择**：根据叙事需要选择合适的镜头类型
- **Camera Movement 设计**：运镜方式匹配情绪和动作
- **三版本 Prompt 生成**：为不同生成引擎构建定制化 Prompt
- **Duration 规划**：时长匹配 Seedance 2.0 的四档设定

## 镜头类型选择

| 类型 | 英文 | 用途 | 使用场景 |
|------|------|------|----------|
| 远景 | Wide shot | 展示环境/氛围 | 场景开头、空间关系 |
| 中景 | Medium shot | 展示人物互动 | 对话、日常动作 |
| 近景 | Close-up | 突出表情/细节 | 情感爆发、关键道具 |
| 大特写 | Extreme close-up | 极致细节 | 眼神、嘴唇、物品 |
| 过肩 | Over-shoulder shot | 对话视角 | 两人对话 |
| 主观 | POV shot | 代入感 | 角色视角 |
| 俯拍 | Bird-eye view | 全局/压迫感 | 群像、孤独感 |
| 仰拍 | Low-angle shot | 力量/威严 | 英雄、反派 |
| 荷兰角 | Dutch angle | 不安/紧张 | 悬疑、混乱场面 |

## 运镜设计

| 运镜 | 英文 | 效果 | 适用场景 |
|------|------|------|----------|
| 静止 | Static | 稳定/沉静 | 对话、沉思 |
| 左摇 | Pan left | 环境展示 | 跟随视线 |
| 右摇 | Pan right | 环境展示 | 跟随运动 |
| 上摇 | Tilt up | 仰视/揭示 | 建筑、人物登场 |
| 下摇 | Tilt down | 俯视/发现 | 细节揭示 |
| 推镜 | Zoom in | 聚焦/紧张 | 关键时刻 |
| 拉镜 | Zoom out | 揭示全貌 | 场景收尾 |
| 慢推轨 | Slow dolly-in | 渐进聚焦 | 情感深入 |
| 跟拍 | Tracking shot | 动态跟随 | 动作场面、追逐 |

Seedance 2.0 具备**导演级运镜控制**，可通过 Prompt 自然描述运镜方式。

## 三版本 Prompt 生成规范

每个 Shot 需要生成三种 Prompt，针对不同生成引擎优化：

### image_prompt（英文，给 DALL-E 3 文生图）

**用途**：生成静态关键帧/分镜图

**格式**：
```
{style}, {shot_type}, {scene_description}, {character_action_without_names}, {lighting}, {mood}, {composition}
```

**规则**：
- **必须英文**
- **不含角色名**（对应 MovieAgent 的 Coarse Plot 思路）
- 使用角色外观描述替代名字（如 "a young woman with blonde braid" 而非 "Elsa"）
- 包含风格前缀、镜头类型、场景描述、光影、氛围
- 专业摄影/美术指导用语

**示例**：
```
manga style, medium shot, dimly lit office interior at night, a young man with short messy black hair and thin-framed glasses rubbing his eyes tiredly at a desk, warm lamp light contrasting cool window light, melancholy atmosphere, rule of thirds composition
```

### video_prompt（中文/混合，给 Seedance 2.0 图生视频）

**用途**：描述动态变化、运镜，驱动视频生成

**格式**：
```
@Image1 作为{角色名}外观参考。@Image2 作为首帧，{dynamic_action}, {camera_movement}, {lighting_changes}
```

**规则**：
- 使用 `@Image` 引用角色参考图和首帧图
- @Image 编号从 1 开始，按 image_paths 数组顺序
- 角色参考图排在前面，首帧图排在最后
- 重点描述**动态变化**（动作、表情变化、物体运动）
- 包含运镜描述
- 可以使用角色名

**示例**：
```
@Image1 作为Elsa外观参考。@Image2 作为首帧，角色微微抬头，眼神中流露出惊异，手指周围缓缓浮现冰晶，镜头缓慢推进
```

### audio_prompt（中文，给 Seedance 2.0 音视频联合生成）

**用途**：描述该镜头的完整音频设计

**格式**：
```
{环境音效}, {动作音效}, {角色台词+语气}, {BGM描述}
```

**对白写入格式**：
```
{性别/年龄描述}{语气描述}说：'{台词内容}'
```

**示例**：
- `空旷的城堡大厅，冰晶凝结的清脆声，年轻女性惊异地说：'那个声音……我又听到了'，空灵的钢琴BGM缓缓响起`
- `深夜安静的办公室，空调低沉嗡嗡声，键盘敲击声停止，年轻男性疲惫地叹气：'又是加班到深夜'，淡淡忧伤的钢琴旋律`

**根据镜头类型的 audio_prompt 策略**：

| 镜头类型 | audio_prompt 策略 |
|----------|------------------|
| 远景空镜 | 环境音 + 氛围 BGM，无对白 |
| 中景对话 | 角色台词 + 语气 + 轻微环境音 |
| 近景特写 | 强化情绪音效（心跳、呼吸）+ 台词 |
| 动作镜头 | 动作音效为主 + 紧张 BGM |
| 转场镜头 | 渐弱音效 + 过渡 BGM |

## Seedance 2.0 时长对齐

Seedance 2.0 支持 **4/5/10/15 秒**四档时长，`Duration` 必须为这四个值之一：

| 镜头场景 | 推荐时长 |
|----------|---------|
| 快速切换/表情反应 | 4s |
| 标准镜头/对话/空镜 | 5s |
| 长对话/动作/全景展示 | 10s |
| 关键情节/复杂互动/长镜头 | 15s |

## 构图法则

- **三分法**：主体放在三等分线交点
- **对角线**：动态感，用于动作场面
- **中心构图**：庄重/对称，用于正面特写
- **留白**：给字幕和情绪留空间（漫剧重要）

## 镜头节奏设计

### 场景内节奏

一个场景内的镜头序列应有节奏变化：

1. **开场镜头**：远景/中景建立场景
2. **发展镜头**：中景/近景推进情节
3. **高潮镜头**：近景/特写放大情绪
4. **过渡镜头**：收束，为下一场景铺垫

### 跨场景节奏

遵循 `.codebuddy/rules/narrative-rhythm.md` 的节奏约束。

## 与 MovieAgent 流水线的配合

### 双版本描述对应

| MovieAgent 字段 | 我们的字段 | 用途 |
|-----------------|-----------|------|
| `Coarse Plot` | `image_prompt` | 无人名描述 → 文生图 |
| `Plot/Visual Description` | `video_prompt` | 详细描述 → 图生视频 |
| — | `audio_prompt` | 音效描述 → 音视频联合 |

### seedance_mode 选择

| 条件 | seedance_mode |
|------|--------------|
| 有角色 best.png 参考图 | `multimodal` |
| 仅场景图/空镜 | `i2v` |
| 无首帧图 | `t2v` |

## MCP Tool 调用指引

分镜设计的 LLM CoT 推理由主对话直接执行，**MCP tool 仅用于记录日志和更新状态**：

### 记录每个 Shot 的生成日志

```
MCP tool: generation_log(
  project_id="...",
  stage="breakdown",
  input_params='{"sub_script": "...", "scene": "...", "shot": "..."}',
  output_path="projects/{project_id}/script_breakdown.json",
  status="success",
  error_msg=null
)
```

### 更新项目状态

```
MCP tool: project_update_status(project_id="...", status="script_broken")
```

### 查询角色信息（用于 Involving Characters）

```
MCP tool: character_list(project_id="...")
```

> **注意**：三版本 Prompt 生成（image_prompt / video_prompt / audio_prompt）是 CoT 推理的产物，直接写入 `script_breakdown.json`，不需要通过 MCP tool。

## 输出格式

Shot 级数据嵌套在 `script_breakdown.json` 的三层结构中，遵循 `schemas/script_breakdown.schema.json`。

**关键字段清单**（每个 Shot 必须包含）：
- `Involving Characters`：角色 + 边界框
- `Plot/Visual Description`：详细视觉描述
- `Coarse Plot`：简洁无人名描述
- `image_prompt`：英文文生图 Prompt
- `video_prompt`：Seedance 视频 Prompt
- `audio_prompt`：中文音效 Prompt
- `Shot Type`：镜头类型
- `Camera Movement`：运镜方式
- `Duration`：4/5/10/15
- `Subtitles`：对白字幕
- `seedance_mode`：生成模式
