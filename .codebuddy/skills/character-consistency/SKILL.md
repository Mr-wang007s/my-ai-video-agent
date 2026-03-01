---
name: character-consistency
description: 角色一致性技术指南。当需要设计角色外观、维护角色在多镜头间的视觉一致性、管理角色资产库时，应使用此 Skill。
---

# 角色一致性

提供在 AI 生成漫剧中保持角色视觉一致性的完整技术方案，包括角色设计、MovieAgent 格式资产库管理、`<TOK>` 描述规范和 **Seedance 2.0 @ 引用** 策略。

## 角色资产库结构（MovieAgent 格式）

### character_list/ 目录规范

每个角色在 `character_list/` 下有独立的资产目录：

```
projects/{project_id}/character_list/
├── {CharName}/
│   ├── best.png       ← 最佳参考图（必须，角色正面半身/全身像）
│   ├── best.txt       ← <TOK> 外观描述（必须，英文）
│   ├── photo_1.png    ← 多角度参考图（3-5张推荐）
│   ├── photo_1.txt    ← 对应描述
│   ├── photo_2.png
│   ├── photo_2.txt
│   ├── ...
│   └── audio.wav      ← 声音参考（用于 TTS 声音克隆）
├── {CharName2}/
│   └── ...
```

**命名规则**：
- 目录名使用角色英文名或拼音（如 `Elsa`、`XiaoWang`），不含空格
- `best.png` / `best.txt` 为必须文件
- `photo_N.png` / `photo_N.txt` 按序号命名（N=1,2,3...）
- `audio.wav` 可选，用于声音克隆

### `<TOK>` 外观描述规范

`best.txt` 使用 `<TOK>` 占位符格式描述角色外观：

```
<TOK> has long blonde hair in a braid, wearing a sparkling blue dress, ice blue eyes, fair skin, elegant posture
```

**构建规则**：
- 以 `<TOK>` 开头（占位符，在图像生成时替换为角色标识）
- 使用英文描述
- 包含：发型发色、服装、眼睛、肤色、体型、标志特征
- 使用具体的、不可变的特征描述
- 避免模糊词汇（如 "handsome"、"beautiful"）
- 标志特征放在前面（如眼镜、疤痕、特殊饰品）
- 单行文本，不换行

**示例**：
- `<TOK> has short messy black hair, thin-framed glasses, wearing a white dress shirt with loosened tie, dark brown eyes, average build, slight dark circles under eyes`
- `<TOK> wears a purple cape over a dark dress, has auburn hair in twin braids, green eyes, freckles across nose, warm smile`
- `<TOK> is a tall muscular man with short blonde hair, ice harvester outfit with fur-lined vest, brown eyes, rugged appearance`

## 角色设计流程（两步式）

### Step 3a: 角色提取（/extract-characters）

从剧本中提取角色信息，写入 `characters.json`（遵循 `schemas/character_list.schema.json`）：

- 基础信息：名称、描述、在故事中的作用
- 外观细节：从文本推断的发型发色、服装、体型等
- 角色关系：与其他角色的关系
- 配音设置：性别、语速、默认情绪
- **设计状态**：初始为 `extracted`

**此步骤不生成图片，不消耗图像 API**。

### Step 3b: 角色精细设计（/design-characters {角色名}）

为单个角色生成完整的 `character_list/{CharName}/` 资产目录：

1. **生成 `<TOK>` 描述**：根据 `characters.json` 中的外观描述，构建英文 `<TOK>` 描述
2. **生成 best.png**：使用 `<TOK>` 描述（去掉 `<TOK>` 前缀）+ 风格关键词生成最佳参考图
3. **生成多角度 photo_N.png**：基于 best.png 风格，生成 3-5 张不同角度/表情/姿态的参考图
4. **写入 best.txt**：保存 `<TOK>` 描述
5. **写入 photo_N.txt**：保存每张参考图的描述
6. **生成 audio.wav**（可选）：使用 TTS 生成角色声音样本
7. **更新 characters.json**：设计状态改为 `designed`，填入 `tok_description` 和 `asset_dir`

### 参考图生成策略

**best.png 生成 Prompt**：
```
{style} style, {shot_type} portrait, {appearance_description_without_TOK}, clean background, high quality, high resolution, character reference sheet
```

**多角度 photo_N.png 生成 Prompt**：
```
photo_1: "{style} style, front view, {appearance}, neutral expression, clean background"
photo_2: "{style} style, 3/4 view, {appearance}, slight smile, clean background"
photo_3: "{style} style, side profile, {appearance}, looking ahead, clean background"
photo_4: "{style} style, close-up face, {appearance}, showing emotion, clean background"
photo_5: "{style} style, full body, {appearance}, action pose, clean background"
```

## 一致性保持技术（Seedance 2.0 优化）

### 方案 A：Seedance 2.0 @ 引用（首选）

Seedance 2.0 原生支持角色一致性，通过多模态参考输入：

1. 每次生成视频时，将角色的 `best.png` 作为 `image_paths` 传入
2. 在 `video_prompt` 中用 `@Image1 作为{角色名}外观` 锁定角色形象
3. Seedance 2.0 的多镜头叙事能力会自动保持跨场景一致性

