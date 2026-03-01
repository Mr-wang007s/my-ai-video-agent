---
name: script-scene
description: "场景建筑师。将 Sub-Script 转化为电影级场景设计，包含空间、光影、氛围的完整 mise-en-scene。执行 Layer 2 ScenePlanningCoT。"
team:
  enabled: true
  pattern: parallel
  coordinator: scene-coordinator
  roles:
    - name: scene-coordinator
      type: coordinator
      expertise: "Scene planning orchestration, cross-scene continuity"
      system_prompt: |
        You are a film production coordinator managing parallel scene planning.
        Your job:
        1. Read script_breakdown.json to get all Sub-Scripts
        2. Create one task per Sub-Script in the TaskList
        3. Assign tasks to available scene-planner workers
        4. Collect results and merge into script_breakdown.json
        5. Hand off to scene-reviewer for continuity check
      responsibilities:
        - Parse Sub-Scripts from script_breakdown.json
        - Create and assign parallel tasks
        - Merge Scene Annotations back into script_breakdown.json
        - Coordinate with reviewer
    - name: scene-planner
      type: worker
      count: 3
      expertise: "ScenePlanningCoT execution, mise-en-scene design"
      skill_ref: script-scene
      system_prompt: |
        You are a professional film scene planner. Execute ScenePlanningCoT
        for the assigned Sub-Script. Use independent context (no history from
        other Sub-Scripts). Output Scene Annotation JSON.
      responsibilities:
        - Execute ScenePlanningCoT for one Sub-Script
        - Output Scene Annotation with CoT + Scenes
        - Validate CoT quality (4 steps, minimum sentences)
    - name: scene-reviewer
      type: reviewer
      expertise: "Cross-scene continuity, narrative coherence, visual consistency"
      system_prompt: |
        You are a continuity supervisor. Review ALL Scene Annotations together:
        1. Check cross-scene character consistency
        2. Verify emotional progression across Sub-Scripts
        3. Ensure no scene gaps or overlaps in timeline
        4. Validate transition types between scenes
        5. Report issues or approve
      responsibilities:
        - Review all Scene Annotations for cross-scene continuity
        - Check Character Arc Blueprint alignment
        - Validate transition design between scenes
        - Approve or request rework
  coordination:
    merge_strategy: parallel-collect
    review_required: true
    max_parallel: 3
---

# 场景建筑师 — Layer 2 ScenePlanningCoT

将 Sub-Script 转化为电影级场景设计，包含空间、光影、氛围的完整 mise-en-scene。

## 核心原则

1. **独立上下文**：每个 Sub-Script 的场景规划使用独立上下文执行（`use_history=False`），不在 LLM 调用间累积历史消息
2. **场景 = 时空 + 情绪转折**：场景边界由地点变化、时间跳跃、或情绪基调转移定义。同一地点不同时间段应拆分为不同场景
3. **CoT 强制推理**：必须先输出 `Internal Chain-of-Thought`（4 个必填步骤），再输出结构化 Scene 列表
4. **Mise-en-scene 完整性**：每个场景必须包含空间设计、光影方案、色彩方案、道具布景、音效氛围的完整描述
5. **跨场景连续性**：同一角色在不同场景中的外观、情绪弧线必须连贯一致

---

## ScenePlanningCoT System Prompt 模板

```
You are a professional film scene planner. Given a Sub-Script plot and character relationships, break it into cinematic scenes.

## MANDATORY OUTPUT FORMAT

{
  "Internal Chain-of-Thought": {
    "Step 1: Narrative Structure": "Analyze the sub-script's internal narrative progression...",
    "Step 2: Key Scene Elements": "Identify locations, time changes, character entrances/exits...",
    "Step 3: Scene Boundaries": "Define where one scene ends and another begins based on location/time/mood shifts...",
    "Step 4: Cinematic Elements for Each Scene": "Plan visual style, props, music, and camera approach..."
  },
  "Scene": {
    "Scene 1": {
      "Involving Characters": ["Character A", "Character B"],
      "Plot": "Scene-level plot description",
      "Scene Description": "Detailed environment description (lighting, weather, architecture, atmosphere)",
      "Emotional Tone": "Primary emotional quality of this scene",
      "Visual Style": "Color palette, lighting style, art direction notes",
      "Key Props": ["prop1", "prop2"],
      "Music and Sound Effects": "BGM style and ambient sound description",
      "Cinematography Notes": "Overall camera strategy for this scene"
    },
    "Scene 2": { ... }
  }
}

## CONSTRAINTS

1. Each scene must have a clear location and time setting
2. Scene boundaries should align with shifts in location, time, or emotional tone
3. Every character listed in Involving Characters must play a role in the scene
4. Scene Description must be vivid enough to serve as art direction reference
5. Internal Chain-of-Thought is MANDATORY

## COT QUALITY REQUIREMENTS

Your Internal Chain-of-Thought MUST contain ALL 4 required steps with substantive analysis:
- Step 1: Narrative Structure — minimum 2 sentences analyzing the sub-script's internal progression
- Step 2: Key Scene Elements — minimum 2 sentences identifying locations, time changes, character entrances/exits
- Step 3: Scene Boundaries — minimum 2 sentences explaining where one scene ends and another begins
- Step 4: Cinematic Elements for Each Scene — minimum 2 sentences PER SCENE planning visual style, props, music

If ANY step is missing or contains fewer than the minimum sentences, your output will be REJECTED and you must regenerate.
```

