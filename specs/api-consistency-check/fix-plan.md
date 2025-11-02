# API 接口一致性修复方案

## 📋 修复概览

本文档提供针对已识别问题的具体修复方案，按优先级排序。

### 修复策略

1. **立即修复**：影响功能或数据准确性的高优先级问题
2. **近期修复**：影响用户体验或代码质量的中优先级问题  
3. **后续优化**：不影响功能的低优先级改进

---

## 🔴 立即修复方案

### PAY-001: Decimal vs number 类型不匹配

**问题描述**

后端使用 `Decimal` 类型处理金额，前端使用 `number` 类型，可能导致精度丢失。

**影响范围**

- 支付金额计算
- 订阅价格显示
- 优惠券折扣计算

**建议修复方式**

**方案 1：使用字符串传输（推荐）**

修改前端类型定义，将金额字段改为字符串：

```typescript
// 前端修改：electron/renderer/src/services/payment.ts
export interface Plan {
  id: number;
  name: string;
  // 修改前
  // price: number;
  // original_price?: number;
  
  // 修改后
  price: string;  // 使用字符串避免精度丢失
  original_price?: string;
  // ... 其他字段
}

export interface Payment {
  // 修改前
  // amount: number;
  
  // 修改后
  amount: string;
  // ... 其他字段
}
```

使用时转换：

```typescript
// 显示价格
const priceNumber = parseFloat(plan.price);
console.log(`¥${priceNumber.toFixed(2)}`);

// 或使用货币格式化库
import { formatCurrency } from './utils';
console.log(formatCurrency(plan.price, 'CNY'));
```

**方案 2：使用货币处理库**

```typescript
// 安装 decimal.js 或 big.js
npm install decimal.js

// 使用示例
import Decimal from 'decimal.js';

const price = new Decimal(plan.price);
const discount = new Decimal('0.9'); 
const finalPrice = price.times(discount);
```

**修复优先级**: 🔴 最高 - 建议在下个版本中修复

---

### PAY-005: 创建支付请求参数不完整

**问题描述**

前端创建支付时仅发送 `subscription_id` 和 `method`，缺少 `amount`、`currency`、`coupon_code`、`return_url` 等字段。

**修复代码**

```typescript
// 修改前：electron/renderer/src/services/payment.ts:263-276
export const createPayment = async (
  subscriptionId: string,
  method: 'alipay' | 'wechat' | 'bank_transfer',
  baseUrl: string = DEFAULT_BASE_URL
): Promise<Payment> => {
  const response = await authFetch(`${baseUrl}/api/payment/payments`, {
    method: 'POST',
    body: JSON.stringify({
      subscription_id: subscriptionId,
      method: method,
    }),
  });
  return handleResponse(response);
};

// 修改后
export interface CreatePaymentRequest {
  subscription_id?: number;  // 可选，如果是订阅支付
  amount: string;  // 必填，支付金额（使用字符串）
  payment_method: 'alipay' | 'wechat' | 'bank_transfer';
  currency?: string;  // 可选，默认 CNY
  coupon_code?: string;  // 可选，优惠券代码
  return_url?: string;  // 可选，支付成功返回 URL
}

export const createPayment = async (
  request: CreatePaymentRequest,
  baseUrl: string = DEFAULT_BASE_URL
): Promise<Payment> => {
  const response = await authFetch(`${baseUrl}/api/payment/payments`, {
    method: 'POST',
    body: JSON.stringify({
      subscription_id: request.subscription_id,
      amount: request.amount,
      payment_method: request.payment_method,
      currency: request.currency || 'CNY',
      coupon_code: request.coupon_code,
      return_url: request.return_url,
    }),
  });
  return handleResponse(response);
};
```

**调用示例**

```typescript
// 使用示例
const payment = await createPayment({
  subscription_id: 123,
  amount: '99.00',  // 字符串格式
  payment_method: 'alipay',
  currency: 'CNY',
  return_url: 'https://app.example.com/payment/success',
});
```

**修复优先级**: 🔴 最高

---

### AUTH-004: username 验证逻辑缺失

**问题描述**

后端有严格的 username 验证规则（3-50字符，仅支持字母数字下划线连字符），前端仅做简单替换。

**修复代码**

