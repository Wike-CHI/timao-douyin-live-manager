# 科大讯飞星火 Lite 模型集成说明

## 概述

本项目已集成科大讯飞星火 Lite 模型，用于以下核心AI功能：
- **AI分析**：实时分析直播内容和观众互动
- **话术生成**：智能生成符合场景的直播话术
- **直播间氛围与情绪分析**：评估直播间氛围状态和观众情绪

讯飞星火 Lite 模型提供**免费额度**，适合测试和小规模使用。

## 配置说明

### 1. 环境变量配置

在项目根目录的 `.env` 文件中添加以下配置：

```bash
# 科大讯飞星火 API 配置
XUNFEI_API_KEY=your_appid:your_api_secret
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1
XUNFEI_MODEL=lite
```

**获取 API Key：**
1. 访问 [讯飞开放平台](https://www.xfyun.cn/)
2. 注册并登录账号
3. 创建应用，获取 APPID 和 APISecret
4. API Key 格式为：`APPID:APISecret`（中间用冒号连接）

### 2. 可用模型

| 模型ID | 模型名称 | 定价 | 特点 |
|--------|---------|------|------|
| `lite` | 讯飞星火-Lite | 免费 | 适合测试和小规模使用 |
| `generalv3` | 讯飞星火-V3.0 | 0.003元/1K tokens | 通用场景 |
| `generalv3.5` | 讯飞星火-V3.5 | 0.0036元/1K tokens | 增强版本 |
| `4.0Ultra` | 讯飞星火-V4.0 Ultra | 0.005元/1K tokens | 最强性能 |

**默认使用 `lite` 模型（免费）**

## API 接口

### 1. 测试连接

**端点：** `POST /api/ai/xunfei/test`

**请求示例：**
```bash
curl -X POST http://localhost:9019/api/ai/xunfei/test \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}'
```

**响应示例：**
```json
{
  "success": true,
  "message": "连接成功",
  "response": "你好！我是科大讯飞研发的认知智能大模型...",
  "model": "lite",
  "usage": {
    "prompt_tokens": 5,
    "completion_tokens": 20,
    "total_tokens": 25,
    "request_time_ms": 850.5
  }
}
```

### 2. 氛围与情绪分析

**端点：** `POST /api/ai/xunfei/analyze/atmosphere`

**功能：** 分析直播间氛围状态、观众情绪、互动参与度

**请求体：**
```json
{
  "transcript": "大家好，欢迎来到我的直播间...",
  "comments": [
    {"user": "用户1", "content": "主播好！"},
    {"user": "用户2", "content": "666"}
  ],
  "context": {
    "duration_minutes": 30,
    "viewer_count": 150
  },
  "user_id": "user_123",
  "anchor_id": "anchor_456",
  "session_id": "session_789"
}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "atmosphere": {
      "level": "活跃",
      "score": 75,
      "description": "直播间氛围良好，观众参与度较高"
    },
    "emotion": {
      "primary": "兴奋",
      "secondary": "好奇",
      "intensity": 70
    },
    "engagement": {
      "interaction_rate": 65,
      "positive_rate": 80
    },
    "trends": [
      "观众情绪逐渐升温",
      "互动频率增加"
    ],
    "suggestions": [
      "保持当前节奏",
      "可以适当增加互动环节"
    ]
  },
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 80,
    "total_tokens": 230,
    "request_time_ms": 1200.3
  }
}
```

### 3. 话术生成

**端点：** `POST /api/ai/xunfei/generate/script`

**功能：** 智能生成直播话术

**话术类型：**
- `interaction`: 互动引导话术
- `engagement`: 关注点赞召唤话术
- `clarification`: 澄清回应话术
- `humor`: 幽默活跃话术
- `transition`: 转场过渡话术
- `call_to_action`: 行动召唤话术

**请求体：**
```json
{
  "script_type": "interaction",
  "context": {
    "current_topic": "产品介绍",
    "atmosphere": "活跃",
    "viewer_count": 200
  },
  "user_id": "user_123",
  "anchor_id": "anchor_456",
  "session_id": "session_789"
}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "line": "宝宝们有没有想了解的问题呀？打在公屏上让我看到！",
    "tone": "热情",
    "tags": ["互动", "引导", "提问"]
  },
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150,
    "request_time_ms": 800.5
  }
}
```

### 4. 实时分析

**端点：** `POST /api/ai/xunfei/analyze/realtime`

**功能：** 对直播窗口进行实时分析，输出节奏复盘、亮点识别、风险预警等

**请求体：**
```json
{
  "transcript": "刚才给大家介绍了新品的特点...",
  "comments": [
    {"user": "用户1", "content": "价格多少？"},
    {"user": "用户2", "content": "什么时候发货？"}
  ],
  "previous_summary": "上一窗口氛围良好，观众积极参与",
  "user_id": "user_123",
  "anchor_id": "anchor_456",
  "session_id": "session_789"
}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "summary": "本窗口主播完成产品介绍，观众关注价格和发货信息",
    "highlight_points": [
      "产品特点讲解清晰",
      "观众提问积极"
    ],
    "risks": [
      "价格问题未及时回应",
      "可能影响购买决策"
    ],
    "suggestions": [
      "及时回应价格和发货问题",
      "可以设置限时优惠增加紧迫感"
    ],
    "scripts": [
      {
        "text": "看到有宝宝问价格，现在下单只要XX元，限时优惠哦！",
        "type": "clarification",
        "tags": ["回应", "价格", "促销"]
      }
    ],
    "atmosphere": {
      "level": "活跃",
      "score": 75
    },
    "emotion": {
      "primary": "好奇",
      "intensity": 70
    }
  },
  "usage": {
    "prompt_tokens": 200,
    "completion_tokens": 120,
    "total_tokens": 320,
    "request_time_ms": 1500.8
  }
}
```

### 5. 聊天完成（通用接口）

**端点：** `POST /api/ai/xunfei/chat/completions`

**功能：** OpenAI 兼容的聊天完成接口

**请求体：**
```json
{
  "messages": [
    {"role": "system", "content": "你是一位专业的直播助手"},
    {"role": "user", "content": "如何提升直播间互动率？"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000,
  "user_id": "user_123"
}
```

### 6. 使用统计

**端点：** `GET /api/ai/xunfei/usage/stats?days=7`

**功能：** 查询讯飞模型的使用统计

**响应示例：**
```json
{
  "success": true,
  "period_days": 7,
  "total": {
    "calls": 150,
    "tokens": 45000,
    "cost": 0.0
  },
  "by_model": {
    "lite": {
      "calls": 150,
      "total_tokens": 45000,
      "cost": 0.0
    }
  }
}
```

## Token 消耗监控

所有讯飞 API 调用都会自动记录到 AI 使用监控系统中：

### 查看整体统计

```bash
# 查看今日统计
curl http://localhost:9019/api/ai_usage/stats/current

# 查看模型定价
curl http://localhost:9019/api/ai_usage/models/pricing
```

### 功能名称映射

监控系统会自动识别以下功能：
- `直播间氛围与情绪分析`
- `话术生成`
- `实时分析`
- `聊天完成`
- `测试连接`

## Python 客户端示例

```python
from server.ai.xunfei_lite_client import get_xunfei_client

# 初始化客户端
client = get_xunfei_client()

# 1. 测试连接
content, usage = client.chat_completion(
    messages=[{"role": "user", "content": "你好"}]
)
print(f"响应: {content}")
print(f"Token消耗: {usage.total_tokens}")

# 2. 氛围分析
result = client.analyze_live_atmosphere(
    transcript="欢迎大家来到直播间...",
    comments=[
        {"user": "观众1", "content": "主播好！"}
    ]
)
print(f"氛围等级: {result['atmosphere']['level']}")
print(f"Token消耗: {result['_usage']['total_tokens']}")

# 3. 话术生成
result = client.generate_script(
    script_type="interaction",
    context={"topic": "产品介绍"}
)
print(f"话术: {result['line']}")
print(f"Token消耗: {result['_usage']['total_tokens']}")
```

## 集成到现有服务

### 替换默认 AI 模型

如果要将讯飞 Lite 作为默认模型，可以修改相关服务的配置：

**方式 1：环境变量配置**
```bash
# .env 文件
AI_SERVICE=xunfei
AI_API_KEY=your_appid:your_api_secret
AI_BASE_URL=https://spark-api-open.xf-yun.com/v1
AI_MODEL=lite
```

**方式 2：代码集成**
```python
from server.ai.xunfei_lite_client import get_xunfei_client

# 在 AI 服务中使用讯飞客户端
client = get_xunfei_client()

# 调用分析接口
result = client.analyze_realtime(
    transcript=transcript,
    comments=comments,
    previous_summary=prev_summary
)
```

## 最佳实践

### 1. Token 消耗优化
- 截断过长的转写文本（建议保留最近 2000 字符）
- 限制弹幕数量（建议最多 100 条）
- 使用窗口分析而非全量分析

### 2. 错误处理
```python
try:
    client = get_xunfei_client()
    result = client.analyze_live_atmosphere(...)
except ValueError as e:
    # API Key 未配置
    logger.error(f"配置错误: {e}")
except Exception as e:
    # API 调用失败
    logger.error(f"调用失败: {e}")
```

### 3. 性能优化
- 批量处理：将多个短文本合并后再调用
- 异步调用：使用异步方式避免阻塞
- 缓存结果：对相似输入使用缓存

## 成本估算

以 Lite 模型（免费）为例：
- 每次氛围分析：约 200-300 tokens
- 每次话术生成：约 100-200 tokens
- 每次实时分析：约 300-500 tokens

**日均调用 1000 次的成本：**
- Lite 模型：¥0.00（免费）
- V3.0 模型：约 ¥1.20
- V3.5 模型：约 ¥1.44

## 注意事项

1. **API Key 格式**：必须是 `APPID:APISecret` 格式
2. **免费额度**：Lite 模型有每日调用限制，详见讯飞官网
3. **内容合规**：输入内容需符合相关法规要求
4. **Token 限制**：单次请求不超过 8000 tokens

## 故障排查

### 1. 连接失败
```
Error: XUNFEI_API_KEY 未配置
```
**解决方案：** 在 `.env` 文件中配置 `XUNFEI_API_KEY`

### 2. API 调用失败
```
Error: Invalid API key format
```
**解决方案：** 检查 API Key 格式是否为 `APPID:APISecret`

### 3. Token 消耗异常
**解决方案：** 查看监控日志 `GET /api/ai_usage/stats/current`

## 技术支持

- 讯飞开放平台：https://www.xfyun.cn/
- API 文档：https://www.xfyun.cn/doc/spark/Web.html
- 项目 Issue：提交到项目 GitHub Issues

## 更新日志

### v1.0.0 (2025-11-03)
- ✅ 集成讯飞星火 Lite 模型
- ✅ 支持氛围与情绪分析
- ✅ 支持话术生成
- ✅ 支持实时分析
- ✅ 集成 Token 消耗监控
- ✅ 添加使用统计 API

