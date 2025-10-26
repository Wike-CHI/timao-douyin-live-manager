# -*- coding: utf-8 -*-
"""
管理员API路由
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from ..database import get_db
from ..core.dependencies import require_admin_role, get_current_user
from ..services.admin_service import AdminService
from ..services.audit_service import AuditService
from ..models.user import User, UserRole
from ..models.permission import AuditLog
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


# ==================== Pydantic 模型 ====================

class UserListResponse(BaseModel):
    """用户列表响应"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserDetailResponse(BaseModel):
    """用户详情响应"""
    user: UserListResponse
    subscriptions: List[Dict[str, Any]]
    payments: List[Dict[str, Any]]
    audit_logs: List[Dict[str, Any]]
    stats: Dict[str, Any]


class UserUpdateRequest(BaseModel):
    """用户更新请求"""
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class UserBanRequest(BaseModel):
    """用户封禁请求"""
    reason: Optional[str] = None
    duration_days: Optional[int] = Field(None, gt=0, le=365)


class SystemStatsResponse(BaseModel):
    """系统统计响应"""
    users: Dict[str, int]
    subscriptions: Dict[str, int]
    payments: Dict[str, Any]
    revenue: Dict[str, float]


class ChartDataResponse(BaseModel):
    """图表数据响应"""
    data: List[Dict[str, Any]]


class PlanDistributionResponse(BaseModel):
    """套餐分布响应"""
    plan_name: str
    plan_type: str
    subscription_count: int
    active_count: int


class PaymentMethodStatsResponse(BaseModel):
    """支付方式统计响应"""
    payment_method: str
    count: int
    total_amount: float
    success_count: int
    success_rate: float


class SystemHealthResponse(BaseModel):
    """系统健康状态响应"""
    database: str
    expired_subscriptions: int
    pending_payments: int
    timestamp: str


class CleanupResultResponse(BaseModel):
    """清理结果响应"""
    expired_subscriptions: int
    deleted_audit_logs: int


class ExportRequest(BaseModel):
    """导出请求"""
    format: str = Field("csv", regex="^(csv|json)$")
    filters: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreateUserRequest(BaseModel):
    """创建用户请求"""
    username: str
    email: EmailStr
    password: str
    nickname: Optional[str] = None
    phone: Optional[str] = None
    role: UserRoleEnum = UserRoleEnum.USER
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('用户名长度必须在3-50个字符之间')
        return v


class UpdateUserRequest(BaseModel):
    """更新用户请求"""
    nickname: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRoleEnum] = None
    status: Optional[UserStatusEnum] = None
    email_verified: Optional[bool] = None
    phone_verified: Optional[bool] = None


class SystemStatsResponse(BaseModel):
    """系统统计响应"""
    total_users: int
    active_users: int
    new_users_today: int
    total_subscriptions: int
    active_subscriptions: int
    total_revenue: float
    revenue_this_month: float


class CreateSubscriptionPlanRequest(BaseModel):
    """创建订阅套餐请求"""
    name: str
    description: Optional[str] = None
    plan_type: str
    price: float
    duration_days: int
    features: Dict[str, Any] = {}
    usage_limits: Dict[str, Any] = {}
    is_active: bool = True


