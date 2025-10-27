import useAuthStore from '../store/useAuthStore';
import authService from './authService';

const DEFAULT_BASE_URL = (import.meta.env?.VITE_FASTAPI_URL as string | undefined) || 'http://127.0.0.1:10090';

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

export interface LiveReportStartReq { live_url: string; segment_minutes?: number }
export interface LiveReportStartResp { success: boolean; data?: { session_id: string; recording_dir: string; segment_seconds: number } }
export interface LiveReportStatusResp { active: boolean; status: any }
export interface LiveReportGenResp { success: boolean; data?: { comments: string; transcript: string; report: string } }

export const startLiveReport = async (liveUrl: string, segmentMinutes = 30, baseUrl: string = DEFAULT_BASE_URL) => {
  const headers = await buildHeaders();
  const response = await fetch(`${baseUrl}/api/report/live/start`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ live_url: liveUrl, segment_minutes: segmentMinutes } satisfies LiveReportStartReq),
  });
  return handleResponse<LiveReportStartResp>(response);
};

export const stopLiveReport = async (baseUrl: string = DEFAULT_BASE_URL) => {
  const headers = await buildHeaders();
  const response = await fetch(`${baseUrl}/api/report/live/stop`, { method: 'POST', headers });
  return handleResponse<LiveReportStartResp>(response);
};

export const getLiveReportStatus = async (baseUrl: string = DEFAULT_BASE_URL) => {
  const headers = await buildHeaders();
  const response = await fetch(`${baseUrl}/api/report/live/status`, { headers });
  return handleResponse<LiveReportStatusResp>(response);
};

export const generateLiveReport = async (baseUrl: string = DEFAULT_BASE_URL) => {
  const headers = await buildHeaders();
  const response = await fetch(`${baseUrl}/api/report/live/generate`, { method: 'POST', headers });
  return handleResponse<LiveReportGenResp>(response);
};

