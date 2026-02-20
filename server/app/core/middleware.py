# -*- coding: utf-8 -*-
"""
安全中间件模块
简化版 - 无用户系统
包括CORS、安全头、请求日志等中间件
"""

import time
import logging
from collections import defaultdict
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
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
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss: http://127.0.0.1:* http://localhost:* https:; "
            "frame-ancestors 'none';"
        )

        # 移除可能泄露信息的头
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)

        return response


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """简单速率限制中间件（内存版）"""

    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self._requests = defaultdict(list)

    def _is_rate_limited(self, client_ip: str) -> bool:
        """检查是否超过速率限制"""
        now = time.time()
        # 清理过期记录
        self._requests[client_ip] = [
            t for t in self._requests[client_ip]
            if now - t < self.period
        ]
        # 检查是否超限
        if len(self._requests[client_ip]) >= self.calls:
            return True
        # 记录本次请求
        self._requests[client_ip].append(now)
        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host

        if self._is_rate_limited(client_ip):
            return Response(
                content=json.dumps({"detail": "Rate limit exceeded"}),
                status_code=429,
                media_type="application/json"
            )

        return await call_next(request)


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
            "http://localhost:10050",
            "http://localhost:3001",
            "http://localhost:8080",
            "http://localhost:10200",  # Vite dev server
            "http://127.0.0.1:10050",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:10200",
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

    # 请求日志
    if config.get("enable_request_log", True):
        app.add_middleware(RequestLoggingMiddleware)

    # 速率限制
    if config.get("enable_rate_limit", True):
        app.add_middleware(
            SimpleRateLimitMiddleware,
            calls=config.get("rate_limit_calls", 100),
            period=config.get("rate_limit_period", 60)
        )

    # 安全头
    if config.get("enable_security_headers", True):
        app.add_middleware(SecurityHeadersMiddleware)

    # CORS
    setup_cors_middleware(app, config.get("cors_origins"))

    logger.info("Security middleware setup completed (simplified - no auth system)")