class UpdateSubscriptionPlanRequest(BaseModel):
    """更新订阅套餐请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    duration_days: Optional[int] = None
    features: Optional[Dict[str, Any]] = None
    usage_limits: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


# 用户管理API
@router.get("/users", response_model=Dict[str, Any])
async def get_users(
    search: Optional[str] = Query(None, description="搜索关键词"),
    role: Optional[UserRole] = Query(None, description="用户角色"),
    is_active: Optional[bool] = Query(None, description="是否活跃"),
    is_verified: Optional[bool] = Query(None, description="是否已验证"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取用户列表"""
    try:
        admin_service = AdminService(db)
        audit_service = AuditService(db)
        
        skip = (page - 1) * size
        users, total = admin_service.get_users(
            search=search,
            role=role,
            is_active=is_active,
            is_verified=is_verified,
            skip=skip,
            limit=size
        )
        
        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="view_users",
            resource_type="user",
            details={"search": search, "role": role, "page": page}
        )
        
        return {
            "items": [UserListResponse.from_orm(user) for user in users],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户列表失败")


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取用户详情"""
    try:
        admin_service = AdminService(db)
        audit_service = AuditService(db)
        
        user_detail = admin_service.get_user_detail(user_id)
        if not user_detail:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="view_user_detail",
            resource_type="user",
            resource_id=user_id
        )
        
        return UserDetailResponse(**user_detail)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户详情失败")


@router.put("/users/{user_id}", response_model=UserListResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """更新用户信息"""
    try:
        admin_service = AdminService(db)
        audit_service = AuditService(db)
        
        # 检查用户是否存在
        existing_user = db.query(User).filter(User.id == user_id).first()
        if not existing_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 更新用户
        update_data = user_update.dict(exclude_unset=True)
        updated_user = admin_service.update_user(user_id, **update_data)
        
        if not updated_user:
            raise HTTPException(status_code=400, detail="更新用户失败")
        
        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="update_user",
            resource_type="user",
            resource_id=user_id,
            details={"updated_fields": list(update_data.keys())}
        )
        
        return UserListResponse.from_orm(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新用户失败")


@router.post("/users/{user_id}/ban", response_model=UserListResponse)
async def ban_user(
    user_id: int,
    ban_request: UserBanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """封禁用户"""
    try:
        admin_service = AdminService(db)
        audit_service = AuditService(db)
        
        banned_user = admin_service.ban_user(
            user_id=user_id,
            reason=ban_request.reason,
            duration_days=ban_request.duration_days
        )
        
        if not banned_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="ban_user",
            resource_type="user",
            resource_id=user_id,
            details={
                "reason": ban_request.reason,
                "duration_days": ban_request.duration_days
            }
        )
        
        return UserListResponse.from_orm(banned_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"封禁用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail="封禁用户失败")


@router.post("/users/{user_id}/unban", response_model=UserListResponse)
async def unban_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """解封用户"""
    try:
        admin_service = AdminService(db)
        audit_service = AuditService(db)
        
        unbanned_user = admin_service.unban_user(user_id)
        if not unbanned_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="unban_user",
            resource_type="user",
            resource_id=user_id
        )
        
        return UserListResponse.from_orm(unbanned_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解封用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail="解封用户失败")


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """删除用户"""
    try:
        admin_service = AdminService(db)
        audit_service = AuditService(db)
        
        success = admin_service.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="delete_user",
            resource_type="user",
            resource_id=user_id
        )
        
        return {"message": "用户删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除用户失败")


# ==================== 系统监控接口 ====================

@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取系统统计信息"""
    try:
        admin_service = AdminService(db)
        stats = admin_service.get_system_stats()
        return SystemStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"获取系统统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取系统统计失败")


