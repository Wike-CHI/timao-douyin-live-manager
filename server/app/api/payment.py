# -*- coding: utf-8 -*-
"""
支付相关API路由
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from ..core.dependencies import (
    get_db, get_current_active_user, require_admin_role,
    get_request_info
)
from ..models.user import User
from ..models.payment import (
    Plan, Subscription, Payment, Invoice, Coupon,
    PlanType, PlanDuration, PaymentStatus, PaymentMethod,
    SubscriptionStatus, InvoiceStatus
)
from ..services.payment_service import PaymentService
from ..services.audit_service import AuditService

router = APIRouter(prefix="/payment", tags=["payment"])


# ==================== Pydantic 模型 ====================

class PlanCreate(BaseModel):
    """创建套餐请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    plan_type: PlanType
    duration: PlanDuration
    price: Decimal = Field(..., ge=0)
    original_price: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="CNY", max_length=3)
    features: Dict[str, Any] = Field(default_factory=dict)
    limits: Dict[str, Any] = Field(default_factory=dict)
    sort_order: int = Field(default=0)


class PlanUpdate(BaseModel):
    """更新套餐请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    original_price: Optional[Decimal] = Field(None, ge=0)
    features: Optional[Dict[str, Any]] = None
    limits: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class PlanResponse(BaseModel):
    """套餐响应"""
    id: int
    name: str
    description: Optional[str]
    plan_type: str
    duration: str
    price: Decimal
    original_price: Decimal
    currency: str
    features: Dict[str, Any]
    limits: Dict[str, Any]
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    """创建订阅请求"""
    plan_id: int
    trial_days: int = Field(default=0, ge=0, le=30)
    auto_renew: bool = Field(default=True)


class SubscriptionResponse(BaseModel):
    """订阅响应"""
    id: int
    user_id: int
    plan_id: int
    status: str
    start_date: datetime
    end_date: datetime
    auto_renew: bool
    trial_end_date: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancel_reason: Optional[str]
    is_active: bool
    is_trial: bool
    days_remaining: int
    plan: PlanResponse
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    """创建支付请求"""
    subscription_id: Optional[int] = None
    amount: Decimal = Field(..., gt=0)
    payment_method: PaymentMethod
    currency: str = Field(default="CNY", max_length=3)
    coupon_code: Optional[str] = None
    return_url: Optional[str] = None


class PaymentResponse(BaseModel):
    """支付响应"""
    id: int
    user_id: int
    subscription_id: Optional[int]
    amount: Decimal
    currency: str
    payment_method: str
    status: str
    transaction_id: str
    external_id: Optional[str]
    payment_url: Optional[str]
    paid_at: Optional[datetime]
    failed_at: Optional[datetime]
    failure_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CouponCreate(BaseModel):
    """创建优惠券请求"""
    code: str = Field(..., min_length=3, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    discount_type: str = Field(..., regex="^(percentage|fixed)$")
    discount_value: Decimal = Field(..., gt=0)
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_discount: Optional[Decimal] = Field(None, ge=0)
    usage_limit: Optional[int] = Field(None, gt=0)
    valid_from: datetime
    valid_until: datetime
    applicable_plans: Optional[List[int]] = None

    @validator('valid_until')
    def validate_dates(cls, v, values):
        if 'valid_from' in values and v <= values['valid_from']:
            raise ValueError('valid_until must be after valid_from')
        return v


class CouponResponse(BaseModel):
    """优惠券响应"""
    id: int
    code: str
    name: str
    description: Optional[str]
    discount_type: str
    discount_value: Decimal
    min_amount: Optional[Decimal]
    max_discount: Optional[Decimal]
    usage_limit: Optional[int]
    used_count: int
    valid_from: datetime
    valid_until: datetime
    is_active: bool
    is_valid: bool
    applicable_plans: List[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CouponValidateRequest(BaseModel):
    """验证优惠券请求"""
    code: str
    amount: Decimal = Field(..., gt=0)
    plan_id: Optional[int] = None


class CouponValidateResponse(BaseModel):
    """验证优惠券响应"""
    valid: bool
    message: str
    discount_amount: Optional[Decimal] = None
    final_amount: Optional[Decimal] = None


class InvoiceResponse(BaseModel):
    """发票响应"""
    id: int
    user_id: int
    payment_id: Optional[int]
    invoice_number: str
    status: str
    amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    issue_date: datetime
    due_date: Optional[datetime]
    paid_date: Optional[datetime]
    billing_name: Optional[str]
    billing_email: Optional[str]
    billing_address: Optional[str]
    tax_id: Optional[str]
    items: List[Dict[str, Any]]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentStatistics(BaseModel):
    """支付统计"""
    total_amount: float
    total_count: int
    success_count: int
    success_rate: float
    by_method: Dict[str, int]
    by_status: Dict[str, int]


class SubscriptionStatistics(BaseModel):
    """订阅统计"""
    total_count: int
    active_count: int
    by_status: Dict[str, int]
    by_plan: Dict[str, int]


# ==================== 套餐管理 ====================

@router.post("/plans", response_model=PlanResponse)
async def create_plan(
    plan_data: PlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role),
    request_info: dict = Depends(get_request_info)
):
    """创建套餐"""
    payment_service = PaymentService(db)
    audit_service = AuditService(db)
    
    plan = payment_service.create_plan(
        name=plan_data.name,
        description=plan_data.description,
        plan_type=plan_data.plan_type,
        duration=plan_data.duration,
        price=plan_data.price,
        features=plan_data.features,
        limits=plan_data.limits,
        original_price=plan_data.original_price,
        currency=plan_data.currency
    )
    
    # 记录审计日志
    await audit_service.log_action(
        user_id=current_user.id,
        action="create_plan",
        resource_type="plan",
        resource_id=plan.id,
        details={"plan_name": plan.name, "plan_type": plan.plan_type},
        ip_address=request_info["ip"],
        user_agent=request_info["user_agent"]
    )
    
    return plan


@router.get("/plans", response_model=List[PlanResponse])
async def get_plans(
    plan_type: Optional[PlanType] = Query(None),
    is_active: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取套餐列表"""
    payment_service = PaymentService(db)
    plans = payment_service.get_plans(
        plan_type=plan_type,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return plans


@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: int,
    db: Session = Depends(get_db)
):
    """获取套餐详情"""
    payment_service = PaymentService(db)
    plan = payment_service.get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )
    return plan


