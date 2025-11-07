import authService from './authService';
import { buildServiceUrl } from './apiConfig';
import type { ApiConfig } from './apiConfig';

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
  return fetch(buildServiceUrl(service, path, overrideBaseUrl), {
    ...options,
    headers,
  });
};

