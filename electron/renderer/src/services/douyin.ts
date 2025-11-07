import useAuthStore from '../store/useAuthStore';
import authService from './authService';
import { buildServiceUrl } from './apiConfig';
import { apiCall } from '../utils/error-handler';

const buildDouyinUrl = (path: string, baseUrl?: string) =>
  buildServiceUrl('douyin', path, baseUrl);

const buildHeaders = async () => {
  const authHeaders = await authService.getAuthHeaders();
  return {
    'Content-Type': 'application/json',
    ...authHeaders,
  };
};


export interface DouyinRelayStatus {
  is_running: boolean;
  live_id: string | null;
  room_id: string | null;
  last_error: string | null;
  persist_enabled?: boolean;
  persist_root?: string | null;
  fetcher_status?: Record<string, any>;  // 修复 DY-003: 添加抓取器详细状态
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
  cookie?: string,  // 修复 DY-001: 添加 Cookie 参数
  baseUrl?: string
): Promise<DouyinRelayResponse> => {
  const headers = await buildHeaders();
  const body: any = { live_id: liveId };
  
  // 修复 DY-001: 支持可选的 Cookie
  if (cookie) {
    body.cookie = cookie;
  }

  return apiCall(
    () => fetch(buildDouyinUrl('/api/douyin/start', baseUrl), {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    }),
    '启动抖音中继'
  );
};

export const stopDouyinRelay = async (
  baseUrl?: string
): Promise<DouyinRelayResponse> => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(buildDouyinUrl('/api/douyin/stop', baseUrl), {
      method: 'POST',
      headers,
    }),
    '停止抖音中继'
  );
};

export const getDouyinRelayStatus = async (
  baseUrl?: string
): Promise<DouyinRelayStatus> => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(buildDouyinUrl('/api/douyin/status', baseUrl), {
      method: 'GET',
      headers,
    }),
    '获取抖音中继状态'
  );
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
  const streamUrl = buildDouyinUrl('/api/douyin/stream', baseUrl);
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
  return apiCall(
    () => fetch(buildDouyinUrl('/api/douyin/web/persist', baseUrl), {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    }),
    '更新抖音持久化配置'
  );
};
