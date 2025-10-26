# -*- coding: utf-8 -*-
"""
支付服务
"""
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from ..models.payment import (
    Plan, Subscription, Payment, Invoice, Coupon, CouponUsage,
    PlanType, PlanDuration, PaymentStatus, PaymentMethod, 
    SubscriptionStatus, InvoiceStatus
)
from ..models.user import User
from ..database import get_db
from ..core.security import encryptor
import logging

logger = logging.getLogger(__name__)


class PaymentService:
    """支付服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 套餐管理 ====================
    
    def create_plan(
        self,
        name: str,
        description: str,
        plan_type: PlanType,
        duration: PlanDuration,
        price: Decimal,
        features: Dict[str, Any],
        limits: Dict[str, Any],
        original_price: Optional[Decimal] = None,
        currency: str = "CNY"
    ) -> Plan:
        """创建套餐"""
        plan = Plan(
            name=name,
            description=description,
            plan_type=plan_type,
            duration=duration,
            price=price,
            original_price=original_price or price,
            currency=currency,
            features=features,
            limits=limits
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan
    
    def get_plan(self, plan_id: int) -> Optional[Plan]:
        """获取套餐"""
        return self.db.query(Plan).filter(Plan.id == plan_id).first()
    
    def get_plans(
        self,
        plan_type: Optional[PlanType] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Plan]:
        """获取套餐列表"""
        query = self.db.query(Plan)
        
        if plan_type:
            query = query.filter(Plan.plan_type == plan_type)
        if is_active is not None:
            query = query.filter(Plan.is_active == is_active)
        
        return query.order_by(Plan.sort_order, Plan.id).offset(skip).limit(limit).all()
    
    def update_plan(
        self,
        plan_id: int,
        **kwargs
    ) -> Optional[Plan]:
        """更新套餐"""
        plan = self.get_plan(plan_id)
        if not plan:
            return None
        
        for key, value in kwargs.items():
            if hasattr(plan, key):
                setattr(plan, key, value)
        
        self.db.commit()
        self.db.refresh(plan)
        return plan
    
    def delete_plan(self, plan_id: int) -> bool:
        """删除套餐（软删除）"""
        plan = self.get_plan(plan_id)
        if not plan:
            return False
        
        plan.is_active = False
        self.db.commit()
        return True
    
    # ==================== 订阅管理 ====================
    
    def create_subscription(
        self,
        user_id: int,
        plan_id: int,
        start_date: Optional[datetime] = None,
        trial_days: int = 0,
        auto_renew: bool = True
    ) -> Optional[Subscription]:
        """创建订阅"""
        plan = self.get_plan(plan_id)
        if not plan:
            return None
        
        if start_date is None:
            start_date = datetime.utcnow()
        
        # 计算结束时间
        if plan.duration == PlanDuration.MONTHLY:
            end_date = start_date + timedelta(days=30)
        elif plan.duration == PlanDuration.QUARTERLY:
            end_date = start_date + timedelta(days=90)
        elif plan.duration == PlanDuration.YEARLY:
            end_date = start_date + timedelta(days=365)
        else:  # LIFETIME
            end_date = start_date + timedelta(days=36500)  # 100年
        
        # 试用期
        trial_end_date = None
        if trial_days > 0:
            trial_end_date = start_date + timedelta(days=trial_days)
        
        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
            trial_end_date=trial_end_date,
            auto_renew=auto_renew
        )
        
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
    
    def get_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """获取订阅"""
        return self.db.query(Subscription).filter(Subscription.id == subscription_id).first()
    
    def get_user_subscriptions(
        self,
        user_id: int,
        status: Optional[SubscriptionStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Subscription]:
        """获取用户订阅列表"""
        query = self.db.query(Subscription).filter(Subscription.user_id == user_id)
        
        if status:
            query = query.filter(Subscription.status == status)
        
        return query.order_by(desc(Subscription.created_at)).offset(skip).limit(limit).all()
    
    def get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        """获取用户当前活跃订阅"""
        return self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.end_date > datetime.utcnow()
            )
        ).first()
    
    def cancel_subscription(
        self,
        subscription_id: int,
        reason: Optional[str] = None,
        immediate: bool = False
    ) -> Optional[Subscription]:
        """取消订阅"""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return None
        
        subscription.auto_renew = False
        subscription.cancelled_at = datetime.utcnow()
        subscription.cancel_reason = reason
        
        if immediate:
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.end_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
    
    def renew_subscription(
        self,
        subscription_id: int,
        plan_id: Optional[int] = None
    ) -> Optional[Subscription]:
        """续费订阅"""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return None
        
        # 如果指定了新套餐，更新套餐
        if plan_id and plan_id != subscription.plan_id:
            plan = self.get_plan(plan_id)
            if not plan:
                return None
            subscription.plan_id = plan_id
        
        # 延长订阅时间
        plan = subscription.plan
        if plan.duration == PlanDuration.MONTHLY:
            subscription.end_date += timedelta(days=30)
        elif plan.duration == PlanDuration.QUARTERLY:
            subscription.end_date += timedelta(days=90)
        elif plan.duration == PlanDuration.YEARLY:
            subscription.end_date += timedelta(days=365)
        
        subscription.status = SubscriptionStatus.ACTIVE
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
    
    def check_expired_subscriptions(self) -> List[Subscription]:
        """检查过期订阅"""
        expired_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.end_date <= datetime.utcnow()
            )
        ).all()
        
        for subscription in expired_subscriptions:
            subscription.status = SubscriptionStatus.EXPIRED
        
        self.db.commit()
        return expired_subscriptions
    
    # ==================== 支付处理 ====================
    
    def create_payment(
        self,
        user_id: int,
        amount: Decimal,
        payment_method: PaymentMethod,
        subscription_id: Optional[int] = None,
        currency: str = "CNY",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Payment:
        """创建支付记录"""
        transaction_id = f"pay_{uuid.uuid4().hex[:16]}"
        
        payment = Payment(
            user_id=user_id,
            subscription_id=subscription_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            transaction_id=transaction_id,
            metadata=metadata or {}
        )
        
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def get_payment(self, payment_id: int) -> Optional[Payment]:
        """获取支付记录"""
        return self.db.query(Payment).filter(Payment.id == payment_id).first()
    
    def get_payment_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """根据交易ID获取支付记录"""
        return self.db.query(Payment).filter(Payment.transaction_id == transaction_id).first()
    
    def update_payment_status(
        self,
        payment_id: int,
        status: PaymentStatus,
        external_id: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> Optional[Payment]:
        """更新支付状态"""
        payment = self.get_payment(payment_id)
        if not payment:
            return None
        
        payment.status = status
        if external_id:
            payment.external_id = external_id
        
        if status == PaymentStatus.COMPLETED:
            payment.paid_at = datetime.utcnow()
        elif status == PaymentStatus.FAILED:
            payment.failed_at = datetime.utcnow()
            payment.failure_reason = failure_reason
        
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def process_payment_webhook(
        self,
        payment_method: PaymentMethod,
        webhook_data: Dict[str, Any]
    ) -> Optional[Payment]:
        """处理支付回调"""
        # 这里需要根据不同的支付方式实现具体的回调处理逻辑
        # 示例实现
        transaction_id = webhook_data.get('transaction_id')
        if not transaction_id:
            return None
        
        payment = self.get_payment_by_transaction_id(transaction_id)
        if not payment:
            return None
        
        # 根据回调数据更新支付状态
        if webhook_data.get('status') == 'success':
            self.update_payment_status(payment.id, PaymentStatus.COMPLETED)
            
            # 如果是订阅支付，激活订阅
            if payment.subscription_id:
                subscription = self.get_subscription(payment.subscription_id)
                if subscription:
                    subscription.status = SubscriptionStatus.ACTIVE
                    self.db.commit()
        else:
            self.update_payment_status(
                payment.id,
                PaymentStatus.FAILED,
                failure_reason=webhook_data.get('error_message')
            )
        
        return payment
    
    def refund_payment(
        self,
        payment_id: int,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Optional[Payment]:
        """退款"""
        payment = self.get_payment(payment_id)
        if not payment or payment.status != PaymentStatus.COMPLETED:
            return None
        
        refund_amount = amount or payment.amount
        if refund_amount > payment.amount:
            return None
        
        payment.status = PaymentStatus.REFUNDED
        payment.refunded_at = datetime.utcnow()
        payment.refund_amount = refund_amount
        payment.refund_reason = reason
        
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    # ==================== 优惠券管理 ====================
    
    def create_coupon(
        self,
        code: str,
        name: str,
        discount_type: str,
        discount_value: Decimal,
        valid_from: datetime,
        valid_until: datetime,
        description: Optional[str] = None,
        min_amount: Optional[Decimal] = None,
        max_discount: Optional[Decimal] = None,
        usage_limit: Optional[int] = None,
        applicable_plans: Optional[List[int]] = None
    ) -> Coupon:
        """创建优惠券"""
        coupon = Coupon(
            code=code,
            name=name,
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            min_amount=min_amount,
            max_discount=max_discount,
            usage_limit=usage_limit,
            valid_from=valid_from,
            valid_until=valid_until,
            applicable_plans=applicable_plans or []
        )
        
        self.db.add(coupon)
        self.db.commit()
        self.db.refresh(coupon)
        return coupon
    
    def get_coupon_by_code(self, code: str) -> Optional[Coupon]:
        """根据代码获取优惠券"""
        return self.db.query(Coupon).filter(Coupon.code == code).first()
    
    def validate_coupon(
        self,
        code: str,
        user_id: int,
        amount: Decimal,
        plan_id: Optional[int] = None
    ) -> tuple[bool, str, Optional[Decimal]]:
        """验证优惠券"""
        coupon = self.get_coupon_by_code(code)
        if not coupon:
            return False, "优惠券不存在", None
        
        if not coupon.is_valid:
            return False, "优惠券已失效", None
        
        # 检查最低消费金额
        if coupon.min_amount and amount < coupon.min_amount:
            return False, f"最低消费金额为 {coupon.min_amount}", None
        
        # 检查适用套餐
        if plan_id and coupon.applicable_plans and plan_id not in coupon.applicable_plans:
            return False, "优惠券不适用于当前套餐", None
        
        # 检查用户是否已使用
        usage = self.db.query(CouponUsage).filter(
            and_(
                CouponUsage.user_id == user_id,
                CouponUsage.coupon_id == coupon.id
            )
        ).first()
        
        if usage:
            return False, "优惠券已使用", None
        
        discount_amount = coupon.calculate_discount(amount)
        return True, "优惠券有效", discount_amount
    
    def use_coupon(
        self,
        code: str,
        user_id: int,
        payment_id: int,
        discount_amount: Decimal
    ) -> Optional[CouponUsage]:
        """使用优惠券"""
        coupon = self.get_coupon_by_code(code)
        if not coupon:
            return None
        
        usage = CouponUsage(
            user_id=user_id,
            coupon_id=coupon.id,
            payment_id=payment_id,
            discount_amount=discount_amount
        )
        
        coupon.used_count += 1
        
        self.db.add(usage)
        self.db.commit()
        self.db.refresh(usage)
        return usage
    
    # ==================== 发票管理 ====================
    
    def create_invoice(
        self,
        user_id: int,
        payment_id: int,
        amount: Decimal,
        tax_amount: Decimal = Decimal('0'),
        billing_info: Optional[Dict[str, str]] = None,
        items: Optional[List[Dict[str, Any]]] = None
    ) -> Invoice:
        """创建发票"""
        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        invoice = Invoice(
            user_id=user_id,
            payment_id=payment_id,
            invoice_number=invoice_number,
            amount=amount,
            tax_amount=tax_amount,
            total_amount=amount + tax_amount,
            issue_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30),
            items=items or [],
            billing_name=billing_info.get('name') if billing_info else None,
            billing_email=billing_info.get('email') if billing_info else None,
            billing_address=billing_info.get('address') if billing_info else None,
            tax_id=billing_info.get('tax_id') if billing_info else None
        )
        
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice
    
    def get_invoice(self, invoice_id: int) -> Optional[Invoice]:
        """获取发票"""
        return self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    def get_user_invoices(
        self,
        user_id: int,
        status: Optional[InvoiceStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Invoice]:
        """获取用户发票列表"""
        query = self.db.query(Invoice).filter(Invoice.user_id == user_id)
        
        if status:
            query = query.filter(Invoice.status == status)
        
        return query.order_by(desc(Invoice.created_at)).offset(skip).limit(limit).all()
    
    def update_invoice_status(
        self,
        invoice_id: int,
        status: InvoiceStatus
    ) -> Optional[Invoice]:
        """更新发票状态"""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            return None
        
        invoice.status = status
        if status == InvoiceStatus.PAID:
            invoice.paid_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(invoice)
        return invoice
    
    # ==================== 统计分析 ====================
    
    def get_payment_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取支付统计"""
        query = self.db.query(Payment)
        
        if start_date:
            query = query.filter(Payment.created_at >= start_date)
        if end_date:
            query = query.filter(Payment.created_at <= end_date)
        
        payments = query.all()
        
        total_amount = sum(p.amount for p in payments if p.status == PaymentStatus.COMPLETED)
        total_count = len(payments)
        success_count = len([p for p in payments if p.status == PaymentStatus.COMPLETED])
        
        return {
            "total_amount": float(total_amount),
            "total_count": total_count,
            "success_count": success_count,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "by_method": self._group_by_payment_method(payments),
            "by_status": self._group_by_payment_status(payments)
        }
    
    def get_subscription_statistics(self) -> Dict[str, Any]:
        """获取订阅统计"""
        subscriptions = self.db.query(Subscription).all()
        
        active_count = len([s for s in subscriptions if s.is_active])
        total_count = len(subscriptions)
        
        return {
            "total_count": total_count,
            "active_count": active_count,
            "by_status": self._group_by_subscription_status(subscriptions),
            "by_plan": self._group_by_plan(subscriptions)
        }
    
    def _group_by_payment_method(self, payments: List[Payment]) -> Dict[str, int]:
        """按支付方式分组"""
        result = {}
        for payment in payments:
            method = payment.payment_method
            result[method] = result.get(method, 0) + 1
        return result
    
    def _group_by_payment_status(self, payments: List[Payment]) -> Dict[str, int]:
        """按支付状态分组"""
        result = {}
        for payment in payments:
            status = payment.status
            result[status] = result.get(status, 0) + 1
        return result
    
    def _group_by_subscription_status(self, subscriptions: List[Subscription]) -> Dict[str, int]:
        """按订阅状态分组"""
        result = {}
        for subscription in subscriptions:
            status = subscription.status
            result[status] = result.get(status, 0) + 1
        return result
    
    def _group_by_plan(self, subscriptions: List[Subscription]) -> Dict[str, int]:
        """按套餐分组"""
        result = {}
        for subscription in subscriptions:
            plan_name = subscription.plan.name if subscription.plan else "Unknown"
            result[plan_name] = result.get(plan_name, 0) + 1
        return result