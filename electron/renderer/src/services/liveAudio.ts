import useAuthStore from '../store/useAuthStore';
import authService from './authService';

const DEFAULT_BASE_URL = import.meta.env?.VITE_FASTAPI_URL as string || 'http://127.0.0.1:9019';

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

export interface StartLiveAudioPayload {
  live_url: string; // 支持完整 URL 或 直播间 ID
  session_id?: string;
  chunk_duration?: number; // 0.2~2.0s
  profile?: 'fast' | 'stable'; // 预设：快速/稳妥
  // 模式与模型后端已固定为 'vad' + 'small'，以下参数仅保留 VAD 与句子组装的细节调参
  vad_min_silence_sec?: number;
  vad_min_speech_sec?: number;
  vad_hangover_sec?: number;
  vad_rms?: number;
  // Sentence assembler params
  max_wait?: number;
  max_chars?: number;
  silence_flush?: number;
  min_sentence_chars?: number;
}

export interface LiveAudioStatus {
  is_running: boolean;
  live_id: string | null;
  live_url: string | null;
  session_id: string | null;
  mode?: 'delta' | 'sentence' | 'vad' | string;
  profile?: 'fast' | 'stable' | string;
  advanced?: {
    music_filter?: boolean;
    music_detection_enabled?: boolean;
    music_guard_active?: boolean;
    music_guard_score?: number;
    persist_enabled?: boolean;
    persist_root?: string;
    agc_enabled?: boolean;
    agc_gain?: number;
    diarizer_active?: boolean;
    max_speakers?: number;
    last_speaker?: string;
  };
  stats: {
    total_audio_chunks?: number;
    successful_transcriptions?: number;
    failed_transcriptions?: number;
    average_confidence?: number;
  };
}

export interface LiveAudioMessage {
  type: 'transcription' | 'transcription_delta' | 'level' | 'status' | 'pong' | 'error' | string;
  data?: any;
}

export const startLiveAudio = async (
  payload: StartLiveAudioPayload,
  baseUrl: string = DEFAULT_BASE_URL
) => {
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
  const response = await fetch(`${baseUrl}/api/live_audio/start`, {
    method: 'POST',
    headers: await buildHeaders(),
    body: JSON.stringify(body),
  });
  return handleResponse(response);
};

export const stopLiveAudio = async (baseUrl: string = DEFAULT_BASE_URL) => {
  const response = await fetch(`${baseUrl}/api/live_audio/stop`, {
    method: 'POST',
    headers: await buildHeaders(),
  });
  return handleResponse(response);
};

export const getLiveAudioStatus = async (
  baseUrl: string = DEFAULT_BASE_URL
): Promise<LiveAudioStatus> => {
  const response = await fetch(`${baseUrl}/api/live_audio/status`, {
    method: 'GET',
    headers: await buildHeaders(),
  });
  return handleResponse(response);
};

export const openLiveAudioWebSocket = (
  onMessage: (message: LiveAudioMessage) => void,
  baseUrl: string = DEFAULT_BASE_URL
): WebSocket => {
  const wsUrl = baseUrl.replace(/^http/i, 'ws').replace(/\/$/, '') + '/api/live_audio/ws';
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

export const updateLiveAudioAdvanced = async (
  payload: {
    agc?: boolean;
    diarization?: boolean;
    max_speakers?: number;
    persist_enabled?: boolean;
    persist_root?: string;
  },
  baseUrl: string = DEFAULT_BASE_URL
) => {
  const headers = await buildHeaders();
  const response = await fetch(`${baseUrl}/api/live_audio/advanced`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
};
