# -*- coding: utf-8 -*-
"""联合测试（语音+弹幕）API."""

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..services.live_test_hub import get_live_test_hub

router = APIRouter(prefix="/api/live-test", tags=["live-test"])


class StartRequest(BaseModel):
    live_id: str


@router.post("/start")
async def start_live_test(payload: StartRequest):
    hub = get_live_test_hub()
    result = await hub.start(payload.live_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "无法启动"))
    return result


@router.post("/stop")
async def stop_live_test():
    hub = get_live_test_hub()
    result = await hub.stop()
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "停止失败"))
    return result


@router.get("/status")
async def live_test_status():
    hub = get_live_test_hub()
    status = hub.get_status()
    return {
        "is_running": status.is_running,
        "live_id": status.live_id,
        "ast_running": status.ast_running,
        "douyin_running": status.douyin_running,
        "last_error": status.last_error,
    }


@router.get("/stream")
async def live_test_stream() -> StreamingResponse:
    hub = get_live_test_hub()
    queue = await hub.register_client()

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await hub.unregister_client(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
