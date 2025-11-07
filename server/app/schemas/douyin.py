"""Douyin monitoring related schemas."""

from __future__ import annotations

from typing import Dict, Optional, Any

from pydantic import BaseModel


class StartDouyinMonitoringRequest(BaseModel):
    live_id: Optional[str] = None
    live_url: Optional[str] = None
    cookie: Optional[str] = None


class DouyinStatusResponse(BaseModel):
    is_monitoring: bool
    current_room_id: Optional[str]
    current_live_id: Optional[str]
    fetcher_status: Dict[str, Any]

