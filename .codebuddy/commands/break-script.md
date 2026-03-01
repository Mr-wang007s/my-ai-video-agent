---
name: break-script
description: "Step 4: 三层 CoT 分镜拆解 — MovieAgent 核心，Sub-Scripts → Scenes → Shots"
---

## 前置条件

- 项目状态为 `characters_extracted` 或 `characters_designed`
- `projects/{project_id}/script_synopsis.json` 已存在
- `projects/{project_id}/characters.json` 已存在

## 必须加载的 Skill

```
use_skill("script-parser")      # Layer 1: 编剧拆解
use_skill("script-scene")       # Layer 2: 场景规划（with Team）
use_skill("shot-director")      # Layer 3: 镜头创建（with Team）
use_skill("shot-rhythm")        # 时长校验
```

## 执行步骤

### Step 4a: Sub-Script 拆解（编剧 CoT） — 单 Agent

**无 Team 调度**，主对话直接执行 Layer 1 screenwriterCoT。

1. 读取输入：
   ```
   Read: projects/{project_id}/script_synopsis.json
   Read: projects/{project_id}/characters.json
   Read: projects/{project_id}/raw_script.txt
   ```
2. 使用 script-parser skill 的 Layer 1 Prompt 模板
3. 强制输出 Internal Chain-of-Thought（5 个必填步骤）
4. 写入 `projects/{project_id}/script_breakdown.json` 根层级
5. 验证：Sub-Script 数量 ≤ 20，每个 Plot ≥ 50 词

### Step 4b: 场景规划（场景 CoT） — script-scene Team

**Spawn `script-scene` Team** 并行处理所有 Sub-Script：

```
TeamCreate: script-scene-{project_id}
Spawn:
  - scene-coordinator (coordinator) — 任务分发、结果合并
  - scene-planner x3 (worker) — 并行处理 Sub-Script 的场景拆解
  - scene-reviewer (reviewer) — 跨场景连续性校验
```

**协作流程**（parallel + review 模式）：
1. scene-coordinator 读取 Layer 1 输出，将 Sub-Scripts 均分给 3 个 scene-planner
2. 每个 scene-planner 独立处理分配到的 Sub-Scripts：
   - 使用 script-scene skill 的 Layer 2 Prompt 模板
   - 每次独立上下文（不累积历史）
   - 强制输出 Internal Chain-of-Thought（4 个必填步骤）
3. scene-coordinator 收集所有 planner 的输出
4. scene-reviewer 验证：
   - 跨场景连续性（时间线、角色状态）
   - CoT 完整性校验（4 步齐全、内容非空）
   - 场景边界合理性
5. scene-coordinator 合并结果，嵌套写入 Scene Annotation
6. TeamDelete 清理资源

### Step 4c: 镜头创建（镜头 CoT） — shot-director Team

**Spawn `shot-director` Team** 处理每个 Scene 的镜头拆解：

```
TeamCreate: shot-director-{project_id}
Spawn:
  - shot-coordinator (coordinator) — 按 Scene 编排处理顺序
  - shot-designer (worker) — 创建镜头骨架（双版本描述、角色布局、边界框）
  - image-prompter (specialist) — 生成 image_prompt（英文，无角色名）
  - video-prompter (specialist) — 生成 video_prompt（含 @Image 引用）
  - audio-prompter (specialist) — 生成 audio_prompt（中文，含对白/音效/BGM）
  - rhythm-checker (specialist) — 校验镜头时长（Duration 对齐 4/5/10/15s 档位）
  - shot-reviewer (reviewer) — 最终质量审核
```

**协作流程**（specialization + multi-modal + review 模式）：
1. shot-coordinator 遍历所有 Scene，逐 Scene 编排处理：
2. 对每个 Scene：
   a. **shot-designer** 创建镜头骨架：
      - 使用 shot-director skill 的 Layer 3 Prompt 模板
      - 独立上下文，强制输出 Internal Chain-of-Thought（6 个必填步骤）
      - 输出：Involving Characters + 边界框 + Plot/Visual Description + Coarse Plot + Shot Type + Camera Movement
   b. **3 个 Prompt 专家并行工作**（multi-modal 模式）：
      - image-prompter：基于 Coarse Plot 生成英文 image_prompt（禁止含角色名）
      - video-prompter：基于 Plot/Visual Description 生成 video_prompt（含 @Image 引用）
      - audio-prompter：基于对白和情绪生成中文 audio_prompt
   c. **rhythm-checker** 校验 Duration：
      - 按对白时长公式计算最低时长
      - 向上对齐到 Seedance 档位（4/5/10/15）
      - 超长对白强制拆分
   d. **shot-reviewer** 最终审核：
      - CoT 完整性（6 步齐全）
      - image_prompt 不含角色名
      - video_prompt @Image 引用数量正确
      - Duration 与对白/动作匹配
3. shot-coordinator 合并所有 Scene 的 Shot 结果，嵌套写入 Shot Annotation
4. TeamDelete 清理资源

### 最终汇总

12. **更新状态**：
    ```
    Write: projects/{project_id}/status.json  ← {"status": "script_broken", "updated_at": "..."}
    ```

13. **向用户展示概览**：总 Sub-Script/Scene/Shot 数、预估总时长、角色出场统计

14. **提示下一步**：`/export-guide`

## 注意事项

- 三层拆解中每层使用独立上下文（对应 MovieAgent 的 `use_history=False`）
- 遵循 `cot-reasoning` 规则，禁止跳过推理
- Layer 2 和 Layer 3 通过 Team 并行加速处理
- `script_breakdown.json` 是后续导出的核心数据来源
- 所有数据通过文件系统读写，不依赖 MCP 或数据库
