---
name: character-acting
description: "角色表演指导。角色的内在灵魂——性格档案、情感反应模式、表演指导词汇、对白演绎、音色设计。涵盖 Step 3a（性格提取）、Step 4c（Shot 表演指导）和 Step 5（配音指导）。"
team:
  enabled: true
  pattern: specialization
  coordinator: casting-director
  roles:
    - name: casting-director
      type: coordinator
      expertise: "Character ensemble management, performance vision"
      system_prompt: |
        You coordinate character enrichment. For each character:
        1. Assign personality-writer to build the character profile
        2. Assign voice-designer to plan voice and dialogue style
        3. Review results for internal consistency
        4. Ensure each character has a distinct personality and voice
      responsibilities:
        - Coordinate per-character enrichment
        - Ensure character profiles are internally consistent
        - Verify character differentiation (no two characters feel the same)
    - name: personality-writer
      type: specialist
      expertise: "Character psychology, personality traits, behavioral patterns"
      skill_ref: character-acting
      system_prompt: |
        Build a deep character profile:
        - Personality traits and MBTI-style classification
        - Speaking style (vocabulary, speech patterns, catchphrases)
        - Emotional reaction patterns (how they respond to stress, joy, fear)
        - Relationship dynamics with each other character
        - Character arc trajectory across the story
        - Facial expressions and body language specific to this character
      responsibilities:
        - Build Character Profile (personality, habits, emotional patterns)
        - Define facial expression vocabulary per character
        - Define body language vocabulary per character
    - name: voice-designer
      type: specialist
      expertise: "Voice acting direction, dialogue performance, audio design"
      skill_ref: prompt-audio
      system_prompt: |
        Design the voice identity for each character:
        - Voice type selection and refinement
        - Default speaking rhythm and speed
        - Emotion-to-voice parameter mapping specific to this character
        - Signature vocal qualities (raspy, melodic, nasal, etc.)
        - Sample audio_prompt dialogue lines demonstrating the character's voice
      responsibilities:
        - Select and customize voice_type per character
        - Define emotion-voice parameter mapping
        - Write sample audio_prompt dialogue lines
    - name: character-reviewer
      type: reviewer
      expertise: "Character consistency, ensemble balance"
      system_prompt: |
        Review all character profiles together:
        1. Each character has a distinct personality
        2. Voice types are differentiated (no two main characters sound alike)
        3. Relationship dynamics are reciprocal and consistent
        4. Character arcs are compatible with the plot
        5. No contradictions in emotional patterns
        6. Expression/body language vocabularies are character-specific
      responsibilities:
        - Validate character differentiation
        - Check consistency of relationship dynamics
        - Verify arc compatibility with plot
  coordination:
    merge_strategy: coordinator-merge
    review_required: true
    max_parallel: 3
---

# 角色表演指导 (Character Acting)

角色的内在灵魂——性格档案、情感反应模式、表演指导词汇、对白演绎、音色设计。

## 1. Core Principles

角色的灵魂由三个维度构成，缺一不可：

| 维度 | 定义 | 载体 |
|------|------|------|
| **Personality（性格）** | 角色是谁——思维方式、行为模式、价值观 | Character Profile |
| **Voice（声音）** | 角色如何表达——音色、语速、语气习惯 | voice_type + audio_prompt |
| **Performance（表演）** | 角色如何呈现——表情、肢体、情绪外化 | Plot/Visual Description + video_prompt |

**核心原则**：
- 每个角色必须在三个维度上都是**独特**的，不允许两个角色在任一维度上雷同
- 性格决定表演：角色的情绪反应模式直接映射到表情、肢体和语音参数
- 一致性贯穿全程：角色从 Step 3a 提取到 Step 5 配音，性格内核不变，表演随情节弧线演化
- 表演指导词汇必须具体、可执行，避免模糊词（如"表情丰富"），优先使用本文档的词汇表

