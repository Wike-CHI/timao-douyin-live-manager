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
import { startAILiveAnalysis, stopAILiveAnalysis, openAILiveStream, generateAnswerScripts } from '../../services/ai';
import { useLiveConsoleStore, getLiveConsoleSocket } from '../../store/useLiveConsoleStore';

// Note: Do not cap transcript items; persist to disk is handled by backend.
// We keep full in-memory log for current session (may grow large for long sessions).
const FASTAPI_BASE_URL = (import.meta.env?.VITE_FASTAPI_URL as string | undefined) || 'http://127.0.0.1:10090';

const LiveConsolePage = () => {
  const [showSaveInfo, setShowSaveInfo] = useState(false);
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
  const [agcEnabled, setAgcEnabled] = useState<boolean>(true);
  const [agcGain, setAgcGain] = useState<number>(1);
  const [diarizationEnabled, setDiarizationEnabled] = useState<boolean>(true);
  const [maxSpeakers, setMaxSpeakers] = useState<number>(2);
  const [lastSpeaker, setLastSpeaker] = useState<string>('unknown');
  const [douyinStatus, setDouyinStatus] = useState<any>(null);
  const [douyinConnected, setDouyinConnected] = useState<boolean>(false);
  const navigate = useNavigate();
  const { isPaid } = useAuthStore();

  const isRunning = status?.is_running ?? false;
  const generatingRef = useRef(false);

  const speakerLabelShort = useCallback((value?: string | null) => {
    if (!value) return '未识别';
    const norm = String(value).toLowerCase();
    if (norm === 'host') return '主播';
    if (norm === 'guest') return '嘉宾';
    if (norm === 'unknown' || norm === 'neutral' || norm === 'undefined' || norm === 'null') return '未识别';
    return `嘉宾(${value})`;
  }, []);

  const renderSpeakerBadge = useCallback(
    (value?: string | null) => {
      const label = speakerLabelShort(value);
      if (!label) return null;
      const norm = String(value || '').toLowerCase();
      const isHost = norm === 'host';
      const isUnknown = !norm || norm === 'unknown' || norm === 'neutral' || norm === 'undefined' || norm === 'null';
      const tone = isUnknown
        ? 'bg-slate-100 text-slate-500'
        : isHost
          ? 'bg-purple-100 text-purple-600'
          : 'bg-amber-100 text-amber-600';
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${tone}`}>
          {label}
        </span>
      );
    },
    [speakerLabelShort]
  );

  const formatSpeakerDebug = useCallback((dbg?: Record<string, number>) => {
    if (!dbg) return '';
    return Object.entries(dbg)
      .filter(([, value]) => typeof value === 'number' && Number.isFinite(value))
      .slice(0, 4)
      .map(([key, value]) => `${key}:${Number(value).toFixed(2)}`)
      .join(' · ');
  }, []);

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
      
      // 获取抖音直播间状态
      try {
        const douyinResult = await getDouyinRelayStatus(FASTAPI_BASE_URL);
        // 应用重启后不保留上次直播间信息：当未运行时，清空 live_id/room_id
        const normalized = douyinResult?.is_running
          ? douyinResult
          : { ...douyinResult, live_id: null, room_id: null };
        setDouyinStatus(normalized);
        setDouyinConnected(!!normalized.is_running);
      } catch (err) {
        console.error('获取抖音状态失败:', err);
        setDouyinStatus(null);
        setDouyinConnected(false);
      }
      
      // 简洁模式：不再同步 profile 到 UI
      // sync persist settings if present（高级选项已移除）
      try {
        if ((result as any)?.advanced) {
          const a = (result as any).advanced || {};
          if (typeof a.persist_enabled === 'boolean') setPersistTr(a.persist_enabled);
          if (typeof a.persist_root === 'string') setPersistTrRoot(a.persist_root || '');
          if (typeof a.agc_enabled === 'boolean') setAgcEnabled(a.agc_enabled);
          if (typeof a.agc_gain === 'number') setAgcGain(Number(a.agc_gain));
          if (typeof a.diarizer_active === 'boolean') setDiarizationEnabled(a.diarizer_active);
          if (typeof a.max_speakers === 'number' && a.max_speakers >= 1) setMaxSpeakers(a.max_speakers);
          if (typeof a.last_speaker === 'string') setLastSpeaker(a.last_speaker);
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

  // 移除基于 isRunning 的自动清空，避免瞬时抖动导致首次点击被清空
  // useEffect(() => {
  //   if (!isRunning) {
  //     setSelectedQuestions([]);
  //     setAnswerError(null);
  //     setAnswerScripts([]);
  //   }
  // }, [isRunning, setAnswerScripts, setAnswerError]);

  // Poll backend live status while running to update累计片段/平均置信度
  useEffect(() => {
    if (!isRunning) return;
    const id = setInterval(() => {
      getLiveAudioStatus(FASTAPI_BASE_URL)
        .then(setStatus)
        .catch(() => {});
      // 同时轮询抖音状态
      getDouyinRelayStatus(FASTAPI_BASE_URL)
        .then((douyinResult) => {
          setDouyinStatus(douyinResult);
          setDouyinConnected(douyinResult.is_running);
        })
        .catch(() => {
          setDouyinStatus(null);
          setDouyinConnected(false);
        });
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
      // 检查付费状态
      if (!isPaid) {
        setError('功能暂时不可用');
        setLoading(false);
        return;
      }

      const input = liveInput.trim();
      if (!input) throw new Error('请填写直播地址或直播间ID');
      const idMatch = input.match(/live\.douyin\.com\/([A-Za-z0-9_\-]+)/);
      const liveId = idMatch ? idMatch[1] : input;
      const liveUrl = idMatch ? input : `https://live.douyin.com/${liveId}`;

      // 异步启动所有服务，不阻塞彼此
      const services = [
        // 1) 弹幕服务启动函数
        async () => {
          let retries = 0;
          const maxRetries = 5;
          while (retries < maxRetries) {
            try {
              await startDouyinRelay(liveId, FASTAPI_BASE_URL);
              // 默认开启弹幕持久化
              await updateDouyinPersist({ persist_enabled: true }, FASTAPI_BASE_URL);
              console.log('抖音直播互动服务启动成功');
              return true;
            } catch (err) {
              retries++;
              console.error(`抖音直播互动服务启动失败 (尝试 ${retries}/${maxRetries}):`, err);
              if (retries >= maxRetries) {
                throw new Error(`抖音直播互动服务启动失败: ${(err as Error).message}`);
              }
              // 等待一段时间后重试
              await new Promise(resolve => setTimeout(resolve, 2000 * retries));
            }
          }
        },
        // 2) 音频服务启动函数
        async () => {
          let retries = 0;
          const maxRetries = 5;
          while (retries < maxRetries) {
            try {
              await startLiveAudio({ liveUrl }, FASTAPI_BASE_URL);
              connectWebSocket(FASTAPI_BASE_URL);
              // 默认开启字幕持久化
              await updateLiveAudioAdvanced(
                {
                  persist_enabled: true,
                  agc: agcEnabled,
                  diarization: diarizationEnabled,
                  max_speakers: diarizationEnabled ? maxSpeakers : 1,
                },
                FASTAPI_BASE_URL
              );
              console.log('实时音频转写服务启动成功');
              return true;
            } catch (err) {
              retries++;
              console.error(`实时音频转写服务启动失败 (尝试 ${retries}/${maxRetries}):`, err);
              if (retries >= maxRetries) {
                throw new Error(`实时音频转写服务启动失败: ${(err as Error).message}`);
              }
              // 等待一段时间后重试
              await new Promise(resolve => setTimeout(resolve, 2000 * retries));
            }
          }
        },
        // 3) 录制服务启动函数
        async () => {
          let retries = 0;
          const maxRetries = 3;
          while (retries < maxRetries) {
            try {
              await startLiveReport(liveUrl, 30, FASTAPI_BASE_URL);
              console.log('直播录制服务启动成功');
              return true;
            } catch (err) {
              retries++;
              console.error(`直播录制服务启动失败 (尝试 ${retries}/${maxRetries}):`, err);
              if (retries >= maxRetries) {
                console.warn(`直播录制服务启动失败: ${(err as Error).message}`);
                // 录制服务失败不阻塞其他服务
                return false;
              }
              // 等待一段时间后重试
              await new Promise(resolve => setTimeout(resolve, 2000 * retries));
            }
          }
        }
      ];

      // 并行启动所有服务
      const results = await Promise.allSettled(services.map(service => service()));
      
      // 检查结果并处理错误
      const errors: string[] = [];
      results.forEach((result, index) => {
        if (result.status === 'rejected') {
          const serviceName = ['抖音直播互动服务', '实时音频转写服务', '直播录制服务'][index];
          errors.push(`${serviceName}: ${result.reason.message}`);
        }
      });

      if (errors.length > 0) {
        // 如果关键服务（前两个）都失败了，则抛出错误
        if (results[0].status === 'rejected' && results[1].status === 'rejected') {
          throw new Error(`多个服务启动失败:\n${errors.join('\n')}`);
        }
        // 如果只有非关键服务失败，显示警告但不阻塞
        if (errors.length > 0) {
          console.warn('部分服务启动失败:', errors.join('\n'));
        }
      }

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
      setError((err as Error).message ?? '启动直播服务失败');
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    setError(null);
    try {
      // 异步停止所有服务
      const services = [
        async () => {
          try {
            await stopLiveAudio(FASTAPI_BASE_URL);
            console.log('实时音频转写服务停止成功');
          } catch (err) {
            console.error('实时音频转写服务停止失败:', err);
            throw err;
          }
        },
        async () => {
          try {
            await stopDouyinRelay(FASTAPI_BASE_URL);
            console.log('抖音直播互动服务停止成功');
          } catch (err) {
            console.error('抖音直播互动服务停止失败:', err);
            // 不抛出错误，继续执行其他停止操作
          }
        },
        async () => {
          try {
            await stopLiveReport(FASTAPI_BASE_URL);
            console.log('直播录制服务停止成功');
          } catch (err) {
            console.error('直播录制服务停止失败:', err);
            // 不抛出错误，继续执行其他停止操作
          }
        },
        async () => {
          try {
            await stopAILiveAnalysis(FASTAPI_BASE_URL).catch(() => {});
            console.log('AI实时分析服务停止成功');
          } catch (err) {
            console.error('AI实时分析服务停止失败:', err);
            // 不抛出错误，继续执行其他停止操作
          }
        }
      ];

      // 并行停止所有服务
      await Promise.allSettled(services.map(service => service()));

      resetSessionState();
      disconnectWebSocket();
      analysisBootRef.current = false;
      // 主动清空本地选择与结果，避免残留
      setSelectedQuestions([]);
      setAnswerError(null);
      setAnswerScripts([]);
    } catch (err) {
      console.error(err);
      setError((err as Error).message ?? '停止直播服务失败');
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
    // 确保所有字段都正确处理
    if (payload.topic_playlist !== undefined) {
      normalized.topic_playlist = toArray(payload.topic_playlist);
    }
    if (payload.lead_candidates !== undefined) {
      normalized.lead_candidates = toArray(payload.lead_candidates);
    }
    // 确保观众情绪数据正确处理
    if (payload.audience_sentiment !== undefined) {
      normalized.audience_sentiment = payload.audience_sentiment;
    } else if (card && typeof card === 'object' && card.audience_sentiment !== undefined) {
      normalized.audience_sentiment = card.audience_sentiment;
    }
    return normalized;
  }, []);

  const connectAIStream = useCallback(async () => {
    if (aiSourceRef.current) return;
    // 使用统一的鉴权 SSE 流
    const es = await openAILiveStream(
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
    setSelectedQuestions([text]);
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
    if (generatingRef.current) return;
    if (!selectedQuestions.length) {
      setAnswerError('请先选择至少一个弹幕问题');
      return;
    }
    try {
      generatingRef.current = true;
      setAnswerLoading(true);
      setAnswerError(null);
      const transcriptSnippet = log
        .slice(0, 6)
        .reverse()
        .map((item) => item.text)
        .filter(Boolean)
        .join('\n');
      const latestQuestion = selectedQuestions[0];
      const payload: any = {
        questions: latestQuestion ? [latestQuestion] : [],
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
      generatingRef.current = false;
    }
  }, [selectedQuestions, log, styleProfile, vibe, setAnswerScripts, FASTAPI_BASE_URL]);

  // --------------- State persistence ---------------
  return (
    <div className="space-y-8">
      <div className="timao-soft-card relative min-h-[250px] flex flex-col gap-4 lg:flex-row lg:flex-wrap lg:items-center lg:justify-between">
        <div className="flex items-center gap-4">
          <div className="text-4xl">📡</div>
          <div>
            <div className="text-lg font-semibold text-purple-600">直播控制台</div>
            <div className="text-sm timao-support-text">{isRunning ? '运行中' : '未开始'}</div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3 justify-center w-full lg:basis-full lg:justify-center">
          <input
            value={liveInput}
            onChange={(event) => setLiveInput(event.target.value)}
            className="timao-input w-64 text-sm"
            placeholder="直播地址或ID (e.g. https://live.douyin.com/xxxx)"
            disabled={isRunning || loading}
          />
          {/* 简洁模式：不暴露“预设”选择，保持默认策略 */}
          {/* 模式/引擎固定：稳妥（VAD）· 轻量（Small） */}
          {/* 开始转写按钮和停止转写按钮向右移动600px */}
          <button className="timao-primary-btn ml-[600px]" onClick={handleStart} disabled={loading || isRunning}>
            {loading ? '处理中...' : isRunning ? '运行中' : '开始转写'}
          </button>
          <button className="timao-outline-btn" onClick={handleStop} disabled={loading || !isRunning}>
            停止
          </button>
        </div>
        {/* 直播间状态信息（左下角，三行内联显示与输入框左对齐） */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs">
          {/* 第一行：连接状态 + 当前直播间ID */}
          <div className="flex items-center gap-3">
            <span className="text-gray-600">连接状态：</span>
            <span className={`px-2 py-0.5 rounded-full font-medium transition-colors duration-200 ${
              douyinConnected ? 'text-emerald-700' : 'text-rose-700'
            }`}>
              {douyinConnected ? '运行中' : '已断开'}
            </span>
            <span className="text-gray-600">当前直播间ID：</span>
            <span className={`text-gray-800 font-mono text-xs px-2 py-1 rounded ${
              douyinStatus?.live_id ? 'text-blue-700' : 'text-gray-700'
            }`}>
              {douyinStatus?.live_id ?? '—'}
            </span>
          </div>
          {/* 第二行：当前直播间ID + Room ID */}
          <div className="flex items-center gap-3">
            <span className="text-gray-600">当前直播间ID：</span>
            <span className={`text-gray-800 font-mono text-xs px-2 py-1 rounded ${
              douyinStatus?.live_id ? 'text-blue-700' : 'text-gray-700'
            }`}>
              {douyinStatus?.live_id ?? '—'}
            </span>
            <span className="text-gray-600">Room ID：</span>
            <span className={`text-gray-800 font-mono text-xs px-2 py-1 rounded ${
              douyinStatus?.room_id ? 'text-purple-700' : 'text-gray-700'
            }`}>
              {douyinStatus?.room_id ?? '—'}
            </span>
          </div>
          {/* 第三行：实时通道状态 */}
          <div className="flex items-center gap-3">
            <span className="text-gray-600">实时通道状态：</span>
            <span className={`px-2 py-0.5 rounded-full font-medium transition-colors duration-200 ${
              (douyinConnected && getLiveConsoleSocket()?.readyState === WebSocket.OPEN) ? 'text-emerald-700' : 'text-amber-700'
            }`}>
              {(douyinConnected && getLiveConsoleSocket()?.readyState === WebSocket.OPEN) ? '已连接' : '未连接'}
            </span>
          </div>
        </div>
      </div>

      {error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div>
      ) : null}

      {/* 四宫格布局 */}
      <div className="grid grid-cols-2 gap-4 h-[900px]">
        {/* 第一宫格：主播实时语音转写和弹幕数据流 */}
        <div className="timao-card flex flex-col h-[450px] w-full min-h-[450px] max-h-[450px] min-w-0 overflow-hidden px-4 pt-4">
          {/* 简化的标题栏 */}
          <div className="flex items-center justify-between mb-3 flex-shrink-0">
            <h3 className="text-base font-semibold text-purple-600 flex items-center gap-2 ml-[5px]">
              实时语音转写
            </h3>
            <div className="flex items-center gap-2">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${isRunning ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                {isRunning ? '实时' : '暂停'}
              </span>
              <button
                className={`px-2 py-1 rounded-md text-xs transition-colors ${
                  collapsed 
                    ? 'bg-purple-100 text-purple-700 hover:bg-purple-200' 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                onClick={() => setCollapsed((v) => !v)}
              >
                {collapsed ? '选择' : '展开'}
              </button>
            </div>
          </div>
          
          {/* 并排显示：语音转写和弹幕数据流 */}
          <div className="flex-1 flex flex-col lg:flex-row gap-4 overflow-hidden min-h-0">
            {/* 左侧：语音转写区域 */}
            <div className="flex-1 flex flex-col min-h-0 lg:min-w-0">
              <div className="flex items-center justify-between mb-2 flex-shrink-0">
                <h4 className="text-sm font-medium text-gray-700 ml-[10px]">语音转写</h4>
                <button
                  className={`px-2 py-1 rounded-md text-xs transition-colors ${
                    collapsed 
                      ? 'bg-purple-100 text-purple-700 hover:bg-purple-200' 
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                  onClick={() => setCollapsed((v) => !v)}
                >
                  {collapsed ? '选择' : '展开'}
                </button>
              </div>
              
              <div className="flex-1 min-h-0">
                {collapsed ? (
                  // 选择模式 - 简化版
                  <div className="space-y-2 overflow-y-auto flex-1 min-h-0 custom-scrollbar max-h-[380px]">
                    <select
                      className="timao-input w-full text-sm"
                      value={selectedId ?? (log[0]?.id || '')}
                      onChange={(e) => setSelectedId(e.target.value || null)}
                    >
                      {log.length === 0 ? (
                        <option value="">暂无记录</option>
                      ) : (
                        log.map((item, index) => (
                          <option key={item.id} value={item.id}>
                            {index === 0 ? '[最新] ' : ''}{new Date(item.timestamp * 1000).toLocaleTimeString()} · {(item.text || '').slice(0, 15)}...
                          </option>
                        ))
                      )}
                    </select>
                    <div className="rounded-lg bg-white border p-2 lg:p-3 text-sm min-h-[60px] lg:min-h-[80px]">
                      {(() => {
                        const found = log.find((x) => x.id === (selectedId ?? log[0]?.id));
                        return found ? (
                          <div>
                            <div className="text-xs text-gray-500 mb-2">
                              {new Date(found.timestamp * 1000).toLocaleTimeString()}
                            </div>
                            <div className="text-gray-800 text-xs lg:text-sm">{found.text}</div>
                          </div>
                        ) : (
                          <div className="text-center text-gray-500 py-2 lg:py-4">
                            {isRunning ? '等待识别...' : '暂无内容'}
                          </div>
                        );
                      })()}
                    </div>
                  </div>
                ) : (
                  // 展开模式 - 简化版
                  <div className="space-y-2 overflow-y-auto flex-1 min-h-0 custom-scrollbar max-h-[380px]">
                    {log.length === 0 ? (
                      <div className="text-center py-4 lg:py-8 text-gray-500">
                        <div className="text-xs lg:text-sm">{isRunning ? '等待语音识别...' : '点击开始转写'}</div>
                      </div>
                    ) : (
                      <>
                        {/* 显示所有记录 */}
                        {log.map((item, index) => (
                          <div key={item.id} className={`rounded-lg border bg-white p-2 ${index === 0 ? 'border-2 border-purple-200 bg-purple-50' : ''}`}>
                            <div className="flex justify-between text-xs text-purple-600 mb-1">
                              <span>{index === 0 ? '最新' : `记录 ${index + 1}`}</span>
                              <span>{new Date(item.timestamp * 1000).toLocaleTimeString()}</span>
                            </div>
                            <div className="text-xs lg:text-sm text-gray-800">{item.text}</div>
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
            
            {/* 右侧：弹幕数据流区域 */}
            <div className="flex-1 flex flex-col min-h-0 lg:min-w-0">
              <div className="flex items-center justify-between mb-2 flex-shrink-0">
                <h4 className="text-sm font-medium text-gray-700 flex items-center gap-1 ml-[10px]">
                  实时弹幕
                </h4>
              </div>
              
              <div className="flex-1 min-h-0 overflow-hidden">
                <DouyinRelayPanel 
                  baseUrl={FASTAPI_BASE_URL} 
                  onSelectQuestion={handleSelectQuestion}
                  liveId={liveInput}
                  isRunning={isRunning}
                />
              </div>
            </div>
          </div>
        </div>

        {/* 第二宫格：智能话术建议 */}
         <div className="timao-card flex flex-col h-[450px] w-full min-h-[450px] max-h-[450px] min-w-0 overflow-hidden px-4 pt-4">
           <div className="flex items-center justify-between mb-3 flex-shrink-0">
             <h3 className="text-base font-semibold text-purple-600 flex items-center gap-2">
               智能话术建议
             </h3>
             <span className="text-xs timao-support-text">点击弹幕生成话术</span>
           </div>
          <div className="flex-1 overflow-y-auto space-y-2 min-h-0">
            <div>
              <div className="text-xs text-slate-500 mb-1">已选问题</div>
              {selectedQuestions.length ? (
                <ul className="space-y-2 max-h-20 overflow-y-auto">
                  {selectedQuestions.slice(0, 3).map((q) => (
                    <li key={q} className="flex items-start justify-between gap-2 rounded-lg border bg-white/90 p-2 text-sm text-slate-700">
                      <span className="flex-1 leading-relaxed">{q}</span>
                      <button
                        className="timao-support-text text-[10px] hover:text-rose-500 flex-shrink-0"
                        onClick={() => handleRemoveQuestion(q)}
                        title="移除该问题"
                      >
                        移除
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="timao-outline-card text-xs timao-support-text py-2">
                  在弹幕列表中点击对应按钮，即可将问题加入这里。
                </div>
              )}
              <div className="mt-2 flex items-center gap-2 ml-[5px]">
                <button
                  className="timao-primary-btn text-xs px-3 py-1"
                  onClick={handleGenerateAnswers}
                  disabled={!selectedQuestions.length || answerLoading}
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
                <div className="space-y-2 max-h-62 overflow-y-auto">
                  {answerScripts.slice(0, 4).map((script, idx) => (
                    <div key={idx} className="rounded-lg border bg-white/90 p-2 text-sm text-slate-700">
                      <div className="font-medium text-slate-800 mb-1">话术 {idx + 1}</div>
                      <div className="leading-relaxed text-slate-600">
                        {typeof script === 'string' ? script : script?.line || script?.question || '暂无内容'}
                      </div>
                      {typeof script === 'object' && script?.notes && (
                        <div className="text-xs text-slate-500 mt-1">备注：{script.notes}</div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="timao-outline-card text-xs timao-support-text py-2">
                  选择问题后点击"生成话术"按钮。
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 第三宫格：直播间分析 */}
        <div className="timao-card flex flex-col h-[450px] w-full min-h-[450px] max-h-[450px] min-w-0 overflow-hidden px-4 pt-4">
          <div className="flex items-center justify-between mb-3 flex-shrink-0">
            <h3 className="text-base font-semibold text-purple-600 flex items-center gap-2 ml-[5px]">
              直播间分析
            </h3>
            <span className="text-xs timao-support-text">AI分析结果</span>
          </div>
          <div className="flex-1 overflow-y-auto min-h-0">
            {!aiEvents.length ? (
              <div className="timao-outline-card text-sm timao-support-text flex items-center justify-center h-full">
                {isRunning ? '正在生成直播分析…（开始字幕后约1分钟内出现结果）' : '请先开始实时字幕'}
              </div>
            ) : (
              <div className="space-y-3 p-1">
                {aiEvents.slice(0, 2).map((ev, idx) => {
                  const sentiment = ev?.audience_sentiment
                    || (ev?.analysis_card && typeof ev.analysis_card === 'object' ? ev.analysis_card.audience_sentiment : null);
                  const sentimentSignals = Array.isArray(sentiment?.signals) ? sentiment.signals : [];
                  const fallbackTopics = Array.isArray(ev?.topic_playlist) ? ev.topic_playlist : [];
                  const hasAny = ev?.summary
                    || (Array.isArray(ev?.highlight_points) && ev.highlight_points.length)
                    || (Array.isArray(ev?.risks) && ev.risks.length)
                    || (Array.isArray(ev?.suggestions) && ev.suggestions.length)
                    || (Array.isArray(ev?.top_questions) && ev.top_questions.length)
                    || (sentiment && (sentiment.label || sentimentSignals.length))
                    || (ev?.audience_sentiment && (ev.audience_sentiment.label || (Array.isArray(ev.audience_sentiment.signals) && ev.audience_sentiment.signals.length)))
                    || ev?.analysis_focus
                    || fallbackTopics.length
                    || ev?.error || ev?.raw;
                  return (
                    <div key={idx} className="rounded-lg border border-white/60 shadow-sm p-3 bg-white/95">
                      {ev?.error ? (
                        <div className="text-xs text-red-600 mb-2">AI 分析错误：{String(ev.error)}</div>
                      ) : null}
                      {ev?.summary ? (
                        <div className="text-sm text-slate-700 mb-3 whitespace-pre-wrap leading-relaxed">{ev.summary}</div>
                      ) : null}
                      {Array.isArray(ev?.highlight_points) && ev.highlight_points.length ? (
                        <>
                          <div className="text-xs text-slate-500 mb-1 font-medium">亮点</div>
                          <ul className="list-disc pl-4 text-sm text-slate-600 space-y-1">
                            {ev.highlight_points.slice(0, 2).map((x: any, i: number) => (<li key={i} className="truncate">{String(x)}</li>))}
                          </ul>
                        </>
                      ) : null}
                      {Array.isArray(ev?.risks) && ev.risks.length ? (
                        <>
                          <div className="text-xs text-slate-500 mt-2 mb-1 font-medium">风险</div>
                          <ul className="list-disc pl-4 text-sm text-slate-600 space-y-1">
                            {ev.risks.slice(0, 2).map((x: any, i: number) => (<li key={i} className="truncate">{String(x)}</li>))}
                          </ul>
                        </>
                      ) : null}
                      {Array.isArray(ev?.suggestions) && ev.suggestions.length ? (
                        <>
                          <div className="text-xs text-slate-500 mt-2 mb-1 font-medium">建议</div>
                          <ul className="list-disc pl-4 text-sm text-slate-600 space-y-1">
                            {ev.suggestions.slice(0, 3).map((x: any, i: number) => (<li key={i} className="truncate">{String(x)}</li>))}
                          </ul>
                        </>
                      ) : null}
                      {(sentiment && (sentiment.label || sentimentSignals.length)) || (ev?.audience_sentiment && (ev.audience_sentiment.label || (Array.isArray(ev.audience_sentiment.signals) && ev.audience_sentiment.signals.length))) ? (
                        <>
                          <div className="text-xs text-slate-500 mt-2 mb-1 font-medium">观众情绪</div>
                          <div className="text-sm text-slate-600">
                            状态：<span className="font-medium">{sentiment?.label || ev?.audience_sentiment?.label || '—'}</span>
                          </div>
                          {sentimentSignals.length ? (
                            <ul className="list-disc pl-4 text-sm text-slate-600 mt-1 space-y-1">
                              {sentimentSignals.slice(0, 2).map((signal: any, i: number) => (
                                <li key={i} className="truncate">{String(signal)}</li>
                              ))}
                            </ul>
                          ) : Array.isArray(ev?.audience_sentiment?.signals) && ev.audience_sentiment.signals.length ? (
                            <ul className="list-disc pl-4 text-sm text-slate-600 mt-1 space-y-1">
                              {ev.audience_sentiment.signals.slice(0, 2).map((signal: any, i: number) => (
                                <li key={i} className="truncate">{String(signal)}</li>
                              ))}
                            </ul>
                          ) : null}
                        </>
                      ) : null}
                      {Array.isArray(ev?.top_questions) && ev.top_questions.length ? (
                        <>
                          <div className="text-xs text-slate-500 mt-2 mb-1 font-medium">高频问题</div>
                          <ul className="list-disc pl-4 text-sm text-slate-600 space-y-1">
                            {ev.top_questions.slice(0, 2).map((x: any, i: number) => (<li key={i} className="truncate">{String(x)}</li>))}
                          </ul>
                        </>
                      ) : null}
                      {Array.isArray(ev?.topic_playlist) && ev.topic_playlist.length ? (
                        <>
                          <div className="text-xs text-slate-500 mt-2 mb-1 font-medium">话题推荐</div>
                          <ul className="list-disc pl-4 text-sm text-slate-600 space-y-1">
                            {ev.topic_playlist.slice(0, 2).map((x: any, i: number) => (<li key={i} className="truncate">{String(x.topic)}</li>))}
                          </ul>
                        </>
                      ) : null}
                      {!hasAny ? (
                        <div className="text-sm text-slate-400 text-center py-4">暂无可显示内容</div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* 第四宫格：主播画像与氛围分析 */}
        <div className="timao-card flex flex-col h-[450px] w-full min-h-[450px] max-h-[450px] min-w-0 overflow-hidden px-4 pt-4">
          <div className="flex items-center justify-between mb-3 flex-shrink-0">
            <h3 className="text-base font-semibold text-purple-600 flex items-center gap-2 ml-[5px]">
              主播画像与氛围分析
            </h3>
            <span className="text-xs timao-support-text">实时情绪识别</span>
          </div>
          <div className="flex-1 overflow-y-auto min-h-0">
            {(!styleProfile && !vibe) ? (
              <div className="timao-outline-card text-sm timao-support-text flex items-center justify-center h-full">
                {isRunning ? '正在学习主播风格与氛围…' : '开始实时字幕'}
              </div>
            ) : (
              <div className="space-y-3">
                {styleProfile ? (
                  <div className="rounded-lg bg-white/90 border p-3">
                    <div className="text-xs text-slate-500 mb-2 font-medium">主播风格画像</div>
                    <div className="text-sm text-slate-600 space-y-2">
                      <div className="flex items-center">
                        <span className="text-slate-500 w-16 flex-shrink-0">人物：</span>
                        <span className="truncate">{String(styleProfile.persona ?? '—')}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-slate-500 w-16 flex-shrink-0">语气：</span>
                        <span className="truncate">{String(styleProfile.tone ?? '—')}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-slate-500 w-16 flex-shrink-0">节奏：</span>
                        <span className="truncate">{String(styleProfile.tempo ?? '—')}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-slate-500 w-16 flex-shrink-0">用词：</span>
                        <span className="truncate">{String(styleProfile.register ?? '—')}</span>
                      </div>
                      {Array.isArray(styleProfile.catchphrases) && styleProfile.catchphrases.length ? (
                        <div className="flex items-center">
                          <span className="text-slate-500 w-16 flex-shrink-0">口头禅：</span>
                          <span className="truncate">{styleProfile.catchphrases.slice(0, 2).join('、')}</span>
                        </div>
                      ) : null}
                    </div>
                  </div>
                ) : null}
                
                {vibe ? (
                  <div className="rounded-lg bg-white/90 border p-3">
                    <div className="text-xs text-slate-500 mb-2 font-medium">直播间氛围指数</div>
                    <div className="text-sm text-slate-600 space-y-2">
                      <div className="flex items-center">
                        <span className="text-slate-500 w-20 flex-shrink-0">热度等级：</span>
                        <span>{String(vibe.level ?? '—')}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-slate-500 w-20 flex-shrink-0">氛围分数：</span>
                        <span>{String(vibe.score ?? '—')}</span>
                      </div>
                    </div>
                  </div>
                ) : null}
                
                {/* 实时统计 */}
                <div className="rounded-xl bg-white/90 border p-3">
                  <div className="text-xs text-slate-500 mb-2 font-medium">实时统计</div>
                  <div className="text-sm text-slate-600 space-y-2">
                    <div className="flex items-center">
                      <span className="text-slate-500 w-20 flex-shrink-0">转写记录：</span>
                      <span>{log.length} 条</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-slate-500 w-20 flex-shrink-0">AI分析：</span>
                      <span>{aiEvents.length} 次</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-slate-500 w-20 flex-shrink-0">已选问题：</span>
                      <span>{selectedQuestions.length} 个</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-slate-500 w-20 flex-shrink-0">生成话术：</span>
                      <span>{Array.isArray(answerScripts) ? answerScripts.length : 0} 条</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            {/* 错误信息显示 */}
            {douyinStatus?.last_error && (
              <div className="flex items-start justify-between pt-3 border-t border-gray-100 mt-3">
                <span className="text-gray-600">错误信息：</span>
                <span className="text-red-600 text-sm max-w-40 text-right break-words">
                  {douyinStatus.last_error}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      

      {/* 第三行：其他功能区域 */}
      <div className="grid gap-6 xl:grid-cols-3 lg:grid-cols-2 md:grid-cols-1">
        {/* 左侧：音频增强等卡片 */}
        <section className="flex flex-col gap-4">
          <div className="timao-card hidden">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
                <span>🎛️</span>
                音频增强
              </h3>
              <span className="text-xs text-slate-400">增益 {agcGain.toFixed(2)}</span>
            </div>
            <div className="space-y-3 text-sm text-slate-600">
              <div className="flex items-center justify-between">
                <span>自动增益（AGC）</span>
                <span className="text-purple-600">{agcEnabled ? '已开启（默认）' : '已关闭'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>说话人分离</span>
                <span className="text-purple-600">
                  {diarizationEnabled ? `已开启（≤${maxSpeakers} 人）` : '已关闭'}
                </span>
              </div>
              <div className="text-xs text-slate-400">
                <span className="mr-1">最近发言者：</span>
                {renderSpeakerBadge(lastSpeaker)}
              </div>
            </div>
          </div>

          <div className="timao-card hidden">
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

          <div className="timao-card hidden">
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

        {/* 中间：实时字幕和当前会话 */}
        <section className="flex flex-col gap-4">
          <div className="timao-card hidden">
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
                <div className="flex items-center gap-2">
                  <span>时间 {new Date(latest.timestamp * 1000).toLocaleTimeString()}</span>
                  {renderSpeakerBadge(latest.speaker)}
                </div>
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
                        speaker_debug: latest.speakerDebug || {},
                        room_id: (status as any)?.live_id || null,
                        session_id: (status as any)?.session_id || null,
                      };
                      (window as any).utils?.copyToClipboard(JSON.stringify(payload, null, 2));
                    } catch {}
                  }}
                >复制JSON</button>
              </div>
            ) : null}
            {(() => {
              const debugText = formatSpeakerDebug(latest?.speakerDebug || undefined);
              return debugText
                ? (
                  <div className="text-[10px] text-slate-400 mt-1">
                    {debugText}
                  </div>
                )
                : null;
            })()}
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

          <div className="timao-soft-card hidden">
            <div className="text-sm text-slate-500 mb-1">当前会话</div>
            <div className="text-lg font-semibold text-purple-600">{status?.session_id ?? '—'}</div>
            <div className="text-xs timao-support-text mt-2">
              已累计片段 {status?.stats?.total_audio_chunks ?? 0} · 成功转写 {status?.stats?.successful_transcriptions ?? 0}
            </div>
          </div>

          {showSaveInfo && saveInfo ? (
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
        </section>

      </div>
    </div>
  );
};

export default LiveConsolePage;