@router.put("/plans/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: int,
    plan_data: PlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role),
    request_info: dict = Depends(get_request_info)
):
    """更新套餐"""
    payment_service = PaymentService(db)
    audit_service = AuditService(db)
    
    plan = payment_service.update_plan(
        plan_id,
        **plan_data.dict(exclude_unset=True)
    )
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )
    
    # 记录审计日志
    await audit_service.log_action(
        user_id=current_user.id,
        action="update_plan",
        resource_type="plan",
        resource_id=plan.id,
        details={"plan_name": plan.name, "changes": plan_data.dict(exclude_unset=True)},
        ip_address=request_info["ip"],
        user_agent=request_info["user_agent"]
    )
    
    return plan


@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role),
    request_info: dict = Depends(get_request_info)
):
    """删除套餐"""
    payment_service = PaymentService(db)
    audit_service = AuditService(db)
    
    success = payment_service.delete_plan(plan_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )
    
    # 记录审计日志
    await audit_service.log_action(
        user_id=current_user.id,
        action="delete_plan",
        resource_type="plan",
        resource_id=plan_id,
        ip_address=request_info["ip"],
        user_agent=request_info["user_agent"]
    )
    
    return {"message": "套餐已删除"}


# ==================== 订阅管理 ====================

@router.post("/subscriptions", response_model=SubscriptionResponse)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    request_info: dict = Depends(get_request_info)
):
    """创建订阅"""
    payment_service = PaymentService(db)
    audit_service = AuditService(db)
    
    # 检查是否已有活跃订阅
    active_subscription = payment_service.get_active_subscription(current_user.id)
    if active_subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已有活跃的订阅"
        )
    
    subscription = payment_service.create_subscription(
        user_id=current_user.id,
        plan_id=subscription_data.plan_id,
        trial_days=subscription_data.trial_days,
        auto_renew=subscription_data.auto_renew
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )
    
    # 记录审计日志
    await audit_service.log_action(
        user_id=current_user.id,
        action="create_subscription",
        resource_type="subscription",
        resource_id=subscription.id,
        details={"plan_id": subscription_data.plan_id, "trial_days": subscription_data.trial_days},
        ip_address=request_info["ip"],
        user_agent=request_info["user_agent"]
    )
    
    return subscription


