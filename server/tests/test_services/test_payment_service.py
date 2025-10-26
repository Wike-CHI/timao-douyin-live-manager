"""
Unit tests for PaymentService.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from app.services.payment_service import PaymentService
from app.models.payment import Plan, Subscription, Payment, Invoice, Coupon, CouponUsage
from app.models.payment import PlanType, PlanDuration, PaymentStatus, PaymentMethod, SubscriptionStatus, InvoiceStatus


class TestPaymentService:
    """Test cases for PaymentService."""

    def test_create_plan(self, payment_service, db_session):
        """Test creating a new plan."""
        plan_data = {
            "name": "Premium Plan",
            "description": "Premium features",
            "price": Decimal("19.99"),
            "duration_months": 1,
            "plan_type": PlanType.PREMIUM,
            "features": {"max_streams": 10, "ai_analysis": True}
        }
        
        plan = payment_service.create_plan(**plan_data)
        
        assert plan.name == "Premium Plan"
        assert plan.price == Decimal("19.99")
        assert plan.duration_months == 1
        assert plan.plan_type == PlanType.PREMIUM
        assert plan.features["max_streams"] == 10

    def test_get_plan_by_id(self, payment_service, test_plan):
        """Test getting plan by ID."""
        plan = payment_service.get_plan_by_id(test_plan.id)
        
        assert plan is not None
        assert plan.id == test_plan.id
        assert plan.name == test_plan.name

    def test_get_plan_by_id_not_found(self, payment_service):
        """Test getting non-existent plan."""
        plan = payment_service.get_plan_by_id(999)
        
        assert plan is None

    def test_get_active_plans(self, payment_service, db_session):
        """Test getting active plans."""
        # Create active and inactive plans
        active_plan = Plan(
            name="Active Plan",
            price=Decimal("9.99"),
            duration_months=1,
            is_active=True
        )
        inactive_plan = Plan(
            name="Inactive Plan",
            price=Decimal("9.99"),
            duration_months=1,
            is_active=False
        )
        
        db_session.add_all([active_plan, inactive_plan])
        db_session.commit()
        
        plans = payment_service.get_active_plans()
        
        assert len(plans) >= 1
        assert all(plan.is_active for plan in plans)
        assert any(plan.name == "Active Plan" for plan in plans)
        assert not any(plan.name == "Inactive Plan" for plan in plans)

    def test_update_plan(self, payment_service, test_plan):
        """Test updating a plan."""
        update_data = {
            "name": "Updated Plan",
            "price": Decimal("29.99"),
            "description": "Updated description"
        }
        
        updated_plan = payment_service.update_plan(test_plan.id, update_data)
        
        assert updated_plan.name == "Updated Plan"
        assert updated_plan.price == Decimal("29.99")
        assert updated_plan.description == "Updated description"

    def test_update_plan_not_found(self, payment_service):
        """Test updating non-existent plan."""
        with pytest.raises(ValueError, match="Plan not found"):
            payment_service.update_plan(999, {"name": "Test"})

    def test_delete_plan(self, payment_service, test_plan):
        """Test deleting a plan."""
        payment_service.delete_plan(test_plan.id)
        
        # Plan should be marked as inactive
        plan = payment_service.get_plan_by_id(test_plan.id)
        assert plan.is_active is False

    def test_create_subscription(self, payment_service, test_user, test_plan):
        """Test creating a subscription."""
        subscription = payment_service.create_subscription(
            user_id=test_user.id,
            plan_id=test_plan.id
        )
        
        assert subscription.user_id == test_user.id
        assert subscription.plan_id == test_plan.id
        assert subscription.status == SubscriptionStatus.ACTIVE
        assert subscription.start_date is not None
        assert subscription.end_date is not None

    def test_create_subscription_invalid_plan(self, payment_service, test_user):
        """Test creating subscription with invalid plan."""
        with pytest.raises(ValueError, match="Plan not found"):
            payment_service.create_subscription(
                user_id=test_user.id,
                plan_id=999
            )

    def test_get_user_subscriptions(self, payment_service, test_user, test_plan, db_session):
        """Test getting user subscriptions."""
        # Create subscriptions
        subscription1 = Subscription(
            user_id=test_user.id,
            plan_id=test_plan.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30)
        )
        subscription2 = Subscription(
            user_id=test_user.id,
            plan_id=test_plan.id,
            status=SubscriptionStatus.EXPIRED,
            start_date=datetime.utcnow() - timedelta(days=60),
            end_date=datetime.utcnow() - timedelta(days=30)
        )
        
        db_session.add_all([subscription1, subscription2])
        db_session.commit()
        
        subscriptions = payment_service.get_user_subscriptions(test_user.id)
        
        assert len(subscriptions) == 2
        assert all(sub.user_id == test_user.id for sub in subscriptions)

    def test_get_active_subscription(self, payment_service, test_user, test_plan, db_session):
        """Test getting user's active subscription."""
        # Create active subscription
        subscription = Subscription(
            user_id=test_user.id,
            plan_id=test_plan.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30)
        )
        
        db_session.add(subscription)
        db_session.commit()
        
        active_sub = payment_service.get_active_subscription(test_user.id)
        
        assert active_sub is not None
        assert active_sub.status == SubscriptionStatus.ACTIVE
        assert active_sub.user_id == test_user.id

    def test_get_active_subscription_none(self, payment_service, test_user):
        """Test getting active subscription when none exists."""
        active_sub = payment_service.get_active_subscription(test_user.id)
        
        assert active_sub is None

    def test_cancel_subscription(self, payment_service, test_user, test_plan, db_session):
        """Test canceling a subscription."""
        # Create active subscription
        subscription = Subscription(
            user_id=test_user.id,
            plan_id=test_plan.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30)
        )
        
        db_session.add(subscription)
        db_session.commit()
        db_session.refresh(subscription)
        
        cancelled_sub = payment_service.cancel_subscription(subscription.id)
        
        assert cancelled_sub.status == SubscriptionStatus.CANCELLED
        assert cancelled_sub.cancelled_at is not None

    def test_cancel_subscription_not_found(self, payment_service):
        """Test canceling non-existent subscription."""
        with pytest.raises(ValueError, match="Subscription not found"):
            payment_service.cancel_subscription(999)

    def test_renew_subscription(self, payment_service, test_user, test_plan, db_session):
        """Test renewing a subscription."""
        # Create expiring subscription
        subscription = Subscription(
            user_id=test_user.id,
            plan_id=test_plan.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=datetime.utcnow() - timedelta(days=25),
            end_date=datetime.utcnow() + timedelta(days=5)
        )
        
        db_session.add(subscription)
        db_session.commit()
        db_session.refresh(subscription)
        
        renewed_sub = payment_service.renew_subscription(subscription.id)
        
        assert renewed_sub.end_date > subscription.end_date
        assert renewed_sub.status == SubscriptionStatus.ACTIVE

    def test_check_expired_subscriptions(self, payment_service, test_user, test_plan, db_session):
        """Test checking and updating expired subscriptions."""
        # Create expired subscription
        expired_sub = Subscription(
            user_id=test_user.id,
            plan_id=test_plan.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=datetime.utcnow() - timedelta(days=60),
            end_date=datetime.utcnow() - timedelta(days=1)
        )
        
        db_session.add(expired_sub)
        db_session.commit()
        
        expired_count = payment_service.check_expired_subscriptions()
        
        assert expired_count >= 1
        
        # Refresh and check status
        db_session.refresh(expired_sub)
        assert expired_sub.status == SubscriptionStatus.EXPIRED

    def test_create_payment(self, payment_service, test_user, test_plan):
        """Test creating a payment."""
        payment_data = {
            "user_id": test_user.id,
            "plan_id": test_plan.id,
            "amount": test_plan.price,
            "payment_method": PaymentMethod.CREDIT_CARD,
            "currency": "USD"
        }
        
        payment = payment_service.create_payment(**payment_data)
        
        assert payment.user_id == test_user.id
        assert payment.plan_id == test_plan.id
        assert payment.amount == test_plan.price
        assert payment.status == PaymentStatus.PENDING
        assert payment.payment_method == PaymentMethod.CREDIT_CARD

    def test_get_payment_by_id(self, payment_service, test_user, test_plan, db_session):
        """Test getting payment by ID."""
        payment = Payment(
            user_id=test_user.id,
            plan_id=test_plan.id,
            amount=test_plan.price,
            payment_method=PaymentMethod.CREDIT_CARD,
            status=PaymentStatus.COMPLETED
        )
        
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)
        
        retrieved_payment = payment_service.get_payment_by_id(payment.id)
        
        assert retrieved_payment is not None
        assert retrieved_payment.id == payment.id
        assert retrieved_payment.amount == payment.amount

    def test_get_user_payments(self, payment_service, test_user, test_plan, db_session):
        """Test getting user payments."""
        # Create multiple payments
        for i in range(3):
            payment = Payment(
                user_id=test_user.id,
                plan_id=test_plan.id,
                amount=Decimal("9.99"),
                payment_method=PaymentMethod.CREDIT_CARD,
                status=PaymentStatus.COMPLETED
            )
            db_session.add(payment)
        
        db_session.commit()
        
        payments = payment_service.get_user_payments(test_user.id)
        
        assert len(payments) == 3
        assert all(payment.user_id == test_user.id for payment in payments)

    def test_update_payment_status(self, payment_service, test_user, test_plan, db_session):
        """Test updating payment status."""
        payment = Payment(
            user_id=test_user.id,
            plan_id=test_plan.id,
            amount=test_plan.price,
            payment_method=PaymentMethod.CREDIT_CARD,
            status=PaymentStatus.PENDING
        )
        
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)
        
        updated_payment = payment_service.update_payment_status(
            payment.id, 
            PaymentStatus.COMPLETED,
            transaction_id="txn_123456"
        )
        
        assert updated_payment.status == PaymentStatus.COMPLETED
        assert updated_payment.transaction_id == "txn_123456"
        assert updated_payment.paid_at is not None

    def test_process_payment_webhook(self, payment_service, test_user, test_plan, db_session):
        """Test processing payment webhook."""
        payment = Payment(
            user_id=test_user.id,
            plan_id=test_plan.id,
            amount=test_plan.price,
            payment_method=PaymentMethod.CREDIT_CARD,
            status=PaymentStatus.PENDING
        )
        
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)
        
        webhook_data = {
            "payment_id": payment.id,
            "status": "completed",
            "transaction_id": "webhook_txn_123"
        }
        
        result = payment_service.process_payment_webhook(webhook_data)
        
        assert result is True
        
        # Refresh payment
        db_session.refresh(payment)
        assert payment.status == PaymentStatus.COMPLETED
        assert payment.transaction_id == "webhook_txn_123"

    def test_refund_payment(self, payment_service, test_user, test_plan, db_session):
        """Test refunding a payment."""
        payment = Payment(
            user_id=test_user.id,
            plan_id=test_plan.id,
            amount=test_plan.price,
            payment_method=PaymentMethod.CREDIT_CARD,
            status=PaymentStatus.COMPLETED,
            paid_at=datetime.utcnow()
        )
        
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)
        
        refunded_payment = payment_service.refund_payment(
            payment.id,
            reason="Customer request"
        )
        
        assert refunded_payment.status == PaymentStatus.REFUNDED
        assert refunded_payment.refund_reason == "Customer request"
        assert refunded_payment.refunded_at is not None

    def test_create_coupon(self, payment_service):
        """Test creating a coupon."""
        coupon_data = {
            "code": "SAVE20",
            "discount_type": "percentage",
            "discount_value": Decimal("20.0"),
            "usage_limit": 100,
            "expires_at": datetime.utcnow() + timedelta(days=30)
        }
        
        coupon = payment_service.create_coupon(**coupon_data)
        
        assert coupon.code == "SAVE20"
        assert coupon.discount_type == "percentage"
        assert coupon.discount_value == Decimal("20.0")
        assert coupon.usage_limit == 100
        assert coupon.is_active is True

    def test_get_coupon_by_code(self, payment_service, test_coupon):
        """Test getting coupon by code."""
        coupon = payment_service.get_coupon_by_code(test_coupon.code)
        
        assert coupon is not None
        assert coupon.code == test_coupon.code
        assert coupon.discount_value == test_coupon.discount_value

    def test_validate_coupon_valid(self, payment_service, test_coupon):
        """Test validating a valid coupon."""
        is_valid, message = payment_service.validate_coupon(test_coupon.code)
        
        assert is_valid is True
        assert message == "Coupon is valid"

    def test_validate_coupon_not_found(self, payment_service):
        """Test validating non-existent coupon."""
        is_valid, message = payment_service.validate_coupon("INVALID")
        
        assert is_valid is False
        assert "not found" in message

    def test_validate_coupon_expired(self, payment_service, db_session):
        """Test validating expired coupon."""
        expired_coupon = Coupon(
            code="EXPIRED",
            discount_type="percentage",
            discount_value=Decimal("10.0"),
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        
        db_session.add(expired_coupon)
        db_session.commit()
        
        is_valid, message = payment_service.validate_coupon("EXPIRED")
        
        assert is_valid is False
        assert "expired" in message

    def test_use_coupon(self, payment_service, test_user, test_coupon, db_session):
        """Test using a coupon."""
        payment = Payment(
            user_id=test_user.id,
            amount=Decimal("10.0"),
            payment_method=PaymentMethod.CREDIT_CARD,
            status=PaymentStatus.PENDING
        )
        
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)
        
        usage = payment_service.use_coupon(test_coupon.code, test_user.id, payment.id)
        
        assert usage is not None
        assert usage.coupon_id == test_coupon.id
        assert usage.user_id == test_user.id
        assert usage.payment_id == payment.id

    def test_calculate_discount(self, payment_service, test_coupon):
        """Test calculating discount amount."""
        original_amount = Decimal("100.0")
        
        discount = payment_service.calculate_discount(test_coupon, original_amount)
        
        # test_coupon has 10% discount
        expected_discount = original_amount * (test_coupon.discount_value / 100)
        assert discount == expected_discount

    def test_create_invoice(self, payment_service, test_user, test_plan, db_session):
        """Test creating an invoice."""
        payment = Payment(
            user_id=test_user.id,
            plan_id=test_plan.id,
            amount=test_plan.price,
            payment_method=PaymentMethod.CREDIT_CARD,
            status=PaymentStatus.COMPLETED
        )
        
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)
        
        invoice = payment_service.create_invoice(payment.id)
        
        assert invoice.payment_id == payment.id
        assert invoice.user_id == test_user.id
        assert invoice.amount == payment.amount
        assert invoice.status == InvoiceStatus.GENERATED

    def test_get_user_invoices(self, payment_service, test_user, test_plan, db_session):
        """Test getting user invoices."""
        # Create payment and invoice
        payment = Payment(
            user_id=test_user.id,
            plan_id=test_plan.id,
            amount=test_plan.price,
            payment_method=PaymentMethod.CREDIT_CARD,
            status=PaymentStatus.COMPLETED
        )
        
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)
        
        invoice = Invoice(
            payment_id=payment.id,
            user_id=test_user.id,
            amount=payment.amount,
            status=InvoiceStatus.GENERATED
        )
        
        db_session.add(invoice)
        db_session.commit()
        
        invoices = payment_service.get_user_invoices(test_user.id)
        
        assert len(invoices) == 1
        assert invoices[0].user_id == test_user.id

    def test_get_payment_stats(self, payment_service, test_user, test_plan, db_session):
        """Test getting payment statistics."""
        # Create some payments
        for i in range(3):
            payment = Payment(
                user_id=test_user.id,
                plan_id=test_plan.id,
                amount=Decimal("10.0"),
                payment_method=PaymentMethod.CREDIT_CARD,
                status=PaymentStatus.COMPLETED,
                paid_at=datetime.utcnow()
            )
            db_session.add(payment)
        
        db_session.commit()
        
        stats = payment_service.get_payment_stats()
        
        assert "total_payments" in stats
        assert "total_revenue" in stats
        assert "successful_payments" in stats
        assert "failed_payments" in stats
        assert stats["total_payments"] >= 3

    def test_get_subscription_stats(self, payment_service, test_user, test_plan, db_session):
        """Test getting subscription statistics."""
        # Create subscriptions with different statuses
        statuses = [SubscriptionStatus.ACTIVE, SubscriptionStatus.EXPIRED, SubscriptionStatus.CANCELLED]
        
        for status in statuses:
            subscription = Subscription(
                user_id=test_user.id,
                plan_id=test_plan.id,
                status=status,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30)
            )
            db_session.add(subscription)
        
        db_session.commit()
        
        stats = payment_service.get_subscription_stats()
        
        assert "total_subscriptions" in stats
        assert "active_subscriptions" in stats
        assert "expired_subscriptions" in stats
        assert "cancelled_subscriptions" in stats
        assert stats["total_subscriptions"] >= 3