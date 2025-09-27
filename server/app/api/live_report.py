# -*- coding: utf-8 -*-
"""
Live Report API
Start/stop a live recording session (Douyin), and after finishing, run
SenseVoice transcription per 30-min segment and compose a recap report.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.live_report_service import get_live_report_service


router = APIRouter(prefix="/api/report/live", tags=["live-report"])


class StartReq(BaseModel):
    live_url: str = Field(..., description="Douyin live URL, e.g., https://live.douyin.com/xxxx")
    segment_minutes: int = Field(30, ge=5, le=120, description="Segment length in minutes (default 30)")


class BaseResp(BaseModel):
    success: bool = True
    message: str = "ok"
    data: Optional[dict] = None


@router.post("/start")
async def start_live_report(req: StartReq) -> BaseResp:
    try:
        svc = get_live_report_service()
        status = await svc.start(req.live_url, req.segment_minutes)
        return BaseResp(data={
            "session_id": status.session_id,
            "recording_pid": status.recording_pid,
            "recording_dir": status.recording_dir,
            "segment_seconds": status.segment_seconds,
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop")
async def stop_live_report() -> BaseResp:
    try:
        svc = get_live_report_service()
        status = await svc.stop()
        return BaseResp(data={
            "session_id": status.session_id,
            "stopped_at": status.stopped_at,
            "segments": status.segments,
            "comments_count": status.comments_count,
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def live_report_status() -> dict:
    svc = get_live_report_service()
    s = svc.status()
    return {"active": s is not None, "status": s.__dict__ if s else None}


@router.post("/generate")
async def generate_live_report() -> BaseResp:
    try:
        svc = get_live_report_service()
        artifacts = await svc.generate_report()
        return BaseResp(data=artifacts)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

