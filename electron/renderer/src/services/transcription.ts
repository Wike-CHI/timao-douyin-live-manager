import useAuthStore from '../store/useAuthStore';

const DEFAULT_BASE_URL = (import.meta.env?.VITE_FASTAPI_URL as string | undefined) || 'http://127.0.0.1:8000';

const buildHeaders = () => {
  const { token } = useAuthStore.getState();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
};

const handleResponse = async (response: Response) => {
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail || response.statusText || '请求失败';
    throw new Error(detail);
  }
  return data;
};

export interface StartTranscriptionPayload {
  roomId: string;
  sessionId?: string;
  chunkDuration?: number;
  minConfidence?: number;
  saveAudio?: boolean;
  enableVad?: boolean;
  vadModelPath?: string | null;
  deviceIndex?: number | null;
}

export interface TranscriptionStats {
  total_audio_chunks?: number;
  successful_transcriptions?: number;
  failed_transcriptions?: number;
  average_confidence?: number;
  [key: string]: unknown;
}

export interface TranscriptionStatus {
  is_running: boolean;
  current_room_id: string | null;
  current_session_id: string | null;
  stats: TranscriptionStats;
}

export interface TranscriptionMessage {
  type: 'transcription' | 'status' | 'pong' | string;
  data?: {
    text: string;
    confidence: number;
    timestamp: number;
    is_final: boolean;
    words?: { word: string; start: number; end: number }[];
    room_id?: string;
    session_id?: string;
  };
}

export interface TranscriptionDeltaMessage {
  type: 'transcription_delta';
  data: {
    op: 'append' | 'replace' | 'final';
    text: string;
    timestamp: number;
    confidence: number;
  };
}

export const startTranscription = async (
  payload: StartTranscriptionPayload,
  baseUrl: string = DEFAULT_BASE_URL
) => {
  // 仅在显式提供时发送专业参数，保留后端自动策略
  const body: Record<string, unknown> = {
    room_id: payload.roomId,
    session_id: payload.sessionId,
    save_audio: payload.saveAudio ?? false,
  };
  if (typeof payload.chunkDuration === 'number') body.chunk_duration = payload.chunkDuration;
  if (typeof payload.minConfidence === 'number') body.min_confidence = payload.minConfidence;
  if (typeof payload.enableVad === 'boolean') body.enable_vad = payload.enableVad;
  if (typeof payload.vadModelPath !== 'undefined') body.vad_model_path = payload.vadModelPath;
  if (typeof payload.deviceIndex !== 'undefined') body.device_index = payload.deviceIndex;

  const response = await fetch(`${baseUrl}/api/transcription/start`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(body),
  });
  return handleResponse(response);
};

export const stopTranscription = async (baseUrl: string = DEFAULT_BASE_URL) => {
  const response = await fetch(`${baseUrl}/api/transcription/stop`, {
    method: 'POST',
    headers: buildHeaders(),
  });
  return handleResponse(response);
};

export const getTranscriptionStatus = async (
  baseUrl: string = DEFAULT_BASE_URL
): Promise<TranscriptionStatus> => {
  const response = await fetch(`${baseUrl}/api/transcription/status`, {
    method: 'GET',
    headers: buildHeaders(),
  });
  return handleResponse(response);
};

export const openTranscriptionWebSocket = (
  onMessage: (message: TranscriptionMessage) => void,
  baseUrl: string = DEFAULT_BASE_URL
): WebSocket => {
  const wsUrl = baseUrl
    .replace(/^http/i, 'ws')
    .replace(/\/$/, '')
    .concat('/api/transcription/ws');

  const socket = new WebSocket(wsUrl);
  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as TranscriptionMessage;
      onMessage(data);
    } catch (error) {
      console.error('解析转录消息失败:', error);
    }
  };
  return socket;
};

export const createSessionId = () => `session-${Date.now()}`;

// New: list audio input devices (from backend / PyAudio)
export interface AudioDevice {
  index: number;
  name: string;
  maxInputChannels: number;
}

export const listDevices = async (
  baseUrl: string = DEFAULT_BASE_URL
): Promise<{ devices: AudioDevice[] }> => {
  const response = await fetch(`${baseUrl}/api/transcription/devices`, {
    method: 'GET',
    headers: buildHeaders(),
  });
  return handleResponse(response);
};

// New: update runtime config (device / preset)
export const updateTranscriptionConfig = async (
  config: { deviceIndex?: number | null; deviceName?: string; presetMode?: 'fast' | 'accurate'; silenceGate?: number },
  baseUrl: string = DEFAULT_BASE_URL
) => {
  const response = await fetch(`${baseUrl}/api/transcription/config`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify({
      device_index: typeof config.deviceIndex === 'undefined' ? undefined : config.deviceIndex,
      device_name: config.deviceName,
      preset_mode: config.presetMode,
      silence_gate: config.silenceGate,
    }),
  });
  return handleResponse(response);
};
