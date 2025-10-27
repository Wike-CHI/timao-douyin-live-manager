import { mockLogin, mockPaymentPoll, mockPaymentUpload, mockRegister, mockUseFirstFree } from './mockAuth';
import useAuthStore from '../store/useAuthStore';

const RAW_AUTH_BASE_URL = (import.meta.env?.VITE_AUTH_BASE_URL as string | undefined)?.trim();
const FASTAPI_BASE_URL = (import.meta.env?.VITE_FASTAPI_URL as string | undefined)?.trim();
const AUTH_BASE_URL = (RAW_AUTH_BASE_URL || FASTAPI_BASE_URL || '').replace(/\s+$/, '');
const isMock = !AUTH_BASE_URL; // 未配置真实后端地址时使用本地模拟

const joinUrl = (path: string) => {
  if (!AUTH_BASE_URL) return path; // mock 模式下不使用
  const base = AUTH_BASE_URL.replace(/\/$/, '');
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
  token_type: string;
  expires_in: number;
  user: UserInfo;
  isPaid: boolean;
  firstFreeUsed: boolean;
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
  if (isMock) return mockLogin(payload);
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
  if (isMock) return mockRegister(payload);
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
  if (isMock) return mockPaymentUpload(file);
  const form = new FormData();
  form.append('file', file);
  const { token } = useAuthStore.getState();
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const resp = await fetch(joinUrl('/api/payment/upload'), {
    method: 'POST',
    headers,
    body: form,
  });
  if (!resp.ok) {
    const txt = await resp.text().catch(() => '上传失败');
    throw new Error(txt || '上传失败');
  }
  return resp.json();
};

export const pollPayment = async () => {
  if (isMock) return mockPaymentPoll();
  const { token } = useAuthStore.getState();
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const resp = await fetch(joinUrl('/api/payment/status'), { method: 'GET', headers });
  if (!resp.ok) {
    const txt = await resp.text().catch(() => '查询失败');
    throw new Error(txt || '查询失败');
  }
  return resp.json();
};

export const useFirstFree = async () => {
  if (isMock) return mockUseFirstFree();
  const { token } = useAuthStore.getState();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  const resp = await fetch(joinUrl('/api/auth/useFree'), {
    method: 'POST',
    headers,
    body: JSON.stringify({}),
  });
  if (!resp.ok) {
    const txt = await resp.text().catch(() => '首次免费失败');
    throw new Error(txt || '首次免费失败');
  }
  return resp.json();
};