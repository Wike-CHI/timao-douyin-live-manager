# -*- coding: utf-8 -*-
"""
FastAPI依赖项模块（本地化版本）

本地化模式下，移除数据库和JWT认证，返回固定的本地用户。
"""

from typing import Optional, List, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)


class LocalUser:
    """本地用户对象 - 替代数据库User模型"""
    
    def __init__(self):
        self.id = 1
        self.username = "local_user"
        self.email = "local@localhost"
        self.is_active = True
        self.is_deleted = False
        self.role = "super_admin"
        self.roles = []
    
    def is_locked(self) -> bool:
        """用户是否被锁定"""
        return False
    
    def __repr__(self):
        return f"<LocalUser(id={self.id}, username={self.username})>"


# HTTP Bearer认证 - 保留用于API兼容性，但不实际验证
security = HTTPBearer(auto_error=False)

# 全局本地用户实例
_local_user = LocalUser()


def get_db():
    """
    获取数据库会话 - 本地化模式下返回None
    
    保留此函数签名以保持API兼容性。
    """
    yield None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> LocalUser:
    """
    获取当前用户 - 本地化模式下始终返回本地用户
    
    保留此函数签名以保持API兼容性，但不进行任何认证。
    """
    return _local_user


async def get_current_active_user(
    current_user: LocalUser = Depends(get_current_user)
) -> LocalUser:
    """
    获取当前活跃用户 - 本地化模式下始终返回本地用户
    """
    return current_user


def require_roles(required_roles: List[str]):
    """
    要求特定角色的依赖项 - 本地化模式下始终通过
    
    保留此函数签名以保持API兼容性。
    """
    def role_checker(current_user: LocalUser = Depends(get_current_active_user)) -> LocalUser:
        # 本地化模式：始终通过角色检查
        return current_user
    return role_checker


def require_permissions(required_permissions: List[str]):
    """
    要求特定权限的依赖项 - 本地化模式下始终通过
    
    保留此函数签名以保持API兼容性。
    """
    def permission_checker(
        current_user: LocalUser = Depends(get_current_active_user)
    ) -> LocalUser:
        # 本地化模式：始终通过权限检查
        return current_user
    return permission_checker


def require_admin_role(current_user: LocalUser = Depends(get_current_active_user)) -> LocalUser:
    """
    要求管理员角色 - 本地化模式下始终通过
    """
    return current_user


def require_super_admin_role(current_user: LocalUser = Depends(get_current_active_user)) -> LocalUser:
    """
    要求超级管理员角色 - 本地化模式下始终通过
    """
    return current_user


async def check_rate_limit(
    request: Request,
    identifier_type: str = "ip",
    max_requests: int = 100,
    window_minutes: int = 60
):
    """
    检查速率限制 - 本地化模式下不限制
    """
    return True


class OptionalAuth:
    """可选认证依赖项 - 本地化模式下始终返回本地用户"""
    
    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
    
    async def __call__(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
    ) -> Optional[LocalUser]:
        """可选的用户认证 - 始终返回本地用户"""
        return _local_user


# 实例化可选认证
optional_auth = OptionalAuth()


def get_user_from_token(token: str, db: Any = None) -> Optional[LocalUser]:
    """
    从令牌获取用户（工具函数）- 本地化模式下忽略token
    """
    return _local_user


def validate_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    验证刷新令牌 - 本地化模式下返回固定payload
    """
    return {
        "sub": "1",
        "user_id": 1,
        "username": "local_user"
    }


async def get_request_info(request: Request) -> dict:
    """获取请求信息（用于审计日志）"""
    return {
        "ip_address": request.client.host if request.client else "127.0.0.1",
        "user_agent": request.headers.get("user-agent", ""),
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers)
    }


# ========== 兼容性别名 ==========
# 以下类型别名用于保持现有代码的类型兼容性

User = LocalUser  # 类型别名，保持现有代码的兼容性
