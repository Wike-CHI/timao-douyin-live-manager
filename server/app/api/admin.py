# -*- coding: utf-8 -*-
"""
管理员API路由
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator, EmailStr
from server.app.database import get_db
from server.app.core.dependencies import require_admin_role, get_current_user
from server.app.services.admin_service import AdminService
from server.app.services.audit_service import AuditService
from server.app.models.user import User, UserRoleEnum, UserStatusEnum
from server.app.models.permission import AuditLog
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


# ==================== Pydantic 模型 ====================

class UserListResponse(BaseModel):
    """用户列表响应"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    nickname: Optional[str] = None
    phone: Optional[str] = None
    role: UserRoleEnum
    status: Optional[UserStatusEnum] = None
    is_active: bool
    is_verified: bool
    email_verified: Optional[bool] = False
    phone_verified: Optional[bool] = False
    login_count: Optional[int] = 0
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm(cls, user: User):
        """从ORM对象创建响应"""
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=getattr(user, 'full_name', None) or user.nickname,
            nickname=user.nickname,
            phone=user.phone,
            role=user.role,
            status=user.status,
            is_active=user.is_active,
            is_verified=user.email_verified,
            email_verified=user.email_verified,
            phone_verified=user.phone_verified,
            login_count=user.login_count,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )


class UserDetailResponse(BaseModel):
    """用户详情响应"""
    user: UserListResponse
    subscriptions: List[Dict[str, Any]]
    payments: List[Dict[str, Any]]
    audit_logs: List[Dict[str, Any]]
    stats: Dict[str, Any]


