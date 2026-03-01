# 质量标准

## CoT 推理质量（核心）

### 三层嵌套 JSON 结构校验
- [ ] script_breakdown.json 包含 Relationships + Internal Chain-of-Thought + Sub-Script 三个顶层键
- [ ] 每个 Sub-Script 包含 Scene Annotation（含 CoT + Scene 列表）
- [ ] 每个 Scene 包含 Shot Annotation（含 CoT + Shot 列表）
- [ ] 三层嵌套的层级关系正确

### CoT 推理完整性
- [ ] Layer 1 CoT 包含 5 个必填步骤
- [ ] Layer 2 CoT 包含 4 个必填步骤
- [ ] Layer 3 CoT 包含 6 个必填步骤
- [ ] 每个步骤有实质性分析内容（非空字符串）
- 遵循 `.codebuddy/rules/cot-reasoning.md` 的完整规则

## Prompt 规范

### image_prompt（英文，用于 Gemini 等平台文生图）
- 必须使用英文
- 必须包含风格前缀（如 `manga style,` `anime style,`）
- **禁止**包含角色名（使用外观描述替代）
- 必须包含角色外观描述（来自 `<TOK>` 描述去掉前缀）
- 使用 negative prompt 排除常见缺陷

### video_prompt（用于可灵等平台图生视频）
- 重点描述动态变化和运镜
- 可以使用角色名
- 避免重复描述图片中已有的静态信息

### audio_prompt（中文，配音/音效参考）
- 使用中文描述
- 包含环境音效 + 动作音效 + 对白（含性别/语气） + BGM
- 对白格式：`{性别/年龄}{语气}说：'{台词}'`

### Negative Prompt 标准模板
```
low quality, blurry, deformed, extra fingers, bad anatomy, disfigured, poorly drawn face, mutation, mutated, ugly, watermark, text
```

## 画面一致性（用户手动生成时参考）

- 同一场景内，背景风格、光照方向、色调应保持一致
- 角色外观通过 `<TOK>` 描述 + `image_prompt` 中的完整外观描述保障一致性
- 同一话/集内，整体画风不应出现显著跳变
- 建议在 Gemini 生成时使用相同的风格前缀