## 2. Character Profile Schema

每个角色在 `characters.json` 中应包含完整的性格档案：

```json
{
  "name": "角色名",
  "appearance_description": "外观描述（来自 character-consistency Skill）",
  "personality": {
    "mbti": "INTJ",
    "core_traits": ["坚韧", "内敛", "责任感强"],
    "flaws": ["过于自我牺牲", "难以表达真实感情"],
    "values": "守护所爱之人"
  },
  "speaking_style": {
    "vocabulary_level": "formal",
    "speech_patterns": ["倒装句式", "常用反问"],
    "catchphrases": ["无论如何，我会……", "这是我的选择"],
    "speech_speed": "moderate",
    "pause_habit": "长句后停顿"
  },
  "emotional_reactions": {
    "stress": "沉默压抑，双手握拳",
    "joy": "微微嘴角上扬，不外露",
    "anger": "冷怒型——声音反而更平静，眼神变锐利",
    "fear": "身体微僵，快速分析局势",
    "sadness": "独处时才流露，人前始终镇定"
  },
  "relationship_dynamics": {
    "角色B": "保护欲强，语气会不自觉变柔和",
    "角色C": "竞争关系，对话中暗含较劲"
  },
  "character_arc": {
    "starting_state": "封闭内心，独自承担",
    "turning_point": "被迫接受他人帮助",
    "ending_state": "学会信任与依赖"
  },
  "voice": {
    "voice_type": "young_male",
    "speed": 1.0,
    "emotion_default": "determined",
    "signature_quality": "沉稳低沉，尾音略微下压"
  }
}
```

### 性格特质分类（MBTI 简化模型）

| 维度 | 选项 A | 选项 B | 对表演的影响 |
|------|--------|--------|-------------|
| 能量来源 | 外向 E（肢体丰富、语速快） | 内向 I（动作克制、语速慢） | 肢体语言幅度 |
| 信息处理 | 感觉 S（关注细节、描述具体） | 直觉 N（关注大局、言语抽象） | 对白风格 |
| 决策方式 | 思考 T（逻辑分析、语气理性） | 情感 F（情绪驱动、语气感性） | 情绪反应模式 |
| 生活态度 | 判断 J（果断、语气肯定） | 感知 P（犹豫、语气探索） | 对白节奏 |

### 说话风格维度

| 维度 | 选项示例 | 对 audio_prompt 的影响 |
|------|---------|----------------------|
| 用词习惯 | 书面语 / 口语化 / 方言 / 专业术语 | 台词文本本身 |
| 语速特征 | 快速连珠 / 不紧不慢 / 慢条斯理 | speed 参数 |
| 停顿习惯 | 思考型停顿 / 戏剧性停顿 / 几乎不停 | 对白中标注 `...` |
| 口头禅 | 角色专属高频词/句式 | 台词中反复出现 |
| 语气习惯 | 反问多 / 陈述为主 / 祈使句多 | 语调描述 |

### 情感反应模式

每个角色面对同一刺激的反应应当不同。以下为映射模板：

| 情境 | 外向热血型 | 内向沉稳型 | 冷静分析型 | 感性脆弱型 |
|------|-----------|-----------|-----------|-----------|
| 同伴受伤 | 立刻冲上前，大喊名字 | 无言握紧拳头，默默上前 | 迅速分析伤势，指挥救治 | 双手颤抖，泪水夺眶而出 |
| 被背叛 | 暴怒质问，语速加快 | 沉默良久，转身离开 | 冷笑，语气反而平静 | 不敢相信地摇头后退 |
| 获得胜利 | 高举双手，放声大笑 | 微微点头，嘴角上扬 | 已在计划下一步 | 感动落泪，拥抱同伴 |
| 面对恐惧 | 强撑镇定，声音微颤 | 身体僵硬，表情凝固 | 后退一步，观察分析 | 躲到他人身后，紧抓衣袖 |

