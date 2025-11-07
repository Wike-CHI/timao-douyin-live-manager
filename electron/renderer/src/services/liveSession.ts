import { fetchJsonWithAuth } from './http';
import { apiCall } from '../utils/error-handler';

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
export const getSessionStatus = async (): Promise<SessionStatusResponse> => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/live_session/status', {
      method: 'GET',
    }),
    '获取会话状态'
  );
};

/**
 * 恢复之前的会话
 */
export const resumeSession = async (): Promise<SessionStatusResponse> => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/live_session/resume', {
      method: 'POST',
    }),
    '恢复会话'
  );
};

/**
 * 暂停当前会话
 */
export const pauseSession = async (): Promise<SessionStatusResponse> => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/live_session/pause', {
      method: 'POST',
    }),
    '暂停会话'
  );
};

/**
 * 恢复暂停的会话
 */
export const resumePausedSession = async (): Promise<SessionStatusResponse> => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/live_session/resume_paused', {
      method: 'POST',
    }),
    '恢复暂停会话'
  );
};

/**
 * 恢复暂停的会话（别名，保持API一致性）
 */
export const resumePaused = resumePausedSession;

