---
description: 漫剧流水线调度规则 — 定义每步应加载的 Skill 和 MCP tool
globs: "**"
alwaysApply: true
---

# 漫剧流水线调度规则

当用户要求制作漫剧、执行流水线步骤时，**必须按以下规则调度 Skill 和 MCP tool**。

## MCP Server

所有工具操作通过 `manga-agent` MCP Server（16 个 tools）执行，**不使用 bash 调用 python 脚本**。

## 步骤 → Skill → MCP Tool 映射

| 步骤 | 触发关键词 | 必须加载的 Skill | MCP Tools |
|------|-----------|-----------------|-----------|
| Step 1: 创建项目 | init-project, 创建项目 | — | `project_create`, `project_init_db` |
| Step 2: 导入剧本 | import-script, 导入剧本 | `manga-script` | `script_import`, `script_text` |
| Step 3a: 提取角色 | extract-characters, 提取角色 | `manga-script` | `character_save`, `project_update_status` |
| Step 3b: 设计角色 | design-characters, 设计角色 | `character-consistency` | `character_save`, `project_update_status` |
| Step 4: 分镜拆解 | break-script, 分镜 | `script-breakdown` + `storyboard-design` | `project_update_status`, `generation_log` |
| Step 5: 导出指南 | export-guide, 导出 | — | `export_storyboard_markdown`, `project_update_status` |

## 调度原则

1. **Skill 先行**：执行任何步骤前，先用 `use_skill` 加载对应 Skill 获取领域知识
2. **MCP 优先**：所有数据库操作和文件生成通过 MCP tool 完成，不用 bash
3. **CoT 强制**：Step 4 分镜拆解必须遵循 `cot-reasoning` 规则，输出 Internal Chain-of-Thought
4. **状态驱动**：每步完成后用 `project_update_status` 更新项目状态
5. **日志记录**：每次操作用 `generation_log` 记录

## 状态流转

```
draft → imported → characters_extracted → characters_designed → script_broken → exported
```

## 手动操作指引（导出后）

导出的制作指南文件用于以下手动操作：
- **图片生成**：复制 `image_prompt` 到 Gemini 3
- **视频生成**：复制 `video_prompt` 到可灵
- **最终合成**：在剪映中按 `audio_prompt` 配音，按顺序拼接视频
