# MovieAgent 核心实现分析（基于源码）

> **论文**: Automated Movie Generation via Multi-Agent CoT Planning (arXiv:2503.07314)
> **仓库**: https://github.com/showlab/MovieAgent
> **本地**: `D:\codespace\MovieAgent`

---

## 一、项目本质

MovieAgent 是一个**纯编排系统**，代码量极小（核心仅 4 个文件 ~62KB），不做任何模型训练，完全依赖：
- **LLM**（GPT-4o / DeepSeek / Qwen）做文本规划
- **现成模型**（ROICtrl / HunyuanVideo_I2V / VALL-E）做素材生成
- **moviepy** 做最终拼接

---

## 二、源码结构

```
MovieAgent/
├── movie_agent/
│   ├── run.py                 (351行) ← 主调度：ScriptBreakAgent 5步流水线
│   ├── system_prompts.py      (568行) ← 所有 Prompt 模板（灵魂文件）
│   ├── base_agent.py          (188行) ← LLM 调用封装
│   ├── tools.py               (277行) ← 生成模型调度层
│   ├── configs/
│   │   ├── ROICtrl.json              ← ROICtrl 模型路径配置
│   │   └── HunyuanVideo_I2V.json    ← HunyuanVideo 推理参数
│   ├── models/                       ← 14 个模型的本地实现
│   │   ├── ROICtrl/ROICtrl.py       ← 角色一致性图像生成（核心）
│   │   ├── HunyuanVideo_I2V/        ← 图生视频
│   │   ├── VALLE/                   ← TTS 声音克隆
│   │   ├── ConsisID/               ← 角色一致性（备选）
│   │   ├── StoryDiffusion/          ← 故事扩散（备选）
│   │   └── ... (SVD, CogVideoX, SD 系列等)
│   └── script/
│       └── run.sh                   ← 启动脚本
├── dataset/                          ← 10 部电影的数据集
│   ├── FrozenII/
│   ├── Deadpool/
│   ├── NeZha2/
│   ├── NovelStory_2/               ← 原创小说场景（悟空、八戒、二郎神）
│   └── ...
└── requirements.txt
```

---

## 三、输入格式（实际文件）

### 3.1 `script_synopsis.json`

FrozenII 示例:
```json
{
  "MovieScript": "Anna, Elsa, Kristoff, Olaf, and Mattias embark on a journey to uncover the truth behind the mysterious voice calling Elsa. As they travel to the enchanted forest, they discover that the past holds secrets about their kingdom and Elsa's powers...",
  "Character": ["Anna", "Elsa", "Kristoff", "Mattias", "Olaf"]
}
```

NovelStory_2（原创小说）示例:
```json
{
  "MovieScript": "Wukong, Bajie, and ErLang cross paths when a powerful artifact goes missing from the heavenly realm...",
  "Character": ["Bajie", "ErLang", "Wukong"]
}
```

**关键点**: `MovieScript` 就是一段叙事文本（150-300 词），不需要完整剧本。

### 3.2 角色素材库

```
character_list/
├── Elsa/
│   ├── best.png       ← 最佳参考图（必须）
│   ├── best.txt       ← "<TOK> has long blonde hair in a braid, wearing a sparkling blue dress..."
│   ├── photo_1.png    ← 多角度（ROICtrl ED LoRA 训练用）
│   ├── photo_1.txt
│   └── ... (6-19 张参考图)
├── Anna/
│   ├── best.png
│   ├── best.txt       ← "<TOK> wears a purple cape over a dark dress..."
│   └── ...
```

**关键设计**: 
- `<TOK>` 是占位符，在 ROICtrl 的 ED LoRA 中被替换为角色特有的 token embedding
- `best.txt` 描述角色外观，用于 prompt 构造
- 每个角色 6-19 张不同角度/表情的参考图

---

## 四、5 步流水线源码解析

### 主入口 (`run.py` main)

```python
def main():
    args = parse_args()
    movie_director = ScriptBreakAgent(args, ...)
    
    movie_director.ScriptBreak()      # Step 1: 剧本 → Sub-Scripts
    movie_director.ScenePlanning()     # Step 2: Sub-Scripts → Scenes
    movie_director.ShotPlotCreate()    # Step 3: Scenes → Shots
    movie_director.VideoAudioGen()     # Step 4: Shots → 视频片段
    movie_director.Final()             # Step 5: 片段 → 成片
```

完全线性执行，无用户交互，无并行，无重试。

### ScriptBreakAgent 初始化

