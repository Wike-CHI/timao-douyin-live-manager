# -*- coding: utf-8 -*-
"""
权限和角色相关数据库模型
"""

from typing import Optional
from sqlalchemy import Column, String, Boolean, Text, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import BaseModel


class Permission(BaseModel):
    """权限模型"""
    
    __tablename__ = "permissions"
    
    # 基本信息
    name = Column(String(100), unique=True, nullable=False, comment="权限名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, nullable=True, comment="权限描述")
    
    # 权限分组
    category = Column(String(50), nullable=False, comment="权限分类")
    module = Column(String(50), nullable=False, comment="所属模块")
    
    # 权限级别
    level = Column(Integer, default=1, nullable=False, comment="权限级别")
    
    # 状态
    is_system = Column(Boolean, default=False, nullable=False, comment="是否系统权限")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    
    # 关联关系
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_permission_name', 'name'),
        Index('idx_permission_category', 'category'),
        Index('idx_permission_module', 'module'),
        Index('idx_permission_active', 'is_active'),
    )


class RolePermission(BaseModel):
    """角色权限关联模型"""
    
    __tablename__ = "role_permissions"
    
    role_id = Column(Integer, ForeignKey('user_roles.id'), nullable=False, comment="角色ID")
    permission_id = Column(Integer, ForeignKey('permissions.id'), nullable=False, comment="权限ID")
    
    # 权限配置
    granted = Column(Boolean, default=True, nullable=False, comment="是否授予")
    conditions = Column(Text, nullable=True, comment="权限条件(JSON)")
    
    # 关联关系
    role = relationship("UserRole", back_populates="permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    
    # 索引和约束
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uk_role_permission'),
        Index('idx_role_permission_role_id', 'role_id'),
        Index('idx_role_permission_permission_id', 'permission_id'),
    )


class AuditLog(BaseModel):
    """审计日志模型"""
    
    __tablename__ = "audit_logs"
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment="用户ID")
    
    # 操作信息
    action = Column(String(100), nullable=False, comment="操作类型")
    resource_type = Column(String(50), nullable=False, comment="资源类型")
    resource_id = Column(String(100), nullable=True, comment="资源ID")
    
    # 详细信息
    description = Column(Text, nullable=True, comment="操作描述")
    old_values = Column(Text, nullable=True, comment="旧值(JSON)")
    new_values = Column(Text, nullable=True, comment="新值(JSON)")
    
    # 请求信息
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    request_id = Column(String(100), nullable=True, comment="请求ID")
    
    # 结果信息
    success = Column(Boolean, default=True, nullable=False, comment="是否成功")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 关联关系
    user = relationship("User", back_populates="audit_logs")
    
    # 索引
    __table_args__ = (
        Index('idx_audit_user_id', 'user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_resource_type', 'resource_type'),
        Index('idx_audit_created_at', 'created_at'),
        Index('idx_audit_success', 'success'),
    )
    
    @classmethod
    def log_action(cls, user_id: Optional[int], action: str, resource_type: str, 
                   resource_id: Optional[str] = None, description: Optional[str] = None,
                   old_values: Optional[dict] = None, new_values: Optional[dict] = None,
                   ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                   request_id: Optional[str] = None, success: bool = True,
                   error_message: Optional[str] = None) -> 'AuditLog':
        """记录操作日志"""
        import json
        
        log = cls(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            success=success,
            error_message=error_message
        )
        
        if old_values:
            log.old_values = json.dumps(old_values, ensure_ascii=False, default=str)
        if new_values:
            log.new_values = json.dumps(new_values, ensure_ascii=False, default=str)
        
        return log