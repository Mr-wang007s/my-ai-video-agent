---
name: design-characters
description: "Step 3b: 角色设计 — 按需逐个设计角色，生成 character_list/ 资产目录。支持参数化调用。"
---

## 前置条件

- 项目状态为 `characters_extracted` 或 `characters_designing`
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
3. 更新项目状态为 `characters_designing`：
   ```
   MCP tool: project_update_status(project_id, status="characters_designing")
   ```
4. 构建 `<TOK>` 描述（遵循 character-consistency skill 规范）
5. 生成 best.png：
   ```
   MCP tool: image_generate(prompt="...", output_dir="projects/{project_id}/character_list/{CharName}", engine="dalle")
   ```
6. 生成多角度参考图（3-5 张）
7. 写入 best.txt（`<TOK>` 描述）
8. 可选生成语音样本：
   ```
   MCP tool: speech_generate(text="...", voice="...", output_dir="...")
   ```
9. 更新数据库：
   ```
   MCP tool: character_save(project_id, name, description, appearance, reference_images, style_keywords)
   MCP tool: generation_log(project_id, stage="design", status="success")
   ```
10. 更新 `characters.json` 中的 `design_status` → `designed`
11. 验证产出：best.png 存在、best.txt 使用 `<TOK>` 开头、≥3 张 photo_N.png

### 方式 3: 批量设计 — all

```
/design-characters all
```

逐个设计所有 `design_status == "extracted"` 的角色，每完成一个展示进度。

## 角色目录命名规则

- 优先使用角色英文名（如有），否则使用拼音（如 `XiaoWang`）
- 首字母大写，不含空格和特殊字符

## 注意事项

- 每个角色约消耗 3-5 次图像 API 调用
- 建议先设计主要角色，次要角色按需设计
