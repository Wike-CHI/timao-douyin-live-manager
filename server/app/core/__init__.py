# -*- coding: utf-8 -*-
"""
核心功能模块
包括安全、中间件、运行时配置等核心功能
"""

from .security import (
    DataEncryption,
    encryptor
)

from .dependencies import (
    get_db,
    get_default_user_id
)

from .middleware import (
    SecurityHeadersMiddleware,
    SimpleRateLimitMiddleware,
    RequestLoggingMiddleware,
    ContentTypeValidationMiddleware,
    setup_cors_middleware,
    setup_security_middleware
)

from .runtime_config import (
    RuntimeConfig,
    VoiceSettings,
    AISettings,
    runtime_config
)

__all__ = [
    # Security
    "DataEncryption",
    "encryptor",

    # Dependencies
    "get_db",
    "get_default_user_id",

    # Middleware
    "SecurityHeadersMiddleware",
    "SimpleRateLimitMiddleware",
    "RequestLoggingMiddleware",
    "ContentTypeValidationMiddleware",
    "setup_cors_middleware",
    "setup_security_middleware",

    # Runtime Config
    "RuntimeConfig",
    "VoiceSettings",
    "AISettings",
    "runtime_config",
]