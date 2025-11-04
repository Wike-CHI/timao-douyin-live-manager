# -*- coding: utf-8 -*-
"""
统一直播会话管理 API
支持会话创建、恢复、暂停、停止等操作
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.live_session_manager import get_session_manager
from server.utils.service_logger import log_service_start, log_service_error

router = APIRouter(prefix="/api/live_session", tags=["live-session"])
logger = logging.getLogger(__name__)


class SessionStatusResponse(BaseModel):
    """会话状态响应"""
    success: bool = True
    message: str = "ok"
    data: Optional[dict] = None


@router.get("/status")
async def get_session_status() -> SessionStatusResponse:
    """获取当前会话状态"""
    try:
        session_mgr = get_session_manager()
        session = await session_mgr.get_current_session()
        
        if not session:
            return SessionStatusResponse(
                success=True,
                message="没有活跃会话",
                data={"session": None}
            )
        
        return SessionStatusResponse(
            success=True,
            message="ok",
            data={
                "session": {
                    "session_id": session.session_id,
                    "live_url": session.live_url,
                    "live_id": session.live_id,
                    "room_id": session.room_id,
                    "anchor_name": session.anchor_name,
                    "platform_key": session.platform_key,
                    "session_date": session.session_date,
                    "started_at": session.started_at,
                    "last_updated_at": session.last_updated_at,
                    "status": session.status,
                    "recording_active": session.recording_active,
                    "audio_transcription_active": session.audio_transcription_active,
                    "ai_analysis_active": session.ai_analysis_active,
                    "douyin_relay_active": session.douyin_relay_active,
                    "last_error": session.last_error,
                }
            }
        )
    except Exception as e:
        log_service_error("统一会话管理", str(e))
        logger.error(f"获取会话状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取会话状态失败: {str(e)}")


@router.post("/resume")
async def resume_session() -> SessionStatusResponse:
    """恢复之前的会话（如果有效）"""
    try:
        session_mgr = get_session_manager()
        session = await session_mgr.resume_session()
        
        if not session:
            return SessionStatusResponse(
                success=False,
                message="没有可恢复的会话",
                data={"session": None}
            )
        
        log_service_start("统一会话管理", session_id=session.session_id, action="恢复会话")
        
        return SessionStatusResponse(
            success=True,
            message=f"会话已恢复: {session.session_id}",
            data={
                "session": {
                    "session_id": session.session_id,
                    "live_url": session.live_url,
                    "live_id": session.live_id,
                    "room_id": session.room_id,
                    "status": session.status,
                }
            }
        )
    except Exception as e:
        log_service_error("统一会话管理", str(e))
        logger.error(f"恢复会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"恢复会话失败: {str(e)}")


@router.post("/pause")
async def pause_session() -> SessionStatusResponse:
    """暂停当前会话"""
    try:
        session_mgr = get_session_manager()
        session = await session_mgr.pause_session()
        
        if not session:
            return SessionStatusResponse(
                success=False,
                message="没有活跃会话可暂停",
                data={"session": None}
            )
        
        return SessionStatusResponse(
            success=True,
            message=f"会话已暂停: {session.session_id}",
            data={
                "session": {
                    "session_id": session.session_id,
                    "status": session.status,
                }
            }
        )
    except Exception as e:
        log_service_error("统一会话管理", str(e))
        logger.error(f"暂停会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"暂停会话失败: {str(e)}")


@router.post("/resume_paused")
async def resume_paused_session() -> SessionStatusResponse:
    """恢复暂停的会话"""
    try:
        session_mgr = get_session_manager()
        session = await session_mgr.resume_paused_session()
        
        if not session:
            return SessionStatusResponse(
                success=False,
                message="没有可恢复的暂停会话",
                data={"session": None}
            )
        
        return SessionStatusResponse(
            success=True,
            message=f"会话已恢复: {session.session_id}",
            data={
                "session": {
                    "session_id": session.session_id,
                    "status": session.status,
                }
            }
        )
    except Exception as e:
        log_service_error("统一会话管理", str(e))
        logger.error(f"恢复暂停会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"恢复暂停会话失败: {str(e)}")

