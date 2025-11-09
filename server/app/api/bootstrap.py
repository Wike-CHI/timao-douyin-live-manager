# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter
from server.app.schemas.common import BaseResponse
from server.app.utils.api import success_response

from server.utils import bootstrap  # type: ignore

router = APIRouter(prefix="/api/bootstrap", tags=["bootstrap"])


@router.get("/status")
async def get_bootstrap_status() -> dict:
    """Return current bootstrap status for FFmpeg and models.
    Fields:
    - running: bool
    - ffmpeg: { state: ok|missing|checking|error, path, error }
    - models: { state: ok|missing|checking, model_present, vad_present }
    - suggestions: [str]
    """
    try:
        return bootstrap.get_status()
    except Exception:
        return {"running": False, "ffmpeg": {"state": "unknown"}, "models": {"state": "unknown"}, "suggestions": []}


@router.get("/version", response_model=BaseResponse)
async def get_version():
    """
    获取应用版本信息（用于Electron客户端更新检测）
    
    Returns:
        当前最新版本号、下载地址、更新说明
    """
    return success_response({
        "latest_version": "1.0.0",  # 当前版本
        "download_url": "http://129.211.218.135/updates/",
        "release_notes": "初始版本",
        "is_required": False,  # 是否强制更新
    })

