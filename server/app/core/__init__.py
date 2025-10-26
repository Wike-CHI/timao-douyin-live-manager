# -*- coding: utf-8 -*-
"""
核心功能模块
包括安全、认证、权限、中间件等核心功能
"""

from .security import (
    PasswordPolicy,
    LoginLimiter,
    SessionManager,
    DataEncryption,
    JWTManager,
    hash_password,
    verify_password,
    generate_verification_token,
    encryptor
)

from .dependencies import (
    get_db,
    get_current_user,
    get_current_active_user,
    require_roles,
    require_permissions,
    require_admin_role,
    require_super_admin_role,
    check_rate_limit,
    optional_auth,
    get_user_from_token,
    validate_refresh_token,
    get_request_info
)

from .middleware import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    AuditLogMiddleware,
    IPWhitelistMiddleware,
    ContentTypeValidationMiddleware,
    setup_cors_middleware,
    setup_security_middleware
)

__all__ = [
    # Security
    "PasswordPolicy",
    "LoginLimiter", 
    "SessionManager",
    "DataEncryption",
    "JWTManager",
    "hash_password",
    "verify_password",
    "generate_verification_token",
    "encryptor",
    
    # Dependencies
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "require_roles",
    "require_permissions", 
    "require_admin_role",
    "require_super_admin_role",
    "check_rate_limit",
    "optional_auth",
    "get_user_from_token",
    "validate_refresh_token",
    "get_request_info",
    
    # Middleware
    "SecurityHeadersMiddleware",
    "RateLimitMiddleware",
    "RequestLoggingMiddleware",
    "AuditLogMiddleware",
    "IPWhitelistMiddleware",
    "ContentTypeValidationMiddleware",
    "setup_cors_middleware",
    "setup_security_middleware"
]