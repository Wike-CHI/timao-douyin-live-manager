# -*- coding: utf-8 -*-
"""V2 Live Audio API - Using LiveAudioAgent

Integrates Pydantic AI architecture with live audio streaming.
Provides REST endpoints for live audio transcription control.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from server.agents.live_audio import LiveAudioAgent, LiveAudioAgentConfig, LiveAudioAgentResult
from server.app.core.runtime_config import runtime_config


router = APIRouter(prefix="/api/v2/live_audio", tags=["Live Audio V2"])


# Request Models
class StartLiveAudioRequest(BaseModel):
    """启动直播音频转写请求"""
    live_url: str
    session_id: Optional[str] = None
    chunk_duration: Optional[float] = 3.0
    profile: Optional[str] = "fast"


class StatusResponse(BaseModel):
    """状态响应"""
    success: bool
    data: Dict[str, Any]


# Endpoints
@router.post("/start", response_model=LiveAudioAgentResult)
async def start_live_audio(req: StartLiveAudioRequest) -> LiveAudioAgentResult:
    """启动直播音频转写

    使用运行时配置中的语音设置，支持前端实时配置

    Args:
        req: 启动请求，包含直播 URL

    Returns:
        LiveAudioAgentResult 包含 session_id 和状态信息
    """
    # Get current voice config from runtime
    voice_config = runtime_config.voice

    # Create agent config
    agent_config = LiveAudioAgentConfig(
        live_url=req.live_url,
        session_id=req.session_id,
        mode="vad",
        model_size="small",
        chunk_duration=req.chunk_duration or 3.0,
        profile=req.profile or "fast",
    )

    # Create and run agent
    agent = LiveAudioAgent(agent_config)
    result = await agent.start()

    return result


@router.post("/stop", response_model=LiveAudioAgentResult)
async def stop_live_audio() -> LiveAudioAgentResult:
    """停止直播音频转写

    Returns:
        LiveAudioAgentResult 包含最终状态
    """
    agent = LiveAudioAgent()
    result = await agent.stop()
    return result


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """获取转写状态

    Returns:
        状态信息字典
    """
    agent = LiveAudioAgent()
    result = await agent.get_status()

    return {
        "success": result.success,
        "data": {
            "is_running": result.is_running,
            "live_id": result.live_id,
            "session_id": result.session_id,
            "live_url": result.live_url,
            "ffmpeg_pid": result.ffmpeg_pid,
            "details": result.details,
        },
        "error": result.error,
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查

    返回 VoiceAgent 和 LiveAudioAgent 健康状态，以及当前配置

    Returns:
        健康状态和配置信息
    """
    from server.agents.voice import VoiceAgent

    # Check voice agent
    voice_agent = VoiceAgent()
    voice_healthy = await voice_agent.health_check()

    # Check live audio agent
    live_agent = LiveAudioAgent()
    live_healthy = await live_agent.health_check()

    # Get current config
    voice_config = runtime_config.voice

    return {
        "success": True,
        "data": {
            "voice_agent": {
                "healthy": voice_healthy,
                "model": voice_config.model,
                "language": voice_config.language,
                "enable_vad": voice_config.enable_vad,
            },
            "live_agent": {
                "healthy": live_healthy,
            },
            "config": {
                "sample_rate": voice_config.sample_rate,
            }
        }
    }


@router.get("/models")
async def get_model_status() -> Dict[str, Any]:
    """获取模型状态

    Returns:
        模型缓存状态
    """
    # Delegate to V1 API for model status
    from server.app.api.live_audio import get_model_status as v1_get_model_status
    return await v1_get_model_status()


@router.post("/preload_models")
async def preload_models() -> Dict[str, Any]:
    """预加载模型

    Returns:
        预加载结果
    """
    # Delegate to V1 API for model preloading
    from server.app.api.live_audio import preload as v1_preload
    # The V1 preload expects a request body
    from server.app.schemas.live_audio import LiveAudioPreloadRequest
    req = LiveAudioPreloadRequest(sizes=["small"])
    return await v1_preload(req)
