# -*- coding: utf-8 -*-
"""
订阅和支付相关数据库模型
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Enum, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel, UUIDMixin


class SubscriptionPlanTypeEnum(enum.Enum):
    """订阅套餐类型枚举"""
    FREE = "free"           # 免费版
    BASIC = "basic"         # 基础版
    PREMIUM = "premium"     # 高级版
    ENTERPRISE = "enterprise"  # 企业版


class SubscriptionStatusEnum(enum.Enum):
    """订阅状态枚举"""
    ACTIVE = "active"       # 激活
    EXPIRED = "expired"     # 过期
    CANCELLED = "cancelled" # 取消
    SUSPENDED = "suspended" # 暂停


class PaymentStatusEnum(enum.Enum):
    """支付状态枚举"""
    PENDING = "pending"     # 待支付
    PAID = "paid"          # 已支付
    FAILED = "failed"      # 支付失败
    REFUNDED = "refunded"  # 已退款
    CANCELLED = "cancelled" # 已取消


class PaymentMethodEnum(enum.Enum):
    """支付方式枚举"""
    ALIPAY = "alipay"      # 支付宝
    WECHAT = "wechat"      # 微信支付
    BANK_CARD = "bank_card" # 银行卡
    PAYPAL = "paypal"      # PayPal
    STRIPE = "stripe"      # Stripe


class SubscriptionPlan(BaseModel, UUIDMixin):
    """订阅套餐模型"""
    
    __tablename__ = "subscription_plans"
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="套餐名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, nullable=True, comment="套餐描述")
    plan_type = Column(Enum(SubscriptionPlanTypeEnum), nullable=False, comment="套餐类型")
    
    # 价格信息
    price = Column(Numeric(10, 2), nullable=False, comment="价格")
    currency = Column(String(3), default="CNY", nullable=False, comment="货币")
    billing_cycle = Column(Integer, default=30, nullable=False, comment="计费周期（天）")
    
    # 功能限制
    max_streams = Column(Integer, nullable=True, comment="最大直播间数量")
    max_storage_gb = Column(Integer, nullable=True, comment="最大存储空间(GB)")
    max_ai_requests = Column(Integer, nullable=True, comment="最大AI请求数/月")
    max_export_count = Column(Integer, nullable=True, comment="最大导出次数/月")
    
    # 功能权限
    features = Column(Text, nullable=True, comment="功能列表(JSON)")
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    is_popular = Column(Boolean, default=False, nullable=False, comment="是否热门")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序")
    
    # 关联关系
    subscriptions = relationship("UserSubscription", back_populates="plan")
    
    # 索引
    __table_args__ = (
        Index('idx_plan_type', 'plan_type'),
        Index('idx_plan_active', 'is_active'),
        Index('idx_plan_sort', 'sort_order'),
    )
    
    def get_features_list(self) -> list:
        """获取功能列表"""
        if self.features:
            import json
            return json.loads(self.features)
        return []
    
    def set_features_list(self, features: list) -> None:
        """设置功能列表"""
        import json
        self.features = json.dumps(features, ensure_ascii=False)


class UserSubscription(BaseModel, UUIDMixin):
    """用户订阅模型"""
    
    __tablename__ = "user_subscriptions"
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment="用户ID")
    plan_id = Column(Integer, ForeignKey('subscription_plans.id'), nullable=False, comment="套餐ID")
    
    # 订阅信息
    status = Column(Enum(SubscriptionStatusEnum), default=SubscriptionStatusEnum.ACTIVE, nullable=False, comment="订阅状态")
    starts_at = Column(DateTime, nullable=False, comment="开始时间")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    
    # 自动续费
    auto_renew = Column(Boolean, default=False, nullable=False, comment="是否自动续费")
    next_billing_date = Column(DateTime, nullable=True, comment="下次计费日期")
    
    # 使用统计
    streams_used = Column(Integer, default=0, nullable=False, comment="已使用直播间数量")
    storage_used_gb = Column(Numeric(10, 2), default=0, nullable=False, comment="已使用存储空间(GB)")
    ai_requests_used = Column(Integer, default=0, nullable=False, comment="已使用AI请求数")
    export_count_used = Column(Integer, default=0, nullable=False, comment="已使用导出次数")
    
    # 取消信息
    cancelled_at = Column(DateTime, nullable=True, comment="取消时间")
    cancel_reason = Column(Text, nullable=True, comment="取消原因")
    
    # 关联关系
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    payments = relationship("PaymentRecord", back_populates="subscription")
    
    # 索引
    __table_args__ = (
        Index('idx_subscription_user_id', 'user_id'),
        Index('idx_subscription_plan_id', 'plan_id'),
        Index('idx_subscription_status', 'status'),
        Index('idx_subscription_expires_at', 'expires_at'),
        Index('idx_subscription_auto_renew', 'auto_renew'),
    )
    
    def is_active(self) -> bool:
        """检查订阅是否激活"""
        return (self.status == SubscriptionStatusEnum.ACTIVE and 
                datetime.utcnow() < self.expires_at)
    
    def is_expired(self) -> bool:
        """检查订阅是否过期"""
        return datetime.utcnow() >= self.expires_at
    
    def extend_subscription(self, days: int) -> None:
        """延长订阅"""
        if self.is_expired():
            self.expires_at = datetime.utcnow() + timedelta(days=days)
        else:
            self.expires_at += timedelta(days=days)
        
        if self.auto_renew:
            self.next_billing_date = self.expires_at
    
    def cancel_subscription(self, reason: str = None) -> None:
        """取消订阅"""
        self.status = SubscriptionStatusEnum.CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.cancel_reason = reason
        self.auto_renew = False
        self.next_billing_date = None
    
    def can_use_feature(self, feature: str) -> bool:
        """检查是否可以使用某个功能"""
        if not self.is_active():
            return False
        
        features = self.plan.get_features_list()
        return feature in features
    
    def check_usage_limit(self, resource: str) -> dict:
        """检查资源使用限制"""
        result = {"can_use": True, "used": 0, "limit": None, "remaining": None}
        
        if resource == "streams":
            result["used"] = self.streams_used
            result["limit"] = self.plan.max_streams
            if self.plan.max_streams:
                result["remaining"] = max(0, self.plan.max_streams - self.streams_used)
                result["can_use"] = self.streams_used < self.plan.max_streams
        
        elif resource == "storage":
            result["used"] = float(self.storage_used_gb)
            result["limit"] = self.plan.max_storage_gb
            if self.plan.max_storage_gb:
                result["remaining"] = max(0, self.plan.max_storage_gb - float(self.storage_used_gb))
                result["can_use"] = float(self.storage_used_gb) < self.plan.max_storage_gb
        
        elif resource == "ai_requests":
            result["used"] = self.ai_requests_used
            result["limit"] = self.plan.max_ai_requests
            if self.plan.max_ai_requests:
                result["remaining"] = max(0, self.plan.max_ai_requests - self.ai_requests_used)
                result["can_use"] = self.ai_requests_used < self.plan.max_ai_requests
        
        elif resource == "exports":
            result["used"] = self.export_count_used
            result["limit"] = self.plan.max_export_count
            if self.plan.max_export_count:
                result["remaining"] = max(0, self.plan.max_export_count - self.export_count_used)
                result["can_use"] = self.export_count_used < self.plan.max_export_count
        
        return result


class PaymentRecord(BaseModel, UUIDMixin):
    """支付记录模型"""
    
    __tablename__ = "payment_records"
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment="用户ID")
    subscription_id = Column(Integer, ForeignKey('user_subscriptions.id'), nullable=True, comment="订阅ID")
    
    # 支付信息
    order_no = Column(String(100), unique=True, nullable=False, comment="订单号")
    amount = Column(Numeric(10, 2), nullable=False, comment="支付金额")
    currency = Column(String(3), default="CNY", nullable=False, comment="货币")
    
    # 支付方式和状态
    payment_method = Column(Enum(PaymentMethodEnum), nullable=False, comment="支付方式")
    status = Column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.PENDING, nullable=False, comment="支付状态")
    
    # 第三方支付信息
    third_party_order_id = Column(String(200), nullable=True, comment="第三方订单ID")
    third_party_response = Column(Text, nullable=True, comment="第三方响应(JSON)")
    
    # 时间信息
    paid_at = Column(DateTime, nullable=True, comment="支付时间")
    refunded_at = Column(DateTime, nullable=True, comment="退款时间")
    
    # 描述信息
    description = Column(Text, nullable=True, comment="支付描述")
    refund_reason = Column(Text, nullable=True, comment="退款原因")
    
    # 发票信息
    invoice_requested = Column(Boolean, default=False, nullable=False, comment="是否需要发票")
    invoice_title = Column(String(200), nullable=True, comment="发票抬头")
    invoice_tax_id = Column(String(50), nullable=True, comment="税号")
    invoice_issued = Column(Boolean, default=False, nullable=False, comment="是否已开发票")
    invoice_issued_at = Column(DateTime, nullable=True, comment="开票时间")
    
    # 关联关系
    user = relationship("User")
    subscription = relationship("UserSubscription", back_populates="payments")
    
    # 索引
    __table_args__ = (
        Index('idx_payment_user_id', 'user_id'),
        Index('idx_payment_order_no', 'order_no'),
        Index('idx_payment_status', 'status'),
        Index('idx_payment_method', 'payment_method'),
        Index('idx_payment_paid_at', 'paid_at'),
    )
    
    def mark_as_paid(self, third_party_order_id: str = None, response_data: dict = None) -> None:
        """标记为已支付"""
        self.status = PaymentStatusEnum.PAID
        self.paid_at = datetime.utcnow()
        if third_party_order_id:
            self.third_party_order_id = third_party_order_id
        if response_data:
            import json
            self.third_party_response = json.dumps(response_data, ensure_ascii=False)
    
    def mark_as_failed(self, response_data: dict = None) -> None:
        """标记为支付失败"""
        self.status = PaymentStatusEnum.FAILED
        if response_data:
            import json
            self.third_party_response = json.dumps(response_data, ensure_ascii=False)
    
    def mark_as_refunded(self, reason: str = None) -> None:
        """标记为已退款"""
        self.status = PaymentStatusEnum.REFUNDED
        self.refunded_at = datetime.utcnow()
        if reason:
            self.refund_reason = reason
    
    def request_invoice(self, title: str, tax_id: str = None) -> None:
        """申请发票"""
        self.invoice_requested = True
        self.invoice_title = title
        self.invoice_tax_id = tax_id
    
    def issue_invoice(self) -> None:
        """开具发票"""
        self.invoice_issued = True
        self.invoice_issued_at = datetime.utcnow()