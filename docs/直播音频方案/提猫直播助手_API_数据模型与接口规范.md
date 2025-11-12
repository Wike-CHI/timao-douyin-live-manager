# 提猫直播助手 - 数据模型与接口规范

## 1. 数据模型设计

### 1.1 评论数据模型 (Comment)

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Comment:
    """直播评论数据模型"""
    id: str                    # 评论唯一标识
    user_id: str              # 用户ID
    username: str             # 用户昵称
    content: str              # 评论内容
    timestamp: datetime       # 评论时间戳
    room_id: str              # 直播间ID
    user_level: Optional[int] = None    # 用户等级
    is_vip: bool = False      # 是否VIP用户
    gift_count: Optional[int] = None    # 礼物数量
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'room_id': self.room_id,
            'user_level': self.user_level,
            'is_vip': self.is_vip,
            'gift_count': self.gift_count
        }
```

### 1.2 热词数据模型 (HotWord)

```python
@dataclass
class HotWord:
    """热词数据模型"""
    word: str                 # 热词内容
    count: int               # 出现次数
    score: float             # 热度分数
    trend: str               # 趋势 (up/down/stable)
    last_updated: datetime   # 最后更新时间
    category: Optional[str] = None  # 词汇分类
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'word': self.word,
            'count': self.count,
            'score': self.score,
            'trend': self.trend,
            'last_updated': self.last_updated.isoformat(),
            'category': self.category
        }
```

### 1.3 AI话术数据模型 (Tip)

```python
@dataclass
class Tip:
    """AI话术数据模型"""
    id: str                   # 话术唯一标识
    content: str             # 话术内容
    type: str                # 话术类型 (greeting/interaction/promotion)
    confidence: float        # 置信度分数
    generated_at: datetime   # 生成时间
    source_comments: list[str]  # 源评论ID列表
    hot_words: list[str]     # 相关热词
    is_used: bool = False    # 是否已使用
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'content': self.content,
            'type': self.type,
            'confidence': self.confidence,
            'generated_at': self.generated_at.isoformat(),
            'source_comments': self.source_comments,
            'hot_words': self.hot_words,
            'is_used': self.is_used
        }
```

### 1.4 配置数据模型 (Config)

```python
@dataclass
class Config:
    """应用配置数据模型"""
    ai_provider: str         # AI服务提供商
    room_id: str            # 直播间ID
    comment_buffer_size: int # 评论缓冲区大小
    hotword_update_interval: int  # 热词更新间隔
    ai_tip_interval: int    # AI话术生成间隔
    auto_mode: bool = True  # 是否自动模式
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'ai_provider': self.ai_provider,
            'room_id': self.room_id,
            'comment_buffer_size': self.comment_buffer_size,
            'hotword_update_interval': self.hotword_update_interval,
            'ai_tip_interval': self.ai_tip_interval,
            'auto_mode': self.auto_mode
        }
```

## 2. API 接口规范

### 2.1 基础响应格式

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2024-01-20T10:30:00Z",
  "code": 200
}
```

### 2.2 健康检查接口

**GET** `/api/health`

**响应示例:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 3600,
    "services": {
      "comment_ingest": "running",
      "nlp_processor": "running",
      "ai_generator": "running"
    }
  },
  "message": "服务运行正常",
  "timestamp": "2024-01-20T10:30:00Z",
  "code": 200
}
```

### 2.3 评论流推送接口 (Server-Sent Events)

**GET** `/api/stream/comments`

**Headers:**
```
Accept: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**响应格式:**
```
data: {"id": "comment_123", "user_id": "user_456", "username": "用户昵称", "content": "评论内容", "timestamp": "2024-01-20T10:30:00Z", "room_id": "room_789"}

data: {"id": "comment_124", "user_id": "user_457", "username": "另一个用户", "content": "另一条评论", "timestamp": "2024-01-20T10:30:01Z", "room_id": "room_789"}
```

### 2.4 热词排行接口

**GET** `/api/hotwords`

**查询参数:**
- `limit` (可选): 返回数量限制，默认10
- `category` (可选): 词汇分类过滤

**响应示例:**
```json
{
  "success": true,
  "data": {
    "hotwords": [
      {
        "word": "好看",
        "count": 156,
        "score": 89.5,
        "trend": "up",
        "last_updated": "2024-01-20T10:29:00Z",
        "category": "positive"
      },
      {
        "word": "主播",
        "count": 134,
        "score": 78.2,
        "trend": "stable",
        "last_updated": "2024-01-20T10:29:00Z",
        "category": "neutral"
      }
    ],
    "total": 2,
    "updated_at": "2024-01-20T10:29:00Z"
  },
  "message": "获取热词成功",
  "timestamp": "2024-01-20T10:30:00Z",
  "code": 200
}
```

### 2.5 最新话术接口

