# -*- coding: utf-8 -*-
"""User authentication and profile endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr

from ..models.user import UserDocument, UserPublic, UserSessionDocument
from ..services.auth_utils import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from ..utils.settings import get_settings

router = APIRouter(prefix="/api/auth", tags=["Auth"])

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    nickname: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserDocument:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效 token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效或过期 token")
    user = await UserDocument.get(user_id)
    if not user or user.status != user.status.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用")
    return user


@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest) -> TokenResponse:
    exists = await UserDocument.find_one(UserDocument.email == data.email)
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已注册")
    user = UserDocument(
        email=data.email,
        password_hash=hash_password(data.password),
        nickname=data.nickname or data.email.split("@")[0],
    )
    await user.insert()
    access_token = create_access_token(user.id, {"role": user.role})
    refresh_token = create_refresh_token(user.id)
    await UserSessionDocument(
        user_id=user.id,
        refresh_token=refresh_token,
        expires_at=UserSessionDocument.expires_at_default(settings.refresh_token_expire_days),
    ).insert()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest) -> TokenResponse:
    user = await UserDocument.find_one(UserDocument.email == data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
    if user.status != user.status.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已禁用")
    user.last_login_at = datetime.utcnow()
    await user.save()
    access_token = create_access_token(user.id, {"role": user.role})
    refresh_token = create_refresh_token(user.id)
    await UserSessionDocument(
        user_id=user.id,
        refresh_token=refresh_token,
        expires_at=UserSessionDocument.expires_at_default(settings.refresh_token_expire_days),
    ).insert()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest) -> TokenResponse:
    try:
        payload = jwt.decode(data.refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效 token 类型")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效 token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新 token 已失效")

    session = await UserSessionDocument.find_one(UserSessionDocument.refresh_token == data.refresh_token)
    if not session or session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新 token 无效或已过期")

    user = await UserDocument.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    access_token = create_access_token(user.id, {"role": user.role})
    new_refresh = create_refresh_token(user.id)
    session.refresh_token = new_refresh
    session.expires_at = UserSessionDocument.expires_at_default(settings.refresh_token_expire_days)
    await session.save()
    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


@router.post("/logout")
async def logout(data: RefreshRequest) -> dict[str, str]:
    session = await UserSessionDocument.find_one(UserSessionDocument.refresh_token == data.refresh_token)
    if session:
        await session.delete()
    return {"message": "已退出"}


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: UserDocument = Depends(get_current_user)) -> UserPublic:
    return UserPublic(**current_user.dict())


@router.patch("/profile", response_model=UserPublic)
async def update_profile(data: UpdateProfileRequest, current_user: UserDocument = Depends(get_current_user)) -> UserPublic:
    if data.nickname is not None:
        current_user.nickname = data.nickname
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url
    current_user.updated_at = datetime.utcnow()
    await current_user.save()
    return UserPublic(**current_user.dict())


@router.get("/sessions")
async def list_sessions(current_user: UserDocument = Depends(get_current_user)) -> list[dict[str, str | datetime]]:
    sessions = await UserSessionDocument.find(UserSessionDocument.user_id == current_user.id).to_list()
    return [
        {
            "id": s.id,
            "user_agent": s.user_agent,
            "ip": s.ip,
            "expires_at": s.expires_at,
            "created_at": s.created_at,
        }
        for s in sessions
    ]
