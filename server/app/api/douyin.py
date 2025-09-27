# -*- coding: utf-8 -*-
"""
抖音直播监控 API 接口
封装对 DouyinLiveService 的启动/停止/状态查询
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# 服务导入
from ..services.douyin_service import get_douyin_service

router = APIRouter(prefix="/api/douyin", tags=["douyin"])


class StartMonitoringRequest(BaseModel):
    live_id: Optional[str] = None
    live_url: Optional[str] = None
    # 可选 cookie 字符串（建议为浏览器导出的 Cookie 字符串）
    cookie: Optional[str] = None


def _parse_live_id(live_url_or_id: Optional[str]) -> Optional[str]:
    if not live_url_or_id:
        return None
    s = live_url_or_id.strip()
    import re
    m = re.search(r"live\.douyin\.com/([A-Za-z0-9_\-]+)", s)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_\-]+", s):
        return s
    return None


class BaseResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class StatusResponse(BaseModel):
    is_monitoring: bool
    current_room_id: Optional[str]
    current_live_id: Optional[str]
    fetcher_status: Dict[str, Any]


@router.post("/start", response_model=BaseResponse)
async def start_monitoring(request: StartMonitoringRequest):
    """
    启动抖音直播监控
    """
    try:
        service = get_douyin_service()
        # 支持 live_url 解析 live_id
        live_id = _parse_live_id(request.live_id) or _parse_live_id(request.live_url)
        if not live_id:
            raise HTTPException(status_code=400, detail="live_id 或 live_url 无效")
        # 传递可选 cookie 到服务层
        result = await service.start_monitoring(live_id, cookie=request.cookie)
        if result.get("success"):
            return BaseResponse(success=True, message="监控已启动", data=result)
        return BaseResponse(success=False, message=result.get("error", "监控启动失败"), data=result)
    except Exception as e:
        logging.exception("启动监控失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop", response_model=BaseResponse)
async def stop_monitoring():
    """
    停止抖音直播监控
    """
    try:
        service = get_douyin_service()
        result = await service.stop_monitoring()
        if result.get("success"):
            return BaseResponse(success=True, message="监控已停止", data=result)
        return BaseResponse(success=False, message=result.get("error", "监控停止失败"), data=result)
    except Exception as e:
        logging.exception("停止监控失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """
    获取抖音直播监控状态
    """
    try:
        service = get_douyin_service()
        status = service.get_status()
        return StatusResponse(
            is_monitoring=status.get("is_monitoring", False),
            current_room_id=status.get("current_room_id"),
            current_live_id=status.get("current_live_id"),
            fetcher_status=status.get("fetcher_status", {}),
        )
    except Exception as e:
        logging.exception("获取监控状态失败")
        raise HTTPException(status_code=500, detail=str(e))
