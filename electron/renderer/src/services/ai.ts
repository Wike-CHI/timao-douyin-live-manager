import authService from './authService';
import { buildServiceUrl } from './apiConfig';
import { fetchJsonWithAuth } from './http';
import { apiCall } from '../utils/error-handler';
import type {
  StartAILiveAnalysisRequest,
  GenerateOneScriptRequest,
  GenerateOneScriptResponse,
  GenerateAnswerScriptsRequest,
  GenerateAnswerScriptsResponse,
} from '../types/api-types';

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

// ========== AI 实时分析接口 ==========

/**
 * 启动 AI 实时分析
 */
export const startAILiveAnalysis = async (
  payload: StartAILiveAnalysisRequest = {}
) => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/ai/live/start', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
    '启动 AI 实时分析'
  );
};

/**
 * 停止 AI 实时分析
 */
export const stopAILiveAnalysis = async () => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/ai/live/stop', {
      method: 'POST',
    }),
    '停止 AI 实时分析'
  );
};

/**
 * 打开 AI 实时分析 SSE 流（带鉴权）
 */
export const openAILiveStream = async (
  onMessage: (event: MessageEvent) => void,
  onError?: (event: Event) => void
): Promise<EventSource> => {
  // EventSource 不支持自定义 headers，需要通过 URL 参数传递 token
  const url = await buildAuthUrl(buildServiceUrl('main', '/api/ai/live/stream'));
  const eventSource = new EventSource(url);
  
  eventSource.onmessage = onMessage;
  
  if (onError) {
    eventSource.onerror = onError;
  }
  
  return eventSource;
};

// ========== AI 话术生成接口 ==========

/**
 * 生成单条话术
 */
export const generateOneScript = async (
  payload: GenerateOneScriptRequest
): Promise<GenerateOneScriptResponse> => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/ai/scripts/generate_one', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
    '生成单条话术'
  );
};

export const generateAnswerScripts = async (
  payload: GenerateAnswerScriptsRequest
): Promise<GenerateAnswerScriptsResponse> => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/ai/live/answers', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
    '生成回答话术'
  );
};
