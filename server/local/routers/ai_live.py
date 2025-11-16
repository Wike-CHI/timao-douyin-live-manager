# -*- coding: utf-8 -*-
"""AI Live Analyzer API (REST + SSE)."""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from ..services.ai_live_analyzer import get_ai_live_analyzer
from ..schemas import (
    StartAILiveAnalysisRequest,
    GenerateLiveAnswersRequest,
)
from ..schemas.common import BaseResponse
from ..utils.api import success_response, handle_service_error

# TODO: 本地服务暂不需要认证，后续可添加
# from .auth import get_current_user
# router = APIRouter(prefix="/api/ai/live", tags=["ai-live"], dependencies=[Depends(get_current_user)])
router = APIRouter(prefix="/api/ai/live", tags=["ai-live"])


@router.post("/start", response_model=BaseResponse[Dict[str, Any]])
async def start_ai(req: StartAILiveAnalysisRequest):
    svc = get_ai_live_analyzer()
    res = await svc.start(req.window_sec, session_id=req.session_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message", "failed"))
    return success_response(res)


@router.post("/stop", response_model=BaseResponse[Dict[str, Any]])
async def stop_ai():
    svc = get_ai_live_analyzer()
    result = await svc.stop()
    return success_response(result)


@router.get("/status", response_model=BaseResponse[Dict[str, Any]])
async def ai_status():
    svc = get_ai_live_analyzer()
    return success_response(svc.status())


@router.get("/context", response_model=BaseResponse[Dict[str, Any]])
async def ai_context():
    """Expose the latest learned style_profile and vibe for consumers.

    This allows other modules (or frontend) to mimic the host's language style
    when generating scripts outside the main analyzer loop.
    """
    svc = get_ai_live_analyzer()
    st = svc.status()
    return success_response({
        "style_profile": st.get("style_profile") or {},
        "vibe": st.get("vibe") or {},
        "updated_from": "ai_live_analyzer:last_result",
    })


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


@router.post("/answers", response_model=BaseResponse[Dict[str, Any]])
async def generate_live_answers(req: GenerateLiveAnswersRequest):
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
    return success_response(result)
