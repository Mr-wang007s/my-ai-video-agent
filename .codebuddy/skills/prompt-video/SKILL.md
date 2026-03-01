---
name: prompt-video
description: "视频提示词工程。为视频生成平台（可灵 / Seedance / Runway）构造高质量 video_prompt，管理 @Image 引用和 seedance_mode 选择。"
team:
  enabled: true
  pattern: review
  coordinator: motion-director
  roles:
    - name: motion-director
      type: coordinator
      expertise: "Video prompt engineering, dynamic description"
      system_prompt: |
        Generate video_prompts following prompt-video Skill rules.
        Focus on dynamic changes, camera movement, character actions.
        Submit to reference-validator for @Image audit.
      responsibilities:
        - Generate video_prompt with @Image references
        - Plan image_paths arrays
        - Determine seedance_mode
    - name: reference-validator
      type: reviewer
      expertise: "@Image reference validation, action continuity"
      system_prompt: |
        Validate video_prompts:
        1. Count @ImageN references == len(image_paths)
        2. Characters with designed assets MUST have @Image refs
        3. Last @Image is always the keyframe (作为首帧)
        4. Action continuity: previous shot end state matches this shot start
        5. No static description of what is already in the image
        Report violations with specific shot IDs and fixes.
      responsibilities:
        - "@Image reference count validation"
        - Action continuity checking
        - Static description detection
  coordination:
    merge_strategy: sequential-pipeline
    review_required: true
---

# 视频提示词工程 (prompt-video)

为视频生成平台（可灵 / Seedance / Runway / Pika）构造高质量 `video_prompt`，管理 `@Image` 引用、`seedance_mode` 选择和镜头间动作连续性。

## 1. video_prompt 构造公式

每个 `video_prompt` 按以下结构组装：

```
{character_reference_images}, {keyframe_image}, {dynamic_action}, {camera_movement}, {atmosphere_change}
```

| 组件 | 说明 | 示例 |
|------|------|------|
| `character_reference_images` | 角色参考图的 @Image 引用 | `@Image1 作为Elsa外观参考。` |
| `keyframe_image` | 首帧图（始终是最后一个 @Image） | `@Image2 作为首帧，` |
| `dynamic_action` | 角色的动态动作描述 | `角色微微抬头，冰晶从手中飘出` |
| `camera_movement` | 镜头运动 | `镜头缓慢推近` |
| `atmosphere_change` | 氛围/光影变化（可选） | `光线逐渐变暖` |

### 核心原则

- **只描述动态变化**：静态信息已在首帧图片中，video_prompt 不要重复描述
- **动作优先**：重点是角色做什么、场景如何变化，而非画面看起来像什么
- **简洁有力**：避免冗长描述，每个动作用精确词汇

**正确写法**（聚焦动态）：
```
@Image1 作为Elsa外观参考。@Image2 作为首帧，角色缓缓抬起右手，冰晶从指尖迸发向天空扩散，镜头从中景推至面部特写
```

**错误写法**（重复静态描述）：
```
@Image1 作为Elsa外观参考。@Image2 作为首帧，一个金发女人穿着紫色裙子站在城堡阳台上看着远方
```

## 2. @Image 引用规范

### 编号规则（强制）

1. **角色参考图在前**，按 `image_paths` 数组顺序依次编号：`@Image1`, `@Image2`, ...
2. **首帧图（keyframe）永远是最后一个 @Image**
3. 首帧引用格式固定为：`@ImageN 作为首帧，{动作描述}`

### 引用模板

```
"@Image1 作为{角色A名}外观参考。@Image2 作为{角色B名}外观参考。@ImageN 作为首帧，{dynamic_action}, {camera_movement}"
```

### 校验规则（强制执行）

| 规则 | 要求 |
|------|------|
| 引用数量 | `@ImageN` 引用总数 **必须等于** `image_paths` 数组长度 |
| 已设计角色 | 有 `character_list/{Name}/best.png` 资产的角色 **必须** 有 `@Image` 引用 |
| 未设计角色 | 无资产的角色 **仅用文字描述**，不添加 `@Image` 引用 |
| 首帧位置 | 最后一个 `@Image` **必须是** 首帧（`作为首帧`） |
| 顺序一致 | `@Image` 编号顺序 **必须与** `image_paths` 数组顺序完全对应 |

### 完整示例

#### 示例 1：单角色（Elsa）

```
image_paths: [
  "character_list/Elsa/best.png",
  "images/shots/S1_Sc1_Shot1.png"
]

video_prompt: "@Image1 作为Elsa外观参考。@Image2 作为首帧，角色微微抬头，冰晶从手中飘出，镜头缓慢推近"
```

