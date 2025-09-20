# -*- coding: utf-8 -*-
"""
数据适配器定义与默认实现
用于将 F2 抓取到的直播互动数据，适配到目标系统的数据流（如 WebSocket 广播、数据持久化等）。
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, List
from datetime import datetime

# 统一的消息数据结构约定：
# {
#   "type": "chat"|"gift"|"like"|"member"|"social"|"room_stats",
#   ... 其他字段见 service.DouyinLiveFetcher 回调规范
# }

class LiveDataAdapter(ABC):
    """抽象适配器: 将抓取的数据分发到目标系统"""

    @abstractmethod
    async def handle(self, message_type: str, data: Dict[str, Any]) -> None:
        """处理单条消息"""
        raise NotImplementedError

    async def on_start(self, context: Optional[Dict[str, Any]] = None) -> None:
        """抓取开始时触发，可用于初始化资源"""
        return None

    async def on_stop(self) -> None:
        """抓取停止时触发，可用于释放资源"""
        return None


class NoopAdapter(LiveDataAdapter):
    """默认空适配器，不做任何处理"""

    async def handle(self, message_type: str, data: Dict[str, Any]) -> None:
        return None


class CallbackAdapter(LiveDataAdapter):
    """将消息转发给外部 callback 的适配器"""

    def __init__(self, callback: Callable[[str, Dict[str, Any]], Any]):
        self._callback = callback

    async def handle(self, message_type: str, data: Dict[str, Any]) -> None:
        if asyncio.iscoroutinefunction(self._callback):
            await self._callback(message_type, data)
        else:
            self._callback(message_type, data)


class CompositeAdapter(LiveDataAdapter):
    """组合适配器：顺序调用多个适配器"""

    def __init__(self, adapters: Optional[List[LiveDataAdapter]] = None) -> None:
        self._adapters: List[LiveDataAdapter] = adapters or []

    def add(self, adapter: LiveDataAdapter) -> None:
        self._adapters.append(adapter)

    async def on_start(self, context: Optional[Dict[str, Any]] = None) -> None:
        for ad in self._adapters:
            try:
                await ad.on_start(context)
            except Exception:
                # 即使某个适配器出错，也不阻断其它适配器
                pass

    async def on_stop(self) -> None:
        for ad in self._adapters:
            try:
                await ad.on_stop()
            except Exception:
                pass

    async def handle(self, message_type: str, data: Dict[str, Any]) -> None:
        for ad in self._adapters:
            try:
                await ad.handle(message_type, data)
            except Exception:
                pass


# 可选：与 server.websocket_handler.LiveDataBroadcaster 对接的适配器
class WebsocketBroadcasterAdapter(LiveDataAdapter):
    """将聊天与统计等事件映射到现有 WebSocket 广播器，并写入数据管理器"""

    def __init__(self) -> None:
        # 无需显式依赖，延迟导入 server 侧对象
        pass

    async def handle(self, message_type: str, data: Dict[str, Any]) -> None:
        # 当前系统主要关注 chat（评论），其他类型可按需扩展
        if message_type == "chat":
            # 延迟导入，避免在未安装/未加载 server 包时出错
            from server.models import Comment, data_manager
            from server.websocket_handler import broadcast_comment as ws_broadcast_comment

            # 生成 Comment 实例（尽量从数据中取值，缺失时回退）
            # timestamp 优先解析 ISO 格式，失败时取当前时间
            ts = data.get("timestamp")
            ts_ms: int
            try:
                if isinstance(ts, (int, float)):
                    # 视为秒或毫秒：> 1e12 认为已是毫秒
                    ts_ms = int(ts if ts > 1e12 else ts * 1000)
                elif isinstance(ts, str):
                    ts_ms = int(datetime.fromisoformat(ts).timestamp() * 1000)
                else:
                    ts_ms = int(datetime.now().timestamp() * 1000)
            except Exception:
                ts_ms = int(datetime.now().timestamp() * 1000)

            comment = Comment(
                user=data.get("username") or "",
                content=data.get("content") or "",
                timestamp=ts_ms,
                platform="douyin",
                room_id=data.get("room_id") or "",
                user_id=str(data.get("user_id") or ""),
                user_level=int(data.get("user_level") or 0),
                is_vip=bool(data.get("is_vip") or False),
                gift_count=int(data.get("gift_count") or 0),
                metadata={}
            )

            # 写入数据管理器，维持现有统计/热词等流水线
            data_manager.add_comment(comment)
            # 立即广播单条评论给前端
            ws_broadcast_comment(comment)
        elif message_type == "room_stats":
            # 如需映射统计，可在此扩展
            pass
        else:
            # 其他类型暂不处理，保留扩展点
            pass