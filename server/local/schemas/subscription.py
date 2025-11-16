"""Subscription and payment related schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from ..models.subscription import (
    SubscriptionPlanTypeEnum,
    SubscriptionStatusEnum,
    PaymentMethodEnum,
    PaymentStatusEnum,
)


class SubscriptionPlanResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    plan_type: SubscriptionPlanTypeEnum
    price: Decimal
    duration_days: int
    features: Dict[str, Any] = Field(default_factory=dict)
    usage_limits: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool
    is_popular: Optional[bool] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserSubscriptionResponse(BaseModel):
    id: int
    plan: SubscriptionPlanResponse
    status: SubscriptionStatusEnum
    start_date: datetime
    end_date: datetime
    auto_renew: bool
    usage_stats: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentRecordResponse(BaseModel):
    id: int
    amount: Decimal
    currency: str
    payment_method: PaymentMethodEnum
    status: PaymentStatusEnum
    transaction_id: Optional[str]
    payment_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class CreateSubscriptionRequest(BaseModel):
    plan_id: int
    trial_days: int = Field(0, ge=0, le=30)
    auto_renew: bool = True


class UpdateSubscriptionRequest(BaseModel):
    auto_renew: Optional[bool] = None


class CancelSubscriptionRequest(BaseModel):
    reason: Optional[str] = None
    immediate: bool = False


class CreatePaymentRequest(BaseModel):
    plan_id: int
    payment_method: PaymentMethodEnum
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None


class ConfirmPaymentRequest(BaseModel):
    payment_id: int
    transaction_id: str
    payment_data: Optional[Dict[str, Any]] = None

