import useAuthStore from '../store/useAuthStore';
import authService from './authService';
import { apiConfig, buildApiUrl, requestWithRetry } from './apiConfig';

// 使用统一的API配置管理
const getAuthBaseUrl = () => {
  // 优先使用环境变量配置的认证服务地址
  const authUrl = import.meta.env?.VITE_AUTH_BASE_URL?.trim();
  if (authUrl) {
    return authUrl;
  }
  
  // 回退到主服务地址
  return apiConfig.getServiceUrl('main');
};

const joinUrl = (path: string) => {
  const base = getAuthBaseUrl().replace(/\/$/, '');
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${base}${p}`;
};

// 定义与后端UserResponse模型一致的接口
export interface UserInfo {
  id: number;
  username: string;
  email: string;
  nickname?: string;
  avatar_url?: string;
  role: string;
  status: string;
  email_verified: boolean;
  phone_verified: boolean;
  created_at: string; // 日期时间在JSON中会转换为字符串
}

// 定义与后端LoginResponse模型一致的接口
export interface LoginResponse {
  success: boolean;
  token: string;
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: UserInfo;
  isPaid: boolean;
}

// 定义与后端UserResponse模型一致的接口（用于注册响应）
export interface UserResponse extends UserInfo {}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  nickname: string;
  username?: string;
  phone?: string;
}

export interface RegisterResponse {
  success: boolean;
  user: UserResponse;
}

export const login = async (payload: LoginPayload): Promise<LoginResponse> => {
  // 转换前端字段名到后端期望的字段名
  const requestBody = {
    username_or_email: payload.email,
    password: payload.password
  };
  const resp = await fetch(joinUrl('/api/auth/login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody),
  });
  if (!resp.ok) {
    const txt = await resp.text().catch(() => '登录失败');
    throw new Error(txt || '登录失败');
  }
  return resp.json();
};

export const register = async (payload: RegisterPayload): Promise<RegisterResponse> => {
  const body: RegisterPayload = { ...payload };
  if (!body.username) {
    const fallback = body.nickname?.trim() || body.email.split('@')[0];
    body.username = fallback.replace(/[^A-Za-z0-9_-]/g, '').slice(0, 50) || `user_${Date.now()}`;
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

export const uploadPayment = async (file: File) => {
  const form = new FormData();
  form.append('file', file);
  const authHeaders = await authService.getAuthHeaders();
  const resp = await fetch(joinUrl('/api/payment/upload'), {
    method: 'POST',
    headers: authHeaders,
    body: form,
  });
  if (!resp.ok) {
    const txt = await resp.text().catch(() => '上传失败');
    throw new Error(txt || '上传失败');
  }
  return resp.json();
};

export const pollPayment = async () => {
  const authHeaders = await authService.getAuthHeaders();
  const headers = { 
    'Content-Type': 'application/json',
    ...authHeaders
  };
  const resp = await fetch(joinUrl('/api/payment/poll'), {
    method: 'GET',
    headers,
  });
  if (!resp.ok) {
    const txt = await resp.text().catch(() => '查询支付状态失败');
    throw new Error(txt || '查询支付状态失败');
  }
  return resp.json();
};