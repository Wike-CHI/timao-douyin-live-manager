import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  DouyinRelayStatus,
  DouyinStreamEvent,
  getDouyinRelayStatus,
  openDouyinStream,
  startDouyinRelay,
  stopDouyinRelay,
} from '../../services/douyin';

const DEFAULT_MAX_MESSAGES = 80;
const DEFAULT_MAX_EVENTS = 120;

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

// Non chat/gift events that we will show in a separate panel
type OtherEventType =
  | 'like'
  | 'member'
  | 'follow'
  | 'fansclub'
  | 'emoji_chat'
  | 'room_info'
  | 'room_stats'
  | 'room_user_stats'
  | 'room_rank'
  | 'room_control'
  | 'stream_adaptation'
  | 'status'
  | 'error';

interface OtherEventEntry {
  id: string;
  type: OtherEventType;
  text: string;
  timestamp: number;
}

interface DouyinRelayPanelProps {
  baseUrl?: string;
  maxMessages?: number;
  onSelectQuestion?: (entry: ChatEntry) => void;
  liveId?: string; // 添加 liveId 属性，从父组件传入
  isRunning?: boolean; // 添加运行状态属性
  onStart?: () => void; // 添加启动回调
  onStop?: () => void; // 添加停止回调
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

const DouyinRelayPanel = ({ 
  baseUrl, 
  maxMessages = DEFAULT_MAX_MESSAGES, 
  onSelectQuestion,
  liveId, // 从父组件接收 liveId
  isRunning, // 从父组件接收运行状态
  onStart, // 从父组件接收启动回调
  onStop // 从父组件接收停止回调
}: DouyinRelayPanelProps) => {
  const [status, setStatus] = useState<DouyinRelayStatus | null>(null);
  const [chatLog, setChatLog] = useState<ChatEntry[]>([]);
  const [rankList, setRankList] = useState<RankEntry[]>([]);
  const [eventLog, setEventLog] = useState<OtherEventEntry[]>([]);
  const [banner, setBanner] = useState<{ tone: StatusTone; message: string } | null>({
    tone: 'info',
    message: '等待启动直播互动',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamConnected, setStreamConnected] = useState(false);

  const eventSourceRef = useRef<EventSource | null>(null);
  const lastStartedLiveIdRef = useRef<string>('');

  // Event filter toggles; by default show core interactive events, hide room_* noise
  const [eventFilters, setEventFilters] = useState<Record<OtherEventType, boolean>>({
    like: true,
    member: true,
    follow: true,
    fansclub: true,
    emoji_chat: true,
    room_info: false,
    room_stats: false,
    room_user_stats: false,
    room_rank: false,
    room_control: false,
    stream_adaptation: false,
    status: true,
    error: true,
  });

  const appendChat = useCallback((entry: ChatEntry) => {
    // 不裁剪条数：完整保留会话中的弹幕/礼物/点赞；滚动列表负责展示
    setChatLog((prev) => [entry, ...prev]);
  }, []);

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

  const appendEvent = useCallback((entry: OtherEventEntry) => {
    // 不裁剪条数：完整保留互动事件历史；滚动列表负责展示
    setEventLog((prev) => [entry, ...prev]);
  }, []);

  // Build short text for event panel
  const buildEventText = (type: OtherEventType, payload: Record<string, unknown> | null | undefined): string => {
    const p = payload || {};
    const nick = (p.nickname as string) || '匿名';
    switch (type) {
      case 'like': {
        const c = p.count as number | undefined;
        return c && c > 1 ? `${nick} 点赞 +${c}` : `${nick} 点赞`;
      }
      case 'member':
        return `${nick} 进入直播间`;
      case 'follow':
        return `${nick} 关注了主播`;
      case 'fansclub': {
        const content = (p.content as string) || '';
        return content ? `粉丝团：${content} — ${nick}` : `粉丝团互动 — ${nick}`;
      }
      case 'emoji_chat': {
        const content = (p.default_content as string) || '';
        return content ? `表情：${content} — ${nick}` : `表情互动 — ${nick}`;
      }
      case 'room_info': {
        const title = (p.title as string) || '';
        return title ? `房间信息更新：${title}` : '房间信息更新';
      }
      case 'room_stats': {
        const likeCount = (p.like_count as number | undefined) ?? null;
        const totalUser = (p.total_user as number | undefined) ?? null;
        const parts = [
          totalUser != null ? `人气 ${totalUser}` : '',
          likeCount != null ? `点赞 ${likeCount}` : '',
        ].filter(Boolean);
        return parts.length ? `统计：${parts.join(' · ')}` : '统计更新';
      }
      case 'room_user_stats': {
        const current = (p.current as number | undefined) ?? null;
        const total = (p.total as number | undefined) ?? null;
        return `在线 ${current ?? '-'} · 累计 ${total ?? '-'}`;
      }
      case 'room_control': {
        const statusTxt = String((p.status as unknown) ?? '-');
        return `房间控制：状态 ${statusTxt}`;
      }
      case 'stream_adaptation': {
        const t = (p.adaptation_type as number | string | undefined) ?? '-';
        const low = (p.enable_low_quality as boolean | undefined) ?? false;
        return `流自适应：type=${t} · 低码率=${low ? '是' : '否'}`;
      }
      case 'status': {
        const stage = (p.stage as string | undefined) || '-';
        return `状态：${stage}`;
      }
      case 'error': {
        const msg = (p.message as string | undefined) || '未知错误';
        return `错误：${msg}`;
      }
      case 'room_rank':
        return '排行榜更新';
      default:
        return String(type);
    }
  };

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
          appendEvent({
            id: `status-${event.timestamp ?? Date.now()}-${Math.random()}`,
            type: 'status',
            text: buildEventText('status', payload),
            timestamp: Date.now(),
          });
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
          appendEvent({
            id: `error-${event.timestamp ?? Date.now()}-${Math.random()}`,
            type: 'error',
            text: buildEventText('error', payload),
            timestamp: Date.now(),
          });
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
        case 'like':
        case 'member':
        case 'fansclub':
        case 'follow':
        case 'emoji_chat':
        case 'room_info':
        case 'room_stats':
        case 'room_user_stats':
        case 'room_control':
        case 'stream_adaptation': {
          const t = event.type as OtherEventType;
          appendEvent({
            id: `${t}-${event.timestamp ?? Date.now()}-${Math.random()}`,
            type: t,
            text: buildEventText(t, payload),
            timestamp: Date.now(),
          });
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

  // 使用从父组件传入的 liveId 和 isRunning 状态
  useEffect(() => {
    if (isRunning && liveId) {
      // 启动抖音直播互动（带重试机制）
      const startDouyin = async () => {
        let retries = 0;
        const maxRetries = 5;
        while (retries < maxRetries) {
          try {
            setLoading(true);
            setError(null);
            await startDouyinRelay(liveId, baseUrl);
            lastStartedLiveIdRef.current = liveId;
            await refreshStatus();
            connectStream();
            console.log('抖音直播互动服务启动成功');
            break; // 成功启动则退出循环
          } catch (e) {
            retries++;
            console.error(`抖音直播互动服务启动失败 (尝试 ${retries}/${maxRetries}):`, e);
            if (retries >= maxRetries) {
              setError((e as Error).message || '启动失败');
            } else {
              // 等待一段时间后重试
              await new Promise(resolve => setTimeout(resolve, 2000 * retries));
            }
          } finally {
            if (retries >= maxRetries || !loading) {
              setLoading(false);
            }
          }
        }
      };
      startDouyin();
    } else if (!isRunning) {
      // 停止抖音直播互动
      const stopDouyin = async () => {
        try {
          setLoading(true);
          setError(null);
          await stopDouyinRelay(baseUrl);
          disconnectStream();
          await refreshStatus();
          console.log('抖音直播互动服务停止成功');
        } catch (e) {
          console.error('抖音直播互动服务停止失败:', e);
          setError((e as Error).message || '停止失败');
        } finally {
          setLoading(false);
        }
      };
      stopDouyin();
    }
  }, [isRunning, liveId, baseUrl, connectStream, disconnectStream, refreshStatus]);

  useEffect(() => {
    refreshStatus();
    return () => {
      disconnectStream();
    };
  }, [refreshStatus, disconnectStream]);

  const currentStatusText = useMemo(() => {
    if (isRunning) {
      const liveIdText = status?.live_id ?? (lastStartedLiveIdRef.current || '未知');
      return `直播间 ${liveIdText} 正在同步`;
    }
    return '未运行 · 等待上层启动';
  }, [isRunning, status?.live_id]);

  const filteredEvents = useMemo(() => {
    return eventLog.filter((e) => eventFilters[e.type]);
  }, [eventLog, eventFilters]);

  const toggleFilter = (key: OtherEventType) => {
    setEventFilters((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <section className="space-y-3">
      {/* 删除原有的标题区域，包含抖音直播互动标签、状态提示文本、功能描述标签、直播状态图标 */}

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

      {/* 只显示弹幕数据，隐藏互动事件和粉丝贡献榜 */}
      <div className="flex h-full flex-col">
        <div className="mb-3 flex items-center justify-between">
          <h4 className="flex items-center gap-2 text-sm font-semibold text-purple-600">
            <span>💬</span>
            实时弹幕
          </h4>
          <span className="text-xs timao-support-text">{chatLog.length} 条</span>
        </div>
        <div className="max-h-[400px] space-y-3 overflow-y-auto pr-1 flex-1 custom-scrollbar">
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
                {onSelectQuestion && item.category === 'chat' ? (
                  <div className="mt-2 flex justify-end">
                    <button
                      className="timao-outline-btn text-[11px] px-2 py-0.5"
                      onClick={() => onSelectQuestion(item)}
                      disabled={false}
                      title="生成答疑话术"
                    >
                      生成答疑话术
                    </button>
                  </div>
                ) : null}
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
};

export default DouyinRelayPanel;