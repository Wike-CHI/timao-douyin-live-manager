# -*- coding: utf-8 -*-
"""
直播报告相关数据模型
"""

from typing import Optional, Union, List, Dict, Any
from pydantic import BaseModel, Field
from ..schemas.common import BaseResponse


class StartLiveReportRequest(BaseModel):
    """启动直播录制请求"""
    live_url: str = Field(..., description="Douyin live URL, e.g., https://live.douyin.com/xxxx")
    segment_minutes: int = Field(30, ge=5, le=120, description="Segment length in minutes (default 30)")


class StartLiveReportResponse(BaseResponse[dict]):
    """启动直播录制响应"""
    pass


class StopLiveReportResponse(BaseResponse[dict]):
    """停止直播录制响应"""
    pass


class GenerateLiveReportResponse(BaseResponse[Dict[str, Any]]):
    """生成直播报告响应"""
    pass

