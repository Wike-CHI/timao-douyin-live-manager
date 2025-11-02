/**
 * API 数据类型说明文档（修复 PAY-004, MISC-002）
 * 
 * 本文件定义了前后端数据交互中的类型约定和说明
 */

/**
 * ## 日期时间类型说明
 * 
 * 后端使用 Python `datetime` 类型，序列化为 ISO 8601 格式字符串。
 * 前端统一使用 `string` 类型接收，需要时转换为 `Date` 对象。
 * 
 * ### 格式说明
 * - UTC 时间: `"2025-11-02T15:30:00Z"`
 * - 带时区时间: `"2025-11-02T15:30:00+08:00"`
 * 
 * ### 转换示例
 * ```typescript
 * // 字符串转 Date 对象
 * const dateStr: string = "2025-11-02T15:30:00Z";
 * const dateObj: Date = new Date(dateStr);
 * 
 * // Date 对象转字符串
 * const dateObj = new Date();
 * const dateStr = dateObj.toISOString();
 * 
 * // 格式化显示
 * const formatted = dateObj.toLocaleString('zh-CN', {
 *   year: 'numeric',
 *   month: '2-digit',
 *   day: '2-digit',
 *   hour: '2-digit',
 *   minute: '2-digit',
 *   second: '2-digit',
 * });
 * ```
 * 
 * ### 相对时间计算
 * ```typescript
 * // 计算剩余天数
 * const endDate = new Date("2025-12-31T23:59:59Z");
 * const now = new Date();
 * const diffMs = endDate.getTime() - now.getTime();
 * const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
 * console.log(`剩余 ${diffDays} 天`);
 * ```
 */

/**
 * ISO 8601 日期时间字符串
 * 
 * 格式: YYYY-MM-DDTHH:mm:ss[.ffffff][Z|±HH:mm]
 * 示例: "2025-11-02T15:30:00Z" 或 "2025-11-02T15:30:00.123456+08:00"
 */
export type DateTimeString = string;

/**
 * ISO 8601 日期字符串
 * 
 * 格式: YYYY-MM-DD
 * 示例: "2025-11-02"
 */
export type DateString = string;

/**
 * ## 金额类型说明（修复 PAY-001）
 * 
 * 后端使用 `Decimal` 类型处理金额，避免浮点数精度问题。
 * 前端也应使用 `string` 类型传输金额，避免 JavaScript `number` 的精度丢失。
 * 
 * ### 为什么使用字符串？
 * 
 * JavaScript 的 `number` 类型是双精度浮点数（IEEE 754），可能导致：
 * - `0.1 + 0.2 !== 0.3` （结果是 0.30000000000000004）
 * - 大数值精度丢失
 * 
 * ### 使用示例
 * ```typescript
 * // ✅ 正确：使用字符串
 * const price: MoneyString = "99.99";
 * const total: MoneyString = "199.98";
 * 
 * // ❌ 错误：使用数字
 * const price: number = 99.99;
 * ```
 * 
 * ### 格式化显示
 * ```typescript
 * import { MoneyFormatter } from '@/utils/validators';
 * 
 * const price = "99.99";
 * const formatted = MoneyFormatter.format(price, '¥');
 * console.log(formatted);  // "¥99.99"
 * ```
 * 
 * ### 金额运算
 * ```typescript
 * import { MoneyFormatter } from '@/utils/validators';
 * 
 * const price1 = "99.99";
 * const price2 = "49.50";
 * const total = MoneyFormatter.add(price1, price2);
 * console.log(total);  // "149.49"
 * ```
 */

/**
 * 金额字符串（避免浮点数精度问题）
 * 
 * 格式: 数字字符串，最多2位小数
 * 示例: "99.99", "0.50", "1000.00"
 */
export type MoneyString = string;

/**
 * ## 枚举类型说明
 * 
 * 后端使用 Python `Enum`，前端使用 TypeScript 字符串字面量联合类型。
 */

/**
 * 用户角色
 * 对应后端: UserRoleEnum
 */
export type UserRole = 'user' | 'admin' | 'super_admin';

/**
 * 用户状态
 * 对应后端: UserStatusEnum
 */
export type UserStatus = 'active' | 'inactive' | 'suspended' | 'banned';

/**
 * 套餐类型
 * 对应后端: PlanType
 */
export type PlanType = 'free' | 'basic' | 'professional' | 'enterprise';

/**
 * 套餐时长
 * 对应后端: PlanDuration
 */
export type PlanDuration = 'monthly' | 'quarterly' | 'yearly' | 'lifetime';

/**
 * 支付方式
 * 对应后端: PaymentMethod
 */
export type PaymentMethod = 'alipay' | 'wechat' | 'bank_transfer' | 'stripe' | 'points';

/**
 * 支付状态
 * 对应后端: PaymentStatus
 */
export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'cancelled';

/**
 * 订阅状态
 * 对应后端: SubscriptionStatus
 */
export type SubscriptionStatus = 'active' | 'expired' | 'cancelled' | 'pending';

/**
 * ## 可选类型说明
 * 
 * 后端的 `Optional[T]` 对应前端的 `T | null | undefined`。
 * 
 * ### 约定
 * - 使用 `?:` 表示字段可选（可以不传）
 * - 使用 `| null` 表示字段可以为 null
 * - 使用 `| undefined` 表示字段可以为 undefined
 * 
 * ### 示例
 * ```typescript
 * interface User {
 *   id: number;              // 必填，不可为 null
 *   nickname?: string;       // 可选，可以不传
 *   avatar_url: string | null;  // 必传，但可以为 null
 * }
 * ```
 */

/**
 * ## 实用工具类型
 */

/**
 * 分页参数
 */
export interface PaginationParams {
  skip?: number;  // 默认 0
  limit?: number;  // 默认 10
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

/**
 * 基础响应
 */
export interface BaseResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
}

/**
 * 错误响应（FastAPI 标准格式）
 */
export interface ErrorResponse {
  detail: string;
}

/**
 * 扩展错误响应（带字段验证）
 */
export interface ExtendedErrorResponse {
  detail: string;
  code?: string;
  field?: string;
  errors?: Array<{
    field: string;
    message: string;
  }>;
}

