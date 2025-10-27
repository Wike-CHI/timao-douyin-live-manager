10# -*- coding: utf-8 -*-
"""
权限管理API路由
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

from server.app.core.dependencies import (
    get_current_user,
    require_admin_role,
    require_permissions,
    get_request_info
)
from server.app.models import User, AuditLog
from server.app.services.permission_service import permission_service

router = APIRouter(prefix="/permission", tags=["权限管理"])


# Pydantic 模型
class PermissionCreate(BaseModel):
    """创建权限请求"""
    name: str = Field(..., description="权限名称")
    description: str = Field(..., description="权限描述")
    category: str = Field(..., description="权限类别")
    module: str = Field(..., description="所属模块")
    level: int = Field(1, description="权限级别")
    conditions: Optional[Dict[str, Any]] = Field(None, description="权限条件")


class PermissionUpdate(BaseModel):
    """更新权限请求"""
    name: Optional[str] = Field(None, description="权限名称")
    description: Optional[str] = Field(None, description="权限描述")
    category: Optional[str] = Field(None, description="权限类别")
    level: Optional[int] = Field(None, description="权限级别")
    conditions: Optional[Dict[str, Any]] = Field(None, description="权限条件")


class PermissionResponse(BaseModel):
    """权限响应"""
    id: str
    name: str
    description: str
    category: str
    module: str
    level: int
    conditions: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class RolePermissionAssign(BaseModel):
    """角色权限分配请求"""
    role: str = Field(..., description="角色名称")
    permission_id: str = Field(..., description="权限ID")
    granted: bool = Field(True, description="是否授予")
    conditions: Optional[Dict[str, Any]] = Field(None, description="权限条件")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class RolePermissionResponse(BaseModel):
    """角色权限响应"""
    id: str
    role: str
    permission_id: str
    granted: bool
    conditions: Dict[str, Any]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class UserPermissionResponse(BaseModel):
    """用户权限响应"""
    id: str
    name: str
    description: str
    category: str
    module: str
    level: int
    granted: bool
    conditions: Dict[str, Any]
    expires_at: Optional[datetime]


class PermissionCheckRequest(BaseModel):
    """权限检查请求"""
    permission_name: str = Field(..., description="权限名称")
    module: str = Field(..., description="模块名称")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class RoleTemplateRequest(BaseModel):
    """角色模板请求"""
    permissions: List[str] = Field(..., description="权限ID列表")


# 权限管理路由
@router.post("/permissions", response_model=PermissionResponse)
async def create_permission(
    permission_data: PermissionCreate,
    current_user: User = Depends(require_admin_role),
    request_info: dict = Depends(get_request_info)
):
    """创建权限"""
    try:
        permission = await permission_service.create_permission(
            name=permission_data.name,
            description=permission_data.description,
            category=permission_data.category,
            module=permission_data.module,
            level=permission_data.level,
            conditions=permission_data.conditions
        )
        
        # 记录审计日志
        await AuditLog.log_action(
            user_id=current_user.id,
            action="create_permission",
            resource_type="permission",
            resource_id=permission.id,
            details={"permission_name": permission.name},
            ip_address=request_info.get("ip"),
            user_agent=request_info.get("user_agent")
        )
        
        return PermissionResponse(
            id=permission.id,
            name=permission.name,
            description=permission.description,
            category=permission.category,
            module=permission.module,
            level=permission.level,
            conditions=permission.conditions,
            created_at=permission.created_at,
            updated_at=permission.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建权限失败")


@router.get("/permissions", response_model=List[PermissionResponse])
async def get_permissions(
    category: Optional[str] = Query(None, description="权限类别"),
    module: Optional[str] = Query(None, description="模块名称"),
    level: Optional[int] = Query(None, description="权限级别"),
    current_user: User = Depends(require_admin_role)
):
    """获取权限列表"""
    permissions = await permission_service.get_permissions(
        category=category,
        module=module,
        level=level
    )
    
    return [
        PermissionResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            category=p.category,
            module=p.module,
            level=p.level,
            conditions=p.conditions,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in permissions
    ]


@router.put("/permissions/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: str,
    permission_data: PermissionUpdate,
    current_user: User = Depends(require_admin_role),
    request_info: dict = Depends(get_request_info)
):
    """更新权限"""
    try:
        permission = await permission_service.update_permission(
            permission_id=permission_id,
            name=permission_data.name,
            description=permission_data.description,
            category=permission_data.category,
            level=permission_data.level,
            conditions=permission_data.conditions
        )
        
        # 记录审计日志
        await AuditLog.log_action(
            user_id=current_user.id,
            action="update_permission",
            resource_type="permission",
            resource_id=permission.id,
            details={"permission_name": permission.name},
            ip_address=request_info.get("ip"),
            user_agent=request_info.get("user_agent")
        )
        
        return PermissionResponse(
            id=permission.id,
            name=permission.name,
            description=permission.description,
            category=permission.category,
            module=permission.module,
            level=permission.level,
            conditions=permission.conditions,
            created_at=permission.created_at,
            updated_at=permission.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新权限失败")


@router.delete("/permissions/{permission_id}")
async def delete_permission(
    permission_id: str,
    current_user: User = Depends(require_admin_role),
    request_info: dict = Depends(get_request_info)
):
    """删除权限"""
    success = await permission_service.delete_permission(permission_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="权限不存在")
    
    # 记录审计日志
    await AuditLog.log_action(
        user_id=current_user.id,
        action="delete_permission",
        resource_type="permission",
        resource_id=permission_id,
        ip_address=request_info.get("ip"),
        user_agent=request_info.get("user_agent")
    )
    
    return {"message": "权限删除成功"}


# 角色权限管理路由
@router.post("/role-permissions", response_model=RolePermissionResponse)
async def assign_permission_to_role(
    assignment: RolePermissionAssign,
    current_user: User = Depends(require_admin_role),
    request_info: dict = Depends(get_request_info)
):
    """为角色分配权限"""
    try:
        role_permission = await permission_service.assign_permission_to_role(
            role=assignment.role,
            permission_id=assignment.permission_id,
            granted=assignment.granted,
            conditions=assignment.conditions,
            expires_at=assignment.expires_at
        )
        
        # 记录审计日志
        await AuditLog.log_action(
            user_id=current_user.id,
            action="assign_role_permission",
            resource_type="role_permission",
            resource_id=role_permission.id,
            details={
                "role": assignment.role,
                "permission_id": assignment.permission_id,
                "granted": assignment.granted
            },
            ip_address=request_info.get("ip"),
            user_agent=request_info.get("user_agent")
        )
        
        return RolePermissionResponse(
            id=role_permission.id,
            role=role_permission.role,
            permission_id=role_permission.permission_id,
            granted=role_permission.granted,
            conditions=role_permission.conditions,
            expires_at=role_permission.expires_at,
            created_at=role_permission.created_at,
            updated_at=role_permission.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="分配权限失败")


@router.delete("/role-permissions/{role}/{permission_id}")
async def revoke_permission_from_role(
    role: str,
    permission_id: str,
    current_user: User = Depends(require_admin_role),
    request_info: dict = Depends(get_request_info)
):
    """撤销角色权限"""
    success = await permission_service.revoke_permission_from_role(
        role=role,
        permission_id=permission_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="角色权限不存在")
    
    # 记录审计日志
    await AuditLog.log_action(
        user_id=current_user.id,
        action="revoke_role_permission",
        resource_type="role_permission",
        details={
            "role": role,
            "permission_id": permission_id
        },
        ip_address=request_info.get("ip"),
        user_agent=request_info.get("user_agent")
    )
    
    return {"message": "权限撤销成功"}


@router.get("/roles/{role}/permissions", response_model=List[RolePermissionResponse])
async def get_role_permissions(
    role: str,
    include_expired: bool = Query(False, description="包含过期权限"),
    current_user: User = Depends(require_admin_role)
):
    """获取角色权限"""
    permissions = await permission_service.get_role_permissions(
        role=role,
        include_expired=include_expired
    )
    
    return [
        RolePermissionResponse(
            id=p.id,
            role=p.role,
            permission_id=p.permission_id,
            granted=p.granted,
            conditions=p.conditions,
            expires_at=p.expires_at,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in permissions
    ]


# 用户权限查询路由
@router.post("/check")
async def check_user_permission(
    check_request: PermissionCheckRequest,
    current_user: User = Depends(get_current_user)
):
    """检查用户权限"""
    has_permission = await permission_service.check_user_permission(
        user_id=current_user.id,
        permission_name=check_request.permission_name,
        module=check_request.module,
        context=check_request.context
    )
    
    return {"has_permission": has_permission}


@router.get("/users/{user_id}/permissions", response_model=List[UserPermissionResponse])
async def get_user_permissions(
    user_id: str,
    module: Optional[str] = Query(None, description="模块名称"),
    current_user: User = Depends(get_current_user)
):
    """获取用户权限"""
    # 只能查看自己的权限，或者管理员可以查看所有用户权限
    if current_user.id != user_id and current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="无权限查看其他用户权限")
    
    permissions = await permission_service.get_user_permissions(
        user_id=user_id,
        module=module
    )
    
    return [
        UserPermissionResponse(
            id=p["id"],
            name=p["name"],
            description=p["description"],
            category=p["category"],
            module=p["module"],
            level=p["level"],
            granted=p["granted"],
            conditions=p["conditions"],
            expires_at=p["expires_at"]
        )
        for p in permissions
    ]


@router.get("/my-permissions", response_model=List[UserPermissionResponse])
async def get_my_permissions(
    module: Optional[str] = Query(None, description="模块名称"),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户权限"""
    permissions = await permission_service.get_user_permissions(
        user_id=current_user.id,
        module=module
    )
    
    return [
        UserPermissionResponse(
            id=p["id"],
            name=p["name"],
            description=p["description"],
            category=p["category"],
            module=p["module"],
            level=p["level"],
            granted=p["granted"],
            conditions=p["conditions"],
            expires_at=p["expires_at"]
        )
        for p in permissions
    ]


