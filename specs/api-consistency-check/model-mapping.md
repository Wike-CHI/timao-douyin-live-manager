# 数据模型映射表

## 📋 概述

本文档提供前后端数据模型的详细映射关系，确保类型一致性。

---

## 🔄 基础类型映射

### Python ↔ TypeScript 类型对照表

| Python 类型 | TypeScript 类型 | 说明 | 示例 |
|-------------|----------------|------|------|
| `str` | `string` | 字符串 | `"hello"` |
| `int` | `number` | 整数 | `42` |
| `float` | `number` | 浮点数（⚠️ 精度问题） | `3.14` |
| `bool` | `boolean` | 布尔值 | `true` / `false` |
| `None` | `null` | 空值 | `null` |
| `Any` | `any` | 任意类型 | - |
| `datetime` | `string` | ISO 8601 日期时间字符串 | `"2025-11-02T15:30:00Z"` |
| `date` | `string` | ISO 8601 日期字符串 | `"2025-11-02"` |
| `Decimal` | `string` | ⚠️ 金额使用字符串避免精度丢失 | `"99.00"` |
| `List[T]` | `T[]` 或 `Array<T>` | 数组 | `[1, 2, 3]` |
| `Dict[K, V]` | `Record<K, V>` | 字典/对象 | `{key: value}` |
| `Optional[T]` | `T \| null \| undefined` | 可选类型 | - |
| `Union[T1, T2]` | `T1 \| T2` | 联合类型 | - |
| `Literal["a", "b"]` | `"a" \| "b"` | 字面量类型 | - |

### ⚠️ 特别注意

1. **日期时间**: 后端 `datetime` 序列化为 ISO 8601 字符串，前端接收为 `string`
2. **金额**: 后端 `Decimal` 避免精度丢失，建议前端也使用 `string` 传输
3. **可选性**: Python `Optional[T]` = TypeScript `T | null | undefined`
4. **枚举**: Python `Enum` 转为 TypeScript 字符串字面量联合类型

---

## 📦 模块级映射

### 认证模块 (Auth)

#### UserInfo / UserResponse

| 后端字段 (Python) | 前端字段 (TypeScript) | 类型映射 | 必填 | 说明 |
|-------------------|----------------------|----------|------|------|
| `id: int` | `id: number` | ✅ | 是 | 用户 ID |
| `username: str` | `username: string` | ✅ | 是 | 用户名 |
| `email: str` | `email: string` | ✅ | 是 | 邮箱 |
| `nickname: Optional[str]` | `nickname?: string \| null` | ✅ | 否 | 昵称 |
| `avatar_url: Optional[str]` | `avatar_url?: string \| null` | ✅ | 否 | 头像 URL |
| `role: str` | `role: string` | ✅ | 是 | 角色（应为枚举） |
| `status: str` | `status: string` | ✅ | 是 | 状态（应为枚举） |
| `email_verified: bool` | `email_verified: boolean` | ✅ | 是 | 邮箱已验证 |
| `phone_verified: bool` | `phone_verified: boolean` | ✅ | 是 | 手机已验证 |
| `created_at: datetime` | `created_at: string` | ✅ | 是 | 创建时间（ISO 8601） |

**后端定义位置**: `server/app/api/auth.py:76-90`  
**前端定义位置**: `electron/renderer/src/services/auth.ts:24-35`

#### LoginResponse

| 后端字段 | 前端字段 | 类型映射 | 必填 | 说明 |
|----------|----------|----------|------|------|
| `success: bool` | `success: boolean` | ✅ | 是 | 成功标志 |
| `token: str` | `token: string` | ✅ | 是 | 访问令牌 |
| `access_token: str` | `access_token: string` | ✅ | 是 | 访问令牌 |
| `refresh_token: str` | `refresh_token: string` | ✅ | 是 | 刷新令牌 |
| `token_type: str` | `token_type?: string` | ⚠️ | 是 | 前端应为必填 |
| `expires_in: int` | `expires_in: number` | ✅ | 是 | 过期时间（秒） |
| `user: UserResponse` | `user: UserInfo` | ✅ | 是 | 用户信息 |
| `isPaid: bool` | `isPaid: boolean` | ✅ | 是 | 付费状态 |
| `firstFreeUsed: bool` | ❌ **缺失** | ❌ | 否 | ⚠️ 前端缺少此字段 |
| `aiUsage: Optional[Dict]` | ❌ **缺失** | ❌ | 否 | ⚠️ 前端缺少此字段 |

**后端定义位置**: `server/app/api/auth.py:93-104`  
**前端定义位置**: `electron/renderer/src/services/auth.ts:38-46`

**问题**: AUTH-001, AUTH-002

---

### 支付模块 (Payment)

#### Plan / PlanResponse

