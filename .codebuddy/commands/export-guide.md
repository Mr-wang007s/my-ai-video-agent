---
name: export-guide
description: "Step 5: 导出制作指南 — 从 script_breakdown.json 生成 Markdown + CSV 供人工在 Gemini/可灵/剪映操作"
---

## 前置条件

- 项目状态为 `script_broken`
- `projects/{project_id}/script_breakdown.json` 已存在

## 必须加载的 Skill

```
use_skill("export-render")
```

## Team 调度

**Spawn `export-render` Team** 进行质量审核和导出：

```
TeamCreate: export-render-{project_id}
Spawn:
  - post-supervisor (coordinator) — 协调审核流程、生成最终导出文件
  - structure-auditor (reviewer) — 校验三层嵌套结构完整性
  - prompt-auditor (reviewer) — 校验三版本 Prompt 规范（image/video/audio）
  - rhythm-auditor (reviewer) — 校验时长对齐、转场规则、情绪曲线
```

**协作流程**（parallel + review 模式）：
1. post-supervisor 读取 `script_breakdown.json`，分发给 3 个审核者
2. **3 个 auditor 并行审核**：
   - structure-auditor：三层嵌套完整性、CoT 字段齐全、Sub-Script/Scene/Shot 层级正确
   - prompt-auditor：image_prompt 英文且无角色名、video_prompt @Image 引用正确、audio_prompt 中文格式
   - rhythm-auditor：Duration 对齐 Seedance 档位、转场规则合规、情绪曲线连贯
3. post-supervisor 收集审核结果：
   - 全部通过 → 生成导出文件
   - 有问题 → 汇总问题清单，提示用户或自动修复
4. post-supervisor 生成导出文件：
   ```
   Write: projects/{project_id}/exports/storyboard_guide.md
   Write: projects/{project_id}/exports/storyboard_prompts.csv
   ```
5. TeamDelete 清理资源

## 执行步骤

1. **验证前置条件**：
   ```
   Read: projects/{project_id}/status.json
   ```
   确认状态为 `script_broken`。

2. **读取核心数据**：
   ```
   Read: projects/{project_id}/script_breakdown.json
   Read: projects/{project_id}/characters.json
   ```

3. **Spawn export-render Team** 执行审核和导出（见上方 Team 调度）

4. **更新状态**：
   ```
   Write: projects/{project_id}/status.json  ← {"status": "exported", "updated_at": "..."}
   ```

5. **向用户展示结果**：
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
- 所有数据通过文件系统读写，不依赖 MCP 或数据库
