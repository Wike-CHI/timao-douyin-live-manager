# -*- coding: utf-8 -*-
"""
云端轻量路由模块
包含: 认证、用户资料、订阅/支付
"""

from .auth import router as auth_router
from .profile import router as profile_router
from .subscription import router as subscription_router

__all__ = ["auth_router", "profile_router", "subscription_router"]
