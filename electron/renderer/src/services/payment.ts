import useAuthStore from '../store/useAuthStore';
import authService from './authService';
import { SubscriptionPlan, CreateSubscriptionRequest } from '../types/api-types';
import { apiCall } from '../utils/error-handler';

const DEFAULT_BASE_URL = import.meta.env?.VITE_FASTAPI_URL as string || 'http://127.0.0.1:9030'; // 默认端口改为 9030，避免 Windows 端口排除范围 8930-9029

/**
 * 构建包含鉴权信息的请求头
 */
const buildHeaders = async (): Promise<Record<string, string>> => {
  const authHeaders = await authService.getAuthHeaders();
  return {
    'Content-Type': 'application/json',
    ...authHeaders,
  };
};

/**
 * 统一的 fetch 包装函数，自动添加鉴权头
 */
const authFetch = async (url: string, options?: RequestInit): Promise<Response> => {
  const headers = {
    ...(await buildHeaders()),
    ...(options?.headers || {}),
  };
  
  return fetch(url, {
    ...options,
    headers,
  });
};

/**
 * 处理响应（保留用于兼容性）
 */

// ========== 类型定义 ==========

/**
 * 套餐信息（修复 PAY-001, PAY-004）
 * 对应后端: PlanResponse (server/app/api/payment.py:56-74)
 * 
 * 注意:
 * - price/original_price 使用字符串避免精度丢失
 * - created_at/updated_at 是 ISO 8601 格式的日期时间字符串
 */
export interface Plan {
  id: number;
  name: string;
  description?: string;
  plan_type: string;
  duration: string;
  price: string; // 修改为 string 避免精度丢失（PAY-001）
  original_price?: string; // 修改为 string 避免精度丢失（PAY-001）
  currency: string;
  features: Record<string, any>;
  limits: Record<string, any>;
  is_active: boolean;
  is_popular?: boolean; // 添加 is_popular 属性
  sort_order: number;
  created_at: string;
  updated_at: string;
}

/**
 * 订阅信息（修复 PAY-004）
 * 对应后端: SubscriptionResponse (server/app/api/payment.py:84-104)
 * 
 * 注意: 所有日期时间字段都是 ISO 8601 格式的字符串
 * - start_date: 订阅开始时间
 * - end_date: 订阅结束时间
 * - trial_end_date: 试用结束时间（可选）
 * - cancelled_at: 取消时间（可选）
 * - created_at: 创建时间
 * - updated_at: 更新时间
 */
export interface Subscription {
  id: number;
  user_id: number;
  plan_id: number;
  status: 'active' | 'expired' | 'cancelled' | 'pending';
  start_date: string;  // ISO 8601 日期时间字符串
  end_date: string;  // ISO 8601 日期时间字符串
  auto_renew: boolean;
  trial_end_date?: string;  // ISO 8601 日期时间字符串
  cancelled_at?: string;  // ISO 8601 日期时间字符串
  cancel_reason?: string;
  is_active: boolean;
  is_trial: boolean;
  days_remaining: number;
  plan?: Plan;
  plan_name?: string; // 添加 plan_name 属性
  expires_at?: string; // 添加 expires_at 属性
  created_at: string;  // ISO 8601 日期时间字符串
  updated_at: string;  // ISO 8601 日期时间字符串
}

