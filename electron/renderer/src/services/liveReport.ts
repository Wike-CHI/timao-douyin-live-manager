import useAuthStore from '../store/useAuthStore';
import authService from './authService';
import { apiCall } from '../utils/error-handler';
import type { ReviewData, ReportArtifacts } from '../types/report';

// 导出类型供其他模块使用
export type { ReviewData, ReportArtifacts } from '../types/report';

const DEFAULT_BASE_URL = import.meta.env?.VITE_FASTAPI_URL as string || 'http://127.0.0.1:9030'; // 默认端口改为 9030，避免 Windows 端口排除范围 8930-9029

const buildHeaders = async () => {
  const authHeaders = await authService.getAuthHeaders();
  return {
    'Content-Type': 'application/json',
    ...authHeaders,
  };
};


export interface LiveReportStartReq { 
  live_url: string; 
  segment_minutes?: number 
}

export interface LiveReportStartResp { 
  success: boolean; 
  data?: { 
    session_id: string; 
    recording_dir: string; 
    segment_seconds: number 
  } 
}

export interface LiveReportStatusResp { 
  active: boolean; 
  status: any 
}

export interface LiveReportGenResp { 
  success: boolean; 
  data?: ReportArtifacts;
}

export const startLiveReport = async (liveUrl: string, segmentMinutes = 30, baseUrl: string = DEFAULT_BASE_URL) => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(`${baseUrl}/api/report/live/start`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ live_url: liveUrl, segment_minutes: segmentMinutes } satisfies LiveReportStartReq),
    }),
    '启动直播报告'
  );
};

export const stopLiveReport = async (baseUrl: string = DEFAULT_BASE_URL) => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(`${baseUrl}/api/report/live/stop`, { method: 'POST', headers }),
    '停止直播报告'
  );
};

export const pauseLiveReport = async (baseUrl: string = DEFAULT_BASE_URL) => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(`${baseUrl}/api/report/live/pause`, { method: 'POST', headers }),
    '暂停直播报告'
  );
};

export const resumeLiveReport = async (baseUrl: string = DEFAULT_BASE_URL) => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(`${baseUrl}/api/report/live/resume`, { method: 'POST', headers }),
    '恢复直播报告'
  );
};

export const getResumableSession = async (baseUrl: string = DEFAULT_BASE_URL) => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(`${baseUrl}/api/report/live/resumable`, { headers }),
    '获取可恢复会话'
  );
};

export const getLiveReportStatus = async (baseUrl: string = DEFAULT_BASE_URL) => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(`${baseUrl}/api/report/live/status`, { headers }),
    '获取直播报告状态'
  );
};

export const generateLiveReport = async (baseUrl: string = DEFAULT_BASE_URL) => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(`${baseUrl}/api/report/live/generate`, { method: 'POST', headers }),
    '生成直播报告'
  );
};

