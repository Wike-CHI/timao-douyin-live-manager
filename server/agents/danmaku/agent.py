# -*- coding: utf-8 -*-
"""Danmaku Agent - 弹幕处理

Wraps DouyinWebRelay with Agent pattern for danmaku collection.
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any

from server.agents.base import BaseAgent, AgentResult


class DanmakuAgentConfig(BaseModel):
    """Danmaku Agent 配置"""
    live_id: str
    session_id: Optional[str] = None
    persist_enabled: bool = True
    persist_root: Optional[str] = None


class DanmakuAgentResult(AgentResult):
    """Danmaku Agent 结果"""
    live_id: str = ""
    room_id: Optional[str] = None
    is_running: bool = False
    message_count: int = 0
    websocket_connected: bool = False
    details: Dict[str, Any] = {}


class DanmakuAgent(BaseAgent[DanmakuAgentResult]):
    """Danmaku Agent

    Manages Douyin live danmaku (bullet comment) collection.
    Provides unified interface for starting/stopping danmaku monitoring.

    Example:
        config = DanmakuAgentConfig(live_id="123456")
        agent = DanmakuAgent(config)
        result = await agent.start()

        # Later...
        await agent.stop()
    """

    def __init__(self, config: Optional[DanmakuAgentConfig] = None):
        super().__init__(name="danmaku")
        self.config = config
        self._relay = None

    def _get_relay(self):
        """Lazy load the relay to avoid import issues"""
        if self._relay is None:
            from server.app.services.douyin_web_relay import get_douyin_web_relay
            self._relay = get_douyin_web_relay()
        return self._relay

    async def run(self, input_data: dict) -> DanmakuAgentResult:
        """执行 Agent 操作

        Args:
            input_data: {
                "action": "start" | "stop" | "status",
                "live_id": "...",  # for start
                "session_id": "...",  # optional
            }

        Returns:
            DanmakuAgentResult
        """
        action = input_data.get("action", "status")

        if action == "start":
            return await self.start()
        elif action == "stop":
            return await self.stop()
        else:
            return await self.get_status()

    async def start(self) -> DanmakuAgentResult:
        """启动弹幕采集

        Returns:
            DanmakuAgentResult with session info
        """
        if not self.config:
            return DanmakuAgentResult(
                success=False,
                error="Config required for start action. Provide DanmakuAgentConfig."
            )

        try:
            relay = self._get_relay()

            # Start the relay
            result = await relay.start(
                self.config.live_id,
                self.config.session_id
            )

            # Get current status
            status = relay.get_status()

            return DanmakuAgentResult(
                success=True,
                live_id=status.live_id or self.config.live_id,
                room_id=status.room_id,
                is_running=True,
                details={
                    "persist_enabled": self.config.persist_enabled,
                    "session_id": self.config.session_id,
                }
            )
        except Exception as e:
            return DanmakuAgentResult(
                success=False,
                error=str(e),
                is_running=False
            )

    async def stop(self) -> DanmakuAgentResult:
        """停止弹幕采集

        Returns:
            DanmakuAgentResult with final status
        """
        try:
            relay = self._get_relay()
            await relay.stop()

            return DanmakuAgentResult(
                success=True,
                is_running=False
            )
        except Exception as e:
            return DanmakuAgentResult(
                success=False,
                error=str(e)
            )

    async def get_status(self) -> DanmakuAgentResult:
        """获取当前状态

        Returns:
            DanmakuAgentResult with current status
        """
        try:
            relay = self._get_relay()
            status = relay.get_status()
            health = relay.get_health_status()

            return DanmakuAgentResult(
                success=True,
                live_id=status.live_id or "",
                room_id=status.room_id,
                is_running=status.is_running,
                message_count=health.get("message_count", 0),
                websocket_connected=health.get("websocket_connected", False),
                details={
                    "webcast_status": getattr(status, 'webcast_status', None),
                }
            )
        except Exception as e:
            return DanmakuAgentResult(
                success=False,
                error=str(e)
            )

    async def health_check(self) -> bool:
        """健康检查

        Returns:
            True if relay is available
        """
        try:
            relay = self._get_relay()
            return relay is not None
        except Exception:
            return False

    async def register_client_queue(self):
        """注册客户端队列用于接收弹幕事件

        Returns:
            asyncio.Queue for receiving danmaku events
        """
        relay = self._get_relay()
        return await relay.register_client()

    def unregister_client_queue(self, queue) -> None:
        """注销客户端队列

        Args:
            queue: The queue to unregister
        """
        relay = self._get_relay()
        relay.unregister_client(queue)