## 3. Facial Expression Vocabulary（面部微表情词汇表）

在编写 `Plot/Visual Description` 和 `video_prompt` 时，从此词汇表中选取精确描述：

### 眼神

| 表情 | 传达情绪 | 使用场景 |
|------|---------|---------|
| 坚定凝视 | 决心、信念 | 做出重要决定、面对挑战 |
| 回避目光 | 愧疚、害羞、隐瞒 | 说谎、面对喜欢的人、被戳中痛处 |
| 泪光闪烁 | 感动、悲伤、压抑 | 重逢、告别、触及内心 |
| 瞳孔放大 | 震惊、恐惧 | 突发事件、看到意外画面 |
| 半眯 | 怀疑、审视、狡黠 | 不信任对方、思考对策 |
| 深情注视 | 爱意、温柔、珍惜 | 与爱人共处、守护的瞬间 |
| 目光涣散 | 失神、绝望、回忆 | 受到重大打击、陷入回忆 |
| 眼神锐利 | 警觉、敌意、冷怒 | 对峙、发现危险、被激怒 |
| 快速眨眼 | 紧张、不安 | 说谎时、面对压力 |
| 含笑注视 | 会心、慈爱 | 看到令人欣慰的画面 |

### 眉毛

| 表情 | 传达情绪 | 使用场景 |
|------|---------|---------|
| 紧蹙 | 担忧、痛苦、思考 | 面对难题、忍受疼痛 |
| 挑眉 | 惊讶、有趣、挑衅 | 听到意外消息、挑战对方 |
| 舒展 | 放松、释然、满足 | 危机解除、理解真相后 |
| 一侧挑起 | 质疑、不信 | 听到可疑说辞 |
| 快速抖动 | 惊讶、不可置信 | 瞬间冲击 |
| 眉头微动 | 犹豫、不确定 | 内心纠结时 |

### 嘴部

| 表情 | 传达情绪 | 使用场景 |
|------|---------|---------|
| 抿唇 | 隐忍、克制、不甘 | 压抑怒火、忍住泪水 |
| 嘴角上扬 | 含蓄笑、自信 | 胸有成竹、看到有趣的事 |
| 微微张开 | 惊讶、呆滞 | 意外发生时 |
| 咬下唇 | 紧张、犹豫、隐忍 | 做艰难决定、压抑情感 |
| 颤抖 | 恐惧、悲伤、激动 | 极端情绪时 |
| 微笑但嘴角僵硬 | 强颜欢笑、伪装 | 不想让人担心 |
| 咬牙 | 愤怒、决心、忍耐 | 下定决心、承受痛苦 |
| 撇嘴 | 不屑、不满 | 轻视对方 |

### 整体面部

| 表情 | 传达情绪 | 使用场景 |
|------|---------|---------|
| 面部僵硬 | 压抑、震惊、冻结 | 无法消化的信息 |
| 肌肉放松 | 释怀、如释重负 | 真相大白、危机解除 |
| 面色微红 | 羞涩、激动、尴尬 | 被表白、被当众表扬 |
| 面色苍白 | 恐惧、虚弱、震惊 | 见到恐怖场景、失血 |
| 泪痕 | 悲伤后的平静 | 哭过之后 |
| 狰狞扭曲 | 极度愤怒或痛苦 | 失控瞬间 |
| 表情空白 | 麻木、绝望 | 情感过载后的关机 |

## 4. Body Language Vocabulary（肢体语言词汇表）

### 手部

