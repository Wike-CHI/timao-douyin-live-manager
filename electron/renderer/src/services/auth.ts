import { mockLogin, mockPaymentPoll, mockPaymentUpload, mockRegister, mockGetWallet, mockRecharge, mockConsume, mockUseFirstFree } from './mockAuth';
import type { LoginPayload, RegisterPayload } from './mockAuth';
import useAuthStore from '../store/useAuthStore';
import { getCloudBaseAuth, getCloudBaseApp } from './cloudbase';

 const AUTH_BASE_URL = (import.meta.env?.VITE_AUTH_BASE_URL as string | undefined)?.trim();
 const rawEnvId = (import.meta.env?.VITE_CLOUDBASE_ENV_ID as string | undefined)?.trim();
 const DEFAULT_ENV_ID = 'cloud-2gw460e590303de0';
 const CLOUDBASE_ENV_ID = rawEnvId || DEFAULT_ENV_ID;
 const enableCloudBaseFlag = ((import.meta.env?.VITE_ENABLE_CLOUDBASE as string | undefined) || 'true')
   .toLowerCase()
   .trim() !== 'false';
 const enableCloudBase = !AUTH_BASE_URL && enableCloudBaseFlag;
const cloudbaseAuth = enableCloudBase ? (getCloudBaseAuth(CLOUDBASE_ENV_ID) as any) : null;
const cloudbaseApp = enableCloudBase ? getCloudBaseApp(CLOUDBASE_ENV_ID) : null;
 const isMock = !AUTH_BASE_URL && !enableCloudBase;

 const joinUrl = (path: string) => {
   if (!AUTH_BASE_URL) return path; // mock 模式下不使用
   const base = AUTH_BASE_URL.replace(/\/$/, '');
   const p = path.startsWith('/') ? path : `/${path}`;
   return `${base}${p}`;
 };

const callCF = async (name: string, action: string, data?: any) => {
  if (!cloudbaseApp) throw new Error('CloudBase 未初始化');
  const resp = await cloudbaseApp.callFunction({ name, data: { action, data } });
  return resp?.result;
};

const fileToBase64 = (file: File) =>
  new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const res = reader.result as string;
      const base64 = res.includes(',') ? res.split(',')[1] : res;
      resolve(base64);
    };
    reader.onerror = (err) => reject(err);
    reader.readAsDataURL(file);
  });
 export const login = async (payload: LoginPayload) => {
  if (enableCloudBase) {
    const result = await callCF('auth', 'login', payload);
    if (!result || result.code !== 0) {
      throw new Error(result?.msg || '登录失败');
    }
    const { token, user } = result.data || {};
    return {
      success: true,
      token: token || '',
      user: {
        id: user?._id || user?.uid || 'cloud-user',
        email: user?.email || payload.email,
        nickname: user?.nickName || user?.nickname || payload.email.split('@')[0],
      },
      isPaid: false,
      balance: 0,
      firstFreeUsed: false,
    };
  }
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
  if (enableCloudBase) {
    const result = await callCF('auth', 'register', { email: payload.email, password: payload.password, nickName: payload.nickname });
    if (!result || result.code !== 0) {
      throw new Error(result?.msg || '注册失败');
    }
    return {
      success: true,
      user: {
        id: result.data?.uid || 'cloud-user',
        email: payload.email,
        nickname: payload.nickname,
      },
    };
  }
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
  if (enableCloudBase) {
    const { token } = useAuthStore.getState();
    if (!token) throw new Error('未登录，无法提交审核');
    const plansResult = await callCF('payment', 'getPlans');
    const planId = plansResult?.data?.plans?.[0]?.planId || 'basic';
    const createRes = await callCF('payment', 'createOrder', { token, planId });
    if (!createRes || createRes.code !== 0) throw new Error(createRes?.msg || '创建订单失败');
    const orderId = createRes.data?.orderId;
    const base64 = await fileToBase64(file);
    const upRes = await callCF('payment', 'uploadVoucher', { token, orderId, voucherBase64: base64 });
    if (!upRes || upRes.code !== 0) throw new Error(upRes?.msg || '上传失败');
    return { success: true, message: upRes.msg || '上传成功' };
  }
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
  if (enableCloudBase) {
    const { token } = useAuthStore.getState();
    if (!token) return { success: false, message: '未登录' };
    const res = await callCF('payment', 'getOrderStatus', { token });
    if (!res || res.code !== 0) return { success: false, message: res?.msg || '查询失败' };
    const status = (res.data?.status || 'pending').toLowerCase();
    return { success: true, status } as any;
  }
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
 export const cloudbaseSignOut = async () => {
  if (enableCloudBase) {
    const { token } = useAuthStore.getState();
    try {
      await callCF('auth', 'logout', { token });
    } catch {}
  }
 };

// 钱包相关 API
export const getWallet = async () => {
  if (cloudbaseAuth) {
    return { success: true, balance: 0, firstFreeUsed: false };
  }
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
  if (cloudbaseAuth) throw new Error('云开发模式下暂未开放充值');
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
  if (cloudbaseAuth) throw new Error('云开发模式下暂未开放扣费');
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
  if (cloudbaseAuth) return { success: false, message: '云开发模式下请直接使用体验功能' };
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