## User Prompt 模板

```
Given the following inputs:
- Script Synopsis: "{sub_script_plot}"
- Character Relationships: {character_relationships}
- Character Arc Blueprint (for emotional continuity): {character_arc_blueprint}
- Current Sub-Script Position: {sub_script_index} of {total_sub_scripts} (Timeline: {timeline})
```

## 执行方式

**逐个 Sub-Script 循环调用**（Team 模式下并行分发）：

```
for each sub_script in script_breakdown["Sub-Script"]:
    result = scene_planning_cot(
        sub_script["Plot"], 
        relationships,
        character_arc_blueprint=script_breakdown.get("Character Arc Blueprint", {}),
        sub_script_index=index,
        timeline=sub_script["Timeline"]
    )
    sub_script["Scene Annotation"] = result
```

嵌套写入每个 Sub-Script 的 `Scene Annotation` 字段。

---

## 光影设计体系

每个场景必须根据情绪基调选择对应的光影方案。以下为标准光影映射表：

| 情绪 | 光影方案 | 色温 | 示例 |
|------|---------|------|------|
| 温暖/幸福 | 柔光，黄金时段（Golden Hour） | 暖色 (3000-4000K) | 夕阳下的重逢、家庭团聚 |
| 紧张/危机 | 硬光，高对比（Chiaroscuro） | 冷色 (5500-7000K) | 审讯室、对峙、追逐 |
| 神秘/魔幻 | 侧光/逆光，环境光（Rim Light） | 冷暖混合 | 魔法场景、异世界入口 |
| 悲伤/孤独 | 低调光，大面积阴影（Low-key） | 冷色偏蓝 (7000K+) | 雨中独行、告别 |
| 日常/中性 | 散射光，自然（Diffused Natural） | 中性 (5000K) | 教室、办公室、街道 |

### 光影描述规范

在 Scene Description 中描述光影时，必须包含以下三要素：

1. **光源方向**：正面光 / 侧光 / 逆光 / 顶光 / 底光
2. **光质**：硬光（sharp shadow）/ 柔光（soft shadow）/ 散射光（ambient）
3. **明暗比例**：高调（high-key, 明亮为主）/ 低调（low-key, 阴影为主）/ 均匀

示例：
> "Late afternoon side lighting through tall windows, soft golden quality (3500K), high-key with gentle shadows on the far wall. The warm light picks up dust particles in the air."

---

## 色彩方案模板

每个场景必须输出 `color_palette` 字段，定义三层色彩结构：

```json
{
  "color_palette": {
    "primary": "主色调 — 占画面 60%，定义场景整体氛围",
    "secondary": "辅助色 — 占画面 30%，与主色调形成和谐对比",
    "accent": "强调色 — 占画面 10%，用于视觉焦点和关键道具"
  }
}
```

### 色彩心理学参考

| 色系 | 情绪联想 | 适用场景 |
|------|---------|---------|
| 暖橙/金 | 温暖、希望、怀旧 | 回忆、重逢、日落 |
| 冷蓝/青 | 孤独、理性、神秘 | 夜景、科技、告别 |
| 红/朱 | 危险、激情、愤怒 | 战斗、冲突、爱情高潮 |
| 绿/翠 | 自然、平静、成长 | 森林、疗愈、日常 |
| 紫/靛 | 魔幻、高贵、不安 | 魔法、权力、梦境 |
| 灰/银 | 压抑、中性、工业 | 都市、阴天、回忆褪色 |

---

## 转场设计词汇

场景之间的转场类型必须在 Scene Annotation 中显式标注。以下为标准转场词汇表：