# 权限统计路由
@router.get("/statistics")
async def get_permission_statistics(
    current_user: User = Depends(require_admin_role)
):
    """获取权限统计信息"""
    stats = await permission_service.get_permission_statistics()
    return stats


# 角色模板管理路由
@router.post("/roles/{role}/template")
async def create_role_template(
    role: str,
    template_request: RoleTemplateRequest,
    current_user: User = Depends(require_admin_role),
    request_info: dict = Depends(get_request_info)
):
    """创建角色权限模板"""
    success = await permission_service.create_role_template(
        role=role,
        permissions=template_request.permissions
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="创建角色模板失败")
    
    # 记录审计日志
    await AuditLog.log_action(
        user_id=current_user.id,
        action="create_role_template",
        resource_type="role",
        resource_id=role,
        details={"permissions_count": len(template_request.permissions)},
        ip_address=request_info.get("ip"),
        user_agent=request_info.get("user_agent")
    )
    
    return {"message": "角色模板创建成功"}


@router.post("/roles/{target_role}/apply-template/{source_role}")
async def apply_role_template(
    target_role: str,
    source_role: str,
    current_user: User = Depends(require_admin_role),
    request_info: dict = Depends(get_request_info)
):
    """应用角色权限模板"""
    success = await permission_service.apply_role_template(
        source_role=source_role,
        target_role=target_role
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="应用角色模板失败")
    
    # 记录审计日志
    await AuditLog.log_action(
        user_id=current_user.id,
        action="apply_role_template",
        resource_type="role",
        resource_id=target_role,
        details={"source_role": source_role},
        ip_address=request_info.get("ip"),
        user_agent=request_info.get("user_agent")
    )
    
    return {"message": "角色模板应用成功"}