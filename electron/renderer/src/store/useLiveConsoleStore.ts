import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import {
  LiveAudioStatus,
  LiveAudioMessage,
  openLiveAudioWebSocket,
} from '../services/liveAudio';

export interface TranscriptEntry {
  id: string;
  text: string;
  timestamp: number;
  confidence: number;
  isFinal: boolean;
  words?: { word: string; start: number; end: number }[];
  speaker?: string;
  speakerDebug?: Record<string, number>;
}

interface SaveInfo {
  trDir?: string;
  dmDir?: string;
  videoDir?: string;
}

interface ReportArtifacts {
  comments?: string;
  transcript?: string;
  report?: string;
}

interface LiveConsoleState {
  liveInput: string;
  status: LiveAudioStatus | null;
  latest: TranscriptEntry | null;
  log: TranscriptEntry[];
  mode: 'delta' | 'sentence' | 'vad';
  error: string | null;
  backendLevel: number;
  confSum: number;
  confCount: number;
  reportPaths: ReportArtifacts | null;
  reportStatus: any;
  saveInfo: SaveInfo | null;
  styleProfile: any;
  vibe: any;
  persistTr: boolean;
  persistTrRoot: string;
  persistDm: boolean;
  persistDmRoot: string;
  aiEvents: any[];
  answerScripts: any[];
  setLiveInput: (value: string) => void;
  setStatus: (value: LiveAudioStatus | null) => void;
  setLatest: (value: TranscriptEntry | null) => void;
  setMode: (value: 'delta' | 'sentence' | 'vad') => void;
  setError: (value: string | null) => void;
  setBackendLevel: (value: number) => void;
  setConfAggregates: (conf: number) => void;
  setReportPaths: (value: ReportArtifacts | null) => void;
  setReportStatus: (value: any) => void;
  setSaveInfo: (value: SaveInfo | null) => void;
  setStyleProfile: (value: any) => void;
  setVibe: (value: any) => void;
  setPersistTr: (value: boolean) => void;
  setPersistTrRoot: (value: string) => void;
  setPersistDm: (value: boolean) => void;
  setPersistDmRoot: (value: string) => void;
  setAiEvents: (value: any[]) => void;
  setAnswerScripts: (value: any[]) => void;
  pushAiEvent: (value: any) => void;
  appendLog: (entry: TranscriptEntry) => void;
  resetSessionState: () => void;
  connectWebSocket: (baseUrl: string) => void;
  disconnectWebSocket: () => void;
  handleWebSocketMessage: (message: LiveAudioMessage) => void;
}

const socketHolder: { current: WebSocket | null } = { current: null };
const deltaModeHolder: { current: boolean } = { current: false };
const reconnectState: { shouldReconnect: boolean; timer: any } = { shouldReconnect: false, timer: null };

const normalizeText = (s: string) =>
  (s || '')
    .replace(/[\s\t\n\r]+/g, '')
    .replace(/[,;:]/g, (m) => ({ ',': '，', ';': '；', ':': '：' } as const)[m as ',' | ';' | ':'] || m)
    .replace(/[\.!?]/g, '。')
    .replace(/([，。！？；：,…])\1+/g, '$1');

const isDupLike = (a: string, b: string) => {
  const A = normalizeText(a);
  const B = normalizeText(b);
  if (!A || !B) return false;
  if (A === B) return true;
  if (A.length >= 6 && (A.includes(B) || B.includes(A))) return true;
  return false;
};

