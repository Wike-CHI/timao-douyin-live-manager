import { buildServiceUrl } from './apiConfig';
import { fetchJsonWithAuth } from './http';
import { apiCall } from '../utils/error-handler';
import type {
  StartLiveAudioRequest,
  LiveAudioStatus,
  LiveAudioMessage,
  LiveAudioAdvancedSettings,
} from '../types/api-types';

export const startLiveAudio = async (payload: StartLiveAudioRequest) => {
  const body: Record<string, unknown> = {
    live_url: payload.live_url,
    session_id: payload.session_id,
  };
  if (typeof payload.profile === 'string') body.profile = payload.profile;
  if (typeof payload.chunk_duration === 'number') body.chunk_duration = payload.chunk_duration;
  // 后端固定 mode='vad' & model='small'，忽略前端传入
  if (typeof payload.vad_min_silence_sec === 'number') body.vad_min_silence_sec = payload.vad_min_silence_sec;
  if (typeof payload.vad_min_speech_sec === 'number') body.vad_min_speech_sec = payload.vad_min_speech_sec;
  if (typeof payload.vad_hangover_sec === 'number') body.vad_hangover_sec = payload.vad_hangover_sec;
  if (typeof payload.vad_rms === 'number') body.vad_rms = payload.vad_rms;
  if (typeof payload.max_wait === 'number') body.max_wait = payload.max_wait;
  if (typeof payload.max_chars === 'number') body.max_chars = payload.max_chars;
  if (typeof payload.silence_flush === 'number') body.silence_flush = payload.silence_flush;
  if (typeof payload.min_sentence_chars === 'number') body.min_sentence_chars = payload.min_sentence_chars;
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/live_audio/start', {
    method: 'POST',
    body: JSON.stringify(body),
    }),
    '启动实时转写'
  );
};

export const stopLiveAudio = async () => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/live_audio/stop', {
    method: 'POST',
    }),
    '停止实时转写'
  );
};

export const getLiveAudioStatus = async (): Promise<LiveAudioStatus> => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/live_audio/status', {
    method: 'GET',
    }),
    '获取实时转写状态'
  );
};

export const openLiveAudioWebSocket = (
  onMessage: (message: LiveAudioMessage) => void
): WebSocket => {
  const resolved = buildServiceUrl('main', '/api/live_audio/ws').replace(/^http/i, 'ws');
  const wsUrl = resolved.replace(/\/$/, '');
  const socket = new WebSocket(wsUrl);
  socket.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data) as LiveAudioMessage;
      onMessage(data);
    } catch (e) {
      console.error('解析 live_audio WS 消息失败:', e);
    }
  };
  return socket;
};

export const updateLiveAudioAdvanced = async (settings: LiveAudioAdvancedSettings) => {
  return apiCall(
    () => fetchJsonWithAuth('main', '/api/live_audio/advanced', {
    method: 'POST',
    body: JSON.stringify(settings),
    }),
    '更新实时转写高级设置'
  );
};