- @Image1 → `character_list/Elsa/best.png`（角色参考图）
- @Image2 → `images/shots/S1_Sc1_Shot1.png`（首帧图，最后一个）

#### 示例 2：双角色（Elsa + Anna）

```
image_paths: [
  "character_list/Elsa/best.png",
  "character_list/Anna/best.png",
  "images/shots/S1_Sc1_Shot2.png"
]

video_prompt: "@Image1 作为Elsa外观参考。@Image2 作为Anna外观参考。@Image3 作为首帧，两人面对面交谈，Elsa表情困惑"
```

- @Image1 → Elsa 参考图
- @Image2 → Anna 参考图
- @Image3 → 首帧图（最后一个）

#### 示例 3：纯场景（无角色参考图）

```
image_paths: [
  "images/shots/S1_Sc2_Shot2.png"
]

video_prompt: "@Image1 作为首帧，鸟瞰城市灯火依次熄灭，镜头缓慢上升"
```

- @Image1 → 首帧图（唯一图片，也是最后一个）
- 无角色参考图，纯场景动态

## 3. seedance_mode 决策树

根据镜头涉及的角色和图片资产，选择正确的 Seedance 模式：

```
镜头涉及角色是否有已设计资产（character_list/{Name}/best.png）？
│
├─ 是（≥1 个已设计角色参与） → multimodal
│   └─ image_paths = [角色1/best.png, ..., 角色N/best.png, keyframe.png]
│   └─ video_prompt 包含 @Image 引用
│
├─ 否，但有首帧图（场景图/空镜） → i2v
│   └─ image_paths = [keyframe.png]
│   └─ video_prompt = "@Image1 作为首帧，{动态描述}"
│
└─ 无任何图片 → t2v
    └─ image_paths = []
    └─ video_prompt = 完整的文生视频描述（同时包含画面内容和动态变化）
```

### 模式对照表

| 条件 | seedance_mode | image_paths 内容 | video_prompt 特点 |
|------|--------------|-----------------|------------------|
| ≥1 已设计角色 | `multimodal` | 角色参考图 + 首帧图 | @Image 引用 + 动态描述 |
| 仅场景图/空镜 | `i2v` | 仅首帧图 | @Image1 作为首帧 + 动态描述 |
| 无任何图片 | `t2v` | 空数组 | 完整场景描述 + 动态描述 |

## 4. 动态描述词汇表

video_prompt 的核心是**动态描述**。使用细化的动作词汇替代笼统描述，让生成结果更精准：

### 面部动态

| 基础动作 | 细化描述 |
|---------|---------|
| 睁眼 | 缓缓睁开双眼，瞳孔逐渐聚焦 |
| 微笑 | 嘴角缓缓上扬，眉眼间流露出温暖 |
| 皱眉 | 眉头微微蹙起，眼神中透出疑惑 |
| 流泪 | 泪水在眼眶中打转，沿脸颊缓缓滑落 |
| 惊讶 | 双眼猛然睁大，嘴唇微微张开 |
| 愤怒 | 眉头紧锁，嘴角下沉，眼神变得凌厉 |

### 手部动态

| 基础动作 | 细化描述 |
|---------|---------|
| 伸手 | 右手缓缓抬起，手指微微张开向前探出 |
| 握拳 | 五指缓慢收紧攥成拳头，指节发白 |
| 触碰 | 手指轻轻触碰物体表面，带有试探感 |
| 挥手 | 手臂抬起，手掌左右轻摇做告别姿态 |
| 施法 | 双手向前推出，能量光芒从掌心迸发 |

### 身体动态

| 基础动作 | 细化描述 |
|---------|---------|
| 转身 | 身体以腰部为轴缓慢旋转180度 |
| 起身 | 双手撑住椅臂缓缓站起，身体挺直 |
| 后退 | 身体微微向后倾斜，脚步缓缓后移 |
| 奔跑 | 双臂摆动，步幅加大，衣摆随风飘动 |
| 倒下 | 身体失去平衡，缓慢向一侧倾倒 |

### 环境动态

| 基础动作 | 细化描述 |
|---------|---------|
| 风吹 | 微风拂过，发丝和裙摆向右轻轻飘动 |
| 花落 | 花瓣从枝头脱落，旋转着缓缓飘向地面 |
| 雨落 | 雨滴从天空坠落，在地面溅起细小水花 |
| 烟雾 | 淡淡烟雾从地面缓缓升起，逐渐弥散开来 |
| 水流 | 溪水沿岩石表面蜿蜒流淌，泛起细碎波光 |

