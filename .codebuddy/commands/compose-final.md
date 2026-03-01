---
name: compose-final
description: "Step 6: 最终合成 — 视频拼接、字幕烧录、BGM 混合，输出成片"
---

## 前置条件

- 项目状态为 `generated`
- `projects/{project_id}/script_breakdown.json` 已存在
- `projects/{project_id}/video_manifest.json` 已存在
- `projects/{project_id}/videos/` 下有视频片段

## 执行步骤

1. **验证前置条件**：
   ```
   MCP tool: project_get(project_id)
   ```

2. **更新状态**：
   ```
   MCP tool: project_update_status(project_id, status="composing")
   ```

3. **构建合成配置**：
   - 从 `script_breakdown.json` 提取有序 Shot 列表
   - 从 `video_manifest.json` 映射 shot_id → video_path
   - 确定转场方式（同 Scene: cut, 跨 Scene: fade, 跨 Sub-Script: fade+黑屏）
   - 构建字幕列表（时间轴对齐）

4. **执行合成**：
   ```
   MCP tool: video_compose(config_json='<compose_config JSON>')
   ```

5. **验证产出**：成片文件存在、时长匹配、音频连续、字幕正确

6. **更新状态**：
   ```
   MCP tool: project_update_status(project_id, status="completed")
   MCP tool: generation_log(project_id, stage="compose", status="success")
   ```

7. **向用户展示结果**：成片路径、总时长、总镜头数、文件大小

## 注意事项

- 需要安装 FFmpeg
- 成片输出到 `projects/{project_id}/final/`
- 转场规则遵循 narrative-rhythm 规则
- 字幕样式：24px, 白色黑边，底部居中
