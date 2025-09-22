# -*- coding: utf-8 -*-
"""Web 端抖音弹幕测试接口."""

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..services.douyin_web_relay import get_douyin_web_relay

router = APIRouter(prefix="/api/douyin/web", tags=["douyin-web"])


class StartRequest(BaseModel):
    live_id: str


@router.post("/start")
async def start_relay(payload: StartRequest):
    relay = get_douyin_web_relay()
    result = await relay.start(payload.live_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "无法启动"))
    return result


@router.post("/stop")
async def stop_relay():
    relay = get_douyin_web_relay()
    result = await relay.stop()
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "停止失败"))
    return result


@router.get("/status")
async def relay_status():
    relay = get_douyin_web_relay()
    status = relay.get_status()
    return {
        "is_running": status.is_running,
        "live_id": status.live_id,
        "room_id": status.room_id,
        "last_error": status.last_error,
    }


@router.get("/stream")
async def stream_events() -> StreamingResponse:
    relay = get_douyin_web_relay()
    queue = await relay.register_client()

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await relay.unregister_client(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
