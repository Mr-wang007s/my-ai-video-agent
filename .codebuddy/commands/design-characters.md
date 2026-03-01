---
name: design-characters
description: "Step 3b: 角色设计 — 构建 <TOK> 描述，创建 character_list/ 文本资产。用户自行在 Gemini 等平台生成参考图。"
---

## 前置条件

- 项目状态为 `characters_extracted`
- `projects/{project_id}/characters.json` 已存在

## 必须加载的 Skill

```
use_skill("character-consistency")
```

## 三种调用方式

### 方式 1: 无参数 — 列出角色状态

```
/design-characters
```

读取 `projects/{project_id}/characters.json`，展示所有角色及其设计状态。

### 方式 2: 指定角色 — 精细设计

```
/design-characters 小王
```

**执行**：
1. 验证前置条件
2. 读取 `characters.json`，找到目标角色
3. 构建 `<TOK>` 英文外观描述（遵循 character-consistency skill 规范）
4. 创建 `character_list/{CharName}/` 目录
5. 写入 `best.txt`（`<TOK>` 开头的英文描述）
6. 生成用于 Gemini 的 Prompt，供用户手动生成 best.png：
   - 输出完整的英文 Prompt（含风格前缀和 negative prompt）
   - 建议用户在 Gemini 生成后，将最佳图片保存为 `best.png`
   - 建议额外生成 3-5 张多角度参考图（photo_1.png ~ photo_5.png）
7. 更新数据库：
   ```
   MCP tool: character_save(project_id, name, description, appearance, reference_images, style_keywords)
   MCP tool: generation_log(project_id, stage="design", status="success")
   ```
8. 更新 `characters.json` 中的 `design_status` → `designed`
9. 更新项目状态：
   ```
   MCP tool: project_update_status(project_id, status="characters_designed")
   ```

### 方式 3: 批量设计 — all

```
/design-characters all
```

逐个为所有 `design_status == "extracted"` 的角色构建 `<TOK>` 描述和 Prompt。

## 角色目录命名规则

- 优先使用角色英文名（如有），否则使用拼音（如 `XiaoWang`）
- 首字母大写，不含空格和特殊字符

## 注意事项

- 角色设计为纯文本操作，不调用任何 API
- 用户需自行在 Gemini 等平台生成参考图并放入 `character_list/{CharName}/` 目录
- `best.png` 是可选的，但对后续分镜拆解中的角色描述一致性有帮助
