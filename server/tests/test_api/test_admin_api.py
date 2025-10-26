"""
管理员API集成测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from io import StringIO
import json

from app.models.user import User
from app.models.permission import AuditLog


class TestUserManagement:
    """用户管理测试"""
    
    def test_get_users_success(self, client: TestClient, admin_headers):
        """测试获取用户列表"""
        response = client.get("/api/admin/users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
    
    def test_get_users_unauthorized(self, client: TestClient, user_headers):
        """测试非管理员获取用户列表"""
        response = client.get("/api/admin/users", headers=user_headers)
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]
    
    def test_get_users_with_search(self, client: TestClient, admin_headers):
        """测试搜索用户"""
        response = client.get("/api/admin/users?search=test", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_get_users_with_filters(self, client: TestClient, admin_headers):
        """测试过滤用户"""
        response = client.get("/api/admin/users?is_active=true&email_verified=true", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_get_users_with_pagination(self, client: TestClient, admin_headers):
        """测试分页获取用户"""
        response = client.get("/api/admin/users?page=1&size=10", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 10
    
    def test_get_user_details_success(self, client: TestClient, admin_headers, test_user):
        """测试获取用户详情"""
        response = client.get(f"/api/admin/users/{test_user.id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert "subscriptions" in data
        assert "payments" in data
        assert "audit_logs" in data
    
    def test_get_user_details_not_found(self, client: TestClient, admin_headers):
        """测试获取不存在用户的详情"""
        response = client.get("/api/admin/users/999", headers=admin_headers)
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_update_user_success(self, client: TestClient, admin_headers, test_user):
        """测试更新用户信息"""
        update_data = {
            "full_name": "Updated Name",
            "email": "updated@test.com",
            "is_active": True
        }
        response = client.put(f"/api/admin/users/{test_user.id}", json=update_data, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["email"] == "updated@test.com"
    
    def test_update_user_invalid_email(self, client: TestClient, admin_headers, test_user):
        """测试更新用户无效邮箱"""
        update_data = {
            "email": "invalid-email"
        }
        response = client.put(f"/api/admin/users/{test_user.id}", json=update_data, headers=admin_headers)
        assert response.status_code == 422
    
    def test_ban_user_success(self, client: TestClient, admin_headers, test_user):
        """测试封禁用户"""
        ban_data = {
            "reason": "Violation of terms",
            "duration_days": 7
        }
        response = client.post(f"/api/admin/users/{test_user.id}/ban", json=ban_data, headers=admin_headers)
        assert response.status_code == 200
        assert "User banned successfully" in response.json()["message"]
    
    def test_ban_user_not_found(self, client: TestClient, admin_headers):
        """测试封禁不存在的用户"""
        ban_data = {
            "reason": "Test",
            "duration_days": 1
        }
        response = client.post("/api/admin/users/999/ban", json=ban_data, headers=admin_headers)
        assert response.status_code == 404
    
    def test_unban_user_success(self, client: TestClient, admin_headers, db_session, test_user):
        """测试解封用户"""
        # 先封禁用户
        from app.services.admin_service import AdminService
        admin_service = AdminService(db_session)
        admin_service.ban_user(test_user.id, "Test ban", 7)
        
        response = client.post(f"/api/admin/users/{test_user.id}/unban", headers=admin_headers)
        assert response.status_code == 200
        assert "User unbanned successfully" in response.json()["message"]
    
    def test_delete_user_success(self, client: TestClient, admin_headers, db_session):
        """测试软删除用户"""
        # 创建测试用户
        from app.services.user_service import UserService
        user_service = UserService(db_session)
        user = user_service.create_user({
            "username": "delete_test_user",
            "email": "delete@test.com",
            "password": "testpass123",
            "full_name": "Delete Test User"
        })
        
        response = client.delete(f"/api/admin/users/{user.id}", headers=admin_headers)
        assert response.status_code == 200
        assert "User deleted successfully" in response.json()["message"]


class TestSystemMonitoring:
    """系统监控测试"""
    
    def test_get_system_stats_success(self, client: TestClient, admin_headers):
        """测试获取系统统计"""
        response = client.get("/api/admin/stats/system", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "total_subscriptions" in data
        assert "active_subscriptions" in data
        assert "total_payments" in data
        assert "total_revenue" in data
    
    def test_get_system_stats_unauthorized(self, client: TestClient, user_headers):
        """测试非管理员获取系统统计"""
        response = client.get("/api/admin/stats/system", headers=user_headers)
        assert response.status_code == 403
    
    def test_get_user_growth_chart(self, client: TestClient, admin_headers):
        """测试获取用户增长图表数据"""
        response = client.get("/api/admin/charts/user-growth", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "labels" in data
        assert "data" in data
        assert isinstance(data["labels"], list)
        assert isinstance(data["data"], list)
    
    def test_get_user_growth_chart_with_period(self, client: TestClient, admin_headers):
        """测试获取指定时期的用户增长图表"""
        response = client.get("/api/admin/charts/user-growth?period=7", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["labels"]) <= 7
    
    def test_get_revenue_chart(self, client: TestClient, admin_headers):
        """测试获取收入图表数据"""
        response = client.get("/api/admin/charts/revenue", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "labels" in data
        assert "data" in data
    
    def test_get_plan_distribution(self, client: TestClient, admin_headers):
        """测试获取计划分布数据"""
        response = client.get("/api/admin/stats/plan-distribution", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for item in data:
            assert "plan_name" in item
            assert "count" in item
            assert "percentage" in item
    
    def test_get_payment_methods_stats(self, client: TestClient, admin_headers):
        """测试获取支付方式统计"""
        response = client.get("/api/admin/stats/payment-methods", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for item in data:
            assert "method" in item
            assert "count" in item
            assert "percentage" in item


class TestActivityMonitoring:
    """活动监控测试"""
    
    def test_get_recent_activities(self, client: TestClient, admin_headers):
        """测试获取最近活动"""
        response = client.get("/api/admin/activities/recent", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    def test_get_recent_activities_with_limit(self, client: TestClient, admin_headers):
        """测试限制获取最近活动数量"""
        response = client.get("/api/admin/activities/recent?limit=5", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5
    
    def test_get_security_events(self, client: TestClient, admin_headers):
        """测试获取安全事件"""
        response = client.get("/api/admin/activities/security", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    def test_get_security_events_with_filters(self, client: TestClient, admin_headers):
        """测试过滤获取安全事件"""
        start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        response = client.get(f"/api/admin/activities/security?start_date={start_date}&end_date={end_date}", 
                            headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_get_failed_logins(self, client: TestClient, admin_headers):
        """测试获取失败登录记录"""
        response = client.get("/api/admin/activities/failed-logins", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    def test_get_failed_logins_with_pagination(self, client: TestClient, admin_headers):
        """测试分页获取失败登录记录"""
        response = client.get("/api/admin/activities/failed-logins?page=1&size=10", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 10


class TestSystemMaintenance:
    """系统维护测试"""
    
    def test_system_health_check(self, client: TestClient, admin_headers):
        """测试系统健康检查"""
        response = client.get("/api/admin/system/health", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "database_status" in data
        assert "expired_subscriptions_count" in data
        assert "pending_payments_count" in data
        assert "system_uptime" in data
    
    def test_system_health_check_unauthorized(self, client: TestClient, user_headers):
        """测试非管理员系统健康检查"""
        response = client.get("/api/admin/system/health", headers=user_headers)
        assert response.status_code == 403
    
    def test_cleanup_expired_data(self, client: TestClient, admin_headers):
        """测试清理过期数据"""
        response = client.post("/api/admin/system/cleanup", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "expired_subscriptions_updated" in data
        assert "old_audit_logs_deleted" in data
        assert "cleanup_timestamp" in data
    
    def test_cleanup_expired_data_with_days(self, client: TestClient, admin_headers):
        """测试指定天数清理过期数据"""
        cleanup_data = {
            "days_to_keep": 30
        }
        response = client.post("/api/admin/system/cleanup", json=cleanup_data, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "expired_subscriptions_updated" in data
        assert "old_audit_logs_deleted" in data


class TestDataExport:
    """数据导出测试"""
    
    def test_export_users_csv(self, client: TestClient, admin_headers):
        """测试导出用户数据为CSV"""
        export_data = {
            "format": "csv",
            "include_inactive": True
        }
        response = client.post("/api/admin/export/users", json=export_data, headers=admin_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
    
    def test_export_users_json(self, client: TestClient, admin_headers):
        """测试导出用户数据为JSON"""
        export_data = {
            "format": "json",
            "include_inactive": False
        }
        response = client.post("/api/admin/export/users", json=export_data, headers=admin_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # 验证JSON格式
        data = response.json()
        assert isinstance(data, list)
    
    def test_export_users_with_filters(self, client: TestClient, admin_headers):
        """测试过滤导出用户数据"""
        start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        export_data = {
            "format": "csv",
            "start_date": start_date,
            "end_date": end_date,
            "email_verified": True
        }
        response = client.post("/api/admin/export/users", json=export_data, headers=admin_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    def test_export_payments_csv(self, client: TestClient, admin_headers):
        """测试导出支付数据为CSV"""
        export_data = {
            "format": "csv"
        }
        response = client.post("/api/admin/export/payments", json=export_data, headers=admin_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    def test_export_payments_json(self, client: TestClient, admin_headers):
        """测试导出支付数据为JSON"""
        export_data = {
            "format": "json",
            "status": "completed"
        }
        response = client.post("/api/admin/export/payments", json=export_data, headers=admin_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
    
    def test_export_payments_with_date_range(self, client: TestClient, admin_headers):
        """测试按日期范围导出支付数据"""
        start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        export_data = {
            "format": "csv",
            "start_date": start_date,
            "end_date": end_date
        }
        response = client.post("/api/admin/export/payments", json=export_data, headers=admin_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    def test_export_unauthorized(self, client: TestClient, user_headers):
        """测试非管理员导出数据"""
        export_data = {
            "format": "csv"
        }
        response = client.post("/api/admin/export/users", json=export_data, headers=user_headers)
        assert response.status_code == 403


class TestAuditLogging:
    """审计日志测试"""
    
    def test_admin_actions_logged(self, client: TestClient, admin_headers, test_user, db_session):
        """测试管理员操作被记录"""
        # 执行管理员操作
        update_data = {
            "full_name": "Updated by Admin"
        }
        response = client.put(f"/api/admin/users/{test_user.id}", json=update_data, headers=admin_headers)
        assert response.status_code == 200
        
        # 检查审计日志
        from app.models.permission import AuditLog
        audit_log = db_session.query(AuditLog).filter(
            AuditLog.action == "update_user",
            AuditLog.resource_type == "user",
            AuditLog.resource_id == str(test_user.id)
        ).first()
        
        assert audit_log is not None
        assert audit_log.level == "info"
    
    def test_sensitive_actions_logged_as_warning(self, client: TestClient, admin_headers, test_user, db_session):
        """测试敏感操作被记录为警告级别"""
        # 执行敏感操作（封禁用户）
        ban_data = {
            "reason": "Test ban",
            "duration_days": 1
        }
        response = client.post(f"/api/admin/users/{test_user.id}/ban", json=ban_data, headers=admin_headers)
        assert response.status_code == 200
        
        # 检查审计日志
        from app.models.permission import AuditLog
        audit_log = db_session.query(AuditLog).filter(
            AuditLog.action == "ban_user",
            AuditLog.resource_type == "user",
            AuditLog.resource_id == str(test_user.id)
        ).first()
        
        assert audit_log is not None
        assert audit_log.level == "warning"


class TestErrorHandling:
    """错误处理测试"""
    
    def test_invalid_user_id_format(self, client: TestClient, admin_headers):
        """测试无效用户ID格式"""
        response = client.get("/api/admin/users/invalid_id", headers=admin_headers)
        assert response.status_code == 422
    
    def test_invalid_pagination_params(self, client: TestClient, admin_headers):
        """测试无效分页参数"""
        response = client.get("/api/admin/users?page=-1&size=0", headers=admin_headers)
        assert response.status_code == 422
    
    def test_invalid_date_format(self, client: TestClient, admin_headers):
        """测试无效日期格式"""
        response = client.get("/api/admin/activities/security?start_date=invalid_date", headers=admin_headers)
        assert response.status_code == 422
    
    def test_invalid_export_format(self, client: TestClient, admin_headers):
        """测试无效导出格式"""
        export_data = {
            "format": "invalid_format"
        }
        response = client.post("/api/admin/export/users", json=export_data, headers=admin_headers)
        assert response.status_code == 422


class TestRateLimiting:
    """速率限制测试"""
    
    @pytest.mark.slow
    def test_admin_api_rate_limiting(self, client: TestClient, admin_headers):
        """测试管理员API速率限制"""
        # 快速发送多个请求
        responses = []
        for _ in range(10):
            response = client.get("/api/admin/stats/system", headers=admin_headers)
            responses.append(response.status_code)
        
        # 大部分请求应该成功，但可能有一些被限制
        success_count = sum(1 for status in responses if status == 200)
        assert success_count >= 5  # 至少一半的请求成功


class TestConcurrency:
    """并发测试"""
    
    @pytest.mark.slow
    def test_concurrent_user_updates(self, client: TestClient, admin_headers, test_user):
        """测试并发用户更新"""
        import threading
        import time
        
        results = []
        
        def update_user(name_suffix):
            update_data = {
                "full_name": f"Concurrent Update {name_suffix}"
            }
            response = client.put(f"/api/admin/users/{test_user.id}", 
                                json=update_data, headers=admin_headers)
            results.append(response.status_code)
        
        # 创建多个线程同时更新用户
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_user, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 所有请求都应该成功（数据库应该处理并发）
        assert all(status == 200 for status in results)