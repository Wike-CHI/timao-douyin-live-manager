import useAuthStore from '../store/useAuthStore';
import authService from './authService';
import { apiConfig, buildApiUrl, requestWithRetry } from './apiConfig';
import { AIUsage } from '../types/api-types';
import { apiCall } from '../utils/error-handler';

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

/**
 * 用户信息（修复 PAY-004）
 * 对应后端: UserResponse (server/app/api/auth.py:76-90)
 * 
 * 注意: created_at 是 ISO 8601 格式的日期时间字符串
 * 示例: "2025-11-02T15:30:00Z"
 */
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
  created_at: string;  // ISO 8601 日期时间字符串
}

// 定义与后端LoginResponse模型一致的接口（修复 AUTH-001, AUTH-002）
export interface LoginResponse {
  success: boolean;
  token: string;
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: UserInfo;
  isPaid: boolean;
  /** 是否已使用首次免费额度 */
  firstFreeUsed?: boolean;
  /** AI 使用统计信息 */
  aiUsage?: AIUsage;
}

// 定义与后端UserResponse模型一致的接口（用于注册响应）
export interface UserResponse extends UserInfo {}

export interface LoginPayload {
  email: string;
  password: string;
  remember_me?: boolean;  // 是否记住登录状态
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
    password: payload.password,
    remember_me: payload.remember_me !== undefined ? payload.remember_me : true  // 默认记住
  };
  
  // 使用统一的错误处理
  return apiCall<LoginResponse>(
    () => fetch(joinUrl('/api/auth/login'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    }),
    '登录'
  );
};

export const register = async (payload: RegisterPayload): Promise<RegisterResponse> => {
  // 导入验证器（修复 AUTH-004）
  const { UserValidator } = await import('../utils/validators');
  
  const body: RegisterPayload = { ...payload };
  
  // 生成或验证用户名
  if (!body.username) {
    body.username = UserValidator.generateUsername(body.nickname || '', body.email);
  } else {
    // 验证用户提供的用户名
    const validation = UserValidator.validateUsername(body.username);
    if (!validation.valid) {
      throw new Error(validation.message);
    }
  }
  
  // 验证密码
  const passwordValidation = UserValidator.validatePassword(body.password);
  if (!passwordValidation.valid) {
    throw new Error(passwordValidation.message);
  }
  
  // 验证邮箱
  const emailValidation = UserValidator.validateEmail(body.email);
  if (!emailValidation.valid) {
    throw new Error(emailValidation.message);
  }
  
  // 验证手机号（如果提供）
  if (body.phone) {
    const phoneValidation = UserValidator.validatePhone(body.phone);
    if (!phoneValidation.valid) {
      throw new Error(phoneValidation.message);
    }
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