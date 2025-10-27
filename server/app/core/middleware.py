# -*- coding: utf-8 -*-
"""
安全中间件模块
包括CORS、安全头、请求日志、速率限制等中间件
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from server.app.core.security import LoginLimiter
from server.app.models.permission import AuditLog
from server.app.database import DatabaseManager
import json

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none';"
        )
        
        # 移除可能泄露信息的头
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取客户端IP
        client_ip = request.client.host
        
        # 检查速率限制
        if LoginLimiter.is_locked(client_ip, "rate_limit"):
            return Response(
                content=json.dumps({"detail": "Rate limit exceeded"}),
                status_code=429,
                media_type="application/json"
            )
        
        # 记录请求
        result = LoginLimiter.record_attempt(client_ip, True, "rate_limit")
        
        response = await call_next(request)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 记录请求信息
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
            "content_type": request.headers.get("content-type", ""),
        }
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            response_info = {
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
            }
            
            # 记录日志
            if response.status_code >= 400:
                logger.warning(f"Request failed: {request_info} -> {response_info}")
            else:
                logger.info(f"Request processed: {request_info} -> {response_info}")
            
            # 添加处理时间头
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request error: {request_info} -> {str(e)} (time: {process_time})")
            raise


class AuditLogMiddleware(BaseHTTPMiddleware):
    """审计日志中间件"""
    
    def __init__(self, app, log_all_requests: bool = False):
        super().__init__(app)
        self.log_all_requests = log_all_requests
        self.sensitive_paths = [
            "/auth/login",
            "/auth/register",
            "/auth/change-password",
            "/admin/",
            "/subscription/payment"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否需要记录此请求
        should_log = self.log_all_requests or any(
            path in str(request.url) for path in self.sensitive_paths
        )
        
        if not should_log:
            return await call_next(request)
        
        start_time = time.time()
        user_id = None
        
        # 尝试从Authorization头获取用户ID
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from server.app.core.security import JWTManager
                token = auth_header.split(" ")[1]
                payload = JWTManager.verify_token(token, "access")
                user_id = payload.get("sub")
            except:
                pass
        
        # 处理请求
        response = await call_next(request)
        
        # 记录审计日志
        try:
            db_manager = DatabaseManager()
            db = db_manager.get_session()
            
            audit_log = AuditLog(
                user_id=user_id,
                action=f"{request.method} {request.url.path}",
                resource=request.url.path,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent", ""),
                success=response.status_code < 400,
                error_message=None if response.status_code < 400 else f"HTTP {response.status_code}",
                request_data={
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers),
                    "query_params": dict(request.query_params)
                },
                response_data={
                    "status_code": response.status_code,
                    "process_time": time.time() - start_time
                }
            )
            
            db.add(audit_log)
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to log audit entry: {e}")
        
        return response


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """IP白名单中间件"""
    
    def __init__(self, app, whitelist: list = None, admin_only: bool = True):
        super().__init__(app)
        self.whitelist = whitelist or []
        self.admin_only = admin_only
        self.admin_paths = ["/admin/", "/api/admin/"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host
        
        # 检查是否为管理员路径
        is_admin_path = any(path in str(request.url) for path in self.admin_paths)
        
        # 如果是管理员路径且启用了IP限制
        if is_admin_path and self.admin_only and self.whitelist:
            if client_ip not in self.whitelist:
                logger.warning(f"Blocked admin access from IP: {client_ip}")
                return Response(
                    content=json.dumps({"detail": "Access denied"}),
                    status_code=403,
                    media_type="application/json"
                )
        
        return await call_next(request)


class ContentTypeValidationMiddleware(BaseHTTPMiddleware):
    """内容类型验证中间件"""
    
    def __init__(self, app, allowed_types: list = None):
        super().__init__(app)
        self.allowed_types = allowed_types or [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "text/plain"
        ]
        self.methods_with_body = ["POST", "PUT", "PATCH"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查需要验证内容类型的方法
        if request.method in self.methods_with_body:
            content_type = request.headers.get("content-type", "").split(";")[0]
            
            if content_type and content_type not in self.allowed_types:
                logger.warning(f"Blocked request with invalid content type: {content_type}")
                return Response(
                    content=json.dumps({"detail": "Invalid content type"}),
                    status_code=415,
                    media_type="application/json"
                )
        
        return await call_next(request)


def setup_cors_middleware(app, origins: list = None):
    """设置CORS中间件"""
    if origins is None:
        origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:8080",
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time"]
    )


def setup_security_middleware(app, config: dict = None):
    """设置所有安全中间件"""
    if config is None:
        config = {}
    
    # 内容类型验证
    if config.get("validate_content_type", True):
        app.add_middleware(ContentTypeValidationMiddleware)
    
    # IP白名单（仅管理员路径）
    whitelist = config.get("admin_ip_whitelist", [])
    if whitelist:
        app.add_middleware(IPWhitelistMiddleware, whitelist=whitelist)
    
    # 审计日志
    if config.get("enable_audit_log", True):
        app.add_middleware(
            AuditLogMiddleware,
            log_all_requests=config.get("log_all_requests", False)
        )
    
    # 请求日志
    if config.get("enable_request_log", True):
        app.add_middleware(RequestLoggingMiddleware)
    
    # 速率限制
    if config.get("enable_rate_limit", True):
        app.add_middleware(
            RateLimitMiddleware,
            calls=config.get("rate_limit_calls", 100),
            period=config.get("rate_limit_period", 60)
        )
    
    # 安全头
    if config.get("enable_security_headers", True):
        app.add_middleware(SecurityHeadersMiddleware)
    
    # CORS
    setup_cors_middleware(app, config.get("cors_origins"))
    
    logger.info("Security middleware setup completed")