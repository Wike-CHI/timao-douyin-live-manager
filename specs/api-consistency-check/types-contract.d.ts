/**
 * API 类型契约定义
 * 
 * 本文件由 API 一致性检查工具自动生成
 * 生成时间: 2025-11-02
 * 版本: 1.0.0
 * 
 * 使用说明:
 * 1. 这是前后端共享的类型定义
 * 2. 所有日期时间使用 string 类型（ISO 8601 格式）
 * 3. 所有金额使用 string 类型（避免精度丢失）
 * 4. 根据后端 Pydantic 模型生成
 */

// ==================== 基础类型 ====================

/**
 * ISO 8601 日期时间字符串
 * 格式示例: "2025-11-02T15:30:00Z" 或 "2025-11-02T15:30:00+08:00"
 */
export type DateTimeString = string;

/**
 * ISO 8601 日期字符串
 * 格式示例: "2025-11-02"
 */
export type DateString = string;

/**
 * 金额字符串（避免浮点数精度问题）
 * 格式示例: "99.00", "0.99"
 */
export type MoneyString = string;

// ==================== 认证模块 ====================

/**
 * 用户角色枚举
 */
export type UserRole = 'user' | 'admin' | 'super_admin';

/**
 * 用户状态枚举
 */
export type UserStatus = 'active' | 'inactive' | 'suspended' | 'banned';

/**
 * 用户信息
 * 对应后端: UserResponse (server/app/api/auth.py:76-90)
 */
export interface UserInfo {
  id: number;
  username: string;
  email: string;
  nickname?: string | null;
  avatar_url?: string | null;
  role: UserRole;
  status: UserStatus;
  email_verified: boolean;
  phone_verified: boolean;
  created_at: DateTimeString;
}

/**
 * AI 使用统计
 * 对应后端: aiUsage 字段 (server/app/api/auth.py:104)
 */
export interface AIUsage {
  requests_used: number;
  requests_limit: number;
  tokens_used: number;
  tokens_limit: number;
  first_free_used: boolean;
}

/**
 * 登录请求
 * 对应后端: UserLoginRequest (server/app/api/auth.py:70-73)
 */
export interface LoginRequest {
  username_or_email: string;
  password: string;
}

/**
 * 登录响应
 * 对应后端: LoginResponse (server/app/api/auth.py:93-104)
 */
export interface LoginResponse {
  success: boolean;
  token: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserInfo;
  isPaid: boolean;
  firstFreeUsed?: boolean;
  aiUsage?: AIUsage;
}

/**
 * 注册请求
 * 对应后端: UserRegisterRequest (server/app/api/auth.py:32-67)
 */
export interface RegisterRequest {
  email: string;
  password: string;
  nickname?: string | null;
  username?: string | null;
  phone?: string | null;
}

/**
 * 注册响应
 */
export interface RegisterResponse {
  success: boolean;
  user: UserInfo;
}

/**
 * 刷新令牌请求
 * 对应后端: RefreshTokenRequest (server/app/api/auth.py:107-109)
 */
export interface RefreshTokenRequest {
  refresh_token: string;
}

// ==================== 支付/订阅模块 ====================

/**
 * 套餐类型
 */
export type PlanType = 'free' | 'basic' | 'professional' | 'enterprise';

/**
 * 套餐时长
 */
export type PlanDuration = 'monthly' | 'quarterly' | 'yearly' | 'lifetime';

/**
 * 支付方式
 */
export type PaymentMethod = 'alipay' | 'wechat' | 'bank_transfer' | 'stripe' | 'points';

/**
 * 支付状态
 */
export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'cancelled';

/**
 * 订阅状态
 */
export type SubscriptionStatus = 'active' | 'expired' | 'cancelled' | 'pending';

/**
 * 套餐信息
 * 对应后端: PlanResponse (server/app/api/payment.py:56-74)
 */
export interface Plan {
  id: number;
  name: string;
  description?: string | null;
  plan_type: PlanType;
  duration: string;  // 后端为枚举，前端显示为字符串
  price: MoneyString;  // 使用字符串避免精度丢失
  original_price: MoneyString;
  currency: string;
  features: Record<string, any>;
  limits: Record<string, any>;
  is_active: boolean;
  sort_order: number;
  created_at: DateTimeString;
  updated_at: DateTimeString;
}

/**
 * 订阅信息
 * 对应后端: SubscriptionResponse (server/app/api/payment.py:84-104)
 */
export interface Subscription {
  id: number;
  user_id: number;
  plan_id: number;
  status: SubscriptionStatus;
  start_date: DateTimeString;
  end_date: DateTimeString;
  auto_renew: boolean;
  trial_end_date?: DateTimeString | null;
  cancelled_at?: DateTimeString | null;
  cancel_reason?: string | null;
  is_active: boolean;
  is_trial: boolean;
  days_remaining: number;
  plan: Plan;  // 嵌套的完整套餐对象
  created_at: DateTimeString;
  updated_at: DateTimeString;
}

/**
 * 创建订阅请求
 * 对应后端: SubscriptionCreate (server/app/api/payment.py:77-81)
 */
export interface CreateSubscriptionRequest {
  plan_id: number;
  trial_days?: number;  // 0-30 天
  auto_renew?: boolean;  // 默认 true
}

/**
 * 创建支付请求
 * 对应后端: PaymentCreate (server/app/api/payment.py:107-114)
 */
