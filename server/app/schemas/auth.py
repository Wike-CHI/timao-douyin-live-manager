# -*- coding: utf-8 -*-
"""
认证相关数据模型
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
import re
import secrets
from ..schemas.common import BaseResponse


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
    remember_me: bool = Field(True, description="默认记住用户")


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
    """登录响应模型"""
    success: bool = Field(default=True)
    token: str = Field(..., description="前端期望的字段名")
    access_token: str
    refresh_token: str
    token_type: str = Field(default="bearer")
    expires_in: int = Field(default=86400, description="24小时")
    user: UserResponse
    isPaid: bool = Field(default=False)
    firstFreeUsed: bool = Field(default=False)
    aiUsage: Optional[Dict[str, Any]] = None


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

