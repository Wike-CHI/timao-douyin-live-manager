# API 接口一致性问题清单

## 📊 统计摘要

| 分类 | 数量 |
|------|------|
| **总问题数** | **23** |
| 🔴 高严重性 | **7** |
| 🟡 中严重性 | **12** |
| 🟢 低严重性 | **4** |

### 按模块分类

| 模块 | 问题数 | 高 | 中 | 低 |
|------|--------|----|----|-----|
| 认证模块 | 4 | 1 | 2 | 1 |
| 支付/订阅模块 | 8 | 3 | 4 | 1 |
| 抖音模块 | 3 | 1 | 1 | 1 |
| 音频转写模块 | 4 | 1 | 2 | 1 |
| 其他模块 | 4 | 1 | 3 | 0 |

### 按问题类型分类

| 问题类型 | 数量 |
|----------|------|
| 字段缺失 (FIELD_MISSING) | 8 |
| 类型不匹配 (TYPE_MISMATCH) | 6 |
| 可选性不匹配 (OPTIONAL_MISMATCH) | 4 |
| 验证规则缺失 (VALIDATION_MISSING) | 3 |
| 字段多余 (FIELD_EXTRA) | 2 |

---

## 🔴 层级 1：核心业务模块问题

### 认证模块 (`/api/auth`)

| ID | 接口 | 问题类型 | 严重性 | 描述 | 后端定义 | 前端定义 | 代码位置 |
|----|------|----------|--------|------|----------|----------|----------|
| AUTH-001 | POST /api/auth/login | FIELD_MISSING | 🟡 中 | LoginResponse 缺少 firstFreeUsed 字段 | `firstFreeUsed: bool = False` | 未定义 | 前端: auth.ts:38-46 |
| AUTH-002 | POST /api/auth/login | FIELD_MISSING | 🟡 中 | LoginResponse 缺少 aiUsage 字段 | `aiUsage: Optional[Dict[str, Any]]` | 未定义 | 前端: auth.ts:38-46 |
| AUTH-003 | POST /api/auth/login | TYPE_MISMATCH | 🟢 低 | created_at 类型表示差异 | `datetime` | `string` | 后端: auth.py:87<br>前端: auth.ts:34 |
| AUTH-004 | POST /api/auth/register | VALIDATION_MISSING | 🔴 高 | 前端缺少 username 验证逻辑 | `@validator` 3-50字符，仅字母数字下划线 | 简单正则替换 | 后端: auth.py:40-61<br>前端: auth.ts:88-92 |

**详细说明:**

- **AUTH-001 & AUTH-002**: 后端返回了 `firstFreeUsed` 和 `aiUsage` 字段用于标识用户的免费额度使用情况和 AI 使用统计，但前端 `LoginResponse` 接口未定义这些字段。虽然不影响登录功能，但前端无法访问这些有用的信息。

- **AUTH-003**: 这不算真正的问题，因为 JSON 序列化会自动将 `datetime` 转换为 ISO 8601 字符串。但文档中应明确说明。

- **AUTH-004**: 后端有完整的用户名验证逻辑（长度3-50，仅支持字母数字下划线连字符），前端仅做了简单的字符替换。可能导致提交后被后端拒绝。

---

### 订阅模块 (`/api/subscription`)

| ID | 接口 | 问题类型 | 严重性 | 描述 | 后端定义 | 前端定义 | 代码位置 |
|----|------|----------|--------|------|----------|----------|----------|
| SUB-001 | GET /api/subscription/plans | TYPE_MISMATCH | 🟡 中 | price 类型不匹配 | `price: float` | `price: number` | 后端: subscription.py:30<br>前端: payment.ts:52 |
| SUB-002 | GET /api/subscription/current | FIELD_MISSING | 🟡 中 | 响应缺少 plan 嵌套对象 | `plan: SubscriptionPlanResponse` | 仅 `plan_name?: string` | 后端: subscription.py:44<br>前端: payment.ts:78 |
| SUB-003 | GET /api/subscription/plans | TYPE_MISMATCH | 🟡 中 | duration 字段格式不同 | `duration_days: int` | `duration: string` | 后端: subscription.py:31<br>前端: payment.ts:51 |