@router.get("/subscriptions", response_model=List[SubscriptionResponse])
async def get_user_subscriptions(
    status: Optional[SubscriptionStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户订阅列表"""
    payment_service = PaymentService(db)
    subscriptions = payment_service.get_user_subscriptions(
        user_id=current_user.id,
        status=status,
        skip=skip,
        limit=limit
    )
    return subscriptions


@router.get("/subscriptions/active", response_model=Optional[SubscriptionResponse])
async def get_active_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前活跃订阅"""
    payment_service = PaymentService(db)
    subscription = payment_service.get_active_subscription(current_user.id)
    return subscription


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: int,
    reason: Optional[str] = Body(None),
    immediate: bool = Body(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    request_info: dict = Depends(get_request_info)
):
    """取消订阅"""
    payment_service = PaymentService(db)
    audit_service = AuditService(db)
    
    subscription = payment_service.get_subscription(subscription_id)
    if not subscription or subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )
    
    subscription = payment_service.cancel_subscription(
        subscription_id,
        reason=reason,
        immediate=immediate
    )
    
    # 记录审计日志
    await audit_service.log_action(
        user_id=current_user.id,
        action="cancel_subscription",
        resource_type="subscription",
        resource_id=subscription_id,
        details={"reason": reason, "immediate": immediate},
        ip_address=request_info["ip"],
        user_agent=request_info["user_agent"]
    )
    
    return {"message": "订阅已取消"}


@router.post("/subscriptions/{subscription_id}/renew")
async def renew_subscription(
    subscription_id: int,
    plan_id: Optional[int] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    request_info: dict = Depends(get_request_info)
):
    """续费订阅"""
    payment_service = PaymentService(db)
    audit_service = AuditService(db)
    
    subscription = payment_service.get_subscription(subscription_id)
    if not subscription or subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )
    
    subscription = payment_service.renew_subscription(subscription_id, plan_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="续费失败"
        )
    
    # 记录审计日志
    await audit_service.log_action(
        user_id=current_user.id,
        action="renew_subscription",
        resource_type="subscription",
        resource_id=subscription_id,
        details={"new_plan_id": plan_id},
        ip_address=request_info["ip"],
        user_agent=request_info["user_agent"]
    )
    
    return {"message": "订阅已续费"}


# ==================== 支付处理 ====================

@router.post("/payments", response_model=PaymentResponse)
async def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    request_info: dict = Depends(get_request_info)
):
    """创建支付"""
    payment_service = PaymentService(db)
    audit_service = AuditService(db)
    
    amount = payment_data.amount
    
    # 验证优惠券
    if payment_data.coupon_code:
        valid, message, discount_amount = payment_service.validate_coupon(
            payment_data.coupon_code,
            current_user.id,
            amount,
            plan_id=None  # 如果需要可以从subscription中获取
        )
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        amount -= discount_amount
    
    payment = payment_service.create_payment(
        user_id=current_user.id,
        amount=amount,
        payment_method=payment_data.payment_method,
        subscription_id=payment_data.subscription_id,
        currency=payment_data.currency,
        metadata={
            "coupon_code": payment_data.coupon_code,
            "return_url": payment_data.return_url
        }
    )
    
    # 使用优惠券
    if payment_data.coupon_code and discount_amount:
        payment_service.use_coupon(
            payment_data.coupon_code,
            current_user.id,
            payment.id,
            discount_amount
        )
    
    # 记录审计日志
    await audit_service.log_action(
        user_id=current_user.id,
        action="create_payment",
        resource_type="payment",
        resource_id=payment.id,
        details={
            "amount": float(payment_data.amount),
            "payment_method": payment_data.payment_method,
            "coupon_code": payment_data.coupon_code
        },
        ip_address=request_info["ip"],
        user_agent=request_info["user_agent"]
    )
    
    return payment


