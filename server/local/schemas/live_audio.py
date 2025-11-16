"""Live audio transcription schemas."""

from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, Field


class StartLiveAudioRequest(BaseModel):
    live_url: str = Field(..., description="Douyin live URL or ID")
    session_id: Optional[str] = None
    chunk_duration: Optional[float] = Field(None, ge=0.2, le=2.0)
    profile: Optional[str] = Field(None, description="Preset profile: fast/stable")
    vad_min_silence_sec: Optional[float] = Field(None, ge=0.2, le=2.5)
    vad_min_speech_sec: Optional[float] = Field(None, ge=0.2, le=2.5)
    vad_hangover_sec: Optional[float] = Field(None, ge=0.1, le=1.5)
    vad_rms: Optional[float] = Field(None, ge=0.001, le=0.2)
    vad_force_flush_sec: Optional[float] = Field(None, ge=2.0, le=12.0)
    vad_force_flush_overlap_sec: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_wait: Optional[float] = Field(None, ge=0.5, le=10.0)
    max_chars: Optional[int] = Field(None, ge=16, le=240)
    silence_flush: Optional[int] = Field(None, ge=1, le=8)
    min_sentence_chars: Optional[int] = Field(None, ge=0, le=80)


class LiveAudioAdvancedRequest(BaseModel):
    persist_enabled: Optional[bool] = Field(None, description="Persist transcriptions to disk")
    persist_root: Optional[str] = Field(None, description="Root directory for persistence")
    agc: Optional[bool] = Field(None, description="Automatic gain control")
    diarization: Optional[bool] = Field(None, description="Speaker diarisation toggle")
    max_speakers: Optional[int] = Field(None, ge=1, le=4)


class LiveAudioPreloadRequest(BaseModel):
    sizes: List[str] = Field(default_factory=lambda: ["small"], description="Model sizes to preload")

