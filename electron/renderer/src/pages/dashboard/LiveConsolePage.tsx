import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  createSessionId,
  getTranscriptionStatus,
  openTranscriptionWebSocket,
  startTranscription,
  stopTranscription,
  TranscriptionMessage,
  TranscriptionStatus,
} from '../../services/transcription';
import DouyinRelayPanel from '../../components/douyin/DouyinRelayPanel';

interface TranscriptEntry {
  id: string;
  text: string;
  timestamp: number;
  confidence: number;
  isFinal: boolean;
}

const MAX_LOG_ITEMS = 50;
const FASTAPI_BASE_URL = (import.meta.env?.VITE_FASTAPI_URL as string | undefined) || 'http://127.0.0.1:8007';

const LiveConsolePage = () => {
  const [roomId, setRoomId] = useState('default_room');
  const [sessionId, setSessionId] = useState<string>(createSessionId());
  const [status, setStatus] = useState<TranscriptionStatus | null>(null);
  const [latest, setLatest] = useState<TranscriptEntry | null>(null);
  const [log, setLog] = useState<TranscriptEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // VAD 控件
  const [enableVad, setEnableVad] = useState(false);
  const [vadModelPath, setVadModelPath] = useState<string>('');

  const socketRef = useRef<WebSocket | null>(null);

  const isRunning = status?.is_running ?? false;

  const appendLog = useCallback((entry: TranscriptEntry) => {
    setLog((prev) => {
      const updated = [entry, ...prev];
      if (updated.length > MAX_LOG_ITEMS) {
        updated.length = MAX_LOG_ITEMS;
      }
      return updated;
    });
  }, []);

  const handleSocketMessage = useCallback(
    (message: TranscriptionMessage) => {
      if (message.type === 'transcription' && message.data) {
        const entry: TranscriptEntry = {
          id: `${message.data.timestamp}-${Math.random()}`,
          text: message.data.text,
          confidence: message.data.confidence,
          timestamp: message.data.timestamp,
          isFinal: message.data.is_final,
        };
        setLatest(entry);
        if (entry.isFinal && entry.text.trim()) {
          appendLog(entry);
        }
      }
    },
    [appendLog]
  );

  const connectWebSocket = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
    }
    const socket = openTranscriptionWebSocket(handleSocketMessage, FASTAPI_BASE_URL);
    socketRef.current = socket;
  }, [handleSocketMessage]);

  const refreshStatus = useCallback(async () => {
    try {
      const result = await getTranscriptionStatus(FASTAPI_BASE_URL);
      setStatus(result);
      if (result.is_running) {
        if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
          connectWebSocket();
        }
      }
    } catch (err) {
      console.error(err);
      setError((err as Error).message ?? '获取转录状态失败');
    }
  }, [connectWebSocket]);

  useEffect(() => {
    refreshStatus();
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [refreshStatus]);

  const handleStart = async () => {
    setLoading(true);
    setError(null);
    try {
      const currentSession = sessionId || createSessionId();
      setSessionId(currentSession);
      await startTranscription(
        {
          roomId,
          sessionId: currentSession,
          chunkDuration: 1.0,
          minConfidence: 0.6,
          saveAudio: false,
          enableVad,
          vadModelPath: enableVad && vadModelPath.trim() ? vadModelPath.trim() : null,
        },
        FASTAPI_BASE_URL
      );
      await refreshStatus();
      connectWebSocket();
    } catch (err) {
      console.error(err);
      setError((err as Error).message ?? '启动转录失败');
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    setError(null);
    try {
      await stopTranscription(FASTAPI_BASE_URL);
      setLatest(null);
      setStatus((prev) => (prev ? { ...prev, is_running: false } : prev));
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    } catch (err) {
      console.error(err);
      setError((err as Error).message ?? '停止转录失败');
    } finally {
      setLoading(false);
    }
  };

  const formattedCountdown = useMemo(() => {
    if (!isRunning) return '暂停';
    return '运行中';
  }, [isRunning]);

  return (
    <div className="space-y-6">
      <div className="timao-soft-card flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-4">
          <div className="text-4xl">🎙️</div>
          <div>
            <div className="text-lg font-semibold text-purple-600">音频转写 · SenseVoiceSmall</div>
            <div className="text-sm timao-support-text">
              {isRunning
                ? `会话 ${status?.current_session_id ?? sessionId} 正在运行`
                : '未运行 · 点击开始以激活实时转写'}
            </div>
            <div className="text-xs text-slate-400">
              服务地址：{FASTAPI_BASE_URL}
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <input
            value={roomId}
            onChange={(event) => setRoomId(event.target.value)}
            className="timao-input w-48 text-sm"
            placeholder="Room ID"
            disabled={isRunning || loading}
          />
          <button
            className="timao-primary-btn"
            onClick={handleStart}
            disabled={loading || isRunning}
          >
            {loading ? '处理中...' : isRunning ? '运行中' : '开始转写'}
          </button>
          <button
            className="timao-outline-btn"
            onClick={handleStop}
            disabled={loading || !isRunning}
          >
            停止
          </button>
        </div>
      </div>

      {error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
          {error}
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.2fr_1.2fr_0.8fr] lg:grid-cols-[1fr_1fr]">
        <section className="timao-card h-full flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
              <span>📝</span>
              语音转写流
            </h3>
            <span className="timao-status-pill text-xs">
              {isRunning ? '实时更新中' : '已暂停'}
            </span>
          </div>
          <div className="space-y-3 overflow-y-auto pr-1">
            {log.length === 0 ? (
              <div className="timao-outline-card text-sm timao-support-text text-center">
                暂无转写结果。{isRunning ? '请说话以生成文本。' : '点击开始转写以开启实时字幕。'}
              </div>
            ) : (
              log.map((item) => (
                <div
                  key={item.id}
                  className="rounded-2xl border border-white/60 shadow-md p-4 bg-white/95"
                >
                  <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                    <span>{new Date(item.timestamp * 1000).toLocaleTimeString()}</span>
                    <span>置信度 {(item.confidence * 100).toFixed(1)}%</span>
                  </div>
                  <div className="text-slate-600 text-sm leading-relaxed">{item.text}</div>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="flex flex-col gap-4">
          <div className="timao-card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
                <span>🎛️</span>
                转写设置
              </h3>
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={enableVad}
                  onChange={(e) => setEnableVad(e.target.checked)}
                />
                启用 VAD（语音活动检测）
              </label>
            </div>
            <div className="mt-3">
              <label className="text-xs text-slate-500 block mb-1">VAD 模型路径（可选）</label>
              <input
                type="text"
                placeholder="例如：models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
                className="timao-input w-full"
                value={vadModelPath}
                onChange={(e) => setVadModelPath(e.target.value)}
                disabled={!enableVad}
              />
              <div className="text-xs timao-support-text mt-1">
                为空则按后端默认策略。建议将模型离线放入 models/ 目录并填写绝对或项目相对路径。
              </div>
            </div>
          </div>
          <div className="timao-card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
                <span>💡</span>
                实时字幕
              </h3>
              <span className="text-xs timao-support-text">{formattedCountdown}</span>
            </div>
            <div className="rounded-2xl bg-purple-50/80 border border-purple-100 px-4 py-3 text-slate-700 min-h-[72px] flex items-center">
              {latest?.text ? latest.text : '等待识别结果...'}
            </div>
            {latest ? (
              <div className="text-xs text-slate-400 mt-3">
                时间 {new Date(latest.timestamp * 1000).toLocaleTimeString()} · 置信度{' '}
                {(latest.confidence * 100).toFixed(1)}%
              </div>
            ) : null}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="timao-soft-card">
              <div className="text-sm text-slate-500 mb-1">当前会话</div>
              <div className="text-lg font-semibold text-purple-600">
                {status?.current_session_id ?? sessionId}
              </div>
              <div className="text-xs timao-support-text mt-2">
                已累计片段 {status?.stats?.total_audio_chunks ?? 0} · 成功转写{' '}
                {status?.stats?.successful_transcriptions ?? 0}
              </div>
            </div>
            <div className="timao-soft-card">
              <div className="text-sm text-slate-500 mb-1">平均置信度</div>
              <div className="text-lg font-semibold text-purple-600">
                {(status?.stats?.average_confidence ?? 0).toFixed(2)}
              </div>
              <div className="text-xs timao-support-text mt-2">
                失败次数 {status?.stats?.failed_transcriptions ?? 0}
              </div>
            </div>
          </div>
        </section>

        <section className="flex flex-col gap-4">
          <div className="timao-card">
            <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2 mb-3">
              <span>🔍</span>
              SenseVoice 状态
            </h3>
            <ul className="space-y-2 text-sm timao-support-text">
              <li>· 服务状态：{isRunning ? '运行中' : '已停止'}</li>
              <li>· 当前 Room：{status?.current_room_id ?? 'N/A'}</li>
              <li>· 监听端点：/api/transcription/ws</li>
            </ul>
          </div>

          <div className="timao-card">
            <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2 mb-3">
              <span>📎</span>
              使用提示
            </h3>
            <ul className="space-y-2 text-sm timao-support-text">
              <li>· 启动前请确认麦克风或声卡输入已配置。</li>
              <li>· SenseVoice 模型需提前下载并满足依赖。</li>
              <li>· 若启动失败，请查看日志或终端输出。</li>
            </ul>
          </div>
        </section>
      </div>

      <DouyinRelayPanel baseUrl={FASTAPI_BASE_URL} />
    </div>
  );
};

export default LiveConsolePage;
