---
name: storyboard-design
description: 分镜设计与镜头语言指南。当需要将剧本场景拆解为具体镜头、设计运镜方式、生成三版本 Prompt（image_prompt / video_prompt / audio_prompt）时，应使用此 Skill。
---

# 分镜设计

提供从剧本到分镜的转化方法论，包括镜头语言、构图法则、运镜设计和三版本 Prompt 生成。

## 在流水线中的位置

分镜设计知识主要服务于 **Step 4c: 镜头创建（ShotPlotCreateCoT）**，具体体现在：

- **Shot Type 选择**：根据叙事需要选择合适的镜头类型
- **Camera Movement 设计**：运镜方式匹配情绪和动作
- **三版本 Prompt 生成**：为不同平台构建定制化 Prompt
- **Duration 规划**：时长匹配叙事节奏

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

## 三版本 Prompt 生成规范

每个 Shot 需要生成三种 Prompt，针对不同平台优化：

### image_prompt（英文，用于 Gemini 等平台文生图）

**用途**：生成静态关键帧/分镜图

**格式**：
```
{style}, {shot_type}, {scene_description}, {character_action_without_names}, {lighting}, {mood}, {composition}
```

**规则**：
- **必须英文**
- **不含角色名**（对应 MovieAgent 的 Coarse Plot 思路）
- 使用角色外观描述替代名字
- 包含风格前缀、镜头类型、场景描述、光影、氛围

### video_prompt（中文/混合，用于可灵等平台图生视频）

**用途**：描述动态变化、运镜

**规则**：
- 重点描述**动态变化**（动作、表情变化、物体运动）
- 包含运镜描述
- 可以使用角色名

### audio_prompt（中文，配音/音效参考）

**用途**：描述该镜头的完整音频设计，供在剪映中配音时参考

**对白写入格式**：`{性别/年龄描述}{语气描述}说：'{台词内容}'`

## 时长规划

| 镜头场景 | 推荐时长 |
|----------|---------|
| 快速切换/表情反应 | 4-5s |
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

1. **开场镜头**：远景/中景建立场景
2. **发展镜头**：中景/近景推进情节
3. **高潮镜头**：近景/特写放大情绪
4. **过渡镜头**：收束，为下一场景铺垫

### 跨场景节奏

遵循 `.codebuddy/rules/narrative-rhythm.md` 的节奏约束。

## 输出格式

Shot 级数据嵌套在 `script_breakdown.json` 的三层结构中。

**关键字段清单**（每个 Shot 必须包含）：
- `Involving Characters`：角色 + 边界框
- `Plot/Visual Description`：详细视觉描述
- `Coarse Plot`：简洁无人名描述
- `image_prompt`：英文文生图 Prompt（用于 Gemini）
- `video_prompt`：图生视频 Prompt（用于可灵）
- `audio_prompt`：中文音效描述（用于剪映配音）
- `Shot Type`、`Camera Movement`、`Duration`、`Subtitles`
