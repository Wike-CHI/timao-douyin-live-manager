"""Authentication related schemas."""

from __future__ import annotations

import re
import secrets
from datetime import datetime
from typing import Dict, Optional, Any

from pydantic import BaseModel, EmailStr, validator


class UserRegisterRequest(BaseModel):
    """User registration payload."""

    email: EmailStr
    password: str
    nickname: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None

    @validator("username", pre=True, always=True)
    def validate_or_generate_username(cls, value: Optional[str], values: Dict[str, Any]) -> str:
        candidate = (value or "").strip()
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
            raise ValueError("用户名长度必须在3-50个字符之间")
        if not candidate.replace("_", "").replace("-", "").isalnum():
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        return candidate

    @validator("password")
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("密码长度至少6个字符")
        return value


class UserLoginRequest(BaseModel):
    """User login payload."""

    username_or_email: str
    password: str
    remember_me: bool = True


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @validator("new_password")
    def validate_new_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("密码长度至少6个字符")
        return value


class EmailVerifyRequest(BaseModel):
    token: str


class UserResponse(BaseModel):
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
    success: bool = True
    token: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 86400
    user: UserResponse
    isPaid: bool = False
    firstFreeUsed: bool = False
    aiUsage: Optional[Dict[str, Any]] = None


class RegisterResponse(BaseModel):
    success: bool = True
    user: UserResponse

