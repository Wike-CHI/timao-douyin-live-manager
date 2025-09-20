# -*- coding: utf-8 -*-
"""
DouyinLiveFetcher: 基于 F2 的抖音直播互动数据抓取器
- 提供启动/停止/状态查询接口
- 通过适配器将事件输出到目标系统
- 封装 F2 DouyinHandler 以保持与 server/app/services/douyin_service 对齐
"""
from __future__ import annotations

import sys
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

# 动态加入 F2 路径
F2_PATH = Path(__file__).resolve().parent.parent / "f2"
if str(F2_PATH) not in sys.path:
    sys.path.insert(0, str(F2_PATH))

try:
    from f2.apps.douyin.handler import DouyinHandler
    from f2.apps.douyin.utils import TokenManager
except Exception as e:
    logging.getLogger(__name__).error(f"导入 F2 模块失败: {e}")
    raise

from .adapters import LiveDataAdapter, NoopAdapter


@dataclass
class FetcherStatus:
    is_running: bool
    room_id: Optional[str]
    live_id: Optional[str]
    callbacks_count: int


class DouyinLiveFetcher:
    """抖音直播互动数据抓取器"""

    def __init__(self, adapter: Optional[LiveDataAdapter] = None) -> None:
        self._logger = logging.getLogger(__name__)
        self._adapter: LiveDataAdapter = adapter or NoopAdapter()
        self._handler_http: Optional[DouyinHandler] = None
        self._handler_wss: Optional[DouyinHandler] = None
        self._is_running: bool = False
        self._room_id: Optional[str] = None
        self._live_id: Optional[str] = None

        # F2 请求参数
        self._http_kwargs = {
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Referer": "https://www.douyin.com/",
                "Content-Type": "application/protobuffer;",
            },
            "proxies": {"http://": None, "https://": None},
            "timeout": 10,
            "cookie": f"ttwid={TokenManager.gen_ttwid()}; __live_version__=\"1.1.2.6631\"; live_use_vvc=\"false\";",
        }
        self._wss_kwargs = {
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Upgrade": "websocket",
                "Connection": "Upgrade",
            },
            "proxies": {"http://": None, "https://": None},
            "timeout": 10,
            "show_message": False,
            "cookie": "",
        }

        # WebSocket 回调映射
        self._wss_callbacks = {
            "WebcastChatMessage": self._on_chat,
            "WebcastGiftMessage": self._on_gift,
            "WebcastLikeMessage": self._on_like,
            "WebcastMemberMessage": self._on_member,
            "WebcastSocialMessage": self._on_social,
            "WebcastRoomUserSeqMessage": self._on_room_stats,
        }

    def _normalize_cookie(self, cookie: Union[str, Dict[str, Any], None]) -> Optional[str]:
        if cookie is None:
            return None
        if isinstance(cookie, str):
            return cookie.strip()
        if isinstance(cookie, dict):
            # 简单拼接为 k=v; k2=v2 格式
            parts = []
            for k, v in cookie.items():
                parts.append(f"{k}={v}")
            return "; ".join(parts)
        return str(cookie)

    async def start(self, live_id: str, cookie: Optional[Union[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """启动抓取，可选传入 cookie 覆盖默认的 ttwid 方案"""
        if self._is_running:
            return {"success": False, "error": "fetcher already running"}

        try:
            # 应用外部 cookie 覆盖
            norm_cookie = self._normalize_cookie(cookie)
            if norm_cookie:
                self._http_kwargs["cookie"] = norm_cookie
                self._wss_kwargs["cookie"] = norm_cookie
                self._logger.info("已应用外部提供的 Cookie")

            self._logger.info(f"启动抖音抓取 live_id={live_id}")
            self._handler_http = DouyinHandler(self._http_kwargs)

            # 游客信息
            user = await self._handler_http.fetch_query_user()
            if not user:
                raise RuntimeError("获取游客信息失败")

            room = await self._handler_http.fetch_user_live_videos(live_id)
            if not room:
                raise RuntimeError("获取直播间信息失败")
            if getattr(room, "live_status", 0) != 2:
                raise RuntimeError("直播间未开播")

            live_im = await self._handler_http.fetch_live_im(
                room_id=room.room_id, unique_id=user.user_unique_id
            )
            if not live_im:
                raise RuntimeError("获取直播间IM信息失败")

            self._room_id = room.room_id
            self._live_id = live_id
            self._is_running = True

            # 适配器 on_start
            await self._adapter.on_start(
                {
                    "room_id": self._room_id,
                    "live_id": self._live_id,
                    "user_unique_id": user.user_unique_id,
                    "cursor": live_im.cursor,
                }
            )

            # 启动 WSS 监听（后台任务）
            asyncio.create_task(
                self._run_wss(
                    room_id=self._room_id,
                    user_unique_id=user.user_unique_id,
                    internal_ext=live_im.internal_ext,
                    cursor=live_im.cursor,
                )
            )

            return {
                "success": True,
                "room_id": self._room_id,
                "live_id": self._live_id,
                "user_unique_id": user.user_unique_id,
            }
        except Exception as e:
            self._logger.error(f"启动抓取失败: {e}")
            await self.stop()
            return {"success": False, "error": str(e)}

    async def stop(self) -> Dict[str, Any]:
        """停止抓取"""
        if not self._is_running:
            return {"success": False, "error": "fetcher not running"}

        self._is_running = False
        self._room_id = None
        self._live_id = None
        try:
            await self._adapter.on_stop()
        except Exception as e:
            self._logger.warning(f"停止适配器时出错: {e}")
        return {"success": True}

    def status(self) -> FetcherStatus:
        return FetcherStatus(
            is_running=self._is_running,
            room_id=self._room_id,
            live_id=self._live_id,
            callbacks_count=1,  # 适配器作为单一出口
        )

    async def _run_wss(self, room_id: str, user_unique_id: str, internal_ext: str, cursor: str):
        try:
            self._handler_wss = DouyinHandler(self._wss_kwargs)
            await self._handler_wss.fetch_live_danmaku(
                room_id=room_id,
                user_unique_id=user_unique_id,
                internal_ext=internal_ext,
                cursor=cursor,
                wss_callbacks=self._wss_callbacks,
            )
        except Exception as e:
            self._logger.error(f"WSS 监听异常: {e}")
            self._is_running = False

    # 事件处理：将 F2 消息转换为统一结构并交给适配器
    async def _on_chat(self, msg) -> None:
        try:
            data = {
                "type": "chat",
                "id": str(getattr(msg, "msgId", "")),
                "username": getattr(getattr(msg, "user", None), "nickName", ""),
                "content": getattr(msg, "content", ""),
                "user_id": str(getattr(getattr(msg, "user", None), "id", "")),
                "user_level": getattr(getattr(msg, "user", None), "level", 0),
                "timestamp": datetime.now().isoformat(),
                "room_id": self._room_id,
            }
            await self._adapter.handle("chat", data)
        except Exception as e:
            self._logger.error(f"处理聊天消息失败: {e}")

    async def _on_gift(self, msg) -> None:
        try:
            gift = getattr(msg, "gift", None)
            data = {
                "type": "gift",
                "id": str(getattr(msg, "msgId", "")),
                "username": getattr(getattr(msg, "user", None), "nickName", ""),
                "gift_name": getattr(gift, "name", ""),
                "gift_count": getattr(msg, "comboCount", 0),
                "gift_id": getattr(gift, "id", 0),
                "timestamp": datetime.now().isoformat(),
                "room_id": self._room_id,
            }
            await self._adapter.handle("gift", data)
        except Exception as e:
            self._logger.error(f"处理礼物消息失败: {e}")

    async def _on_like(self, msg) -> None:
        try:
            data = {
                "type": "like",
                "id": str(getattr(msg, "msgId", "")),
                "username": getattr(getattr(msg, "user", None), "nickName", ""),
                "like_count": getattr(msg, "count", 0),
                "timestamp": datetime.now().isoformat(),
                "room_id": self._room_id,
            }
            await self._adapter.handle("like", data)
        except Exception as e:
            self._logger.error(f"处理点赞消息失败: {e}")

    async def _on_member(self, msg) -> None:
        try:
            data = {
                "type": "member",
                "id": str(getattr(msg, "msgId", "")),
                "username": getattr(getattr(msg, "user", None), "nickName", ""),
                "action": getattr(msg, "action", "enter"),
                "timestamp": datetime.now().isoformat(),
                "room_id": self._room_id,
            }
            await self._adapter.handle("member", data)
        except Exception as e:
            self._logger.error(f"处理成员消息失败: {e}")

    async def _on_social(self, msg) -> None:
        try:
            data = {
                "type": "social",
                "id": str(getattr(msg, "msgId", "")),
                "username": getattr(getattr(msg, "user", None), "nickName", ""),
                "action": getattr(msg, "action", ""),
                "timestamp": datetime.now().isoformat(),
                "room_id": self._room_id,
            }
            await self._adapter.handle("social", data)
        except Exception as e:
            self._logger.error(f"处理社交消息失败: {e}")

    async def _on_room_stats(self, msg) -> None:
        try:
            data = {
                "type": "room_stats",
                "online": getattr(msg, "online", 0),
                "total": getattr(msg, "total", 0),
                "timestamp": datetime.now().isoformat(),
                "room_id": self._room_id,
            }
            await self._adapter.handle("room_stats", data)
        except Exception as e:
            self._logger.error(f"处理房间统计失败: {e}")