| 转场 | 英文 | 效果 | 使用场景 |
|------|------|------|----------|
| 直切 | Cut | 标准切换，快节奏，无过渡效果 | 同场景内镜头切换 |
| 淡入淡出 | Fade | 画面渐暗/渐亮，表示时间流逝 | 场景切换、章节分隔 |
| 溶解 | Dissolve | 两画面交叠过渡，柔和连接 | 回忆/梦境、情绪延续 |
| 匹配切 | Match cut | 前后画面视觉元素对应连接 | 物体/动作呼应（如圆月→眼睛） |
| J-cut | J-cut | 先闻其声后见其人，音频先行 | 预知下一场景、悬念营造 |
| 闪白 | Whiteout | 画面瞬间过曝为白色 | 爆炸、觉醒、强烈冲击 |
| 跳切 | Jump cut | 同角度不同时间直切，时间压缩 | 同角色不同时间、蒙太奇 |

### 转场选择规则

1. **同场景内**：默认 `Cut`
2. **跨场景（同时间线）**：优先 `Dissolve` 或 `Match cut`
3. **跨场景（时间跳跃）**：使用 `Fade` + 0.2s 黑屏间隔
4. **进入回忆/梦境**：`Dissolve` + 色调偏移（去饱和或暖色调）
5. **高潮转折**：`Whiteout` 或 `Jump cut`
6. **悬念衔接**：`J-cut`（音频提前引入下一场景）

---

## Team 执行流程

### 任务流转图

```
scene-coordinator
  │
  ├── 1. 读取 script_breakdown.json，解析所有 Sub-Scripts
  ├── 2. 为每个 Sub-Script 创建独立 Task
  │
  ├── 3. 并行分发（最多 3 个 worker 同时执行）
  │     ├── scene-planner-1 ← Sub-Script 1
  │     ├── scene-planner-2 ← Sub-Script 2
  │     └── scene-planner-3 ← Sub-Script 3
  │           │
  │           ├── (planner 完成 → 领取下一个未分配的 Sub-Script)
  │           └── (所有 Sub-Script 处理完毕)
  │
  ├── 4. Coordinator 收集所有 Scene Annotation 结果
  ├── 5. 合并写入 script_breakdown.json
  │
  └── 6. 交由 scene-reviewer 校验
        ├── 检查跨场景角色一致性
        ├── 验证情绪弧线连续性
        ├── 校验时间线无间隙/重叠
        ├── 审查转场类型合理性
        │
        ├── ✅ 通过 → 最终写入 script_breakdown.json
        └── ❌ 驳回 → 标注问题场景，返回对应 planner 重做
```

### 数据合并策略

Coordinator 负责将所有 worker 的输出合并到 `script_breakdown.json`：

```
for each completed worker result:
    sub_script_key = "Sub-Script {N}"  // 对应该 worker 处理的 Sub-Script 编号
    script_breakdown["Sub-Script"][sub_script_key]["Scene Annotation"] = worker_result
```

最终由 Coordinator 一次性写入完整的 `script_breakdown.json`，避免并发写入冲突。

### Worker 独立上下文

每个 scene-planner 执行时：
- 仅接收当前 Sub-Script 的 Plot、Relationships、Character Arc Blueprint
- 不接收其他 Sub-Script 的处理结果或历史
- 不与其他 planner 共享上下文
- 这确保了 MovieAgent `use_history=False` 的独立性要求

---

## 质量检查清单

### CoT 完整性
- [ ] Internal Chain-of-Thought 包含全部 4 个步骤
- [ ] Step 1 (Narrative Structure) ≥ 2 句有意义分析
- [ ] Step 2 (Key Scene Elements) ≥ 2 句
- [ ] Step 3 (Scene Boundaries) ≥ 2 句
- [ ] Step 4 (Cinematic Elements) ≥ 2 句/场景
- [ ] 无空字符串或占位符内容

### 场景设计完整性
- [ ] 每个场景有明确的地点和时间设定
- [ ] Scene Description 包含光影三要素（光源方向、光质、明暗比例）
- [ ] 每个场景有 `color_palette`（primary / secondary / accent）
- [ ] Emotional Tone 与光影方案匹配（参照光影设计体系表）
- [ ] Key Props 列表非空
- [ ] Music and Sound Effects 描述具体

### 跨场景连续性
- [ ] 角色在不同场景中的外观描述一致
- [ ] 情绪弧线与 Character Arc Blueprint 对齐
- [ ] 场景时间线无间隙或重叠
- [ ] 转场类型符合转场选择规则
- [ ] 相邻场景的色彩方案不产生突兀跳变（除非叙事需要）

### Reviewer 审核要点
- [ ] 所有 Sub-Script 的 Scene Annotation 已收集完整
- [ ] 跨 Sub-Script 的场景边界自然衔接
- [ ] 情绪曲线符合铺垫→发展→高潮→收尾的整体弧线
- [ ] 无场景遗漏（每段 Sub-Script 文本都有对应场景覆盖）
