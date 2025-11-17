# -*- coding: utf-8 -*-
"""
本地重度路由模块
包含: 直播转写、AI 处理、实时弹幕等重度服务
"""

from .live_audio import router as live_audio_router
from .ai_live import router as ai_live_router
from .live_session import router as live_session_router
from .ai_gateway import router as ai_gateway_router
from .douyin_web import router as douyin_web_router
from .bootstrap import router as bootstrap_router
from .live_report import router as live_report_router

__all__ = [
    "live_audio_router",
    "ai_live_router", 
    "live_session_router",
    "ai_gateway_router",
    "douyin_web_router",
    "bootstrap_router",
    "live_report_router"
]
