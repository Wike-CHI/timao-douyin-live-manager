# -*- coding: utf-8 -*-
"""
团队协作相关数据库模型
"""

from datetime import datetime
from typing import Optional
import enum
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index, Boolean, Enum
from sqlalchemy.orm import relationship

from .base import BaseModel


class TeamRoleEnum(enum.Enum):
    """团队角色枚举"""
    OWNER = "owner"          # 所有者
    MANAGER = "manager"      # 管理员
    STREAMER = "streamer"    # 主播
    ASSISTANT = "assistant"  # 助理
    VIEWER = "viewer"        # 观察者（只读）


class Team(BaseModel):
    """团队/工作室模型"""
    
    __tablename__ = "teams"
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="团队名称")
    slug = Column(String(100), unique=True, nullable=False, comment="团队标识")
    description = Column(Text, nullable=True, comment="团队描述")
    avatar_url = Column(String(500), nullable=True, comment="团队头像URL")
    
    # 所有者
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment="所有者ID")
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    member_limit = Column(Integer, default=10, nullable=False, comment="成员上限")
    
    # 团队设置（JSON格式）
    settings = Column(Text, nullable=True, comment="团队设置JSON")
    # 示例: {
    #   "allow_member_invite": true,
    #   "require_approval": false,
    #   "data_sharing": true
    # }
    
    # 关联关系
    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_team_owner_id', 'owner_id'),
        Index('idx_team_slug', 'slug'),
        Index('idx_team_active', 'is_active'),
    )
    
    def get_settings(self) -> dict:
        """获取团队设置"""
        import json
        if not self.settings:
            return {
                "allow_member_invite": True,
                "require_approval": False,
                "data_sharing": True
            }
        try:
            return json.loads(self.settings)
        except:
            return {}
    
    def set_settings(self, settings: dict) -> None:
        """设置团队配置"""
        import json
        self.settings = json.dumps(settings, ensure_ascii=False)
    
    def get_member_count(self) -> int:
        """获取成员数量"""
        return len(self.members)
    
    def can_add_member(self) -> bool:
        """是否可以添加成员"""
        return self.get_member_count() < self.member_limit


class TeamMember(BaseModel):
    """团队成员模型"""
    
    __tablename__ = "team_members"
    
    # 基本信息
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False, comment="团队ID")
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment="用户ID")
    role = Column(Enum(TeamRoleEnum), default=TeamRoleEnum.VIEWER, nullable=False, comment="团队角色")
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    invited_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment="邀请人ID")
    invited_at = Column(DateTime, default=datetime.utcnow, comment="邀请时间")
    joined_at = Column(DateTime, default=datetime.utcnow, comment="加入时间")
    
    # 权限配置（JSON格式）
    permissions = Column(Text, nullable=True, comment="权限配置JSON")
    # 示例: {
    #   "can_view_analytics": true,
    #   "can_manage_live": false,
    #   "can_use_ai": true
    # }
    
    # 备注
    notes = Column(Text, nullable=True, comment="备注")
    
    # 关联关系
    team = relationship("Team", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="team_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])
    
    # 索引
    __table_args__ = (
        Index('idx_team_member_team_id', 'team_id'),
        Index('idx_team_member_user_id', 'user_id'),
        Index('idx_team_member_role', 'role'),
        Index('idx_team_member_active', 'is_active'),
    )
    
    def get_permissions(self) -> dict:
        """获取权限配置"""
        import json
        
        # 根据角色返回默认权限
        default_permissions = {
            TeamRoleEnum.OWNER: {
                "can_view_analytics": True,
                "can_manage_live": True,
                "can_use_ai": True,
                "can_manage_team": True,
                "can_invite_member": True
            },
            TeamRoleEnum.MANAGER: {
                "can_view_analytics": True,
                "can_manage_live": True,
                "can_use_ai": True,
                "can_manage_team": False,
                "can_invite_member": True
            },
            TeamRoleEnum.STREAMER: {
                "can_view_analytics": True,
                "can_manage_live": True,
                "can_use_ai": True,
                "can_manage_team": False,
                "can_invite_member": False
            },
            TeamRoleEnum.ASSISTANT: {
                "can_view_analytics": True,
                "can_manage_live": False,
                "can_use_ai": True,
                "can_manage_team": False,
                "can_invite_member": False
            },
            TeamRoleEnum.VIEWER: {
                "can_view_analytics": True,
                "can_manage_live": False,
                "can_use_ai": False,
                "can_manage_team": False,
                "can_invite_member": False
            }
        }
        
        if not self.permissions:
            return default_permissions.get(self.role, {})
        
        try:
            custom_perms = json.loads(self.permissions)
            # 合并默认权限和自定义权限
            default = default_permissions.get(self.role, {})
            default.update(custom_perms)
            return default
        except:
            return default_permissions.get(self.role, {})
    
    def set_permissions(self, permissions: dict) -> None:
        """设置权限配置"""
        import json
        self.permissions = json.dumps(permissions, ensure_ascii=False)
    
    def has_permission(self, permission: str) -> bool:
        """检查是否有指定权限"""
        perms = self.get_permissions()
        return perms.get(permission, False)
