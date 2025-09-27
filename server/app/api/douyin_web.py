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
    live_id: str | None = None
    live_url: str | None = None


class PersistReq(BaseModel):
    persist_enabled: bool | None = None
    persist_root: str | None = None


def _parse_live_id(live_url_or_id: str | None) -> str | None:
    if not live_url_or_id:
        return None
    s = live_url_or_id.strip()
    # Allow passing a full URL like https://live.douyin.com/40452701152?... → extract number/id
    import re
    m = re.search(r"live\.douyin\.com/([A-Za-z0-9_\-]+)", s)
    if m:
        return m.group(1)
    # Already an ID
    if re.fullmatch(r"[A-Za-z0-9_\-]+", s):
        return s
    return None


@router.post("/start")
async def start_relay(payload: StartRequest):
    relay = get_douyin_web_relay()
    # Accept either live_id or live_url; parse if needed
    live_id = _parse_live_id(payload.live_id) or _parse_live_id(payload.live_url)
    if not live_id:
        raise HTTPException(status_code=400, detail="live_id 或 live_url 无效")
    result = await relay.start(live_id)
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
    out = {
        "is_running": status.is_running,
        "live_id": status.live_id,
        "room_id": status.room_id,
        "last_error": status.last_error,
    }
    try:
        out.update(relay.get_persist())
    except Exception:
        pass
    return out


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


@router.post("/persist")
async def update_persist(req: PersistReq):
    relay = get_douyin_web_relay()
    out = relay.update_persist(enable=req.persist_enabled, root=req.persist_root)
    return out
