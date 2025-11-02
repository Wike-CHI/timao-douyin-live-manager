import useAuthStore from '../store/useAuthStore';
import authService from './authService';
import { SubscriptionPlan, CreateSubscriptionRequest } from '../types/api-types';
import { apiCall } from '../utils/error-handler';

const DEFAULT_BASE_URL = import.meta.env?.VITE_FASTAPI_URL as string || 'http://127.0.0.1:9019';

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
const handleResponse = async <T>(response: Response): Promise<T> => {
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = (data as any)?.detail || response.statusText || '请求失败';
    throw new Error(detail);
  }
  return data as T;
};

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
 */
export const getPlans = async (baseUrl: string = DEFAULT_BASE_URL): Promise<Plan[]> => {
  // 优先尝试 /api/payment/plans，如果失败则尝试 /api/subscription/plans
  try {
    const response = await authFetch(`${baseUrl}/api/payment/plans`);
    return handleResponse(response);
  } catch (error) {
    // 如果 /api/payment/plans 失败，尝试使用 /api/subscription/plans
    console.warn('尝试使用备用端点 /api/subscription/plans');
    const response = await authFetch(`${baseUrl}/api/subscription/plans`);
    const data = await handleResponse<any[]>(response);
    // 转换数据格式以匹配 Plan 接口
    return data.map(plan => ({
      ...plan,
      duration: plan.duration_days ? `${plan.duration_days}天` : 'monthly',
      is_popular: false,
      original_price: plan.price
    }));
  }
};

/**
 * 获取单个套餐详情
 */
export const getPlan = async (planId: string, baseUrl: string = DEFAULT_BASE_URL): Promise<Plan> => {
  const response = await authFetch(`${baseUrl}/api/payment/plans/${planId}`);
  return handleResponse(response);
};

// ========== 订阅管理 API ==========

/**
 * 创建订阅（支持试用期，修复 PAY-003）
 */
export const createSubscription = async (
  request: CreateSubscriptionRequest,
  baseUrl: string = DEFAULT_BASE_URL
): Promise<Subscription> => {
  const response = await authFetch(`${baseUrl}/api/payment/subscriptions`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
  return handleResponse(response);
};

/**
 * 获取用户当前订阅
 */
export const getCurrentSubscription = async (baseUrl: string = DEFAULT_BASE_URL): Promise<Subscription | null> => {
  try {
    // 优先尝试 /api/payment/subscriptions/current
    const response = await authFetch(`${baseUrl}/api/payment/subscriptions/current`);
    return handleResponse(response);
  } catch (error) {
    // 如果失败，尝试使用 /api/subscription/current
    try {
      console.warn('尝试使用备用端点 /api/subscription/current');
      const response = await authFetch(`${baseUrl}/api/subscription/current`);
      const data = await handleResponse<any>(response);
      // 转换数据格式以匹配 Subscription 接口
      if (!data) return null;
      return {
        ...data,
        plan_name: data.plan?.name,
        expires_at: data.end_date
      };
    } catch (fallbackError) {
      // 如果没有订阅，返回 null
      if ((fallbackError as any)?.message?.includes('404')) {
        return null;
      }
      throw fallbackError;
    }
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
  const response = await authFetch(`${baseUrl}/api/payment/subscriptions?skip=${skip}&limit=${limit}`);
  return handleResponse(response);
};

/**
 * 取消订阅
 */
export const cancelSubscription = async (
  subscriptionId: string,
  baseUrl: string = DEFAULT_BASE_URL
): Promise<Subscription> => {
  const response = await authFetch(`${baseUrl}/api/payment/subscriptions/${subscriptionId}/cancel`, {
    method: 'POST',
  });
  return handleResponse(response);
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
  
  const response = await authFetch(`${baseUrl}/api/payment/subscriptions/${subscriptionId}/renew`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
  return handleResponse(response);
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

/**
 * 获取支付详情
 */
export const getPayment = async (paymentId: string, baseUrl: string = DEFAULT_BASE_URL): Promise<Payment> => {
  const response = await authFetch(`${baseUrl}/api/payment/payments/${paymentId}`);
  return handleResponse(response);
};

/**
 * 获取用户支付历史
 */
export const getPaymentHistory = async (
  skip: number = 0,
  limit: number = 10,
  baseUrl: string = DEFAULT_BASE_URL
): Promise<Payment[]> => {
  const response = await authFetch(`${baseUrl}/api/payment/payments?skip=${skip}&limit=${limit}`);
  return handleResponse(response);
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
  const response = await authFetch(`${baseUrl}/api/payment/coupons/validate`, {
    method: 'POST',
    body: JSON.stringify({
      code: code,
      amount: amount,
    }),
  });
  return handleResponse(response);
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
  const response = await authFetch(`${baseUrl}/api/subscription/create_payment`, {
    method: 'POST',
    body: JSON.stringify({
      plan_id: planId,
      payment_method: method,
    }),
  });
  return handleResponse(response);
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
  
  const response = await authFetch(`${baseUrl}/api/subscription/confirm_payment`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
  return handleResponse(response);
};

/**
 * 获取支付历史 (订阅专用API)
 */
export const getSubscriptionPaymentHistory = async (
  skip: number = 0,
  limit: number = 10,
  baseUrl: string = DEFAULT_BASE_URL
): Promise<Payment[]> => {
  const response = await authFetch(`${baseUrl}/api/subscription/payment_history?skip=${skip}&limit=${limit}`);
  return handleResponse(response);
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
  
  const response = await authFetch(`${baseUrl}/api/subscription/consume_points`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
  return handleResponse(response);
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
  const response = await authFetch(`${baseUrl}/api/subscription/check_points?points=${points}`);
  return handleResponse(response);
};

/**
 * 导出统一的 fetch 函数供其他模块使用
 */
export { authFetch, buildHeaders };