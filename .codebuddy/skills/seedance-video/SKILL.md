---
name: seedance-video
description: Seedance 2.0 视频生成技术指南。当需要将静态图片转为动态视频、调用火山引擎 Seedance 2.0 API、优化视频生成 Prompt 时，应使用此 Skill。
---

# Seedance 2.0 视频生成

提供火山方舟 Seedance 2.0 API 的使用规范、Prompt 优化技巧和参数配置指南。

## 概述

Seedance 2.0 是字节跳动发布的新一代 AI 视频生成模型，采用**统一的多模态音视频联合生成架构**，核心能力：

- **音视频联合生成**：原生输出带音效/配音的视频（双声道立体声），音画精准对齐
- **多镜头叙事**：跨场景保持角色身份、服装、风格一致
- **多模态参考**：支持最多 9 张图 + 3 段视频 + 3 段音频 + 文本 作为混合输入
- **@ 引用语法**：精确指定每个参考素材的用途
- **原生 1080p**：电影级输出画质
- **最长 15 秒**：高质量连续输出

## 三种生成模式

| 模式 | mode 值 | 输入 | 适用场景 |
|------|---------|------|----------|
| 文生视频 | `t2v` | 纯文本 Prompt | 创意构思、快速原型 |
| 图生视频 | `i2v` | 图片 + 文本 | 分镜图动态化、产品展示 |
| 多模态参考 | `multimodal` | 多图/视频/音频 + 文本 | 短片、多角色故事、风格参考 |

## 调用方式

通过 MCP tool `video_generate`（`manga-agent` server）调用：

### 文生视频
```
mcp: video_generate(
     prompt="一个年轻男子坐在深夜办公室窗前，窗外城市灯火，他缓缓抬头看向窗外，轻叹一口气",
     output_dir="projects/{project_id}/videos",
     mode="t2v", duration=5, resolution="1080p", ratio="16:9",
     audio_prompt="安静的办公室环境音，键盘敲击声渐停，一声轻叹")
```

### 图生视频
```
mcp: video_generate(
     prompt="@Image1 作为首帧，角色缓缓转头，微风吹动发丝，镜头慢慢推进",
     output_dir="projects/{project_id}/videos",
     mode="i2v", duration=5, shot_id="SH001",
     image_paths='["projects/{project_id}/images/SH001.png"]',
     audio_prompt="微风声，衣物轻微摩擦声")
```

### 多模态参考（多角色故事）
```
mcp: video_generate(
     prompt="@Image1 和 @Image2 作为男女主角外观。场景在 @Image3 咖啡馆中，两人面对面坐着",
     output_dir="projects/{project_id}/videos",
     mode="multimodal", duration=10, shot_id="SH005",
     image_paths='["character_list/CharA/best.png", "character_list/CharB/best.png", "images/shots/bg.png"]',
     audio_prompt="咖啡馆轻柔背景音乐，杯碟碰撞声，轻声对话")
```

### 资产注册
视频生成后，用 `asset_save` 注册到数据库：
```
mcp: asset_save(project_id="...", asset_type="video", name="S1_Sc1_Shot1", 
     file_path="videos/s1_sc1_shot1.mp4")
mcp: generation_log(project_id="...", stage="video", status="success")
```

## @ 引用语法

Seedance 2.0 通过 `@` 引用精确控制参考素材用途：

| 用途 | 提示词模式 | 说明 |
|------|-----------|------|
| 设置首帧 | `@Image1 作为首帧` | 图片作为视频第一帧 |
| 角色外观 | `@Image1 作为男主角外观` | 保持角色一致性 |
| 运动参考 | `参考 @Video1 的动作节奏` | 复制动作风格 |
| 运镜参考 | `跟随 @Video1 的镜头运动` | 复制运镜方式 |
| 背景音乐 | `使用 @Audio1 作为背景音乐` | 音乐与画面同步 |
| 视频延长 | `将 @Video1 延长 5 秒` | 连续叙事 |
| 替换角色 | `将 @Video1 中的角色替换为 @Image1` | 角色置换 |
| 场景背景 | `@Image3 作为背景场景` | 固定场景 |

**多素材组合示例**：
```
@Image1 和 @Image2 作为男女主角外观。第一幕：@Image3 咖啡馆场景，镜头从窗外缓慢推进。使用 @Audio1 作为背景音乐，音乐节奏与画面切换同步。
```

## Prompt 优化

### 文生视频 Prompt 要点

文生视频 Prompt 需要同时描述**画面内容**和**动态变化**：

**正确写法**：
```
一位穿白色连衣裙的年轻女子站在樱花树下，微风吹落花瓣，她闭眼深呼吸后缓缓睁开双眼，镜头从中景慢慢推进至面部特写，夕阳余晖洒在脸上
```

