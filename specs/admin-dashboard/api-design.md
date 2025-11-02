# 管理后台 API 接口设计

## 基础信息

- **Base URL**: `http://127.0.0.1:9019/api/admin`
- **认证方式**: JWT Bearer Token
- **Content-Type**: `application/json`

---

## 1. 用户管理 API

### 1.1 获取用户列表

```
GET /api/admin/users
```

**Query参数**:
```typescript
{
  page?: number;           // 页码，默认1
  perPage?: number;        // 每页数量，默认25
  filter?: {
    role?: 'user' | 'streamer' | 'assistant' | 'admin' | 'super_admin';
    status?: 'active' | 'inactive' | 'suspended' | 'banned';
    search?: string;        // 搜索用户名、邮箱、手机号
    created_from?: string; // ISO日期
    created_to?: string;   // ISO日期
  };
  sort?: string;           // "id", "-id", "created_at", "-created_at", "last_login_at"
}
```

**响应**:
```json
{
  "data": [
    {
      "id": 1,
      "username": "user1",
      "email": "user1@example.com",
      "phone": "13800138000",
      "nickname": "用户1",
      "role": "user",
      "status": "active",
      "email_verified": true,
      "login_count": 42,
      "last_login_at": "2025-11-01T10:00:00Z",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 1234,
  "page": 1,
  "perPage": 25
}
```

### 1.2 获取用户详情

```
GET /api/admin/users/:id
```

**响应**:
```json
{
  "data": {
    "id": 1,
    "username": "user1",
    "email": "user1@example.com",
    // ... 基本信息
    "subscription": {
      "id": 10,
      "plan": {
        "id": 2,
        "name": "premium",
        "display_name": "高级版"
      },
      "status": "active",
      "expires_at": "2025-12-01T00:00:00Z"
    },
    "stats": {
      "active_sessions": 2,
      "total_logins": 42
    },
    "audit_logs": [
      {
        "id": 100,
        "action": "login",
        "created_at": "2025-11-01T10:00:00Z"
      }
    ]
  }
}
```

### 1.3 创建用户

```
POST /api/admin/users
```

