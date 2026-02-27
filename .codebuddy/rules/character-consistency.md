# 角色一致性检查规则

## 必须执行的一致性保障

### character_list/ 资产库（MovieAgent 格式）
- 每个已设计角色**必须**有 `character_list/{CharName}/` 目录
- 目录中**必须**包含 `best.png`（最佳参考图）和 `best.txt`（`<TOK>` 描述）
- `best.txt` **必须**以 `<TOK>` 开头，使用英文描述角色外观
- 推荐包含 3-5 张多角度参考图（photo_1.png ~ photo_5.png）

### Seedance 2.0 @ 引用（首要手段）
- 每次调用 Seedance 生成视频时，**必须**在 `image_paths` 中传入角色的 `best.png`
- 在 `video_prompt` 中**必须**用 `@ImageN 作为{角色名}外观` 指定角色参考
- 多角色场景中，每个角色都需要独立的 `best.png` 和 @ 引用
- @Image 编号按 `image_paths` 数组顺序，角色参考图在前，首帧图在最后

### Prompt 工程（辅助手段）
- 每个分镜图 `image_prompt` 中**必须**包含角色外观描述（来自 `<TOK>` 描述去掉 `<TOK>` 前缀）
- `image_prompt` 中**禁止**使用角色名（对应 MovieAgent 的 Coarse Plot 思路）
- **禁止**改写、缩写或省略外观描述
- 不同镜头中同一角色的描述文字必须完全一致

### 多角色画面
- 使用边界框 `[x1, y1, x2, y2]` 定位角色（归一化坐标 [0,1]）
- 每镜头最多 3 个角色（推荐 1-2）
- 边界框不得重叠
- 注意身高比例一致性

## 检查清单

### 角色提取阶段（/extract-characters）
- [ ] characters.json 包含所有有名角色
- [ ] 每个角色有外观描述（appearance_description）
- [ ] design_status 初始为 "extracted"

### 角色设计阶段（/design-characters）
- [ ] best.png 清晰展示角色全部外观特征
- [ ] best.txt 使用 `<TOK>` 开头的英文描述
- [ ] 至少 3 张多角度参考图，风格一致
- [ ] characters.json 中 design_status 为 "designed"
- [ ] tok_description 和 asset_dir 已正确填入
- [ ] 角色外观描述具体、可重复（无模糊词汇）

### 分镜拆解阶段（/break-script）
- [ ] Shot 中 image_prompt 不含角色名
- [ ] Shot 中 video_prompt 的 @Image 编号正确
- [ ] 仅为有 character_list 资产的角色添加 @Image 引用

### 视频生成阶段（/generate-video）
- [ ] 每次 Seedance 调用的 `image_paths` 包含角色 best.png
- [ ] `video_prompt` 中 @ 引用与 image_paths 顺序匹配
- [ ] 角色发型、发色在所有镜头中一致
- [ ] 角色服装在同一场景中一致（除非有换装情节）
- [ ] 角色体型/身高比例在所有镜头中一致
- [ ] 标志性特征（眼镜、疤痕、饰品）在所有镜头中出现

### 最终审查
- [ ] 连续观看所有镜头，角色可辨识
- [ ] 不同场景间角色外观无跳变
- [ ] 多角色画面中角色不会混淆
