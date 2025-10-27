# -*- coding: utf-8 -*-
"""
用户认证API路由
"""

from datetime import datetime
import secrets
from typing import Optional
import re
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session

from server.app.database import get_db_session
from server.app.services.user_service import UserService
from server.app.models.user import UserRoleEnum


# 创建路由器
router = APIRouter(prefix="/api/auth", tags=["认证"])

# HTTP Bearer 认证
security = HTTPBearer()


# Pydantic 模型
class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    email: EmailStr
    password: str
    nickname: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None
    
    @validator('username', pre=True, always=True)
    def validate_or_generate_username(cls, v, values):
        candidate = (v or "").strip()
        email = values.get("email")
        nickname = (values.get("nickname") or "").strip()
        
        if not candidate:
            if nickname:
                candidate = nickname
            elif email:
                candidate = email.split("@")[0]
        
        candidate = re.sub(r"[^A-Za-z0-9_-]", "", candidate or "")
        if len(candidate) < 3:
            candidate = f"user_{secrets.token_hex(3)}"
        candidate = candidate[:50]
        
        if len(candidate) < 3 or len(candidate) > 50:
            raise ValueError('用户名长度必须在3-50个字符之间')
        if not candidate.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return candidate
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6个字符')
        return v


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username_or_email: str
    password: str


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    nickname: Optional[str]
    avatar_url: Optional[str]
    role: str
    status: str
    email_verified: bool
    phone_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24小时
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6个字符')
        return v


class EmailVerifyRequest(BaseModel):
    """邮箱验证请求"""
    token: str


# 依赖注入：获取当前用户
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session)
) -> Optional[dict]:
    """获取当前认证用户"""
    try:
        token = credentials.credentials
        user = UserService.validate_session(token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "status": user.status.value
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )


# API 路由
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: UserRegisterRequest,
    req: Request,
    db: Session = Depends(get_db_session)
):
    """用户注册"""
    try:
        user = UserService.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            phone=request.phone,
            nickname=request.nickname
        )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            role=user.role.value,
            status=user.status.value,
            email_verified=user.email_verified,
            phone_verified=user.phone_verified,
            created_at=user.created_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


@router.post("/login", response_model=LoginResponse)
async def login_user(
    request: UserLoginRequest,
    req: Request,
    db: Session = Depends(get_db_session)
):
    """用户登录"""
    try:
        # 获取客户端IP
        client_ip = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent")
        
        # 认证用户
        user = UserService.authenticate_user(
            username_or_email=request.username_or_email,
            password=request.password,
            ip_address=client_ip
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名/邮箱或密码错误"
            )
        
        # 创建会话
        session = UserService.create_session(
            user=user,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return LoginResponse(
            access_token=session.session_token,
            refresh_token=session.refresh_token,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                nickname=user.nickname,
                avatar_url=user.avatar_url,
                role=user.role.value,
                status=user.status.value,
                email_verified=user.email_verified,
                phone_verified=user.phone_verified,
                created_at=user.created_at
            )
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db_session)
):
    """刷新访问令牌"""
    try:
        session = UserService.refresh_session(request.refresh_token)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        # 获取用户信息
        user = UserService.get_user_by_id(session.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )
        
        return LoginResponse(
            access_token=session.session_token,
            refresh_token=session.refresh_token,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                nickname=user.nickname,
                avatar_url=user.avatar_url,
                role=user.role.value,
                status=user.status.value,
                email_verified=user.email_verified,
                phone_verified=user.phone_verified,
                created_at=user.created_at
            )
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌失败"
        )


@router.post("/logout")
async def logout_user(
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session)
):
    """用户登出"""
    try:
        token = credentials.credentials
        success = UserService.logout_user(token)
        
        if success:
            return {"message": "登出成功"}
        else:
            return {"message": "登出失败"}
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失败"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取当前用户信息"""
    try:
        user = UserService.get_user_by_id(current_user["id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            role=user.role.value,
            status=user.status.value,
            email_verified=user.email_verified,
            phone_verified=user.phone_verified,
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """修改密码"""
    try:
        success = UserService.change_password(
            user_id=current_user["id"],
            old_password=request.old_password,
            new_password=request.new_password
        )
        
        if success:
            return {"message": "密码修改成功，请重新登录"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="原密码错误"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码修改失败"
        )


@router.post("/verify-email")
async def verify_email(
    request: EmailVerifyRequest,
    db: Session = Depends(get_db_session)
):
    """验证邮箱"""
    try:
        success = UserService.verify_email(request.token)
        
        if success:
            return {"message": "邮箱验证成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的验证令牌"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="邮箱验证失败"
        )


@router.get("/stats")
async def get_user_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取用户统计信息"""
    try:
        stats = UserService.get_user_stats(current_user["id"])
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )
