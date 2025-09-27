# -*- coding: utf-8 -*-
"""Hotwords management API.

Provide simple GET/POST to fetch and update hotwords mapping used by
post-processing. Data is stored at data/hotwords.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.live_audio_stream_service import get_live_audio_service


router = APIRouter(prefix="/api/nlp", tags=["nlp"])


DATA_PATH = Path("data/hotwords.json").resolve()


class HotwordsBody(BaseModel):
    replace: Dict[str, List[str]] = Field(default_factory=dict)


@router.get("/hotwords")
async def get_hotwords() -> dict:
    if DATA_PATH.exists():
        try:
            data = json.loads(DATA_PATH.read_text(encoding="utf-8")) or {}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        data = {"replace": {}}
    return data


@router.post("/hotwords")
async def set_hotwords(body: HotwordsBody) -> dict:
    # Update file
    try:
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        DATA_PATH.write_text(json.dumps({"replace": body.replace}, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Update in-service replacer
    try:
        svc = get_live_audio_service()
        svc.update_hotwords(body.replace)
    except Exception:
        pass
    return {"success": True}


@router.post("/hotwords/reset")
async def reset_hotwords() -> dict:
    """Restore default hotwords (if default file exists), else empty mapping."""
    default_path = Path("data/hotwords.default.json").resolve()
    try:
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        if default_path.exists():
            DATA_PATH.write_text(default_path.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            DATA_PATH.write_text(json.dumps({"replace": {}}, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        svc = get_live_audio_service()
        svc.update_hotwords({})
    except Exception:
        pass
    return {"success": True}