```python
class ScriptBreakAgent:
    def __init__(self, args, ...):
        # 3 个 LLM Agent（全部用 BaseAgent 封装）
        self.screenwriter_agent = BaseAgent(args.LLM, 
            system_prompt=sys_prompts["screenwriterCoT-sys"], use_history=False, temp=0.7)
        self.sceneplanning_agent = BaseAgent(args.LLM, 
            system_prompt=sys_prompts["ScenePlanningCoT-sys"], use_history=False, temp=0.7)
        self.shotplotcreate_agent = BaseAgent(args.LLM, 
            system_prompt=sys_prompts["ShotPlotCreateCoT-sys"], use_history=False, temp=0.7)
        
        # 工具层
        self.tools = ToolCalling(args, sample_model, audio_model, talk_model, Image2Video, ...)
```

**注意**: `use_history=False`，每次调用都只发 system + 当次 user message，不保留上下文。

---

### Step 1: ScriptBreak（剧本拆解）

```python
def ScriptBreak(self):
    movie_script, characters_list = self.extract_characters_from_json(self.script_path, 40)
    
    query = f"""
        Script Synopsis: {movie_script}
        Character: {characters_list}
    """
    result = self.screenwriter_agent(query, parse=True)  # → JSON
    save_json(result, self.sub_script_path)               # → Step_1_script_results.json
```

**Prompt（`screenwriterCoT-sys`）核心要求**:
- 输出 `Internal Chain-of-Thought`：分 5 步推理（叙事结构 → 角色提取 → 时间分段 → 验证 → 理由）
- 将故事拆分为 ≤20 个 Sub-Script
- 每个 Sub-Script ≥50 词，保留原文不修改
- 输出角色关系图 `Relationships`

**输出格式**:
```json
{
  "Relationships": { "Anna - Elsa": "Sisters", ... },
  "Internal Chain-of-Thought": { ... },
  "Sub-Script": {
    "Sub-Script 1": {
      "Plot": "详细剧情（≥50词）",
      "Involving Characters": ["Anna", "Elsa"],
      "Timeline": "Beginning",
      "Reason for Division": "..."
    },
    ...
  }
}
```

---

### Step 2: ScenePlanning（场景规划）

```python
def ScenePlanning(self):
    data = self.read_json(self.sub_script_path)
    character_relationships = data['Relationships']
    
    for sub_script_name in data['Sub-Script']:
        sub_script = data['Sub-Script'][sub_script_name]["Plot"]
        query = f"""
            Given the following inputs:
            - Script Synopsis: "{sub_script}"
            - Character Relationships: {character_relationships}
        """
        task_response = self.sceneplanning_agent(query, parse=True)
        data['Sub-Script'][sub_script_name]["Scene Annotation"] = task_response
    
    save_json(data, self.scene_path)  # → Step_2_scene_results.json
```

**逐个 Sub-Script 调用 LLM**，为每个 Sub-Script 规划场景。

**输出格式（嵌套在每个 Sub-Script 下）**:
```json
{
  "Internal Chain-of-Thought": { ... },
  "Scene": {
    "Scene 1": {
      "Involving Characters": ["Elsa", "Anna"],
      "Plot": "...",
      "Scene Description": "Dense forest with towering trees...",
      "Emotional Tone": "Wonder mixed with apprehension",
      "Visual Style": "Cool blue lighting...",
      "Key Props": ["magical mist", "autumn leaves"],
      "Music and Sound Effects": "Whispered echoes...",
      "Cinematography Notes": "Wide establishing shots..."
    }
  }
}
```

---

### Step 3: ShotPlotCreate（镜头创建）

```python
def ShotPlotCreate(self):
    data = self.read_json(self.scene_path)
    
    for sub_script_name in data['Sub-Script']:
        scene_list = data['Sub-Script'][sub_script_name]["Scene Annotation"]["Scene"]
        for scene_name in scene_list:
            scene_details = scene_list[scene_name]
            query = f"""
                Given the following Scene Details:
                - Involving Characters: "{scene_details['Involving Characters']}"
                - Plot: "{scene_details['Plot']}"
                - Scene Description: "{scene_details['Scene Description']}"
                - Emotional Tone: "{scene_details['Emotional Tone']}"
                - Key Props: {scene_details['Key Props']}
                - Cinematography Notes: "{scene_details['Cinematography Notes']}"
            """
            task_response = self.shotplotcreate_agent(query, parse=True)
            scene_list[scene_name]["Shot Annotation"] = task_response
    
    save_json(data, self.shot_path)  # → Step_3_shot_results.json
```

**双层循环**: Sub-Script → Scene，逐场景生成镜头。

