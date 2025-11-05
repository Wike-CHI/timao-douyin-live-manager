import useAuthStore from '../store/useAuthStore';
import authService from './authService';

const DEFAULT_BASE_URL = import.meta.env?.VITE_FASTAPI_URL as string || 'http://127.0.0.1:9030'; // 默认端口改为 9030，避免 Windows 端口排除范围 8930-9029

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
    const detail = (data as any)?.detail || response.statusText || '请求失败';
    throw new Error(detail);
  }
  return data as T;
};

export interface LiveSessionState {
  session_id: string;
  live_url: string;
  live_id: string | null;
  room_id: string | null;
  anchor_name: string | null;
  platform_key: string;
  session_date: string;
  started_at: number;
  last_updated_at: number;
  status: 'recording' | 'paused' | 'stopped' | 'error';
  recording_active: boolean;
  audio_transcription_active: boolean;
  ai_analysis_active: boolean;
  douyin_relay_active: boolean;
  recording_session_id: string | null;
  audio_session_id: string | null;
  ai_session_id: string | null;
  douyin_session_id: string | null;
  last_error: string | null;
  metadata?: Record<string, any>;
}

export interface SessionStatusResponse {
  success: boolean;
  message: string;
  data?: {
    session: LiveSessionState | null;
  };
}

/**
 * 获取当前会话状态
 */
export const getSessionStatus = async (baseUrl: string = DEFAULT_BASE_URL): Promise<SessionStatusResponse> => {
  const headers = await buildHeaders();
  const response = await fetch(`${baseUrl}/api/live_session/status`, {
    method: 'GET',
    headers,
  });
  return handleResponse<SessionStatusResponse>(response);
};

/**
 * 恢复之前的会话
 */
export const resumeSession = async (baseUrl: string = DEFAULT_BASE_URL): Promise<SessionStatusResponse> => {
  const headers = await buildHeaders();
  const response = await fetch(`${baseUrl}/api/live_session/resume`, {
    method: 'POST',
    headers,
  });
  return handleResponse<SessionStatusResponse>(response);
};

/**
 * 暂停当前会话
 */
export const pauseSession = async (baseUrl: string = DEFAULT_BASE_URL): Promise<SessionStatusResponse> => {
  const headers = await buildHeaders();
  const response = await fetch(`${baseUrl}/api/live_session/pause`, {
    method: 'POST',
    headers,
  });
  return handleResponse<SessionStatusResponse>(response);
};

/**
 * 恢复暂停的会话
 */
export const resumePausedSession = async (baseUrl: string = DEFAULT_BASE_URL): Promise<SessionStatusResponse> => {
  const headers = await buildHeaders();
  const response = await fetch(`${baseUrl}/api/live_session/resume_paused`, {
    method: 'POST',
    headers,
  });
  return handleResponse<SessionStatusResponse>(response);
};

/**
 * 恢复暂停的会话（别名，保持API一致性）
 */
export const resumePaused = resumePausedSession;

