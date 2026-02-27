# Seedance 2.0 API 接口文档

## 接入信息

- 服务商：火山引擎 - 火山方舟大模型服务平台
- 官方 API 文档：https://www.volcengine.com/docs/82379/1393047
- 创建视频任务 API：https://www.volcengine.com/docs/82379/1520757
- 查询视频任务 API：https://www.volcengine.com/docs/82379/1521309
- 体验平台：https://dreamina.capcut.com （即梦）
- 模型版本：Seedance 2.0

## 认证

使用火山方舟 API Key 进行 Bearer Token 认证。

环境变量：
- `ARK_API_KEY`：火山方舟 API Key
- `ARK_BASE_URL`：API 基础地址（默认 https://ark.cn-beijing.volces.com/api/v3）
- `SEEDANCE_MODEL`：模型标识（默认 doubao-seedance-2-0-pro-250224）

## API Key 获取

1. 访问 https://console.volcengine.com/ark
2. 创建 API Key
3. 将 Key 配置到 `.env` 文件中

## 主要接口

### 1. 创建视频生成任务

```
POST {ARK_BASE_URL}/video/generations
Content-Type: application/json
Authorization: Bearer {ARK_API_KEY}
```

#### 请求体

```json
{
  "model": "doubao-seedance-2-0-pro-250224",
  "content": [
    {
      "type": "image_url",
      "image_url": { "url": "https://example.com/image.jpg" }
    },
    {
      "type": "text",
      "text": "@Image1 作为首帧，角色缓缓转头 --dur 5 --rs 1080p --rt 16:9"
    }
  ]
}
```

#### content 数组元素类型

| type | 字段 | 说明 |
|------|------|------|
| `text` | `text` | 文本提示词（含参数后缀和 @ 引用） |
| `image_url` | `image_url.url` | 图片 URL 或 base64 data URI |
| `video_url` | `video_url.url` | 视频参考 URL |
| `audio_url` | `audio_url.url` | 音频参考 URL |

#### 参数后缀（附加在 text 末尾）

| 参数 | 格式 | 说明 |
|------|------|------|
| `--dur` | 4/5/10/15 | 视频时长（秒） |
| `--rs` | 720p/1080p | 分辨率 |
| `--rt` | 16:9/9:16/1:1/4:3/3:4/21:9 | 宽高比 |
| `--seed` | 0-999999 | 随机种子 |
| `--cf` | true/false | 固定镜头 |
| `--wm` | true/false | 水印 |

#### 响应

```json
{
  "id": "task_xxxxx",
  "status": "processing"
}
```

### 2. 查询视频生成任务

```
GET {ARK_BASE_URL}/video/generations/{task_id}
Authorization: Bearer {ARK_API_KEY}
```

#### 响应（成功）

```json
{
  "id": "task_xxxxx",
  "status": "succeeded",
  "output": {
    "video_url": "https://..."
  }
}
```

#### 响应（失败）

```json
{
  "id": "task_xxxxx",
  "status": "failed",
  "error": {
    "message": "..."
  }
}
```

### 3. 查询任务列表

```
GET {ARK_BASE_URL}/video/generations
Authorization: Bearer {ARK_API_KEY}
```

### 4. 取消/删除任务

```
DELETE {ARK_BASE_URL}/video/generations/{task_id}
Authorization: Bearer {ARK_API_KEY}
```

## 状态枚举

| 状态 | 说明 |
|------|------|
| processing | 生成中 |
| succeeded | 生成完成 |
| failed | 生成失败 |
| cancelled | 已取消 |

## 输入限制

| 项目 | 限制 |
|------|------|
| 图片数量 | 最多 9 张 |
| 视频数量 | 最多 3 段（总时长 ≤ 15s） |
| 音频数量 | 最多 3 段 MP3 |
| 图片格式 | JPEG, PNG, WebP |
| 图片大小 | 最大 10MB |
| 视频时长 | 4s / 5s / 10s / 15s |
| 分辨率 | 720p / 1080p |

## 重要注意事项

1. **视频 URL 有效期仅 24 小时**，生成成功后必须立即下载到本地
2. 生成速度约 40-60 秒（5s 视频），15s 视频可能需要 2-3 分钟
3. 生成成功率约 99.5%
4. 禁止生成违规内容
5. API Key 仅创建时显示一次，请妥善保管
6. **Seedance 2.0 生成的视频自带原生音轨**，包含音效和环境音，无需额外合成

## 音视频联合生成

Seedance 2.0 默认生成带音频的视频：

- **双声道立体声**：具有空间感的沉浸式音效
- **音画精准对齐**：音频节奏与视觉动作同步
- **高仿真音效**：还原环境音、动作音效、氛围音乐
- 可通过 Prompt 中的音频描述词控制音效类型

通过在 Prompt 中加入音效描述来控制生成的音频内容：
```
角色缓缓走在雨中。音效描述：细密的雨声，脚步踩在水洼上的声音，远处的雷鸣
```

## Python SDK 安装

```bash
pip install requests python-dotenv
```

## 完整示例

```python
import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ARK_API_KEY")
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 文生视频（带音效）
payload = {
    "model": "doubao-seedance-2-0-pro-250224",
    "content": [
        {
            "type": "text",
            "text": "一只金毛犬在秋天的落叶中奔跑，慢动作，电影感。音效：落叶沙沙声，狗的喘息声，轻快的背景音乐 --dur 5 --rs 1080p --rt 16:9"
        }
    ]
}

# 提交任务
resp = requests.post(f"{BASE_URL}/video/generations", headers=headers, json=payload, timeout=30)
task_id = resp.json()["id"]

# 轮询结果
for _ in range(60):
    time.sleep(5)
    result = requests.get(f"{BASE_URL}/video/generations/{task_id}", headers=headers).json()
    if result["status"] == "succeeded":
        video_url = result["output"]["video_url"]
        # 立即下载（URL 24h 有效）
        video_data = requests.get(video_url).content
        with open("output.mp4", "wb") as f:
            f.write(video_data)
        break
```