| 动作 | 传达情绪 | 使用场景 |
|------|---------|---------|
| 双手交叉 | 防御、抗拒、不信任 | 对话中保持距离 |
| 手指互绞 | 焦虑、紧张、不安 | 等待结果、面对未知 |
| 单手托腮 | 思考、无聊、观察 | 分析局势、漫不经心 |
| 握拳 | 愤怒、决心、克制 | 发誓、忍怒、准备战斗 |
| 轻弹手指 | 不耐烦、催促 | 等待太久 |
| 双手摊开 | 无奈、坦诚、投降 | 解释、表白、放弃抵抗 |
| 手指轻叩桌面 | 思考、等待、不耐 | 思考对策 |
| 紧握他人的手 | 信任、不舍、传递力量 | 告别、承诺、鼓励 |
| 手掌轻抚面颊 | 温柔、安慰 | 安慰哭泣的人 |
| 颤抖的手 | 恐惧、激动、虚弱 | 极端情绪或身体透支 |

### 站姿 / 坐姿

| 姿态 | 传达情绪 | 使用场景 |
|------|---------|---------|
| 挺胸抬头 | 自信、骄傲、强势 | 宣告、对峙 |
| 佝偻低头 | 沮丧、自卑、疲惫 | 失败后、被打击 |
| 双手叉腰 | 挑战、不服、霸气 | 对抗、争论 |
| 倚靠墙壁/椅背 | 慵懒、满不在乎 | 旁观、不想参与 |
| 重心不稳 | 紧张、动摇、受伤 | 被震慑、伤后站立 |
| 笔直端坐 | 严肃、正式、警觉 | 重要对话、审讯 |
| 蜷缩抱膝 | 脆弱、自我保护 | 独处时的崩溃 |

### 动态动作

| 动作 | 传达情绪 | 使用场景 |
|------|---------|---------|
| 猛然回头 | 警觉、震惊、被叫住 | 听到异响、被呼唤 |
| 缓步走来 | 从容、威压、温柔 | 大人物登场、走向爱人 |
| 冲上前 | 焦急、愤怒、保护欲 | 救人、质问、阻止 |
| 后退一步 | 惊讶、恐惧、抗拒 | 发现真相、面对威胁 |
| 原地踱步 | 焦虑、思考、等待 | 等消息、想办法 |
| 转身背对 | 拒绝、失望、隐藏表情 | 不想让人看到脆弱 |
| 单膝跪地 | 臣服、恳求、受伤倒地 | 重要承诺、战斗受伤 |
| 缓缓倒下 | 力竭、绝望、死亡 | 战斗结束、最终时刻 |

## 5. Dialogue Emotion Spectrum（对白情感光谱）

替代简单的 happy/sad/angry 标签，使用细腻的情感层次描述角色在特定 Shot 中的情绪状态：

### 基本情感光谱

| 情感大类 | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---------|---------|---------|---------|---------|---------|
| **喜** | 微笑 | 欣喜 | 狂喜 | 感动落泪 | — |
| **怒** | 不悦 | 烦躁 | 愤怒 | 暴怒 | 冷怒（最危险） |
| **哀** | 惆怅 | 忧伤 | 悲痛 | 绝望 | 释然 |
| **惧** | 不安 | 紧张 | 恐惧 | 惊恐 | 颤栗 |

### 复合情感

| 复合情绪 | 组成 | 面部特征 | 语音特征 |
|---------|------|---------|---------|
| 苦笑 | 哀 + 喜 | 嘴角上扬但眼神悲伤 | 气声短笑，尾音下沉 |
| 含泪微笑 | 喜 + 哀 | 泪光闪烁 + 嘴角上扬 | 声音微颤，语调温柔 |
| 恼羞成怒 | 怒 + 惧（社交） | 面色微红 + 眉头紧蹙 | 语速加快，音调升高 |
| 强颜欢笑 | 喜（伪装）+ 哀（真实） | 微笑但嘴角僵硬 | 语气刻意轻快但不自然 |
| 故作镇定 | 惧（内在）+ 理性（外在） | 面部僵硬但试图放松 | 语速刻意放慢，偶尔卡顿 |
| 绝处逢生 | 惧→喜 | 瞳孔放大→眼含泪光→释然 | 急促喘息→声音颤抖→笑出声 |
| 怒极反笑 | 怒→喜（扭曲） | 眼神锐利 + 嘴角上扬 | 低沉笑声，语气冰冷 |

