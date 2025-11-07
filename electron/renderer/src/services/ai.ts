import useAuthStore from '../store/useAuthStore';
import authService from './authService';
import { buildServiceUrl } from './apiConfig';
import { buildJsonAuthHeaders } from './http';
import { apiCall } from '../utils/error-handler';

const DEFAULT_BASE_URL = import.meta.env?.VITE_FASTAPI_URL as string || 'http://127.0.0.1:9030'; // 默认端口改为 9030，避免 Windows 端口排除范围 8930-9029

/**
 * 构建包含鉴权信息的请求头
 */
const buildHeaders = buildJsonAuthHeaders;

/**
 * 构建包含 token 的 URL（用于 EventSource，因为它不支持自定义 headers）
 */
const buildAuthUrl = async (url: string): Promise<string> => {
  const token = await authService.ensureValidToken();
  if (!token) return url;
  
  const urlObj = new URL(url);
  urlObj.searchParams.set('token', token);
  return urlObj.toString();
};

/**
 * 统一的 fetch 包装函数，自动添加鉴权头
 */
const authFetch = async (path: string, options?: RequestInit, baseUrl?: string): Promise<Response> => {
  const headers = await buildJsonAuthHeaders(options?.headers as Record<string, string> | undefined);
  const url = buildServiceUrl('main', path, baseUrl ?? DEFAULT_BASE_URL);

  return fetch(url, {
    ...options,
    headers,
  });
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
  baseUrl?: string
) => {
  return apiCall(
    () => authFetch('/api/ai/live/start', {
      method: 'POST',
      body: JSON.stringify(payload),
    }, baseUrl ?? DEFAULT_BASE_URL),
    '启动 AI 实时分析'
  );
};

/**
 * 停止 AI 实时分析
 */
export const stopAILiveAnalysis = async (baseUrl?: string) => {
  return apiCall(
    () => authFetch('/api/ai/live/stop', {
      method: 'POST',
    }, baseUrl ?? DEFAULT_BASE_URL),
    '停止 AI 实时分析'
  );
};

/**
 * 打开 AI 实时分析 SSE 流（带鉴权）
 */
export const openAILiveStream = async (
  onMessage: (event: MessageEvent) => void,
  onError?: (event: Event) => void,
  baseUrl?: string
): Promise<EventSource> => {
  // EventSource 不支持自定义 headers，需要通过 URL 参数传递 token
  const url = await buildAuthUrl(buildServiceUrl('main', '/api/ai/live/stream', baseUrl ?? DEFAULT_BASE_URL));
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
  baseUrl?: string
): Promise<GenerateOneScriptResponse> => {
  return apiCall(
    () => authFetch('/api/ai/scripts/generate_one', {
      method: 'POST',
      body: JSON.stringify(payload),
    }, baseUrl ?? DEFAULT_BASE_URL),
    '生成单条话术'
  );
};

export interface GenerateAnswerScriptsPayload {
  questions: string[];
  transcript?: string;
  style_profile?: Record<string, unknown>;
  vibe?: Record<string, unknown>;
}

export interface GenerateAnswerScriptsResponse {
  success: boolean;
  data?: {
    scripts: Array<{ question: string; line: string; notes?: string }>;
  };
  message?: string;
}

export const generateAnswerScripts = async (
  payload: GenerateAnswerScriptsPayload,
  baseUrl?: string
): Promise<GenerateAnswerScriptsResponse> => {
  return apiCall(
    () => authFetch('/api/ai/live/answers', {
      method: 'POST',
      body: JSON.stringify(payload),
    }, baseUrl ?? DEFAULT_BASE_URL),
    '生成回答话术'
  );
};

/**
 * 导出统一的 fetch 函数供其他模块使用
 */
export { authFetch, buildHeaders, buildAuthUrl };