**输出格式（嵌套在每个 Scene 下）**:
```json
{
  "Internal Chain-of-Thought": { ... },
  "Shot": {
    "Shot 1": {
      "Involving Characters": {
        "Elsa": [0.1, 0.06, 0.49, 1.0],
        "Anna": [0.58, 0.04, 0.95, 1.0]
      },
      "Plot/Visual Description": "Elsa and Anna approach the magical mist wall... (≥30词)",
      "Coarse Plot": "Two figures walking toward swirling mist (≤20词, 不含人名)",
      "Emotional Enhancement": "...",
      "Shot Type": "Medium shot",
      "Camera Movement": "Slow dolly-in",
      "Subtitles": {
        "Elsa": "I can feel something calling me.",
        "Anna": "We'll face it together."
      }
    }
  }
}
```

**关键细节**:
- `Involving Characters` 是 **dict** 而非 list，value 是归一化边界框 `[x1, y1, x2, y2]`
- `Coarse Plot` 不含人名，专门给 ROICtrl 做 caption
- `Plot/Visual Description` 详细描述，给非 ROICtrl 模型用
- `Subtitles` 是 `{角色名: 对白}` 的 dict
- 每镜头 ≤3 个角色（最好 1-2 个）
- 边界框 x 方向间距 ≤0.5，不允许重叠

---

### Step 4: VideoAudioGen（视频生成）

```python
def VideoAudioGen(self):
    data = self.read_json(self.shot_path)
    
    for sub_script_name in data['Sub-Script']:
        for scene_name in scene_list:
            for shot_name in shot_lists:
                shot_info = shot_lists[shot_name]
                
                # 根据模型选择不同的 prompt
                if self.sample_model == "ROICtrl":
                    plot = shot_info["Coarse Plot"]      # 无人名的简洁描述
                else:
                    plot = shot_info["Plot/Visual Description"]  # 详细描述
                
                character_list = shot_info["Involving Characters"]  # dict: {name: [box]}
                subtitle = shot_info["Subtitles"]
                
                # 构建角色照片路径列表
                character_phot_list = [
                    os.path.join(self.character_photo_path, name.replace(" ","_"), "best.png") 
                    for name in character_list
                ]
                
                # 文件名: "Sub-Script_1|Scene_1|Shot_1.jpg"
                save_path = os.path.join(
                    self.video_save_path,
                    f"{sub_script_name}|{scene_name}|{shot_name}.jpg"
                )
                
                # 调用工具链: 图像生成 → 图生视频
                self.tools.sample(plot, character_phot_list, character_box, 
                                  subtitle, save_path, (1024, 512))
```

**ToolCalling.sample() 执行链**:
```python
def sample(self, prompt, refer_path, character_box, subtitle, save_path, size):
    # 1. 生成关键帧图片
    self.gen.predict(prompt, refer_path, character_box, save_path, size)
    
    # 2. 图片转视频
    video_save_path = save_path.replace(".jpg", ".mp4")
    self.image2video.predict(prompt, save_path, video_save_path, size)
```

---

### Step 5: Final（合成）

```python
def Final(self):
    mp4_files = sorted([f for f in os.listdir(self.video_save_path) if f.endswith('.mp4')])
    clips = [VideoFileClip(os.path.join(directory, f)) for f in mp4_files]
    final_video = concatenate_videoclips(clips)
    final_video.write_videofile("final_video.mp4", codec="libx264")
```

纯粹的按文件名排序拼接，无转场、无字幕烧录。

---

## 五、ROICtrl 角色一致性机制（核心技术）

### 原理

ROICtrl = **Region of Interest Control**，基于 Stable Diffusion v1.4，核心思想：
1. 用 **ED LoRA** 为每个角色训练独立的 token embedding（`<Anna1> <Anna2>`）
2. 推理时通过**边界框**指定角色在画面中的位置
3. 在 UNet 的 cross-attention 层注入 ROI 信息

### 实际调用代码

```python
class ROICtrl_pipe:
    def predict(self, prompt, refer_images, character_box, save_name, size, seed=0):
        input_data = {
            "caption": f"{prompt}, 4K, high quality, high resolution, best quality",
            "roi_boxes": [],
            "roi_phrases": [],
            "height": size[1],   # 512
            "width": size[0],    # 1024
            "seed": 42,
            "roictrl_scheduled_sampling_beta": 1.0
        }
        
        for name in character_box:
            # 随机化 y 坐标（上下位置）
            y1, y2 = random.uniform(0.00001, 0.2), random.uniform(0.8, 0.9999)
            character_box[name][1], character_box[name][3] = y1, y2
            
            # 构造 ROI phrase: "a <Anna1> <Anna2>"
            roi_phrase = f"a <{name}1> <{name}2>"
            
            input_data["roi_boxes"].append(character_box[name])
            input_data["roi_phrases"].append(roi_phrase)
        
        # 编码 ROI 输入（cross attention 注入）
        cross_attention_kwargs = {
            'roictrl': encode_roi_input(input_data, self.pipe, ...)
        }
        
        # 调用 SD pipeline
        result = self.pipe(
            prompt=input_data["caption"],
            negative_prompt="worst quality, low quality...",
            cross_attention_kwargs=cross_attention_kwargs,
            height=input_data['height'],
            width=input_data['width'],
        ).images[0]
        result.save(save_name)
```