class UserUpdateRequest(BaseModel):
    """用户更新请求"""
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRoleEnum] = None
    status: Optional[UserStatusEnum] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    email_verified: Optional[bool] = None
    phone_verified: Optional[bool] = None
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
    format: str = Field("csv", pattern="^(csv|json)$")
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
@router.post("/users", response_model=UserListResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """创建用户"""
    try:
        admin_service = AdminService(db)
        audit_service = AuditService(db)
        
        # 检查用户名和邮箱是否已存在
        existing_user = db.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名或邮箱已存在"
            )
        
        # 创建用户
        new_user = admin_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            nickname=user_data.nickname,
            phone=user_data.phone,
            role=user_data.role
        )
        
        if not new_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="创建用户失败"
            )
        
        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="create_user",
            resource_type="user",
            resource_id=new_user.id,
            details={"username": user_data.username, "email": user_data.email}
        )
        
        user_response = UserListResponse.from_orm(new_user)
        return {
            "data": user_response.model_dump()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建用户失败")


@router.get("/users", response_model=Dict[str, Any])
async def get_users(
    search: Optional[str] = Query(None, description="搜索关键词"),
    role: Optional[UserRoleEnum] = Query(None, description="用户角色"),
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
        
        # 转换为字典格式
        user_list = []
        for user in users:
            user_response = UserListResponse.from_orm(user)
            user_dict = user_response.model_dump()
            user_list.append(user_dict)
        
        return {
            "data": user_list,
            "total": total,
            "page": page,
            "perPage": size,
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
        
        # 格式化响应数据
        user_response = UserListResponse.from_orm(user_detail["user"])
        detail_data = {
            "user": user_response.model_dump(),
            "subscriptions": [
                {
                    "id": sub.id if hasattr(sub, 'id') else None,
                    "plan": {"name": getattr(sub, 'plan', {}).get('name', '未知') if isinstance(getattr(sub, 'plan', {}), dict) else str(getattr(sub, 'plan', '未知'))},
                    "status": getattr(sub, 'status', '未知'),
                    "created_at": sub.created_at.isoformat() if hasattr(sub, 'created_at') and sub.created_at else None,
                }
                for sub in user_detail.get("subscriptions", [])
            ],
            "payments": [
                {
                    "id": pay.id if hasattr(pay, 'id') else None,
                    "amount": float(getattr(pay, 'amount', 0)),
                    "status": getattr(pay, 'status', '未知'),
                    "created_at": pay.created_at.isoformat() if hasattr(pay, 'created_at') and pay.created_at else None,
                }
                for pay in user_detail.get("payments", [])
            ],
            "audit_logs": [
                {
                    "id": log.id if hasattr(log, 'id') else None,
                    "action": getattr(log, 'action', '未知'),
                    "description": getattr(log, 'description', ''),
                    "created_at": log.created_at.isoformat() if hasattr(log, 'created_at') and log.created_at else None,
                }
                for log in user_detail.get("audit_logs", [])
            ],
            "stats": user_detail.get("stats", {})
        }
        
        return {
            "data": detail_data
        }
        
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
        
        user_response = UserListResponse.from_orm(updated_user)
        return {
            "data": user_response.model_dump()
        }
        
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
        
        user_response = UserListResponse.from_orm(banned_user)
        return {
            "data": user_response.model_dump()
        }
        
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
        
        user_response = UserListResponse.from_orm(unbanned_user)
        return {
            "data": user_response.model_dump()
        }
        
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
        
        return {
            "data": {"id": user_id}
        }
        
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


# ==================== 套餐管理接口 ====================

class PlanCreateRequest(BaseModel):
    """创建套餐请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    plan_type: str = Field(..., description="套餐类型: free, basic, professional, enterprise")
    billing_cycle: str = Field(..., description="计费周期: monthly, quarterly, yearly, lifetime")
    price: float = Field(..., ge=0)
    original_price: Optional[float] = Field(None, ge=0)
    duration_days: int = Field(..., gt=0)
    ai_quota: Optional[int] = Field(0, ge=0)
    recording_duration: Optional[int] = Field(0, ge=0)
    storage_quota: Optional[int] = Field(0, ge=0)
    max_concurrent_streams: Optional[int] = Field(1, ge=1)
    is_active: bool = True
    features: Optional[Dict[str, Any]] = None
    limits: Optional[Dict[str, Any]] = None


class PlanUpdateRequest(BaseModel):
    """更新套餐请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    plan_type: Optional[str] = None
    billing_cycle: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    original_price: Optional[float] = Field(None, ge=0)
    duration_days: Optional[int] = Field(None, gt=0)
    ai_quota: Optional[int] = Field(None, ge=0)
    recording_duration: Optional[int] = Field(None, ge=0)
    storage_quota: Optional[int] = Field(None, ge=0)
    max_concurrent_streams: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    features: Optional[Dict[str, Any]] = None
    limits: Optional[Dict[str, Any]] = None


class PlanResponse(BaseModel):
    """套餐响应"""
    id: int
    name: str
    description: Optional[str]
    plan_type: str
    duration: str
    price: float
    original_price: Optional[float]
    currency: str
    features: Optional[Dict[str, Any]]
    limits: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # 额外字段(从duration和其他字段计算)
    billing_cycle: Optional[str] = None
    duration_days: Optional[int] = None
    ai_quota: Optional[int] = None
    recording_duration: Optional[int] = None
    storage_quota: Optional[int] = None
    max_concurrent_streams: Optional[int] = None
    
    class Config:
        from_attributes = True


@router.get("/plans")
async def get_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None, description="搜索套餐名称"),
    plan_type: Optional[str] = Query(None, description="套餐类型"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取套餐列表"""
    try:
        from server.app.models.payment import Plan
        from sqlalchemy import and_, or_
        
        query = db.query(Plan)
        
        # 搜索过滤
        if search:
            query = query.filter(
                or_(
                    Plan.name.ilike(f"%{search}%"),
                    Plan.description.ilike(f"%{search}%")
                )
            )
        
        # 类型过滤
        if plan_type:
            query = query.filter(Plan.plan_type == plan_type)
        
        # 状态过滤
        if is_active is not None:
            query = query.filter(Plan.is_active == is_active)
        
        total = query.count()
        plans = query.order_by(Plan.created_at.desc()).offset(skip).limit(limit).all()
        
        # 转换响应
        items = []
        for plan in plans:
            plan_dict = {
                "id": plan.id,
                "name": plan.name,
                "description": plan.description,
                "plan_type": plan.plan_type,
                "duration": plan.duration,
                "price": float(plan.price),
                "original_price": float(plan.original_price) if plan.original_price else None,
                "currency": plan.currency,
                "features": plan.features or {},
                "limits": plan.limits or {},
                "is_active": plan.is_active,
                "created_at": plan.created_at,
                "updated_at": plan.updated_at,
                # 从duration解析
                "billing_cycle": plan.duration,
                "duration_days": plan.limits.get("duration_days") if plan.limits else 30,
                "ai_quota": plan.limits.get("ai_quota") if plan.limits else 0,
                "recording_duration": plan.limits.get("recording_duration") if plan.limits else 0,
                "storage_quota": plan.limits.get("storage_quota") if plan.limits else 0,
                "max_concurrent_streams": plan.limits.get("max_concurrent_streams", 1) if plan.limits else 1,
            }
            items.append(plan_dict)
        
        return {
            "data": items,
            "total": total
        }
        
    except Exception as e:
        logger.error(f"获取套餐列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取套餐列表失败")


@router.get("/plans/{plan_id}")
async def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取套餐详情"""
    try:
        from server.app.models.payment import Plan
        
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="套餐不存在")
        
        plan_dict = {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "plan_type": plan.plan_type,
            "duration": plan.duration,
            "price": float(plan.price),
            "original_price": float(plan.original_price) if plan.original_price else None,
            "currency": plan.currency,
            "features": plan.features or {},
            "limits": plan.limits or {},
            "is_active": plan.is_active,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "billing_cycle": plan.duration,
            "duration_days": plan.limits.get("duration_days") if plan.limits else 30,
            "ai_quota": plan.limits.get("ai_quota") if plan.limits else 0,
            "recording_duration": plan.limits.get("recording_duration") if plan.limits else 0,
            "storage_quota": plan.limits.get("storage_quota") if plan.limits else 0,
            "max_concurrent_streams": plan.limits.get("max_concurrent_streams", 1) if plan.limits else 1,
        }
        
        return {"data": plan_dict}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取套餐详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取套餐详情失败")


@router.post("/plans", status_code=201)
async def create_plan(
    plan_data: PlanCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """创建套餐"""
    try:
        from server.app.models.payment import Plan
        
        # 构建limits和features
        limits = plan_data.limits or {}
        limits.update({
            "duration_days": plan_data.duration_days,
            "ai_quota": plan_data.ai_quota,
            "recording_duration": plan_data.recording_duration,
            "storage_quota": plan_data.storage_quota,
            "max_concurrent_streams": plan_data.max_concurrent_streams,
        })
        
        features = plan_data.features or {}
        
        plan = Plan(
            name=plan_data.name,
            description=plan_data.description,
            plan_type=plan_data.plan_type,
            duration=plan_data.billing_cycle,
            price=plan_data.price,
            original_price=plan_data.original_price,
            currency="CNY",
            features=features,
            limits=limits,
            is_active=plan_data.is_active
        )
        
        db.add(plan)
        db.commit()
        db.refresh(plan)
        
        # 记录审计日志
        audit_service = AuditService(db)
        await audit_service.log_action(
            user_id=current_user.id,
            action="create_plan",
            resource_type="plan",
            resource_id=str(plan.id),
            details={"name": plan.name, "plan_type": plan.plan_type}
        )
        
        plan_dict = {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "plan_type": plan.plan_type,
            "duration": plan.duration,
            "price": float(plan.price),
            "original_price": float(plan.original_price) if plan.original_price else None,
            "currency": plan.currency,
            "features": plan.features,
            "limits": plan.limits,
            "is_active": plan.is_active,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
        }
        
        return {"data": plan_dict}
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建套餐失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建套餐失败: {str(e)}")


@router.put("/plans/{plan_id}")
async def update_plan(
    plan_id: int,
    plan_data: PlanUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """更新套餐"""
    try:
        from server.app.models.payment import Plan
        
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="套餐不存在")
        
        # 更新基本字段
        if plan_data.name is not None:
            plan.name = plan_data.name
        if plan_data.description is not None:
            plan.description = plan_data.description
        if plan_data.plan_type is not None:
            plan.plan_type = plan_data.plan_type
        if plan_data.billing_cycle is not None:
            plan.duration = plan_data.billing_cycle
        if plan_data.price is not None:
            plan.price = plan_data.price
        if plan_data.original_price is not None:
            plan.original_price = plan_data.original_price
        if plan_data.is_active is not None:
            plan.is_active = plan_data.is_active
        
        # 更新limits
        if plan.limits is None:
            plan.limits = {}
        
        if plan_data.duration_days is not None:
            plan.limits["duration_days"] = plan_data.duration_days
        if plan_data.ai_quota is not None:
            plan.limits["ai_quota"] = plan_data.ai_quota
        if plan_data.recording_duration is not None:
            plan.limits["recording_duration"] = plan_data.recording_duration
        if plan_data.storage_quota is not None:
            plan.limits["storage_quota"] = plan_data.storage_quota
        if plan_data.max_concurrent_streams is not None:
            plan.limits["max_concurrent_streams"] = plan_data.max_concurrent_streams
        
        # 更新features
        if plan_data.features is not None:
            if plan.features is None:
                plan.features = {}
            plan.features.update(plan_data.features)
        
        if plan_data.limits is not None:
            plan.limits.update(plan_data.limits)
        
        db.commit()
        db.refresh(plan)
        
        # 记录审计日志
        audit_service = AuditService(db)
        await audit_service.log_action(
            user_id=current_user.id,
            action="update_plan",
            resource_type="plan",
            resource_id=str(plan.id),
            details={"name": plan.name}
        )
        
        plan_dict = {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "plan_type": plan.plan_type,
            "duration": plan.duration,
            "price": float(plan.price),
            "original_price": float(plan.original_price) if plan.original_price else None,
            "currency": plan.currency,
            "features": plan.features,
            "limits": plan.limits,
            "is_active": plan.is_active,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
        }
        
        return {"data": plan_dict}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新套餐失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新套餐失败: {str(e)}")


@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """删除套餐"""
    try:
        from server.app.models.payment import Plan
        
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="套餐不存在")
        
        # 软删除 - 只是禁用
        plan.is_active = False
        db.commit()
        
        # 记录审计日志
        audit_service = AuditService(db)
        await audit_service.log_action(
            user_id=current_user.id,
            action="delete_plan",
            resource_type="plan",
            resource_id=str(plan.id),
            details={"name": plan.name}
        )
        
        return {"message": "套餐已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除套餐失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除套餐失败")