# -*- coding: utf-8 -*-
"""
订阅和支付API路由
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.api.auth import get_current_user
from app.services.subscription_service import SubscriptionService
from app.models.subscription import SubscriptionPlanTypeEnum, PaymentMethodEnum


# 创建路由器
router = APIRouter(prefix="/api/subscription", tags=["订阅"])


# Pydantic 模型
class SubscriptionPlanResponse(BaseModel):
    """订阅套餐响应"""
    id: int
    name: str
    description: Optional[str]
    plan_type: str
    price: float
    duration_days: int
    features: dict
    usage_limits: dict
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserSubscriptionResponse(BaseModel):
    """用户订阅响应"""
    id: int
    plan: SubscriptionPlanResponse
    status: str
    start_date: datetime
    end_date: datetime
    auto_renew: bool
    usage_stats: dict
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentRecordResponse(BaseModel):
    """支付记录响应"""
    id: int
    amount: float
    currency: str
    payment_method: str
    status: str
    transaction_id: Optional[str]
    payment_data: dict
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreatePaymentRequest(BaseModel):
    """创建支付请求"""
    plan_id: int
    payment_method: PaymentMethodEnum
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None


class ConfirmPaymentRequest(BaseModel):
    """确认支付请求"""
    payment_id: int
    transaction_id: str
    payment_data: Optional[dict] = None


class UpdateSubscriptionRequest(BaseModel):
    """更新订阅请求"""
    auto_renew: Optional[bool] = None


# API 路由
@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(
    active_only: bool = True,
    db: Session = Depends(get_db_session)
):
    """获取订阅套餐列表"""
    try:
        plans = SubscriptionService.get_subscription_plans(active_only=active_only)
        return [
            SubscriptionPlanResponse(
                id=plan.id,
                name=plan.name,
                description=plan.description,
                plan_type=plan.plan_type.value,
                price=plan.price,
                duration_days=plan.duration_days,
                features=plan.features,
                usage_limits=plan.usage_limits,
                is_active=plan.is_active,
                created_at=plan.created_at
            )
            for plan in plans
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取套餐列表失败"
        )


@router.get("/my-subscription", response_model=Optional[UserSubscriptionResponse])
async def get_my_subscription(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取当前用户的订阅信息"""
    try:
        subscription = SubscriptionService.get_user_subscription(current_user["id"])
        
        if not subscription:
            return None
        
        return UserSubscriptionResponse(
            id=subscription.id,
            plan=SubscriptionPlanResponse(
                id=subscription.plan.id,
                name=subscription.plan.name,
                description=subscription.plan.description,
                plan_type=subscription.plan.plan_type.value,
                price=subscription.plan.price,
                duration_days=subscription.plan.duration_days,
                features=subscription.plan.features,
                usage_limits=subscription.plan.usage_limits,
                is_active=subscription.plan.is_active,
                created_at=subscription.plan.created_at
            ),
            status=subscription.status.value,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            auto_renew=subscription.auto_renew,
            usage_stats=subscription.usage_stats,
            created_at=subscription.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订阅信息失败"
        )


@router.post("/create-payment")
async def create_payment(
    request: CreatePaymentRequest,
    current_user: dict = Depends(get_current_user),
    req: Request,
    db: Session = Depends(get_db_session)
):
    """创建支付订单"""
    try:
        # 获取客户端IP
        client_ip = req.client.host if req.client else None
        
        payment = SubscriptionService.create_payment(
            user_id=current_user["id"],
            plan_id=request.plan_id,
            payment_method=request.payment_method,
            return_url=request.return_url,
            cancel_url=request.cancel_url,
            client_ip=client_ip
        )
        
        return {
            "payment_id": payment.id,
            "amount": payment.amount,
            "currency": payment.currency,
            "payment_method": payment.payment_method.value,
            "payment_url": payment.payment_data.get("payment_url"),
            "qr_code": payment.payment_data.get("qr_code"),
            "expires_at": payment.payment_data.get("expires_at")
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建支付订单失败"
        )


@router.post("/confirm-payment")
async def confirm_payment(
    request: ConfirmPaymentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """确认支付"""
    try:
        success = SubscriptionService.confirm_payment(
            payment_id=request.payment_id,
            transaction_id=request.transaction_id,
            payment_data=request.payment_data
        )
        
        if success:
            return {"message": "支付确认成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="支付确认失败"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="支付确认失败"
        )


@router.get("/payment-history", response_model=List[PaymentRecordResponse])
async def get_payment_history(
    current_user: dict = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db_session)
):
    """获取支付历史"""
    try:
        payments = SubscriptionService.get_payment_history(
            user_id=current_user["id"],
            limit=limit,
            offset=offset
        )
        
        return [
            PaymentRecordResponse(
                id=payment.id,
                amount=payment.amount,
                currency=payment.currency,
                payment_method=payment.payment_method.value,
                status=payment.status.value,
                transaction_id=payment.transaction_id,
                payment_data=payment.payment_data,
                created_at=payment.created_at
            )
            for payment in payments
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取支付历史失败"
        )


@router.put("/update-subscription")
async def update_subscription(
    request: UpdateSubscriptionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """更新订阅设置"""
    try:
        subscription = SubscriptionService.get_user_subscription(current_user["id"])
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到订阅信息"
            )
        
        if request.auto_renew is not None:
            SubscriptionService.update_auto_renew(
                subscription_id=subscription.id,
                auto_renew=request.auto_renew
            )
        
        return {"message": "订阅设置更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新订阅设置失败"
        )


@router.post("/cancel-subscription")
async def cancel_subscription(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """取消订阅"""
    try:
        subscription = SubscriptionService.get_user_subscription(current_user["id"])
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到订阅信息"
            )
        
        success = SubscriptionService.cancel_subscription(subscription.id)
        
        if success:
            return {"message": "订阅取消成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="订阅取消失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取消订阅失败"
        )


@router.get("/usage-stats")
async def get_usage_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取使用统计"""
    try:
        stats = SubscriptionService.get_usage_stats(current_user["id"])
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取使用统计失败"
        )


@router.post("/webhook/payment")
async def payment_webhook(
    request: Request,
    db: Session = Depends(get_db_session)
):
    """支付回调webhook"""
    try:
        # 获取原始请求体
        body = await request.body()
        headers = dict(request.headers)
        
        # 处理支付回调
        result = SubscriptionService.handle_payment_webhook(
            body=body,
            headers=headers
        )
        
        return {"status": "success", "message": "Webhook processed"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="处理支付回调失败"
        )