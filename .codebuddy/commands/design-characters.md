---
name: design-characters
description: "Step 3b: 角色设计 — 按需逐个设计角色，生成 character_list/ 资产目录。支持参数化调用。"
---

## 前置条件

- 项目状态为 `characters_extracted` 或 `characters_designing`
- `projects/{project_id}/characters.json` 已存在

## 三种调用方式

### 方式 1: 无参数 — 列出角色状态

```
/design-characters
```

**执行**：
1. 读取 `projects/{project_id}/characters.json`
2. 展示所有角色及其设计状态：

| 角色 | 外观描述 | 设计状态 |
|------|---------|---------|
| 小王 | 短发，戴黑框眼镜... | ❌ extracted |
| 小李 | 长发飘逸，穿白裙... | ✅ designed |
| 老张 | 秃头，穿西装... | ❌ extracted |

3. 提示用户使用 `/design-characters {角色名}` 设计指定角色

### 方式 2: 指定角色 — 精细设计

```
/design-characters 小王
```

**执行**：
1. 验证前置条件
2. 读取 `characters.json`，找到目标角色
3. 如果角色 `design_status == "designed"`，提示用户该角色已设计，询问是否重新设计
4. 更新角色 `design_status` 为 `"designing"`
5. 更新项目状态为 `characters_designing`（如果还不是）
6. **Dispatch to character-designer agent**：

   ```
   Project: {project_id}
   Task: 为角色 "小王" 生成完整的 character_list 资产目录

   角色信息：
   - 名称: 小王
   - 描述: {characters.json 中的 description}
   - 外观描述: {characters.json 中的 appearance_description}
   - 风格关键词: {style_keywords}
   - 配音设置: {voice}
   - 项目风格: {project.style}

   Output:
   - projects/{project_id}/character_list/XiaoWang/best.png
   - projects/{project_id}/character_list/XiaoWang/best.txt
   - projects/{project_id}/character_list/XiaoWang/photo_1.png ~ photo_3.png
   - projects/{project_id}/character_list/XiaoWang/photo_1.txt ~ photo_3.txt
   - projects/{project_id}/character_list/XiaoWang/audio.wav (optional)
   - 更新 characters.json: design_status → "designed", tok_description, asset_dir

   使用 character-consistency skill 指导设计。
   ```

7. 验证产出：
   - `best.png` 存在且 > 0 bytes
   - `best.txt` 使用 `<TOK>` 开头
   - 至少 3 张 photo_N.png
   - characters.json 已更新

8. 向用户展示结果：
   - 角色参考图预览
   - `<TOK>` 描述
   - 多角度参考图列表
   - 设计状态更新

### 方式 3: 批量设计 — all

```
/design-characters all
```

**执行**：
1. 读取 `characters.json`
2. 筛选所有 `design_status == "extracted"` 的角色
3. 逐个调度 character-designer agent
4. 每完成一个角色，展示进度
5. 全部完成后，展示所有角色的设计状态

## 角色目录命名规则

将中文角色名转为英文/拼音作为目录名：
- 优先使用角色英文名（如有）
- 否则使用拼音（如 `XiaoWang`、`LaoZhang`）
- 不含空格和特殊字符
- 首字母大写

## 重新设计

如果角色已设计但用户不满意：
```
/design-characters 小王
```
会提示"该角色已设计，是否重新设计？"用户确认后：
1. 保留旧资产为备份
2. 重新执行设计流程
3. 更新 characters.json

## 注意事项

- 每个角色设计约消耗 3-5 次图像 API 调用（best + 多角度）
- audio.wav 生成需要 TTS API 支持
- 建议先设计主要角色（出场频率高的），次要角色按需设计
- Step 4 分镜拆解会检查角色是否有 character_list 资产，有则引用，无则仅用文字描述
