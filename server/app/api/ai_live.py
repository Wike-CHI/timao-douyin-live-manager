# -*- coding: utf-8 -*-
"""AI Live Analyzer API (REST + SSE)."""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..services.ai_live_analyzer import get_ai_live_analyzer


router = APIRouter(prefix="/api/ai/live", tags=["ai-live"])


class StartReq(BaseModel):
    window_sec: int = Field(60, ge=30, le=600)


class AnswerRequest(BaseModel):
    questions: List[str] = Field(..., min_items=1, description="待回答的弹幕问题列表")
    transcript: Optional[str] = Field(None, description="可选的口播上下文（多句换行）")
    style_profile: Optional[Dict[str, Any]] = Field(None, description="可选的主播画像覆盖")
    vibe: Optional[Dict[str, Any]] = Field(None, description="可选的氛围上下文")


@router.post("/start")
async def start_ai(req: StartReq):
    svc = get_ai_live_analyzer()
    res = await svc.start(req.window_sec)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message", "failed"))
    return res


@router.post("/stop")
async def stop_ai():
    svc = get_ai_live_analyzer()
    return await svc.stop()


@router.get("/status")
async def ai_status():
    svc = get_ai_live_analyzer()
    return svc.status()


@router.get("/context")
async def ai_context():
    """Expose the latest learned style_profile and vibe for consumers.

    This allows other modules (or frontend) to mimic the host's language style
    when generating scripts outside the main analyzer loop.
    """
    svc = get_ai_live_analyzer()
    st = svc.status()
    return {
        "style_profile": st.get("style_profile") or {},
        "vibe": st.get("vibe") or {},
        "updated_from": "ai_live_analyzer:last_result",
    }


@router.get("/stream")
async def ai_stream() -> StreamingResponse:
    svc = get_ai_live_analyzer()
    q = await svc.register_client()

    async def gen() -> AsyncGenerator[str, None]:
        try:
            while True:
                ev = await q.get()
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await svc.unregister_client(q)

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/answers")
async def generate_live_answers(req: AnswerRequest):
    svc = get_ai_live_analyzer()
    try:
        result = svc.generate_answer_scripts(
            questions=req.questions,
            transcript=req.transcript,
            style_profile=req.style_profile,
            vibe=req.vibe,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"success": True, "data": result}