| 后端字段 | 前端字段 | 类型映射 | 必填 | 说明 |
|----------|----------|----------|------|------|
| `id: int` | `id: number` | ✅ | 是 | 套餐 ID |
| `name: str` | `name: string` | ✅ | 是 | 套餐名称 |
| `description: Optional[str]` | `description?: string` | ✅ | 否 | 描述 |
| `plan_type: str` | `plan_type: string` | ✅ | 是 | 类型（枚举） |
| `duration: str` | `duration: string` | ✅ | 是 | 时长 |
| `price: Decimal` | `price: number` | ⚠️ | 是 | ⚠️ 应改为 `string` |
| `original_price: Decimal` | `original_price?: number` | ⚠️ | 是 | ⚠️ 应改为 `string` |
| `currency: str` | `currency: string` | ✅ | 是 | 货币 |
| `features: Dict` | `features: Record<string, any>` | ✅ | 是 | 功能特性 |
| `limits: Dict` | `limits: Record<string, any>` | ✅ | 是 | 使用限制 |
| `is_active: bool` | `is_active: boolean` | ✅ | 是 | 是否激活 |
| `sort_order: int` | `sort_order: number` | ✅ | 是 | 排序 |
| `created_at: datetime` | `created_at: string` | ✅ | 是 | 创建时间 |
| `updated_at: datetime` | `updated_at: string` | ✅ | 是 | 更新时间 |
| ❌ | `is_popular?: boolean` | ❌ | 否 | ⚠️ 后端无此字段 |

**后端定义位置**: `server/app/api/payment.py:56-74`  
**前端定义位置**: `electron/renderer/src/services/payment.ts:46-62`

**问题**: PAY-001, PAY-002

#### Subscription / SubscriptionResponse

| 后端字段 | 前端字段 | 类型映射 | 必填 | 说明 |
|----------|----------|----------|------|------|
| `id: int` | `id: number` | ✅ | 是 | 订阅 ID |
| `user_id: int` | `user_id: number` | ✅ | 是 | 用户 ID |
| `plan_id: int` | `plan_id: number` | ✅ | 是 | 套餐 ID |
| `status: str` | `status: string` | ✅ | 是 | 状态 |
| `start_date: datetime` | `start_date: string` | ✅ | 是 | 开始日期 |
| `end_date: datetime` | `end_date: string` | ✅ | 是 | 结束日期 |
| `auto_renew: bool` | `auto_renew: boolean` | ✅ | 是 | 自动续费 |
| `trial_end_date: Optional[datetime]` | `trial_end_date?: string` | ✅ | 否 | 试用结束 |
| `cancelled_at: Optional[datetime]` | `cancelled_at?: string` | ✅ | 否 | 取消时间 |
| `cancel_reason: Optional[str]` | `cancel_reason?: string` | ✅ | 否 | 取消原因 |
| `is_active: bool` | `is_active: boolean` | ✅ | 是 | 是否激活 |
| `is_trial: bool` | `is_trial: boolean` | ✅ | 是 | 是否试用 |
| `days_remaining: int` | `days_remaining: number` | ✅ | 是 | 剩余天数 |
| `plan: PlanResponse` | `plan?: Plan` | ⚠️ | 是 | ⚠️ 前端应为必填 |
| `created_at: datetime` | `created_at: string` | ✅ | 是 | 创建时间 |
| `updated_at: datetime` | `updated_at: string` | ✅ | 是 | 更新时间 |
| ❌ | `plan_name?: string` | ❌ | 否 | ⚠️ 冗余字段 |
| ❌ | `expires_at?: string` | ❌ | 否 | ⚠️ 使用 end_date |

**后端定义位置**: `server/app/api/payment.py:84-104`  
**前端定义位置**: `electron/renderer/src/services/payment.ts:64-83`

**问题**: SUB-002, PAY-004

#### PaymentCreate

| 后端字段 | 前端字段 | 类型映射 | 必填 | 说明 |
|----------|----------|----------|------|------|
| `subscription_id: Optional[int]` | `subscription_id: number` | ⚠️ | 否 | ⚠️ 应为可选 |
| `amount: Decimal` | ❌ **缺失** | ❌ | 是 | ⚠️ 前端缺失！ |
| `payment_method: PaymentMethod` | `method: string` | ⚠️ | 是 | 字段名不一致 |
| `currency: str` | ❌ **缺失** | ❌ | 否 | ⚠️ 前端缺失 |
| `coupon_code: Optional[str]` | ❌ **缺失** | ❌ | 否 | ⚠️ 前端缺失 |
| `return_url: Optional[str]` | ❌ **缺失** | ❌ | 否 | ⚠️ 前端缺失 |

**后端定义位置**: `server/app/api/payment.py:107-114`  
**前端定义位置**: `electron/renderer/src/services/payment.ts:263-276`