### 图生视频 Prompt 要点

图生视频的 Prompt 重点描述**动态变化**（静态信息已在图片中）：

**正确写法**：
```
@Image1 作为首帧，角色缓缓睁开双眼，微风吹动发丝，镜头慢慢推进，光影柔和变化
```

**错误写法**（重复描述图片已有内容）：
```
一个黑发年轻男人坐在办公桌前
```

### 音频 Prompt 要点

通过 `audio_prompt` 字段描述期望的音效/配音：

```
# 环境音效
"audio_prompt": "安静的夜晚，远处传来蛐蛐声，偶尔有轻微的风声"

# 角色配音（与画面动作匹配）
"audio_prompt": "年轻男性声音轻声说'又是一个加班的夜晚'，伴随键盘敲击声和鼠标点击声"

# ASMR 细节
"audio_prompt": "翻书页的沙沙声，茶杯放在木桌上的轻响"

# 背景音乐
"audio_prompt": "舒缓的钢琴BGM，带有淡淡忧伤的氛围"
```

### Prompt 结构模板

```
{角色/场景描述}, {动作/运动描述}, {镜头运动}, {光影变化}, {情绪氛围}
```

### 动作词汇表

| 类别 | 关键词 |
|------|--------|
| 面部 | 缓缓睁眼、微笑、皱眉、泪水滑落、凝视远方 |
| 头部 | 轻轻点头、摇头、转头、抬头望天 |
| 手部 | 伸出手、握拳、挥手、拿起物品、轻轻触碰 |
| 身体 | 起身、坐下、走向前方、转身、倚靠墙壁 |
| 环境 | 风吹树叶、花瓣飘落、雨滴坠落、光影流转、烟雾缭绕 |
| 镜头 | 镜头推进、镜头拉远、镜头平移、环绕拍摄、低机位仰拍 |

## 参数配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| mode | string | "t2v" | 生成模式：t2v / i2v / multimodal |
| prompt | string | - | 视频生成提示词（必填） |
| audio_prompt | string | "" | 音效/配音提示词（开启音视频联合生成） |
| image_paths | string[] | [] | 参考图片路径列表（最多 9 张） |
| video_refs | string[] | [] | 参考视频 URL 列表（最多 3 段） |
| audio_refs | string[] | [] | 参考音频 URL 列表（最多 3 段） |
| duration | int | 5 | 视频时长（秒）：4 / 5 / 10 / 15 |
| resolution | string | "1080p" | 分辨率：720p / 1080p |
| ratio | string | "16:9" | 宽高比：16:9 / 9:16 / 1:1 / 4:3 / 3:4 / 21:9 |
| seed | int | null | 随机种子（控制生成随机性） |
| fixed_camera | bool | false | 固定镜头（禁止自动运镜） |
| shot_id | string | "" | 镜头 ID，用于输出文件命名 |

## 多镜头叙事策略

Seedance 2.0 原生支持跨场景角色一致性，在漫剧流水线中的最佳实践：

### 角色一致性
1. 为每个角色生成高质量参考图
2. 每次生成视频时，通过 `image_paths` 传入角色参考图
3. 在 Prompt 中用 `@Image1 作为{角色名}外观` 锁定角色形象

### 多镜头连续性
1. 前一个镜头的视频可作为下一个镜头的参考输入
2. 使用 `参考 @Video1 的画面风格` 保持一致性
3. 使用 `将 @Video1 延长 N 秒` 实现连续叙事

### 音视频联合生成策略
1. **有对白的镜头**：在 `audio_prompt` 中描述角色说的话 + 环境音
2. **纯画面镜头**：在 `audio_prompt` 中描述环境音效和 BGM
3. **情绪转折镜头**：通过音频 prompt 强化情绪（如紧张时加入心跳声）

## 输入限制

| 项目 | 限制 |
|------|------|
| 图片 | 最多 9 张，JPEG/PNG/WebP |
| 视频 | 最多 3 段，总时长 ≤ 15s |
| 音频 | 最多 3 段 MP3 |
| 视频时长 | 4s / 5s / 10s / 15s |
| 分辨率 | 720p / 1080p |

## 成本与性能

- 约 40-60 秒生成 5 秒视频
- 15 秒视频需要更长时间（约 2-3 分钟）
- 视频 URL 有效期仅 **24 小时**，必须及时下载
- 生成成功率约 99.5%

## 错误处理

遵循 `.codebuddy/rules/api-usage.md` 中的重试机制。所有生成记录通过 `scripts/db_manager.py` 写入 `generations` 表。

## API 文档参考

详细的 API 接口文档参见 `references/seedance-api.md`。
