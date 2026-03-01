---
name: export-guide
description: "Step 5: 导出制作指南 — 从 script_breakdown.json 生成 Markdown + CSV 供人工在 Gemini/可灵/剪映操作"
---

## 前置条件

- 项目状态为 `script_broken`
- `projects/{project_id}/script_breakdown.json` 已存在

## 执行步骤

1. **验证前置条件**：
   ```
   MCP tool: project_get(project_id)
   ```

2. **导出 Markdown 制作指南**：
   ```
   MCP tool: export_storyboard_markdown(project_id)
   ```
   产出：`projects/{project_id}/exports/storyboard_guide.md`

3. **导出 CSV Prompt 表格**：
   ```
   MCP tool: export_storyboard_csv(project_id)
   ```
   产出：`projects/{project_id}/exports/storyboard_prompts.csv`

4. **记录操作日志**：
   ```
   MCP tool: generation_log(project_id, stage="export", status="success")
   ```

5. **更新状态**：
   ```
   MCP tool: project_update_status(project_id, status="exported")
   ```

6. **向用户展示结果**：
   - 汇报总镜头数和预估时长
   - 展示导出文件路径
   - 提供使用说明

## 使用说明（告知用户）

### Gemini 图片生成
- 打开 `storyboard_guide.md` 或 `storyboard_prompts.csv`
- 复制每个镜头的 `image_prompt` 到 Gemini 3
- 将生成的图片保存到 `projects/{project_id}/images/shots/` 目录

### 可灵视频生成
- 复制 `video_prompt_clean` 列的内容到可灵
- 上传对应的关键帧图片（来自 Gemini 生成结果）
- 参考 `duration` 列设置视频时长

### 剪映最终合成
- 按 `shot_id` 顺序将视频导入剪映时间线
- 参考 `audio_prompt` 添加配音/音效/BGM
- 参考 `subtitles` 列添加字幕
- 参考 `transition` 列设置转场效果

## 注意事项

- 导出操作不调用任何外部 API
- CSV 使用 UTF-8 BOM 编码，可直接用 Excel 打开
- `video_prompt_clean` 已清理 @Image 引用语法，可直接复制使用
