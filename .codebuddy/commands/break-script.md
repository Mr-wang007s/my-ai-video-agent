---
name: break-script
description: "Step 4: 三层 CoT 分镜拆解 — MovieAgent 核心，Sub-Scripts → Scenes → Shots"
---

## 前置条件

- 项目状态为 `characters_extracted` 或 `characters_designing`
- `projects/{project_id}/script_synopsis.json` 已存在
- `projects/{project_id}/characters.json` 已存在

## 必须加载的 Skill

```
use_skill("script-breakdown")
use_skill("storyboard-design")
```

## 执行步骤

### Step 4a: Sub-Script 拆解（编剧 CoT）

1. 使用 script-breakdown skill 的 Layer 1 Prompt 模板
2. 强制输出 Internal Chain-of-Thought
3. 写入 `projects/{project_id}/script_breakdown.json` 根层级
4. 验证：Sub-Script 数量 ≤ 20，每个 Plot ≥ 50 词

### Step 4b: 场景规划（场景 CoT）

5. 使用 Layer 2 Prompt 模板，逐个 Sub-Script 循环调用
6. 每次独立上下文（不累积历史）
7. 嵌套写入 Scene Annotation

### Step 4c: 镜头创建（镜头 CoT）

8. 使用 Layer 3 Prompt 模板，双层循环：Sub-Script → Scene
9. 每个 Shot 包含完整字段（双版本描述、三版本 Prompt、边界框）
10. Duration 为 4/5/10/15 之一
11. 嵌套写入 Shot Annotation

### 最终汇总

12. **更新状态**：
    ```
    MCP tool: project_update_status(project_id, status="script_broken")
    MCP tool: generation_log(project_id, stage="breakdown", status="success")
    ```

13. **向用户展示概览**：总 Sub-Script/Scene/Shot 数、预估总时长、角色出场统计

14. **提示下一步**：`/generate-video`

## 注意事项

- 三层拆解由主对话直接执行 CoT 推理，每层独立上下文
- 遵循 `cot-reasoning` 规则，禁止跳过推理
- 约需 1 + N + M 次 LLM 推理调用
- `script_breakdown.json` 是后续所有步骤的核心输入
