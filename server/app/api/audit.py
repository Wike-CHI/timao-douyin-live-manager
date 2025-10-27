# -*- coding: utf-8 -*-
"""
审计日志API路由
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, validator
from datetime import datetime, timedelta
import io

from server.app.core.dependencies import require_admin_role, get_current_active_user
from server.app.services.audit_service import audit_service, AuditLevel, AuditCategory
from server.app.models import User

router = APIRouter(prefix="/audit", tags=["审计日志"])


# Pydantic 模型
class AuditLogResponse(BaseModel):
    """审计日志响应"""
    id: str
    user_id: Optional[str]
    username: Optional[str]
    user_email: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    level: str
    category: str
    timestamp: datetime


class AuditLogsResponse(BaseModel):
    """审计日志列表响应"""
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserActivityResponse(BaseModel):
    """用户活动响应"""
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    timestamp: datetime
    level: str
    category: str


class SecurityEventResponse(BaseModel):
    """安全事件响应"""
    id: str
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    timestamp: datetime
    level: str
    category: str


class AuditStatisticsResponse(BaseModel):
    """审计统计响应"""
    total_logs: int
    active_users: int
    level_distribution: Dict[str, int]
    category_distribution: Dict[str, int]
    top_actions: List[Dict[str, Any]]
    daily_activity: List[Dict[str, Any]]
    period: Dict[str, datetime]


class ExportRequest(BaseModel):
    """导出请求"""
    start_time: datetime
    end_time: datetime
    format: str = "json"
    
    @validator('format')
    def validate_format(cls, v):
        if v not in ['json', 'csv']:
            raise ValueError('格式必须是json或csv')
        return v
    
    @validator('end_time')
    def validate_time_range(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('结束时间必须晚于开始时间')
        return v


# API 路由
@router.get("/logs", response_model=AuditLogsResponse)
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="用户ID"),
    action: Optional[str] = Query(None, description="操作"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    resource_id: Optional[str] = Query(None, description="资源ID"),
    level: Optional[AuditLevel] = Query(None, description="审计级别"),
    category: Optional[AuditCategory] = Query(None, description="审计分类"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    ip_address: Optional[str] = Query(None, description="IP地址"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页大小"),
    current_user: User = Depends(require_admin_role)
):
    """获取审计日志（管理员）"""
    result = await audit_service.get_audit_logs(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        level=level,
        category=category,
        start_time=start_time,
        end_time=end_time,
        ip_address=ip_address,
        page=page,
        page_size=page_size
    )
    
    return result


@router.get("/user/{user_id}/activity", response_model=List[UserActivityResponse])
async def get_user_activity(
    user_id: str,
    days: int = Query(30, ge=1, le=365, description="天数"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    current_user: User = Depends(require_admin_role)
):
    """获取用户活动记录（管理员）"""
    activity = await audit_service.get_user_activity(
        user_id=user_id,
        days=days,
        limit=limit
    )
    
    return activity


@router.get("/my-activity", response_model=List[UserActivityResponse])
async def get_my_activity(
    days: int = Query(30, ge=1, le=90, description="天数"),
    limit: int = Query(50, ge=1, le=200, description="限制数量"),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户活动记录"""
    activity = await audit_service.get_user_activity(
        user_id=current_user.id,
        days=days,
        limit=limit
    )
    
    return activity


@router.get("/security-events", response_model=List[SecurityEventResponse])
async def get_security_events(
    hours: int = Query(24, ge=1, le=168, description="小时数"),
    level: Optional[AuditLevel] = Query(None, description="审计级别"),
    current_user: User = Depends(require_admin_role)
):
    """获取安全事件（管理员）"""
    events = await audit_service.get_security_events(
        hours=hours,
        level=level
    )
    
    return events


@router.get("/statistics", response_model=AuditStatisticsResponse)
async def get_audit_statistics(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(require_admin_role)
):
    """获取审计统计信息（管理员）"""
    # 默认统计最近30天
    if not start_time:
        start_time = datetime.utcnow() - timedelta(days=30)
    if not end_time:
        end_time = datetime.utcnow()
    
    stats = await audit_service.get_audit_statistics(
        start_time=start_time,
        end_time=end_time
    )
    
    if not stats:
        raise HTTPException(status_code=500, detail="获取统计信息失败")
    
    return stats


@router.post("/export")
async def export_audit_logs(
    export_request: ExportRequest,
    current_user: User = Depends(require_admin_role)
):
    """导出审计日志（管理员）"""
    # 限制导出时间范围（最多90天）
    time_diff = export_request.end_time - export_request.start_time
    if time_diff.days > 90:
        raise HTTPException(status_code=400, detail="导出时间范围不能超过90天")
    
    data = await audit_service.export_audit_logs(
        start_time=export_request.start_time,
        end_time=export_request.end_time,
        format=export_request.format
    )
    
    if not data:
        raise HTTPException(status_code=500, detail="导出失败")
    
    # 设置文件名
    filename = f"audit_logs_{export_request.start_time.strftime('%Y%m%d')}_{export_request.end_time.strftime('%Y%m%d')}"
    
    if export_request.format == "json":
        media_type = "application/json"
        filename += ".json"
    else:
        media_type = "text/csv"
        filename += ".csv"
    
    # 返回文件流
    return StreamingResponse(
        io.StringIO(data),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.delete("/cleanup")
async def cleanup_old_logs(
    days: int = Query(90, ge=30, le=365, description="保留天数"),
    current_user: User = Depends(require_admin_role)
):
    """清理旧的审计日志（管理员）"""
    deleted_count = await audit_service.cleanup_old_logs(days=days)
    
    return {
        "message": f"成功清理 {deleted_count} 条旧审计日志",
        "deleted_count": deleted_count,
        "retention_days": days
    }


@router.get("/levels")
async def get_audit_levels(current_user: User = Depends(require_admin_role)):
    """获取审计级别列表（管理员）"""
    return {
        "levels": [
            {"value": level.value, "name": level.value.upper()}
            for level in AuditLevel
        ]
    }


@router.get("/categories")
async def get_audit_categories(current_user: User = Depends(require_admin_role)):
    """获取审计分类列表（管理员）"""
    category_names = {
        AuditCategory.AUTH: "认证相关",
        AuditCategory.USER: "用户管理",
        AuditCategory.SUBSCRIPTION: "订阅管理",
        AuditCategory.PAYMENT: "支付相关",
        AuditCategory.ADMIN: "管理员操作",
        AuditCategory.SECURITY: "安全相关",
        AuditCategory.SYSTEM: "系统操作",
        AuditCategory.DATA: "数据操作"
    }
    
    return {
        "categories": [
            {"value": category.value, "name": category_names.get(category, category.value)}
            for category in AuditCategory
        ]
    }