**问题**: PAY-005（高优先级）

---

### 抖音模块 (Douyin)

#### StartMonitoringRequest / StartDouyinRequest

| 后端字段 | 前端字段 | 类型映射 | 必填 | 说明 |
|----------|----------|----------|------|------|
| `live_id: Optional[str]` | ✅ 使用（参数） | ✅ | 否 | 直播间 ID |
| `live_url: Optional[str]` | ❌ 未使用 | ❌ | 否 | ⚠️ 前端未使用 |
| `cookie: Optional[str]` | ❌ **缺失** | ❌ | 否 | ⚠️ 前端缺失 |

**后端定义位置**: `server/app/api/douyin.py:24-28`  
**前端定义位置**: `electron/renderer/src/services/douyin.ts:55-66`

**问题**: DY-001

#### StatusResponse / DouyinStatus

| 后端字段 | 前端字段 | 类型映射 | 必填 | 说明 |
|----------|----------|----------|------|------|
| `is_monitoring: bool` | `is_running: boolean` | ⚠️ | 是 | 字段名不一致 |
| `current_room_id: Optional[str]` | `room_id?: string \| null` | ✅ | 否 | 房间 ID |
| `current_live_id: Optional[str]` | `live_id?: string \| null` | ✅ | 否 | 直播 ID |
| `fetcher_status: Dict` | ❌ **缺失** | ❌ | 是 | ⚠️ 前端缺失 |

**后端定义位置**: `server/app/api/douyin.py:50-54`  
**前端定义位置**: `electron/renderer/src/services/douyin.ts:34-41`

**问题**: DY-003

---

### 音频转写模块 (LiveAudio)

#### StartLiveAudioRequest / StartLiveAudioPayload

| 后端字段 | 前端字段 | 类型映射 | 必填 | 说明 |
|----------|----------|----------|------|------|
| `live_url: str` | `live_url: string` | ✅ | 是 | 直播 URL |
| `session_id: Optional[str]` | `session_id?: string` | ✅ | 否 | 会话 ID |
| `chunk_duration: Optional[float]` | `chunk_duration?: number` | ✅ | 否 | 音频块时长 |
| `profile: Optional[str]` | `profile?: string` | ✅ | 否 | 配置文件 |
| 多个 VAD 参数 | 多个 VAD 参数 | ✅ | 否 | 语音活动检测参数 |

**后端定义位置**: `server/app/api/live_audio.py:25-50`  
**前端定义位置**: `electron/renderer/src/services/liveAudio.ts:23-38`

**问题**: AUDIO-001

#### LiveAudioStatus

| 后端字段 | 前端字段 | 类型映射 | 必填 | 说明 |
|----------|----------|----------|------|------|
| `is_running: bool` | `is_running: boolean` | ✅ | 是 | 运行状态 |
| `live_id: Optional[str]` | `live_id: string \| null` | ✅ | 否 | 直播 ID |
| `live_url: Optional[str]` | `live_url: string \| null` | ✅ | 否 | 直播 URL |
| `session_id: Optional[str]` | `session_id: string \| null` | ✅ | 否 | 会话 ID |
| `mode: str` | `mode?: string` | ✅ | 是 | 模式 |
| `model: str` (通过方法) | ❌ **缺失** | ❌ | 是 | ⚠️ 前端缺失 |
| `advanced: dict` | `advanced?: object` | ✅ | 否 | 高级设置 |
| `stats: dict` | `stats: object` | ✅ | 是 | 统计信息 |

**后端定义位置**: `server/app/api/live_audio.py:141-176`  
**前端定义位置**: `electron/renderer/src/services/liveAudio.ts:40-66`

**问题**: AUDIO-002

---

## 🔧 修复建议

### 立即修复项

1. **金额类型统一**: 所有金额字段改为 `string` 类型
2. **完善缺失字段**: 
   - LoginResponse 添加 `firstFreeUsed` 和 `aiUsage`
   - PaymentCreate 添加所有必需字段
   - DouyinStatus 添加 `fetcher_status`
   - LiveAudioStatus 添加 `model`
3. **字段名统一**: 
   - Douyin: `is_monitoring` vs `is_running`
   - Payment: `payment_method` vs `method`

### 近期优化项

1. **枚举类型化**: 将所有枚举字符串改为 TypeScript 联合类型
2. **移除冗余字段**: 清理前端定义的后端不返回的字段
3. **补充可选参数**: Cookie、trial_days 等可选参数

---

## 📚 参考文档

- [OpenAPI 契约](./api-contract.yaml)
- [TypeScript 类型定义](./types-contract.d.ts)
- [问题清单](./issues-table.md)
- [修复方案](./fix-plan.md)

---

*文档生成时间: 2025-11-02*  
*版本: 1.0*

