# -*- coding: utf-8 -*-
"""Live Audio Agent - V2 Architecture

Wraps LiveAudioStreamService with Agent pattern for live audio transcription.
"""
from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any

from server.agents.base import BaseAgent, AgentResult


class LiveAudioAgentConfig(BaseModel):
    """Live Audio Agent 配置"""
    live_url: str
    session_id: Optional[str] = None
    mode: Literal["vad", "delta"] = "vad"
    model_size: Literal["small"] = "small"
    chunk_duration: float = 3.0
    vad_min_silence_sec: float = 0.8
    vad_min_speech_sec: float = 0.25
    vad_hangover_sec: float = 0.15
    profile: Literal["fast", "stable"] = "fast"


class LiveAudioAgentResult(AgentResult):
    """Live Audio Agent 结果"""
    session_id: str = ""
    live_id: str = ""
    live_url: str = ""
    ffmpeg_pid: Optional[int] = None
    is_running: bool = False
    details: Dict[str, Any] = {}


class LiveAudioAgent(BaseAgent[LiveAudioAgentResult]):
    """Live Audio Agent

    Manages live audio stream transcription from Douyin live streams.
    Integrates with VoiceAgent for ASR and uses RuntimeConfig for settings.

    Example:
        config = LiveAudioAgentConfig(live_url="https://live.douyin.com/123456")
        agent = LiveAudioAgent(config)
        result = await agent.start()

        # Later...
        await agent.stop()
    """

    def __init__(self, config: Optional[LiveAudioAgentConfig] = None):
        super().__init__(name="live_audio")
        self.config = config
        self._service = None

    def _get_service(self):
        """Lazy load the service to avoid import issues"""
        if self._service is None:
            from server.app.services.live_audio_stream_service import get_live_audio_service
            self._service = get_live_audio_service()
        return self._service

    async def run(self, input_data: dict) -> LiveAudioAgentResult:
        """执行 Agent 操作

        Args:
            input_data: {
                "action": "start" | "stop" | "status",
                "live_url": "...",  # for start
                "session_id": "...",  # optional
            }

        Returns:
            LiveAudioAgentResult
        """
        action = input_data.get("action", "status")

        if action == "start":
            return await self.start()
        elif action == "stop":
            return await self.stop()
        else:
            return await self.get_status()

    async def start(self) -> LiveAudioAgentResult:
        """启动直播音频转写

        Returns:
            LiveAudioAgentResult with session info
        """
        if not self.config:
            return LiveAudioAgentResult(
                success=False,
                error="Config required for start action. Provide LiveAudioAgentConfig."
            )

        try:
            service = self._get_service()

            # Apply configuration to service
            if self.config.chunk_duration:
                service.chunk_seconds = self.config.chunk_duration
            service.mode = self.config.mode
            service.set_model_size(self.config.model_size)

            # Start the service
            status = await service.start(
                self.config.live_url,
                self.config.session_id
            )

            return LiveAudioAgentResult(
                success=True,
                session_id=status.session_id or "",
                live_id=status.live_id or "",
                live_url=status.live_url or "",
                ffmpeg_pid=status.ffmpeg_pid,
                is_running=True,
                details={
                    "mode": self.config.mode,
                    "model_size": self.config.model_size,
                    "chunk_duration": self.config.chunk_duration,
                }
            )
        except Exception as e:
            return LiveAudioAgentResult(
                success=False,
                error=str(e),
                is_running=False
            )

    async def stop(self) -> LiveAudioAgentResult:
        """停止直播音频转写

        Returns:
            LiveAudioAgentResult with final status
        """
        try:
            service = self._get_service()
            status = await service.stop()

            return LiveAudioAgentResult(
                success=True,
                session_id=status.session_id or "",
                live_id=status.live_id or "",
                is_running=False
            )
        except Exception as e:
            return LiveAudioAgentResult(
                success=False,
                error=str(e)
            )

    async def get_status(self) -> LiveAudioAgentResult:
        """获取当前转写状态

        Returns:
            LiveAudioAgentResult with current status
        """
        try:
            service = self._get_service()
            status = service.status()

            return LiveAudioAgentResult(
                success=True,
                session_id=status.session_id or "",
                live_id=status.live_id or "",
                live_url=status.live_url or "",
                ffmpeg_pid=status.ffmpeg_pid,
                is_running=status.is_running,
                details={
                    "is_receiving_audio": getattr(status, 'is_receiving_audio', False),
                    "audio_chunk_count": getattr(status, 'audio_chunk_count', 0),
                }
            )
        except Exception as e:
            return LiveAudioAgentResult(
                success=False,
                error=str(e)
            )

    async def health_check(self) -> bool:
        """健康检查

        Returns:
            True if service is available
        """
        try:
            service = self._get_service()
            return service is not None
        except Exception:
            return False

    def add_transcription_callback(self, name: str, callback) -> None:
        """添加转写结果回调

        Args:
            name: Callback identifier
            callback: Async callback function
        """
        service = self._get_service()
        service.add_transcription_callback(name, callback)

    def add_level_callback(self, name: str, callback) -> None:
        """添加音量级别回调

        Args:
            name: Callback identifier
            callback: Callback function
        """
        service = self._get_service()
        service.add_level_callback(name, callback)

    def remove_transcription_callback(self, name: str) -> None:
        """移除转写结果回调"""
        service = self._get_service()
        service.remove_transcription_callback(name)

    def remove_level_callback(self, name: str) -> None:
        """移除音量级别回调"""
        service = self._get_service()
        service.remove_level_callback(name)
