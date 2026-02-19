# -*- coding: utf-8 -*-
"""
FastAPI依赖项模块
简化版 - 无用户认证
"""

from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# 默认用户ID（用于本地应用）
DEFAULT_USER_ID = "local_user"

def get_db() -> Session:
    """获取数据库会话"""
    from server.app.database import db_manager
    if not db_manager:
        raise RuntimeError("Database not initialized")

    session = db_manager.get_session_sync()
    try:
        yield session
    finally:
        session.close()

async def get_request_info(request: Request) -> dict:
    """获取请求信息（用于日志）"""
    return {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", ""),
        "method": request.method,
        "url": str(request.url),
    }

def get_default_user_id() -> str:
    """获取默认用户ID"""
    return DEFAULT_USER_ID
