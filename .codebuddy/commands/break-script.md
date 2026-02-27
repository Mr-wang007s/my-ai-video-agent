---
name: break-script
description: "Step 4: 三层 CoT 分镜拆解 — MovieAgent 核心，Sub-Scripts → Scenes → Shots"
---

## 前置条件

- 项目状态为 `characters_extracted` 或 `characters_designing`
- `projects/{project_id}/script_synopsis.json` 已存在
- `projects/{project_id}/characters.json` 已存在
- 建议至少设计了主要角色（`/design-characters` 完成关键角色）

## 执行步骤

### Step 4a: Sub-Script 拆解

1. **Dispatch to screenwriter agent**：

   ```
   Project: {project_id}
   Task: 将剧本拆分为 Sub-Scripts（≤20个章节/幕），使用 screenwriterCoT

   Input: projects/{project_id}/script_synopsis.json (MovieScript + Character)
   Output: projects/{project_id}/script_breakdown.json (根层级)

   使用 script-breakdown skill 的 Layer 1 Prompt 模板。
   强制输出 Internal Chain-of-Thought。
   ```

2. **验证**：
   - script_breakdown.json 已创建
   - 包含 Relationships、Internal Chain-of-Thought、Sub-Script 三个顶层键
   - Sub-Script 数量 ≤ 20
   - 每个 Sub-Script 的 Plot ≥ 50 词

3. **可选：督导审查**：
   ```
   Dispatch to script-supervisor agent:
   Task: Review Layer 1 output quality
   ```

4. **展示结果**：向用户展示 Sub-Script 概览（编号、Plot 摘要、涉及角色、时间线）

### Step 4b: 场景规划

5. **Dispatch to scene-planner agent**：

   ```
   Project: {project_id}
   Task: 逐个 Sub-Script 拆解为 Scenes

   Input: projects/{project_id}/script_breakdown.json
   Output: 嵌套写入 script_breakdown.json 的 Scene Annotation

   使用 script-breakdown skill 的 Layer 2 Prompt 模板。
   逐个 Sub-Script 循环调用，每次独立上下文。
   ```

6. **验证**：
   - 每个 Sub-Script 都有 Scene Annotation
   - 每个 Scene Annotation 包含 Internal Chain-of-Thought 和 Scene 列表
   - Scene Description 足够具象

### Step 4c: 镜头创建

7. **Dispatch to shot-creator agent**：

   ```
   Project: {project_id}
   Task: 逐个 Scene 拆解为 Shots

   Input:
   - projects/{project_id}/script_breakdown.json
   - projects/{project_id}/characters.json (角色清单)
   - projects/{project_id}/character_list/ (检查已设计角色)

   Output: 嵌套写入 script_breakdown.json 的 Shot Annotation

   使用 script-breakdown skill 的 Layer 3 Prompt 模板。
   双层循环：Sub-Script → Scene。
   仅为有 character_list 资产的角色添加 @Image 引用。
   ```

8. **验证**：
   - 每个 Scene 都有 Shot Annotation
   - 每个 Shot 包含完整字段（双版本描述、三版本 Prompt、边界框）
   - Duration 为 4/5/10/15 之一
   - 所有对白分配到了 Subtitles

### 最终汇总

9. **更新状态**：
   ```bash
   python scripts/db_manager.py --action update_status --data '{"project_id": "{project_id}", "status": "script_broken"}'
   ```

10. **向用户展示概览**：
    - 总 Sub-Script 数
    - 总 Scene 数
    - 总 Shot 数
    - 预估总时长
    - 角色出场统计
    - 有/无资产的角色列表

11. **提示下一步**：
    - 如果有重要角色还未设计，建议先执行 `/design-characters {角色名}`
    - 准备就绪后执行 `/generate-video` 开始生成视频

## 注意事项

- 这是最核心的步骤，约需 1 + N + M 次 LLM 调用
- 10 分钟短片约 20-40 次 LLM 调用
- 三层拆解串行执行，不可并行
- 每层完成后可选择让 script-supervisor 审查
- script_breakdown.json 是后续所有步骤的核心输入
