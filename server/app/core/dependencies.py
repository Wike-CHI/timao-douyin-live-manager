# -*- coding: utf-8 -*-
"""
FastAPI依赖项模块
用于认证、权限检查、会话管理等
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from server.app.database import DatabaseManager
from server.app.models.user import User, UserRole
from server.app.models.permission import Permission, RolePermission
from server.app.core.security import JWTManager, SessionManager, LoginLimiter
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer认证
security = HTTPBearer()

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

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    token = credentials.credentials
    
    try:
        # 验证JWT令牌
        payload = JWTManager.verify_token(token, "access")
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # 从数据库获取用户
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # 检查用户状态
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is locked"
            )
        
        # 更新会话活动时间
        session_id = payload.get("session_id")
        if session_id:
            SessionManager.update_session_activity(session_id)
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def require_roles(required_roles: List[str]):
    """要求特定角色的依赖项"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_roles = [role.name for role in current_user.roles]
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {required_roles}"
            )
        return current_user
    return role_checker

def require_permissions(required_permissions: List[str]):
    """要求特定权限的依赖项"""
    def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        # 获取用户所有权限
        user_permissions = set()
        for role in current_user.roles:
            role_permissions = db.query(RolePermission).filter(
                RolePermission.role_id == role.id,
                RolePermission.granted == True
            ).all()
            for rp in role_permissions:
                permission = db.query(Permission).filter(
                    Permission.id == rp.permission_id
                ).first()
                if permission:
                    user_permissions.add(permission.name)
        
        # 检查是否有所需权限
        missing_permissions = set(required_permissions) - user_permissions
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {list(missing_permissions)}"
            )
        
        return current_user
    return permission_checker

def require_admin_role(current_user: User = Depends(get_current_active_user)) -> User:
    """要求管理员角色"""
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and "super_admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return current_user

def require_super_admin_role(current_user: User = Depends(get_current_active_user)) -> User:
    """要求超级管理员角色"""
    user_roles = [role.name for role in current_user.roles]
    if "super_admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin role required"
        )
    return current_user

async def check_rate_limit(
    request: Request,
    identifier_type: str = "ip",
    max_requests: int = 100,
    window_minutes: int = 60
):
    """检查速率限制"""
    if identifier_type == "ip":
        identifier = request.client.host
    elif identifier_type == "user":
        # 从请求中获取用户ID（需要先认证）
        try:
            credentials = await security(request)
            payload = JWTManager.verify_token(credentials.credentials, "access")
            identifier = payload.get("sub")
        except:
            identifier = request.client.host
    else:
        identifier = request.client.host
    
    # 使用LoginLimiter的逻辑进行速率限制
    status_info = LoginLimiter.get_status(identifier, "rate_limit")
    if status_info.get("locked"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    return True

class OptionalAuth:
    """可选认证依赖项"""
    
    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
    
    async def __call__(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
        db: Session = Depends(get_db)
    ) -> Optional[User]:
        """可选的用户认证"""
        if not credentials:
            return None
        
        try:
            token = credentials.credentials
            payload = JWTManager.verify_token(token, "access")
            user_id = payload.get("sub")
            
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.is_active and not user.is_locked:
                    # 更新会话活动时间
                    session_id = payload.get("session_id")
                    if session_id:
                        SessionManager.update_session_activity(session_id)
                    return user
        except:
            pass
        
        return None

# 实例化可选认证
optional_auth = OptionalAuth()

def get_user_from_token(token: str, db: Session) -> Optional[User]:
    """从令牌获取用户（工具函数）"""
    try:
        payload = JWTManager.verify_token(token, "access")
        user_id = payload.get("sub")
        
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.is_active and not user.is_locked:
                return user
    except:
        pass
    
    return None

def validate_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """验证刷新令牌"""
    token = credentials.credentials
    
    try:
        # 验证刷新令牌
        payload = JWTManager.verify_token(token, "refresh")
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # 检查用户是否存在且活跃
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active or user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return payload
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token"
        )

async def get_request_info(request: Request) -> dict:
    """获取请求信息（用于审计日志）"""
    return {
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent", ""),
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers)
    }