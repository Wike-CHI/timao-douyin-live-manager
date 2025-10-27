# -*- coding: utf-8 -*-
"""
权限管理服务
实现基于角色的权限控制系统(RBAC)
"""

from typing import List, Optional, Dict, Any, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
import json
import logging

from server.app.models import (
    User, UserRole, Permission, RolePermission, AuditLog
)
from server.app.database import DatabaseManager

logger = logging.getLogger(__name__)


class PermissionService:
    """权限管理服务"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    # 权限管理
    async def create_permission(
        self,
        name: str,
        description: str,
        category: str,
        module: str,
        level: int = 1,
        conditions: Optional[Dict[str, Any]] = None
    ) -> Permission:
        """创建权限"""
        with self.db_manager.get_session() as db:
            # 检查权限是否已存在
            existing = db.query(Permission).filter(
                Permission.name == name,
                Permission.module == module
            ).first()
            
            if existing:
                raise ValueError(f"权限 {name} 在模块 {module} 中已存在")
            
            permission = Permission(
                name=name,
                description=description,
                category=category,
                module=module,
                level=level,
                conditions=conditions or {}
            )
            
            db.add(permission)
            db.commit()
            db.refresh(permission)
            
            logger.info(f"创建权限: {name} (模块: {module})")
            return permission
    
    async def get_permissions(
        self,
        category: Optional[str] = None,
        module: Optional[str] = None,
        level: Optional[int] = None
    ) -> List[Permission]:
        """获取权限列表"""
        with self.db_manager.get_session() as db:
            query = db.query(Permission)
            
            if category:
                query = query.filter(Permission.category == category)
            if module:
                query = query.filter(Permission.module == module)
            if level is not None:
                query = query.filter(Permission.level <= level)
            
            return query.order_by(Permission.category, Permission.module, Permission.name).all()
    
    async def update_permission(
        self,
        permission_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        level: Optional[int] = None,
        conditions: Optional[Dict[str, Any]] = None
    ) -> Permission:
        """更新权限"""
        with self.db_manager.get_session() as db:
            permission = db.query(Permission).filter(Permission.id == permission_id).first()
            if not permission:
                raise ValueError("权限不存在")
            
            if name:
                permission.name = name
            if description:
                permission.description = description
            if category:
                permission.category = category
            if level is not None:
                permission.level = level
            if conditions is not None:
                permission.conditions = conditions
            
            permission.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(permission)
            
            logger.info(f"更新权限: {permission.name}")
            return permission
    
    async def delete_permission(self, permission_id: str) -> bool:
        """删除权限"""
        with self.db_manager.get_session() as db:
            permission = db.query(Permission).filter(Permission.id == permission_id).first()
            if not permission:
                return False
            
            # 删除相关的角色权限关联
            db.query(RolePermission).filter(
                RolePermission.permission_id == permission_id
            ).delete()
            
            db.delete(permission)
            db.commit()
            
            logger.info(f"删除权限: {permission.name}")
            return True
    
    # 角色权限管理
    async def assign_permission_to_role(
        self,
        role: str,
        permission_id: str,
        granted: bool = True,
        conditions: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None
    ) -> RolePermission:
        """为角色分配权限"""
        with self.db_manager.get_session() as db:
            # 检查权限是否存在
            permission = db.query(Permission).filter(Permission.id == permission_id).first()
            if not permission:
                raise ValueError("权限不存在")
            
            # 检查是否已存在
            existing = db.query(RolePermission).filter(
                RolePermission.role == role,
                RolePermission.permission_id == permission_id
            ).first()
            
            if existing:
                # 更新现有记录
                existing.granted = granted
                existing.conditions = conditions or {}
                existing.expires_at = expires_at
                existing.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing)
                return existing
            
            # 创建新记录
            role_permission = RolePermission(
                role=role,
                permission_id=permission_id,
                granted=granted,
                conditions=conditions or {},
                expires_at=expires_at
            )
            
            db.add(role_permission)
            db.commit()
            db.refresh(role_permission)
            
            logger.info(f"为角色 {role} 分配权限: {permission.name}")
            return role_permission
    
    async def revoke_permission_from_role(
        self,
        role: str,
        permission_id: str
    ) -> bool:
        """撤销角色权限"""
        with self.db_manager.get_session() as db:
            role_permission = db.query(RolePermission).filter(
                RolePermission.role == role,
                RolePermission.permission_id == permission_id
            ).first()
            
            if not role_permission:
                return False
            
            db.delete(role_permission)
            db.commit()
            
            logger.info(f"撤销角色 {role} 的权限")
            return True
    
    async def get_role_permissions(
        self,
        role: str,
        include_expired: bool = False
    ) -> List[RolePermission]:
        """获取角色权限"""
        with self.db_manager.get_session() as db:
            query = db.query(RolePermission).filter(
                RolePermission.role == role,
                RolePermission.granted == True
            )
            
            if not include_expired:
                query = query.filter(
                    or_(
                        RolePermission.expires_at.is_(None),
                        RolePermission.expires_at > datetime.utcnow()
                    )
                )
            
            return query.all()
    
    # 用户权限检查
    async def check_user_permission(
        self,
        user_id: str,
        permission_name: str,
        module: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """检查用户权限"""
        with self.db_manager.get_session() as db:
            # 获取用户角色
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # 超级管理员拥有所有权限
            if user.role == "super_admin":
                return True
            
            # 获取权限
            permission = db.query(Permission).filter(
                Permission.name == permission_name,
                Permission.module == module
            ).first()
            
            if not permission:
                return False
            
            # 检查角色权限
            role_permission = db.query(RolePermission).filter(
                RolePermission.role == user.role,
                RolePermission.permission_id == permission.id,
                RolePermission.granted == True,
                or_(
                    RolePermission.expires_at.is_(None),
                    RolePermission.expires_at > datetime.utcnow()
                )
            ).first()
            
            if not role_permission:
                return False
            
            # 检查条件
            if role_permission.conditions or permission.conditions:
                return self._check_conditions(
                    role_permission.conditions,
                    permission.conditions,
                    context or {}
                )
            
            return True
    
    async def get_user_permissions(
        self,
        user_id: str,
        module: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取用户所有权限"""
        with self.db_manager.get_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return []
            
            # 超级管理员拥有所有权限
            if user.role == "super_admin":
                query = db.query(Permission)
                if module:
                    query = query.filter(Permission.module == module)
                permissions = query.all()
                
                return [
                    {
                        "id": p.id,
                        "name": p.name,
                        "description": p.description,
                        "category": p.category,
                        "module": p.module,
                        "level": p.level,
                        "granted": True,
                        "conditions": {},
                        "expires_at": None
                    }
                    for p in permissions
                ]
            
            # 获取角色权限
            query = db.query(RolePermission, Permission).join(
                Permission, RolePermission.permission_id == Permission.id
            ).filter(
                RolePermission.role == user.role,
                RolePermission.granted == True,
                or_(
                    RolePermission.expires_at.is_(None),
                    RolePermission.expires_at > datetime.utcnow()
                )
            )
            
            if module:
                query = query.filter(Permission.module == module)
            
            results = query.all()
            
            return [
                {
                    "id": permission.id,
                    "name": permission.name,
                    "description": permission.description,
                    "category": permission.category,
                    "module": permission.module,
                    "level": permission.level,
                    "granted": role_permission.granted,
                    "conditions": role_permission.conditions,
                    "expires_at": role_permission.expires_at
                }
                for role_permission, permission in results
            ]
    
    def _check_conditions(
        self,
        role_conditions: Dict[str, Any],
        permission_conditions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """检查权限条件"""
        # 合并条件
        conditions = {**permission_conditions, **role_conditions}
        
        for key, expected_value in conditions.items():
            context_value = context.get(key)
            
            if isinstance(expected_value, dict):
                # 支持复杂条件
                operator = expected_value.get("operator", "eq")
                value = expected_value.get("value")
                
                if operator == "eq" and context_value != value:
                    return False
                elif operator == "ne" and context_value == value:
                    return False
                elif operator == "in" and context_value not in value:
                    return False
                elif operator == "not_in" and context_value in value:
                    return False
                elif operator == "gt" and context_value <= value:
                    return False
                elif operator == "gte" and context_value < value:
                    return False
                elif operator == "lt" and context_value >= value:
                    return False
                elif operator == "lte" and context_value > value:
                    return False
            else:
                # 简单相等条件
                if context_value != expected_value:
                    return False
        
        return True
    
    # 权限统计
    async def get_permission_statistics(self) -> Dict[str, Any]:
        """获取权限统计信息"""
        with self.db_manager.get_session() as db:
            total_permissions = db.query(Permission).count()
            
            # 按类别统计
            category_stats = db.query(
                Permission.category,
                db.func.count(Permission.id).label('count')
            ).group_by(Permission.category).all()
            
            # 按模块统计
            module_stats = db.query(
                Permission.module,
                db.func.count(Permission.id).label('count')
            ).group_by(Permission.module).all()
            
            # 角色权限统计
            role_stats = db.query(
                RolePermission.role,
                db.func.count(RolePermission.id).label('count')
            ).filter(
                RolePermission.granted == True
            ).group_by(RolePermission.role).all()
            
            return {
                "total_permissions": total_permissions,
                "category_stats": [
                    {"category": cat, "count": count}
                    for cat, count in category_stats
                ],
                "module_stats": [
                    {"module": mod, "count": count}
                    for mod, count in module_stats
                ],
                "role_stats": [
                    {"role": role, "permissions_count": count}
                    for role, count in role_stats
                ]
            }
    
    # 权限模板
    async def create_role_template(
        self,
        role: str,
        permissions: List[str]
    ) -> bool:
        """创建角色权限模板"""
        try:
            with self.db_manager.get_session() as db:
                # 清除现有权限
                db.query(RolePermission).filter(
                    RolePermission.role == role
                ).delete()
                
                # 添加新权限
                for permission_id in permissions:
                    permission = db.query(Permission).filter(
                        Permission.id == permission_id
                    ).first()
                    
                    if permission:
                        role_permission = RolePermission(
                            role=role,
                            permission_id=permission_id,
                            granted=True
                        )
                        db.add(role_permission)
                
                db.commit()
                logger.info(f"创建角色模板: {role}")
                return True
                
        except Exception as e:
            logger.error(f"创建角色模板失败: {e}")
            return False
    
    async def apply_role_template(
        self,
        source_role: str,
        target_role: str
    ) -> bool:
        """应用角色权限模板"""
        try:
            with self.db_manager.get_session() as db:
                # 获取源角色权限
                source_permissions = db.query(RolePermission).filter(
                    RolePermission.role == source_role,
                    RolePermission.granted == True
                ).all()
                
                # 清除目标角色权限
                db.query(RolePermission).filter(
                    RolePermission.role == target_role
                ).delete()
                
                # 复制权限
                for perm in source_permissions:
                    new_permission = RolePermission(
                        role=target_role,
                        permission_id=perm.permission_id,
                        granted=perm.granted,
                        conditions=perm.conditions,
                        expires_at=perm.expires_at
                    )
                    db.add(new_permission)
                
                db.commit()
                logger.info(f"应用角色模板: {source_role} -> {target_role}")
                return True
                
        except Exception as e:
            logger.error(f"应用角色模板失败: {e}")
            return False


# 全局权限服务实例
permission_service = PermissionService()