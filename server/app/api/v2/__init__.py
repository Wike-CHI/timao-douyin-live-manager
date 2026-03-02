# -*- coding: utf-8 -*-
"""V2 API 模块 - Pydantic AI 架构"""

from .settings import router as settings_router
from .voice import router as voice_router

__all__ = ["settings_router", "voice_router"]