**GET** `/api/tips/latest`

**查询参数:**
- `type` (可选): 话术类型过滤
- `limit` (可选): 返回数量限制，默认5

**响应示例:**
```json
{
  "success": true,
  "data": {
    "tips": [
      {
        "id": "tip_001",
        "content": "感谢大家的支持，看到这么多朋友说好看，主播很开心呢！",
        "type": "interaction",
        "confidence": 0.92,
        "generated_at": "2024-01-20T10:28:00Z",
        "source_comments": ["comment_123", "comment_124"],
        "hot_words": ["好看", "主播"],
        "is_used": false
      }
    ],
    "total": 1,
    "generated_at": "2024-01-20T10:28:00Z"
  },
  "message": "获取话术成功",
  "timestamp": "2024-01-20T10:30:00Z",
  "code": 200
}
```

### 2.6 标记话术已使用接口

**PUT** `/api/tips/{tip_id}/used`

**响应示例:**
```json
{
  "success": true,
  "data": {
    "tip_id": "tip_001",
    "is_used": true,
    "updated_at": "2024-01-20T10:30:00Z"
  },
  "message": "话术状态更新成功",
  "timestamp": "2024-01-20T10:30:00Z",
  "code": 200
}
```

### 2.7 配置管理接口

**GET** `/api/config`

**响应示例:**
```json
{
  "success": true,
  "data": {
    "ai_provider": "deepseek",
    "room_id": "room_789",
    "comment_buffer_size": 1000,
    "hotword_update_interval": 5,
    "ai_tip_interval": 10,
    "auto_mode": true
  },
  "message": "获取配置成功",
  "timestamp": "2024-01-20T10:30:00Z",
  "code": 200
}
```

**POST** `/api/config`

**请求体:**
```json
{
  "ai_provider": "openai",
  "room_id": "room_789",
  "comment_buffer_size": 1500,
  "hotword_update_interval": 3,
  "ai_tip_interval": 8,
  "auto_mode": false
}
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "updated_fields": ["ai_provider", "comment_buffer_size", "hotword_update_interval", "ai_tip_interval", "auto_mode"],
    "config": {
      "ai_provider": "openai",
      "room_id": "room_789",
      "comment_buffer_size": 1500,
      "hotword_update_interval": 3,
      "ai_tip_interval": 8,
      "auto_mode": false
    }
  },
  "message": "配置更新成功",
  "timestamp": "2024-01-20T10:30:00Z",
  "code": 200
}
```

## 3. 错误响应格式

### 3.1 标准错误响应

```json
{
  "success": false,
  "data": null,
  "message": "错误描述",
  "error": {
    "code": "ERROR_CODE",
    "details": "详细错误信息"
  },
  "timestamp": "2024-01-20T10:30:00Z",
  "code": 400
}
```

### 3.2 常见错误码

| HTTP状态码 | 错误码 | 描述 |
|-----------|--------|------|
| 400 | INVALID_PARAMS | 请求参数无效 |
| 401 | UNAUTHORIZED | 未授权访问 |
| 404 | NOT_FOUND | 资源不存在 |
| 429 | RATE_LIMIT | 请求频率超限 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |
| 503 | SERVICE_UNAVAILABLE | 服务不可用 |

## 4. WebSocket 接口 (可选扩展)

### 4.1 实时数据推送

**连接地址:** `ws://127.0.0.1:5001/ws`

**消息格式:**
```json
{
  "type": "comment|hotword|tip",
  "data": {},
  "timestamp": "2024-01-20T10:30:00Z"
}
```

**示例消息:**
```json
{
  "type": "comment",
  "data": {
    "id": "comment_123",
    "username": "用户昵称",
    "content": "评论内容",
    "timestamp": "2024-01-20T10:30:00Z"
  },
  "timestamp": "2024-01-20T10:30:00Z"
}
```

## 5. 数据流约定

### 5.1 评论处理流程

1. **评论抓取** → Comment对象
2. **内容过滤** → 过滤敏感内容
3. **存储缓冲** → 环形缓冲区
4. **实时推送** → SSE/WebSocket
5. **热词分析** → HotWord对象
6. **AI处理** → Tip对象

### 5.2 数据同步策略

- **评论流**: 实时推送，无缓存
- **热词数据**: 5秒更新周期，本地缓存
- **AI话术**: 10秒生成周期，持久化存储
- **配置数据**: 变更时立即同步

## 6. 性能指标

### 6.1 响应时间要求

- 健康检查: < 100ms
- 热词查询: < 200ms
- 话术查询: < 300ms
- 配置操作: < 500ms

### 6.2 并发处理能力

- 最大并发连接: 100
- SSE连接数: 50
- 评论处理速率: 1000条/秒

### 6.3 数据容量限制

- 评论缓冲区: 1000条
- 热词缓存: 100个
- 话术历史: 50条