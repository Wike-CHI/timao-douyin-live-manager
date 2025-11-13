import authService from './authService';
import { buildServiceUrl } from './apiConfig';
import type { ApiConfig } from './apiConfig';
import { requestManager } from './requestManager';

export const buildJsonAuthHeaders = async (
  extra?: Record<string, string>
): Promise<Record<string, string>> => {
  const authHeaders = await authService.getAuthHeaders();
  return {
    'Content-Type': 'application/json',
    ...authHeaders,
    ...(extra || {}),
  };
};

export const fetchJsonWithAuth = async (
  service: keyof ApiConfig['services'],
  path: string,
  options: RequestInit = {},
  overrideBaseUrl?: string
) => {
  const headers = await buildJsonAuthHeaders(options.headers as Record<string, string> | undefined);
  
  // 创建一个被追踪的 AbortController
  // 如果用户已经提供了 signal,则合并两个信号
  const controller = requestManager.createAbortController();
  
  // 如果用户提供了自己的 signal,当任一信号被 abort 时都要取消请求
  if (options.signal) {
    const userSignal = options.signal;
    userSignal.addEventListener('abort', () => {
      controller.abort();
    });
  }
  
  return fetch(buildServiceUrl(service, path, overrideBaseUrl), {
    ...options,
    headers,
    signal: controller.signal,
  });
};

