import { mockLogin, mockPaymentPoll, mockPaymentUpload, mockRegister, mockGetWallet, mockRecharge, mockConsume, mockUseFirstFree } from './mockAuth';
import useAuthStore from '../store/useAuthStore';
import { getCloudBaseAuth } from './cloudbase';

const AUTH_BASE_URL = (import.meta.env?.VITE_AUTH_BASE_URL as string | undefined)?.trim();
const rawEnvId = (import.meta.env?.VITE_CLOUDBASE_ENV_ID as string | undefined)?.trim();
const DEFAULT_ENV_ID = 'cloud-2gw460e590303de0';
const CLOUDBASE_ENV_ID = rawEnvId || DEFAULT_ENV_ID;
const enableCloudBaseFlag = ((import.meta.env?.VITE_ENABLE_CLOUDBASE as string | undefined) || 'true')
  .toLowerCase()
  .trim() !== 'false';
const enableCloudBase = !AUTH_BASE_URL && enableCloudBaseFlag;
const cloudbaseAuth = enableCloudBase ? (getCloudBaseAuth(CLOUDBASE_ENV_ID) as any) : null;
const isMock = !AUTH_BASE_URL && !enableCloudBase;

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
  if (cloudbaseAuth) {
    try {
      const credential = await cloudbaseAuth.signInWithEmailAndPassword(payload.email, payload.password);
      const tokenInfo = await cloudbaseAuth.getAccessToken();
      const token = typeof tokenInfo === 'string' ? tokenInfo : tokenInfo?.accessToken;
      const user = cloudbaseAuth.currentUser;
      return {
        success: true,
        token: token || '',
        user: {
          id: user?.uid || credential?.user?.uid || 'cloud-user',
          email: user?.email || credential?.user?.email || payload.email,
          nickname: user?.nickName || credential?.user?.nickName || payload.email.split('@')[0],
        },
        isPaid: false,
        balance: 0,
        firstFreeUsed: false,
      };
    } catch (error) {
      const message = (error as Error)?.message || '云开发登录失败';
      throw new Error(message.includes('INVALID_EMAIL') ? '邮箱格式不正确' : message);
    }
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
  if (cloudbaseAuth) {
    try {
      await cloudbaseAuth.signUpWithEmailAndPassword(payload.email, payload.password);
      const credential = await cloudbaseAuth.signInWithEmailAndPassword(payload.email, payload.password);
      if (payload.nickname) {
        try {
          await cloudbaseAuth.currentUser?.update({ nickName: payload.nickname });
        } catch {}
      }
      return {
        success: true,
        user: {
          id: credential?.user?.uid || cloudbaseAuth.currentUser?.uid || 'cloud-user',
          email: payload.email,
          nickname: payload.nickname,
        },
      };
    } catch (error) {
      const message = (error as Error)?.message || '云开发注册失败';
      throw new Error(message.includes('EMAIL_EXISTS') ? '该邮箱已注册' : message);
    }
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
  if (cloudbaseAuth) throw new Error('当前模式暂未开通支付能力');
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
  if (cloudbaseAuth) throw new Error('当前模式暂未开通支付能力');
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

export const cloudbaseSignOut = async () => {
  if (cloudbaseAuth) {
    try {
      await cloudbaseAuth.signOut();
    } catch {}
  }
};
