# -*- coding: utf-8 -*-
"""
Live Audio Transcription API (Douyin)

Start/stop a live stream transcription session from a Douyin live URL (or ID),
and stream results over WebSocket with delta/full messages, plus input level.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from pathlib import Path

from ..services.live_audio_stream_service import get_live_audio_service


router = APIRouter(prefix="/api/live_audio", tags=["live-audio"])


class StartReq(BaseModel):
    live_url: str = Field(..., description="Douyin live URL or ID")
    session_id: Optional[str] = None
    chunk_duration: Optional[float] = Field(None, ge=0.2, le=2.0)
    profile: Optional[str] = Field(None, description="Preset: 'fast' or 'stable' (applied before other params)")
    # Mode and model are fixed (mode='vad', model='small'); inputs are ignored.
    mode: Optional[str] = Field(None, description="Ignored; fixed to 'vad'")
    model: Optional[str] = Field(None, description="Ignored; fixed to 'small'")
    # VAD params (effective when mode == 'vad')
    vad_min_silence_sec: Optional[float] = Field(None, ge=0.2, le=2.5)
    vad_min_speech_sec: Optional[float] = Field(None, ge=0.2, le=2.5)
    vad_hangover_sec: Optional[float] = Field(None, ge=0.1, le=1.5)
    vad_rms: Optional[float] = Field(None, ge=0.001, le=0.2)
    # Assembler params (sentence tuning)
    max_wait: Optional[float] = Field(None, ge=0.5, le=10.0)
    max_chars: Optional[int] = Field(None, ge=16, le=240)
    silence_flush: Optional[int] = Field(None, ge=1, le=8)
    min_sentence_chars: Optional[int] = Field(None, ge=0, le=80)


class BaseResp(BaseModel):
    success: bool = True
    message: str = "ok"
    data: Optional[dict] = None


@router.post("/start")
async def start_live_audio(req: StartReq) -> BaseResp:
    svc = get_live_audio_service()
    try:
        # Apply profile first; subsequent explicit params override the preset
        if req.profile:
            svc.apply_profile(req.profile)
        if req.chunk_duration is not None:
            svc.chunk_seconds = float(req.chunk_duration)
        # Hard-lock mode/model regardless of inputs
        svc.mode = "vad"
        svc.set_model_size("small")
        if req.vad_min_silence_sec is not None:
            svc.vad_min_silence_sec = float(req.vad_min_silence_sec)
        if req.vad_min_speech_sec is not None:
            svc.vad_min_speech_sec = float(req.vad_min_speech_sec)
        if req.vad_hangover_sec is not None:
            svc.vad_hangover_sec = float(req.vad_hangover_sec)
        if req.vad_rms is not None:
            svc.vad_min_rms = float(req.vad_rms)
        # sentence assembler params
        if req.max_wait is not None:
            svc._assembler.max_wait = float(req.max_wait)
        if req.max_chars is not None:
            svc._assembler.max_chars = int(req.max_chars)
        if req.silence_flush is not None:
            svc._assembler.silence_flush = int(req.silence_flush)
        if req.min_sentence_chars is not None:
            svc.min_sentence_chars = int(req.min_sentence_chars)
        st = await svc.start(req.live_url, req.session_id)
        return BaseResp(data={
            "session_id": st.session_id,
            "live_id": st.live_id,
            "live_url": st.live_url,
            "ffmpeg_pid": st.ffmpeg_pid,
            "mode": "vad",
            "model": "small",
            "profile": getattr(svc, "profile", "fast"),
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop")
async def stop_live_audio() -> BaseResp:
    svc = get_live_audio_service()
    st = await svc.stop()
    return BaseResp(data={
        "is_running": st.is_running,
        "session_id": st.session_id,
    })


@router.get("/status")
async def live_audio_status() -> dict:
    svc = get_live_audio_service()
    st = svc.status()
    return {
        "is_running": st.is_running,
        "live_id": st.live_id,
        "live_url": st.live_url,
        "session_id": st.session_id,
        "mode": getattr(svc, "mode", "delta"),
        "profile": getattr(svc, "profile", "fast"),
        "model": svc.get_model_size(),
        "advanced": {
            "music_filter": getattr(svc, "enable_music_filter", False),
            "diarization": getattr(svc, "enable_diarization", False),
            "persist_enabled": getattr(svc, "persist_enabled", False),
            "persist_root": getattr(svc, "persist_root", None),
        },
        "stats": {
            "total_audio_chunks": st.total_audio_chunks,
            "successful_transcriptions": st.successful_transcriptions,
            "failed_transcriptions": st.failed_transcriptions,
            "average_confidence": st.average_confidence,
        },
    }


@router.get("/health")
async def live_audio_health() -> dict:
    """Preflight health check for local ASR assets (Small + VAD) and init status.
    - Validates local model/VAD directories under models/models/iic/
    - Attempts a lazy init; returns current status and suggestions
    """
    svc = get_live_audio_service()
    root = Path(__file__).resolve().parents[3]
    model_dir = root / "models" / "models" / "iic" / "SenseVoiceSmall"
    vad_dir = root / "models" / "models" / "iic" / "speech_fsmn_vad_zh-cn-16k-common-pytorch"
    present = {
        "model_dir": str(model_dir),
        "model_present": model_dir.exists(),
        "vad_dir": str(vad_dir),
        "vad_present": vad_dir.exists(),
    }
    init_ok = False
    init_error = None
    try:
        # Ensure backend initialized (strict: requires VAD)
        await svc._ensure_sv()  # type: ignore[attr-defined]
        init_ok = getattr(svc, "_sv", None) is not None
    except Exception as e:  # pragma: no cover
        init_ok = False
        init_error = str(e)
    suggestions = []
    if not present["model_present"]:
        suggestions.append("Run: python3 tools/download_sensevoice.py")
    if not present["vad_present"]:
        suggestions.append("Run: python3 tools/download_vad_model.py")
    return {
        "success": bool(present["model_present"] and present["vad_present"] and init_ok),
        "assets": present,
        "initialized": init_ok,
        "error": init_error,
        "suggestions": suggestions,
    }


class AdvancedReq(BaseModel):
    # Simplified: only persistence is configurable
    persist_enabled: bool | None = Field(None, description="Persist transcriptions to JSONL")
    persist_root: str | None = Field(None, description="Root directory for persistence (default records/live_logs)")


@router.post("/advanced")
async def update_advanced(req: AdvancedReq) -> BaseResp:
    svc = get_live_audio_service()
    # Only persist toggles
    conf: dict = {}
    try:
        if (req.persist_enabled is not None) or (req.persist_root is not None):
            conf = svc.update_persist(enable=req.persist_enabled, root=req.persist_root)
    except Exception:
        pass
    return BaseResp(data=conf)


class PreloadReq(BaseModel):
    sizes: list[str] = Field(default_factory=lambda: ["small"], description="Model sizes to preload (only 'small' is supported)")


@router.post("/preload_models")
async def preload_models(req: PreloadReq) -> BaseResp:
    svc = get_live_audio_service()
    ok = []
    fail = []
    for sz in req.sizes:
        try:
            if sz not in {"small"}:
                fail.append({"size": sz, "error": "invalid"})
                continue
            await svc.preload_model(sz)
            ok.append(sz)
        except Exception as e:
            fail.append({"size": sz, "error": str(e)})
    return BaseResp(data={"ok": ok, "fail": fail})


@router.get("/models")
async def get_model_status() -> dict:
    svc = get_live_audio_service()
    return {
        "busy": svc.get_preload_busy(),
        "cache": svc.get_model_cache_status(),
        "current_model": svc.get_model_size(),
    }


# WebSocket: stream transcription and level messages
class WSManager:
    def __init__(self) -> None:
        self.clients: List[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.clients.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.clients:
            self.clients.remove(ws)

    async def send_json(self, ws: WebSocket, msg: Dict[str, Any]) -> None:
        try:
            await ws.send_json(msg)
        except Exception:
            self.disconnect(ws)


ws_mgr = WSManager()


@router.websocket("/ws")
async def live_audio_ws(ws: WebSocket):
    svc = get_live_audio_service()
    await ws_mgr.connect(ws)
    cb_name = f"ws_{id(ws)}"

    async def on_tr(msg: Dict[str, Any]) -> None:
        try:
            await ws.send_json(msg)
        except Exception:
            pass

    async def on_level(rms: float, ts: float) -> None:
        try:
            await ws.send_json({"type": "level", "data": {"rms": rms, "timestamp": ts}})
        except Exception:
            pass

    svc.add_transcription_callback(cb_name, on_tr)
    svc.add_level_callback(cb_name, on_level)
    try:
        while True:
            # basic keepalive loop; allow receive pings
            try:
                data = await ws.receive_json()
                if isinstance(data, dict) and data.get("type") == "ping":
                    await ws.send_json({"type": "pong"})
            except Exception:
                await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    finally:
        svc.remove_transcription_callback(cb_name)
        svc.remove_level_callback(cb_name)
        ws_mgr.disconnect(ws)
