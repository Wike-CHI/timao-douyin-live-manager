/**
 * 统一的支付和订阅 API（修复 MISC-004）
 * 封装两套 API 的差异，提供统一接口
 * 
 * 问题：项目中存在两套并行的 API
 * - /api/payment/*
 * - /api/subscription/*
 * 
 * 解决方案：创建统一入口，优先使用主 API，失败后降级到备用 API
 */

import authService from './authService';
import type { Plan, Subscription, Payment } from './payment';

const DEFAULT_BASE_URL = import.meta.env?.VITE_FASTAPI_URL as string || 'http://127.0.0.1:9030'; // 默认端口改为 9030，避免 Windows 端口排除范围 8930-9029

// 优先使用的 API 前缀（建议使用 /api/payment，更语义化）
const PRIMARY_API_PREFIX = '/api/payment';
const FALLBACK_API_PREFIX = '/api/subscription';

/**
 * 构建鉴权请求头
 */
const buildHeaders = async (): Promise<Record<string, string>> => {
  const authHeaders = await authService.getAuthHeaders();
  return {
    'Content-Type': 'application/json',
    ...authHeaders,
  };
};

/**
 * 处理响应
 */
const handleResponse = async <T>(response: Response): Promise<T> => {
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = (data as any)?.detail || response.statusText || '请求失败';
    throw new Error(detail);
  }
  return data as T;
};

/**
 * 智能 API 调用：优先使用主 API，失败后降级到备用 API
 */
async function smartFetch<T>(
  primaryPath: string,
  fallbackPath?: string,
  options?: RequestInit
): Promise<T> {
  const baseUrl = DEFAULT_BASE_URL;
  const headers = await buildHeaders();
  
  try {
    // 尝试主 API
    const response = await fetch(`${baseUrl}${primaryPath}`, {
      ...options,
      headers: {
        ...headers,
        ...(options?.headers || {}),
      },
    });
    return handleResponse<T>(response);
  } catch (error) {
    if (!fallbackPath) {
      throw error;
    }
    
    // 降级到备用 API
    console.warn(`主 API ${primaryPath} 失败，尝试备用 API ${fallbackPath}`);
    const response = await fetch(`${baseUrl}${fallbackPath}`, {
      ...options,
      headers: {
        ...headers,
        ...(options?.headers || {}),
      },
    });
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

/**
 * 获取单个套餐详情
 */
export const getPlan = async (planId: string): Promise<Plan> => {
  return smartFetch<Plan>(
    `${PRIMARY_API_PREFIX}/plans/${planId}`,
    `${FALLBACK_API_PREFIX}/plans/${planId}`
  );
};

/**
 * 获取用户当前订阅
 */
export const getCurrentSubscription = async (): Promise<Subscription | null> => {
  try {
    return await smartFetch<Subscription>(
      `${PRIMARY_API_PREFIX}/subscriptions/current`,
      `${FALLBACK_API_PREFIX}/current`
    );
  } catch (error) {
    // 如果没有订阅，返回 null
    if ((error as any)?.message?.includes('404')) {
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
  return smartFetch<Subscription[]>(
    `${PRIMARY_API_PREFIX}/subscriptions?skip=${skip}&limit=${limit}`,
    `${FALLBACK_API_PREFIX}/subscriptions?skip=${skip}&limit=${limit}`
  );
};

/**
 * 创建订阅
 */
export const createSubscription = async (
  planId: number,
  couponCode?: string
): Promise<Subscription> => {
  const body: any = { plan_id: planId };
  if (couponCode) {
    body.coupon_code = couponCode;
  }
  
  return smartFetch<Subscription>(
    `${PRIMARY_API_PREFIX}/subscriptions`,
    `${FALLBACK_API_PREFIX}/subscriptions`,
    {
      method: 'POST',
      body: JSON.stringify(body),
    }
  );
};

/**
 * 取消订阅
 */
export const cancelSubscription = async (
  subscriptionId: number
): Promise<Subscription> => {
  return smartFetch<Subscription>(
    `${PRIMARY_API_PREFIX}/subscriptions/${subscriptionId}/cancel`,
    `${FALLBACK_API_PREFIX}/subscriptions/${subscriptionId}/cancel`,
    {
      method: 'POST',
    }
  );
};

/**
 * 获取支付历史
 */
export const getPaymentHistory = async (
  skip: number = 0,
  limit: number = 10
): Promise<Payment[]> => {
  return smartFetch<Payment[]>(
    `${PRIMARY_API_PREFIX}/payments?skip=${skip}&limit=${limit}`,
    `${FALLBACK_API_PREFIX}/payment_history?skip=${skip}&limit=${limit}`
  );
};

/**
 * 导出所有统一 API
 */
export default {
  getPlans,
  getPlan,
  getCurrentSubscription,
  getSubscriptionHistory,
  createSubscription,
  cancelSubscription,
  getPaymentHistory,
};

