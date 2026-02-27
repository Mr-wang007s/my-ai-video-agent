---
name: compose-final
description: "Step 6: 最终合成 — 视频拼接、字幕烧录、BGM 混合，输出成片"
---

## 前置条件

- 项目状态为 `generated`（已通过 `/generate-video` 完成视频生成）
- `projects/{project_id}/script_breakdown.json` 已存在（Shot 顺序 + 字幕）
- `projects/{project_id}/video_manifest.json` 已存在
- `projects/{project_id}/videos/` 下有视频片段

## 执行步骤

1. **验证前置条件**：
   ```bash
   python scripts/db_manager.py --action get_project --data '{"project_id": "{project_id}"}'
   ```
   确认状态为 `generated`。

2. **更新状态为 composing**：
   ```bash
   python scripts/db_manager.py --action update_status --data '{"project_id": "{project_id}", "status": "composing"}'
   ```

3. **Dispatch to editor agent**：

   ```
   Project: {project_id}
   Working directory: projects/{project_id}/

   Task: 将所有视频片段按 Sub-Script|Scene|Shot 顺序拼接，烧字幕，输出成片

   Input files:
   - projects/{project_id}/script_breakdown.json（提取有序 Shot 列表 + 字幕）
   - projects/{project_id}/video_manifest.json（视频文件映射）
   - projects/{project_id}/videos/（视频片段）
   - projects/{project_id}/audio/manifest.json（TTS override，如存在）

   Output files:
   - projects/{project_id}/final/{project_name}_final.mp4

   执行流程：
   1. 从 script_breakdown.json 提取有序 Shot 列表
   2. 从 video_manifest.json 映射 shot_id → video_path
   3. 确定转场方式（同 Scene: cut, 跨 Scene: fade, 跨 Sub-Script: fade+黑屏）
   4. 从 Subtitles 构建字幕列表
   5. 生成 compose_config.json
   6. 调用 video_compose.py 执行 FFmpeg 合成
   7. 验证输出文件
   ```

4. **验证产出**：
   - 成片文件存在且可播放
   - 时长与预期匹配
   - 音频连续
   - 字幕正确

5. **更新状态**：
   ```bash
   python scripts/db_manager.py --action update_status --data '{"project_id": "{project_id}", "status": "completed"}'
   ```

6. **向用户展示结果**：
   - 成片文件路径
   - 总时长
   - 总镜头数
   - 文件大小

## 注意事项

- 需要安装 FFmpeg
- 成片输出到 `projects/{project_id}/final/` 目录
- 转场规则遵循 narrative-rhythm 规则
- 字幕样式：24px, 白色黑边，底部居中
