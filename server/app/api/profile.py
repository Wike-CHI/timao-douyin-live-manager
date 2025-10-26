# -*- coding: utf-8 -*-
"""
用户个人资料管理API路由
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime

from app.core.dependencies import get_current_active_user
from app.services.profile_service import profile_service
from app.models import User

router = APIRouter(prefix="/profile", tags=["用户资料"])


# Pydantic 模型
class BasicInfoUpdate(BaseModel):
    """基本信息更新"""
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    birth_date: Optional[datetime] = None
    gender: Optional[str] = None
    
    @validator('bio')
    def validate_bio(cls, v):
        if v and len(v) > 500:
            raise ValueError('个人简介不能超过500字符')
        return v
    
    @validator('website')
    def validate_website(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('网站地址必须以http://或https://开头')
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        if v and v not in ['male', 'female', 'other']:
            raise ValueError('性别必须是male、female或other')
        return v


class ContactInfoUpdate(BaseModel):
    """联系信息更新"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('手机号格式不正确')
        return v


class PreferencesUpdate(BaseModel):
    """偏好设置更新"""
    language: Optional[str] = None
    timezone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    
    @validator('language')
    def validate_language(cls, v):
        if v and v not in ['zh-CN', 'zh-TW', 'en-US', 'ja-JP', 'ko-KR']:
            raise ValueError('不支持的语言')
        return v


class PrivacySettingsUpdate(BaseModel):
    """隐私设置更新"""
    show_email: bool = False
    show_phone: bool = False
    show_real_name: bool = False
    allow_search: bool = True
    show_online_status: bool = True
    allow_friend_requests: bool = True


class TwoFactorVerification(BaseModel):
    """双因素认证验证"""
    verification_code: str
    
    @validator('verification_code')
    def validate_code(cls, v):
        if not v or len(v) != 6 or not v.isdigit():
            raise ValueError('验证码必须是6位数字')
        return v


class UserProfileResponse(BaseModel):
    """用户资料响应"""
    id: str
    username: str
    email: str
    phone: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    website: Optional[str]
    birth_date: Optional[datetime]
    gender: Optional[str]
    language: Optional[str]
    timezone: Optional[str]
    preferences: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    is_email_verified: bool
    is_phone_verified: bool
    status: str


class SecurityInfoResponse(BaseModel):
    """安全信息响应"""
    two_factor_enabled: bool
    is_email_verified: bool
    is_phone_verified: bool
    last_password_change: Optional[datetime]
    last_login: Optional[datetime]
    login_count: int
    failed_login_attempts: int
    account_locked_until: Optional[datetime]


# API 路由
@router.get("/", response_model=UserProfileResponse)
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """获取当前用户资料"""
    profile = await profile_service.get_user_profile(current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="用户资料不存在")
    
    return profile


@router.put("/basic")
async def update_basic_info(
    info: BasicInfoUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """更新基本信息"""
    success = await profile_service.update_basic_info(
        user_id=current_user.id,
        full_name=info.full_name,
        bio=info.bio,
        location=info.location,
        website=info.website,
        birth_date=info.birth_date,
        gender=info.gender
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="更新失败")
    
    return {"message": "基本信息更新成功"}


@router.put("/contact")
async def update_contact_info(
    info: ContactInfoUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """更新联系信息"""
    result = await profile_service.update_contact_info(
        user_id=current_user.id,
        email=info.email,
        phone=info.phone
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """上传头像"""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="只能上传图片文件")
    
    # 读取文件数据
    file_data = await file.read()
    
    result = await profile_service.upload_avatar(
        user_id=current_user.id,
        file_data=file_data,
        filename=file.filename
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.delete("/avatar")
async def delete_avatar(current_user: User = Depends(get_current_active_user)):
    """删除头像"""
    success = await profile_service.delete_avatar(current_user.id)
    
    if not success:
        raise HTTPException(status_code=400, detail="删除失败")
    
    return {"message": "头像删除成功"}


@router.put("/preferences")
async def update_preferences(
    prefs: PreferencesUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """更新偏好设置"""
    success = await profile_service.update_preferences(
        user_id=current_user.id,
        language=prefs.language,
        timezone=prefs.timezone,
        preferences=prefs.preferences
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="更新失败")
    
    return {"message": "偏好设置更新成功"}


@router.get("/preferences")
async def get_preferences(current_user: User = Depends(get_current_active_user)):
    """获取偏好设置"""
    preferences = await profile_service.get_preferences(current_user.id)
    if preferences is None:
        raise HTTPException(status_code=404, detail="偏好设置不存在")
    
    return preferences


@router.put("/privacy")
async def update_privacy_settings(
    privacy: PrivacySettingsUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """更新隐私设置"""
    success = await profile_service.update_privacy_settings(
        user_id=current_user.id,
        privacy_settings=privacy.dict()
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="更新失败")
    
    return {"message": "隐私设置更新成功"}


@router.get("/security", response_model=SecurityInfoResponse)
async def get_security_info(current_user: User = Depends(get_current_active_user)):
    """获取账户安全信息"""
    security_info = await profile_service.get_security_info(current_user.id)
    if not security_info:
        raise HTTPException(status_code=404, detail="安全信息不存在")
    
    return security_info


@router.post("/2fa/enable")
async def enable_two_factor(current_user: User = Depends(get_current_active_user)):
    """启用双因素认证"""
    result = await profile_service.enable_two_factor(current_user.id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/2fa/verify")
async def verify_two_factor_setup(
    verification: TwoFactorVerification,
    current_user: User = Depends(get_current_active_user)
):
    """验证双因素认证设置"""
    result = await profile_service.verify_two_factor_setup(
        user_id=current_user.id,
        verification_code=verification.verification_code
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/2fa/disable")
async def disable_two_factor(
    verification: TwoFactorVerification,
    current_user: User = Depends(get_current_active_user)
):
    """禁用双因素认证"""
    result = await profile_service.disable_two_factor(
        user_id=current_user.id,
        verification_code=verification.verification_code
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result