export const useLiveConsoleStore = create<LiveConsoleState>()(
  persist(
    (set, get) => ({
      liveInput: '',
      status: null,
      latest: null,
      log: [],
      mode: 'vad',
      error: null,
      backendLevel: 0,
      confSum: 0,
      confCount: 0,
      reportPaths: null,
      reportStatus: null,
      saveInfo: null,
      styleProfile: null,
      vibe: null,
      persistTr: false,
      persistTrRoot: '',
      persistDm: false,
      persistDmRoot: '',
      aiEvents: [],
      answerScripts: [],
      setLiveInput: (value) => set({ liveInput: value }),
      setStatus: (value) => set({ status: value }),
      setLatest: (value) => set({ latest: value }),
      setMode: (value) => set({ mode: value }),
      setError: (value) => set({ error: value }),
      setBackendLevel: (value) => set({ backendLevel: value }),
      setConfAggregates: (conf) =>
        set((state) => {
          if (Number.isNaN(conf) || conf <= 0) return state;
          return {
            ...state,
            confSum: state.confSum + conf,
            confCount: state.confCount + 1,
          };
        }),
      setReportPaths: (value) => set({ reportPaths: value }),
      setReportStatus: (value) => set({ reportStatus: value }),
      setSaveInfo: (value) => set({ saveInfo: value }),
      setStyleProfile: (value) => set({ styleProfile: value }),
      setVibe: (value) => set({ vibe: value }),
      setPersistTr: (value) => set({ persistTr: value }),
      setPersistTrRoot: (value) => set({ persistTrRoot: value }),
      setPersistDm: (value) => set({ persistDm: value }),
      setPersistDmRoot: (value) => set({ persistDmRoot: value }),
      setAiEvents: (value) => set({ aiEvents: value }),
      setAnswerScripts: (value) => set({ answerScripts: value }),
      pushAiEvent: (value) =>
        set((state) => ({
          ...state,
          aiEvents: [value, ...state.aiEvents].slice(0, 10),
        })),
      appendLog: (entry) =>
        set((state) => {
          const last = state.log[0];
          if (last && isDupLike(entry.text, last.text)) {
            return { ...state, latest: entry };
          }
          return {
            ...state,
            latest: entry,
            log: [entry, ...state.log],
          };
        }),
      resetSessionState: () =>
        set((state) => ({
          ...state,
          status: state.status ? { ...state.status, is_running: false } : state.status,
          latest: null,
          backendLevel: 0,
          error: null,
          saveInfo: null,
        })),
      connectWebSocket: (baseUrl) => {
        const current = socketHolder.current;
        if (current) {
          try { current.close(); } catch { /* ignore */ }
        }
        if (reconnectState.timer) {
          clearTimeout(reconnectState.timer);
          reconnectState.timer = null;
        }
        deltaModeHolder.current = false;
        reconnectState.shouldReconnect = true;
        const socket = openLiveAudioWebSocket((message) => get().handleWebSocketMessage(message), baseUrl);
        socketHolder.current = socket;
        socket.onopen = () => {
          deltaModeHolder.current = false;
        };
        socket.onerror = () => {
          try { socket.close(); } catch { /* ignore */ }
        };
        socket.onclose = () => {
          socketHolder.current = null;
          deltaModeHolder.current = false;
          if (!reconnectState.shouldReconnect) return;
          if (!(get().status?.is_running)) return;
          if (reconnectState.timer) clearTimeout(reconnectState.timer);
          reconnectState.timer = setTimeout(() => {
            get().connectWebSocket(baseUrl);
          }, 1200);
        };
      },
      disconnectWebSocket: () => {
        reconnectState.shouldReconnect = false;
        if (reconnectState.timer) {
          clearTimeout(reconnectState.timer);
          reconnectState.timer = null;
        }
        const current = socketHolder.current;
        if (current) {
          try {
            current.onclose = null;
            current.onerror = null;
            current.onopen = null;
          } catch {
            /* ignore */
          }
          try { current.close(); } catch { /* ignore */ }
        }
        socketHolder.current = null;
        deltaModeHolder.current = false;
      },
      handleWebSocketMessage: (message) => {
        if (!message) return;
        if (message.type === 'level') {
          const level = Number((message as any)?.data?.rms ?? 0);
          get().setBackendLevel(level || 0);
          return;
        }
        if (message.type === 'transcription_delta') {
          deltaModeHolder.current = true;
          const m = message as any;
          const op = m?.data?.op as 'append' | 'replace' | 'final';
          const ts = Number(m?.data?.timestamp) || Date.now() / 1000;
          const conf = Number(m?.data?.confidence) || 0;
          const deltaText = String(m?.data?.text || '');
          const incomingSpeaker = typeof m?.data?.speaker === 'string' ? (m.data.speaker as string) : undefined;
          const incomingSpeakerDebug = typeof m?.data?.speaker_debug === 'object' && m?.data?.speaker_debug !== null
            ? (m.data.speaker_debug as Record<string, number>)
            : undefined;
          let nextText = '';
          set((state) => {
            const base = state.latest?.text ?? '';
            const speaker = incomingSpeaker ?? state.latest?.speaker;
            const speakerDebug = incomingSpeakerDebug ?? state.latest?.speakerDebug;
            if (op === 'append') nextText = base + deltaText;
            else if (op === 'replace') nextText = deltaText;
            else if (op === 'final') nextText = deltaText;
            const entry: TranscriptEntry = {
              id: `${ts}-${Math.random()}`,
              text: nextText,
              confidence: conf,
              timestamp: ts,
              isFinal: op === 'final',
              words: [],
              speaker,
              speakerDebug,
            };
            if (entry.isFinal && entry.text.trim()) {
              const last = state.log[0];
              const shouldAppend = !(last && isDupLike(entry.text, last.text));
              return {
                ...state,
                latest: entry,
                log: shouldAppend ? [entry, ...state.log] : state.log,
                confSum: conf > 0 ? state.confSum + conf : state.confSum,
                confCount: conf > 0 ? state.confCount + 1 : state.confCount,
              };
            }
            return { ...state, latest: entry };
          });
          return;
        }
        if (message.type === 'transcription' && message.data) {
          if (deltaModeHolder.current) return;
          const d = message.data as any;
          const entry: TranscriptEntry = {
            id: `${(d.timestamp ?? Date.now())}-${Math.random()}`,
            text: d.text,
            confidence: Number(d.confidence ?? 0),
            timestamp: Number(d.timestamp ?? Date.now() / 1000),
            isFinal: !!d.is_final,
            words: d.words,
            speaker: d.speaker,
            speakerDebug: d.speaker_debug,
          };
          if (entry.isFinal && entry.text?.trim()) {
            get().appendLog(entry);
            get().setConfAggregates(entry.confidence || 0);
          } else {
            get().setLatest(entry);
          }
          return;
        }
      },
    }),
    {
      name: 'timao-live-console',
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        liveInput: state.liveInput,
        status: state.status,
        latest: state.latest,
        log: state.log,
        mode: state.mode,
        error: state.error,
        backendLevel: state.backendLevel,
        confSum: state.confSum,
        confCount: state.confCount,
        reportPaths: state.reportPaths,
        reportStatus: state.reportStatus,
        saveInfo: state.saveInfo,
        styleProfile: state.styleProfile,
        vibe: state.vibe,
        persistTr: state.persistTr,
        persistTrRoot: state.persistTrRoot,
        persistDm: state.persistDm,
        persistDmRoot: state.persistDmRoot,
        aiEvents: state.aiEvents,
        answerScripts: state.answerScripts,
      }),
    }
  )
);

export const getLiveConsoleSocket = () => socketHolder.current;
