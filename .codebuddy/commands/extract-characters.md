---
name: extract-characters
description: "Step 3a: 提取角色 — 从剧本自动提取所有角色信息，写入 characters.json，不生成图片"
---

## 前置条件

- 项目状态为 `imported`
- `projects/{project_id}/script_synopsis.json` 已存在

## 必须加载的 Skill

```
use_skill("script-parser")
use_skill("character-design")
use_skill("character-acting")
```

## Team 调度

本步骤使用 `character-acting` Team 进行角色深度分析：

```
TeamCreate: character-acting-{project_id}
Spawn:
  - casting-director (coordinator) — 协调角色分析任务
  - personality-writer (specialist) — 角色性格、背景故事、行为模式分析
  - voice-designer (specialist) — 配音风格、语气、情感映射设计
  - character-reviewer (reviewer) — 角色一致性和完整性审核
```

**协作流程**：
1. casting-director 读取 script_synopsis.json，将角色列表分发给专家
2. personality-writer 和 voice-designer 并行处理每个角色
3. character-reviewer 审核所有角色的完整性和一致性
4. casting-director 合并结果，写入 characters.json
5. TeamDelete 清理资源

## 执行步骤

1. **验证前置条件**：
   ```
   Read: projects/{project_id}/status.json
   ```
   确认状态为 `imported`。

2. **读取输入**：
   ```
   Read: projects/{project_id}/script_synopsis.json
   Read: projects/{project_id}/raw_script.txt
   ```

3. **提取角色信息**：通过 character-acting Team 执行，对每个角色提取：
   - 名称、描述、外观描述、角色关系、配音设置、风格关键词
   - 性格特征、行为模式（personality-writer）
   - 声音特征、语气风格（voice-designer）
   - 所有角色 `design_status` 初始为 `extracted`

4. **写入 characters.json**：
   ```
   Write: projects/{project_id}/characters.json
   ```

5. **更新状态**：
   ```
   Write: projects/{project_id}/status.json  ← {"status": "characters_extracted", "updated_at": "..."}
   ```

6. **向用户展示结果**并提示下一步：
   - `/design-characters {角色名}` 逐个设计
   - `/design-characters all` 批量设计

## 注意事项

- **不消耗图像 API**：纯文本分析
- 外观描述不完整时标注"待用户补充"
- 所有数据通过文件系统读写，不依赖 MCP 或数据库
