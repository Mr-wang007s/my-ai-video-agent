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
- 主对话负责检查 CoT 完整性（每层输出后自检）
- 如果 CoT 缺失或过于简略，该层输出应被拒绝并要求重新生成

## CoT 质量下限（新增）

### 最低字数要求

| 层级 | 步骤 | 最低要求 |
|------|------|----------|
| Layer 1 | 每步 | ≥2 句有意义分析 |
| Layer 2 | Step 1-3 | ≥2 句 |
| Layer 2 | Step 4 | ≥2 句/场景 |
| Layer 3 | Step 1-2, 4-5 | ≥2 句 |
| Layer 3 | Step 3 | ≥1 句/角色 |
| Layer 3 | Step 6 | ≥1 句/对白行 |

### 自动校验规则

在每层输出后，必须执行以下检查：

1. **步骤完整性**：检查 CoT 对象的 key 数量是否匹配规范（Layer 1=5, Layer 2=4, Layer 3=6）
2. **内容非空**：每个步骤的值不为空字符串、不为 "{}" 
3. **句子数量**：按上表检查最低句子数（以句号/问号/感叹号计数）
4. **实质性内容**：步骤中不得仅包含重复的模板文字或占位符

### 校验失败处理

- 如果 CoT 校验失败，该层输出应被 **拒绝并要求重新生成**
- 最多重试 2 次，如果仍不合格则记录警告并继续（避免阻塞流水线）

## 独立上下文原则

- 每层的每次调用使用独立上下文（对应 MovieAgent 的 `use_history=False`）
- 不在 LLM 调用间累积历史消息
- 每次调用只发送 System Prompt + 当前 User Message
