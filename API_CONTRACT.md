# 📡 提猫直播助手 - API 接口契约

> **版本**: v1.0.0 | **基础路径**: `http://127.0.0.1:10090` | **更新**: 2025-10-26

---

## 📋 接口总览

| 模块 | 接口数 | 说明 |
|------|--------|------|
| AI 使用监控 | 11 | Token 消耗、成本统计、报告导出 |
| 直播音频转写 | 4 + WS | 音频流拉取、实时转写、状态管理 |
| 抖音直播 | 3 | 弹幕抓取、状态查询 |
| AI 实时分析 | 3 | 直播分析、话术生成 |
| NLP 管理 | 2 | 热词配置 |
| 系统工具 | 2 | 健康检查、文档 |

---

## 🔐 通用规范

### 请求格式

```http
Content-Type: application/json
Authorization: Bearer <token>  # 可选
```

### 响应格式

**成功**
```json
{"success": true, "data": {...}, "message": "操作成功"}
```

**失败**
```json
{"success": false, "error": {"code": "ERROR_CODE", "message": "错误描述"}}
```

---

## 📊 AI 使用监控 API

### GET /api/ai_usage/stats/current
获取实时统计（当前小时 + 今日）

**响应**
```json
{
  "current_hour": {"calls": 36, "tokens": 97200, "cost": 2.94},
  "today": {"calls": 360, "tokens": 972000, "cost": 29.52}
}
```

### GET /api/ai_usage/stats/daily?days_ago=0
获取每日统计

**参数**: `days_ago` (0=今天, 1=昨天)

### GET /api/ai_usage/stats/monthly?year=2025&month=10
获取月度统计

### GET /api/ai_usage/top_users?limit=10&days=7
Top 用户排行

### GET /api/ai_usage/cost_trend?days=30
成本趋势（按天）

### GET /api/ai_usage/dashboard
仪表盘综合数据

**响应**
```json
{
  "today": {"calls": 540, "cost": 36.60, "success_rate": 99.07},
  "this_month": {"calls": 14040, "cost": 951.60},
  "top_users": [...],
  "cost_trend_7days": [...]
}
```

### POST /api/ai_usage/export_report?days=7
导出报告

**响应**: `{"report_path": "...", "download_url": "..."}`

---

## 🎤 直播音频转写 API

### POST /api/live_audio/start
启动音频转写

**请求体**
```json
{
  "liveUrl": "https://live.douyin.com/123456",
  "sessionId": "session_789",
  "profile": "stable"
}
```

### POST /api/live_audio/stop
停止转写

### GET /api/live_audio/status
获取状态

**响应**
```json
{
  "is_running": true,
  "live_id": "123456",
  "session_id": "session_789"
}
```

### WS /api/live_audio/ws
WebSocket 实时转写

**消息格式**
```json
{
  "type": "sentence",
  "text": "大家好，欢迎来到我的直播间",
  "speaker": "host",
  "timestamp": 1729932123.45
}
```

---

## 💬 抖音直播 API

### POST /api/douyin/start
启动弹幕抓取

**请求**: `{"liveUrl": "https://live.douyin.com/123456"}`

### POST /api/douyin/stop
停止抓取

### GET /api/douyin/status
获取状态

---

## 🤖 AI 实时分析 API

### POST /api/ai_live/start
开启 AI 分析

**请求**: `{"anchorId": "anchor_123", "sessionId": "session_789"}`

### POST /api/ai_live/stop
停止分析

### GET /api/ai_live/status
获取状态

---

## 💡 AI 话术生成 API

### POST /api/ai_scripts/generate_answer
生成回答话术

**请求**
```json
{
  "question": "主播你的衣服在哪买的？",
  "context": {"anchor_id": "anchor_123"}
}
```

**响应**
```json
{
  "answers": ["这件是某宝买的，链接在我的购物车里哦~"],
  "confidence": 0.85
}
```

### POST /api/ai_scripts/generate_topics
生成互动话题

**请求**: `{"context": {...}, "limit": 6}`

**响应**: `{"topics": [{"topic": "...", "category": "日常互动"}]}`

---

## 🔧 数据模型

### UsageRecord (使用记录)
```typescript
{
  timestamp: number;
  model: string;
  function: string;
  input_tokens: number;
  output_tokens: number;
  cost: number;
  success: boolean;
}
```

### TranscriptMessage (转写消息)
```typescript
{
  type: 'sentence' | 'partial' | 'error';
  text: string;
  speaker: 'host' | 'guest';
  timestamp: number;
}
```

---

## ⚠️ 错误码

| 错误码 | HTTP | 说明 |
|--------|------|------|
| INVALID_REQUEST | 400 | 参数无效 |
| NOT_FOUND | 404 | 资源不存在 |
| ALREADY_RUNNING | 409 | 任务已运行 |
| INTERNAL_ERROR | 500 | 服务器错误 |

---

## 💻 使用示例

### JavaScript
```javascript
// 获取今日统计
const stats = await fetch('http://127.0.0.1:10090/api/ai_usage/stats/current')
  .then(r => r.json());

// 启动转写
await fetch('http://127.0.0.1:10090/api/live_audio/start', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({liveUrl: 'https://live.douyin.com/123456'})
});

// WebSocket
const ws = new WebSocket('ws://127.0.0.1:10090/api/live_audio/ws');
ws.onmessage = e => console.log(JSON.parse(e.data));
```

### Python
```python
import requests

BASE_URL = 'http://127.0.0.1:10090'

# 获取仪表盘
dashboard = requests.get(f'{BASE_URL}/api/ai_usage/dashboard').json()

# 导出报告
report = requests.post(f'{BASE_URL}/api/ai_usage/export_report?days=7').json()
```

---

**完整文档**: 访问 `http://127.0.0.1:10090/docs`
