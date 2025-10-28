import useAuthStore from '../store/useAuthStore';
import authService from './authService';

// Align with FastAPI default port 9019 used by Electron main
const DEFAULT_BASE_URL = (import.meta.env?.VITE_FASTAPI_URL as string | undefined) || 'http://127.0.0.1:9019';

const resolveBaseUrl = (baseUrl?: string) => {
  const value = baseUrl && baseUrl.trim() ? baseUrl : DEFAULT_BASE_URL;
  return value;
};

const joinUrl = (baseUrl: string | undefined, path: string) => {
  const normalizedBase = resolveBaseUrl(baseUrl).replace(/\/$/, '');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
};

const buildHeaders = async () => {
  const authHeaders = await authService.getAuthHeaders();
  return {
    'Content-Type': 'application/json',
    ...authHeaders,
  };
};

const handleResponse = async <T>(response: Response): Promise<T> => {
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = (data as { detail?: string } | null)?.detail || response.statusText || '请求失败';
    throw new Error(detail);
  }
  return data as T;
};

export interface DouyinRelayStatus {
  is_running: boolean;
  live_id: string | null;
  room_id: string | null;
  last_error: string | null;
  persist_enabled?: boolean;
  persist_root?: string | null;
}

export interface DouyinRelayResponse {
  success: boolean;
  message?: string;
  live_id?: string;
}

export interface DouyinStreamEvent {
  type: string;
  payload?: Record<string, unknown> | null;
  timestamp?: number;
}

export const startDouyinRelay = async (
  liveId: string,
  baseUrl?: string
): Promise<DouyinRelayResponse> => {
  const headers = await buildHeaders();
  const response = await fetch(joinUrl(baseUrl, '/api/douyin/web/start'), {
    method: 'POST',
    headers,
    body: JSON.stringify({ live_id: liveId }),
  });
  return handleResponse<DouyinRelayResponse>(response);
};

export const stopDouyinRelay = async (
  baseUrl?: string
): Promise<DouyinRelayResponse> => {
  const headers = await buildHeaders();
  const response = await fetch(joinUrl(baseUrl, '/api/douyin/web/stop'), {
    method: 'POST',
    headers,
  });
  return handleResponse<DouyinRelayResponse>(response);
};

export const getDouyinRelayStatus = async (
  baseUrl?: string
): Promise<DouyinRelayStatus> => {
  const headers = await buildHeaders();
  const response = await fetch(joinUrl(baseUrl, '/api/douyin/web/status'), {
    method: 'GET',
    headers,
  });
  return handleResponse<DouyinRelayStatus>(response);
};

export interface DouyinStreamHandlers {
  onEvent?: (event: DouyinStreamEvent) => void;
  onError?: (event: Event) => void;
  onOpen?: (event: Event) => void;
}

export const openDouyinStream = (
  handlers: DouyinStreamHandlers,
  baseUrl?: string
): EventSource => {
  const streamUrl = joinUrl(baseUrl, '/api/douyin/web/stream');
  const source = new EventSource(streamUrl);

  if (handlers.onOpen) {
    source.onopen = handlers.onOpen;
  }
  if (handlers.onError) {
    source.onerror = handlers.onError;
  }
  source.onmessage = (event) => {
    if (!handlers.onEvent) {
      return;
    }
    try {
      const data = JSON.parse(event.data) as DouyinStreamEvent;
      handlers.onEvent(data);
    } catch (error) {
      console.error('解析 Douyin SSE 消息失败:', error);
    }
  };

  return source;
};

export const updateDouyinPersist = async (
  payload: { persist_enabled?: boolean; persist_root?: string },
  baseUrl?: string
) => {
  const headers = await buildHeaders();
  const response = await fetch(joinUrl(baseUrl, '/api/douyin/web/persist'), {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
};
