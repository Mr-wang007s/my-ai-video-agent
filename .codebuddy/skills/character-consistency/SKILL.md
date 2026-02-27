---
name: character-consistency
description: 角色一致性技术指南。当需要设计角色外观、维护角色在多镜头间的视觉一致性、管理角色资产库时，应使用此 Skill。
---

# 角色一致性

提供在 AI 生成漫剧中保持角色视觉一致性的完整技术方案，包括角色设计、Prompt 工程和 **Seedance 2.0 @ 引用** 策略。

## 角色设计流程

### 1. 角色定义

从剧本中提取角色信息，为每个角色创建结构化数据（遵循 `schemas/character.schema.json`）：

- 基础信息：姓名、性别、年龄段、性格
- 外观细节：发型发色、眼睛、体型、服装、标志特征
- 风格关键词：用于 Prompt 的英文描述标签
- Prompt 模板：角色在所有镜头中的固定描述片段
- **参考图**：角色高质量参考图（用于 Seedance 2.0 @ 引用）

### 2. prompt_template 构建

prompt_template 是角色一致性的核心，必须包含：

```
{gender_age}, {hair_description}, {eye_description}, {distinguishing_features}, {default_clothing}, {style}
```

**构建规则**：
- 使用具体的、不可变的特征描述
- 避免模糊词汇（如 "handsome"、"beautiful"）
- 标志特征放在前面（如眼镜、疤痕）
- 服装描述可有多个变体（对应换装场景）

### 3. 角色参考图生成

首次生成角色参考图的最佳实践：

1. 使用 prompt_template 生成 3-5 张候选图
2. 选择最符合设定的作为参考图
3. 将参考图路径记录到 `reference_images` 字段
4. **参考图将用于 Seedance 2.0 的 @ 引用，确保角色一致性**

## 一致性保持技术（Seedance 2.0 优化）

### 方案 A：Seedance 2.0 @ 引用（首选，推荐）

Seedance 2.0 原生支持角色一致性，通过多模态参考输入：

1. 每次生成视频时，将角色参考图作为 `image_paths` 传入
2. 在 `video_prompt` 中用 `@Image1 作为{角色名}外观` 锁定角色形象
3. Seedance 2.0 的多镜头叙事能力会自动保持跨场景一致性

**单角色场景**：
```json
{
  "image_paths": ["assets/characters/liming_ref.png", "projects/proj001/images/SH001.png"],
  "prompt": "@Image1 作为李明外观参考。@Image2 作为首帧，角色缓缓走向窗前"
}
```

**多角色场景**：
```json
{
  "image_paths": ["assets/characters/liming_ref.png", "assets/characters/xiaoli_ref.png", "projects/proj001/images/SH005.png"],
  "prompt": "@Image1 作为李明外观。@Image2 作为小丽外观。@Image3 作为首帧场景，两人面对面坐在咖啡馆"
}
```

### 方案 B：Prompt 工程兜底

- 每个镜头文生图 Prompt 中原样插入角色的 `prompt_template`
- 使用 seed 固定随机数（同一角色使用同一 seed 区间）
- 在 negative prompt 中排除不一致的特征
- **与方案 A 配合使用效果最佳**

### 方案 C：IP-Adapter（进阶）

- 使用参考图驱动角色生成
- 适合 Stable Diffusion WebUI / ComfyUI 工作流
- 保持面部和整体风格一致性

### 方案 D：LoRA 微调（高级）

- 使用角色参考图训练专属 LoRA
- 最强一致性，但需要训练时间和资源
- 适合长篇连载漫剧

## 多角色画面处理

### 文生图（分镜图）
```
{style}, {shot_type}, {char_A.prompt_template} on the left, {char_B.prompt_template} on the right, {scene_description}
```

### 图生视频（Seedance 2.0）
```
@Image1 作为{角色A}外观。@Image2 作为{角色B}外观。@Image3 作为首帧场景，{动态描述}
```

注意：
- 每个角色的参考图单独传入
- @ 引用编号从 1 开始，按 image_paths 数组顺序
- 最后一个 Image 通常是分镜图（作为首帧）

## 输出格式

角色数据输出遵循 `schemas/character.schema.json`，写入 `projects/{project_id}/characters.json`：

```json
[
  {
    "id": "char_liming",
    "project_id": "proj001",
    "name": "李明",
    "description": "...",
    "appearance": { ... },
    "style_keywords": ["manga style", "young man", ...],
    "reference_images": ["assets/characters/liming_ref_01.png"],
    "voice": { "voice_type": "young_male", "speed": 1.0 },
    "prompt_template": "a young man with short messy black hair..."
  }
]
```

## 质量检查

遵循 `.codebuddy/rules/character-consistency.md` 中的检查清单。
