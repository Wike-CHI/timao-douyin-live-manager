import { mockLogin, mockPaymentPoll, mockPaymentUpload, mockRegister, mockGetWallet, mockRecharge, mockConsume, mockUseFirstFree } from './mockAuth';
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

export const login = async (payload: LoginPayload) => {
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

export const register = async (payload: RegisterPayload) => {
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

// 钱包相关 API
export const getWallet = async () => {
  if (isMock) return mockGetWallet();
  const { token } = useAuthStore.getState();
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const resp = await fetch(joinUrl('/api/wallet/balance'), { method: 'GET', headers });
  if (!resp.ok) {
    const txt = await resp.text().catch(() => '查询钱包失败');
    throw new Error(txt || '查询钱包失败');
  }
  return resp.json();
};

export const recharge = async (amount: number) => {
  if (isMock) return mockRecharge(amount);
  const { token } = useAuthStore.getState();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  const resp = await fetch(joinUrl('/api/wallet/recharge'), {
    method: 'POST',
    headers,
    body: JSON.stringify({ amount }),
  });
  if (!resp.ok) {
    const txt = await resp.text().catch(() => '充值失败');
    throw new Error(txt || '充值失败');
  }
  return resp.json();
};

export const consume = async (amount: number, reason?: string) => {
  if (isMock) return mockConsume(amount);
  const { token } = useAuthStore.getState();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  const resp = await fetch(joinUrl('/api/wallet/consume'), {
    method: 'POST',
    headers,
    body: JSON.stringify({ amount, reason }),
  });
  if (!resp.ok) {
    const txt = await resp.text().catch(() => '扣费失败');
    throw new Error(txt || '扣费失败');
  }
  return resp.json();
};

export const useFirstFree = async () => {
  if (isMock) return mockUseFirstFree();
  const { token } = useAuthStore.getState();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  const resp = await fetch(joinUrl('/api/wallet/useFree'), {
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
