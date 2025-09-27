import useAuthStore from '../store/useAuthStore';

const DEFAULT_BASE_URL = (import.meta.env?.VITE_FASTAPI_URL as string | undefined) || 'http://127.0.0.1:8007';

const buildHeaders = () => {
  const { token } = useAuthStore.getState();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
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
  liveUrl: string; // 支持完整 URL 或 直播间 ID
  sessionId?: string;
  chunkDuration?: number; // 0.2~2.0s
  profile?: 'fast' | 'stable'; // 预设：快速/稳妥
  // 模式与模型后端已固定为 'vad' + 'small'，以下参数仅保留 VAD 与句子组装的细节调参
  vadMinSilenceSec?: number;
  vadMinSpeechSec?: number;
  vadHangoverSec?: number;
  vadRms?: number;
  // Sentence assembler params
  maxWait?: number;
  maxChars?: number;
  silenceFlush?: number;
  minSentenceChars?: number;
}

export interface LiveAudioStatus {
  is_running: boolean;
  live_id: string | null;
  live_url: string | null;
  session_id: string | null;
  mode?: 'delta' | 'sentence' | 'vad' | string;
  profile?: 'fast' | 'stable' | string;
  advanced?: { music_filter?: boolean; diarization?: boolean };
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
    live_url: payload.liveUrl,
    session_id: payload.sessionId,
  };
  if (typeof payload.profile === 'string') body.profile = payload.profile;
  if (typeof payload.chunkDuration === 'number') body.chunk_duration = payload.chunkDuration;
  // 后端固定 mode='vad' & model='small'，忽略前端传入
  if (typeof payload.vadMinSilenceSec === 'number') body.vad_min_silence_sec = payload.vadMinSilenceSec;
  if (typeof payload.vadMinSpeechSec === 'number') body.vad_min_speech_sec = payload.vadMinSpeechSec;
  if (typeof payload.vadHangoverSec === 'number') body.vad_hangover_sec = payload.vadHangoverSec;
  if (typeof payload.vadRms === 'number') body.vad_rms = payload.vadRms;
  if (typeof payload.maxWait === 'number') body.max_wait = payload.maxWait;
  if (typeof payload.maxChars === 'number') body.max_chars = payload.maxChars;
  if (typeof payload.silenceFlush === 'number') body.silence_flush = payload.silenceFlush;
  if (typeof payload.minSentenceChars === 'number') body.min_sentence_chars = payload.minSentenceChars;
  const response = await fetch(`${baseUrl}/api/live_audio/start`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(body),
  });
  return handleResponse(response);
};

export const stopLiveAudio = async (baseUrl: string = DEFAULT_BASE_URL) => {
  const response = await fetch(`${baseUrl}/api/live_audio/stop`, {
    method: 'POST',
    headers: buildHeaders(),
  });
  return handleResponse(response);
};

export const getLiveAudioStatus = async (
  baseUrl: string = DEFAULT_BASE_URL
): Promise<LiveAudioStatus> => {
  const response = await fetch(`${baseUrl}/api/live_audio/status`, {
    method: 'GET',
    headers: buildHeaders(),
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
  payload: { music_filter?: boolean; diarization?: boolean; max_speakers?: number; persist_enabled?: boolean; persist_root?: string },
  baseUrl: string = DEFAULT_BASE_URL
) => {
  const response = await fetch(`${baseUrl}/api/live_audio/advanced`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(payload || {}),
  });
  return handleResponse(response);
};