```typescript
// 新增：electron/renderer/src/utils/validators.ts
export class UserValidator {
  /**
   * 验证用户名
   * 规则：3-50字符，仅支持字母、数字、下划线和连字符
   */
  static validateUsername(username: string): { valid: boolean; message?: string } {
    if (!username || username.length < 3) {
      return { valid: false, message: '用户名长度至少3个字符' };
    }
    
    if (username.length > 50) {
      return { valid: false, message: '用户名长度不能超过50个字符' };
    }
    
    const pattern = /^[A-Za-z0-9_-]+$/;
    if (!pattern.test(username)) {
      return { valid: false, message: '用户名只能包含字母、数字、下划线和连字符' };
    }
    
    return { valid: true };
  }

  /**
   * 生成合法的用户名
   * 与后端逻辑保持一致
   */
  static generateUsername(nickname: string, email: string): string {
    let candidate = nickname?.trim() || email.split('@')[0];
    
    // 移除非法字符
    candidate = candidate.replace(/[^A-Za-z0-9_-]/g, '');
    
    // 确保长度符合要求
    if (candidate.length < 3) {
      candidate = `user_${Date.now().toString().slice(-6)}`;
    }
    
    if (candidate.length > 50) {
      candidate = candidate.slice(0, 50);
    }
    
    return candidate;
  }

  /**
   * 验证密码
   */
  static validatePassword(password: string): { valid: boolean; message?: string } {
    if (!password || password.length < 6) {
      return { valid: false, message: '密码长度至少6个字符' };
    }
    
    return { valid: true };
  }
}
```

**使用验证器**

```typescript
// 修改：electron/renderer/src/services/auth.ts
import { UserValidator } from '../utils/validators';

export const register = async (payload: RegisterPayload): Promise<RegisterResponse> => {
  const body: RegisterPayload = { ...payload };
  
  // 生成或验证用户名
  if (!body.username) {
    body.username = UserValidator.generateUsername(body.nickname, body.email);
  } else {
    // 验证用户提供的用户名
    const validation = UserValidator.validateUsername(body.username);
    if (!validation.valid) {
      throw new Error(validation.message);
    }
  }
  
  // 验证密码
  const passwordValidation = UserValidator.validatePassword(body.password);
  if (!passwordValidation.valid) {
    throw new Error(passwordValidation.message);
  }
  
  const resp = await fetch(joinUrl('/api/auth/register'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  
  if (!resp.ok) {
    const txt = await resp.text().catch(() => '注册失败');
    throw new Error(txt || '注册失败');
  }
  
  return resp.json();
};
```

**修复优先级**: 🔴 高

---

### MISC-004: API 路径重复

**问题描述**

存在两套并行的 API（`/api/payment/*` 和 `/api/subscription/*`），导致维护复杂度增加。

**建议方案**

**阶段 1：统一入口（立即）**

创建统一的 API 接口封装：

```typescript
// 新增：electron/renderer/src/services/unified-payment.ts
/**
 * 统一的支付和订阅 API
 * 封装两套 API 的差异，提供统一接口
 */

// 优先使用的 API 前缀（根据项目决策选择）
const PRIMARY_API_PREFIX = '/api/payment';  // 或 '/api/subscription'
const FALLBACK_API_PREFIX = '/api/subscription';  // 或 '/api/payment'

/**
 * 智能 API 调用：优先使用主 API，失败后降级到备用 API
 */
async function smartFetch<T>(
  primaryPath: string,
  fallbackPath?: string,
  options?: RequestInit
): Promise<T> {
  const baseUrl = DEFAULT_BASE_URL;
  
  try {
    // 尝试主 API
    const response = await authFetch(`${baseUrl}${primaryPath}`, options);
    return handleResponse<T>(response);
  } catch (error) {
    if (!fallbackPath) {
      throw error;
    }
    
    // 降级到备用 API
    console.warn(`主 API ${primaryPath} 失败，尝试备用 API ${fallbackPath}`);
    const response = await authFetch(`${baseUrl}${fallbackPath}`, options);
    return handleResponse<T>(response);
  }
}

/**
 * 获取套餐列表
 */
export const getPlans = async (): Promise<Plan[]> => {
  return smartFetch<Plan[]>(
    `${PRIMARY_API_PREFIX}/plans`,
    `${FALLBACK_API_PREFIX}/plans`
  );
};

// ... 其他统一接口
```

**阶段 2：后端 API 统一（后续）**

1. 选定主 API 路径（建议 `/api/payment`，更语义化）
2. 标记旧 API 为 deprecated
3. 迁移所有前端调用到新 API
4. 移除旧 API

**修复优先级**: 🔴 高（阶段1）/ 🟡 中（阶段2）

---

## 🟡 近期修复方案

### AUTH-001 & AUTH-002: LoginResponse 缺少字段

**问题描述**

登录响应缺少 `firstFreeUsed` 和 `aiUsage` 字段。

**修复代码**

