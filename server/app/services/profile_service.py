# -*- coding: utf-8 -*-
"""
用户个人资料管理服务
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime
import os
import uuid
import json
import logging
from PIL import Image
import io
import base64

from server.app.models import User, AuditLog
from server.app.database import DatabaseManager
from server.app.core.security import encryptor

logger = logging.getLogger(__name__)


class ProfileService:
    """用户个人资料管理服务"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.upload_dir = "uploads/avatars"
        self.max_avatar_size = 5 * 1024 * 1024  # 5MB
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        
        # 确保上传目录存在
        os.makedirs(self.upload_dir, exist_ok=True)
    
    # 基本资料管理
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户个人资料"""
        with self.db_manager.get_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # 解密敏感信息
            phone = None
            if user.phone:
                try:
                    phone = encryptor.decrypt(user.phone)
                except:
                    phone = user.phone  # 如果解密失败，使用原值
            
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone": phone,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "bio": user.bio,
                "location": user.location,
                "website": user.website,
                "birth_date": user.birth_date,
                "gender": user.gender,
                "language": user.language,
                "timezone": user.timezone,
                "preferences": user.preferences,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "last_login_at": user.last_login_at,
                "is_email_verified": user.is_email_verified,
                "is_phone_verified": user.is_phone_verified,
                "status": user.status
            }
    
    async def update_basic_info(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        bio: Optional[str] = None,
        location: Optional[str] = None,
        website: Optional[str] = None,
        birth_date: Optional[datetime] = None,
        gender: Optional[str] = None
    ) -> bool:
        """更新基本信息"""
        try:
            with self.db_manager.get_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                # 更新字段
                if full_name is not None:
                    user.full_name = full_name
                if bio is not None:
                    user.bio = bio
                if location is not None:
                    user.location = location
                if website is not None:
                    user.website = website
                if birth_date is not None:
                    user.birth_date = birth_date
                if gender is not None:
                    user.gender = gender
                
                user.updated_at = datetime.utcnow()
                db.commit()
                
                # 记录审计日志
                await AuditLog.log_action(
                    user_id=user_id,
                    action="update_basic_info",
                    resource_type="user_profile",
                    resource_id=user_id,
                    details={
                        "updated_fields": [
                            field for field, value in [
                                ("full_name", full_name),
                                ("bio", bio),
                                ("location", location),
                                ("website", website),
                                ("birth_date", birth_date),
                                ("gender", gender)
                            ] if value is not None
                        ]
                    }
                )
                
                logger.info(f"用户 {user_id} 更新基本信息")
                return True
                
        except Exception as e:
            logger.error(f"更新基本信息失败: {e}")
            return False
    
    async def update_contact_info(
        self,
        user_id: str,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新联系信息"""
        try:
            with self.db_manager.get_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return {"success": False, "message": "用户不存在"}
                
                changes = []
                
                # 更新邮箱
                if email is not None and email != user.email:
                    # 检查邮箱是否已被使用
                    existing = db.query(User).filter(
                        User.email == email,
                        User.id != user_id
                    ).first()
                    
                    if existing:
                        return {"success": False, "message": "邮箱已被使用"}
                    
                    user.email = email
                    user.is_email_verified = False  # 需要重新验证
                    changes.append("email")
                
                # 更新手机号
                if phone is not None:
                    # 加密手机号
                    encrypted_phone = encryptor.encrypt(phone) if phone else None
                    
                    if encrypted_phone != user.phone:
                        # 检查手机号是否已被使用
                        if phone:
                            existing = db.query(User).filter(
                                User.phone == encrypted_phone,
                                User.id != user_id
                            ).first()
                            
                            if existing:
                                return {"success": False, "message": "手机号已被使用"}
                        
                        user.phone = encrypted_phone
                        user.is_phone_verified = False  # 需要重新验证
                        changes.append("phone")
                
                if changes:
                    user.updated_at = datetime.utcnow()
                    db.commit()
                    
                    # 记录审计日志
                    await AuditLog.log_action(
                        user_id=user_id,
                        action="update_contact_info",
                        resource_type="user_profile",
                        resource_id=user_id,
                        details={"updated_fields": changes}
                    )
                    
                    logger.info(f"用户 {user_id} 更新联系信息: {changes}")
                
                return {
                    "success": True,
                    "message": "联系信息更新成功",
                    "changes": changes,
                    "verification_required": changes  # 需要重新验证的字段
                }
                
        except Exception as e:
            logger.error(f"更新联系信息失败: {e}")
            return {"success": False, "message": "更新失败"}
    
    # 头像管理
    async def upload_avatar(
        self,
        user_id: str,
        file_data: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """上传头像"""
        try:
            # 检查文件大小
            if len(file_data) > self.max_avatar_size:
                return {"success": False, "message": "文件大小超过限制"}
            
            # 检查文件扩展名
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in self.allowed_extensions:
                return {"success": False, "message": "不支持的文件格式"}
            
            # 生成唯一文件名
            unique_filename = f"{user_id}_{uuid.uuid4().hex}{file_ext}"
            file_path = os.path.join(self.upload_dir, unique_filename)
            
            # 处理图片
            try:
                image = Image.open(io.BytesIO(file_data))
                
                # 转换为RGB模式（如果需要）
                if image.mode in ('RGBA', 'LA', 'P'):
                    image = image.convert('RGB')
                
                # 调整大小（最大300x300）
                image.thumbnail((300, 300), Image.Resampling.LANCZOS)
                
                # 保存图片
                image.save(file_path, 'JPEG', quality=85, optimize=True)
                
            except Exception as e:
                logger.error(f"图片处理失败: {e}")
                return {"success": False, "message": "图片处理失败"}
            
            # 更新数据库
            with self.db_manager.get_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    # 删除已上传的文件
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    return {"success": False, "message": "用户不存在"}
                
                # 删除旧头像文件
                if user.avatar_url:
                    old_file = user.avatar_url.replace("/uploads/avatars/", "")
                    old_path = os.path.join(self.upload_dir, old_file)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                # 更新头像URL
                user.avatar_url = f"/uploads/avatars/{unique_filename}"
                user.updated_at = datetime.utcnow()
                db.commit()
            
            # 记录审计日志
            await AuditLog.log_action(
                user_id=user_id,
                action="upload_avatar",
                resource_type="user_profile",
                resource_id=user_id,
                details={"filename": unique_filename}
            )
            
            logger.info(f"用户 {user_id} 上传头像: {unique_filename}")
            
            return {
                "success": True,
                "message": "头像上传成功",
                "avatar_url": f"/uploads/avatars/{unique_filename}"
            }
            
        except Exception as e:
            logger.error(f"上传头像失败: {e}")
            return {"success": False, "message": "上传失败"}
    
    async def delete_avatar(self, user_id: str) -> bool:
        """删除头像"""
        try:
            with self.db_manager.get_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                # 删除头像文件
                if user.avatar_url:
                    filename = user.avatar_url.replace("/uploads/avatars/", "")
                    file_path = os.path.join(self.upload_dir, filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                # 清除头像URL
                user.avatar_url = None
                user.updated_at = datetime.utcnow()
                db.commit()
                
                # 记录审计日志
                await AuditLog.log_action(
                    user_id=user_id,
                    action="delete_avatar",
                    resource_type="user_profile",
                    resource_id=user_id
                )
                
                logger.info(f"用户 {user_id} 删除头像")
                return True
                
        except Exception as e:
            logger.error(f"删除头像失败: {e}")
            return False
    
    # 偏好设置管理
    async def update_preferences(
        self,
        user_id: str,
        language: Optional[str] = None,
        timezone: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新偏好设置"""
        try:
            with self.db_manager.get_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                changes = []
                
                if language is not None:
                    user.language = language
                    changes.append("language")
                
                if timezone is not None:
                    user.timezone = timezone
                    changes.append("timezone")
                
                if preferences is not None:
                    # 合并偏好设置
                    current_prefs = user.preferences or {}
                    current_prefs.update(preferences)
                    user.preferences = current_prefs
                    changes.append("preferences")
                
                if changes:
                    user.updated_at = datetime.utcnow()
                    db.commit()
                    
                    # 记录审计日志
                    await AuditLog.log_action(
                        user_id=user_id,
                        action="update_preferences",
                        resource_type="user_profile",
                        resource_id=user_id,
                        details={"updated_fields": changes}
                    )
                    
                    logger.info(f"用户 {user_id} 更新偏好设置: {changes}")
                
                return True
                
        except Exception as e:
            logger.error(f"更新偏好设置失败: {e}")
            return False
    
    async def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取偏好设置"""
        with self.db_manager.get_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            return {
                "language": user.language,
                "timezone": user.timezone,
                "preferences": user.preferences or {}
            }
    
    # 隐私设置
    async def update_privacy_settings(
        self,
        user_id: str,
        privacy_settings: Dict[str, Any]
    ) -> bool:
        """更新隐私设置"""
        try:
            with self.db_manager.get_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                # 更新隐私设置
                current_prefs = user.preferences or {}
                current_prefs["privacy"] = privacy_settings
                user.preferences = current_prefs
                user.updated_at = datetime.utcnow()
                db.commit()
                
                # 记录审计日志
                await AuditLog.log_action(
                    user_id=user_id,
                    action="update_privacy_settings",
                    resource_type="user_profile",
                    resource_id=user_id,
                    details={"privacy_settings": list(privacy_settings.keys())}
                )
                
                logger.info(f"用户 {user_id} 更新隐私设置")
                return True
                
        except Exception as e:
            logger.error(f"更新隐私设置失败: {e}")
            return False
    
    # 账户安全
    async def get_security_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取账户安全信息"""
        with self.db_manager.get_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            return {
                "two_factor_enabled": user.two_factor_enabled,
                "is_email_verified": user.is_email_verified,
                "is_phone_verified": user.is_phone_verified,
                "last_password_change": user.password_changed_at,
                "last_login": user.last_login_at,
                "login_count": user.login_count,
                "failed_login_attempts": user.failed_login_attempts,
                "account_locked_until": user.account_locked_until
            }
    
    async def enable_two_factor(self, user_id: str) -> Dict[str, Any]:
        """启用双因素认证"""
        try:
            import pyotp
            import qrcode
            from io import BytesIO
            
            with self.db_manager.get_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return {"success": False, "message": "用户不存在"}
                
                if user.two_factor_enabled:
                    return {"success": False, "message": "双因素认证已启用"}
                
                # 生成密钥
                secret = pyotp.random_base32()
                
                # 生成QR码
                totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                    name=user.email,
                    issuer_name="抖音直播管理系统"
                )
                
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(totp_uri)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                qr_code_data = base64.b64encode(buffer.getvalue()).decode()
                
                # 暂存密钥（等待验证）
                current_prefs = user.preferences or {}
                current_prefs["temp_2fa_secret"] = secret
                user.preferences = current_prefs
                user.updated_at = datetime.utcnow()
                db.commit()
                
                return {
                    "success": True,
                    "secret": secret,
                    "qr_code": f"data:image/png;base64,{qr_code_data}",
                    "message": "请使用认证器应用扫描二维码，然后输入验证码确认"
                }
                
        except Exception as e:
            logger.error(f"启用双因素认证失败: {e}")
            return {"success": False, "message": "启用失败"}
    
    async def verify_two_factor_setup(
        self,
        user_id: str,
        verification_code: str
    ) -> Dict[str, Any]:
        """验证双因素认证设置"""
        try:
            import pyotp
            
            with self.db_manager.get_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return {"success": False, "message": "用户不存在"}
                
                # 获取临时密钥
                temp_secret = user.preferences.get("temp_2fa_secret")
                if not temp_secret:
                    return {"success": False, "message": "未找到待验证的密钥"}
                
                # 验证代码
                totp = pyotp.TOTP(temp_secret)
                if not totp.verify(verification_code):
                    return {"success": False, "message": "验证码错误"}
                
                # 启用双因素认证
                user.two_factor_enabled = True
                user.two_factor_secret = encryptor.encrypt(temp_secret)
                
                # 清除临时密钥
                current_prefs = user.preferences or {}
                current_prefs.pop("temp_2fa_secret", None)
                user.preferences = current_prefs
                
                user.updated_at = datetime.utcnow()
                db.commit()
                
                # 记录审计日志
                await AuditLog.log_action(
                    user_id=user_id,
                    action="enable_two_factor",
                    resource_type="user_security",
                    resource_id=user_id
                )
                
                logger.info(f"用户 {user_id} 启用双因素认证")
                
                return {"success": True, "message": "双因素认证启用成功"}
                
        except Exception as e:
            logger.error(f"验证双因素认证设置失败: {e}")
            return {"success": False, "message": "验证失败"}
    
    async def disable_two_factor(
        self,
        user_id: str,
        verification_code: str
    ) -> Dict[str, Any]:
        """禁用双因素认证"""
        try:
            import pyotp
            
            with self.db_manager.get_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return {"success": False, "message": "用户不存在"}
                
                if not user.two_factor_enabled:
                    return {"success": False, "message": "双因素认证未启用"}
                
                # 验证代码
                secret = encryptor.decrypt(user.two_factor_secret)
                totp = pyotp.TOTP(secret)
                if not totp.verify(verification_code):
                    return {"success": False, "message": "验证码错误"}
                
                # 禁用双因素认证
                user.two_factor_enabled = False
                user.two_factor_secret = None
                user.updated_at = datetime.utcnow()
                db.commit()
                
                # 记录审计日志
                await AuditLog.log_action(
                    user_id=user_id,
                    action="disable_two_factor",
                    resource_type="user_security",
                    resource_id=user_id
                )
                
                logger.info(f"用户 {user_id} 禁用双因素认证")
                
                return {"success": True, "message": "双因素认证禁用成功"}
                
        except Exception as e:
            logger.error(f"禁用双因素认证失败: {e}")
            return {"success": False, "message": "禁用失败"}


# 全局个人资料服务实例
profile_service = ProfileService()