### 情感层次与 audio_prompt 映射

| 情感层次 | 语速 | 音量 | 语调 | audio_prompt 描述词 |
|---------|------|------|------|-------------------|
| 微笑 | 1.0x | 正常 | 轻快上扬 | 轻声微笑着说 |
| 欣喜 | 1.1x | 稍高 | 明显上扬 | 欢快地说 |
| 狂喜 | 1.2x | 高 | 高亢激动 | 兴奋地大声说 |
| 不悦 | 0.95x | 正常 | 略沉 | 语气不善地说 |
| 愤怒 | 1.15x | 高 | 强烈起伏 | 愤怒地吼道 |
| 冷怒 | 0.85x | 低 | 极度平稳 | 冷冷地、一字一顿地说 |
| 惆怅 | 0.9x | 稍低 | 平缓下行 | 怅然若失地低语 |
| 悲痛 | 0.8x | 低 | 低沉颤抖 | 哽咽着说 |
| 不安 | 1.05x | 正常 | 微颤 | 不安地说 |
| 恐惧 | 1.1x | 低 | 颤抖急促 | 颤声说 |

## 6. Performance Direction for Shots

### 6.1 Enriching `Plot/Visual Description`

在 Step 4c Layer 3 生成 Shot 时，`Plot/Visual Description` 中必须包含表演细节。格式：

```
{场景描述}。{角色名}{肢体动作}，{面部表情}，{视线方向/对象}。{对白或内心活动}。
```

**示例**：
```
冰冷的王座大厅中，Elsa 缓步走向窗边（动态），双手交叉抱胸（手部-防御），
眉头紧蹙（眉毛-担忧），目光涣散地望向窗外的暴风雪（眼神-回忆）。
内心独白：曾经的承诺，真的能实现吗？
```

**规则**：
1. 每个含角色的 Shot，`Plot/Visual Description` 必须至少包含 **1 个面部表情** + **1 个肢体动作** 描述
2. 描述词优先从本文档 Section 3/4 词汇表中选取
3. 多角色画面中，每个角色需独立描述表演
4. 表演选择必须与角色性格档案一致（内向角色不应有夸张肢体）
5. 表演强度应匹配对白情感光谱的层次

### 6.2 Enriching `audio_prompt`

在 `audio_prompt` 中为对白添加角色专属的语音指导：

```
{环境音效}, {动作音效}, {voice_type}{情感描述词}说：'{台词}', {BGM描述}
```

**示例**：
```
空旷大厅的回声效果, 缓慢的脚步声, 年轻女性冷冷地一字一顿地说：'我不需要任何人的帮助', 低沉弦乐渐强
```

**规则**：
1. 性别/年龄描述必须与 `voice_type` 对应（young_female → 年轻女性）
2. 情感描述词从 Section 5 的 `audio_prompt 描述词` 列选取
3. 同一角色在不同 Shot 中的基础音色描述保持一致
4. 情绪变化通过情感描述词和语气标注体现，而非更换 voice_type
5. 内心独白标注：`{voice_type}低声喃喃（内心独白）：'{内容}'`

## 7. Character Arc Tracking

### Character Arc Blueprint

在 Step 3a 提取角色时，为每个主要角色建立弧线蓝图：

