# -*- coding: utf-8 -*-
"""
用户相关数据库模型
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
import enum
import hashlib
import secrets

from .base import BaseModel, UUIDMixin, SoftDeleteMixin


class UserRoleEnum(enum.Enum):
    """用户角色枚举"""
    SUPER_ADMIN = "super_admin"  # 超级管理员
    ADMIN = "admin"              # 管理员
    STREAMER = "streamer"        # 主播
    ASSISTANT = "assistant"      # 助理
    USER = "user"               # 普通用户


class UserStatusEnum(enum.Enum):
    """用户状态枚举"""
    ACTIVE = "active"           # 激活
    INACTIVE = "inactive"       # 未激活
    SUSPENDED = "suspended"     # 暂停
    BANNED = "banned"          # 封禁


class User(BaseModel, UUIDMixin, SoftDeleteMixin):
    """用户模型"""
    
    __tablename__ = "users"
    
    # 基本信息
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, comment="邮箱")
    phone = Column(String(20), unique=True, nullable=True, comment="手机号")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    salt = Column(String(32), nullable=False, comment="密码盐值")
    
    # 个人信息
    nickname = Column(String(50), nullable=True, comment="昵称")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")
    bio = Column(Text, nullable=True, comment="个人简介")
    
    # 直播账号绑定
    douyin_user_id = Column(String(100), unique=True, nullable=True, comment="抖音用户ID")
    douyin_nickname = Column(String(100), nullable=True, comment="抖音昵称")
    douyin_avatar = Column(String(500), nullable=True, comment="抖音头像URL")
    douyin_room_id = Column(String(100), nullable=True, comment="抖音直播间ID")
    douyin_cookies = Column(Text, nullable=True, comment="抖音Cookies（加密存储）")
    
    # 主播认证与等级
    streamer_verified = Column(Boolean, default=False, nullable=False, comment="主播认证")
    streamer_level = Column(Integer, default=0, nullable=False, comment="主播等级")
    streamer_followers = Column(Integer, default=0, nullable=False, comment="粉丝数")
    streamer_description = Column(Text, nullable=True, comment="主播简介")
    
    # 直播偏好设置（JSON格式）
    live_settings = Column(Text, nullable=True, comment="直播设置JSON")
    # 示例: {
    #   "auto_transcribe": true,
    #   "ai_assistant_enabled": true,
    #   "ai_model": "qwen-plus",
    #   "hotword_track": true,
    #   "gift_alerts": true,
    #   "comment_filter": ["spam", "ads"]
    # }
    
    # AI 配额管理
    ai_quota_monthly = Column(Integer, default=1000, nullable=False, comment="每月AI配额")
    ai_quota_used = Column(Integer, default=0, nullable=False, comment="已使用配额")
    ai_quota_reset_at = Column(DateTime, nullable=True, comment="配额重置时间")
    ai_unlimited = Column(Boolean, default=False, nullable=False, comment="无限AI配额")
    
    # 状态信息
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.USER, nullable=False, comment="用户角色")
    status = Column(Enum(UserStatusEnum), default=UserStatusEnum.INACTIVE, nullable=False, comment="用户状态")
    
    # 登录信息
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    last_login_ip = Column(String(45), nullable=True, comment="最后登录IP")
    login_count = Column(Integer, default=0, nullable=False, comment="登录次数")
    failed_login_count = Column(Integer, default=0, nullable=False, comment="失败登录次数")
    locked_until = Column(DateTime, nullable=True, comment="锁定到期时间")
    
    # 验证信息
    email_verified = Column(Boolean, default=False, nullable=False, comment="邮箱是否已验证")
    phone_verified = Column(Boolean, default=False, nullable=False, comment="手机号是否已验证")
    email_verify_token = Column(String(100), nullable=True, comment="邮箱验证令牌")
    phone_verify_code = Column(String(10), nullable=True, comment="手机验证码")
    verify_code_expires_at = Column(DateTime, nullable=True, comment="验证码过期时间")
    
    # 密码重置
    reset_token = Column(String(100), nullable=True, comment="密码重置令牌")
    reset_token_expires_at = Column(DateTime, nullable=True, comment="重置令牌过期时间")
    
    # 关联关系
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan")
    payment_subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    live_sessions = relationship("LiveSession", back_populates="user", cascade="all, delete-orphan")
    team_memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_username', 'username'),
        Index('idx_user_phone', 'phone'),
        Index('idx_user_status', 'status'),
        Index('idx_user_role', 'role'),
    )
    
    def set_password(self, password: str) -> None:
        """设置密码"""
        self.salt = secrets.token_hex(16)
        self.password_hash = self._hash_password(password, self.salt)
    
    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return self.password_hash == self._hash_password(password, self.salt)
    
    def _hash_password(self, password: str, salt: str) -> str:
        """密码哈希"""
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
    
    def is_locked(self) -> bool:
        """检查账户是否被锁定"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def lock_account(self, minutes: int = 30) -> None:
        """锁定账户"""
        self.locked_until = datetime.utcnow() + timedelta(minutes=minutes)
    
    def unlock_account(self) -> None:
        """解锁账户"""
        self.locked_until = None
        self.failed_login_count = 0
    
    def generate_reset_token(self) -> str:
        """生成密码重置令牌"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires_at = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token
    
    def generate_email_verify_token(self) -> str:
        """生成邮箱验证令牌"""
        self.email_verify_token = secrets.token_urlsafe(32)
        return self.email_verify_token
    
    def generate_phone_verify_code(self) -> str:
        """生成手机验证码"""
        self.phone_verify_code = str(secrets.randbelow(900000) + 100000)  # 6位数字
        self.verify_code_expires_at = datetime.utcnow() + timedelta(minutes=10)
        return self.phone_verify_code
    
    def verify_email_token(self, token: str) -> bool:
        """验证邮箱令牌"""
        if self.email_verify_token == token:
            self.email_verified = True
            self.email_verify_token = None
            return True
        return False
    
    def verify_phone_code(self, code: str) -> bool:
        """验证手机验证码"""
        if (self.phone_verify_code == code and 
            self.verify_code_expires_at and 
            datetime.utcnow() < self.verify_code_expires_at):
            self.phone_verified = True
            self.phone_verify_code = None
            self.verify_code_expires_at = None
            return True
        return False
    
    def has_permission(self, permission: str) -> bool:
        """检查用户是否有指定权限"""
        # TODO: 实现权限检查逻辑
        if self.role == UserRoleEnum.SUPER_ADMIN:
            return True
        # 这里应该查询用户角色的权限
        return False
    
    def check_ai_quota(self, required: int = 1) -> bool:
        """检查 AI 配额是否充足"""
        if self.ai_unlimited:
            return True
        return self.ai_quota_used + required <= self.ai_quota_monthly
    
    def consume_ai_quota(self, amount: int = 1) -> bool:
        """消耗 AI 配额"""
        if self.ai_unlimited:
            return True
        if not self.check_ai_quota(amount):
            return False
        self.ai_quota_used += amount
        return True
    
    def reset_ai_quota(self) -> None:
        """重置 AI 配额"""
        from datetime import datetime, timedelta
        self.ai_quota_used = 0
        self.ai_quota_reset_at = datetime.utcnow() + timedelta(days=30)
    
    def get_live_settings(self) -> dict:
        """获取直播设置"""
        import json
        if not self.live_settings:
            return {
                "auto_transcribe": True,
                "ai_assistant_enabled": True,
                "ai_model": "qwen-plus",
                "hotword_track": True,
                "gift_alerts": True,
                "comment_filter": []
            }
        try:
            return json.loads(self.live_settings)
        except:
            return {}
    
    def set_live_settings(self, settings: dict) -> None:
        """设置直播配置"""
        import json
        self.live_settings = json.dumps(settings, ensure_ascii=False)
    
    @property
    def is_active(self) -> bool:
        """用户是否激活（兼容性属性）"""
        return self.status == UserStatusEnum.ACTIVE
    
    @property
    def is_verified(self) -> bool:
        """用户是否已验证（兼容性属性）"""
        return self.email_verified
    
    def to_dict(self, exclude: Optional[list] = None) -> dict:
        """转换为字典，排除敏感信息"""
        exclude = exclude or ['password_hash', 'salt', 'reset_token', 'email_verify_token', 'phone_verify_code']
        return super().to_dict(exclude=exclude)


class UserSession(BaseModel):
    """用户会话模型"""
    
    __tablename__ = "user_sessions"
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment="用户ID")
    session_token = Column(String(255), unique=True, nullable=False, comment="会话令牌")
    refresh_token = Column(String(255), unique=True, nullable=True, comment="刷新令牌")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    refresh_expires_at = Column(DateTime, nullable=True, comment="刷新令牌过期时间")
    
    # 会话信息
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    device_info = Column(Text, nullable=True, comment="设备信息")
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False, comment="是否活跃")
    revoked_at = Column(DateTime, nullable=True, comment="撤销时间")
    
    # 关联关系
    user = relationship("User", back_populates="sessions")
    
    # 索引
    __table_args__ = (
        Index('idx_session_token', 'session_token'),
        Index('idx_session_user_id', 'user_id'),
        Index('idx_session_expires_at', 'expires_at'),
    )
    
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.utcnow() > self.expires_at
    
    def is_refresh_expired(self) -> bool:
        """检查刷新令牌是否过期"""
        if self.refresh_expires_at is None:
            return True
        return datetime.utcnow() > self.refresh_expires_at
    
    def revoke(self) -> None:
        """撤销会话"""
        self.is_active = False
        self.revoked_at = datetime.utcnow()
    
    def extend_session(self, hours: int = 24) -> None:
        """延长会话"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        if self.refresh_expires_at:
            self.refresh_expires_at = datetime.utcnow() + timedelta(days=7)


class UserRole(BaseModel):
    """用户角色模型（扩展角色系统用）"""
    
    __tablename__ = "user_roles"
    
    name = Column(String(50), unique=True, nullable=False, comment="角色名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, nullable=True, comment="角色描述")
    is_system = Column(Boolean, default=False, nullable=False, comment="是否系统角色")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    
    # 关联关系
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_role_name', 'name'),
        Index('idx_role_active', 'is_active'),
    )