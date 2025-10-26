# -*- coding: utf-8 -*-
"""
支付相关数据模型
"""
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Numeric, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel


class PlanType(str, Enum):
    """套餐类型"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class PlanDuration(str, Enum):
    """套餐时长"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"


class PaymentStatus(str, Enum):
    """支付状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    """支付方式"""
    ALIPAY = "alipay"
    WECHAT = "wechat"
    STRIPE = "stripe"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"


class SubscriptionStatus(str, Enum):
    """订阅状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class InvoiceStatus(str, Enum):
    """发票状态"""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Plan(BaseModel):
    """套餐模型"""
    __tablename__ = "plans"

    name = Column(String(100), nullable=False, comment="套餐名称")
    description = Column(Text, comment="套餐描述")
    plan_type = Column(String(20), nullable=False, comment="套餐类型")
    duration = Column(String(20), nullable=False, comment="套餐时长")
    price = Column(Numeric(10, 2), nullable=False, comment="价格")
    original_price = Column(Numeric(10, 2), comment="原价")
    currency = Column(String(3), default="CNY", comment="货币")
    features = Column(JSON, comment="功能特性")
    limits = Column(JSON, comment="使用限制")
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序")
    
    # 关联关系
    subscriptions = relationship("Subscription", back_populates="plan")
    
    def __repr__(self):
        return f"<Plan(name='{self.name}', type='{self.plan_type}', price={self.price})>"


class Subscription(BaseModel):
    """订阅模型"""
    __tablename__ = "subscriptions"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False, comment="套餐ID")
    status = Column(String(20), default=SubscriptionStatus.ACTIVE, comment="订阅状态")
    start_date = Column(DateTime, nullable=False, comment="开始时间")
    end_date = Column(DateTime, nullable=False, comment="结束时间")
    auto_renew = Column(Boolean, default=True, comment="自动续费")
    trial_end_date = Column(DateTime, comment="试用结束时间")
    cancelled_at = Column(DateTime, comment="取消时间")
    cancel_reason = Column(String(500), comment="取消原因")
    extra_data = Column(JSON, comment="元数据")
    
    # 关联关系
    user = relationship("User", back_populates="payment_subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")
    
    @property
    def is_active(self) -> bool:
        """是否为活跃订阅"""
        return (
            self.status == SubscriptionStatus.ACTIVE and
            self.end_date > datetime.utcnow()
        )
    
    @property
    def is_trial(self) -> bool:
        """是否为试用期"""
        return (
            self.trial_end_date is not None and
            datetime.utcnow() < self.trial_end_date
        )
    
    @property
    def days_remaining(self) -> int:
        """剩余天数"""
        if self.end_date > datetime.utcnow():
            return (self.end_date - datetime.utcnow()).days
        return 0
    
    def __repr__(self):
        return f"<Subscription(user_id={self.user_id}, plan_id={self.plan_id}, status='{self.status}')>"


class Payment(BaseModel):
    """支付记录模型"""
    __tablename__ = "payments"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), comment="订阅ID")
    amount = Column(Numeric(10, 2), nullable=False, comment="支付金额")
    currency = Column(String(3), default="CNY", comment="货币")
    payment_method = Column(String(20), nullable=False, comment="支付方式")
    status = Column(String(20), default=PaymentStatus.PENDING, comment="支付状态")
    transaction_id = Column(String(100), unique=True, comment="交易ID")
    external_id = Column(String(100), comment="外部交易ID")
    payment_url = Column(String(500), comment="支付链接")
    paid_at = Column(DateTime, comment="支付时间")
    failed_at = Column(DateTime, comment="失败时间")
    failure_reason = Column(String(500), comment="失败原因")
    refunded_at = Column(DateTime, comment="退款时间")
    refund_amount = Column(Numeric(10, 2), comment="退款金额")
    refund_reason = Column(String(500), comment="退款原因")
    extra_data = Column(JSON, comment="元数据")
    
    # 关联关系
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payment", uselist=False)
    
    def __repr__(self):
        return f"<Payment(user_id={self.user_id}, amount={self.amount}, status='{self.status}')>"