```json
{
  "character_arc_blueprint": {
    "Elsa": {
      "arc_type": "transformation",
      "phases": [
        {
          "phase": "setup",
          "sub_scripts": ["Sub-Script1", "Sub-Script2"],
          "emotional_state": "压抑、自我封闭",
          "performance_tone": "克制、内敛",
          "dominant_expressions": ["回避目光", "双手交叉", "抿唇"]
        },
        {
          "phase": "confrontation",
          "sub_scripts": ["Sub-Script3", "Sub-Script4"],
          "emotional_state": "内心挣扎、开始动摇",
          "performance_tone": "纠结、偶尔流露",
          "dominant_expressions": ["紧蹙眉头", "咬下唇", "手指互绞"]
        },
        {
          "phase": "climax",
          "sub_scripts": ["Sub-Script5"],
          "emotional_state": "情感爆发、突破枷锁",
          "performance_tone": "激烈、释放",
          "dominant_expressions": ["泪光闪烁", "握拳", "挺胸抬头"]
        },
        {
          "phase": "resolution",
          "sub_scripts": ["Sub-Script6"],
          "emotional_state": "释然、接纳",
          "performance_tone": "平和、温暖",
          "dominant_expressions": ["深情注视", "含笑注视", "肌肉放松"]
        }
      ]
    }
  }
}
```

### Arc-to-Shot 映射规则

1. 在 Layer 3 创建每个 Shot 时，先查询该 Shot 所属的 Sub-Script 对应的角色弧线 phase
2. Shot 中角色的表演选择（表情、肢体、语气）必须与当前 phase 的 `dominant_expressions` 和 `performance_tone` 一致
3. 允许在 phase 边界的 Shot 中出现渐变过渡（如 setup→confrontation 边界可混合两个 phase 的表演风格）
4. 关键转折 Shot 应使用 **复合情感**（Section 5）来表现角色内心冲突

## 8. Voice Type Mapping

### 基础音色（继承自 voice-synthesis）

| voice_type | 描述 | 适用角色 |
|-----------|------|---------|
| narrator | 男性旁白 | 叙述者 |
| young_male | 年轻男性 | 男主角（18-30） |
| young_female | 年轻女性 | 女主角（18-30） |
| mature_male | 成熟男性 | 长辈、Boss |
| mature_female | 成熟女性 | 女性长辈 |
| child | 儿童 | 小孩角色 |

### 扩展音色

| voice_type | 描述 | 适用角色 | 签名特征 |
|-----------|------|---------|---------|
| raspy_elder | 沙哑老者 | 智者、老人、师父 | 气声明显，语速慢，句间长停顿 |
| cool_female | 清冷御姐 | 女王、强势女性反派 | 语调低平，几乎不带感情波动 |
| lazy_youth | 慵懒少年 | 天才型配角、隐藏实力者 | 拖长尾音，语速偏慢，漫不经心 |
| bubbly_girl | 活泼萝莉 | 元气少女、搞笑担当 | 语调高、语速快、常用语气词"诶""嘛""啦" |
| deep_villain | 深沉反派 | 最终 Boss、暗黑角色 | 低沉浑厚，语速极慢，每个字都有重量 |
| gentle_male | 温柔男性 | 治愈系男配、守护者 | 轻声细语，语调平缓上扬 |

### 情绪-语音参数映射（基础表）

| 情绪 | 语速调整 | 音量调整 | 语调 |
|------|---------|---------|------|
| neutral | 1.0x | 正常 | 平稳 |
| happy | 1.1x | 稍高 | 上扬 |
| sad | 0.85x | 稍低 | 低沉 |
| angry | 1.15x | 高 | 强烈起伏 |
| surprised | 1.2x | 高 | 急促上扬 |
| fearful | 1.1x | 低 | 颤抖 |
| determined | 1.0x | 稍高 | 沉稳有力 |

**注意**：此表为基础映射，每个角色应根据性格档案定制偏移量。例如，冷怒型角色的 angry 不会提高音量，反而降低。

### 对白类型处理

| 类型 | 处理方式 |
|------|----------|
| 角色对话 | 使用角色专属 voice_type + 情绪参数 |
| 内心独白 | 使用角色 voice_type + 降速 20% + 轻声 + 添加"（内心独白）"标记 |
| 旁白叙述 | 使用 narrator voice_type + 均匀语速 |
| 呐喊/吼叫 | 高音量 + 快速 + 可加"吼道"/"嘶吼" |
| 窃窃私语 | 极低音量 + 气声 + 降速 10% |

