---
name: character-consistency
description: 角色一致性技术指南。当需要设计角色外观、维护角色在多镜头间的视觉一致性、管理角色资产库时，应使用此 Skill。
---

# 角色一致性

提供在 AI 生成漫剧中保持角色视觉一致性的完整技术方案，包括角色设计、MovieAgent 格式资产库管理和 `<TOK>` 描述规范。

## 角色资产库结构（MovieAgent 格式）

### character_list/ 目录规范

每个角色在 `character_list/` 下有独立的资产目录：

```
projects/{project_id}/character_list/
├── {CharName}/
│   ├── best.png       ← 最佳参考图（用户在 Gemini 等平台手动生成后放入）
│   ├── best.txt       ← <TOK> 外观描述（必须，英文，由 AI 生成）
│   ├── photo_1.png    ← 多角度参考图（3-5张推荐，用户手动生成）
│   ├── photo_2.png
│   └── ...
├── {CharName2}/
│   └── ...
```

**命名规则**：
- 目录名使用角色英文名或拼音（如 `Elsa`、`XiaoWang`），不含空格
- `best.txt` 为必须文件（AI 自动生成）
- `best.png` 为推荐文件（用户在 Gemini 手动生成后放入）
- `photo_N.png` 按序号命名（N=1,2,3...）

### `<TOK>` 外观描述规范

`best.txt` 使用 `<TOK>` 占位符格式描述角色外观：

```
<TOK> has long blonde hair in a braid, wearing a sparkling blue dress, ice blue eyes, fair skin, elegant posture
```

**构建规则**：
- 以 `<TOK>` 开头（占位符，在图像 Prompt 中替换为完整外观描述）
- 使用英文描述
- 包含：发型发色、服装、眼睛、肤色、体型、标志特征
- 使用具体的、不可变的特征描述
- 避免模糊词汇（如 "handsome"、"beautiful"）
- 标志特征放在前面（如眼镜、疤痕、特殊饰品）
- 单行文本，不换行

**示例**：
- `<TOK> has short messy black hair, thin-framed glasses, wearing a white dress shirt with loosened tie, dark brown eyes, average build, slight dark circles under eyes`
- `<TOK> wears a purple cape over a dark dress, has auburn hair in twin braids, green eyes, freckles across nose, warm smile`

## 角色设计流程

### Step 3a: 角色提取（/extract-characters）

从剧本中提取角色信息，写入 `characters.json`：

- 基础信息：名称、描述、在故事中的作用
- 外观细节：从文本推断的发型发色、服装、体型等
- 角色关系：与其他角色的关系
- 配音设置：性别、语速、默认情绪
- **设计状态**：初始为 `extracted`

### Step 3b: 角色精细设计（/design-characters {角色名}）

为单个角色构建完整的文本描述并生成用于 Gemini 的 Prompt：

1. **生成 `<TOK>` 描述**：根据 `characters.json` 中的外观描述，构建英文 `<TOK>` 描述
2. **创建 `character_list/{CharName}/` 目录**
3. **写入 best.txt**：保存 `<TOK>` 描述
4. **生成 Gemini Prompt**：输出完整的文生图 Prompt，供用户在 Gemini 手动生成 best.png
5. **更新 characters.json**：设计状态改为 `designed`，填入 `tok_description` 和 `asset_dir`

### 参考图 Prompt 模板（供用户在 Gemini 使用）

**best.png Prompt**：
```
{style} style, {shot_type} portrait, {appearance_description_without_TOK}, clean background, high quality, high resolution, character reference sheet
```

**多角度 photo_N.png Prompt**：
```
photo_1: "{style} style, front view, {appearance}, neutral expression, clean background"
photo_2: "{style} style, 3/4 view, {appearance}, slight smile, clean background"
photo_3: "{style} style, side profile, {appearance}, looking ahead, clean background"
photo_4: "{style} style, close-up face, {appearance}, showing emotion, clean background"
photo_5: "{style} style, full body, {appearance}, action pose, clean background"
```

## Prompt 工程一致性策略

- 每个镜头的 `image_prompt` 中嵌入角色外观描述（来自 `<TOK>` 描述去掉 `<TOK>` 前缀）
- `image_prompt` 中**禁止**使用角色名（对应 MovieAgent 的 Coarse Plot 思路）
- 不同镜头中同一角色的描述文字**必须完全一致**（逐字匹配）
- 在 negative prompt 中排除不一致的特征

## 多角色画面处理

### 文生图（image_prompt）

不含角色名，使用外观描述区分角色：
```
{style}, {shot_type}, {char_A_appearance} on the left, {char_B_appearance} on the right, {scene_description}
```

### 边界框（Bounding Box）规范

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
- 每镜头最多 3 个角色（推荐 1-2 个）

## MCP Tool 调用指引

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

### 记录设计日志
```
mcp: generation_log(project_id="...", stage="design", status="success")
mcp: project_update_status(project_id="...", status="characters_designed")
```

## 质量检查

- [ ] best.txt 使用 `<TOK>` 开头的英文描述
- [ ] best.txt 描述具体、可重复（无模糊词汇）
- [ ] characters.json 中的 design_status 正确反映实际状态
- [ ] 已设计角色的 asset_dir 和 tok_description 已填入
- [ ] Gemini Prompt 已输出供用户使用

遵循 `.codebuddy/rules/character-consistency.md` 中的完整检查清单。