### 关键机制

1. **`<TOK>` → `<Name1> <Name2>`**: 每个角色有 2 个学习到的 token
2. **边界框**: LLM 在 Step 3 输出 `[x1, y1, x2, y2]`，y 坐标在推理时随机化
3. **cross_attention_kwargs**: 在 UNet 推理时注入 ROI 位置和角色 embedding
4. **ED LoRA 权重**: 预训练好的，按电影存放在 `weight/MovieAgent-ROICtrl-Frozen/FrozenII/`

---

## 六、Prompt 体系详解

`system_prompts.py` 定义了 **9 个 Prompt**，分 3 类：

### 6.1 评估类（与电影生成无关）
| Prompt | 用途 |
|--------|------|
| `open-prompt-sys` | 图像生成评估采样设计 |
| `open-plan-sys` | 评估规划（探索模型边界） |

### 6.2 电影生成类（核心）
| Prompt | CoT | 用途 |
|--------|-----|------|
| `screenwriter-sys` | ❌ | 基础编剧，直接拆分 |
| `screenwriterCoT-sys` | ✅ | **带推理的编剧（实际使用）** |
| `screenwriterCoT-sys1` | ✅ | 迭代编剧（逐个生成 Sub-Script） |
| `scriptsupervisor-sys` | — | 督导审查（代码中被注释掉） |
| `ScenePlanning-sys` | ❌ | 基础场景规划 |
| `ScenePlanningCoT-sys` | ✅ | **带推理的场景规划（实际使用）** |
| `ShotPlotCreate-sys` | ❌ | 基础镜头创建 |
| `ShotPlotCreateCoT-sys` | ✅ | **带推理的镜头创建（实际使用）** |

### 6.3 CoT 推理结构

每个 CoT Prompt 都要求 LLM 输出 `Internal Chain-of-Thought` 字段：

**编剧 CoT**:
1. Core Narrative Structure（叙事结构）
2. Key Character Information（角色信息）
3. Temporal Segmentation（时间分段）
4. Sub-Script Breakdown Criteria（拆分标准）
5. Division（分割理由）

**场景规划 CoT**:
1. Narrative Structure（叙事结构）
2. Key Scene Elements（场景元素）
3. Scene Boundaries（场景边界）
4. Cinematic Elements for Each Scene（电影元素增强）

**镜头创建 CoT**:
1. Break Down Scene into Key Shots（镜头分解）
2. Shot Composition and Framing（构图与框架）
3. Character Positioning & Bounding Boxes（角色定位）
4. Emotional Impact（情感冲击）
5. Camera Techniques and Movements（运镜技术）
6. Dialogue & Subtitle Accuracy（对白准确性）

---

## 七、BaseAgent 实现

```python
class BaseAgent:
    def __init__(self, llm_type, system_prompt, use_history=False, temp=0.7):
        # 根据 llm_type 初始化不同的 OpenAI 客户端
        # gpt4-o → OpenAI()
        # deepseek-r1/v3 → OpenAI(base_url="dashscope.aliyuncs.com/compatible-mode/v1")
        # 其他 → 同上（阿里云百炼）
        self.messages = [{"role": "system", "content": system_prompt}]

    def __call__(self, message, parse=False):
        self.messages.append({"role": "user", "content": message})
        result = self.generate(message, parse)
        self.messages.append({"role": "assistant", "content": result})
        if parse:
            result = json.loads(result.replace("```json","").replace("```",""))
        return result

    def generate(self, message, json_format):
        if not self.use_history:
            # 每次只发 system + 当前 user（无上下文）
            input_messages = [
                {"role": "system", "content": self.system},
                {"role": "user", "content": message}
            ]
        
        if self.llm_type == "gpt4-o":
            response = self.client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=input_messages,
                response_format={"type": "json_object"} if json_format else None
            )
        elif self.llm_type == "deepseek-r1":
            # 流式处理，分离 reasoning_content 和 answer_content
            completion = self.client.chat.completions.create(
                model="deepseek-r1", messages=input_messages, stream=True)
            for chunk in completion:
                # ... 打印思考过程，拼接最终回答
            return answer_content
```

