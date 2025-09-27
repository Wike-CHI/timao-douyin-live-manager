# -*- coding: utf-8 -*-
"""
AI Test API

Quick endpoints to test Qwen3 MAX analysis without running the full record pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/ai", tags=["ai-test"])


class CommentItem(BaseModel):
    user: Optional[str] = None
    content: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    ts: Optional[int] = None


class WindowReq(BaseModel):
    transcript: str = Field(..., description="5分钟口播文本")
    comments: List[CommentItem] = Field(default_factory=list)
    prev_summary: Optional[str] = Field(None, description="上一窗口carry摘要，可为空")


class LiveReq(BaseModel):
    transcript: str
    comments: List[CommentItem] = Field(default_factory=list)


@router.post("/test_window")
def test_window(req: WindowReq) -> Dict[str, Any]:
    try:
        from ...ai.qwen_openai_compatible import analyze_window  # type: ignore
        comments = [
            {
                "user": (c.user or (c.payload or {}).get("user")),
                "content": c.content or (c.payload or {}).get("content"),
                "payload": c.payload or {},
                "ts": c.ts,
            }
            for c in req.comments
        ]
        out = analyze_window(req.transcript, comments, req.prev_summary)
        return {"success": True, "data": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test_live")
def test_live(req: LiveReq) -> Dict[str, Any]:
    try:
        from ...ai.qwen_openai_compatible import analyze_live_session  # type: ignore
        comments = [
            {
                "user": (c.user or (c.payload or {}).get("user")),
                "content": c.content or (c.payload or {}).get("content"),
                "payload": c.payload or {},
                "ts": c.ts,
            }
            for c in req.comments
        ]
        out = analyze_live_session(req.transcript, comments)
        return {"success": True, "data": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

