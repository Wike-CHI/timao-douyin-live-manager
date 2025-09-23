import { ChangeEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  DouyinRelayStatus,
  DouyinStreamEvent,
  getDouyinRelayStatus,
  openDouyinStream,
  startDouyinRelay,
  stopDouyinRelay,
} from '../../services/douyin';

const DEFAULT_MAX_MESSAGES = 80;

type StatusTone = 'info' | 'success' | 'warning' | 'error';

type ChatCategory = 'chat' | 'gift' | 'like' | 'system';

interface ChatEntry {
  id: string;
  nickname: string;
  content: string;
  timestamp: number;
  category: ChatCategory;
}

interface RankEntry {
  rank: number;
  nickname: string;
  score: string;
  avatar?: string | null;
  userId?: string | number | null;
}

interface DouyinRelayPanelProps {
  baseUrl?: string;
  maxMessages?: number;
}

const toneClasses: Record<StatusTone, string> = {
  info: 'border-slate-200 text-slate-600 bg-slate-50',
  success: 'border-emerald-200 text-emerald-600 bg-emerald-50/80',
  warning: 'border-amber-200 text-amber-600 bg-amber-50/80',
  error: 'border-rose-200 text-rose-600 bg-rose-50/80',
};

const chatCategoryLabel: Record<ChatCategory, string> = {
  chat: '弹幕',
  gift: '礼物',
  like: '点赞',
  system: '系统',
};

