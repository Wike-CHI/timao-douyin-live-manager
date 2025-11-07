import { fetchJsonWithAuth } from './http';
import { apiCall } from '../utils/error-handler';
import type { ReviewData, ReportArtifacts } from '../types/report';
import type {
  StartLiveReportRequest,
  StartLiveReportResponse,
  LiveReportStatusResponse,
  GenerateLiveReportResponse,
} from '../types/api-types';

// 导出类型供其他模块使用
export type { ReviewData, ReportArtifacts } from '../types/report';

export const startLiveReport = async (
  liveUrl: string,
  segmentMinutes = 30
): Promise<StartLiveReportResponse> => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/report/live/start', {
      method: 'POST',
      body: JSON.stringify({ live_url: liveUrl, segment_minutes: segmentMinutes } satisfies StartLiveReportRequest),
    }),
    '启动直播报告'
  );
};

export const stopLiveReport = async () => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/report/live/stop', { method: 'POST' }),
    '停止直播报告'
  );
};

export const pauseLiveReport = async () => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/report/live/pause', { method: 'POST' }),
    '暂停直播报告'
  );
};

export const resumeLiveReport = async () => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/report/live/resume', { method: 'POST' }),
    '恢复直播报告'
  );
};

export const getResumableSession = async () => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/report/live/resumable'),
    '获取可恢复会话'
  );
};

export const getLiveReportStatus = async (): Promise<LiveReportStatusResponse> => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/report/live/status'),
    '获取直播报告状态'
  );
};

export const generateLiveReport = async (): Promise<GenerateLiveReportResponse> => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/report/live/generate', { method: 'POST' }),
    '生成直播报告'
  );
};

