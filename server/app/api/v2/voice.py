# -*- coding: utf-8 -*-
"""V2 Voice API - 使用 VoiceAgent

集成 Pydantic AI 架构的语音转写 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.agents.voice import VoiceAgent, VoiceAgentConfig, VoiceAgentResult
from server.app.core.runtime_config import runtime_config

router = APIRouter(prefix="/api/v2/voice", tags=["Voice V2"])


class TranscribeRequest(BaseModel):
    """转写请求"""
    audio_path: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    healthy: bool
    model: str
    language: str


@router.post("/transcribe", response_model=VoiceAgentResult)
async def transcribe(request: TranscribeRequest) -> VoiceAgentResult:
    """语音转写 - 使用当前运行时配置

    从 RuntimeConfig 获取当前语音设置，支持前端实时配置
    """
    # 获取当前配置
    voice_config = runtime_config.voice

    # 创建 Agent 配置
    agent_config = VoiceAgentConfig(
        model=voice_config.model,
        language=voice_config.language,
        enable_vad=voice_config.enable_vad,
        sample_rate=voice_config.sample_rate,
    )

    # 创建 Agent 并执行转写
    agent = VoiceAgent(agent_config)
    result = await agent.transcribe(request.audio_path)

    return result


@router.get("/health", response_model=HealthResponse)
async def health():
    """健康检查

    返回 VoiceAgent 健康状态和当前配置
    """
    agent = VoiceAgent()
    healthy = await agent.health_check()

    return HealthResponse(
        healthy=healthy,
        model=runtime_config.voice.model,
        language=runtime_config.voice.language,
    )


@router.post("/transcribe_stream")
async def transcribe_stream():
    """流式转写 (TODO)

    未来支持实时流式转写
    """
    raise HTTPException(
        status_code=501,
        detail="Streaming transcription not yet implemented"
    )
