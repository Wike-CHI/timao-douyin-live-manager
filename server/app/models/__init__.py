# -*- coding: utf-8 -*-
"""
数据库模型包
"""

from .base import Base, BaseModel, TimestampMixin, UUIDMixin, SoftDeleteMixin
from .user import User, UserSession, UserRole, UserRoleEnum, UserStatusEnum
from .subscription import (
    SubscriptionPlan, UserSubscription, PaymentRecord,
    SubscriptionPlanTypeEnum, SubscriptionStatusEnum, 
    PaymentStatusEnum, PaymentMethodEnum
)
from .payment import (
    Plan, Subscription, Payment, Invoice, Coupon, CouponUsage,
    PlanType, PlanDuration, PaymentStatus, PaymentMethod, 
    SubscriptionStatus, InvoiceStatus
)
from .permission import Permission, RolePermission, AuditLog
from .live import LiveSession
from .live_review import LiveReviewReport
from .team import Team, TeamMember, TeamRoleEnum

__all__ = [
    # Base classes
    'Base', 'BaseModel', 'TimestampMixin', 'UUIDMixin', 'SoftDeleteMixin',
    
    # User models
    'User', 'UserSession', 'UserRole',
    'UserRoleEnum', 'UserStatusEnum',
    
    # Subscription models (new system)
    'SubscriptionPlan', 'UserSubscription', 'PaymentRecord',
    'SubscriptionPlanTypeEnum', 'SubscriptionStatusEnum',
    'PaymentStatusEnum', 'PaymentMethodEnum',
    
    # Payment models (legacy system)
    'Plan', 'Subscription', 'Payment', 'Invoice', 'Coupon', 'CouponUsage',
    'PlanType', 'PlanDuration', 'PaymentStatus', 'PaymentMethod',
    'SubscriptionStatus', 'InvoiceStatus',
    
    # Permission models
    'Permission', 'RolePermission', 'AuditLog',
    
    # Live models
    'LiveSession',
    'LiveReviewReport',
    
    # Team models
    'Team', 'TeamMember', 'TeamRoleEnum',
]
