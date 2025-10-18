# -*- coding: utf-8 -*-
"""User and session documents for MongoDB."""
from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import uuid4

from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr, Field


class UserStatus(str, Enum):
    active = "active"
    disabled = "disabled"


class UserRole(str, Enum):
    user = "user"
    admin = "admin"


class UserDocument(Document):
    id: str = Field(default_factory=lambda: uuid4().hex)
    email: Indexed(EmailStr, unique=True)
    password_hash: str
    nickname: str = Field(default_factory=lambda: "未命名")
    avatar_url: Optional[str] = None
    role: UserRole = UserRole.user
    status: UserStatus = UserStatus.active
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None

    class Settings:
        name = "users"
        use_state_management = True


class UserSessionDocument(Document):
    id: str = Field(default_factory=lambda: uuid4().hex)
    user_id: str
    refresh_token: str
    user_agent: Optional[str] = None
    ip: Optional[str] = None
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "user_sessions"

    @classmethod
    def expires_at_default(cls, days: int) -> datetime:
        return datetime.utcnow() + timedelta(days=days)


# === Pydantic response / request models ===

class UserPublic(BaseModel):
    id: str
    email: EmailStr
    nickname: str
    avatar_url: Optional[str] = None
    role: UserRole
    status: UserStatus
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        orm_mode = True
