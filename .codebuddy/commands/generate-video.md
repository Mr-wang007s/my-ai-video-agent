---
name: generate-video
description: "Step 5: 生成视频片段 — 基于 script_breakdown.json 三层结构 + character_list 资产，逐镜头生成"
---

## 前置条件

- 项目状态为 `script_broken`
- `projects/{project_id}/script_breakdown.json` 已存在
- `projects/{project_id}/character_list/` 下有已设计角色的资产

## 必须加载的 Skill

```
use_skill("seedance-video")
use_skill("character-consistency")
```

## 执行步骤

1. **验证前置条件**：
   ```
   MCP tool: project_get(project_id)
   ```

2. **更新状态**：
   ```
   MCP tool: project_update_status(project_id, status="generating")
   ```

3. **初始化镜头状态（断点续传）**：

   首次执行时，解析 `script_breakdown.json` 生成镜头列表并批量初始化：
   ```
   MCP tool: shot_batch_init(project_id, shots_json='[{"shot_id": "S1_Sc1_Shot1", ...}, ...]')
   ```

   续传时，获取未完成镜头列表：
   ```
   MCP tool: shot_list_pending(project_id)
   ```

4. **遍历三层结构，逐镜头生成（支持断点续传）**：

   对每个 Shot：

   a. **检查状态**：如果 `shot_list_pending` 返回该镜头 status 为 success，跳过
   
   b. **检查重试次数**：如果 attempts >= 3，标记为 permanently_failed，跳过
   
   c. 标记开始生成：
   ```
   MCP tool: shot_update_status(project_id, shot_id, status="generating")
   ```

   d. 使用 image_prompt 生成关键帧图片：
   ```
   MCP tool: image_generate(prompt="{shot.image_prompt}", output_dir="projects/{project_id}/images/shots", engine="dalle")
   ```

   e. 使用 video_prompt + audio_prompt 调用 Seedance 2.0：
   ```
   MCP tool: video_generate(prompt="{shot.video_prompt}", output_dir="projects/{project_id}/videos", mode="{seedance_mode}", duration={Duration}, image_paths='[...]', audio_prompt="{shot.audio_prompt}", shot_id="{shot_id}")
   ```

   f. **成功**：更新状态 + 注册资产：
   ```
   MCP tool: shot_update_status(project_id, shot_id, status="success", video_path="videos/{shot_id}.mp4")
   MCP tool: asset_save(project_id, asset_type="video", name="{shot_id}", file_path="videos/{shot_id}.mp4")
   ```

   g. **失败**：记录错误，继续下一个镜头：
   ```
   MCP tool: shot_update_status(project_id, shot_id, status="failed", error="{error_message}")
   ```

5. **写入 video_manifest.json**

6. **更新状态**：
   ```
   MCP tool: project_update_status(project_id, status="generated")
   MCP tool: generation_log(project_id, stage="video", status="success")
   ```

7. **向用户展示结果**并提示下一步：`/compose-final`

## 注意事项

- 支持断点续传：中断后重新执行会自动跳过已成功的镜头
- 单镜头连续失败 3 次后标记为 permanently_failed，不再重试
- 最耗时步骤，每镜头约 2-5 分钟
- Seedance 日调用上限 50 次
- 有资产角色必须用 multimodal 模式 + @Image 引用
- 视频 URL 24h 有效，脚本已自动下载
