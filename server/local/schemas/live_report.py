"""Live report related schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StartLiveReportRequest(BaseModel):
    live_url: str = Field(..., description="Douyin live URL")
    segment_minutes: int = Field(30, ge=5, le=120, description="Segment length in minutes")

