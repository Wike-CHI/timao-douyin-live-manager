import authService from './authService';
import { buildServiceUrl } from './apiConfig';
import { fetchJsonWithAuth } from './http';
import { apiCall } from '../utils/error-handler';
import type {
  UserInfo,
  LoginResponse,
  UserResponse,
  LoginRequest,
  RegisterRequest,
  RegisterResponse,
  PaymentUploadResponse,
  PaymentPollResponse,
} from '../types/api-types';

// 重新导出类型，供其他模块使用
export type { 
  LoginResponse, 
  RegisterResponse, 
  UserInfo, 
  UserResponse,
  LoginRequest,
  RegisterRequest
};

const getAuthBaseUrl = () => import.meta.env?.VITE_AUTH_BASE_URL?.trim() || undefined;

const buildAuthUrl = (path: string) =>
  buildServiceUrl('main', path, getAuthBaseUrl());

export const login = async (payload: LoginRequest): Promise<LoginResponse> => {
  // 转换前端字段名到后端期望的字段名
  const requestBody = {
    username_or_email: payload.email,
    password: payload.password,
    remember_me: payload.remember_me !== undefined ? payload.remember_me : true
  };
  
  return apiCall<LoginResponse>(
    () => fetch(buildAuthUrl('/api/auth/login'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    }),
    '登录'
  );
};

export const register = async (payload: RegisterRequest): Promise<RegisterResponse> => {
  // 导入验证器（修复 AUTH-004）
  const { UserValidator } = await import('../utils/validators');
  
  const body: RegisterRequest = { ...payload };
  
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
  
  return apiCall<RegisterResponse>(
    () => fetch(buildAuthUrl('/api/auth/register'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    }),
    '注册'
  );
};

export const uploadPayment = async (file: File): Promise<PaymentUploadResponse> => {
  const form = new FormData();
  form.append('file', file);
  const authHeaders = await authService.getAuthHeaders();
  return apiCall<PaymentUploadResponse>(
    () => fetch(buildAuthUrl('/api/payment/upload'), {
    method: 'POST',
    headers: authHeaders,
    body: form,
    }),
    '上传支付凭证'
  );
};

export const pollPayment = async (): Promise<PaymentPollResponse> => {
  return apiCall<PaymentPollResponse>(
    () => fetchJsonWithAuth('main', '/api/payment/poll', {
    method: 'GET',
    }, getAuthBaseUrl()),
    '查询支付状态'
  );
};