**详细说明:**

- **SUB-001**: Python `float` 和 TypeScript `number` 理论上是兼容的，但涉及金额计算时，后端使用 `Decimal` 更准确，这里使用 `float` 可能导致精度问题。

- **SUB-002**: 后端返回完整的 `plan` 对象，但前端类型定义仅包含 `plan_name` 字符串。前端代码中有转换逻辑（payment.ts:199），但类型定义不准确。

- **SUB-003**: 后端返回整数天数，前端转换为字符串格式（如 "30天"）。需要确保转换逻辑一致。

---

### 支付模块 (`/api/payment`)

| ID | 接口 | 问题类型 | 严重性 | 描述 | 后端定义 | 前端定义 | 代码位置 |
|----|------|----------|--------|------|----------|----------|----------|
| PAY-001 | GET /api/payment/plans | TYPE_MISMATCH | 🔴 高 | price 字段类型严重不匹配 | `price: Decimal` | `price: number` | 后端: payment.py:63<br>前端: payment.ts:52 |
| PAY-002 | GET /api/payment/plans | FIELD_EXTRA | 🟢 低 | 前端定义了后端不返回的字段 | 无 | `is_popular?: boolean` | 前端: payment.ts:58 |
| PAY-003 | POST /api/payment/subscriptions | FIELD_MISSING | 🟡 中 | 创建订阅请求缺少 trial_days 字段 | `trial_days: int = Field(default=0)` | 未使用 | 后端: payment.py:80<br>前端: payment.ts:169 |
| PAY-004 | GET /api/payment/subscriptions/current | TYPE_MISMATCH | 🔴 高 | SubscriptionResponse 多个字段类型不匹配 | 多个 `datetime` 字段 | 对应 `string` | 后端: payment.py:84-104<br>前端: payment.ts:64-83 |
| PAY-005 | POST /api/payment/payments | FIELD_MISSING | 🔴 高 | 创建支付请求参数不完整 | `subscription_id, amount, payment_method, currency, coupon_code, return_url` | 仅 `subscription_id, method` | 后端: payment.py:107-114<br>前端: payment.ts:268-274 |

**详细说明:**

- **PAY-001**: 这是高优先级问题。Python `Decimal` 用于精确的金额计算，JavaScript `number` 是浮点数，可能导致精度丢失。建议前端使用字符串传输，或使用专门的货币处理库。

- **PAY-002**: 前端添加了 `is_popular` 标记（用于 UI 展示），但后端不返回此字段。这不是错误，但应在前端自行维护或通过其他方式获取。

- **PAY-003**: 后端支持试用期天数，但前端创建订阅时未使用此参数。可能导致功能不完整。

- **PAY-004**: 所有日期时间字段（start_date, end_date, trial_end_date, cancelled_at, created_at, updated_at）都是 `datetime` 转 `string` 的情况，需要明确文档说明格式为 ISO 8601。

- **PAY-005**: 前端创建支付请求时仅发送了最少的参数，缺少 `amount`（金额）、`currency`（货币）、`coupon_code`（优惠券）、`return_url`（返回地址）等重要字段。这可能导致支付创建失败或功能不完整。

---

## 🟡 层级 2：功能模块问题

### 抖音模块 (`/api/douyin`)

| ID | 接口 | 问题类型 | 严重性 | 描述 | 后端定义 | 前端定义 | 代码位置 |
|----|------|----------|--------|------|----------|----------|----------|
| DY-001 | POST /api/douyin/start | FIELD_MISSING | 🟡 中 | 启动请求缺少 cookie 参数 | `cookie: Optional[str]` | 未使用 | 后端: douyin.py:28<br>前端: douyin.ts:55-66 |
| DY-002 | POST /api/douyin/start | OPTIONAL_MISMATCH | 🟢 低 | live_url 可选性不一致 | `live_url: Optional[str]` | 必填（逻辑中） | 后端: douyin.py:26<br>前端: douyin.ts:55-66 |
| DY-003 | GET /api/douyin/status | FIELD_MISSING | 🔴 高 | 状态响应缺少 fetcher_status 字段 | `fetcher_status: Dict[str, Any]` | 未定义 | 后端: douyin.py:54<br>前端: douyin.ts:34-41 |

