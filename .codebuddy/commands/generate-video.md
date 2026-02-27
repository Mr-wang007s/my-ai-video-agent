---
name: generate-video
description: "Step 5: 生成视频片段 — 基于分镜+角色参考图，文生图+图生视频"
---

## 前置条件

- 项目状态为 `designed`（已通过 `/design-characters` 完成角色设计）
- `projects/{project_id}/storyboard.json` 已存在
- `projects/{project_id}/characters.json` 已存在（含参考图路径）

## 执行步骤

1. **验证前置条件**：
   ```bash
   python scripts/db_manager.py --action get_project --data '{"project_id": "{project_id}"}'
   ```
   确认状态为 `designed`。

2. **更新状态为 generating**：
   ```bash
   python scripts/db_manager.py --action update_status --data '{"project_id": "{project_id}", "status": "generating"}'
   ```

3. **Dispatch to Visual-Artist Agent**：通过 Task 工具调用 visual-artist 子 Agent：

   ```
   Project: {project_id}
   Working directory: projects/{project_id}/

   Task: 基于分镜表和角色参考图，为每个镜头生成分镜图和视频片段。

   Input files:
   - projects/{project_id}/storyboard.json（分镜表）
   - projects/{project_id}/characters.json（角色数据 + 参考图路径）
   - projects/{project_id}/script.json（剧本，用于对白/情绪参考）

   Output files:
   - projects/{project_id}/images/shots/（每镜头一张分镜图）
   - projects/{project_id}/videos/（每镜头一个视频文件）
   - projects/{project_id}/video_manifest.json（视频清单）

   执行流程：
   1. 遍历 storyboard.json 中的每个 shot
   2. 为每个 shot 生成分镜图：
      - 将角色 prompt_template 嵌入到 shot 的 prompt 中
      - 调用 image_generate.py 生成分镜图，存入 images/shots/
   3. 为每个 shot 生成视频片段：
      - 根据 seedance_mode 选择模式（i2v 或 multimodal）
      - 传入分镜图作为首帧
      - 传入角色参考图作为一致性引用（multimodal 模式）
      - 在 prompt 中使用 @Image1 @Image2 引用
      - 传入 audio_prompt 实现音视频联合生成
      - 调用 seedance_generate.py 生成视频
   4. 为每个生成记录 log_generation
   5. 汇总所有视频为 video_manifest.json

   要求：
   - 使用 seedance-video skill 和 character-consistency skill
   - 角色出现的镜头必须使用 multimodal 模式 + @引用
   - 所有镜头必须有 audio_prompt
   - 视频时长对齐 Seedance 档位（4/5/10/15s）
   - Seedance 日上限 50 次，注意控制调用量
   ```

4. **验证产出**：
   - 每个 shot 都有对应视频文件
   - 视频文件 > 0 bytes
   - video_manifest.json 记录完整

5. **更新状态**：
   ```bash
   python scripts/db_manager.py --action update_status --data '{"project_id": "{project_id}", "status": "generated"}'
   ```

6. **向用户展示结果**：
   - 生成的视频片段列表（shot_id, 时长, 文件大小）
   - 总时长
   - 需要 TTS Override 的镜头数
   - API 调用成本估算

## video_manifest.json 格式

```json
{
  "project_id": "xxx",
  "videos": [
    {
      "shot_id": "SH001",
      "scene_id": "S01",
      "file_path": "projects/{project_id}/videos/SH001_seedance_xxx.mp4",
      "image_path": "projects/{project_id}/images/shots/SH001.png",
      "duration": 5,
      "has_audio": true,
      "needs_tts_override": false,
      "prompt": "...",
      "audio_prompt": "..."
    }
  ],
  "total_duration": 45,
  "total_shots": 10,
  "tts_override_count": 0
}
```

## 注意事项

- 这是最耗时的步骤，每个镜头约 2-5 分钟
- Seedance 日调用上限 50 次，大项目可能需要分多天
- 视频 URL 24h 有效，脚本已自动下载
- 如果某个镜头生成失败，会自动重试一次
- ARK_API_KEY 必须配置
