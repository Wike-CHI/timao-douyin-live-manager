# -*- coding: utf-8 -*-
"""
抖音相关数据模型
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from ..schemas.common import BaseResponse


class StartDouyinMonitoringRequest(BaseModel):
    """启动抖音监控请求"""
    live_id: Optional[str] = Field(None, description="直播间ID")
    live_url: Optional[str] = Field(None, description="直播间URL")
    cookie: Optional[str] = Field(None, description="可选 cookie 字符串")


class StartDouyinMonitoringResponse(BaseResponse[Dict[str, Any]]):
    """启动抖音监控响应"""
    pass


class StopDouyinMonitoringResponse(BaseResponse[Dict[str, Any]]):
    """停止抖音监控响应"""
    pass


class DouyinStatusResponse(BaseModel):
    """抖音监控状态响应"""
    is_monitoring: bool
    current_room_id: Optional[str]
    current_live_id: Optional[str]
    fetcher_status: Dict[str, Any]

