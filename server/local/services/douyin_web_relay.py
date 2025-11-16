# -*- coding: utf-8 -*-
"""Douyin 弹幕到 Web 网页的实时转发服务."""

from __future__ import annotations

import asyncio
import threading
import time
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set

from ..modules.douyin.liveMan import (
    ChatMessage,
    ControlMessage,
    DouyinLiveWebFetcher,
    EmojiChatMessage,
    FansclubMessage,
    GiftMessage,
    LikeMessage,
    MemberMessage,
    RoomMessage,
    RoomRankMessage,
    RoomStatsMessage,
    RoomStreamAdaptationMessage,
    RoomUserSeqMessage,
    SocialMessage,
)
from ..utils.service_logger import log_service_start, log_service_stop
from .douyin_connection_manager import get_connection_manager, reset_connection_manager

logger = logging.getLogger(__name__)


@dataclass
class RelayStatus:
    is_running: bool = False
    live_id: Optional[str] = None
    room_id: Optional[str] = None
    session_id: Optional[str] = None  # 🆕 绑定到统一会话
    last_error: Optional[str] = None


class _WebRelayFetcher(DouyinLiveWebFetcher):
    """DouyinLiveWebFetcher 的特化版本, 将消息透传给回调."""

    def __init__(self, live_id: str, emitter: Callable[[Dict[str, Any]], None]):
        super().__init__(live_id)
        self._emit = emitter

    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        try:
            self._emit(
                {
                    "type": event_type,
                    "payload": payload,
                    "timestamp": time.time(),
                }
            )
        except Exception:
            # 回调失败时忽略，以免影响主体流程
            pass

    def stop(self):  # type: ignore[override]
        try:
            if hasattr(self, "ws") and getattr(self, "ws", None):
                super().stop()
        except Exception:
            pass

    def _wsOnOpen(self, ws):  # noqa: N802
        # 🆕 记录WebSocket连接成功
        self._emit_event("status", {"stage": "connected", "websocket": True})
        super()._wsOnOpen(ws)

    def _wsOnError(self, ws, error):  # noqa: N802
        self._emit_event("error", {"message": str(error)})
        super()._wsOnError(ws, error)

    def _wsOnClose(self, ws, *args):  # noqa: N802
        # 🆕 记录WebSocket连接关闭
        self._emit_event("status", {"stage": "closed", "websocket": False})
        super()._wsOnClose(ws, *args)

    def _parseChatMsg(self, payload):  # noqa: N802
        message = ChatMessage().parse(payload)
        # 🆕 验证弹幕数据有效性
        content = message.content or ""
        user_id = message.user.id or ""
        nickname = message.user.nick_name or ""
        
        # 检查是否是假数据：内容为空、用户ID为空、或内容为纯空格
        if not content.strip() or not user_id or not nickname:
            logger.debug(f"过滤无效弹幕: content={content[:20]}, user_id={user_id}, nickname={nickname}")
            return
        
        # 检查内容长度是否合理（抖音弹幕通常不超过200字符）
        if len(content) > 500:
            logger.warning(f"弹幕内容异常长，可能是假数据: {len(content)}字符")
            return
        
        self._emit_event(
            "chat",
            {
                "user_id": user_id,
                "user_id_str": message.user.id_str,
                "nickname": nickname,
                "content": content,
            },
        )

    def _parseGiftMsg(self, payload):  # noqa: N802
        message = GiftMessage().parse(payload)
        count = message.combo_count or message.total_count or message.repeat_count or 1
        diamond_count = getattr(message.gift, "diamond_count", 0)
        fan_ticket = getattr(message, "fan_ticket_count", 0)
        gift_value = diamond_count * max(count, 1)
        self._emit_event(
            "gift",
            {
                "user_id": message.user.id,
                "user_id_str": message.user.id_str,
                "nickname": message.user.nick_name,
                "gift_name": message.gift.name,
                "count": count,
                "diamond_count": diamond_count,
                "fan_ticket_count": fan_ticket,
                "gift_value": gift_value,
            },
        )

    def _parseLikeMsg(self, payload):  # noqa: N802
        message = LikeMessage().parse(payload)
        self._emit_event(
            "like",
            {
                "user_id": message.user.id,
                "user_id_str": getattr(message.user, "id_str", None),
                "nickname": message.user.nick_name,
                "count": message.count,
                "total": getattr(message, "total", None),
            },
        )

    def _parseMemberMsg(self, payload):  # noqa: N802
        message = MemberMessage().parse(payload)
        gender = None
        try:
            gender = ["female", "male"][message.user.gender]
        except Exception:
            gender = getattr(message.user, "gender", None)
        self._emit_event(
            "member",
            {
                "user_id": message.user.id,
                "user_id_str": getattr(message.user, "id_str", None),
                "nickname": message.user.nick_name,
                "gender": gender,
                "level": getattr(message.user, "level", None),
                "action": "enter",
            },
        )

    def _parseSocialMsg(self, payload):  # noqa: N802
        message = SocialMessage().parse(payload)
        action = None
        social_info = getattr(message, "social_info", None)
        if social_info is not None:
            action = getattr(social_info, "action", None)
        self._emit_event(
            "follow",
            {
                "user_id": message.user.id,
                "user_id_str": getattr(message.user, "id_str", None),
                "nickname": message.user.nick_name,
                "action": action or "follow",
            },
        )

    def _parseRoomUserSeqMsg(self, payload):  # noqa: N802
        message = RoomUserSeqMessage().parse(payload)
        self._emit_event(
            "room_user_stats",
            {
                "current": message.total,
                "total": getattr(message, "total_pv_for_anchor", None),
                "display_short": getattr(message, "display_short", None),
                "display_long": getattr(message, "display_long", None),
            },
        )

    def _parseFansclubMsg(self, payload):  # noqa: N802
        message = FansclubMessage().parse(payload)
        user = getattr(message, "user", None)
        self._emit_event(
            "fansclub",
            {
                "content": message.content,
                "user_id": getattr(user, "id", None),
                "user_id_str": getattr(user, "id_str", None),
                "nickname": getattr(user, "nick_name", None),
            },
        )

    def _parseEmojiChatMsg(self, payload):  # noqa: N802
        message = EmojiChatMessage().parse(payload)
        user = getattr(message, "user", None)
        self._emit_event(
            "emoji_chat",
            {
                "emoji_id": message.emoji_id,
                "default_content": message.default_content,
                "user_id": getattr(user, "id", None),
                "nickname": getattr(user, "nick_name", None),
            },
        )

    def _parseRankMsg(self, payload):  # noqa: N802
        message = RoomRankMessage().parse(payload)
        ranks: List[Dict[str, Any]] = []
        # 安全处理 ranks_list，可能为 None
        ranks_list = getattr(message, 'ranks_list', None)
        if ranks_list is None:
            return
        # 确保 ranks_list 是可迭代的
        try:
            iter(ranks_list)
        except TypeError:
            return
        for item in ranks_list:
            avatar = None
            if item.user.avatar_thumb and item.user.avatar_thumb.url_list_list:
                avatar = item.user.avatar_thumb.url_list_list[0]
            ranks.append(
                {
                    "rank": item.rank,
                    "score": item.score,
                    "score_str": item.score_str,
                    "user_id": item.user.id,
                    "user_id_str": item.user.id_str,
                    "nickname": item.user.nick_name,
                    "avatar": avatar,
                }
            )
        if ranks:
            self._emit_event("room_rank", {"ranks": ranks})

    def _parseRoomMsg(self, payload):  # noqa: N802
        message = RoomMessage().parse(payload)
        common = getattr(message, "common", None)
        self._emit_event(
            "room_info",
            {
                "room_id": getattr(common, "room_id", None),
                "owner_user_id": getattr(common, "owner_user_id", None),
                "title": getattr(message, "title", None),
            },
        )

    def _parseRoomStatsMsg(self, payload):  # noqa: N802
        message = RoomStatsMessage().parse(payload)
        self._emit_event(
            "room_stats",
            {
                "display_long": message.display_long,
                "display_short": getattr(message, "display_short", None),
                "like_count": getattr(message, "like_count", None),
                "total_user": getattr(message, "total_user", None),
            },
        )

    def _parseControlMsg(self, payload):  # noqa: N802
        message = ControlMessage().parse(payload)
        self._emit_event(
            "room_control",
            {
                "status": message.status,
                "tips": getattr(message, "tips", None),
            },
        )
        if message.status == 3:
            self._emit_event("status", {"stage": "room_closed"})
            self.stop()

    def _parseRoomStreamAdaptationMsg(self, payload):  # noqa: N802
        message = RoomStreamAdaptationMessage().parse(payload)
        self._emit_event(
            "stream_adaptation",
            {
                "adaptation_type": message.adaptation_type,
                "enable_low_quality": getattr(message, "enable_low_quality", None),
            },
        )