### 光影动态

| 基础动作 | 细化描述 |
|---------|---------|
| 日出 | 暖光从画面右侧逐渐蔓延，阴影退缩 |
| 日落 | 天空色调由橙转紫，光线逐渐变暗 |
| 闪电 | 白光突然闪亮照亮整个画面，随即恢复暗色 |
| 火焰 | 火光在画面中跳动，投射出摇曳的光影 |
| 魔法光效 | 蓝色/紫色光芒从中心向四周扩散，粒子飞溅 |

### 使用建议

- **优先使用细化描述**：细化版本传达更多视觉信息，生成效果更好
- **可组合使用**：`角色缓缓睁开双眼，嘴角上扬，同时右手抬起`
- **注意时间关系**：使用"同时"、"随后"、"紧接着"等连接词组织多个动作

## 5. 多角色同框动态规则

多角色镜头中，必须**分别描述**每个角色的动作：

### 规则

1. **逐一描述**：每个角色的动作单独写出，用逗号或句号分隔
2. **动作不冲突**：两个角色不能同时做相互矛盾的动作（如 A 拉住 B 的手，但 B 在转身离开）
3. **空间合理**：动作方向要与角色在画面中的位置一致
4. **主次分明**：主要角色的动作先写且更详细，次要角色简要带过

### 示例

**正确**（分别描述、主次分明）：
```
@Image1 作为Elsa外观参考。@Image2 作为Anna外观参考。@Image3 作为首帧，Elsa缓缓抬起右手释放冰晶魔法，Anna在旁侧双手合十惊喜注视，镜头从中景缓慢推至Elsa的手部特写
```

**错误**（笼统、动作冲突）：
```
@Image1 作为Elsa外观参考。@Image2 作为Anna外观参考。@Image3 作为首帧，两个人一起做动作
```

## 6. 动作承接规则（镜头间连续性）

相邻镜头之间必须保证**动作连续性**，避免角色状态跳变。

### 核心原则

**上一镜头的结束状态 = 下一镜头的起始状态**

### 需要跟踪的状态

| 状态维度 | 说明 | 示例 |
|----------|------|------|
| 角色姿势 | 站/坐/躺、手臂位置 | 上镜头结束时站立 → 下镜头起始时站立 |
| 角色位置 | 画面中的相对位置 | 上镜头在画面左侧 → 下镜头在画面左侧 |
| 表情状态 | 情绪表达 | 上镜头结束时微笑 → 下镜头起始时微笑 |
| 物品状态 | 手持物品、道具 | 上镜头拿起剑 → 下镜头仍握着剑 |
| 环境状态 | 天气、光照、场景 | 同一场景内保持一致 |

### 检查流程

对每个 Shot（除第一个外）：

1. 获取**上一 Shot** 的 `video_prompt` 和 `Plot/Visual Description`
2. 提取上一 Shot 结束时的角色状态
3. 确认当前 Shot 的起始描述与上一 Shot 的结束状态一致
4. 如不一致，调整当前 Shot 的 `video_prompt` 起始描述

### 示例

**连续的两个镜头**（正确）：
```
Shot 1 video_prompt: "@Image1 作为Elsa外观参考。@Image2 作为首帧，角色从坐姿缓缓站起，转身面向窗户"
Shot 2 video_prompt: "@Image1 作为Elsa外观参考。@Image2 作为首帧，角色面向窗户伸出右手触碰玻璃，冰霜从指尖蔓延"
```
- Shot 1 结束：站立，面向窗户
- Shot 2 起始：面向窗户（一致）

**不连续的两个镜头**（错误）：
```
Shot 1 video_prompt: "...角色从坐姿缓缓站起，转身面向窗户"
Shot 2 video_prompt: "...角色坐在椅子上低头翻书"  ← 跳变！上一镜头结束时已站起
```

### 场景切换例外

当镜头跨越不同场景时（Scene 边界），不要求动作承接。此时通过转场（fade/dissolve）衔接。

## 7. 平台适配

同一镜头可能需要为不同视频生成平台输出不同格式的 prompt。以下是各平台的适配规则：

### 可灵（KeLing）

- **语言**：中文
- **重点**：动态变化描述
- **格式**：直接描述动作和运镜，不需要 @Image 引用
- **特点**：支持上传参考图，prompt 聚焦动态

```
角色缓缓抬起右手，冰晶从指尖迸发向天空扩散，镜头从中景推至面部特写，光线逐渐变冷
```

