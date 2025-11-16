# -*- coding: utf-8 -*-
"""
订阅和支付API路由
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from server.app.database import get_db_session
from server.app.api.auth import get_current_user
from server.app.services.subscription_service import SubscriptionService
from server.utils.service_logger import log_subscription_event
from server.app.schemas import (
    SubscriptionPlanResponse,
    UserSubscriptionResponse,
    PaymentRecordResponse,
    CreatePaymentRequest,
    ConfirmPaymentRequest,
    UpdateSubscriptionRequest,
)
from server.app.schemas.common import BaseResponse
from server.app.utils.api import success_response, handle_service_error


# 创建路由器
router = APIRouter(prefix="/api/subscription", tags=["订阅"])


# API 路由
@router.get("/plans", response_model=BaseResponse[List[SubscriptionPlanResponse]])
async def get_subscription_plans(
    active_only: bool = True,
    db: Session = Depends(get_db_session)
):
    """获取订阅套餐列表"""
    try:
        import json
        from server.app.models.subscription import SubscriptionPlan
        
        # 直接查询数据库
        query = db.query(SubscriptionPlan)
        if active_only:
            query = query.filter(SubscriptionPlan.is_active == True)
        
        plans = query.order_by(SubscriptionPlan.price).all()
        
        responses = []
        for plan in plans:
            usage_limits = {
                "max_streams": plan.max_streams,
                "max_storage_gb": plan.max_storage_gb,
                "max_ai_requests": plan.max_ai_requests,
                "max_export_count": plan.max_export_count,
            }
            if isinstance(plan.features, str):
                try:
                    features = json.loads(plan.features)
                except json.JSONDecodeError:
                    features = {}
            else:
                features = plan.features or {}
            responses.append(
                SubscriptionPlanResponse(
                    id=plan.id,
                    name=plan.name,
                    description=plan.description,
                    plan_type=plan.plan_type,
                    price=plan.price,
                    duration_days=plan.billing_cycle,
                    features=features,
                    usage_limits=usage_limits,
                    is_active=plan.is_active,
                    created_at=plan.created_at,
                )
            )

        return success_response(responses)
        
    except Exception as e:
        import logging
        logging.error(f"获取套餐列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取套餐列表失败: {str(e)}"
        )


@router.get("/my-subscription", response_model=BaseResponse[Optional[UserSubscriptionResponse]])
@router.get("/current", response_model=BaseResponse[Optional[UserSubscriptionResponse]])  # 别名端点
async def get_my_subscription(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取当前用户的订阅信息"""
    try:
        subscription = SubscriptionService.get_user_subscription(current_user["id"])

        if not subscription:
            return success_response(None, message="暂无订阅")

        plan = subscription.plan
        if isinstance(plan.features, str):
            try:
                plan_features = json.loads(plan.features)
            except json.JSONDecodeError:
                plan_features = {}
        else:
            plan_features = plan.features or {}

        plan_response = SubscriptionPlanResponse(
            id=plan.id,
            name=plan.name,
            description=plan.description,
            plan_type=plan.plan_type,
            price=plan.price,
            duration_days=getattr(plan, "duration_days", getattr(plan, "billing_cycle", 0)),
            features=plan_features,
            usage_limits=plan.usage_limits or {},
            is_active=plan.is_active,
            created_at=plan.created_at,
        )

        response = UserSubscriptionResponse(
            id=subscription.id,
            plan=plan_response,
            status=subscription.status,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            auto_renew=subscription.auto_renew,
            usage_stats=subscription.usage_stats or {},
            created_at=subscription.created_at,
        )

        return success_response(response)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订阅信息失败"
        )


@router.post("/create-payment", response_model=BaseResponse[Dict[str, Any]])
async def create_payment(
    request: CreatePaymentRequest,
    req: Request,
    current_user: dict = Depends(get_current_user),
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
        
        log_subscription_event("创建支付订单", user_id=current_user["id"], plan_id=request.plan_id, 
                               payment_id=payment.id, amount=payment.amount, payment_method=request.payment_method.value)
        
        return success_response(
            {
                "payment_id": payment.id,
                "amount": payment.amount,
                "currency": payment.currency,
                "payment_method": payment.payment_method.value,
                "payment_url": payment.payment_data.get("payment_url"),
                "qr_code": payment.payment_data.get("qr_code"),
                "expires_at": payment.payment_data.get("expires_at"),
            },
            message="支付订单创建成功",
        )

    except ValueError as exc:
        handle_service_error(exc, {}, default_message=str(exc), default_status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        handle_service_error(exc, {}, default_message="创建支付订单失败", default_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/confirm-payment", response_model=BaseResponse[Dict[str, Any]])
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
            from server.app.models.payment import Payment
            payment = db.query(Payment).filter(Payment.id == request.payment_id).first()
            if payment:
                log_subscription_event(
                    "支付确认成功",
                    user_id=payment.user_id,
                    payment_id=payment.id,
                    transaction_id=request.transaction_id,
                    amount=payment.amount,
                )
            return success_response({"payment_id": request.payment_id}, message="支付确认成功")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="支付确认失败",
        )

    except ValueError as exc:
        handle_service_error(exc, {}, default_message=str(exc), default_status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        handle_service_error(exc, {}, default_message="支付确认失败", default_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/payment-history", response_model=BaseResponse[List[PaymentRecordResponse]])
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
        
        records = [
            PaymentRecordResponse(
                id=payment.id,
                amount=payment.amount,
                currency=payment.currency,
                payment_method=payment.payment_method,
                status=payment.status,
                transaction_id=payment.transaction_id,
                payment_data=payment.payment_data,
                created_at=payment.created_at,
            )
            for payment in payments
        ]

        return success_response(records)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取支付历史失败"
        )


@router.put("/update-subscription", response_model=BaseResponse[Dict[str, Any]])
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
            log_subscription_event("更新订阅设置", user_id=current_user["id"], subscription_id=subscription.id, 
                                   auto_renew=request.auto_renew)
        
        return success_response({"auto_renew": request.auto_renew}, message="订阅设置更新成功")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新订阅设置失败"
        )


@router.post("/cancel-subscription", response_model=BaseResponse[Dict[str, Any]])
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
            log_subscription_event(
                "取消订阅",
                user_id=current_user["id"],
                subscription_id=subscription.id,
                plan_name=subscription.plan.name,
            )
            return success_response({"cancelled": True}, message="订阅取消成功")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订阅取消失败",
        )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取消订阅失败"
        )


@router.get("/usage-stats", response_model=BaseResponse[Dict[str, Any]])
async def get_usage_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取使用统计"""
    try:
        stats = SubscriptionService.get_usage_stats(current_user["id"])
        return success_response(stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取使用统计失败"
        )


@router.post("/webhook/payment", response_model=BaseResponse[Dict[str, Any]])
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

        return success_response({"webhook": "processed", "result": result})

    except Exception as exc:
        handle_service_error(exc, {}, default_message="处理支付回调失败", default_status=status.HTTP_500_INTERNAL_SERVER_ERROR)