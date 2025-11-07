import useAuthStore from '../store/useAuthStore';
import { buildServiceUrl } from './apiConfig';
import { buildJsonAuthHeaders } from './http';
import { apiCall } from '../utils/error-handler';

const buildHeaders = buildJsonAuthHeaders;


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
  model?: string;  // 修复 AUDIO-002: 添加模型字段
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
  baseUrl?: string
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
  return apiCall(
    async () => {
      const headers = await buildHeaders();
      return fetch(buildServiceUrl('main', '/api/live_audio/start', baseUrl), {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      });
    },
    '启动实时转写'
  );
};

export const stopLiveAudio = async (baseUrl?: string) => {
  return apiCall(
    async () => {
      const headers = await buildHeaders();
      return fetch(buildServiceUrl('main', '/api/live_audio/stop', baseUrl), {
        method: 'POST',
        headers,
      });
    },
    '停止实时转写'
  );
};

export const getLiveAudioStatus = async (
  baseUrl?: string
): Promise<LiveAudioStatus> => {
  return apiCall(
    async () => {
      const headers = await buildHeaders();
      return fetch(buildServiceUrl('main', '/api/live_audio/status', baseUrl), {
        method: 'GET',
        headers,
      });
    },
    '获取实时转写状态'
  );
};

export const openLiveAudioWebSocket = (
  onMessage: (message: LiveAudioMessage) => void,
  baseUrl?: string
): WebSocket => {
  const resolved = buildServiceUrl('main', '/api/live_audio/ws', baseUrl).replace(/^http/i, 'ws');
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

/**
 * 音频高级设置接口（修复 AUDIO-003）
 */
export interface LiveAudioAdvancedSettings {
  // 持久化设置
  persist_enabled?: boolean;
  persist_root?: string;
  // 自动增益控制
  agc?: boolean;
  agc_target_level?: number;
  // 说话人分离
  diarization?: boolean;
  max_speakers?: number;
  // 音乐检测
  music_detection_enabled?: boolean;
  music_filter?: boolean;
  // VAD 参数
  vad_min_silence_sec?: number;
  vad_min_speech_sec?: number;
  vad_hangover_sec?: number;
  vad_rms?: number;
  // 句子组装参数
  max_wait?: number;
  max_chars?: number;
  silence_flush?: number;
  min_sentence_chars?: number;
}

export const updateLiveAudioAdvanced = async (
  settings: LiveAudioAdvancedSettings,  // 修复 AUDIO-003: 使用具体类型
  baseUrl?: string
) => {
  const headers = await buildHeaders();
  return apiCall(
    () => fetch(buildServiceUrl('main', '/api/live_audio/advanced', baseUrl), {
      method: 'POST',
      headers,
      body: JSON.stringify(settings),
    }),
    '更新实时转写高级设置'
  );
};