@router.get("/charts/user-growth", response_model=ChartDataResponse)
async def get_user_growth_chart(
    days: int = Query(30, ge=1, le=365, description="天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取用户增长图表"""
    try:
        admin_service = AdminService(db)
        data = admin_service.get_user_growth_chart(days)
        return ChartDataResponse(data=data)
        
    except Exception as e:
        logger.error(f"获取用户增长图表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户增长图表失败")


@router.get("/charts/revenue", response_model=ChartDataResponse)
async def get_revenue_chart(
    days: int = Query(30, ge=1, le=365, description="天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取收入图表"""
    try:
        admin_service = AdminService(db)
        data = admin_service.get_revenue_chart(days)
        return ChartDataResponse(data=data)
        
    except Exception as e:
        logger.error(f"获取收入图表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取收入图表失败")


@router.get("/stats/plan-distribution", response_model=List[PlanDistributionResponse])
async def get_plan_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取套餐分布统计"""
    try:
        admin_service = AdminService(db)
        data = admin_service.get_plan_distribution()
        return [PlanDistributionResponse(**item) for item in data]
        
    except Exception as e:
        logger.error(f"获取套餐分布统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取套餐分布统计失败")


@router.get("/stats/payment-methods", response_model=List[PaymentMethodStatsResponse])
async def get_payment_method_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取支付方式统计"""
    try:
        admin_service = AdminService(db)
        data = admin_service.get_payment_method_stats()
        return [PaymentMethodStatsResponse(**item) for item in data]
        
    except Exception as e:
        logger.error(f"获取支付方式统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取支付方式统计失败")


# ==================== 活动监控接口 ====================

@router.get("/activities/recent")
async def get_recent_activities(
    limit: int = Query(50, ge=1, le=200, description="数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取最近活动"""
    try:
        admin_service = AdminService(db)
        activities = admin_service.get_recent_activities(limit)
        return [
            {
                "id": activity.id,
                "user_id": activity.user_id,
                "action": activity.action,
                "resource_type": activity.resource_type,
                "resource_id": activity.resource_id,
                "level": activity.level,
                "category": activity.category,
                "ip_address": activity.ip_address,
                "user_agent": activity.user_agent,
                "created_at": activity.created_at,
                "details": activity.details
            }
            for activity in activities
        ]
        
    except Exception as e:
        logger.error(f"获取最近活动失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取最近活动失败")


@router.get("/security/events")
async def get_security_events(
    hours: int = Query(24, ge=1, le=168, description="小时数"),
    limit: int = Query(100, ge=1, le=500, description="数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取安全事件"""
    try:
        admin_service = AdminService(db)
        start_date = datetime.utcnow() - timedelta(hours=hours)
        events = admin_service.get_security_events(
            start_date=start_date,
            limit=limit
        )
        
        return [
            {
                "id": event.id,
                "user_id": event.user_id,
                "action": event.action,
                "resource_type": event.resource_type,
                "level": event.level,
                "category": event.category,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "created_at": event.created_at,
                "details": event.details
            }
            for event in events
        ]
        
    except Exception as e:
        logger.error(f"获取安全事件失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取安全事件失败")


@router.get("/security/failed-logins")
async def get_failed_login_attempts(
    hours: int = Query(24, ge=1, le=168, description="小时数"),
    limit: int = Query(100, ge=1, le=500, description="数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取失败登录尝试"""
    try:
        admin_service = AdminService(db)
        attempts = admin_service.get_failed_login_attempts(
            hours=hours,
            limit=limit
        )
        
        return [
            {
                "id": attempt.id,
                "user_id": attempt.user_id,
                "ip_address": attempt.ip_address,
                "user_agent": attempt.user_agent,
                "created_at": attempt.created_at,
                "details": attempt.details
            }
            for attempt in attempts
        ]
        
    except Exception as e:
        logger.error(f"获取失败登录尝试失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取失败登录尝试失败")


# ==================== 系统维护接口 ====================

@router.get("/system/health", response_model=SystemHealthResponse)
async def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取系统健康状态"""
    try:
        admin_service = AdminService(db)
        health = admin_service.get_system_health()
        return SystemHealthResponse(**health)
        
    except Exception as e:
        logger.error(f"获取系统健康状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取系统健康状态失败")


@router.post("/system/cleanup", response_model=CleanupResultResponse)
async def cleanup_expired_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """清理过期数据"""
    try:
        admin_service = AdminService(db)
        audit_service = AuditService(db)
        
        result = admin_service.cleanup_expired_data()
        
        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="cleanup_expired_data",
            resource_type="system",
            details=result
        )
        
        return CleanupResultResponse(**result)
        
    except Exception as e:
        logger.error(f"清理过期数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="清理过期数据失败")


# ==================== 数据导出接口 ====================

@router.post("/export/users")
async def export_users(
    export_request: ExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """导出用户数据"""
    try:
        admin_service = AdminService(db)
        audit_service = AuditService(db)
        
        data = admin_service.export_users(
            format=export_request.format,
            filters=export_request.filters
        )
        
        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="export_users",
            resource_type="user",
            details={"format": export_request.format, "filters": export_request.filters}
        )
        
        # 设置响应头
        filename = f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_request.format}"
        media_type = "text/csv" if export_request.format == "csv" else "application/json"
        
        return Response(
            content=data,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"导出用户数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="导出用户数据失败")


@router.post("/export/payments")
async def export_payments(
    export_request: ExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """导出支付数据"""
    try:
        admin_service = AdminService(db)
        audit_service = AuditService(db)
        
        data = admin_service.export_payments(
            format=export_request.format,
            filters=export_request.filters
        )
        
        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="export_payments",
            resource_type="payment",
            details={"format": export_request.format, "filters": export_request.filters}
        )
        
        # 设置响应头
        filename = f"payments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_request.format}"
        media_type = "text/csv" if export_request.format == "csv" else "application/json"
        
        return Response(
            content=data,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"导出支付数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="导出支付数据失败")