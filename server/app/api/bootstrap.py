# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter

from ...utils import bootstrap  # type: ignore

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