```typescript
// 修改：electron/renderer/src/services/auth.ts

// 添加 AI 使用统计接口
export interface AIUsage {
  requests_used: number;
  requests_limit: number;
  tokens_used: number;
  tokens_limit: number;
  first_free_used: boolean;
}

// 修改 LoginResponse
export interface LoginResponse {
  success: boolean;
  token: string;
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: UserInfo;
  isPaid: boolean;
  
  // 新增字段
  firstFreeUsed?: boolean;  // 首次免费额度是否已使用
  aiUsage?: AIUsage;  // AI 使用统计
}
```

**使用示例**

```typescript
// 登录后检查 AI 额度
const loginResponse = await login({ email, password });

if (loginResponse.firstFreeUsed) {
  console.log('首次免费额度已使用');
}

if (loginResponse.aiUsage) {
  const { requests_used, requests_limit } = loginResponse.aiUsage;
  console.log(`AI 请求使用：${requests_used}/${requests_limit}`);
}
```

**修复优先级**: 🟡 中

---

### SUB-002: 订阅响应缺少 plan 对象

**问题描述**

后端返回完整的 `plan` 对象，前端类型定义不准确。

**修复代码**

```typescript
// 修改：electron/renderer/src/services/payment.ts

export interface Subscription {
  id: number;
  user_id: number;
  plan_id: number;
  status: 'active' | 'expired' | 'cancelled' | 'pending';
  start_date: string;
  end_date: string;
  auto_renew: boolean;
  trial_end_date?: string;
  cancelled_at?: string;
  cancel_reason?: string;
  is_active: boolean;
  is_trial: boolean;
  days_remaining: number;
  
  // 修改：添加完整的 plan 对象
  plan: Plan;  // 嵌套的完整套餐信息
  
  // 移除冗余字段（如果 plan 对象已包含）
  // plan_name?: string;
  // expires_at?: string;  // 使用 end_date
  
  created_at: string;
  updated_at: string;
}
```

**修复优先级**: 🟡 中

---

### DY-001: 抖音监控缺少 Cookie 支持

**问题描述**

后端支持可选的 Cookie 参数，前端未使用。

**修复代码**

```typescript
// 修改：electron/renderer/src/services/douyin.ts

export interface StartDouyinRequest {
  live_id?: string;
  live_url?: string;
  cookie?: string;  // 新增：可选的 Cookie 字符串
}

export const startDouyinRelay = async (
  liveId: string,
  cookie?: string,  // 新增参数
  baseUrl?: string
): Promise<DouyinRelayResponse> => {
  const headers = await buildHeaders();
  const body: StartDouyinRequest = { live_id: liveId };
  
  // 添加 Cookie 支持
  if (cookie) {
    body.cookie = cookie;
  }
  
  const response = await fetch(joinUrl(baseUrl, '/api/douyin/start'), {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });
  return handleResponse<DouyinRelayResponse>(response);
};
```

**UI 组件添加 Cookie 输入**

```typescript
// 示例：LiveConsolePage.tsx 添加 Cookie 输入框
const [douyinCookie, setDouyinCookie] = useState<string>('');

// 启动时传递 Cookie
await startDouyinRelay(liveId, douyinCookie, FASTAPI_BASE_URL);
```

**修复优先级**: 🟡 中

---

### AUDIO-003: 音频高级设置类型定义不完整

**问题描述**

前端使用通用的 `Record<string, unknown>` 类型更新高级设置。

**修复代码**

```typescript
// 新增：electron/renderer/src/services/liveAudio.ts

// 定义完整的高级设置接口
export interface LiveAudioAdvancedSettings {
  // 持久化设置
  persist_enabled?: boolean;
  persist_root?: string;
  
  // 自动增益控制
  agc?: boolean;
  agc_target_level?: number;
  
  // 说话人分离
  diarization?: boolean;
  max_speakers?: number;
  
  // 音乐检测
  music_detection_enabled?: boolean;
  music_filter?: boolean;
  
  // VAD 参数
  vad_min_silence_sec?: number;
  vad_min_speech_sec?: number;
  vad_hangover_sec?: number;
  vad_rms?: number;
  
  // 句子组装参数
  max_wait?: number;
  max_chars?: number;
  silence_flush?: number;
  min_sentence_chars?: number;
}

// 修改现有函数
export const updateLiveAudioAdvanced = async (
  settings: LiveAudioAdvancedSettings,  // 使用具体类型
  baseUrl: string = DEFAULT_BASE_URL
) => {
  const response = await fetch(`${baseUrl}/api/live_audio/advanced`, {
    method: 'POST',
    headers: await buildHeaders(),
    body: JSON.stringify(settings),
  });
  return handleResponse(response);
};
```

