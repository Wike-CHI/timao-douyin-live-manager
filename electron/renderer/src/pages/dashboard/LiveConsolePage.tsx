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
import { startAILiveAnalysis, stopAILiveAnalysis, openAILiveStream, generateOneScript } from '../../services/ai';
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
    confSum,
    confCount,
    reportPaths,
    reportStatus,
    saveInfo,
    aiWindowSec,
    styleProfile,
    vibe,
    oneScript,
    oneType,
    persistTr,
    persistTrRoot,
    persistDm,
    persistDmRoot,
    aiEvents,
    setLiveInput,
    setStatus,
    setLatest,
    setMode,
    setError,
    setBackendLevel,
    setReportPaths,
    setReportStatus,
    setSaveInfo,
    setAiWindowSec,
    setStyleProfile,
    setVibe,
    setOneScript,
    setOneType,
    setPersistTr,
    setPersistTrRoot,
    setPersistDm,
    setPersistDmRoot,
    pushAiEvent,
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
  // 一句话术即时生成
  const [genBusy, setGenBusy] = useState(false);

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
      // 默认开启字幕持久化
      try { await updateLiveAudioAdvanced({ persist_enabled: true }, FASTAPI_BASE_URL); } catch {}

      // 3) 录制整场（30 分钟分段）
      try { await startLiveReport(liveUrl, 30, FASTAPI_BASE_URL); } catch {}

      await refreshStatus();

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
      resetSessionState();
      disconnectWebSocket();
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

  const formattedCountdown = useMemo(() => {
    if (!isRunning) return '暂停';
    return '运行中';
  }, [isRunning]);

  const modeLabel = useMemo(() => {
    const m = status?.mode || mode;
    if (m === 'sentence') return '标准';
    if (m === 'vad') return '稳态';
    return '快速';
  }, [status?.mode, mode]);

  const engineLabel = useMemo(() => '轻量', []);
  // AI 实时分析流（SSE，带鉴权）
  const aiSourceRef = useRef<EventSource | null>(null);
  const connectAIStream = useCallback(() => {
    if (aiSourceRef.current) return;
    // 使用统一的鉴权 SSE 流
    const es = openAILiveStream(
      (ev) => {
        try {
          const data = JSON.parse(ev.data);
          if (data?.type === 'ai') {
            if (data.payload) pushAiEvent(data.payload);
            // 若分析结果包含风格/氛围，更新快照，便于 UI 展示与后续生成复用
            const p = data.payload || {};
            if (p.style_profile) setStyleProfile(p.style_profile);
            if (p.vibe) setVibe(p.vibe);
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
  }, [pushAiEvent, setStyleProfile, setVibe]);

  useEffect(() => {
    if (isRunning) {
      const ws = Math.max(30, Math.min(600, Number(aiWindowSec) || 60));
      // 使用统一的鉴权接口启动 AI 分析
      startAILiveAnalysis({ window_sec: ws }, FASTAPI_BASE_URL).catch(() => {});
      connectAIStream();
    } else {
      try { stopAILiveAnalysis(FASTAPI_BASE_URL).catch(() => {}); } catch {}
      if (aiSourceRef.current) { aiSourceRef.current.close(); aiSourceRef.current = null; }
    }
    return () => { if (aiSourceRef.current) { aiSourceRef.current.close(); aiSourceRef.current = null; } };
  }, [isRunning, connectAIStream]);

  // 生成一句话术（调用后端，自动带入 style_profile/vibe，使用统一鉴权）
  const handleGenerateOne = useCallback(async () => {
    try {
      setGenBusy(true);
      setOneScript('');
      const res = await generateOneScript(
        { script_type: oneType, include_context: true },
        FASTAPI_BASE_URL
      );
      const text = res?.data?.content || '';
      if (text) setOneScript(String(text));
    } catch (e) {
      console.error(e);
      setOneScript('生成失败，请稍后再试');
    } finally {
      setGenBusy(false);
    }
  }, [oneType, setOneScript]);

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
            <>
            {/* 固定高度+滚动条，避免内容撑高页面；数据不做上限裁剪 */}
            <div className="space-y-3 overflow-y-auto pr-1 max-h-[360px]">
              {log.length === 0 ? (
                <div className="timao-outline-card text-sm timao-support-text text-center">
                  暂无转写结果。{isRunning ? '等待识别...' : '点击开始转写以开启实时字幕。'}
                </div>
              ) : (
                log.map((item) => (
                  <div key={item.id} className="rounded-2xl border border-white/60 shadow-md p-4 bg-white/95">
                    <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                      <span>{new Date(item.timestamp * 1000).toLocaleTimeString()}</span>
                      <div className="flex items-center gap-2">
                        <span>稳定度 {(item.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                    <div className="text-slate-600 text-sm leading-relaxed">{item.text}</div>
                  </div>
                ))
              )}
            </div>
            </>
          )}
        </section>

        <section className="flex flex-col gap-4">
          {/* AI 分析卡片：常显，并允许设置分析窗口（秒） */}
          <div className="timao-card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
                <span>🧠</span>
                直播助手
              </h3>
              <div className="flex items-center gap-2">
                <span className="text-xs timao-support-text">分析窗口</span>
                <input
                  type="number"
                  min={30}
                  max={600}
                  step={10}
                  className="timao-input w-20 text-xs"
                  value={aiWindowSec}
                  onChange={(e) => setAiWindowSec(Math.max(30, Math.min(600, Number(e.target.value) || 60)))}
                  title="每次AI汇总的时间窗口（30-600秒）"
                />
                <span className="text-xs timao-support-text">秒</span>
                <button
                  className="timao-outline-btn text-xs"
                  onClick={async () => {
                    // 应用新的分析窗口：重启 AI 分析服务并重连 SSE（使用统一鉴权）
                    try { await stopAILiveAnalysis(FASTAPI_BASE_URL).catch(() => {}); } catch {}
                    const ws = Math.max(30, Math.min(600, Number(aiWindowSec) || 60));
                    try {
                      await startAILiveAnalysis({ window_sec: ws }, FASTAPI_BASE_URL).catch(() => {});
                    } catch {}
                    try { if (aiSourceRef.current) { aiSourceRef.current.close(); aiSourceRef.current = null; } } catch {}
                    connectAIStream();
                  }}
                  disabled={!isRunning}
                  title={isRunning ? '应用后，下一个窗口生效' : '请先开始实时字幕'}
                >应用</button>
              </div>
            </div>
            {aiEvents.length === 0 ? (
              <div className="timao-outline-card text-sm timao-support-text">{isRunning ? '正在分析直播内容…（开始字幕后，约 1 分钟出现建议）' : '请先在上方开始实时字幕'}
              </div>
            ) : (
              <div className="space-y-3 max-h-[260px] overflow-y-auto pr-1">
                {aiEvents.map((ev, idx) => {
                  const hasAny = ev?.summary || (Array.isArray(ev?.highlight_points) && ev.highlight_points.length)
                    || (Array.isArray(ev?.risks) && ev.risks.length)
                    || (Array.isArray(ev?.suggestions) && ev.suggestions.length)
                    || (Array.isArray(ev?.top_questions) && ev.top_questions.length)
                    || (Array.isArray(ev?.scripts) && ev.scripts.length)
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
                        <div className="text-sm text-slate-700 mb-2">{ev.summary}</div>
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
                      {Array.isArray(ev?.scripts) && ev.scripts.length ? (
                        <>
                          <div className="text-xs text-slate-500 mt-2 mb-1">可用话术</div>
                          <ul className="list-disc pl-5 text-xs text-slate-600">
                            {ev.scripts.slice(0, 3).map((s: any, i: number) => (
                              <li key={i}>{String(s?.text || s)}</li>
                            ))}
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

          {/* 风格画像与氛围 + 一句话术 */}
          <div className="timao-card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
                <span>🎛️</span>
                风格画像与氛围
              </h3>
              <div className="flex items-center gap-2">
                <select className="timao-input text-xs" value={oneType} onChange={(e) => setOneType(e.target.value)} title="话术类型">
                  <option value="interaction">互动</option>
                  <option value="call_to_action">召唤</option>
                  <option value="transition">转场</option>
                  <option value="clarification">澄清</option>
                  <option value="humor">幽默</option>
                  <option value="welcome">欢迎</option>
                  <option value="closing">收尾</option>
                  <option value="question">答疑</option>
                  <option value="emotion">情绪</option>
                  <option value="product">产品</option>
                </select>
                <button className="timao-primary-btn text-xs" onClick={handleGenerateOne} disabled={genBusy} title="根据当前风格与氛围生成一句话术">
                  {genBusy ? '生成中…' : '生成一句话术'}
                </button>
              </div>
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
                {oneScript ? (
                  <div className="rounded-xl bg-purple-50/80 border border-purple-100 p-3">
                    <div className="text-xs text-slate-500 mb-1">临时话术</div>
                    <div className="text-sm text-slate-700">{oneScript}</div>
                  </div>
                ) : null}
              </div>
            )}
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
              <span className="text-xs timao-support-text">{formattedCountdown}</span>
            </div>
            <div className="rounded-2xl bg-purple-50/80 border border-purple-100 px-4 py-3 text-slate-700 min-h-[72px] flex items-center">
              {latest?.text ? latest.text : '等待识别结果...'}
            </div>
            {latest ? (
              <div className="flex items-center justify-between text-xs text-slate-400 mt-3">
              <span>时间 {new Date(latest.timestamp * 1000).toLocaleTimeString()} · 稳定度 {(latest.confidence * 100).toFixed(0)}%</span>
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
            <div className="timao-soft-card">
              <div className="text-sm text-slate-500 mb-1">平均置信度</div>
              <div className="text-lg font-semibold text-purple-600">{
                (() => {
                  const backendAvg = Number(status?.stats?.average_confidence || 0);
                  const localAvg = confCount > 0 ? confSum / confCount : 0;
                  const pick = backendAvg > 0 ? backendAvg : localAvg;
                  return pick.toFixed(2);
                })()
              }</div>
              <div className="text-xs timao-support-text mt-2">失败次数 {status?.stats?.failed_transcriptions ?? 0}</div>
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

      <DouyinRelayPanel baseUrl={FASTAPI_BASE_URL} />
    </div>
  );
};

export default LiveConsolePage;
