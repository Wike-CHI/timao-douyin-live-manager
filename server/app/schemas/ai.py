"""AI related request schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StartAILiveAnalysisRequest(BaseModel):
    window_sec: int = Field(60, ge=30, le=600)
    session_id: Optional[str] = Field(None, description="Unified session identifier")


class GenerateLiveAnswersRequest(BaseModel):
    questions: List[str] = Field(..., min_items=1)
    transcript: Optional[str] = None
    style_profile: Optional[Dict[str, Any]] = None
    vibe: Optional[Dict[str, Any]] = None


class GenerateOneScriptRequest(BaseModel):
    script_type: str = Field("interaction", description="welcome/product/interaction/closing/...")
    include_context: bool = True
    context: Optional[Dict[str, Any]] = None


class SubmitScriptFeedbackRequest(BaseModel):
    script_id: str
    script_text: str
    score: int = Field(..., ge=1, le=5)
    tags: List[str] = Field(default_factory=list)
    anchor_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

