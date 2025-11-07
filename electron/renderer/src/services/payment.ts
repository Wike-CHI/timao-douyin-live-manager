import { fetchJsonWithAuth } from './http';
import {
  Plan,
  Subscription,
  Payment,
  Coupon,
  PaymentStatistics,
  SubscriptionStatistics,
  CreateSubscriptionRequest,
} from '../types/api-types';
import { apiCall } from '../utils/error-handler';

// ========== 套餐管理 API ==========

/**
 * 获取所有可用套餐
 * 注意：统一使用 /api/subscription/plans（废弃 /api/payment/plans）
 */
export const getPlans = async (): Promise<Plan[]> => {
  const data = await apiCall<any[]>(
    () => fetchJsonWithAuth('main', '/api/subscription/plans'),
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
export const getPlan = async (planId: string): Promise<Plan> => {
  return apiCall(
    () => fetchJsonWithAuth('main', `/api/payment/plans/${planId}`),
    '获取套餐详情'
  );
};

// ========== 订阅管理 API ==========

/**
 * 创建订阅（支持试用期，修复 PAY-003）
 */
export const createSubscription = async (
  request: CreateSubscriptionRequest
): Promise<Subscription> => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/payment/subscriptions', {
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
export const getCurrentSubscription = async (): Promise<Subscription | null> => {
  try {
    const data = await apiCall<any>(
      () => fetchJsonWithAuth('main', '/api/subscription/current'),
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
  limit: number = 10
): Promise<Subscription[]> => {
  return apiCall(
    () => fetchJsonWithAuth('main', `/api/payment/subscriptions?skip=${skip}&limit=${limit}`),
    '获取订阅历史'
  );
};

/**
 * 取消订阅
 */
export const cancelSubscription = async (
  subscriptionId: string
): Promise<Subscription> => {
  return apiCall(
    () => fetchJsonWithAuth('main', `/api/payment/subscriptions/${subscriptionId}/cancel`, {
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
  couponCode?: string
): Promise<Subscription> => {
  const body: any = { plan_id: planId };
  if (couponCode) {
    body.coupon_code = couponCode;
  }
  
  return apiCall(
    () => fetchJsonWithAuth('main', `/api/payment/subscriptions/${subscriptionId}/renew`, {
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
  request: CreatePaymentRequest
): Promise<Payment> => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/payment/payments', {
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
export const getPayment = async (paymentId: string): Promise<Payment> => {
  return apiCall(
    () => fetchJsonWithAuth('main', `/api/payment/payments/${paymentId}`),
    '获取支付详情'
  );
};

/**
 * 获取用户支付历史
 */
export const getPaymentHistory = async (
  skip: number = 0,
  limit: number = 10
): Promise<Payment[]> => {
  return apiCall(
    () => fetchJsonWithAuth('main', `/api/payment/payments?skip=${skip}&limit=${limit}`),
    '获取支付历史'
  );
};

// ========== 优惠券管理 API ==========

/**
 * 验证优惠券
 */
export const validateCoupon = async (
  code: string,
  amount: string
): Promise<{
  valid: boolean;
  coupon?: Coupon;
  discount_amount?: string;
  final_amount?: string;
  message?: string;
}> => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/payment/coupons/validate', {
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
  method: 'alipay' | 'wechat' | 'bank_transfer'
): Promise<{
  success: boolean;
  subscription?: Subscription;
  payment?: Payment;
  message?: string;
}> => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/subscription/create_payment', {
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
  transactionId?: string
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
    () => fetchJsonWithAuth('main', '/api/subscription/confirm_payment', {
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
  limit: number = 10
): Promise<Payment[]> => {
  return apiCall(
    () => fetchJsonWithAuth('main', `/api/subscription/payment_history?skip=${skip}&limit=${limit}`),
    '获取订阅支付历史'
  );
};

// ========== 积分消耗 API ==========

/**
 * 消耗积分
 */
export const consumePoints = async (
  points: number,
  description?: string
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
    () => fetchJsonWithAuth('main', '/api/subscription/consume_points', {
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
  points: number
): Promise<{
  available: boolean;
  current_points: number;
  required_points: number;
  message?: string;
}> => {
  return apiCall(
    () => fetchJsonWithAuth('main', `/api/subscription/check_points?points=${points}`),
    '检查积分'
  );
};