import useAuthStore from '../store/useAuthStore';
import authService from './authService';
import { buildServiceUrl } from './apiConfig';
import { apiCall } from '../utils/error-handler';
import type { ReviewData, ReportArtifacts } from '../types/report';

// 导出类型供其他模块使用
export type { ReviewData, ReportArtifacts } from '../types/report';

const buildHeaders = async () => {
  const authHeaders = await authService.getAuthHeaders();
  return {
    'Content-Type': 'application/json',
    ...authHeaders,
  };
};

const buildReportUrl = (path: string, baseUrl?: string) =>
  buildServiceUrl('main', path, baseUrl);


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

export const startLiveReport = async (liveUrl: string, segmentMinutes = 30, baseUrl?: string) => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(buildReportUrl('/api/report/live/start', baseUrl), {
      method: 'POST',
      headers,
      body: JSON.stringify({ live_url: liveUrl, segment_minutes: segmentMinutes } satisfies LiveReportStartReq),
    }),
    '启动直播报告'
  );
};

export const stopLiveReport = async (baseUrl?: string) => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(buildReportUrl('/api/report/live/stop', baseUrl), { method: 'POST', headers }),
    '停止直播报告'
  );
};

export const pauseLiveReport = async (baseUrl?: string) => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(buildReportUrl('/api/report/live/pause', baseUrl), { method: 'POST', headers }),
    '暂停直播报告'
  );
};

export const resumeLiveReport = async (baseUrl?: string) => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(buildReportUrl('/api/report/live/resume', baseUrl), { method: 'POST', headers }),
    '恢复直播报告'
  );
};

export const getResumableSession = async (baseUrl?: string) => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(buildReportUrl('/api/report/live/resumable', baseUrl), { headers }),
    '获取可恢复会话'
  );
};

export const getLiveReportStatus = async (baseUrl?: string) => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(buildReportUrl('/api/report/live/status', baseUrl), { headers }),
    '获取直播报告状态'
  );
};

export const generateLiveReport = async (baseUrl?: string) => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(buildReportUrl('/api/report/live/generate', baseUrl), { method: 'POST', headers }),
    '生成直播报告'
  );
};

