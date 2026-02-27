---
name: generate-video
description: "Step 5: 生成视频片段 — 基于 script_breakdown.json 三层结构 + character_list 资产，逐镜头生成"
---

## 前置条件

- 项目状态为 `script_broken`（已通过 `/break-script` 完成分镜拆解）
- `projects/{project_id}/script_breakdown.json` 已存在
- `projects/{project_id}/characters.json` 已存在
- `projects/{project_id}/character_list/` 下有已设计角色的资产

## 执行步骤

1. **验证前置条件**：
   ```bash
   python scripts/db_manager.py --action get_project --data '{"project_id": "{project_id}"}'
   ```
   确认状态为 `script_broken`。

2. **更新状态为 generating**：
   ```bash
   python scripts/db_manager.py --action update_status --data '{"project_id": "{project_id}", "status": "generating"}'
   ```

3. **Dispatch to visual-artist agent**：

   ```
   Project: {project_id}
   Working directory: projects/{project_id}/

   Task: 遍历 script_breakdown.json 三层结构，逐镜头生成关键帧图片 + Seedance 2.0 视频

   Input files:
   - projects/{project_id}/script_breakdown.json（三层嵌套：Sub-Script → Scene → Shot）
   - projects/{project_id}/characters.json（角色清单 + 资产状态）
   - projects/{project_id}/character_list/（已设计角色的 best.png 参考图）

   Output files:
   - projects/{project_id}/images/shots/（每个 Shot 一张关键帧图片）
   - projects/{project_id}/videos/（每个 Shot 一个视频文件）
   - projects/{project_id}/video_manifest.json（视频清单）

   执行流程：
   1. 遍历 Sub-Script → Scene → Shot 三层结构
   2. 对每个 Shot：
      a. 使用 image_prompt 生成关键帧图片
      b. 构建 image_paths 数组（角色 best.png + 关键帧）
      c. 使用 video_prompt + audio_prompt 调用 Seedance 2.0
      d. 文件名格式：Sub-Script_N|Scene_N|Shot_N.mp4
   3. 汇总所有视频为 video_manifest.json

   要求：
   - 使用 seedance-video skill 和 character-consistency skill
   - 有资产角色必须用 multimodal 模式 + @Image 引用
   - 无资产角色使用 image_prompt 中的外观描述
   - 视频时长对齐 Seedance 档位（4/5/10/15s）
   - Seedance 日上限 50 次，注意控制调用量
   - 文件名排序即为正确的时间线顺序
   ```

4. **验证产出**：
   - 每个 Shot 有对应关键帧图片和视频文件
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

7. **提示下一步**：
   - 如有需要 TTS Override 的镜头，可先处理音频
   - 准备就绪后执行 `/compose-final` 合成最终成片

## 注意事项

- 这是最耗时的步骤，每个镜头约 2-5 分钟
- Seedance 日调用上限 50 次，大项目可能需要分多天
- 视频 URL 24h 有效，脚本已自动下载
- 如果某个镜头生成失败，会自动重试一次
- ARK_API_KEY 必须配置
