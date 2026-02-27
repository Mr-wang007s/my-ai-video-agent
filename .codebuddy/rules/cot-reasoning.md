# CoT 推理规则

## 强制要求

在 MovieAgent 式分层拆解（`/break-script`）的每一层中，LLM **必须**先输出 `Internal Chain-of-Thought` 字段，再输出结构化结果。

### 禁止跳过推理

- **禁止**直接输出 Sub-Script / Scene / Shot 列表而不包含 CoT
- **禁止**将 CoT 字段设为空对象 `{}`
- 每个 CoT 步骤必须有 **实质性内容**（≥1 句有意义的分析）

### Layer 1 CoT（编剧）必填步骤

```json
{
  "Internal Chain-of-Thought": {
    "Step 1: Core Narrative Structure": "...",     // 必填
    "Step 2: Key Character Information": "...",    // 必填
    "Step 3: Temporal Segmentation": "...",         // 必填
    "Step 4: Sub-Script Breakdown Criteria": "...",// 必填
    "Step 5: Division Rationale": "..."            // 必填
  }
}
```

### Layer 2 CoT（场景规划）必填步骤

```json
{
  "Internal Chain-of-Thought": {
    "Step 1: Narrative Structure": "...",           // 必填
    "Step 2: Key Scene Elements": "...",            // 必填
    "Step 3: Scene Boundaries": "...",              // 必填
    "Step 4: Cinematic Elements for Each Scene": "..." // 必填
  }
}
```

### Layer 3 CoT（镜头创建）必填步骤

```json
{
  "Internal Chain-of-Thought": {
    "Step 1: Break Down Scene into Key Shots": "...",    // 必填
    "Step 2: Shot Composition and Framing": "...",       // 必填
    "Step 3: Character Positioning & Bounding Boxes": "...", // 必填
    "Step 4: Emotional Impact": "...",                   // 必填
    "Step 5: Camera Techniques and Movements": "...",    // 必填
    "Step 6: Dialogue & Subtitle Accuracy": "..."        // 必填
  }
}
```

## 审计与质量

- CoT 推理过程会被保存在 `script_breakdown.json` 中，可审计
- script-supervisor agent 会检查 CoT 完整性
- 如果 CoT 缺失或过于简略，该层输出应被拒绝并要求重新生成

## 独立上下文原则

- 每层的每次调用使用独立上下文（对应 MovieAgent 的 `use_history=False`）
- 不在 LLM 调用间累积历史消息
- 每次调用只发送 System Prompt + 当前 User Message