class DouyinWebRelay:
    """管理 Douyin 抓取线程 -> Async Web 客户端的桥接器."""

    def __init__(self):
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._fetcher: Optional[_WebRelayFetcher] = None
        self._thread: Optional[threading.Thread] = None
        self._status = RelayStatus()
        self._clients: Set[asyncio.Queue] = set()
        self._last_status_event: Optional[Dict[str, Any]] = None
        self._last_rank_event: Optional[Dict[str, Any]] = None
        self._lock = asyncio.Lock()
        # persistence (默认开启弹幕持久化)
        self._persist_enabled: bool = True
        self._persist_root: Optional[str] = "records/live_logs"
        self._writer = None
        # 🆕 数据验证和监控
        self._message_count = 0  # 接收到的消息总数
        self._valid_message_count = 0  # 有效消息数
        self._last_message_time: Optional[float] = None  # 最后一条消息时间
        self._websocket_connected = False  # WebSocket连接状态
        self._signature_failures = 0  # 签名验证失败次数
        self._last_signature_check: Optional[float] = None  # 上次签名检查时间
        self._health_check_task: Optional[asyncio.Task] = None  # 健康检查任务
        
        # 🆕 Redis批量写入配置（弹幕数据）
        import os
        self._redis_batch_enabled: bool = bool(int(os.getenv("REDIS_BATCH_ENABLED", "1")))
        self._redis_batch_size: int = int(os.getenv("DANMU_BATCH_SIZE", "500"))
        self._redis_batch_interval: float = float(os.getenv("DANMU_BATCH_INTERVAL", "5.0"))
        self._redis_batch_buffer: List[Dict[str, Any]] = []
        self._redis_batch_task: Optional[asyncio.Task] = None

    # ------------------------------------------------------------------
    # 客户端管理
    # ------------------------------------------------------------------
    async def register_client(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._clients.add(queue)
        if self._last_status_event:
            queue.put_nowait(self._last_status_event)
        if self._last_rank_event:
            queue.put_nowait(self._last_rank_event)
        return queue

    async def unregister_client(self, queue: asyncio.Queue) -> None:
        self._clients.discard(queue)

    # ------------------------------------------------------------------
    # 启动 / 停止
    # ------------------------------------------------------------------
    async def start(self, live_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        async with self._lock:
            if self._status.is_running:
                if self._status.live_id == live_id:
                    return {"success": True, "message": "已经在抓取该直播间"}
                await self.stop()

            self._event_loop = asyncio.get_running_loop()
            self._status = RelayStatus(is_running=True, live_id=live_id, session_id=session_id)
            self._status.last_error = None
            self._status.room_id = None
            log_service_start("抖音直播互动服务", live_id=live_id)
            self._emit_status("starting", {"live_id": live_id})

            def emitter(event: Dict[str, Any]) -> None:
                if not self._event_loop:
                    return
                # 🆕 统计和验证消息
                event_type = event.get("type", "")
                if event_type in ["chat", "gift", "like", "member", "follow"]:
                    self._message_count += 1
                    payload = event.get("payload", {})
                    # 验证消息有效性
                    if payload.get("content") or payload.get("nickname") or payload.get("user_id"):
                        self._valid_message_count += 1
                    self._last_message_time = time.time()
                elif event_type == "status":
                    # 🆕 更新WebSocket连接状态
                    payload = event.get("payload", {})
                    if payload.get("websocket") is True:
                        self._websocket_connected = True
                    elif payload.get("websocket") is False:
                        self._websocket_connected = False
                
                self._event_loop.call_soon_threadsafe(self._dispatch_event, event)

            self._fetcher = _WebRelayFetcher(live_id, emitter)
            # 🆕 重置监控指标
            self._message_count = 0
            self._valid_message_count = 0
            self._last_message_time = None
            self._websocket_connected = False
            self._signature_failures = 0
            self._last_signature_check = None
            
            # 🆕 启动健康检查任务
            self._health_check_task = asyncio.create_task(self._health_check_loop())

            def runner():
                try:
                    emitter(
                        {
                            "type": "status",
                            "payload": {"stage": "resolving_room"},
                            "timestamp": time.time(),
                        }
                    )
                    
                    # 🔧 修复：按照原始版本的简单流程
                    # 1. 先尝试获取 room_id（通过属性访问，会自动触发获取逻辑）
                    # 2. 如果失败，使用重试机制
                    # 3. 成功获取后直接启动 WebSocket
                    
                    conn_mgr = get_connection_manager()
                    conn_mgr.reset()
                    conn_mgr.set_status_callback(emitter)
                    
                    room_id = None
                    
                    # 重试获取 room_id（最多10次）
                    while conn_mgr.should_retry():
                        attempt = conn_mgr.start_attempt()
                        
                        try:
                            # 🔧 修复：直接访问 room_id 属性，不要提前调用 get_room_status()
                            # room_id 属性会自动触发获取逻辑
                            room_id = self._fetcher.room_id
                            
                            # 确保 room_id 是字符串类型且有效
                            if room_id is not None:
                                room_id = str(room_id)
                                if room_id and room_id.strip():
                                    # 成功获取 room_id
                                    conn_mgr.record_success(f"成功获取房间ID: {room_id}")
                                    emitter(
                                        {
                                            "type": "status",
                                            "payload": {
                                                "stage": "room_ready",
                                                "room_id": room_id,
                                                "attempt": attempt,
                                            },
                                            "timestamp": time.time(),
                                        }
                                    )
                                    break
                            
                            # 未获取到 room_id
                            if not conn_mgr.record_failure("未能获取到 room_id"):
                                break
                            time.sleep(conn_mgr.calculate_delay())
                                    
                        except (ValueError, ConnectionError, RuntimeError) as exc:
                            # 记录异常并判断是否继续重试
                            error_msg = str(exc)
                            # 检测签名验证失败（防爬虫算法更新）
                            if "bogus" in error_msg.lower() or "signature" in error_msg.lower() or "403" in error_msg or "400" in error_msg:
                                self._signature_failures += 1
                                self._last_signature_check = time.time()
                                logger.warning(f"⚠️ 签名验证失败 (累计{self._signature_failures}次): {error_msg}")
                                if self._signature_failures >= 5:
                                    logger.error("🚨 检测到可能的防爬虫算法更新！签名验证失败率过高，请检查a_bogus.js和ac_signature.py算法")
                                    emitter(
                                        {
                                            "type": "warning",
                                            "payload": {
                                                "message": "检测到可能的防爬虫算法更新，请更新算法文件",
                                                "signature_failures": self._signature_failures,
                                                "error": error_msg
                                            },
                                            "timestamp": time.time(),
                                        }
                                    )
                            
                            if not conn_mgr.record_failure(exc):
                                break
                            time.sleep(conn_mgr.calculate_delay())
                        except Exception as exc:
                            # 其他未知异常，记录但继续重试
                            error_msg = str(exc)
                            if "NoneType" in error_msg or "not iterable" in error_msg:
                                if not conn_mgr.record_failure(f"抖音API响应异常: {error_msg}"):
                                    break
                            else:
                                if "bogus" in error_msg.lower() or "signature" in error_msg.lower() or "403" in error_msg or "400" in error_msg:
                                    self._signature_failures += 1
                                    self._last_signature_check = time.time()
                            
                            if not conn_mgr.record_failure(exc):
                                break
                            time.sleep(conn_mgr.calculate_delay())
                    
                    if not room_id:
                        # 所有重试都失败
                        status = conn_mgr.get_status()
                        emitter(
                            {
                                "type": "error",
                                "payload": {
                                    "message": f"无法获取房间ID (尝试{status['attempt']}次): {status['last_error']}",
                                    "success_rate": status['success_rate'],
                                },
                                "timestamp": time.time(),
                            }
                        )
                        return
                    
                    # 🔧 成功获取 room_id，直接启动 WebSocket 连接（与原始版本一致）
                    emitter(
                        {
                            "type": "status",
                            "payload": {"stage": "connecting_websocket"},
                            "timestamp": time.time(),
                        }
                    )
                    # 直接调用 start()，内部会自动处理 WebSocket 连接
                    self._fetcher.start()
                    
                except Exception as exc:
                    emitter(
                        {
                            "type": "error",
                            "payload": {"message": str(exc)},
                            "timestamp": time.time(),
                        }
                    )
                finally:
                    if self._event_loop:
                        self._event_loop.call_soon_threadsafe(self._thread_finished)

            self._thread = threading.Thread(
                target=runner, name="DouyinWebRelay", daemon=True
            )
            self._thread.start()
            # prepare persistence writer
            if self._persist_enabled:
                try:
                    from pathlib import Path
                    from ..utils.jsonl_writer import JSONLWriter  # type: ignore
                    root = Path(self._persist_root or "records").resolve()
                    
                    # 🆕 如果有关联的session_id，按session存储；否则按旧方式存储
                    if self._status.session_id:
                        from .live_session_manager import get_session_manager
                        session_mgr = get_session_manager()
                        session_dir = session_mgr.get_session_data_dir(self._status.session_id)
                        if session_dir:
                            out_dir = session_dir / "artifacts"
                            out_dir.mkdir(parents=True, exist_ok=True)
                            fn = out_dir / "comments.jsonl"
                        else:
                            # 回退到旧方式
                            day = time.strftime("%Y-%m-%d", time.localtime())
                            out_dir = root / "live_logs" / (self._status.live_id or "unknown") / day
                            out_dir.mkdir(parents=True, exist_ok=True)
                            fn = out_dir / f"danmu_{int(time.time())}.jsonl"
                    else:
                        # 旧方式：按日期和live_id存储
                        day = time.strftime("%Y-%m-%d", time.localtime())
                        out_dir = root / "live_logs" / (self._status.live_id or "unknown") / day
                        out_dir.mkdir(parents=True, exist_ok=True)
                        fn = out_dir / f"danmu_{int(time.time())}.jsonl"
                    
                    self._writer = JSONLWriter(fn)
                    self._writer.open()
                except Exception as e:
                    logger.warning(f"弹幕持久化初始化失败: {e}")
                    self._writer = None
            return {"success": True, "live_id": live_id}

    async def stop(self) -> Dict[str, Any]:
        async with self._lock:
            if not self._status.is_running:
                return {"success": True, "message": "未在运行"}

            # 🆕 更新统一会话状态
            try:
                if self._status.session_id:
                    from .live_session_manager import get_session_manager
                    session_mgr = get_session_manager()
                    if session_mgr:
                        await session_mgr.update_session(
                            douyin_relay_active=False
                        )
            except Exception as e:
                logger.warning(f"更新统一会话状态失败: {e}")

            fetcher = self._fetcher
            thread = self._thread
            live_id = self._status.live_id
            room_id = self._status.room_id
            session_id = self._status.session_id
            self._status.is_running = False
            self._status.live_id = None
            self._status.session_id = None

            log_service_stop("抖音直播互动服务", live_id=live_id, room_id=room_id, session_id=session_id)

            if fetcher:
                await asyncio.to_thread(fetcher.stop)
            if thread and thread.is_alive():
                await asyncio.to_thread(thread.join, 5)

            self._emit_status("stopped", {})
            self._fetcher = None
            self._thread = None
            self._status.room_id = None
            # close persistence
            try:
                if self._writer is not None:
                    self._writer.close()
            except Exception:
                pass
            self._writer = None
            # 🆕 停止健康检查任务
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
                self._health_check_task = None
            
            # 🆕 停止批量任务并flush剩余数据
            if self._redis_batch_task:
                self._redis_batch_task.cancel()
                try:
                    await self._redis_batch_task
                except asyncio.CancelledError:
                    pass
                self._redis_batch_task = None
            # 最后flush一次确保没有遗漏
            await self._flush_danmu_batch()
            
            return {"success": True}

    def _thread_finished(self) -> None:
        self._emit_status("stopped", {})
        self._fetcher = None
        self._thread = None
        self._status.is_running = False
        self._status.live_id = None
        self._status.room_id = None

    # ------------------------------------------------------------------
    # 事件派发
    # ------------------------------------------------------------------
    def _dispatch_event(self, event: Dict[str, Any]) -> None:
        event_type = event.get("type")
        if event_type == "status":
            stage = (event.get("payload") or {}).get("stage")
            if stage == "room_ready":
                room_id = (event.get("payload") or {}).get("room_id")
                # 确保 room_id 是字符串类型
                if room_id is not None:
                    self._status.room_id = str(room_id)
                else:
                    self._status.room_id = None
            elif stage == "stopped":
                self._status.room_id = None
            self._last_status_event = event
        elif event_type == "room_rank":
            self._last_rank_event = event
        elif event_type == "error":
            self._status.last_error = (event.get("payload") or {}).get("message")
        for queue in list(self._clients):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass
        # Persist non-status events
        try:
            if self._writer is not None and event_type not in {"status"}:
                self._writer.write(event)
        except Exception:
            pass
        
        # 🆕 Redis批量缓冲（弹幕和互动数据）
        if self._redis_batch_enabled and event_type in {"chat", "gift", "like", "member", "follow"}:
            asyncio.create_task(self._buffer_danmu_for_batch(event))

    def _emit_status(
        self, stage: str, payload: Optional[Dict[str, Any]] = None
    ) -> None:
        data = {
            "type": "status",
            "payload": {"stage": stage, **(payload or {})},
            "timestamp": time.time(),
        }
        if self._event_loop:
            self._event_loop.call_soon_threadsafe(self._dispatch_event, data)

    def get_status(self) -> RelayStatus:
        return self._status
    
    def get_health_status(self) -> Dict[str, Any]:
        """🆕 获取服务健康状态和监控信息"""
        now = time.time()
        # 计算数据质量指标
        valid_rate = (self._valid_message_count / self._message_count * 100) if self._message_count > 0 else 0.0
        time_since_last_msg = (now - self._last_message_time) if self._last_message_time else None
        
        # 判断是否在接收真实数据
        is_receiving_data = (
            self._websocket_connected and
            self._last_message_time is not None and
            (time_since_last_msg is None or time_since_last_msg < 60) and  # 60秒内有消息
            valid_rate > 50  # 有效消息率 > 50%
        )
        
        # 判断是否可能是假数据
        is_possible_fake_data = (
            self._message_count > 0 and
            (valid_rate < 30 or  # 有效消息率过低
             (time_since_last_msg and time_since_last_msg > 300))  # 5分钟没有消息
        )
        
        # 判断是否检测到算法更新
        algorithm_updated = (
            self._signature_failures >= 5 and
            (self._last_signature_check and (now - self._last_signature_check) < 3600)  # 1小时内
        )
        
        return {
            "is_receiving_data": is_receiving_data,
            "is_possible_fake_data": is_possible_fake_data,
            "algorithm_updated": algorithm_updated,
            "message_count": self._message_count,
            "valid_message_count": self._valid_message_count,
            "valid_rate": round(valid_rate, 2),
            "last_message_time": self._last_message_time,
            "time_since_last_msg": round(time_since_last_msg, 2) if time_since_last_msg else None,
            "websocket_connected": self._websocket_connected,
            "signature_failures": self._signature_failures,
            "last_signature_check": self._last_signature_check,
        }
    
    async def _health_check_loop(self):
        """🆕 定期健康检查，检测数据质量和连接状态"""
        try:
            while self._status.is_running:
                await asyncio.sleep(30)  # 每30秒检查一次
                
                if not self._status.is_running:
                    break
                
                health = self.get_health_status()
                
                # 检测假数据
                if health["is_possible_fake_data"]:
                    msg_time_str = f"{health['time_since_last_msg']:.1f}秒" if health['time_since_last_msg'] else "无消息"
                    logger.warning(
                        f"⚠️ 检测到可能的假数据：消息总数={self._message_count}, "
                        f"有效消息率={health['valid_rate']:.1f}%, "
                        f"距离最后消息={msg_time_str}"
                    )
                    # 发送警告事件
                    self._emit_status("warning", {
                        "message": "检测到可能的假数据或数据流中断",
                        "health": health
                    })
                
                # 检测算法更新
                if health["algorithm_updated"]:
                    logger.error(
                        f"🚨 检测到可能的防爬虫算法更新！签名验证失败{self._signature_failures}次"
                    )
                    self._emit_status("warning", {
                        "message": "检测到可能的防爬虫算法更新，请更新算法文件",
                        "signature_failures": self._signature_failures
                    })
                
                # 检测WebSocket连接状态
                if self._status.is_running and not health["websocket_connected"]:
                    logger.warning("⚠️ WebSocket未连接，但服务显示运行中")
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"健康检查任务异常: {e}")

    def get_persist(self) -> Dict[str, Any]:
        return {
            "persist_enabled": self._persist_enabled,
            "persist_root": self._persist_root,
        }

    def update_persist(self, *, enable: Optional[bool] = None, root: Optional[str] = None) -> Dict[str, Any]:
        if enable is not None:
            self._persist_enabled = bool(enable)
        if root is not None:
            self._persist_root = str(root)
        return {"persist_enabled": self._persist_enabled, "persist_root": self._persist_root}

    # 🆕 Redis批量入库相关方法
    async def _buffer_danmu_for_batch(self, event: Dict[str, Any]) -> None:
        """将弹幕/互动事件加入批量缓冲区"""
        try:
            async with self._lock:
                self._redis_batch_buffer.append(event)
                
                # 如果达到批量大小，立即触发写入
                if len(self._redis_batch_buffer) >= self._redis_batch_size:
                    await self._flush_danmu_batch()
            
            # 启动后台批量任务（如果尚未启动）
            if self._redis_batch_task is None or self._redis_batch_task.done():
                self._redis_batch_task = asyncio.create_task(self._batch_danmu_worker())
        except Exception as e:
            logger.error(f"缓冲弹幕数据失败: {e}")

    async def _batch_danmu_worker(self) -> None:
        """后台批量写入任务"""
        try:
            while self._status.is_running:
                await asyncio.sleep(self._redis_batch_interval)
                await self._flush_danmu_batch()
        except asyncio.CancelledError:
            # 任务被取消时，最后flush一次
            await self._flush_danmu_batch()
        except Exception as e:
            logger.error(f"批量弹幕任务异常: {e}")

    async def _flush_danmu_batch(self) -> None:
        """将缓冲的弹幕数据批量写入Redis"""
        try:
            async with self._lock:
                if not self._redis_batch_buffer:
                    return
                
                batch_to_write = self._redis_batch_buffer.copy()
                self._redis_batch_buffer.clear()
            
            if not batch_to_write:
                return
            
            # 写入Redis（按类型分类存储）
            # 本地服务不使用Redis
            # try:
            #     from ..utils.redis_manager import get_redis
            #     redis_mgr = get_redis()
            #     if redis_mgr:
            #         live_id = self._status.live_id or "unknown"
            #         
            #         import json
            #         # 分类统计
            #         chat_count = 0
            #         gift_count = 0
            #         like_count = 0
            #         
            #         for event in batch_to_write:
            #             event_type = event.get("type", "")
            #             
            #             # 弹幕消息 -> Redis List队列
            #             if event_type == "chat":
            #                 redis_key = f"danmu:{live_id}:queue"
            #                 redis_mgr.rpush(redis_key, json.dumps(event, ensure_ascii=False))
            #                 chat_count += 1
            #             
            #             # 礼物消息 -> Redis List队列
            #             elif event_type == "gift":
            #                 redis_key = f"gift:{live_id}:queue"
            #                 redis_mgr.rpush(redis_key, json.dumps(event, ensure_ascii=False))
            #                 gift_count += 1
            #             
            #             # 点赞消息 -> Redis计数器
            #             elif event_type == "like":
            #                 redis_key = f"like:{live_id}:count"
            #                 payload = event.get("payload", {})
            #                 count = payload.get("count", 1)
            #                 redis_mgr.incr(redis_key, count)
            #                 like_count += count
            #             
            #             # 其他互动消息 -> Redis List队列
            #             else:
            #                 redis_key = f"interaction:{live_id}:queue"
            #                 redis_mgr.rpush(redis_key, json.dumps(event, ensure_ascii=False))
            #         
            #         # 设置过期时间（24小时）
            #         for key_prefix in ["danmu", "gift", "like", "interaction"]:
            #             redis_key = f"{key_prefix}:{live_id}:queue" if key_prefix != "like" else f"{key_prefix}:{live_id}:count"
            #             redis_mgr.expire(redis_key, 86400)
            #         
            #         # 热词统计（使用Sorted Set）
            #         if chat_count > 0:
            #             await self._update_hotwords_in_redis(batch_to_write, live_id, redis_mgr)
            #         
            #         logger.info(
            #             f"批量写入Redis: 弹幕{chat_count}条, 礼物{gift_count}条, "
            #             f"点赞{like_count}次 -> {live_id}"
            #         )
            # except Exception as e:
            #     logger.error(f"写入Redis失败: {e}")
            
        except Exception as e:
            logger.error(f"刷新弹幕批次失败: {e}")

    # 本地服务不使用Redis热词统计
    # async def _update_hotwords_in_redis(
    #     self, batch: List[Dict[str, Any]], live_id: str, redis_mgr
    # ) -> None:
    #     """更新热词统计到Redis Sorted Set"""
    #     try:
    #         import re
    #         word_counter: Dict[str, int] = {}
    #         
    #         # 简单分词（按空格和标点分割）
    #         for event in batch:
    #             if event.get("type") != "chat":
    #                 continue
    #             
    #             content = event.get("payload", {}).get("content", "")
    #             if not content:
    #                 continue
    #             
    #             # 简单的中文分词（2-4字词）
    #             words = re.findall(r'[\u4e00-\u9fff]{2,4}', content)
    #             for word in words:
    #                 word_counter[word] = word_counter.get(word, 0) + 1
    #         
    #         # 批量更新到Redis Sorted Set
    #         if word_counter:
    #             redis_key = f"hotwords:{live_id}:sorted_set"
    #             for word, count in word_counter.items():
    #                 redis_mgr.zadd(redis_key, {word: count})
    #             redis_mgr.expire(redis_key, 86400)
    #     except Exception as e:
    #         logger.error(f"更新热词统计失败: {e}")


_relay_instance: Optional[DouyinWebRelay] = None


def get_douyin_web_relay() -> DouyinWebRelay:
    global _relay_instance
    if _relay_instance is None:
        _relay_instance = DouyinWebRelay()
    return _relay_instance
