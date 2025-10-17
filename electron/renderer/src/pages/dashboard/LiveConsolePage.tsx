import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import DouyinRelayPanel from '../../components/douyin/DouyinRelayPanel';
import {
  getLiveAudioStatus,
  startLiveAudio,
  stopLiveAudio,
  updateLiveAudioAdvanced,
} from '../../services/liveAudio';
import { startLiveReport, stopLiveReport, getLiveReportStatus, generateLiveReport } from '../../services/liveReport';
import { startDouyinRelay, stopDouyinRelay, getDouyinRelayStatus, updateDouyinPersist } from '../../services/douyin';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../../store/useAuthStore';
import { useFirstFree as useFirstFreeApi } from '../../services/auth';
import { startAILiveAnalysis, stopAILiveAnalysis, openAILiveStream, generateAnswerScripts } from '../../services/ai';
import { useLiveConsoleStore, getLiveConsoleSocket } from '../../store/useLiveConsoleStore';

// Note: Do not cap transcript items; persist to disk is handled by backend.
// We keep full in-memory log for current session (may grow large for long sessions).
const FASTAPI_BASE_URL = (import.meta.env?.VITE_FASTAPI_URL as string | undefined) || 'http://127.0.0.1:8090';

const LiveConsolePage = () => {
  const {
    liveInput,
    status,
    latest,
    log,
    mode,
    error,
    backendLevel,
    reportPaths,
    reportStatus,
    saveInfo,
    styleProfile,
    vibe,
    persistTr,
    persistTrRoot,
    persistDm,
    persistDmRoot,
    aiEvents,
    answerScripts,
    setLiveInput,
    setStatus,
    setLatest,
    setMode,
    setError,
    setBackendLevel,
    setReportPaths,
    setReportStatus,
    setSaveInfo,
    setStyleProfile,
    setVibe,
    setPersistTr,
    setPersistTrRoot,
    setPersistDm,
    setPersistDmRoot,
    pushAiEvent,
    setAnswerScripts,
    resetSessionState,
    connectWebSocket,
    disconnectWebSocket,
  } = useLiveConsoleStore();
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  // 引擎已固定：Small
  const [engine] = useState<'small'>('small');
  const [reportBusy, setReportBusy] = useState(false);
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([]);
  const [answerLoading, setAnswerLoading] = useState(false);
  const [answerError, setAnswerError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { balance, firstFreeUsed, setFirstFreeUsed } = useAuthStore();

  const isRunning = status?.is_running ?? false;

  useEffect(() => {
    if (collapsed) {
      const first = log[0];
      if (first && (!selectedId || !log.find((x) => x.id === selectedId))) {
        setSelectedId(first.id);
      }
    }
  }, [collapsed, log, selectedId]);

  const refreshStatus = useCallback(async () => {
    try {
      const result = await getLiveAudioStatus(FASTAPI_BASE_URL);
      setStatus(result);
      // 简洁模式：不再同步 profile 到 UI
      // sync persist settings if present（高级选项已移除）
      try {
        if ((result as any)?.advanced) {
          const a = (result as any).advanced || {};
          if (typeof a.persist_enabled === 'boolean') setPersistTr(a.persist_enabled);
          if (typeof a.persist_root === 'string') setPersistTrRoot(a.persist_root || '');
        }
      } catch {}
      // sync douyin persist
      try {
        const ds = await getDouyinRelayStatus(FASTAPI_BASE_URL);
        if (typeof (ds as any)?.persist_enabled === 'boolean') setPersistDm((ds as any).persist_enabled);
        if (typeof (ds as any)?.persist_root === 'string') setPersistDmRoot((ds as any).persist_root || '');
      } catch {}
      if (result.is_running) {
        const socket = getLiveConsoleSocket();
        if (!socket || socket.readyState === WebSocket.CLOSED || socket.readyState === WebSocket.CLOSING) {
          connectWebSocket(FASTAPI_BASE_URL);
        }
      } else {
        disconnectWebSocket();
      }
    } catch (err) {
      console.error(err);
      setError((err as Error).message ?? '获取直播音频状态失败');
    }
  }, [connectWebSocket, disconnectWebSocket, setPersistDm, setPersistDmRoot, setPersistTr, setPersistTrRoot, setStatus, setError]);

  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  useEffect(() => {
    if (!isRunning) {
      setSelectedQuestions([]);
      setAnswerError(null);
      setAnswerScripts([]);
    }
  }, [isRunning, setAnswerScripts, setAnswerError]);

  // Poll backend live status while running to update累计片段/平均置信度
  useEffect(() => {
    if (!isRunning) return;
    const id = setInterval(() => {
      getLiveAudioStatus(FASTAPI_BASE_URL)
        .then(setStatus)
        .catch(() => {});
    }, 2000);
    return () => clearInterval(id);
  }, [isRunning]);

  // 复盘状态轮询
  useEffect(() => {
    let timer: any = null;
    const poll = async () => {
      try {
        const s = await getLiveReportStatus(FASTAPI_BASE_URL);
        setReportStatus(s);
      } catch {}
    };
    poll();
    timer = setInterval(poll, 5000);
    return () => clearInterval(timer);
  }, [setReportStatus]);

  const handleStart = async () => {
    setLoading(true);
    setError(null);
    try {
      // 余额校验
      const currentBalance = Number(balance ?? 0);
      if (currentBalance <= 0) {
        if (!firstFreeUsed) {
          const res = await useFirstFreeApi();
          if (res?.success) {
            setFirstFreeUsed(true);
          } else {
            setError(res?.message || '首次免费使用失败');
            setLoading(false);
            return;
          }
        } else {
          setError('余额不足，请先前往充值或购买套餐');
          navigate('/pay/wallet');
          setLoading(false);
          return;
        }
      }

      const input = liveInput.trim();
      if (!input) throw new Error('请填写直播地址或直播间ID');
      const idMatch = input.match(/live\.douyin\.com\/([A-Za-z0-9_\-]+)/);
      const liveId = idMatch ? idMatch[1] : input;
      const liveUrl = idMatch ? input : `https://live.douyin.com/${liveId}`;

      // 1) 弹幕
      try { await startDouyinRelay(liveId, FASTAPI_BASE_URL); } catch {}
      // 默认开启弹幕持久化
      try { await updateDouyinPersist({ persist_enabled: true }, FASTAPI_BASE_URL); } catch {}
      // 2) 音频（后端固定 Small+VAD，前端不暴露专业选项）
      await startLiveAudio({ liveUrl }, FASTAPI_BASE_URL);
      connectWebSocket(FASTAPI_BASE_URL);
      // 默认开启字幕持久化
      try { await updateLiveAudioAdvanced({ persist_enabled: true }, FASTAPI_BASE_URL); } catch {}

      // 3) 录制整场（30 分钟分段）
      try { await startLiveReport(liveUrl, 30, FASTAPI_BASE_URL); } catch {}

      await refreshStatus();

      try { await stopAILiveAnalysis(FASTAPI_BASE_URL).catch(() => {}); } catch {}
      await startAILiveAnalysis({ window_sec: 30 }, FASTAPI_BASE_URL).catch(() => {});
      analysisBootRef.current = true;
      connectAIStream();

      // 4) 计算保存位置
      try {
        const day = (() => { const d = new Date(); const y=d.getFullYear(); const m=String(d.getMonth()+1).padStart(2,'0'); const dd=String(d.getDate()).padStart(2,'0'); return `${y}-${m}-${dd}`; })();
        const rootTr = (persistTrRoot && persistTrRoot.trim()) || 'records/live_logs';
        const rootDm = (persistDmRoot && persistDmRoot.trim()) || 'records/live_logs';
        const trDir = `${rootTr.replace(/\/$/, '')}/${liveId}/${day}`;
        const dmDir = `${rootDm.replace(/\/$/, '')}/${liveId}/${day}`;
        // 录制目录从 report status 读取
        setTimeout(async () => {
          try {
            const s = await getLiveReportStatus(FASTAPI_BASE_URL);
            const videoDir = s?.status?.recording_dir || '';
            setSaveInfo({ trDir, dmDir, videoDir });
          } catch { setSaveInfo({ trDir, dmDir, videoDir: '' }); }
        }, 300);
      } catch {}
    } catch (err) {
      console.error(err);
      setError((err as Error).message ?? '启动直播音频失败');
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    setError(null);
    try {
      await stopLiveAudio(FASTAPI_BASE_URL);
      try { await stopDouyinRelay(FASTAPI_BASE_URL); } catch {}
      try { await stopLiveReport(FASTAPI_BASE_URL); } catch {}
      try { await stopAILiveAnalysis(FASTAPI_BASE_URL).catch(() => {}); } catch {}
      resetSessionState();
      disconnectWebSocket();
      analysisBootRef.current = false;
    } catch (err) {
      console.error(err);
      setError((err as Error).message ?? '停止直播音频失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReportStart = async () => {
    try {
      setReportBusy(true);
      const input = liveInput.trim();
      if (!input) throw new Error('请先填写直播地址或ID');
      const idMatch = input.match(/live\.douyin\.com\/([A-Za-z0-9_\-]+)/);
      const liveId = idMatch ? idMatch[1] : input;
      const liveUrl = idMatch ? input : `https://live.douyin.com/${liveId}`;
      await startLiveReport(liveUrl, 5, FASTAPI_BASE_URL);
    } catch (e) {
      setError((e as Error).message || '启动复盘失败');
    } finally {
      setReportBusy(false);
    }
  };

  const handleReportStop = async () => {
    try {
      setReportBusy(true);
      await stopLiveReport(FASTAPI_BASE_URL);
    } catch (e) {
      setError((e as Error).message || '停止复盘失败');
    } finally {
      setReportBusy(false);
    }
  };

  const handleReportGenerate = async () => {
    try {
      setReportBusy(true);
      const res = await generateLiveReport(FASTAPI_BASE_URL);
      setReportPaths(res?.data || null);
    } catch (e) {
      setError((e as Error).message || '生成报告失败');
    } finally {
      setReportBusy(false);
    }
  };

  const modeLabel = useMemo(() => {
    const m = status?.mode || mode;
    if (m === 'sentence') return '标准';
    if (m === 'vad') return '稳态';
    return '快速';
  }, [status?.mode, mode]);

  const engineLabel = useMemo(() => '轻量', []);
  // AI 实时分析流（SSE，带鉴权）
  const aiSourceRef = useRef<EventSource | null>(null);
  const analysisBootRef = useRef(false);
  const normalizeAiEvent = useCallback((payload: any, timestamp?: number) => {
    if (!payload || typeof payload !== 'object') {
      return {
        summary: typeof payload === 'string' ? payload : '',
        raw: payload,
        timestamp: timestamp ?? Date.now(),
      };
    }
    const card = payload.analysis_card && typeof payload.analysis_card === 'object'
      ? payload.analysis_card
      : null;
    const toArray = (value: any): any[] => (Array.isArray(value) ? value : []);
    const chooseList = (primary: any, fallback: any): any[] => {
      const primaryArr = toArray(primary);
      if (primaryArr.length) return primaryArr;
      return toArray(fallback);
    };
    const summaryText = payload.summary && String(payload.summary).trim().length
      ? payload.summary
      : (card?.analysis_overview || '');
    const normalized: any = {
      ...payload,
      summary: summaryText,
      highlight_points: chooseList(payload.highlight_points, card?.engagement_highlights),
      risks: chooseList(payload.risks, card?.risks),
      suggestions: chooseList(payload.suggestions, card?.next_actions),
      top_questions: toArray(payload.top_questions),
      analysis_focus: payload.analysis_focus || '',
      audience_sentiment: card && typeof card === 'object' ? card.audience_sentiment || null : null,
      analysis_card: card || undefined,
      timestamp: timestamp ?? Date.now(),
    };
    if (payload.answer_scripts !== undefined) {
      normalized.answer_scripts = toArray(payload.answer_scripts);
    }
    return normalized;
  }, []);

  const connectAIStream = useCallback(() => {
    if (aiSourceRef.current) return;
    // 使用统一的鉴权 SSE 流
    const es = openAILiveStream(
      (ev) => {
        try {
          const data = JSON.parse(ev.data);
          if (data?.type === 'ai') {
            if (data.payload) {
              const normalized = normalizeAiEvent(data.payload, data.timestamp);
              pushAiEvent(normalized);
              const p = normalized || {};
              if (p.style_profile) setStyleProfile(p.style_profile);
              if (p.vibe) setVibe(p.vibe);
              if (Array.isArray(p.answer_scripts)) {
                setAnswerScripts(p.answer_scripts);
              }
            }
            // 若分析结果包含风格/氛围，更新快照，便于 UI 展示与后续生成复用
          }
        } catch {}
      },
      () => {
        // 错误处理：关闭并重连
        try { if (aiSourceRef.current) aiSourceRef.current.close(); } catch {}
        aiSourceRef.current = null;
        setTimeout(connectAIStream, 1500);
      },
      FASTAPI_BASE_URL
    );
    aiSourceRef.current = es;
  }, [normalizeAiEvent, pushAiEvent, setStyleProfile, setVibe, setAnswerScripts]);

  useEffect(() => {
    if (isRunning) {
      if (!analysisBootRef.current) {
        startAILiveAnalysis({ window_sec: 30 }, FASTAPI_BASE_URL).catch(() => {});
        analysisBootRef.current = true;
      }
      connectAIStream();
    } else {
      analysisBootRef.current = false;
      try { stopAILiveAnalysis(FASTAPI_BASE_URL).catch(() => {}); } catch {}
      if (aiSourceRef.current) { aiSourceRef.current.close(); aiSourceRef.current = null; }
    }
    return () => {
      if (!isRunning && aiSourceRef.current) {
        aiSourceRef.current.close();
        aiSourceRef.current = null;
      }
    };
  }, [isRunning, connectAIStream]);

  const handleCopyAnswer = useCallback(async (text: string) => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      console.error('复制话术失败', err);
    }
  }, []);

  const handleSelectQuestion = useCallback((entry: { content: string }) => {
    const text = String(entry?.content || '').trim();
    if (!text) return;
    setSelectedQuestions((prev) => {
      if (prev.includes(text)) return prev;
      const next = [text, ...prev];
      return next.slice(0, 5);
    });
    setAnswerError(null);
  }, [setSelectedQuestions, setAnswerError]);

  const handleRemoveQuestion = useCallback((question: string) => {
    setSelectedQuestions((prev) => prev.filter((q) => q !== question));
  }, [setSelectedQuestions]);

  const handleClearQuestions = useCallback(() => {
    setSelectedQuestions([]);
    setAnswerError(null);
  }, [setSelectedQuestions, setAnswerError]);

  const handleGenerateAnswers = useCallback(async () => {
    if (!selectedQuestions.length) {
      setAnswerError('请先选择至少一个弹幕问题');
      return;
    }
    try {
      setAnswerLoading(true);
      setAnswerError(null);
      const transcriptSnippet = log
        .slice(0, 6)
        .reverse()
        .map((item) => item.text)
        .filter(Boolean)
        .join('\n');
      const payload: any = {
        questions: selectedQuestions,
      };
      if (transcriptSnippet) payload.transcript = transcriptSnippet;
      if (styleProfile) payload.style_profile = styleProfile;
      if (vibe) payload.vibe = vibe;
      const res = await generateAnswerScripts(payload, FASTAPI_BASE_URL);
      const scripts = res?.data?.scripts || [];
      setAnswerScripts(scripts);
    } catch (err) {
      setAnswerError((err as Error)?.message || '生成失败，请稍后再试');
    } finally {
      setAnswerLoading(false);
    }
  }, [selectedQuestions, log, styleProfile, vibe, setAnswerScripts, FASTAPI_BASE_URL]);

  // --------------- State persistence ---------------
  return (
    <div className="space-y-6">
      <div className="timao-soft-card flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-4">
          <div className="text-4xl">📡</div>
          <div>
            <div className="text-lg font-semibold text-purple-600">实时字幕</div>
            <div className="text-sm timao-support-text">{isRunning ? '运行中' : '未开始'}</div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <input
            value={liveInput}
            onChange={(event) => setLiveInput(event.target.value)}
            className="timao-input w-64 text-sm"
            placeholder="直播地址或ID (e.g. https://live.douyin.com/xxxx)"
            disabled={isRunning || loading}
          />
          {/* 简洁模式：不暴露“预设”选择，保持默认策略 */}
          {/* 模式/引擎固定：稳妥（VAD）· 轻量（Small） */}
          <button className="timao-primary-btn" onClick={handleStart} disabled={loading || isRunning}>
            {loading ? '处理中...' : isRunning ? '运行中' : '开始转写'}
          </button>
          <button className="timao-outline-btn" onClick={handleStop} disabled={loading || !isRunning}>
            停止
          </button>
        </div>
      </div>

      {error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.2fr_1.2fr_0.8fr] lg:grid-cols-[1fr_1fr]">
        <section className="timao-card h-full flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
              <span>📝</span>
              语音转写流
            </h3>
            <div className="flex items-center gap-3">
              <span className="timao-status-pill text-xs">{isRunning ? '实时更新中' : '已暂停'}</span>
              <button
                className="text-xs timao-support-text hover:text-purple-600"
                onClick={() => setCollapsed((v) => !v)}
                title={collapsed ? '展开' : '折叠'}
              >
                {collapsed ? '展开 ▾' : '折叠 ▸'}
              </button>
            </div>
          </div>
          {collapsed ? (
            <div className="space-y-2">
              <select
                id="transcript-select"
                className="timao-input w-full"
                value={selectedId ?? (log[0]?.id || '')}
                onChange={(e) => setSelectedId(e.target.value || null)}
                aria-label="选择转写记录"
                title="选择转写记录"
              >
                {log.length === 0 ? (
                  <option value="">暂无转写</option>
                ) : (
                  log.map((item) => (
                    <option key={item.id} value={item.id}>
                      {new Date(item.timestamp * 1000).toLocaleTimeString()} · {(item.text || '').slice(0, 24)}
                    </option>
                  ))
                )}
              </select>
              <div className="rounded-xl bg-white/90 border p-3 text-sm text-slate-700 min-h-[48px]">
                {(() => {
                  const found = log.find((x) => x.id === (selectedId ?? log[0]?.id));
                  return found ? found.text : '暂无转写结果';
                })()}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col">
            {/* 固定高度，列表支持滚动；与右侧卡片齐平 */}
            <div className="space-y-3 overflow-y-auto pr-1 flex-1 min-h-[360px] max-h-[360px]">
              {log.length === 0 ? (
                <div className="timao-outline-card text-sm timao-support-text text-center">
                  暂无转写结果。{isRunning ? '等待识别...' : '点击开始转写以开启实时字幕。'}
                </div>
              ) : (
                log.map((item) => (
                  <div key={item.id} className="rounded-2xl border border-white/60 shadow-md p-4 bg-white/95">
                      <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                        <span>{new Date(item.timestamp * 1000).toLocaleTimeString()}</span>
                      </div>
                      <div className="text-slate-600 text-sm leading-relaxed">{item.text}</div>
                    </div>
                ))
              )}
            </div>
            </div>
          )}
        </section>

        <section className="flex flex-col gap-4">
          {/* AI 分析卡片：固定 60 秒窗口自动刷新 */}
          <div className="timao-card">
            <div className="flex items-center gap-2 mb-3">
              <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
                <span>🧠</span>
                直播分析卡片
              </h3>
              <span className="text-xs timao-support-text">系统默认每 60 秒更新一次</span>
            </div>
            {aiEvents.length === 0 ? (
              <div className="timao-outline-card text-sm timao-support-text">{isRunning ? '正在生成直播分析卡片…（开始字幕后约 1 分钟内出现结果）' : '请先在上方开始实时字幕'}
              </div>
            ) : (
              <div className="space-y-3 max-h-[260px] overflow-y-auto pr-1">
                {aiEvents.map((ev, idx) => {
                  const sentiment = ev?.audience_sentiment
                    || (ev?.analysis_card && typeof ev.analysis_card === 'object' ? ev.analysis_card.audience_sentiment : null);
                  const sentimentSignals = Array.isArray(sentiment?.signals) ? sentiment.signals : [];
                  const hasAny = ev?.summary
                    || (Array.isArray(ev?.highlight_points) && ev.highlight_points.length)
                    || (Array.isArray(ev?.risks) && ev.risks.length)
                    || (Array.isArray(ev?.suggestions) && ev.suggestions.length)
                    || (Array.isArray(ev?.top_questions) && ev.top_questions.length)
                    || (sentiment && (sentiment.label || sentimentSignals.length))
                    || ev?.analysis_focus
                    || ev?.error || ev?.raw;
                  return (
                    <div key={idx} className="rounded-2xl border border-white/60 shadow-md p-3 bg-white/95">
                      {ev?.error ? (
                        <div className="text-xs text-red-600">AI 分析错误：{String(ev.error)}</div>
                      ) : null}
                      {ev?.raw && !ev?.summary ? (
                        <div className="text-xs text-slate-500 whitespace-pre-wrap">{String(ev.raw)}</div>
                      ) : null}
                      {ev?.summary ? (
                        <div className="text-sm text-slate-700 mb-2 whitespace-pre-wrap">{ev.summary}</div>
                      ) : null}
                      {ev?.analysis_focus ? (
                        <div className="text-xs text-purple-600 mb-2">关注点：{ev.analysis_focus}</div>
                      ) : null}
                      {Array.isArray(ev?.highlight_points) && ev.highlight_points.length ? (
                        <>
                          <div className="text-xs text-slate-500 mb-1">亮点</div>
                          <ul className="list-disc pl-5 text-xs text-slate-600">
                            {ev.highlight_points.slice(0, 4).map((x: any, i: number) => (<li key={i}>{String(x)}</li>))}
                          </ul>
                        </>
                      ) : null}
                      {Array.isArray(ev?.risks) && ev.risks.length ? (
                        <>
                          <div className="text-xs text-slate-500 mt-2 mb-1">风险</div>
                          <ul className="list-disc pl-5 text-xs text-slate-600">
                            {ev.risks.slice(0, 4).map((x: any, i: number) => (<li key={i}>{String(x)}</li>))}
                          </ul>
                        </>
                      ) : null}
                      {sentiment && (sentiment.label || sentimentSignals.length) ? (
                        <>
                          <div className="text-xs text-slate-500 mt-2 mb-1">观众情绪</div>
                          <div className="text-xs text-slate-600">
                            状态：{sentiment.label || '—'}
                          </div>
                          {sentimentSignals.length ? (
                            <ul className="list-disc pl-5 text-xs text-slate-600 mt-1">
                              {sentimentSignals.slice(0, 4).map((x: any, i: number) => (<li key={i}>{String(x)}</li>))}
                            </ul>
                          ) : null}
                        </>
                      ) : null}
                      {Array.isArray(ev?.suggestions) && ev.suggestions.length ? (
                        <>
                          <div className="text-xs text-slate-500 mt-2 mb-1">建议</div>
                          <ul className="list-disc pl-5 text-xs text-slate-600">
                            {ev.suggestions.slice(0, 4).map((x: any, i: number) => (<li key={i}>{String(x)}</li>))}
                          </ul>
                        </>
                      ) : null}
                      {Array.isArray(ev?.top_questions) && ev.top_questions.length ? (
                        <>
                          <div className="text-xs text-slate-500 mt-2 mb-1">高频问题</div>
                          <ul className="list-disc pl-5 text-xs text-slate-600">
                            {ev.top_questions.slice(0, 4).map((x: any, i: number) => (<li key={i}>{String(x)}</li>))}
                          </ul>
                        </>
                      ) : null}
                      {!hasAny ? (
                        <div className="text-xs text-slate-400">暂无可显示内容</div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* 风格画像与氛围 */}
          <div className="timao-card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
                <span>🎛️</span>
                风格画像与氛围
              </h3>
            </div>
            {(!styleProfile && !vibe) ? (
              <div className="timao-outline-card text-xs timao-support-text">{isRunning ? '正在学习主播风格与氛围…' : '开始实时字幕后自动学习'}</div>
            ) : (
              <div className="grid grid-cols-1 gap-3">
                {styleProfile ? (
                  <div className="rounded-xl bg-white/90 border p-3">
                    <div className="text-xs text-slate-500 mb-1">风格画像</div>
                    <div className="text-xs text-slate-600">
                      <div>人物：{String(styleProfile.persona ?? '—')}</div>
                      <div>语气：{String(styleProfile.tone ?? '—')} · 节奏：{String(styleProfile.tempo ?? '—')} · 用词：{String(styleProfile.register ?? '—')}</div>
                      {Array.isArray(styleProfile.catchphrases) && styleProfile.catchphrases.length ? (
                        <div>口头禅：{styleProfile.catchphrases.slice(0, 4).join('、')}</div>
                      ) : null}
                      {Array.isArray(styleProfile.slang) && styleProfile.slang.length ? (
                        <div>俚语：{styleProfile.slang.slice(0, 4).join('、')}</div>
                      ) : null}
                    </div>
                  </div>
                ) : null}
                {vibe ? (
                  <div className="rounded-xl bg-white/90 border p-3">
                    <div className="text-xs text-slate-500 mb-1">直播间氛围</div>
                    <div className="text-xs text-slate-600">热度：{String(vibe.level ?? '—')} · 分数：{String(vibe.score ?? '—')}</div>
                  </div>
                ) : null}
              </div>
            )}
          </div>

          <div className="timao-card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
                <span>🗣️</span>
                智能话术建议
              </h3>
              <span className="text-xs timao-support-text">在弹幕中点“生成答疑话术”即可添加</span>
            </div>
            <div className="space-y-3">
              <div>
                <div className="text-xs text-slate-500 mb-1">已选问题</div>
                {selectedQuestions.length ? (
                  <ul className="space-y-2">
                    {selectedQuestions.map((q) => (
                      <li key={q} className="flex items-start justify-between gap-3 rounded-xl border bg-white/90 px-3 py-2 text-xs text-slate-600">
                        <span className="flex-1 leading-relaxed">{q}</span>
                        <button
                          className="timao-support-text text-[11px] hover:text-rose-500"
                          onClick={() => handleRemoveQuestion(q)}
                          title="移除该问题"
                        >
                          移除
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="timao-outline-card text-xs timao-support-text">
                    在实时弹幕列表中点击对应按钮，即可将问题加入这里。
                  </div>
                )}
                <div className="mt-3 flex items-center gap-2">
                  <button
                    className="timao-primary-btn text-xs"
                    onClick={handleGenerateAnswers}
                    disabled={!selectedQuestions.length || answerLoading || !isRunning}
                  >
                    {answerLoading ? '生成中…' : '生成话术'}
                  </button>
                  <button
                    className="timao-outline-btn text-xs"
                    onClick={handleClearQuestions}
                    disabled={!selectedQuestions.length || answerLoading}
                  >
                    清空
                  </button>
                </div>
                {answerError ? (
                  <div className="mt-2 text-xs text-rose-500">{answerError}</div>
                ) : null}
              </div>

              <div>
                <div className="text-xs text-slate-500 mb-1">生成结果</div>
                {Array.isArray(answerScripts) && answerScripts.length ? (
                  <div className="space-y-3">
                    {answerScripts.slice(0, 3).map((item, idx) => (
                      <div key={idx} className="rounded-xl bg-white/90 border p-3 text-xs text-slate-600 space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          {item?.question ? (
                            <span className="text-[11px] text-purple-500">
                              问：{String(item.question)}
                            </span>
                          ) : null}
                          {item?.style ? (
                            <span className="rounded-full border border-purple-200 bg-purple-50 px-2 py-[1px] text-[10px] text-purple-600">
                              {String(item.style)}
                            </span>
                          ) : null}
                        </div>
                        <div className="text-sm text-slate-800 leading-relaxed">
                          {String(item?.line || '')}
                        </div>
                        <div className="flex items-center justify-between">
                          {item?.notes ? (
                            <span className="text-[11px] text-slate-400">{String(item.notes)}</span>
                          ) : <span />}
                          <button
                            className="timao-outline-btn text-[11px] px-2 py-0.5"
                            onClick={() => handleCopyAnswer(String(item?.line || ''))}
                            title="复制话术"
                          >
                            复制
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="timao-outline-card text-xs timao-support-text">
                    生成后的话术会展示在此，帮助你用主播语气快速回复观众。
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="timao-card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
                <span>📶</span>
                声音输入
              </h3>
              <span className="text-xs timao-support-text">{Math.round(backendLevel * 100)}%</span>
            </div>
            <progress
              className="w-full h-2"
              value={Math.round(backendLevel * 100)}
              max={100}
              aria-label="声音输入电平"
            />
          </div>

          <div className="timao-card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
                <span>💡</span>
                实时字幕
              </h3>
            </div>
            <div className="rounded-2xl bg-purple-50/80 border border-purple-100 px-4 py-3 text-slate-700 min-h-[72px] flex items-center">
              {latest?.text ? latest.text : '等待识别结果...'}
            </div>
            {latest ? (
              <div className="flex items-center justify-between text-xs text-slate-400 mt-3">
              <span>时间 {new Date(latest.timestamp * 1000).toLocaleTimeString()}</span>
                <button
                  className="timao-outline-btn text-[10px] px-2 py-0.5"
                  title="复制JSON"
                  onClick={() => {
                    try {
                      const payload = {
                        type: 'transcription',
                        text: latest.text,
                        confidence: latest.confidence,
                        timestamp: latest.timestamp,
                        is_final: latest.isFinal,
                        words: latest.words || [],
                        speaker: latest.speaker || '?',
                        room_id: (status as any)?.live_id || null,
                        session_id: (status as any)?.session_id || null,
                      };
                      (window as any).utils?.copyToClipboard(JSON.stringify(payload, null, 2));
                    } catch {}
                  }}
                >复制JSON</button>
              </div>
            ) : null}
            {latest?.words?.length ? (
              <div className="mt-2 flex flex-wrap gap-1">
                {latest.words.map((w, i) => (
                  <span key={i} className="px-1.5 py-0.5 rounded bg-white/90 border text-xs text-slate-600">
                    {w.word}
                    <span className="ml-1 text-[10px] text-slate-400">{w.start.toFixed(2)}–{w.end.toFixed(2)}s</span>
                  </span>
                ))}
              </div>
            ) : null}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="timao-soft-card">
              <div className="text-sm text-slate-500 mb-1">当前会话</div>
              <div className="text-lg font-semibold text-purple-600">{status?.session_id ?? '—'}</div>
              <div className="text-xs timao-support-text mt-2">
                已累计片段 {status?.stats?.total_audio_chunks ?? 0} · 成功转写 {status?.stats?.successful_transcriptions ?? 0}
              </div>
            </div>
            {saveInfo ? (
              <div className="timao-soft-card">
                <div className="text-sm text-slate-500 mb-1">保存位置</div>
                <div className="flex items-center gap-2 text-xs timao-support-text break-all">
                  <span>字幕：{saveInfo.trDir || '—'}</span>
                  {saveInfo.trDir ? (
                    <button className="timao-outline-btn text-[10px] px-2 py-0.5" onClick={() => {
                      try { (window as any).electronAPI?.openPath(saveInfo.trDir); } catch {}
                    }}>打开</button>
                  ) : null}
                </div>
                <div className="flex items-center gap-2 text-xs timao-support-text break-all mt-1">
                  <span>弹幕：{saveInfo.dmDir || '—'}</span>
                  {saveInfo.dmDir ? (
                    <button className="timao-outline-btn text-[10px] px-2 py-0.5" onClick={() => {
                      try { (window as any).electronAPI?.openPath(saveInfo.dmDir); } catch {}
                    }}>打开</button>
                  ) : null}
                </div>
                <div className="flex items-center gap-2 text-xs timao-support-text break-all mt-1">
                  <span>视频：{saveInfo.videoDir || '—'}</span>
                  {saveInfo.videoDir ? (
                    <button className="timao-outline-btn text-[10px] px-2 py-0.5" onClick={() => {
                      try { (window as any).electronAPI?.openPath(saveInfo.videoDir); } catch {}
                    }}>打开</button>
                  ) : null}
                </div>
              </div>
            ) : null}
          </div>
        </section>

        <section className="flex flex-col gap-4">
          <div className="timao-card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
                <span>🧾</span>
                整场回顾
              </h3>
              <button className="timao-primary-btn" onClick={handleReportGenerate} disabled={reportBusy}>生成回顾</button>
            </div>
            <div className="text-xs timao-support-text mt-1">已自动录制 · 每段约 30 分钟</div>
            <div className="text-xs timao-support-text mt-1">
              状态：{reportStatus?.active ? '录制中' : '未开始'}
              {reportStatus?.status?.segments?.length ? ` · 片段 ${reportStatus.status.segments.length}` : ''}
            </div>
            {reportPaths ? (
              <div className="mt-3 text-xs timao-support-text">
                <div>· 弹幕：{reportPaths.comments || '—'}</div>
                <div>· 转写：{reportPaths.transcript || '—'}</div>
                <div className="flex items-center gap-2">· 报告：{reportPaths.report || '—'}
                  {reportPaths.report ? (
                    <button className="timao-outline-btn text-[10px] px-2 py-0.5" onClick={() => {
                      try { (window as any).electronAPI?.openPath(reportPaths.report as string); } catch {}
                    }}>打开</button>
                  ) : null}
                </div>
              </div>
            ) : null}
          </div>

          {/* 简洁模式：移除服务状态高级设置卡片 */}

          <div className="timao-card">
            <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2 mb-3">
              <span>📎</span>
              使用提示
            </h3>
            <ul className="space-y-2 text-sm timao-support-text">
              <li>· 无需麦克风权限，直接从直播流抓取音频。</li>
              <li>· 需安装 ffmpeg 并确保可执行路径可用。</li>
              <li>· 若启动失败，请查看日志或终端输出。</li>
            </ul>
          </div>
        </section>
      </div>

      <DouyinRelayPanel baseUrl={FASTAPI_BASE_URL} onSelectQuestion={handleSelectQuestion} />
    </div>
  );
};

export default LiveConsolePage;