## 9. Team Execution Flow

### 执行顺序

```
casting-director（协调者）
  │
  ├─→ personality-writer（性格专家）
  │     输入：characters.json + raw_script.txt
  │     输出：enriched character profiles (性格、表情词汇、肢体词汇)
  │
  ├─→ voice-designer（声音专家）
  │     输入：characters.json + character profiles
  │     输出：voice_type 选择 + emotion mapping + 示例 audio_prompt
  │
  └─→ character-reviewer（审核者）
        输入：所有角色的完整档案
        输出：审核报告 + 修改建议
```

### 详细流程

1. **casting-director** 读取 `characters.json` 和 `raw_script.txt`/`script_synopsis.json`
2. **casting-director** 为每个角色创建 Task，分配给 personality-writer 和 voice-designer
3. **personality-writer** 并行处理（max_parallel=3 个角色同时）：
   - 构建性格档案（MBTI、情感反应模式、关系动态）
   - 从词汇表选择角色专属的表情和肢体语言集
   - 输出 Character Arc Blueprint
4. **voice-designer** 在 personality-writer 完成后介入：
   - 基于性格档案选择 voice_type
   - 定制情绪-语音参数偏移
   - 编写 3-5 条示例 audio_prompt 对白
5. **character-reviewer** 在所有角色完成后统一审核：
   - 验证角色间差异化（性格、音色、表演风格不雷同）
   - 检查关系动态的双向一致性
   - 确认弧线与剧情兼容
6. **casting-director** 合并结果，输出最终的 enriched `characters.json`

### 输出产物

| 产物 | 位置 | 描述 |
|------|------|------|
| enriched `characters.json` | `projects/{id}/characters.json` | 包含完整性格档案、voice 配置、弧线蓝图 |
| character arc blueprint | 嵌入 `characters.json` | 每个主角的弧线阶段映射 |
| voice sample prompts | 嵌入各角色 voice 字段 | 示例 audio_prompt 对白 |

## 10. Quality Checklist

### Step 3a 角色提取后

- [ ] 每个角色有完整的 personality 字段（mbti, core_traits, flaws, values）
- [ ] 每个角色有独特的 speaking_style（口头禅不重复）
- [ ] 每个角色有 emotional_reactions 映射（至少 5 种情境）
- [ ] 关系动态是双向的（A→B 的态度和 B→A 对应）
- [ ] 每个主角有 character_arc（starting_state, turning_point, ending_state）
- [ ] 每个角色的表情/肢体词汇集与性格匹配

### Voice 设计后

- [ ] 每个角色分配了 voice_type（无重复，或有充分理由）
- [ ] voice_type 与角色年龄、性格匹配
- [ ] 每个角色有定制的情绪-语音参数偏移
- [ ] 至少 3 条示例 audio_prompt 对白
- [ ] 内向角色的语速 ≤ 1.0x，外向角色 ≥ 1.0x

### 审核后

- [ ] 任意两个主角的性格档案差异 ≥ 3 个维度
- [ ] 任意两个主角的 voice_type 不同
- [ ] 关系动态无矛盾（A 说信任 B，B 也有对应态度）
- [ ] 弧线与剧情 Sub-Script 对应关系合理
- [ ] 复合情感在关键转折点有使用
- [ ] 反派角色的"冷怒"等独特情感有定义

### Step 4c Shot 表演指导后

- [ ] 每个含角色的 Shot 有 ≥1 面部表情 + ≥1 肢体动作
- [ ] 表演选择与当前弧线 phase 一致
- [ ] audio_prompt 对白使用了角色专属 voice_type 和情感描述词
- [ ] 同一场景内角色表演风格连贯
- [ ] 转折 Shot 使用了复合情感
