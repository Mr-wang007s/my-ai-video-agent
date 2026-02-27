# 画面质量标准

## 分辨率要求

- 最终输出视频：最低 1080p (1920x1080)，推荐 2K
- 分镜图片生成：最低 1024x1024，推荐 1024x1536（竖版漫剧）或 1536x1024（横版）
- 角色参考图（best.png）：最低 512x512，推荐 1024x1024

## Seedance 2.0 视频质量

- 原生支持 1080p 输出
- 宽高比选项：16:9 / 9:16 / 1:1
- 时长选项：4s / 5s / 10s / 15s
- 自带双声道立体声音轨

## 画面一致性

- 同一场景内，背景风格、光照方向、色调必须保持一致
- 角色外观通过 **character_list/best.png @引用** + **image_prompt 外观描述** 双重保障一致性
- 同一话/集内，整体画风不允许出现显著跳变
- 使用 Seedance 2.0 的多镜头叙事能力保持跨场景一致性

## CoT 推理质量

### 三层嵌套 JSON 结构校验
- [ ] script_breakdown.json 包含 Relationships + Internal Chain-of-Thought + Sub-Script 三个顶层键
- [ ] 每个 Sub-Script 包含 Scene Annotation（含 CoT + Scene 列表）
- [ ] 每个 Scene 包含 Shot Annotation（含 CoT + Shot 列表）
- [ ] 三层嵌套的层级关系正确

### CoT 推理完整性
- [ ] Layer 1 CoT 包含 5 个必填步骤
- [ ] Layer 2 CoT 包含 4 个必填步骤
- [ ] Layer 3 CoT 包含 6 个必填步骤
- [ ] 每个步骤有实质性分析内容（非空字符串）
- 遵循 `.codebuddy/rules/cot-reasoning.md` 的完整规则

## 生成质量检查清单

### 图片质量
- [ ] 无明显的面部畸变（多余手指、扭曲五官）
- [ ] 角色辨识度：观众能区分不同角色
- [ ] 文字/标志无乱码

### 视频质量
- [ ] 视频无明显闪烁或帧间跳变
- [ ] 动作流畅自然，符合物理规律
- [ ] 运镜稳定，无异常抖动

### 音频质量（Seedance 2.0 原生音轨）
- [ ] 音频与画面动作同步（偏差 < 300ms）
- [ ] 对白发音清晰可辨
- [ ] 环境音效与画面匹配
- [ ] 无明显的音频割裂或噪音
- [ ] 若音频质量不佳，标记 `needs_tts_override: true`

## Prompt 规范

### image_prompt（英文，文生图）
- 必须使用英文
- 必须包含风格前缀（如 `manga style,` `anime style,`）
- **禁止**包含角色名（使用外观描述替代）
- 必须包含角色外观描述（来自 `<TOK>` 描述去掉前缀）
- 使用 negative prompt 排除常见缺陷

### video_prompt（Seedance 2.0 图生视频）
- 使用 @Image 引用角色 best.png
- @Image 编号与 image_paths 数组顺序一致
- 重点描述动态变化和运镜

### audio_prompt（中文，音视频联合）
- 使用中文描述
- 包含环境音效 + 动作音效 + 对白（含性别/语气） + BGM
- 对白格式：`{性别/年龄}{语气}说：'{台词}'`

### Negative Prompt 标准模板
```
low quality, blurry, deformed, extra fingers, bad anatomy, disfigured, poorly drawn face, mutation, mutated, ugly, watermark, text
```