**修复优先级**: 🟡 中

---

## 🟢 后续优化方案

### MISC-002: 日期时间类型统一文档化

**建议方案**

创建类型说明文档：

```typescript
// 新增：electron/renderer/src/types/api-types.ts

/**
 * API 数据类型说明
 * 
 * ## 日期时间类型
 * 
 * 后端使用 Python `datetime` 类型，序列化为 ISO 8601 格式字符串。
 * 前端统一使用 `string` 类型接收，需要时转换为 `Date` 对象。
 * 
 * 格式示例：
 * - "2025-11-02T15:30:00Z" (UTC)
 * - "2025-11-02T15:30:00+08:00" (带时区)
 * 
 * 转换示例：
 * ```typescript
 * const dateStr: string = "2025-11-02T15:30:00Z";
 * const dateObj: Date = new Date(dateStr);
 * ```
 */

/**
 * ISO 8601 日期时间字符串
 */
export type DateTimeString = string;

/**
 * ISO 8601 日期字符串
 */
export type DateString = string;

// 使用示例
export interface UserInfo {
  id: number;
  username: string;
  created_at: DateTimeString;  // 明确标注为日期时间字符串
}
```

**修复优先级**: 🟢 低

---

## 📊 修复计划时间表

| 问题 | 优先级 | 预计工时 | 建议版本 |
|------|--------|----------|----------|
| PAY-001 | 🔴 | 4h | v1.1 |
| PAY-005 | 🔴 | 2h | v1.1 |
| AUTH-004 | 🔴 | 3h | v1.1 |
| MISC-004 | 🔴 | 6h | v1.1-v1.2 |
| DY-003 | 🔴 | 1h | v1.1 |
| AUDIO-003 | 🔴 | 2h | v1.1 |
| PAY-004 | 🔴 | 1h | v1.1 |
| AUTH-001/002 | 🟡 | 1h | v1.2 |
| SUB-001/002/003 | 🟡 | 3h | v1.2 |
| PAY-003 | 🟡 | 1h | v1.2 |
| DY-001 | 🟡 | 2h | v1.2 |
| AUDIO-001/002/004 | 🟡 | 3h | v1.2 |
| MISC-001/002/003 | 🟡 | 4h | v1.2-v1.3 |
| 低优先级项 | 🟢 | 2h | v1.3+ |
| **总计** | - | **35h** | 3 个版本 |

---

## 🎯 实施建议

### 分批实施策略

**版本 1.1（紧急修复 - 2周内）**
- 修复所有🔴高优先级问题
- 重点：金额精度、参数完整性、验证逻辑
- 交付物：修复补丁、更新的类型定义

**版本 1.2（功能完善 - 1个月内）**
- 修复所有🟡中优先级问题
- 重点：接口完整性、类型准确性
- 交付物：完善的 API、更新的文档

**版本 1.3（代码质量 - 持续改进）**
- 优化🟢低优先级项
- 重点：文档、工具链、自动化
- 交付物：API 契约、自动化检查工具

### 质量保证

1. **单元测试**：为修改的代码添加单元测试
2. **集成测试**：验证前后端接口对接
3. **回归测试**：确保修复未引入新问题
4. **Code Review**：所有修复必须经过代码审查

### 风险控制

1. **小步快跑**：每次只修复少量问题，降低风险
2. **向后兼容**：保持 API 向后兼容，避免破坏现有功能
3. **灰度发布**：重要修复先在测试环境验证
4. **回滚方案**：准备快速回滚机制

---

## 📚 参考资料

### 相关文档

- [requirements.md](./requirements.md) - 需求文档
- [design.md](./design.md) - 技术方案设计
- [issues-table.md](./issues-table.md) - 问题清单表格
- [api-contract.yaml](./api-contract.yaml) - OpenAPI 契约
- [types-contract.d.ts](./types-contract.d.ts) - TypeScript 类型契约

### 工具和库推荐

**金额处理**
- [decimal.js](https://github.com/MikeMcl/decimal.js/) - 高精度十进制运算
- [big.js](https://github.com/MikeMcl/big.js/) - 轻量级货币计算

**数据验证**
- [zod](https://github.com/colinhacks/zod) - TypeScript-first 验证库
- [yup](https://github.com/jquense/yup) - 对象模式验证

**API 契约测试**
- [Pact](https://pact.io/) - 契约测试框架
- [OpenAPI Generator](https://openapi-generator.tech/) - 从 OpenAPI 生成客户端代码

---

*文档生成时间: 2025-11-02*  
*版本: 1.0*