### Seedance 2.0

- **语言**：中文
- **重点**：@Image 引用 + 动态描述
- **格式**：严格遵循 @Image 编号规则
- **特点**：multimodal 模式支持角色参考图 + 首帧图

```
@Image1 作为Elsa外观参考。@Image2 作为首帧，角色缓缓抬起右手，冰晶从指尖迸发向天空扩散，镜头从中景推至面部特写
```

### Runway / Pika

- **语言**：英文
- **重点**：camera motion 关键词
- **格式**：英文描述 + 平台特有的 motion 关键词
- **特点**：使用 camera motion 标签控制运镜

```
A woman slowly raises her right hand, ice crystals burst from fingertips spreading into the sky, camera pushes in from medium shot to close-up of face, lighting shifts to cool tones
```

### 平台选择建议

| 场景 | 推荐平台 | 原因 |
|------|---------|------|
| 角色一致性要求高 | Seedance (multimodal) | 支持角色参考图 + @Image 引用 |
| 纯场景/空镜 | 可灵 / Seedance (i2v) | 图生视频效果好 |
| 快速原型测试 | Runway / Pika | 英文 prompt 简单直接 |
| 无图片素材 | Seedance (t2v) / 可灵 | 文生视频模式 |

## 8. Team 执行流程

`prompt-video` Team 使用 `review` 模式，由 motion-director 生成、reference-validator 审核：

### 流程

```
1. motion-director 读取 Shot 数据 + 角色资产状态 + 上一 Shot 结束状态
2. motion-director 为每个 Shot 生成：
   a. 确定 seedance_mode（根据决策树）
   b. 规划 image_paths 数组（角色参考图 + 首帧图）
   c. 构造 video_prompt（按构造公式）
3. motion-director 将结果提交给 reference-validator
4. reference-validator 逐项审核：
   a. @Image 引用数量 == image_paths 长度
   b. 已设计角色都有 @Image 引用
   c. 最后一个 @Image 是首帧（作为首帧）
   d. 动作承接检查（与上一 Shot 的连续性）
   e. 无静态重复描述（不重复图片中已有内容）
5. 如有违规 → 返回 motion-director 修正（附具体 Shot ID 和修复建议）
6. 修正后重新审核，直到通过
7. 输出最终的 video_prompt + seedance_mode + image_paths
```

### 审核报告格式

reference-validator 的审核结果按以下格式输出：

```
[PASS] Shot S1_Sc1_Shot1: All checks passed
[FAIL] Shot S1_Sc1_Shot2:
  - @Image count mismatch: prompt has 2 refs, image_paths has 3
  - FIX: Add "@Image2 作为Anna外观参考。" before keyframe reference
[FAIL] Shot S1_Sc2_Shot1:
  - Action discontinuity: previous shot ends with character standing,
    this shot starts with character sitting
  - FIX: Change opening to "角色从站姿缓缓坐下" or adjust previous shot
[FAIL] Shot S2_Sc1_Shot3:
  - Static description detected: "一个金发女人站在阳台上" repeats image content
  - FIX: Remove static description, focus on dynamic action
```

## 9. 质量检查清单

### video_prompt 生成前

- [ ] 确认角色资产状态（哪些角色有 `character_list/{Name}/best.png`）
- [ ] 确认上一 Shot 的结束状态（用于动作承接）
- [ ] 确认目标平台（决定 prompt 格式和语言）

### video_prompt 构造后

- [ ] `@ImageN` 引用总数 == `image_paths` 数组长度
- [ ] 所有已设计角色都有对应的 `@Image` 引用
- [ ] 最后一个 `@Image` 是首帧（`作为首帧`）
- [ ] 未设计角色仅使用文字描述，无 `@Image` 引用
- [ ] `seedance_mode` 与图片资产匹配（决策树一致）

### 动态描述质量

- [ ] prompt 聚焦动态变化，非静态描述
- [ ] 使用细化动作词汇（非笼统描述）
- [ ] 多角色场景中每个角色的动作分别描述
- [ ] 动作不冲突、空间合理

### 镜头间连续性

- [ ] 上一 Shot 结束状态 == 当前 Shot 起始状态
- [ ] 角色姿势、位置、表情、物品状态连续
- [ ] 场景切换处使用转场（fade/dissolve）而非硬接

### reference-validator 审核通过

- [ ] 所有 Shot 的 @Image 引用校验通过
- [ ] 所有 Shot 的动作承接校验通过
- [ ] 无静态重复描述
- [ ] 审核报告全部为 `[PASS]`
