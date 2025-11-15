# -*- coding: utf-8 -*-
"""
Live Audio Transcription API (Douyin)

Start/stop a live stream transcription session from a Douyin live URL (or ID),
and stream results over WebSocket with delta/full messages, plus input level.
"""

from __future__ import annotations

from ast import List
import asyncio
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pathlib import Path

from ..services.live_audio_stream_service import get_live_audio_service
from server.utils.service_logger import log_service_start, log_service_stop, log_service_error
from server.app.schemas import (
    StartLiveAudioRequest,
    LiveAudioAdvancedRequest,
    LiveAudioPreloadRequest,
)
from server.app.schemas.common import BaseResponse
from server.app.utils.api import success_response, handle_service_error


router = APIRouter(prefix="/api/live_audio", tags=["live-audio"])


@router.post("/start", response_model=BaseResponse[Dict[str, Any]])
async def start_live_audio(req: StartLiveAudioRequest):
    svc = get_live_audio_service()
    try:
        log_service_start("实时音频转写服务", live_url=req.live_url, session_id=req.session_id)
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
        if req.vad_force_flush_sec is not None:
            svc.vad_force_flush_sec = float(req.vad_force_flush_sec)
        if req.vad_force_flush_overlap_sec is not None:
            svc.vad_force_flush_overlap_sec = float(req.vad_force_flush_overlap_sec)
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
        log_service_start("实时音频转写服务", live_id=st.live_id, session_id=st.session_id, ffmpeg_pid=st.ffmpeg_pid)
        return success_response({
            "session_id": st.session_id,
            "live_id": st.live_id,
            "live_url": st.live_url,
            "ffmpeg_pid": st.ffmpeg_pid,
            "mode": "vad",
            "model": "small",
            "profile": getattr(svc, "profile", "fast"),
        })
    except Exception as exc:  # pragma: no cover - mapped via helper
        log_service_error("实时音频转写服务", str(exc), live_url=req.live_url, session_id=req.session_id)
        import logging
        logging.getLogger(__name__).error("Live audio start failed", exc_info=True)
        handle_service_error(
            exc,
            {
                "already running": (409, "实时音频转写服务已在运行中"),
                "invalid": (400, "无效的直播地址或ID"),
                "未开播": (400, "直播间未开播"),
                "not live": (400, "直播间未开播"),
                "sensevoice": (500, "语音识别服务初始化失败"),
                "initialize failed": (500, "语音识别服务初始化失败"),
                "ffmpeg": (500, "音频流处理失败"),
            },
            default_message="启动实时音频转写服务失败",
        )


@router.post("/stop", response_model=BaseResponse[Dict[str, Any]])
async def stop_live_audio():
    svc = get_live_audio_service()
    st = await svc.stop()
    log_service_stop("实时音频转写服务", session_id=st.session_id, live_id=st.live_id)
    return success_response({
        "is_running": st.is_running,
        "session_id": st.session_id,
    })


@router.get("/stream-url/{live_url_or_id}", response_model=BaseResponse[Dict[str, Any]])
async def get_stream_url(live_url_or_id: str):
    """
    获取直播流地址（供客户端本地录制）
    
    Args:
        live_url_or_id: 抖音直播URL或房间ID
    
    Returns:
        直播流地址、主播信息等
    """
    try:
        # StreamCap platform handler (resolve real stream URL from live URL)
        from server.modules.streamcap.platforms import get_platform_handler  # type: ignore
        
        def _parse_live_id(url_or_id: str) -> str | None:
            """Parse Douyin live ID from URL or ID string"""
            if not url_or_id:
                return None
            url_or_id = url_or_id.strip()
            # Already an ID
            if url_or_id.isdigit():
                return url_or_id
            # Extract from URL
            import re
            match = re.search(r'live\.douyin\.com[/\\]+(\d+)', url_or_id)
            if match:
                return match.group(1)
            return None
        
        live_id = _parse_live_id(live_url_or_id)
        if not live_id:
            raise HTTPException(status_code=400, detail="无效的直播地址或ID")
        
        # Resolve stream using StreamCap handler
        handler = get_platform_handler(live_url=f"https://live.douyin.com/{live_id}")
        if handler is None:
            raise HTTPException(status_code=400, detail="不支持的直播平台")
        
        info = await handler.get_stream_info(f"https://live.douyin.com/{live_id}")
        
        # StreamCap returns a StreamData object (attrs) but defensive fallback supports dict
        if isinstance(info, dict):
            is_live = info.get("is_live")
            record_url = info.get("record_url") or info.get("flv_url") or info.get("m3u8_url")
            anchor_name = info.get("anchor_name")
            room_title = info.get("room_title")
        else:
            is_live = getattr(info, "is_live", None)
            record_url = (
                getattr(info, "record_url", None)
                or getattr(info, "flv_url", None)
                or getattr(info, "m3u8_url", None)
            )
            anchor_name = getattr(info, "anchor_name", None)
            room_title = getattr(info, "room_title", None)
        
        if is_live is False:
            raise HTTPException(
                status_code=400,
                detail=f"直播间未开播（{anchor_name or live_id}）"
            )
        
        if not record_url:
            raise HTTPException(status_code=500, detail="无法解析直播流地址")
        
        return success_response({
            "live_id": live_id,
            "stream_url": record_url,
            "anchor_name": anchor_name,
            "room_title": room_title,
            "is_live": is_live,
            "live_url": f"https://live.douyin.com/{live_id}",
        })
    
    except HTTPException:
        raise
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("Get stream URL failed", exc_info=True)
        handle_service_error(
            exc,
            {
                "unsupported": (400, "不支持的直播平台"),
                "invalid": (400, "无效的直播地址"),
                "未开播": (400, "直播间未开播"),
            },
            default_message="获取直播流地址失败",
        )


