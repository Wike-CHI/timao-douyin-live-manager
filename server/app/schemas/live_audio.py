# -*- coding: utf-8 -*-
"""
音频转写相关数据模型
"""

from typing import Optional
from pydantic import BaseModel, Field
from ..schemas.common import BaseResponse


class StartLiveAudioRequest(BaseModel):
    """启动音频转写请求"""
    live_url: str = Field(..., description="Douyin live URL or ID")
    session_id: Optional[str] = Field(None, description="会话ID（可选）")
    chunk_duration: Optional[float] = Field(None, ge=0.2, le=2.0, description="音频块时长")
    profile: Optional[str] = Field(None, description="预设配置: 'fast' or 'stable'")
    # Mode and model are fixed (mode='vad', model='small'); inputs are ignored.
    mode: Optional[str] = Field(None, description="Ignored; fixed to 'vad'")
    model: Optional[str] = Field(None, description="Ignored; fixed to 'small'")
    # VAD params (effective when mode == 'vad')
    vad_min_silence_sec: Optional[float] = Field(None, ge=0.2, le=2.5)
    vad_min_speech_sec: Optional[float] = Field(None, ge=0.2, le=2.5)
    vad_hangover_sec: Optional[float] = Field(None, ge=0.1, le=1.5)
    vad_rms: Optional[float] = Field(None, ge=0.001, le=0.2)
    vad_force_flush_sec: Optional[float] = Field(
        None,
        ge=2.0,
        le=12.0,
        description="Force emit a partial transcription if continuous speech exceeds this duration",
    )
    vad_force_flush_overlap_sec: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Seconds of audio to retain as overlap when force-flushing long speech",
    )
    # Assembler params (sentence tuning)
    max_wait: Optional[float] = Field(None, ge=0.5, le=10.0)
    max_chars: Optional[int] = Field(None, ge=16, le=240)
    silence_flush: Optional[int] = Field(None, ge=1, le=8)
    min_sentence_chars: Optional[int] = Field(None, ge=0, le=80)


class UpdateAdvancedSettingsRequest(BaseModel):
    """更新高级设置请求"""
    persist_enabled: Optional[bool] = Field(None, description="Persist transcriptions to JSONL")
    persist_root: Optional[str] = Field(None, description="Root directory for persistence")
    agc: Optional[bool] = Field(None, description="Enable automatic gain control (AGC)")
    diarization: Optional[bool] = Field(None, description="Enable speaker diarization")
    max_speakers: Optional[int] = Field(
        None,
        ge=1,
        le=4,
        description="Maximum number of speakers to differentiate (1-4)",
    )


class PreloadModelsRequest(BaseModel):
    """预加载模型请求"""
    sizes: list[str] = Field(
        default_factory=lambda: ["small"],
        description="Model sizes to preload (only 'small' is supported)"
    )


class StartLiveAudioResponse(BaseResponse[dict]):
    """启动音频转写响应"""
    pass


class StopLiveAudioResponse(BaseResponse[dict]):
    """停止音频转写响应"""
    pass