export interface Payment {
  id: number;
  user_id: number;
  subscription_id?: number;
  amount: string; // 修改为 string 避免精度丢失（PAY-001）
  method: 'alipay' | 'wechat' | 'bank_transfer' | 'points';
  status: 'pending' | 'completed' | 'failed' | 'cancelled';
  transaction_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Coupon {
  id: string;
  code: string;
  discount_type: 'percentage' | 'fixed';
  discount_value: string; // 修改为 string 避免精度丢失（PAY-001）
  min_amount?: string; // 修改为 string 避免精度丢失（PAY-001）
  max_uses?: number;
  used_count: number;
  expires_at?: string;
  is_active: boolean;
}

export interface PaymentStatistics {
  total_revenue: string; // 修改为 string 避免精度丢失（PAY-001）
  total_payments: number;
  successful_payments: number;
  failed_payments: number;
  average_payment: string; // 修改为 string 避免精度丢失（PAY-001）
}

export interface SubscriptionStatistics {
  total_subscriptions: number;
  active_subscriptions: number;
  expired_subscriptions: number;
  cancelled_subscriptions: number;
  total_points_sold: number;
  total_points_used: number;
}

// ========== 套餐管理 API ==========

/**
 * 获取所有可用套餐
 * 注意：统一使用 /api/subscription/plans（废弃 /api/payment/plans）
 */
export const getPlans = async (baseUrl: string = DEFAULT_BASE_URL): Promise<Plan[]> => {
  const data = await apiCall<any[]>(
    () => authFetch(`${baseUrl}/api/subscription/plans`),
    '获取套餐列表'
  );
  
  // 转换 subscription_plans 格式为前端 Plan 接口
  return data.map(plan => ({
    id: plan.id,
    name: plan.name || plan.display_name,
    description: plan.description,
    plan_type: plan.plan_type,
    duration: plan.billing_cycle ? `${plan.billing_cycle}天` : '30天',
    price: String(plan.price),
    original_price: String(plan.price),
    currency: plan.currency || 'CNY',
    features: plan.features ? (typeof plan.features === 'string' ? JSON.parse(plan.features) : plan.features) : {},
    limits: {
      max_streams: plan.max_streams,
      max_storage_gb: plan.max_storage_gb,
      max_ai_requests: plan.max_ai_requests,
      max_export_count: plan.max_export_count,
    },
    is_active: plan.is_active,
    is_popular: plan.is_popular || false,
    sort_order: plan.sort_order || 0,
    created_at: plan.created_at,
    updated_at: plan.updated_at,
  }));
};

/**
 * 获取单个套餐详情
 */
export const getPlan = async (planId: string, baseUrl: string = DEFAULT_BASE_URL): Promise<Plan> => {
  return apiCall(
    () => authFetch(`${baseUrl}/api/payment/plans/${planId}`),
    '获取套餐详情'
  );
};

// ========== 订阅管理 API ==========

/**
 * 创建订阅（支持试用期，修复 PAY-003）
 */
export const createSubscription = async (
  request: CreateSubscriptionRequest,
  baseUrl: string = DEFAULT_BASE_URL
): Promise<Subscription> => {
  return apiCall(
    () => authFetch(`${baseUrl}/api/payment/subscriptions`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
    '创建订阅'
  );
};

/**
 * 获取用户当前订阅
 * 注意：统一使用 /api/subscription/current
 */
export const getCurrentSubscription = async (baseUrl: string = DEFAULT_BASE_URL): Promise<Subscription | null> => {
  try {
    const data = await apiCall<any>(
      () => authFetch(`${baseUrl}/api/subscription/current`),
      '获取当前订阅'
    );
    
    if (!data) return null;
    
    // 转换格式
    return {
      ...data,
      plan_name: data.plan?.name || data.plan?.display_name,
      expires_at: data.end_date
    };
  } catch (error) {
    // 如果没有订阅，返回 null
    if ((error as any)?.message?.includes('404') || (error as any)?.message?.includes('没有找到')) {
      return null;
    }
    throw error;
  }
};

/**
 * 获取用户订阅历史
 */
export const getSubscriptionHistory = async (
  skip: number = 0,
  limit: number = 10,
  baseUrl: string = DEFAULT_BASE_URL
): Promise<Subscription[]> => {
  return apiCall(
    () => authFetch(`${baseUrl}/api/payment/subscriptions?skip=${skip}&limit=${limit}`),
    '获取订阅历史'
  );
};

/**
 * 取消订阅
 */
export const cancelSubscription = async (
  subscriptionId: string,
  baseUrl: string = DEFAULT_BASE_URL
): Promise<Subscription> => {
  return apiCall(
    () => authFetch(`${baseUrl}/api/payment/subscriptions/${subscriptionId}/cancel`, {
      method: 'POST',
    }),
    '取消订阅'
  );
};

/**
 * 续费订阅
 */
export const renewSubscription = async (
  subscriptionId: string,
  planId: string,
  couponCode?: string,
  baseUrl: string = DEFAULT_BASE_URL
): Promise<Subscription> => {
  const body: any = { plan_id: planId };
  if (couponCode) {
    body.coupon_code = couponCode;
  }

  return apiCall(
    () => authFetch(`${baseUrl}/api/payment/subscriptions/${subscriptionId}/renew`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
    '续费订阅'
  );
};

// ========== 支付管理 API ==========

/**
 * 创建支付请求参数（修复 PAY-005）
 */
export interface CreatePaymentRequest {
  subscription_id?: number;  // 可选，如果是订阅支付
  amount: string;  // 必填，支付金额（使用字符串避免精度丢失）
  payment_method: 'alipay' | 'wechat' | 'bank_transfer' | 'points';
  currency?: string;  // 可选，默认 CNY
  coupon_code?: string;  // 可选，优惠券代码
  return_url?: string;  // 可选，支付成功返回 URL
}

/**
 * 创建支付（修复 PAY-005）
 */
export const createPayment = async (
  request: CreatePaymentRequest,
  baseUrl: string = DEFAULT_BASE_URL
): Promise<Payment> => {
  return apiCall(
    () => authFetch(`${baseUrl}/api/payment/payments`, {
      method: 'POST',
      body: JSON.stringify({
        subscription_id: request.subscription_id,
        amount: request.amount,
        payment_method: request.payment_method,
        currency: request.currency || 'CNY',
        coupon_code: request.coupon_code,
        return_url: request.return_url,
      }),
    }),
    '创建支付'
  );
};

/**
 * 获取支付详情
 */
export const getPayment = async (paymentId: string, baseUrl: string = DEFAULT_BASE_URL): Promise<Payment> => {
  return apiCall(
    () => authFetch(`${baseUrl}/api/payment/payments/${paymentId}`),
    '获取支付详情'
  );
};

/**
 * 获取用户支付历史
 */
export const getPaymentHistory = async (
  skip: number = 0,
  limit: number = 10,
  baseUrl: string = DEFAULT_BASE_URL
): Promise<Payment[]> => {
  return apiCall(
    () => authFetch(`${baseUrl}/api/payment/payments?skip=${skip}&limit=${limit}`),
    '获取支付历史'
  );
};

// ========== 优惠券管理 API ==========

/**
 * 验证优惠券
 */
export const validateCoupon = async (
  code: string,
  amount: string,  // 修改为 string（PAY-001）
  baseUrl: string = DEFAULT_BASE_URL
): Promise<{
  valid: boolean;
  coupon?: Coupon;
  discount_amount?: string;  // 修改为 string（PAY-001）
  final_amount?: string;  // 修改为 string（PAY-001）
  message?: string;
}> => {
  return apiCall(
    () => authFetch(`${baseUrl}/api/payment/coupons/validate`, {
      method: 'POST',
      body: JSON.stringify({
        code: code,
        amount: amount,
      }),
    }),
    '验证优惠券'
  );
};

// ========== 订阅专用 API (来自 /api/subscription) ==========

/**
 * 创建并确认支付 (订阅专用API)
 */
export const createAndConfirmPayment = async (
  planId: string,
  method: 'alipay' | 'wechat' | 'bank_transfer',
  baseUrl: string = DEFAULT_BASE_URL
): Promise<{
  success: boolean;
  subscription?: Subscription;
  payment?: Payment;
  message?: string;
}> => {
  return apiCall(
    () => authFetch(`${baseUrl}/api/subscription/create_payment`, {
      method: 'POST',
      body: JSON.stringify({
        plan_id: planId,
        payment_method: method,
      }),
    }),
    '创建并确认支付'
  );
};

/**
 * 确认支付 (订阅专用API)
 */
export const confirmPayment = async (
  paymentId: string,
  transactionId?: string,
  baseUrl: string = DEFAULT_BASE_URL
): Promise<{
  success: boolean;
  subscription?: Subscription;
  payment?: Payment;
  message?: string;
}> => {
  const body: any = { payment_id: paymentId };
  if (transactionId) {
    body.transaction_id = transactionId;
  }

  return apiCall(
    () => authFetch(`${baseUrl}/api/subscription/confirm_payment`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
    '确认支付'
  );
};

/**
 * 获取支付历史 (订阅专用API)
 */
export const getSubscriptionPaymentHistory = async (
  skip: number = 0,
  limit: number = 10,
  baseUrl: string = DEFAULT_BASE_URL
): Promise<Payment[]> => {
  return apiCall(
    () => authFetch(`${baseUrl}/api/subscription/payment_history?skip=${skip}&limit=${limit}`),
    '获取订阅支付历史'
  );
};

// ========== 积分消耗 API ==========

/**
 * 消耗积分
 */
export const consumePoints = async (
  points: number,
  description?: string,
  baseUrl: string = DEFAULT_BASE_URL
): Promise<{
  success: boolean;
  remaining_points: number;
  message?: string;
}> => {
  const body: any = { points: points };
  if (description) {
    body.description = description;
  }

  return apiCall(
    () => authFetch(`${baseUrl}/api/subscription/consume_points`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
    '消耗积分'
  );
};

/**
 * 检查积分是否足够
 */
export const checkPointsAvailable = async (
  points: number,
  baseUrl: string = DEFAULT_BASE_URL
): Promise<{
  available: boolean;
  current_points: number;
  required_points: number;
  message?: string;
}> => {
  return apiCall(
    () => authFetch(`${baseUrl}/api/subscription/check_points?points=${points}`),
    '检查积分'
  );
};

/**
 * 导出统一的 fetch 函数供其他模块使用
 */
export { authFetch, buildHeaders };