@router.get("/payments", response_model=List[PaymentResponse])
async def get_user_payments(
    status: Optional[PaymentStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户支付记录"""
    query = db.query(Payment).filter(Payment.user_id == current_user.id)
    
    if status:
        query = query.filter(Payment.status == status)
    
    payments = query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    return payments


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取支付详情"""
    payment_service = PaymentService(db)
    payment = payment_service.get_payment(payment_id)
    
    if not payment or payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="支付记录不存在"
        )
    
    return payment


# ==================== 优惠券管理 ====================

@router.post("/coupons", response_model=CouponResponse)
async def create_coupon(
    coupon_data: CouponCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role),
    request_info: dict = Depends(get_request_info)
):
    """创建优惠券"""
    payment_service = PaymentService(db)
    audit_service = AuditService(db)
    
    coupon = payment_service.create_coupon(
        code=coupon_data.code,
        name=coupon_data.name,
        discount_type=coupon_data.discount_type,
        discount_value=coupon_data.discount_value,
        valid_from=coupon_data.valid_from,
        valid_until=coupon_data.valid_until,
        description=coupon_data.description,
        min_amount=coupon_data.min_amount,
        max_discount=coupon_data.max_discount,
        usage_limit=coupon_data.usage_limit,
        applicable_plans=coupon_data.applicable_plans
    )
    
    # 记录审计日志
    await audit_service.log_action(
        user_id=current_user.id,
        action="create_coupon",
        resource_type="coupon",
        resource_id=coupon.id,
        details={"code": coupon.code, "discount_value": float(coupon.discount_value)},
        ip_address=request_info["ip"],
        user_agent=request_info["user_agent"]
    )
    
    return coupon


@router.post("/coupons/validate", response_model=CouponValidateResponse)
async def validate_coupon(
    validate_data: CouponValidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """验证优惠券"""
    payment_service = PaymentService(db)
    
    valid, message, discount_amount = payment_service.validate_coupon(
        validate_data.code,
        current_user.id,
        validate_data.amount,
        validate_data.plan_id
    )
    
    final_amount = None
    if valid and discount_amount:
        final_amount = validate_data.amount - discount_amount
    
    return CouponValidateResponse(
        valid=valid,
        message=message,
        discount_amount=discount_amount,
        final_amount=final_amount
    )


# ==================== 发票管理 ====================

@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_user_invoices(
    status: Optional[InvoiceStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户发票列表"""
    payment_service = PaymentService(db)
    invoices = payment_service.get_user_invoices(
        user_id=current_user.id,
        status=status,
        skip=skip,
        limit=limit
    )
    return invoices


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取发票详情"""
    payment_service = PaymentService(db)
    invoice = payment_service.get_invoice(invoice_id)
    
    if not invoice or invoice.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="发票不存在"
        )
    
    return invoice


# ==================== 统计分析 ====================

@router.get("/statistics/payments", response_model=PaymentStatistics)
async def get_payment_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取支付统计"""
    payment_service = PaymentService(db)
    stats = payment_service.get_payment_statistics(start_date, end_date)
    return PaymentStatistics(**stats)


@router.get("/statistics/subscriptions", response_model=SubscriptionStatistics)
async def get_subscription_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取订阅统计"""
    payment_service = PaymentService(db)
    stats = payment_service.get_subscription_statistics()
    return SubscriptionStatistics(**stats)


# ==================== 管理员功能 ====================

@router.get("/admin/subscriptions", response_model=List[SubscriptionResponse])
async def admin_get_subscriptions(
    user_id: Optional[int] = Query(None),
    status: Optional[SubscriptionStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """管理员获取订阅列表"""
    query = db.query(Subscription)
    
    if user_id:
        query = query.filter(Subscription.user_id == user_id)
    if status:
        query = query.filter(Subscription.status == status)
    
    subscriptions = query.order_by(Subscription.created_at.desc()).offset(skip).limit(limit).all()
    return subscriptions


@router.get("/admin/payments", response_model=List[PaymentResponse])
async def admin_get_payments(
    user_id: Optional[int] = Query(None),
    status: Optional[PaymentStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """管理员获取支付记录"""
    query = db.query(Payment)
    
    if user_id:
        query = query.filter(Payment.user_id == user_id)
    if status:
        query = query.filter(Payment.status == status)
    
    payments = query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    return payments


@router.post("/admin/payments/{payment_id}/refund")
async def admin_refund_payment(
    payment_id: int,
    amount: Optional[Decimal] = Body(None),
    reason: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role),
    request_info: dict = Depends(get_request_info)
):
    """管理员退款"""
    payment_service = PaymentService(db)
    audit_service = AuditService(db)
    
    payment = payment_service.refund_payment(payment_id, amount, reason)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="退款失败"
        )
    
    # 记录审计日志
    await audit_service.log_action(
        user_id=current_user.id,
        action="refund_payment",
        resource_type="payment",
        resource_id=payment_id,
        details={"amount": float(amount) if amount else None, "reason": reason},
        ip_address=request_info["ip"],
        user_agent=request_info["user_agent"]
    )
    
    return {"message": "退款成功"}