**请求体**:
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "SecurePass123!",
  "phone": "13900139000",
  "nickname": "新用户",
  "role": "user",
  "status": "active",
  "email_verified": true,
  "initial_plan_id": 2  // 可选
}
```

### 1.4 更新用户

```
PUT /api/admin/users/:id
```

**请求体** (所有字段可选):
```json
{
  "username": "updated_user",
  "email": "updated@example.com",
  "role": "streamer",
  "status": "active",
  "password": "NewPassword123!"  // 修改密码
}
```

### 1.5 删除用户

```
DELETE /api/admin/users/:id
```

**响应**:
```json
{
  "success": true,
  "message": "用户已删除"
}
```

### 1.6 解锁/锁定用户

```
POST /api/admin/users/:id/unlock
POST /api/admin/users/:id/lock
```

**请求体** (锁定):
```json
{
  "reason": "违反服务条款",
  "duration_days": 7  // 可选，默认永久
}
```

---

## 2. 支付管理 API

### 2.1 获取支付列表

```
GET /api/admin/payments
```

**Query参数**:
```typescript
{
  page?: number;
  perPage?: number;
  filter?: {
    status?: 'pending' | 'paid' | 'failed' | 'refunded' | 'cancelled';
    payment_method?: 'alipay' | 'wechat' | 'bank_card' | 'paypal' | 'stripe';
    user_id?: number;
    date_from?: string;
    date_to?: string;
    min_amount?: number;
    max_amount?: number;
  };
  sort?: string;
}
```

**响应**:
```json
{
  "data": [
    {
      "id": 100,
      "order_no": "ORD202511020001",
      "user": {
        "id": 1,
        "username": "user1",
        "email": "user1@example.com"
      },
      "amount": 99.00,
      "currency": "CNY",
      "payment_method": "alipay",
      "status": "paid",
      "paid_at": "2025-11-01T10:00:00Z",
      "created_at": "2025-11-01T09:55:00Z"
    }
  ],
  "total": 567,
  "page": 1,
  "perPage": 25
}
```

### 2.2 获取支付详情

```
GET /api/admin/payments/:id
```

### 2.3 手动标记已支付

```
POST /api/admin/payments/:id/mark-paid
```

**请求体**:
```json
{
  "third_party_order_id": "ALIPAY_ORDER_123",
  "notes": "手动确认支付"
}
```

### 2.4 退款

```
POST /api/admin/payments/:id/refund
```

**请求体**:
```json
{
  "reason": "用户申请退款",
  "amount": 99.00  // 可选，部分退款。不填则全额退款
}
```

### 2.5 导出支付记录

```
GET /api/admin/payments/export
```

**Query参数**:
```typescript
{
  format: 'csv' | 'excel';
  date_from: string;
  date_to: string;
  filter?: { /* 同列表过滤 */ };
}
```

**响应**: 文件下载

---

## 3. 订阅套餐管理 API

### 3.1 获取套餐列表

```
GET /api/admin/plans
```

**响应**:
```json
{
  "data": [
    {
      "id": 1,
      "name": "free",
      "display_name": "免费版",
      "plan_type": "free",
      "price": 0.00,
      "billing_cycle": 30,
      "max_streams": 1,
      "max_ai_requests": 100,
      "features": ["basic_transcribe", "basic_analysis"],
      "is_active": true,
      "subscription_count": 500
    }
  ]
}
```

### 3.2 获取套餐详情

```
GET /api/admin/plans/:id
```

### 3.3 创建套餐

```
POST /api/admin/plans
```

**请求体**:
```json
{
  "name": "new_plan",
  "display_name": "新套餐",
  "description": "套餐描述",
  "plan_type": "premium",
  "price": 199.00,
  "original_price": 299.00,
  "currency": "CNY",
  "billing_cycle": 30,
  "max_streams": 10,
  "max_storage_gb": 100,
  "max_ai_requests": 10000,
  "max_export_count": 50,
  "features": [
    "advanced_transcribe",
    "ai_analysis",
    "live_scripts",
    "report_generation"
  ],
  "is_active": true,
  "is_popular": false,
  "sort_order": 0
}
```

### 3.4 更新套餐

```
PUT /api/admin/plans/:id
```

**请求体**: 同创建，所有字段可选

### 3.5 删除套餐

```
DELETE /api/admin/plans/:id
```

**响应**:
```json
{
  "success": true,
  "message": "套餐已删除",
  "warning": "有 5 个用户正在使用此套餐"  // 如有
}
```

---

## 4. AI 监控 API

### 4.1 获取AI使用统计

```
GET /api/admin/ai/usage/stats
```

**Query参数**:
```typescript
{
  period?: 'hour' | 'day' | 'week' | 'month';
  start_date?: string;
  end_date?: string;
}
```

**响应**:
```json
{
  "period": "day",
  "start_time": "2025-11-01T00:00:00Z",
  "end_time": "2025-11-02T00:00:00Z",
  "total_calls": 15234,
  "successful_calls": 15120,
  "failed_calls": 114,
  "total_tokens": 5234567,
  "input_tokens": 3456789,
  "output_tokens": 1777778,
  "total_cost": 156.78,
  "by_model": {
    "qwen-plus": {
      "calls": 8000,
      "tokens": 3000000,
      "cost": 120.00
    },
    "deepseek-chat": {
      "calls": 7234,
      "tokens": 2234567,
      "cost": 36.78
    }
  },
  "by_function": {
    "live_analysis": {
      "calls": 5000,
      "tokens": 2000000,
      "cost": 80.00
    },
    "script_generation": {
      "calls": 3000,
      "tokens": 1500000,
      "cost": 60.00
    }
  }
}
```

### 4.2 获取Token消耗趋势

```
GET /api/admin/ai/usage/tokens/trend
```

**Query参数**:
```typescript
{
  group_by: 'hour' | 'day';  // 数据粒度
  start_date: string;
  end_date: string;
}
```

**响应**:
```json
{
  "data": [
    {
      "time": "2025-11-01T00:00:00Z",
      "tokens": 100000,
      "cost": 5.00
    },
    {
      "time": "2025-11-01T01:00:00Z",
      "tokens": 120000,
      "cost": 6.00
    }
  ]
}
```

### 4.3 获取成本分析

```
GET /api/admin/ai/usage/cost/analysis
```

**响应**:
```json
{
  "total_cost": 156.78,
  "average_cost_per_call": 0.0103,
  "cost_by_model": {
    "qwen-plus": 120.00,
    "deepseek-chat": 36.78
  },
  "cost_by_function": {
    "live_analysis": 80.00,
    "script_generation": 60.00,
    "live_review": 16.78
  },
  "trend": [
    // 趋势数据
  ]
}
```

---

## 5. 在线用户统计 API

### 5.1 获取在线用户数

```
GET /api/admin/online-users/count
```

**响应**:
```json
{
  "current": 456,
  "active_sessions": 478,
  "websocket_connections": 123,
  "trend_24h": [
    {
      "time": "2025-11-01T00:00:00Z",
      "count": 300
    },
    // ...
  ]
}
```

### 5.2 获取活跃会话列表

```
GET /api/admin/sessions/active
```

**Query参数**:
```typescript
{
  page?: number;
  perPage?: number;
}
```

**响应**:
```json
{
  "data": [
    {
      "id": "session_abc123",
      "user": {
        "id": 1,
        "username": "user1",
        "email": "user1@example.com"
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "device_info": "Windows 10, Chrome",
      "connected_at": "2025-11-02T10:00:00Z",
      "last_activity": "2025-11-02T10:05:00Z",
      "expires_at": "2025-11-02T18:00:00Z"
    }
  ],
  "total": 478
}
```

### 5.3 强制断开会话

```
POST /api/admin/sessions/:id/disconnect
```

---

## 6. 流水统计 API

### 6.1 获取收入统计

```
GET /api/admin/revenue/stats
```

**Query参数**:
```typescript
{
  period?: 'day' | 'week' | 'month' | 'year';
  start_date?: string;
  end_date?: string;
}
```

**响应**:
```json
{
  "total": 123456.78,
  "today": 1234.56,
  "this_week": 8765.43,
  "this_month": 34567.89,
  "trend": [
    {
      "date": "2025-11-01",
      "amount": 1234.56,
      "count": 15
    }
  ],
  "by_plan": {
    "basic": {
      "amount": 50000.00,
      "count": 500
    },
    "premium": {
      "amount": 73456.78,
      "count": 367
    }
  },
  "by_payment_method": {
    "alipay": {
      "amount": 60000.00,
      "count": 600
    },
    "wechat": {
      "amount": 63456.78,
      "count": 267
    }
  }
}
```

### 6.2 获取支付统计

```
GET /api/admin/revenue/payments
```

**响应**:
```json
{
  "total_payments": 867,
  "successful_payments": 800,
  "failed_payments": 50,
  "refunded_payments": 17,
  "success_rate": 92.3,
  "average_amount": 142.50,
  "payment_method_stats": [
    {
      "method": "alipay",
      "count": 500,
      "success_count": 480,
      "total_amount": 75000.00,
      "success_rate": 96.0
    }
  ]
}
```

### 6.3 导出财务报表

```
GET /api/admin/revenue/export
```

**Query参数**:
```typescript
{
  format: 'csv' | 'excel' | 'pdf';
  start_date: string;
  end_date: string;
  include_ai_costs?: boolean;  // 是否包含AI成本
}
```

---

## 7. AI网关管理 API（复用现有）

使用现有的 `/api/ai_gateway/*` 接口：
- `GET /api/ai_gateway/status` - 获取状态
- `POST /api/ai_gateway/register` - 注册服务商
- `POST /api/ai_gateway/switch` - 切换服务商
- `DELETE /api/ai_gateway/provider/:provider` - 删除服务商

---

## 错误响应格式

```json
{
  "error": {
    "message": "错误描述",
    "code": "ERROR_CODE",
    "details": {
      // 详细信息
    }
  }
}
```

**HTTP状态码**:
- `200` - 成功
- `400` - 请求错误
- `401` - 未授权
- `403` - 权限不足
- `404` - 资源不存在
- `500` - 服务器错误

---

**文档版本**：v1.0  
**创建日期**：2025-11-02