**单角色场景**：
```json
{
  "image_paths": ["character_list/Elsa/best.png", "images/shots/Sub-Script_1|Scene_1|Shot_1.png"],
  "prompt": "@Image1 作为Elsa外观参考。@Image2 作为首帧，角色微微抬头，眼神中流露出惊异"
}
```

**多角色场景**：
```json
{
  "image_paths": ["character_list/Elsa/best.png", "character_list/Anna/best.png", "images/shots/Sub-Script_1|Scene_2|Shot_3.png"],
  "prompt": "@Image1 作为Elsa外观。@Image2 作为Anna外观。@Image3 作为首帧场景，两人面对面站在森林中"
}
```

### 方案 B：Prompt 工程兜底

- 每个镜头文生图 image_prompt 中嵌入角色外观描述（来自 `<TOK>` 描述去掉 `<TOK>` 前缀）
- 使用 seed 固定随机数（同一角色使用同一 seed 区间）
- 在 negative prompt 中排除不一致的特征
- **与方案 A 配合使用效果最佳**

### 方案 C：IP-Adapter（进阶）

- 使用 best.png 驱动角色生成
- 适合 Stable Diffusion WebUI / ComfyUI 工作流
- 保持面部和整体风格一致性

### 方案 D：LoRA 微调（高级）

- 使用 photo_N.png 训练专属 LoRA（类似 MovieAgent 的 ED LoRA）
- 最强一致性，但需要训练时间和 GPU 资源
- 适合长篇连载漫剧

## 多角色画面处理

### 文生图（image_prompt）

不含角色名，使用外观描述区分角色：
```
{style}, {shot_type}, {char_A_appearance} on the left, {char_B_appearance} on the right, {scene_description}
```

### 图生视频（Seedance 2.0 video_prompt）

使用 @Image 引用区分角色：
```
@Image1 作为{角色A}外观。@Image2 作为{角色B}外观。@Image3 作为首帧场景，{动态描述}
```

注意：
- 每个角色的 best.png 单独传入
- @ 引用编号从 1 开始，按 image_paths 数组顺序
- 最后一个 @Image 通常是分镜图（作为首帧）
- 每镜头最多 3 个角色（推荐 1-2 个）

## 边界框（Bounding Box）规范

Shot 级镜头中的 `Involving Characters` 使用归一化边界框：

```json
{
  "Involving Characters": {
    "Elsa": [0.1, 0.06, 0.49, 1.0],
    "Anna": [0.58, 0.04, 0.95, 1.0]
  }
}
```

- 坐标格式：`[x1, y1, x2, y2]`，值在 `[0, 1]` 范围
- 单角色：居中放置，宽度 ~0.3-0.5
- 双角色：左侧 (0.05-0.45) + 右侧 (0.55-0.95)
- 不允许边界框重叠
- y 坐标在实际渲染时可能被随机化

## 输出格式

### characters.json

角色清单遵循 `schemas/character_list.schema.json`，含设计状态（`extracted`/`designed`）。

### character_list/ 目录

每个已设计角色的完整资产目录，包含 best.png + best.txt + photo_N + audio.wav。

## 质量检查

- [ ] best.png 清晰展示角色全部外观特征
- [ ] best.txt 使用 `<TOK>` 开头的英文描述
- [ ] 多角度参考图风格一致
- [ ] characters.json 中的 design_status 正确反映实际状态
- [ ] 已设计角色的 asset_dir 和 tok_description 已填入
- [ ] @Image 引用编号与 image_paths 数组顺序匹配

遵循 `.codebuddy/rules/character-consistency.md` 中的完整检查清单。

## MCP Tool 调用指引

本 Skill 涉及以下 MCP tools（`manga-agent` server）：

### 角色保存到数据库
```
mcp: character_save(project_id="...", name="Elsa", description="冰雪女王", 
     appearance='{"hair": "blonde braid", "dress": "blue"}',
     reference_images='["character_list/Elsa/best.png"]',
     style_keywords='["ice queen", "elegant"]')
```

### 角色列表查询
```
mcp: character_list(project_id="...")
```

### 生成角色参考图（best.png）
```
mcp: image_generate(
     prompt="{style} style, {shot_type} portrait, {appearance}, clean background, high quality",
     output_dir="projects/{project_id}/character_list/{CharName}",
     engine="dalle", size="1024x1024")
```

### 记录设计日志
```
mcp: generation_log(project_id="...", stage="design", status="success")
mcp: project_update_status(project_id="...", status="characters_designing")
```

### 完整角色设计流程
1. 读取 `characters.json` 中的角色信息
2. 构建 `<TOK>` 外观描述 → 写入 `best.txt`
3. `image_generate` → 生成 `best.png`（去掉 `<TOK>` 前缀）
4. `image_generate` × N → 生成多角度 `photo_N.png`
5. `character_save` → 保存角色信息到数据库
6. 更新 `characters.json` 中的 `design_status` → `designed`
7. `generation_log` → 记录设计完成