const DouyinRelayPanel = ({ baseUrl, maxMessages = DEFAULT_MAX_MESSAGES }: DouyinRelayPanelProps) => {
  const [liveIdInput, setLiveIdInput] = useState('');
  const [status, setStatus] = useState<DouyinRelayStatus | null>(null);
  const [chatLog, setChatLog] = useState<ChatEntry[]>([]);
  const [rankList, setRankList] = useState<RankEntry[]>([]);
  const [banner, setBanner] = useState<{ tone: StatusTone; message: string } | null>({
    tone: 'info',
    message: '等待启动直播互动',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamConnected, setStreamConnected] = useState(false);

  const eventSourceRef = useRef<EventSource | null>(null);
  const lastStartedLiveIdRef = useRef<string>('');

  const isRunning = status?.is_running ?? false;

  const appendChat = useCallback(
    (entry: ChatEntry) => {
      setChatLog((prev) => {
        const updated = [entry, ...prev];
        if (updated.length > maxMessages) {
          updated.length = maxMessages;
        }
        return updated;
      });
    },
    [maxMessages]
  );

  const pushSystemMessage = useCallback(
    (content: string) => {
      appendChat({
        id: `system-${Date.now()}-${Math.random()}`,
        nickname: '系统',
        content,
        timestamp: Date.now(),
        category: 'system',
      });
    },
    [appendChat]
  );

  const disconnectStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setStreamConnected(false);
  }, []);

  const handleStreamEvent = useCallback(
    (event: DouyinStreamEvent) => {
      const payload = (event.payload as Record<string, unknown> | null) || {};
      switch (event.type) {
        case 'status': {
          const stage = payload.stage as string | undefined;
          if (stage === 'starting') {
            setBanner({ tone: 'info', message: '正在准备直播互动…' });
          } else if (stage === 'resolving_room') {
            setBanner({ tone: 'info', message: '正在解析直播间信息…' });
          } else if (stage === 'room_ready') {
            const roomId = (payload.room_id as string | number | undefined) ?? null;
            setStatus((prev) =>
              prev
                ? { ...prev, room_id: roomId ? String(roomId) : null, is_running: true }
                : {
                    is_running: true,
                    live_id: lastStartedLiveIdRef.current || null,
                    room_id: roomId ? String(roomId) : null,
                    last_error: null,
                  }
            );
            setBanner({ tone: 'success', message: `已解析直播间，room_id=${roomId ?? '未知'}，等待弹幕…` });
          } else if (stage === 'connected') {
            setBanner({ tone: 'success', message: '已连接，开始接收弹幕。' });
            setStreamConnected(true);
          } else if (stage === 'room_closed') {
            setBanner({ tone: 'warning', message: '直播间已关闭，连接已断开。' });
            disconnectStream();
            setStatus((prev) =>
              prev
                ? { ...prev, is_running: false, room_id: null }
                : { is_running: false, live_id: null, room_id: null, last_error: null }
            );
          } else if (stage === 'stopped' || stage === 'closed') {
            setBanner({ tone: 'warning', message: '连接已关闭。' });
            disconnectStream();
            setStatus((prev) =>
              prev
                ? { ...prev, is_running: false }
                : { is_running: false, live_id: null, room_id: null, last_error: null }
            );
          }
          break;
        }
        case 'error': {
          const message = (payload.message as string | undefined) ?? '连接异常';
          setBanner({ tone: 'error', message: `连接异常：${message}` });
          setStatus((prev) =>
            prev
              ? { ...prev, last_error: message }
              : { is_running: false, live_id: null, room_id: null, last_error: message }
          );
          break;
        }
        case 'chat': {
          const nickname = (payload.nickname as string | undefined) || '匿名';
          const content = (payload.content as string | undefined) || '';
          appendChat({
            id: `chat-${event.timestamp ?? Date.now()}-${Math.random()}`,
            nickname,
            content,
            timestamp: Date.now(),
            category: 'chat',
          });
          break;
        }
        case 'gift': {
          const nickname = (payload.nickname as string | undefined) || '匿名';
          const giftName = (payload.gift_name as string | undefined) || '礼物';
          const count = payload.count as number | undefined;
          appendChat({
            id: `gift-${event.timestamp ?? Date.now()}-${Math.random()}`,
            nickname,
            content: `🎁 送出 ${giftName}${count ? ` x${count}` : ''}`,
            timestamp: Date.now(),
            category: 'gift',
          });
          break;
        }
        case 'like': {
          const nickname = (payload.nickname as string | undefined) || '匿名';
          const count = payload.count as number | undefined;
          appendChat({
            id: `like-${event.timestamp ?? Date.now()}-${Math.random()}`,
            nickname,
            content: `❤️ 点赞${count ? ` ${count} 次` : ''}`,
            timestamp: Date.now(),
            category: 'like',
          });
          break;
        }
        case 'member': {
          const nickname = (payload.nickname as string | undefined) || '访客';
          pushSystemMessage(`${nickname} 进入直播间`);
          break;
        }
        case 'fansclub': {
          const nickname = (payload.nickname as string | undefined) || '粉丝';
          const content = (payload.content as string | undefined) || '加入粉丝团';
          pushSystemMessage(`${nickname} · ${content}`);
          break;
        }
        case 'room_rank': {
          // Normalize raw rank payload and narrow userId type for TS safety
          const ranksRaw = Array.isArray(payload.ranks)
            ? (payload.ranks as Array<Record<string, unknown>>)
            : [];
          const parsedRanks: RankEntry[] = ranksRaw.slice(0, 15).map((item, index) => {
            const rank = Number((item as any).rank ?? index + 1);
            const nickname = ((item as any).nickname as string | undefined) || '匿名';
            const scoreStr = (item as any).score_str as string | undefined;
            const scoreNum = (item as any).score as number | string | undefined;
            const avatar = ((item as any).avatar as string | undefined) || null;

            const userIdRaw = (item as any).user_id as unknown;
            const userIdStrRaw = (item as any).user_id_str as unknown;
            let userId: string | number | null = null;
            if (typeof userIdRaw === 'string' || typeof userIdRaw === 'number') {
              userId = userIdRaw;
            } else if (typeof userIdStrRaw === 'string' || typeof userIdStrRaw === 'number') {
              userId = userIdStrRaw;
            }

            return {
              rank,
              nickname,
              score: scoreStr || String(scoreNum ?? '0'),
              avatar,
              userId,
            } as RankEntry;
          });
          setRankList(parsedRanks);
          break;
        }
        case 'room_control': {
          const statusValue = payload.status as number | undefined;
          const tips = (payload.tips as string | undefined) || '';
          pushSystemMessage(`房间控制状态：${statusValue ?? '未知'} ${tips}`.trim());
          break;
        }
        case 'room_stats': {
          const total = payload.total_user as number | undefined;
          const likes = payload.like_count as number | undefined;
          if (total || likes) {
            pushSystemMessage(`热度：${total ?? '-'} · 点赞：${likes ?? '-'}`);
          }
          break;
        }
        default:
          break;
      }
    },
    [appendChat, disconnectStream, pushSystemMessage]
  );

  const connectStream = useCallback(() => {
    if (eventSourceRef.current) {
      return;
    }
    eventSourceRef.current = openDouyinStream(
      {
        onEvent: handleStreamEvent,
        onOpen: () => {
          setStreamConnected(true);
          setBanner({ tone: 'info', message: '已建立连接，等待消息…' });
        },
        onError: () => {
          setStreamConnected(false);
          setBanner({ tone: 'warning', message: '连接异常，等待自动重连…' });
        },
      },
      baseUrl
    );
  }, [baseUrl, handleStreamEvent]);

  const refreshStatus = useCallback(async () => {
    try {
      const relayStatus = await getDouyinRelayStatus(baseUrl);
      setStatus(relayStatus);
      if (relayStatus.is_running) {
        connectStream();
        if (relayStatus.live_id) {
          lastStartedLiveIdRef.current = relayStatus.live_id;
          setLiveIdInput((current) => current || relayStatus.live_id || '');
        }
      } else {
        disconnectStream();
      }
      if (!relayStatus.is_running) {
        setBanner((prev) => prev ?? { tone: 'info', message: '等待启动直播互动' });
      }
      setError(null);
    } catch (err) {
      setError((err as Error).message || '获取互动状态失败');
    }
  }, [baseUrl, connectStream, disconnectStream]);

  useEffect(() => {
    refreshStatus();
    return () => {
      disconnectStream();
    };
  }, [refreshStatus, disconnectStream]);

  const handleStart = useCallback(async () => {
    const trimmed = liveIdInput.trim();
    if (!trimmed) {
      setError('请输入直播间 ID');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      lastStartedLiveIdRef.current = trimmed;
      await startDouyinRelay(trimmed, baseUrl);
      setBanner({ tone: 'info', message: '启动成功，等待建立连接…' });
      await refreshStatus();
    } catch (err) {
      setError((err as Error).message || '启动失败');
    } finally {
      setLoading(false);
    }
  }, [baseUrl, liveIdInput, refreshStatus]);

  const handleStop = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await stopDouyinRelay(baseUrl);
      await refreshStatus();
      setBanner({ tone: 'info', message: '已停止。' });
    } catch (err) {
      setError((err as Error).message || '停止失败');
    } finally {
      setLoading(false);
    }
  }, [baseUrl, refreshStatus]);

  const handleLiveIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setLiveIdInput(event.target.value);
  };

  const currentStatusText = useMemo(() => {
    if (isRunning) {
      const liveIdText = status?.live_id ?? (lastStartedLiveIdRef.current || '未知');
      return `直播间 ${liveIdText} 正在同步`;
    }
    return '未运行 · 输入直播间号以启动';
  }, [isRunning, status?.live_id]);

  return (
    <section className="timao-card space-y-4">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex items-center gap-3">
          <div className="text-3xl">📡</div>
          <div>
            <div className="text-lg font-semibold text-purple-600">抖音直播互动</div>
            <div className="text-sm timao-support-text">{currentStatusText}</div>
            <div className="text-xs text-slate-400">实时 · 弹幕、礼物、点赞</div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <input
            value={liveIdInput}
            onChange={handleLiveIdChange}
            className="timao-input w-52 text-sm"
            placeholder="输入直播间ID"
            disabled={isRunning || loading}
          />
          <button
            className="timao-primary-btn"
            onClick={handleStart}
            disabled={loading || isRunning || !liveIdInput.trim()}
          >
            {loading && !isRunning ? '处理中…' : isRunning ? '运行中' : '开始'}
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

      {banner ? (
        <div className={`rounded-2xl border px-4 py-3 text-sm ${toneClasses[banner.tone]}`}>
          {banner.message}
        </div>
      ) : null}

      {error ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
          {error}
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <div className="timao-soft-card flex h-full flex-col">
          <div className="mb-3 flex items-center justify-between">
            <h4 className="flex items-center gap-2 text-sm font-semibold text-purple-600">
              <span>💬</span>
              实时弹幕
            </h4>
            <span className="text-xs timao-support-text">{chatLog.length} 条</span>
          </div>
          <div className="max-h-[360px] space-y-3 overflow-y-auto pr-1">
            {chatLog.length === 0 ? (
              <div className="timao-outline-card text-center text-sm timao-support-text">
                {isRunning ? '等待实时弹幕…' : '未启动，请先开始'}
              </div>
            ) : (
              chatLog.map((item) => (
                <div
                  key={item.id}
                  className="rounded-2xl border border-white/70 bg-white/95 p-3 shadow-sm"
                >
                  <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
                    <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
                    <span>{chatCategoryLabel[item.category]}</span>
                  </div>
                  <div className="text-sm leading-relaxed text-slate-700">
                    <span className="font-medium text-purple-500">{item.nickname}</span>
                    <span className="ml-2 text-slate-600">{item.content}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <div className="timao-soft-card">
            <div className="mb-3 flex items-center justify-between">
              <h4 className="flex items-center gap-2 text-sm font-semibold text-purple-600">
                <span>🏆</span>
                粉丝贡献榜
              </h4>
              <span className="text-xs timao-support-text">
                {rankList.length ? `Top ${rankList.length}` : '暂无数据'}
              </span>
            </div>
            <div className="max-h-[220px] space-y-2 overflow-y-auto pr-1">
              {rankList.length === 0 ? (
                <div className="timao-outline-card text-center text-xs timao-support-text">
                  等待贡献榜更新
                </div>
              ) : (
                rankList.map((item) => (
                  <div key={`${item.rank}-${item.nickname}`} className="flex items-center justify-between text-sm text-slate-600">
                    <div className="flex items-center gap-3">
                      <div className="w-8 text-sm font-semibold text-purple-500">#{item.rank}</div>
                      {item.avatar ? (
                        <img
                          src={item.avatar}
                          alt={item.nickname}
                          className="h-8 w-8 rounded-full border border-purple-100 object-cover"
                        />
                      ) : (
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-purple-100/70 text-xs text-purple-600">
                          猫
                        </div>
                      )}
                      <div>
                        <div className="font-medium text-slate-700 leading-tight">{item.nickname}</div>
                        {item.userId ? (
                          <div className="text-xs text-slate-400">ID {String(item.userId)}</div>
                        ) : null}
                      </div>
                    </div>
                    <div className="text-xs text-purple-500">{item.score}</div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="timao-soft-card space-y-2 text-xs text-slate-500">
            <div>· 连接状态：{isRunning ? '运行中' : '未启动'}</div>
            <div>· 当前直播间：{status?.live_id || lastStartedLiveIdRef.current || '—'}</div>
            <div>· Room ID：{status?.room_id || '—'}</div>
            <div>· 实时通道：{streamConnected ? '已连接' : '未连接'}</div>
            {status?.last_error ? (
              <div className="text-rose-600">· 最近错误：{status.last_error}</div>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
};

export default DouyinRelayPanel;
