import { mockLogin, mockPaymentPoll, mockPaymentUpload, mockRegister } from './mockAuth';

const AUTH_BASE_URL = (import.meta.env?.VITE_AUTH_BASE_URL as string | undefined)?.trim();
const isMock = !AUTH_BASE_URL; // 未配置云端地址时使用本地模拟

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
}

export const login = async (payload: LoginPayload) => {
  if (isMock) return mockLogin(payload);
  const resp = await fetch(joinUrl('/api/auth/login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    const txt = await resp.text().catch(() => '登录失败');
    throw new Error(txt || '登录失败');
  }
  return resp.json();
};

export const register = async (payload: RegisterPayload) => {
  if (isMock) return mockRegister(payload);
  const resp = await fetch(joinUrl('/api/auth/register'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
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
  const resp = await fetch(joinUrl('/api/payment/upload'), {
    method: 'POST',
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
  const resp = await fetch(joinUrl('/api/payment/status'), { method: 'GET' });
  if (!resp.ok) {
    const txt = await resp.text().catch(() => '查询失败');
    throw new Error(txt || '查询失败');
  }
  return resp.json();
};

