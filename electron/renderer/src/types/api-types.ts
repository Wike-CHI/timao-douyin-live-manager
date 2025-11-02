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
 * 
 * 修复需求: MISC-003 (错误响应统一)
 */
export interface ErrorResponse {
  detail: string | ErrorDetail | ValidationError[];
}

/**
 * 详细错误对象
 */
export interface ErrorDetail {
  message: string;
  code?: string;
  field?: string;
}

/**
 * Pydantic 验证错误
 */
export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

/**
 * 扩展错误响应（带字段验证）
 * @deprecated 使用 ErrorResponse 替代
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

// ============================================
// 认证模块类型（需求 1: AUTH-001, AUTH-002）
// ============================================

/**
 * AI 使用统计信息
 * 
 * @remarks
 * - `null` 值表示无限制
 * - `first_free_used` 标识是否已使用首次免费额度
 * - token 和请求数都有独立的配额和限制
 */
export interface AIUsage {
  /** 已使用的 token 数量 */
  tokens_used: number;
  /** token 配额（null 表示无限制） */
  token_quota: number | null;
  /** token 限制（null 表示无限制） */
  token_limit: number | null;
  /** 已使用的请求次数 */
  requests_used: number;
  /** 请求限制（null 表示无限制） */
  request_limit: number | null;
  /** 是否已使用首次免费额度 */
  first_free_used: boolean;
}

// ============================================
// 订阅模块类型（需求 2: SUB-001, SUB-002, SUB-003）
// ============================================

/**
 * 订阅计划详情
 * 
 * 修复需求: SUB-001 (price 类型), SUB-003 (duration 格式)
 */
export interface SubscriptionPlan {
  id: number;
  name: string;
  /** 价格（字符串格式避免精度丢失） */
  price: MoneyString;
  /** 原价（如有折扣） */
  original_price?: MoneyString;
  /** 订阅时长（天数） */
  duration_days: number;
  /** 格式化的时长（如 "30天", "365天"） */
  duration_display?: string;
  features: string[];
  is_active: boolean;
  created_at: DateTimeString;
  updated_at: DateTimeString;
}

/**
 * 完整的订阅信息
 * 
 * 修复需求: SUB-002 (plan 嵌套对象)
 */
export interface FullSubscription {
  id: number;
  user_id: number;
  plan_id: number;
  /** 完整的计划对象 */
  plan: SubscriptionPlan;
  status: string;
  start_date: DateTimeString;
  end_date: DateTimeString;
  trial_end_date?: DateTimeString;
  auto_renew: boolean;
  created_at: DateTimeString;
  updated_at: DateTimeString;
}

// ============================================
// 支付模块类型（需求 3: PAY-003）
// ============================================

/**
 * 创建订阅请求（含试用期）
 * 
 * 修复需求: PAY-003 (trial_days 参数)
 */
export interface CreateSubscriptionRequest {
  plan_id: number;
  payment_method: string;
  /** 试用期天数（可选） */
  trial_days?: number;
  auto_renew?: boolean;
  coupon_code?: string;
}

// ============================================
// 抖音模块类型（需求 4: DY-001）
// ============================================

/**
 * 启动抖音监控请求（含 Cookie）
 * 
 * 修复需求: DY-001 (Cookie 参数)
 */
export interface StartDouyinRequest {
  live_id?: string;
  live_url?: string;
  /** 可选的 Cookie 用于访问受限直播间 */
  cookie?: string;
}

// ============================================
// 音频转写模块类型（需求 5: AUDIO-001, AUDIO-002, AUDIO-004）
// ============================================

/**
 * VAD（语音活动检测）配置
 * 
 * 修复需求: AUDIO-001 (VAD 参数类型)
 */
export interface VADConfig {
  /** 最小静音时长（秒），默认 0.3 */
  vad_min_silence_sec?: number;
  /** 最小语音时长（秒），默认 0.1 */
  vad_min_speech_sec?: number;
  /** 语音结束后的延迟（秒），默认 0.2 */
  vad_hangover_sec?: number;
  /** 音量阈值（0-1），默认 0.01 */
  vad_rms?: number;
}

/**
 * 音频转写状态（增强）
 * 
 * 修复需求: AUDIO-002 (model 字段)
 */
export interface EnhancedAudioStatus {
  running: boolean;
  live_url?: string;
  session_id?: string;
  /** 当前使用的模型（如 "SenseVoice-Small"） */
  model?: string;
  start_time?: DateTimeString;
  // ... 其他现有字段
}

/**
 * WebSocket 消息类型
 * 
 * 修复需求: AUDIO-004 (消息类型定义)
 */
export type AudioWSMessageType = 'transcription' | 'level' | 'status' | 'error';

/**
 * WebSocket 消息基类
 */
export interface AudioWSMessage {
  type: AudioWSMessageType;
  timestamp: DateTimeString;
}

/**
 * 转写结果消息
 */
export interface TranscriptionMessage extends AudioWSMessage {
  type: 'transcription';
  text: string;
  language?: string;
  confidence?: number;
}

/**
 * 音量级别消息
 */
export interface LevelMessage extends AudioWSMessage {
  type: 'level';
  level: number;
}

/**
 * 状态变更消息
 */
export interface StatusMessage extends AudioWSMessage {
  type: 'status';
  status: string;
  details?: Record<string, any>;
}

/**
 * 错误消息
 */
export interface ErrorMessage extends AudioWSMessage {
  type: 'error';
  error: string;
  code?: string;
}

/**
 * 所有 WebSocket 消息的联合类型
 */
export type AudioWSMessageUnion = 
  | TranscriptionMessage 
  | LevelMessage 
  | StatusMessage 
  | ErrorMessage;

// ============================================
// 类型守卫（Type Guards）
// ============================================

/**
 * 判断是否是 Pydantic 验证错误数组
 */
export function isValidationErrorArray(
  detail: any
): detail is ValidationError[] {
  return Array.isArray(detail) && detail.every(
    (item) => 'loc' in item && 'msg' in item && 'type' in item
  );
}

/**
 * 判断是否是 ErrorDetail 对象
 */
export function isErrorDetail(detail: any): detail is ErrorDetail {
  return typeof detail === 'object' && detail !== null && 'message' in detail;
}

/**
 * 判断是否是转写结果消息
 */
export function isTranscriptionMessage(
  msg: AudioWSMessageUnion
): msg is TranscriptionMessage {
  return msg.type === 'transcription';
}

/**
 * 判断是否是音量级别消息
 */
export function isLevelMessage(msg: AudioWSMessageUnion): msg is LevelMessage {
  return msg.type === 'level';
}

/**
 * 判断是否是状态变更消息
 */
export function isStatusMessage(msg: AudioWSMessageUnion): msg is StatusMessage {
  return msg.type === 'status';
}

/**
 * 判断是否是错误消息
 */
export function isErrorMessage(msg: AudioWSMessageUnion): msg is ErrorMessage {
  return msg.type === 'error';
}

