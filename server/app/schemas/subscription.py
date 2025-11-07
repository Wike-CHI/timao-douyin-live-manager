# -*- coding: utf-8 -*-
"""
订阅和支付相关数据模型
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from ..schemas.common import BaseResponse, PaginationParams, PaginatedResponse


class SubscriptionPlanResponse(BaseModel):
    """订阅套餐响应"""
    id: int
    name: str
    description: Optional[str] = None
    plan_type: str
    price: Decimal  # 统一使用 Decimal 避免精度问题
    duration_days: int
    features: Dict[str, Any]
    usage_limits: Dict[str, Any]
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
    usage_stats: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentRecordResponse(BaseModel):
    """支付记录响应"""
    id: int
    amount: Decimal  # 统一使用 Decimal
    currency: str
    payment_method: str
    status: str
    transaction_id: Optional[str] = None
    payment_data: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreatePaymentRequest(BaseModel):
    """创建支付请求"""
    plan_id: int
    payment_method: str  # PaymentMethodEnum
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None


class ConfirmPaymentRequest(BaseModel):
    """确认支付请求"""
    payment_id: int
    transaction_id: str
    payment_data: Optional[Dict[str, Any]] = None


class UpdateSubscriptionRequest(BaseModel):
    """更新订阅请求"""
    auto_renew: Optional[bool] = None

