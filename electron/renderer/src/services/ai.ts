import useAuthStore from '../store/useAuthStore';

const DEFAULT_BASE_URL = (import.meta.env?.VITE_FASTAPI_URL as string | undefined) || 'http://127.0.0.1:8007';

/**
 * 构建包含鉴权信息的请求头
 */
const buildHeaders = (): Record<string, string> => {
  const { token } = useAuthStore.getState();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
};

/**
 * 构建包含 token 的 URL（用于 EventSource，因为它不支持自定义 headers）
 */
const buildAuthUrl = (url: string): string => {
  const { token } = useAuthStore.getState();
  if (!token) return url;
  
  const urlObj = new URL(url);
  urlObj.searchParams.set('token', token);
  return urlObj.toString();
};

/**
 * 统一的 fetch 包装函数，自动添加鉴权头
 */
const authFetch = async (url: string, options?: RequestInit): Promise<Response> => {
  const headers = {
    ...buildHeaders(),
    ...(options?.headers || {}),
  };
  
  return fetch(url, {
    ...options,
    headers,
  });
};

/**
 * 处理响应
 */
const handleResponse = async <T>(response: Response): Promise<T> => {
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = (data as any)?.detail || response.statusText || '请求失败';
    throw new Error(detail);
  }
  return data as T;
};

// ========== AI 实时分析接口 ==========

export interface StartAILiveAnalysisPayload {
  window_sec?: number;
}

/**
 * 启动 AI 实时分析
 */
export const startAILiveAnalysis = async (
  payload: StartAILiveAnalysisPayload = {},
  baseUrl: string = DEFAULT_BASE_URL
) => {
  const response = await authFetch(`${baseUrl}/api/ai/live/start`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
};

/**
 * 停止 AI 实时分析
 */
export const stopAILiveAnalysis = async (baseUrl: string = DEFAULT_BASE_URL) => {
  const response = await authFetch(`${baseUrl}/api/ai/live/stop`, {
    method: 'POST',
  });
  return handleResponse(response);
};

/**
 * 打开 AI 实时分析 SSE 流（带鉴权）
 */
export const openAILiveStream = (
  onMessage: (event: MessageEvent) => void,
  onError?: (event: Event) => void,
  baseUrl: string = DEFAULT_BASE_URL
): EventSource => {
  // EventSource 不支持自定义 headers，需要通过 URL 参数传递 token
  const url = buildAuthUrl(`${baseUrl}/api/ai/live/stream`);
  const eventSource = new EventSource(url);
  
  eventSource.onmessage = onMessage;
  
  if (onError) {
    eventSource.onerror = onError;
  }
  
  return eventSource;
};

// ========== AI 话术生成接口 ==========

export interface GenerateOneScriptPayload {
  script_type: string;
  include_context?: boolean;
}

export interface GenerateOneScriptResponse {
  success: boolean;
  data?: {
    content: string;
    type: string;
    timestamp: number;
  };
  message?: string;
}

/**
 * 生成单条话术
 */
export const generateOneScript = async (
  payload: GenerateOneScriptPayload,
  baseUrl: string = DEFAULT_BASE_URL
): Promise<GenerateOneScriptResponse> => {
  const response = await authFetch(`${baseUrl}/api/ai/scripts/generate_one`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
};

/**
 * 导出统一的 fetch 函数供其他模块使用
 */
export { authFetch, buildHeaders, buildAuthUrl };