@router.get("/status", response_model=BaseResponse[Dict[str, Any]])
async def live_audio_status():
    svc = get_live_audio_service()
    st = svc.status()
    # 🆕 获取健康状态和验证信息
    health = svc.get_health_status()
    return success_response({
        "is_running": st.is_running,
        "live_id": st.live_id,
        "health": health,  # 🆕 添加健康状态
        "live_url": st.live_url,
        "session_id": st.session_id,
        "mode": getattr(svc, "mode", "delta"),
        "profile": getattr(svc, "profile", "fast"),
        "model": svc.get_model_size(),
        "advanced": {
            "agc_enabled": getattr(svc, "agc_enabled", False),
            "agc_gain": round(getattr(svc, "_agc_gain", 1.0), 3),
            "diarizer_active": getattr(svc, "_diarizer", None) is not None,
            "max_speakers": getattr(getattr(svc, "_diarizer", None), "max_speakers", 0) if getattr(svc, "_diarizer", None) is not None else 0,
            "last_speaker": getattr(svc, "_last_speaker_label", None),
            "music_filter": getattr(svc, "music_detection_enabled", False),
            "music_detection_enabled": getattr(svc, "music_detection_enabled", False),
            "music_guard_active": st.music_guard_active,
            "music_guard_score": st.music_guard_score,
            "music_last_title": st.music_last_title,
            "music_last_score": st.music_last_score,
            "music_last_detected_at": st.music_last_detected_at,
            "music_match_hold_until": getattr(svc, "_acr_active_until", 0.0) if getattr(svc, "_acr_enabled", False) else 0.0,
            "persist_enabled": getattr(svc, "persist_enabled", False),
            "persist_root": getattr(svc, "persist_root", None),
        },
        "stats": {
            "total_audio_chunks": st.total_audio_chunks,
            "successful_transcriptions": st.successful_transcriptions,
            "failed_transcriptions": st.failed_transcriptions,
            "average_confidence": st.average_confidence,
        },
    })


@router.get("/health", response_model=BaseResponse[Dict[str, Any]])
async def live_audio_health():
    """Preflight health check for local ASR assets (Small + VAD) and init status.
    - Validates local model/VAD directories under models/models/iic/
    - Attempts a lazy init; returns current status and suggestions
    """
    svc = get_live_audio_service()
    # 🔧 修复：使用正确的缓存路径
    root = Path(__file__).resolve().parents[3]
    model_dir = root / "server" / "modules" / "models" / ".cache" / "models" / "iic" / "SenseVoiceSmall"
    vad_dir = root / "server" / "modules" / "models" / ".cache" / "models" / "iic" / "speech_fsmn_vad_zh-cn-16k-common-pytorch"
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
        suggestions.append("Run: python3 server/server/tools/download_sensevoice.py")
    if not present["vad_present"]:
        suggestions.append("Run: python3 tools/download_vad_model.py")
    return success_response({
        "assets": present,
        "initialized": init_ok,
        "error": init_error,
        "suggestions": suggestions,
        "ready": bool(present["model_present"] and present["vad_present"] and init_ok),
    })


@router.post("/advanced", response_model=BaseResponse[Dict[str, Any]])
async def update_advanced(req: LiveAudioAdvancedRequest):
    svc = get_live_audio_service()
    # Only persist toggles
    conf: dict = {}
    try:
        if (req.persist_enabled is not None) or (req.persist_root is not None):
            conf = svc.update_persist(enable=req.persist_enabled, root=req.persist_root)
        if (req.agc is not None) or (req.diarization is not None) or (req.max_speakers is not None):
            adv = svc.update_advanced(
                agc=req.agc,
                diarization=req.diarization,
                max_speakers=req.max_speakers,
            )
            if adv:
                conf = {**conf, **adv}
    except Exception as exc:
        handle_service_error(exc, {}, default_message="更新高级设置失败")
    return success_response(conf or {"message": "updated"})


@router.post("/preload_models", response_model=BaseResponse[Dict[str, Any]])
async def preload_models(req: LiveAudioPreloadRequest):
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
    return success_response({"ok": ok, "fail": fail})


@router.get("/models", response_model=BaseResponse[Dict[str, Any]])
async def get_model_status():
    svc = get_live_audio_service()
    return success_response({
        "busy": svc.get_preload_busy(),
        "cache": svc.get_model_cache_status(),
        "current_model": svc.get_model_size(),
    })


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