export interface CreatePaymentRequest {
  subscription_id?: number | null;
  amount: MoneyString;  // 必填，使用字符串
  payment_method: PaymentMethod;
  currency?: string;  // 默认 "CNY"
  coupon_code?: string | null;
  return_url?: string | null;
}

/**
 * 支付信息
 * 对应后端: PaymentResponse (server/app/api/payment.py:117-136)
 */
export interface Payment {
  id: number;
  user_id: number;
  subscription_id?: number | null;
  amount: MoneyString;
  currency: string;
  payment_method: PaymentMethod;
  status: PaymentStatus;
  transaction_id: string;
  external_id?: string | null;
  payment_url?: string | null;
  paid_at?: DateTimeString | null;
  failed_at?: DateTimeString | null;
  failure_reason?: string | null;
  created_at: DateTimeString;
  updated_at: DateTimeString;
}

/**
 * 优惠券信息
 */
export interface Coupon {
  id: string;
  code: string;
  discount_type: 'percentage' | 'fixed';
  discount_value: MoneyString;
  min_amount?: MoneyString | null;
  max_uses?: number | null;
  used_count: number;
  expires_at?: DateTimeString | null;
  is_active: boolean;
}

/**
 * 验证优惠券响应
 */
export interface ValidateCouponResponse {
  valid: boolean;
  coupon?: Coupon;
  discount_amount?: MoneyString;
  final_amount?: MoneyString;
  message?: string;
}

// ==================== 抖音模块 ====================

/**
 * 启动抖音监控请求
 * 对应后端: StartMonitoringRequest (server/app/api/douyin.py:24-28)
 */
export interface StartDouyinRequest {
  live_id?: string | null;
  live_url?: string | null;
  cookie?: string | null;  // 可选的 Cookie 字符串
}

/**
 * 抖音监控响应
 */
export interface DouyinResponse {
  success: boolean;
  message?: string;
  live_id?: string;
  data?: Record<string, any>;
}

/**
 * 抖音监控状态
 * 对应后端: StatusResponse (server/app/api/douyin.py:50-54)
 */
export interface DouyinStatus {
  is_running: boolean;
  live_id?: string | null;
  room_id?: string | null;
  last_error?: string | null;
  persist_enabled?: boolean;
  persist_root?: string | null;
  fetcher_status?: Record<string, any>;  // 抓取器详细状态
}

/**
 * 抖音流事件
 */
export interface DouyinStreamEvent {
  type: string;
  payload?: Record<string, unknown> | null;
  timestamp?: number;
}

// ==================== 音频转写模块 ====================

/**
 * 启动音频转写请求
 * 对应后端: StartReq (server/app/api/live_audio.py:25-50)
 */
export interface StartLiveAudioRequest {
  live_url: string;
  session_id?: string | null;
  chunk_duration?: number;  // 0.2-2.0 秒
  profile?: 'fast' | 'stable';
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

/**
 * 音频转写状态
 */
export interface LiveAudioStatus {
  is_running: boolean;
  live_id?: string | null;
  live_url?: string | null;
  session_id?: string | null;
  mode?: string;
  profile?: string;
  model?: string;  // 模型大小（如 "small"）
  advanced?: {
    agc_enabled?: boolean;
    agc_gain?: number;
    diarizer_active?: boolean;
    max_speakers?: number;
    last_speaker?: string | null;
    music_filter?: boolean;
    music_detection_enabled?: boolean;
    music_guard_active?: boolean;
    music_guard_score?: number;
    music_last_title?: string | null;
    music_last_score?: number;
    music_last_detected_at?: number;
    music_match_hold_until?: number;
    persist_enabled?: boolean;
    persist_root?: string | null;
  };
  stats?: {
    total_audio_chunks?: number;
    successful_transcriptions?: number;
    failed_transcriptions?: number;
    average_confidence?: number;
  };
}

/**
 * 音频高级设置
 */
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

/**
 * WebSocket 消息类型
 */
export type LiveAudioMessageType = 
  | 'transcription'
  | 'transcription_delta'
  | 'level'
  | 'status'
  | 'pong'
  | 'error';

/**
 * WebSocket 消息
 */
export interface LiveAudioMessage {
  type: LiveAudioMessageType;
  data?: any;
}

// ==================== 错误响应 ====================

/**
 * 标准错误响应
 * FastAPI 默认格式
 */
export interface ErrorResponse {
  detail: string;
}

/**
 * 扩展错误响应
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

// ==================== 工具类型 ====================

/**
 * 分页请求参数
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

// ==================== 导出所有类型 ====================

export type {
  // 认证
  UserInfo,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  RefreshTokenRequest,
  AIUsage,
  // 支付订阅
  Plan,
  Subscription,
  Payment,
  Coupon,
  CreateSubscriptionRequest,
  CreatePaymentRequest,
  ValidateCouponResponse,
  // 抖音
  StartDouyinRequest,
  DouyinResponse,
  DouyinStatus,
  DouyinStreamEvent,
  // 音频转写
  StartLiveAudioRequest,
  LiveAudioStatus,
  LiveAudioAdvancedSettings,
  LiveAudioMessage,
  LiveAudioMessageType,
  // 错误
  ErrorResponse,
  ExtendedErrorResponse,
  // 工具
  PaginationParams,
  PaginatedResponse,
  BaseResponse,
  // 基础类型
  DateTimeString,
  DateString,
  MoneyString,
  UserRole,
  UserStatus,
  PlanType,
  PlanDuration,
  PaymentMethod,
  PaymentStatus,
  SubscriptionStatus,
};