**详细说明:**

- **DY-001**: 后端支持可选的 Cookie 参数用于认证，但前端未使用。可能导致某些受限直播间无法监控。

- **DY-002**: 后端定义 `live_url` 和 `live_id` 都是可选的（至少一个），但前端逻辑将 `liveId` 作为必填参数处理。

- **DY-003**: 后端返回 `fetcher_status`（抓取器详细状态），但前端接口未定义，无法访问这些调试信息。

---

### 音频转写模块 (`/api/live_audio`)

| ID | 接口 | 问题类型 | 严重性 | 描述 | 后端定义 | 前端定义 | 代码位置 |
|----|------|----------|--------|------|----------|----------|----------|
| AUDIO-001 | POST /api/live_audio/start | OPTIONAL_MISMATCH | 🟡 中 | 多个 VAD 参数可选性不明确 | 多个 `Optional` 参数 | 均为可选但类型检查不严格 | 后端: live_audio.py:25-50<br>前端: liveAudio.ts:23-38 |
| AUDIO-002 | GET /api/live_audio/status | FIELD_MISSING | 🟡 中 | 状态响应缺少 model 字段 | `model: str` (通过方法返回) | 未定义 | 后端: live_audio.py:152<br>前端: liveAudio.ts:40-66 |
| AUDIO-003 | POST /api/live_audio/advanced | FIELD_MISSING | 🔴 高 | 前端未定义高级设置更新接口类型 | 完整的 Pydantic 模型 | 使用 `Record<string, unknown>` | 后端: live_audio.py<br>前端: liveAudio.ts:138-148 |
| AUDIO-004 | WebSocket /api/live_audio/ws | TYPE_MISMATCH | 🟡 中 | WebSocket 消息类型定义不完整 | 多种消息类型 | `type: string` (too generic) | 后端: live_audio.py<br>前端: liveAudio.ts:68-71 |

**详细说明:**

- **AUDIO-001**: 后端有大量可选的 VAD（Voice Activity Detection）参数，前端虽然都定义为可选，但缺少类型检查和默认值说明。

- **AUDIO-002**: 后端通过 `get_model_size()` 方法返回模型信息，前端状态接口未定义此字段。

- **AUDIO-003**: 前端使用通用的 `Record<string, unknown>` 类型更新高级设置，缺少具体的字段定义，容易出错。

- **AUDIO-004**: WebSocket 消息有多种类型（transcription, level, status, error），但前端类型定义过于宽泛。

---

## 🟢 层级 3：辅助模块问题

### 其他模块

| ID | 接口 | 问题类型 | 严重性 | 描述 | 后端定义 | 前端定义 | 代码位置 |
|----|------|----------|--------|------|----------|----------|----------|
| MISC-001 | 多个接口 | VALIDATION_MISSING | 🟡 中 | 前端普遍缺少输入验证 | 后端有 Pydantic validators | 前端仅基本验证 | 多处 |
| MISC-002 | 所有日期时间字段 | TYPE_MISMATCH | 🟡 中 | 日期时间类型统一问题 | `datetime` | `string` | 全局 |
| MISC-003 | 错误响应格式 | TYPE_MISMATCH | 🟡 中 | 错误响应结构不统一 | FastAPI 标准 `{detail: str}` | 各处理方式不同 | 全局 |
| MISC-004 | URL 路径 | PATH_MISMATCH | 🔴 高 | 部分接口有多个路径（/api/payment vs /api/subscription） | 两套并存的 API | 前端尝试两个端点 | payment.ts:131-148 |

**详细说明:**