class Invoice(BaseModel):
    """发票模型"""
    __tablename__ = "invoices"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    payment_id = Column(Integer, ForeignKey("payments.id"), comment="支付ID")
    invoice_number = Column(String(50), unique=True, nullable=False, comment="发票号码")
    status = Column(String(20), default=InvoiceStatus.DRAFT, comment="发票状态")
    amount = Column(Numeric(10, 2), nullable=False, comment="发票金额")
    tax_amount = Column(Numeric(10, 2), default=0, comment="税额")
    total_amount = Column(Numeric(10, 2), nullable=False, comment="总金额")
    currency = Column(String(3), default="CNY", comment="货币")
    issue_date = Column(DateTime, nullable=False, comment="开票日期")
    due_date = Column(DateTime, comment="到期日期")
    paid_date = Column(DateTime, comment="支付日期")
    
    # 发票信息
    billing_name = Column(String(200), comment="开票名称")
    billing_email = Column(String(100), comment="开票邮箱")
    billing_address = Column(Text, comment="开票地址")
    tax_id = Column(String(50), comment="税号")
    
    # 发票内容
    items = Column(JSON, comment="发票项目")
    notes = Column(Text, comment="备注")
    
    # 关联关系
    user = relationship("User", back_populates="invoices")
    payment = relationship("Payment", back_populates="invoice")
    
    def __repr__(self):
        return f"<Invoice(number='{self.invoice_number}', amount={self.total_amount}, status='{self.status}')>"


class Coupon(BaseModel):
    """优惠券模型"""
    __tablename__ = "coupons"

    code = Column(String(50), unique=True, nullable=False, comment="优惠券代码")
    name = Column(String(100), nullable=False, comment="优惠券名称")
    description = Column(Text, comment="描述")
    discount_type = Column(String(20), nullable=False, comment="折扣类型: percentage, fixed")
    discount_value = Column(Numeric(10, 2), nullable=False, comment="折扣值")
    min_amount = Column(Numeric(10, 2), comment="最低消费金额")
    max_discount = Column(Numeric(10, 2), comment="最大折扣金额")
    usage_limit = Column(Integer, comment="使用次数限制")
    used_count = Column(Integer, default=0, comment="已使用次数")
    valid_from = Column(DateTime, nullable=False, comment="有效期开始")
    valid_until = Column(DateTime, nullable=False, comment="有效期结束")
    is_active = Column(Boolean, default=True, comment="是否启用")
    applicable_plans = Column(JSON, comment="适用套餐")
    
    # 关联关系
    usages = relationship("CouponUsage", back_populates="coupon")
    
    @property
    def is_valid(self) -> bool:
        """是否有效"""
        now = datetime.utcnow()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.usage_limit is None or self.used_count < self.usage_limit)
        )
    
    def calculate_discount(self, amount: Decimal) -> Decimal:
        """计算折扣金额"""
        if not self.is_valid or (self.min_amount and amount < self.min_amount):
            return Decimal('0')
        
        if self.discount_type == "percentage":
            discount = amount * (self.discount_value / 100)
        else:  # fixed
            discount = self.discount_value
        
        if self.max_discount:
            discount = min(discount, self.max_discount)
        
        return min(discount, amount)
    
    def __repr__(self):
        return f"<Coupon(code='{self.code}', discount={self.discount_value})>"


class CouponUsage(BaseModel):
    """优惠券使用记录"""
    __tablename__ = "coupon_usages"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=False, comment="优惠券ID")
    payment_id = Column(Integer, ForeignKey("payments.id"), comment="支付ID")
    discount_amount = Column(Numeric(10, 2), nullable=False, comment="折扣金额")
    used_at = Column(DateTime, default=datetime.utcnow, comment="使用时间")
    
    # 关联关系
    user = relationship("User")
    coupon = relationship("Coupon", back_populates="usages")
    payment = relationship("Payment")
    
    def __repr__(self):
        return f"<CouponUsage(user_id={self.user_id}, coupon_id={self.coupon_id}, discount={self.discount_amount})>"