**关键**: 
- `use_history=False` → 每次调用独立，不累积上下文
- GPT-4o 支持 `response_format=json_object`
- DeepSeek-R1 通过流式处理分离推理过程

---

## 八、数据嵌套结构（三层 JSON）

最终的 `Step_3_shot_results.json` 结构：

```
Root
├── Relationships: { "A - B": "关系" }
├── Internal Chain-of-Thought: { ... }
└── Sub-Script:
    ├── "Sub-Script 1":
    │   ├── Plot: "..."
    │   ├── Involving Characters: [...]
    │   ├── Timeline: "..."
    │   └── Scene Annotation:
    │       ├── Internal Chain-of-Thought: { ... }
    │       └── Scene:
    │           ├── "Scene 1":
    │           │   ├── Plot, Scene Description, Emotional Tone, ...
    │           │   └── Shot Annotation:
    │           │       ├── Internal Chain-of-Thought: { ... }
    │           │       └── Shot:
    │           │           ├── "Shot 1":
    │           │           │   ├── Involving Characters: { "Elsa": [x1,y1,x2,y2] }
    │           │           │   ├── Plot/Visual Description
    │           │           │   ├── Coarse Plot
    │           │           │   ├── Shot Type
    │           │           │   ├── Camera Movement
    │           │           │   └── Subtitles: { "Elsa": "..." }
    │           │           └── "Shot 2": { ... }
    │           └── "Scene 2": { ... }
    └── "Sub-Script 2": { ... }
```

---

## 九、与我们项目的对比及启示

### 9.1 核心差异

| 维度 | MovieAgent | 我们的项目 |
|------|-----------|-----------|
| **代码量** | ~1400 行（4 个核心文件） | 更多（DB + 多 Agent + 多 Script） |
| **输入** | `synopsis.json` + 角色图片库 | 用户对话式主题输入 |
| **规划** | LLM 全自动（3 步拆解，0 人工） | 5 步流程，每步需用户确认 |
| **数据流** | 3 个 JSON 文件逐步嵌套 | DB + 多个独立 JSON |
| **角色一致性** | ROICtrl ED LoRA + 边界框（本地 GPU） | Seedance @引用（API） |
| **图像生成** | ROICtrl（SD v1.4 定制，本地） | DALL-E 3（API） |
| **视频生成** | HunyuanVideo_I2V（本地 GPU） | Seedance 2.0（API） |
| **音频** | VALL-E 声音克隆（本地） | Seedance 原生 + 火山 TTS |
| **合成** | moviepy 简单拼接 | FFmpeg 完整合成 |
| **部署** | 需 GPU 集群 | 纯 API，轻量 |

### 9.2 最值得借鉴的设计

#### ① 分层拆解（最核心）
```
小说全文 → Sub-Scripts (章节/幕, ≤20) → Scenes (场景) → Shots (镜头)
```
**每一层都由独立的 LLM Agent + 独立的 CoT Prompt 负责**，而不是一次性让 LLM 输出所有镜头。

#### ② 输入极简化
只需 `{ "MovieScript": "故事摘要", "Character": ["角色名"] }` + 角色参考图，系统全自动。

如果输入是小说，只需提取摘要即可，不需要用户手动写分镜。

#### ③ CoT 强制推理
每个 Prompt 都要求 LLM 先输出 `Internal Chain-of-Thought`，再输出最终结果。这样：
- LLM "想清楚再写"，输出质量更高
- 推理过程可审计
- 出错时知道是哪个推理步骤有问题

#### ④ 双版本 Prompt + 督导
- 每个阶段有 CoT 版和非 CoT 版
- `scriptsupervisor-sys` 可以审查编剧输出（虽然代码中注释掉了）
- 为质量把控预留了机制

#### ⑤ Coarse Plot vs Visual Description
镜头有两种描述：
- `Coarse Plot`: 无人名、≤20 词，给 ROICtrl（用边界框定位角色）
- `Plot/Visual Description`: 详细、≥30 词，给其他模型

这种**针对不同生成模型定制不同粒度的 prompt** 的思路值得借鉴。

#### ⑥ 文件名即序列
`"Sub-Script_1|Scene_1|Shot_1.mp4"` → 按文件名排序即得到正确的时间线顺序。

### 9.3 可以忽略的部分

- `ToolBox` 评估模块（VBench / CLIP 等）—— 学术评估用，生产不需要
- `open-prompt-sys` / `open-plan-sys` —— 图像生成模型评估，与电影生成无关
- 14 个本地模型实现 —— 我们用 API 调用替代
