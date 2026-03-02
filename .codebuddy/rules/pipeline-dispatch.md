---
description: 漫剧流水线调度规则 — 定义每步应加载的 Skill、Team 调度和状态机
globs: "**"
alwaysApply: true
---

# 漫剧流水线调度规则

当用户要求制作漫剧、执行流水线步骤时，**必须按以下规则调度 Skill 和 Agent Team**。

## 步骤 → Skill → Team 映射

| 步骤 | 触发关键词 | 加载的 Skill | Team 调度 |
|------|-----------|-------------|-----------|
| Step 1: 创建项目 | `/init-project`, 创建项目 | — | 无 Team（纯文件操作：创建项目目录 + JSON） |
| Step 2: 导入剧本 | `/import-script`, 导入剧本 | `script-parser` | 无 Team（单次解析） |
| Step 3a: 提取角色 | `/extract-characters`, 提取角色 | `script-parser` + `character-design` + `character-acting` | `character-acting` Team（casting-director 协调） |
| Step 3b: 设计角色 | `/design-characters`, 设计角色 | `character-design` | 无 Team（逐角色交互） |
| Step 4a: Layer 1 | `/break-script` (自动) | `script-parser` | 无 Team（单次 screenwriterCoT） |
| Step 4b: Layer 2 | `/break-script` (自动) | `script-scene` + `shot-rhythm` | **`script-scene` Team**（scene-coordinator + planner x3 + reviewer） |
| Step 4c: Layer 3 | `/break-script` (自动) | `shot-director` + `prompt-image` + `prompt-video` + `prompt-audio` + `character-acting` + `shot-rhythm` | **`shot-director` Team**（7 角色，全部 4 种协作模式） |
| Step 5: 导出指南 | `/export-guide`, 导出 | `export-render` | **`export-render` Team**（post-supervisor + 3 auditors） |

## 调度原则

1. **Skill 先行**：执行任何步骤前，先用 `use_skill()` 加载对应 Skill 获取领域知识
2. **Team 按需**：仅在 Skill 定义了 `team.enabled: true` 时 spawn Agent Team
3. **CoT 强制**：Step 4 三层拆解必须遵循 `cot-reasoning` 规则，输出 Internal Chain-of-Thought
4. **状态驱动**：每步完成后更新项目状态文件 `projects/{id}/status.json`
5. **文件系统优先**：数据 I/O 使用 CodeBuddy 原生工具（Read/Write/Bash），不依赖 MCP

## Team 调度流程

当步骤映射到 Team 时，执行以下流程：

```
1. use_skill("{skill-name}") → 加载 Skill 领域知识
2. 读取 SKILL.md 中的 team 定义 → 获取角色配置
3. TeamCreate(team_name="{skill-name}-{project_id}")
4. 按 team.roles[] spawn teammates（Task tool with name + team_name）
5. Coordinator 通过 TaskList 协调工作
6. 所有任务完成 → Coordinator shutdown teammates
7. TeamDelete → 清理资源
8. 更新项目状态
```

### Team 角色类型

| 类型 | 角色 | 数量 | 职责 |
|------|------|------|------|
| `coordinator` | 协调者 | 1 | 任务分发、结果合并、质量关卡 |
| `worker` | 工作者 | N (可并行) | 执行具体 CoT 推理任务 |
| `specialist` | 专家 | 1+ | 特定模态/领域的专精处理 |
| `reviewer` | 审核者 | 1+ | 质量校验、一致性检查 |

### 协作模式

| 模式 | 描述 | 适用场景 |
|------|------|---------|
| `parallel` | 同任务分发给 N 个 worker 并行 | Layer 2 逐 Sub-Script 处理 |
| `specialization` | 不同专家处理同一内容的不同维度 | Layer 3 图/视/音 Prompt 生成 |
| `review` | 生成→审核链 | 每层输出的质量校验 |
| `multi-modal` | 多模态专家并行协作 | Layer 3 三版本 Prompt 同时生成 |

## 状态流转

```
draft → imported → characters_extracted → characters_designed → script_broken → exported
```

每个状态转换由对应步骤的 Coordinator（或单 agent）在完成时写入 `projects/{id}/status.json`。

### 状态验证前置条件

每个步骤执行前**必须**校验项目当前状态，防止跳步或重复执行：

| 步骤 | 要求的当前状态 | 目标状态 | 前置文件校验 |
|------|-------------|---------|------------|
| Step 1: /init-project | （无项目） | `draft` | — |
| Step 2: /import-script | `draft` | `imported` | `projects/{id}/` 目录存在 |
| Step 3a: /extract-characters | `imported` | `characters_extracted` | `raw_script.txt` + `script_synopsis.json` 存在 |
| Step 3b: /design-characters | `characters_extracted` | `characters_designed` | `characters.json` 存在且含 ≥ 1 个角色 |
| Step 4: /break-script | `characters_designed` | `script_broken` | `characters.json` 中所有主角 `design_status == "designed"`，`character_list/` 中有对应 `best.txt` |
| Step 5: /export-guide | `script_broken` | `exported` | `script_breakdown.json` 存在且三层结构完整 |

**校验失败处理**：
- 状态不匹配 → 报告当前状态，建议先执行前置步骤
- 前置文件缺失 → 报告缺失的文件，建议重新执行产生该文件的步骤
- **禁止**跳过中间步骤直接执行后续步骤

## 手动操作指引（导出后）

导出的制作指南文件用于以下手动操作：
- **图片生成**：复制 `image_prompt` 到 Gemini / DALL-E / SD
- **视频生成**：复制 `video_prompt` 到可灵 / Seedance
- **最终合成**：在剪映中按 `audio_prompt` 配音，按顺序拼接视频