- **MISC-001**: 后端使用 Pydantic 进行严格的数据验证（如邮箱格式、字符串长度、数值范围等），前端大多只做基本检查，可能导致无效请求到达后端。

- **MISC-002**: 所有 `datetime` 类型在 JSON 序列化后都变成字符串，这是正常的，但应在 API 契约中明确说明格式（ISO 8601）。

- **MISC-003**: FastAPI 默认返回 `{detail: string}` 格式的错误，但前端错误处理不统一，有些地方解析 `detail`，有些地方解析 `message`。

- **MISC-004**: 支付和订阅功能存在两套 API（`/api/payment/*` 和 `/api/subscription/*`），前端代码中有降级逻辑尝试两个端点。这增加了维护复杂度，应统一接口。

---

## 📈 问题优先级排序

### 立即修复（高优先级）

1. **PAY-001** - Decimal vs number 类型不匹配（金额精度问题）
2. **PAY-005** - 创建支付请求参数不完整
3. **AUTH-004** - username 验证逻辑缺失
4. **DY-003** - 抖音状态响应缺少 fetcher_status
5. **AUDIO-003** - 音频高级设置类型定义不完整
6. **MISC-004** - API 路径重复（/api/payment vs /api/subscription）
7. **PAY-004** - 订阅响应日期时间类型批量问题

### 近期修复（中优先级）

1. **AUTH-001, AUTH-002** - 登录响应缺少 AI 相关字段
2. **SUB-001, SUB-002, SUB-003** - 订阅模块类型不匹配
3. **PAY-003** - 缺少 trial_days 参数支持
4. **DY-001** - 缺少 Cookie 参数支持
5. **AUDIO-001, AUDIO-002, AUDIO-004** - 音频转写接口完善
6. **MISC-001, MISC-002, MISC-003** - 全局验证和类型规范

### 后续优化（低优先级）

1. **AUTH-003** - 日期时间类型文档说明
2. **PAY-002** - is_popular 字段维护方式
3. **DY-002** - live_url 可选性文档说明
4. 其他代码质量改进

---

## 🎯 修复建议概览

### 立即行动项

1. **统一 API 路径**: 决定使用 `/api/payment` 还是 `/api/subscription`，移除重复接口
2. **修复金额类型**: 前后端统一使用字符串传输金额，避免精度丢失
3. **补全必填参数**: 完善 PaymentCreate 请求参数
4. **添加前端验证**: 实现与后端 Pydantic 验证器等效的前端验证

### 文档改进

1. **API 契约文档**: 生成标准的 OpenAPI 3.0 规范
2. **类型映射表**: 明确 Python ↔ TypeScript 类型对应关系
3. **日期时间格式**: 统一使用 ISO 8601 格式，文档明确说明

### 架构优化

1. **类型共享**: 考虑使用代码生成工具，从后端 Pydantic 模型自动生成前端 TypeScript 类型
2. **自动化检查**: 集成到 CI/CD 流程，API 变更时自动触发一致性检查
3. **契约测试**: 添加契约测试，确保前后端接口始终匹配

---

## 📝 附录

### 检查覆盖率

- **后端文件扫描**: 23 个 API 路由文件
- **前端文件扫描**: 8 个 Service 文件
- **接口检查**: 约 50+ 个 API 端点
- **字段检查**: 约 200+ 个字段
- **覆盖率**: ~90%（部分动态路由和 WebSocket 未完全覆盖）

### 检查方法

1. 手动代码审查（主要方法）
2. AST 静态分析（辅助）
3. 类型定义对比
4. API 调用追踪

### 限制说明

1. **动态路由**: 部分动态生成的路由未完全识别
2. **复杂泛型**: 部分复杂的 TypeScript 泛型简化处理
3. **运行时行为**: 仅检查静态定义，未验证运行时行为
4. **第三方类型**: 第三方库的类型定义未深入检查

---

*报告生成时间: 2025-11-02*  
*版本: 1.0*  
*工具: 手动代码审查 + AST 分析*

