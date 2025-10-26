"""
支付API集成测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.payment import Plan, Subscription, Payment, Coupon, Invoice


class TestPlanManagement:
    """计划管理测试"""
    
    def test_get_plans_success(self, client: TestClient):
        """测试获取计划列表"""
        response = client.get("/api/payment/plans")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    def test_get_plan_by_id_success(self, client: TestClient, test_plan):
        """测试根据ID获取计划"""
        response = client.get(f"/api/payment/plans/{test_plan.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_plan.id
        assert data["name"] == test_plan.name
        assert data["price"] == str(test_plan.price)
    
    def test_get_plan_by_id_not_found(self, client: TestClient):
        """测试获取不存在的计划"""
        response = client.get("/api/payment/plans/999")
        assert response.status_code == 404
        assert "Plan not found" in response.json()["detail"]
    
    def test_create_plan_success(self, client: TestClient, admin_headers, sample_plan_data):
        """测试创建计划（管理员）"""
        response = client.post("/api/payment/plans", json=sample_plan_data, headers=admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_plan_data["name"]
        assert data["price"] == str(sample_plan_data["price"])
        assert data["duration_days"] == sample_plan_data["duration_days"]
    
    def test_create_plan_unauthorized(self, client: TestClient, user_headers, sample_plan_data):
        """测试非管理员创建计划"""
        response = client.post("/api/payment/plans", json=sample_plan_data, headers=user_headers)
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]
    
    def test_create_plan_invalid_data(self, client: TestClient, admin_headers):
        """测试创建计划时数据无效"""
        invalid_data = {
            "name": "",  # 空名称
            "price": -10,  # 负价格
            "duration_days": 0  # 零天数
        }
        response = client.post("/api/payment/plans", json=invalid_data, headers=admin_headers)
        assert response.status_code == 422
    
    def test_update_plan_success(self, client: TestClient, admin_headers, test_plan):
        """测试更新计划"""
        update_data = {
            "name": "Updated Plan",
            "description": "Updated description",
            "price": 29.99
        }
        response = client.put(f"/api/payment/plans/{test_plan.id}", json=update_data, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Plan"
        assert data["price"] == "29.99"
    
    def test_update_plan_not_found(self, client: TestClient, admin_headers):
        """测试更新不存在的计划"""
        update_data = {"name": "Updated Plan"}
        response = client.put("/api/payment/plans/999", json=update_data, headers=admin_headers)
        assert response.status_code == 404
    
    def test_delete_plan_success(self, client: TestClient, admin_headers, db_session):
        """测试删除计划"""
        # 创建一个测试计划
        from app.services.payment_service import PaymentService
        payment_service = PaymentService(db_session)
        plan = payment_service.create_plan({
            "name": "Test Delete Plan",
            "description": "Plan to be deleted",
            "price": 19.99,
            "duration_days": 30,
            "features": ["feature1", "feature2"]
        })
        
        response = client.delete(f"/api/payment/plans/{plan.id}", headers=admin_headers)
        assert response.status_code == 200
        assert "Plan deleted successfully" in response.json()["message"]
    
    def test_delete_plan_not_found(self, client: TestClient, admin_headers):
        """测试删除不存在的计划"""
        response = client.delete("/api/payment/plans/999", headers=admin_headers)
        assert response.status_code == 404


class TestSubscriptionManagement:
    """订阅管理测试"""
    
    def test_create_subscription_success(self, client: TestClient, user_headers, test_plan):
        """测试创建订阅"""
        subscription_data = {
            "plan_id": test_plan.id,
            "payment_method": "credit_card"
        }
        response = client.post("/api/payment/subscriptions", json=subscription_data, headers=user_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["plan_id"] == test_plan.id
        assert data["status"] == "active"
        assert "start_date" in data
        assert "end_date" in data
    
    def test_create_subscription_invalid_plan(self, client: TestClient, user_headers):
        """测试创建订阅时计划不存在"""
        subscription_data = {
            "plan_id": 999,
            "payment_method": "credit_card"
        }
        response = client.post("/api/payment/subscriptions", json=subscription_data, headers=user_headers)
        assert response.status_code == 404
        assert "Plan not found" in response.json()["detail"]
    
    def test_get_user_subscriptions(self, client: TestClient, user_headers):
        """测试获取用户订阅列表"""
        response = client.get("/api/payment/subscriptions", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    def test_get_active_subscription(self, client: TestClient, user_headers, db_session, test_user, test_plan):
        """测试获取活跃订阅"""
        # 创建活跃订阅
        from app.services.payment_service import PaymentService
        payment_service = PaymentService(db_session)
        subscription = payment_service.create_subscription(test_user.id, test_plan.id, "credit_card")
        
        response = client.get("/api/payment/subscriptions/active", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == subscription.id
        assert data["status"] == "active"
    
    def test_get_active_subscription_none(self, client: TestClient, user_headers):
        """测试获取活跃订阅（无活跃订阅）"""
        response = client.get("/api/payment/subscriptions/active", headers=user_headers)
        assert response.status_code == 404
        assert "No active subscription found" in response.json()["detail"]
    
    def test_cancel_subscription_success(self, client: TestClient, user_headers, db_session, test_user, test_plan):
        """测试取消订阅"""
        # 创建订阅
        from app.services.payment_service import PaymentService
        payment_service = PaymentService(db_session)
        subscription = payment_service.create_subscription(test_user.id, test_plan.id, "credit_card")
        
        response = client.post(f"/api/payment/subscriptions/{subscription.id}/cancel", headers=user_headers)
        assert response.status_code == 200
        assert "Subscription cancelled successfully" in response.json()["message"]
    
    def test_cancel_subscription_not_found(self, client: TestClient, user_headers):
        """测试取消不存在的订阅"""
        response = client.post("/api/payment/subscriptions/999/cancel", headers=user_headers)
        assert response.status_code == 404
    
    def test_renew_subscription_success(self, client: TestClient, user_headers, db_session, test_user, test_plan):
        """测试续订"""
        # 创建即将过期的订阅
        from app.services.payment_service import PaymentService
        payment_service = PaymentService(db_session)
        subscription = payment_service.create_subscription(test_user.id, test_plan.id, "credit_card")
        
        # 设置为即将过期
        subscription.end_date = datetime.utcnow() + timedelta(days=1)
        db_session.commit()
        
        renew_data = {
            "payment_method": "credit_card"
        }
        response = client.post(f"/api/payment/subscriptions/{subscription.id}/renew", json=renew_data, headers=user_headers)
        assert response.status_code == 200
        assert "Subscription renewed successfully" in response.json()["message"]


class TestPaymentProcessing:
    """支付处理测试"""
    
    def test_create_payment_success(self, client: TestClient, user_headers, test_plan):
        """测试创建支付"""
        payment_data = {
            "plan_id": test_plan.id,
            "payment_method": "credit_card",
            "amount": str(test_plan.price)
        }
        response = client.post("/api/payment/payments", json=payment_data, headers=user_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["plan_id"] == test_plan.id
        assert data["amount"] == str(test_plan.price)
        assert data["status"] == "pending"
    
    def test_create_payment_with_coupon(self, client: TestClient, user_headers, test_plan, test_coupon):
        """测试使用优惠券创建支付"""
        payment_data = {
            "plan_id": test_plan.id,
            "payment_method": "credit_card",
            "amount": str(test_plan.price),
            "coupon_code": test_coupon.code
        }
        response = client.post("/api/payment/payments", json=payment_data, headers=user_headers)
        assert response.status_code == 201
        data = response.json()
        # 应该应用折扣
        expected_amount = test_plan.price * (1 - test_coupon.discount_percent / 100)
        assert float(data["amount"]) == expected_amount
    
    def test_create_payment_invalid_coupon(self, client: TestClient, user_headers, test_plan):
        """测试使用无效优惠券"""
        payment_data = {
            "plan_id": test_plan.id,
            "payment_method": "credit_card",
            "amount": str(test_plan.price),
            "coupon_code": "INVALID_COUPON"
        }
        response = client.post("/api/payment/payments", json=payment_data, headers=user_headers)
        assert response.status_code == 400
        assert "Invalid or expired coupon" in response.json()["detail"]
    
    def test_get_user_payments(self, client: TestClient, user_headers):
        """测试获取用户支付历史"""
        response = client.get("/api/payment/payments", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    def test_get_payment_by_id(self, client: TestClient, user_headers, db_session, test_user, test_plan):
        """测试根据ID获取支付"""
        # 创建支付
        from app.services.payment_service import PaymentService
        payment_service = PaymentService(db_session)
        payment = payment_service.create_payment(test_user.id, test_plan.id, test_plan.price, "credit_card")
        
        response = client.get(f"/api/payment/payments/{payment.id}", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == payment.id
        assert data["amount"] == str(payment.amount)
    
    def test_get_payment_not_found(self, client: TestClient, user_headers):
        """测试获取不存在的支付"""
        response = client.get("/api/payment/payments/999", headers=user_headers)
        assert response.status_code == 404


class TestCouponManagement:
    """优惠券管理测试"""
    
    def test_create_coupon_success(self, client: TestClient, admin_headers):
        """测试创建优惠券（管理员）"""
        coupon_data = {
            "code": "TESTCOUPON2024",
            "discount_percent": 20,
            "max_uses": 100,
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "description": "Test coupon"
        }
        response = client.post("/api/payment/coupons", json=coupon_data, headers=admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "TESTCOUPON2024"
        assert data["discount_percent"] == 20
        assert data["max_uses"] == 100
    
    def test_create_coupon_unauthorized(self, client: TestClient, user_headers):
        """测试非管理员创建优惠券"""
        coupon_data = {
            "code": "TESTCOUPON",
            "discount_percent": 10
        }
        response = client.post("/api/payment/coupons", json=coupon_data, headers=user_headers)
        assert response.status_code == 403
    
    def test_validate_coupon_success(self, client: TestClient, user_headers, test_coupon):
        """测试验证优惠券"""
        response = client.get(f"/api/payment/coupons/{test_coupon.code}/validate", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_coupon.code
        assert data["discount_percent"] == test_coupon.discount_percent
        assert data["is_valid"] is True
    
    def test_validate_coupon_invalid(self, client: TestClient, user_headers):
        """测试验证无效优惠券"""
        response = client.get("/api/payment/coupons/INVALID_CODE/validate", headers=user_headers)
        assert response.status_code == 404
        assert "Coupon not found" in response.json()["detail"]
    
    def test_validate_coupon_expired(self, client: TestClient, user_headers, db_session):
        """测试验证过期优惠券"""
        # 创建过期优惠券
        from app.services.payment_service import PaymentService
        payment_service = PaymentService(db_session)
        expired_coupon = payment_service.create_coupon({
            "code": "EXPIRED_COUPON",
            "discount_percent": 15,
            "expires_at": datetime.utcnow() - timedelta(days=1)
        })
        
        response = client.get(f"/api/payment/coupons/{expired_coupon.code}/validate", headers=user_headers)
        assert response.status_code == 400
        assert "expired" in response.json()["detail"]


class TestInvoiceManagement:
    """发票管理测试"""
    
    def test_get_user_invoices(self, client: TestClient, user_headers):
        """测试获取用户发票列表"""
        response = client.get("/api/payment/invoices", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    def test_get_invoice_by_id(self, client: TestClient, user_headers, db_session, test_user, test_plan):
        """测试根据ID获取发票"""
        # 创建支付和发票
        from app.services.payment_service import PaymentService
        payment_service = PaymentService(db_session)
        payment = payment_service.create_payment(test_user.id, test_plan.id, test_plan.price, "credit_card")
        invoice = payment_service.create_invoice(payment.id, test_plan.price, test_plan.price)
        
        response = client.get(f"/api/payment/invoices/{invoice.id}", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == invoice.id
        assert data["payment_id"] == payment.id
    
    def test_get_invoice_not_found(self, client: TestClient, user_headers):
        """测试获取不存在的发票"""
        response = client.get("/api/payment/invoices/999", headers=user_headers)
        assert response.status_code == 404


class TestPaymentStatistics:
    """支付统计测试"""
    
    def test_get_payment_stats_admin(self, client: TestClient, admin_headers):
        """测试获取支付统计（管理员）"""
        response = client.get("/api/payment/stats/payments", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_payments" in data
        assert "total_revenue" in data
        assert "successful_payments" in data
        assert "failed_payments" in data
    
    def test_get_payment_stats_unauthorized(self, client: TestClient, user_headers):
        """测试非管理员获取支付统计"""
        response = client.get("/api/payment/stats/payments", headers=user_headers)
        assert response.status_code == 403
    
    def test_get_subscription_stats_admin(self, client: TestClient, admin_headers):
        """测试获取订阅统计（管理员）"""
        response = client.get("/api/payment/stats/subscriptions", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_subscriptions" in data
        assert "active_subscriptions" in data
        assert "cancelled_subscriptions" in data
        assert "expired_subscriptions" in data


class TestAdminPaymentFunctions:
    """管理员支付功能测试"""
    
    def test_get_all_subscriptions_admin(self, client: TestClient, admin_headers):
        """测试管理员获取所有订阅"""
        response = client.get("/api/payment/admin/subscriptions", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    def test_get_all_payments_admin(self, client: TestClient, admin_headers):
        """测试管理员获取所有支付"""
        response = client.get("/api/payment/admin/payments", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    def test_refund_payment_success(self, client: TestClient, admin_headers, db_session, test_user, test_plan):
        """测试退款"""
        # 创建已完成的支付
        from app.services.payment_service import PaymentService
        payment_service = PaymentService(db_session)
        payment = payment_service.create_payment(test_user.id, test_plan.id, test_plan.price, "credit_card")
        payment_service.update_payment_status(payment.id, "completed")
        
        refund_data = {
            "reason": "Customer request",
            "amount": str(test_plan.price)
        }
        response = client.post(f"/api/payment/admin/payments/{payment.id}/refund", 
                             json=refund_data, headers=admin_headers)
        assert response.status_code == 200
        assert "Refund processed successfully" in response.json()["message"]
    
    def test_refund_payment_not_found(self, client: TestClient, admin_headers):
        """测试退款不存在的支付"""
        refund_data = {
            "reason": "Test",
            "amount": "10.00"
        }
        response = client.post("/api/payment/admin/payments/999/refund", 
                             json=refund_data, headers=admin_headers)
        assert response.status_code == 404
    
    def test_refund_payment_unauthorized(self, client: TestClient, user_headers):
        """测试非管理员退款"""
        refund_data = {
            "reason": "Test",
            "amount": "10.00"
        }
        response = client.post("/api/payment/admin/payments/1/refund", 
                             json=refund_data, headers=user_headers)
        assert response.status_code == 403


class TestPaymentWebhooks:
    """支付Webhook测试"""
    
    @patch('app.services.payment_service.PaymentService.process_webhook')
    def test_payment_webhook_success(self, mock_process_webhook, client: TestClient):
        """测试支付Webhook处理"""
        mock_process_webhook.return_value = {"status": "success", "payment_id": 1}
        
        webhook_data = {
            "event_type": "payment.completed",
            "payment_id": "pay_123456",
            "amount": "19.99",
            "status": "completed"
        }
        
        response = client.post("/api/payment/webhook", json=webhook_data)
        assert response.status_code == 200
        mock_process_webhook.assert_called_once()
    
    @patch('app.services.payment_service.PaymentService.process_webhook')
    def test_payment_webhook_failure(self, mock_process_webhook, client: TestClient):
        """测试Webhook处理失败"""
        mock_process_webhook.side_effect = Exception("Webhook processing failed")
        
        webhook_data = {
            "event_type": "payment.failed",
            "payment_id": "pay_123456"
        }
        
        response = client.post("/api/payment/webhook", json=webhook_data)
        assert response.status_code == 500
        assert "Webhook processing failed" in response.json()["detail"]


class TestPaymentFiltering:
    """支付过滤测试"""
    
    def test_filter_payments_by_status(self, client: TestClient, user_headers):
        """测试按状态过滤支付"""
        response = client.get("/api/payment/payments?status=completed", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_filter_payments_by_date_range(self, client: TestClient, user_headers):
        """测试按日期范围过滤支付"""
        start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        response = client.get(f"/api/payment/payments?start_date={start_date}&end_date={end_date}", 
                            headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_filter_subscriptions_by_status(self, client: TestClient, user_headers):
        """测试按状态过滤订阅"""
        response = client.get("/api/payment/subscriptions?status=active", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data