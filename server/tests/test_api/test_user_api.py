"""
用户API集成测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.models.user import User
from app.models.permission import AuditLog


class TestUserRegistration:
    """用户注册测试"""
    
    def test_register_success(self, client: TestClient, sample_user_data):
        """测试成功注册"""
        response = client.post("/api/users/register", json=sample_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == sample_user_data["username"]
        assert data["email"] == sample_user_data["email"]
        assert "id" in data
        assert "password" not in data  # 确保密码不在响应中
    
    def test_register_duplicate_username(self, client: TestClient, test_user, sample_user_data):
        """测试重复用户名注册"""
        sample_user_data["username"] = test_user.username
        response = client.post("/api/users/register", json=sample_user_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_register_duplicate_email(self, client: TestClient, test_user, sample_user_data):
        """测试重复邮箱注册"""
        sample_user_data["email"] = test_user.email
        response = client.post("/api/users/register", json=sample_user_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_register_invalid_email(self, client: TestClient, sample_user_data):
        """测试无效邮箱格式"""
        sample_user_data["email"] = "invalid-email"
        response = client.post("/api/users/register", json=sample_user_data)
        assert response.status_code == 422
    
    def test_register_weak_password(self, client: TestClient, sample_user_data):
        """测试弱密码"""
        sample_user_data["password"] = "123"
        response = client.post("/api/users/register", json=sample_user_data)
        assert response.status_code == 400
        assert "Password too weak" in response.json()["detail"]
    
    def test_register_missing_fields(self, client: TestClient):
        """测试缺少必填字段"""
        response = client.post("/api/users/register", json={})
        assert response.status_code == 422


class TestUserLogin:
    """用户登录测试"""
    
    def test_login_success(self, client: TestClient, test_user):
        """测试成功登录"""
        login_data = {
            "username": test_user.username,
            "password": "testpass123"
        }
        response = client.post("/api/users/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == test_user.username
    
    def test_login_with_email(self, client: TestClient, test_user):
        """测试使用邮箱登录"""
        login_data = {
            "username": test_user.email,
            "password": "testpass123"
        }
        response = client.post("/api/users/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    def test_login_wrong_password(self, client: TestClient, test_user):
        """测试错误密码"""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        response = client.post("/api/users/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client: TestClient):
        """测试不存在的用户"""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        response = client.post("/api/users/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_inactive_user(self, client: TestClient, db_session):
        """测试未激活用户登录"""
        # 创建未激活用户
        from app.services.user_service import UserService
        user_service = UserService(db_session)
        user_data = {
            "username": "inactive_user",
            "email": "inactive@test.com",
            "password": "testpass123",
            "full_name": "Inactive User"
        }
        user = user_service.create_user(user_data)
        user.is_active = False
        db_session.commit()
        
        login_data = {
            "username": "inactive_user",
            "password": "testpass123"
        }
        response = client.post("/api/users/login", json=login_data)
        assert response.status_code == 401
        assert "Account is not active" in response.json()["detail"]


class TestUserProfile:
    """用户个人资料测试"""
    
    def test_get_profile_success(self, client: TestClient, user_headers):
        """测试获取个人资料"""
        response = client.get("/api/users/profile", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "full_name" in data
        assert "password" not in data
    
    def test_get_profile_unauthorized(self, client: TestClient):
        """测试未授权获取个人资料"""
        response = client.get("/api/users/profile")
        assert response.status_code == 401
    
    def test_update_profile_success(self, client: TestClient, user_headers):
        """测试更新个人资料"""
        update_data = {
            "full_name": "Updated Name",
            "bio": "Updated bio"
        }
        response = client.put("/api/users/profile", json=update_data, headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["bio"] == "Updated bio"
    
    def test_update_profile_invalid_email(self, client: TestClient, user_headers):
        """测试更新无效邮箱"""
        update_data = {
            "email": "invalid-email"
        }
        response = client.put("/api/users/profile", json=update_data, headers=user_headers)
        assert response.status_code == 422
    
    def test_update_profile_duplicate_email(self, client: TestClient, user_headers, db_session):
        """测试更新重复邮箱"""
        # 创建另一个用户
        from app.services.user_service import UserService
        user_service = UserService(db_session)
        user_service.create_user({
            "username": "other_user",
            "email": "other@test.com",
            "password": "testpass123",
            "full_name": "Other User"
        })
        
        update_data = {
            "email": "other@test.com"
        }
        response = client.put("/api/users/profile", json=update_data, headers=user_headers)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestPasswordManagement:
    """密码管理测试"""
    
    def test_change_password_success(self, client: TestClient, user_headers):
        """测试成功修改密码"""
        password_data = {
            "current_password": "testpass123",
            "new_password": "newpass123"
        }
        response = client.post("/api/users/change-password", json=password_data, headers=user_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Password updated successfully"
    
    def test_change_password_wrong_current(self, client: TestClient, user_headers):
        """测试错误的当前密码"""
        password_data = {
            "current_password": "wrongpass",
            "new_password": "newpass123"
        }
        response = client.post("/api/users/change-password", json=password_data, headers=user_headers)
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]
    
    def test_change_password_weak_new(self, client: TestClient, user_headers):
        """测试弱新密码"""
        password_data = {
            "current_password": "testpass123",
            "new_password": "123"
        }
        response = client.post("/api/users/change-password", json=password_data, headers=user_headers)
        assert response.status_code == 400
        assert "Password too weak" in response.json()["detail"]
    
    @patch('app.services.user_service.UserService.send_password_reset_email')
    def test_forgot_password_success(self, mock_send_email, client: TestClient, test_user):
        """测试忘记密码"""
        mock_send_email.return_value = True
        
        response = client.post("/api/users/forgot-password", json={"email": test_user.email})
        assert response.status_code == 200
        assert "Password reset email sent" in response.json()["message"]
        mock_send_email.assert_called_once()
    
    def test_forgot_password_nonexistent_email(self, client: TestClient):
        """测试不存在的邮箱"""
        response = client.post("/api/users/forgot-password", json={"email": "nonexistent@test.com"})
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


class TestEmailVerification:
    """邮箱验证测试"""
    
    @patch('app.services.user_service.UserService.send_verification_email')
    def test_resend_verification_success(self, mock_send_email, client: TestClient, user_headers, test_user, db_session):
        """测试重新发送验证邮件"""
        # 设置用户为未验证状态
        test_user.email_verified = False
        db_session.commit()
        
        mock_send_email.return_value = True
        
        response = client.post("/api/users/resend-verification", headers=user_headers)
        assert response.status_code == 200
        assert "Verification email sent" in response.json()["message"]
        mock_send_email.assert_called_once()
    
    def test_resend_verification_already_verified(self, client: TestClient, user_headers, test_user, db_session):
        """测试已验证用户重新发送验证邮件"""
        # 确保用户已验证
        test_user.email_verified = True
        db_session.commit()
        
        response = client.post("/api/users/resend-verification", headers=user_headers)
        assert response.status_code == 400
        assert "already verified" in response.json()["detail"]
    
    def test_verify_email_success(self, client: TestClient, test_user, db_session):
        """测试邮箱验证成功"""
        # 生成验证令牌
        from app.services.user_service import UserService
        user_service = UserService(db_session)
        token = user_service.generate_verification_token(test_user.email)
        
        response = client.post(f"/api/users/verify-email?token={token}")
        assert response.status_code == 200
        assert "Email verified successfully" in response.json()["message"]
        
        # 验证用户状态已更新
        db_session.refresh(test_user)
        assert test_user.email_verified is True
    
    def test_verify_email_invalid_token(self, client: TestClient):
        """测试无效验证令牌"""
        response = client.post("/api/users/verify-email?token=invalid_token")
        assert response.status_code == 400
        assert "Invalid or expired token" in response.json()["detail"]


class TestUserActivity:
    """用户活动测试"""
    
    def test_get_login_history(self, client: TestClient, user_headers):
        """测试获取登录历史"""
        response = client.get("/api/users/login-history", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
    
    def test_get_login_history_with_pagination(self, client: TestClient, user_headers):
        """测试分页获取登录历史"""
        response = client.get("/api/users/login-history?page=1&size=5", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5
    
    def test_get_activity_logs(self, client: TestClient, user_headers):
        """测试获取活动日志"""
        response = client.get("/api/users/activity", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestTokenManagement:
    """令牌管理测试"""
    
    def test_refresh_token_success(self, client: TestClient, test_user):
        """测试刷新令牌"""
        # 先登录获取令牌
        login_data = {
            "username": test_user.username,
            "password": "testpass123"
        }
        login_response = client.post("/api/users/login", json=login_data)
        refresh_token = login_response.json()["refresh_token"]
        
        # 使用刷新令牌
        response = client.post("/api/users/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_refresh_token_invalid(self, client: TestClient):
        """测试无效刷新令牌"""
        response = client.post("/api/users/refresh", json={"refresh_token": "invalid_token"})
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]
    
    def test_logout_success(self, client: TestClient, user_headers):
        """测试登出"""
        response = client.post("/api/users/logout", headers=user_headers)
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]
    
    def test_logout_unauthorized(self, client: TestClient):
        """测试未授权登出"""
        response = client.post("/api/users/logout")
        assert response.status_code == 401


class TestUserSearch:
    """用户搜索测试"""
    
    def test_search_users_success(self, client: TestClient, user_headers, db_session):
        """测试搜索用户"""
        # 创建一些测试用户
        from app.services.user_service import UserService
        user_service = UserService(db_session)
        
        for i in range(3):
            user_service.create_user({
                "username": f"search_user_{i}",
                "email": f"search{i}@test.com",
                "password": "testpass123",
                "full_name": f"Search User {i}"
            })
        
        response = client.get("/api/users/search?q=search_user", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3
    
    def test_search_users_empty_query(self, client: TestClient, user_headers):
        """测试空搜索查询"""
        response = client.get("/api/users/search?q=", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_search_users_no_results(self, client: TestClient, user_headers):
        """测试无搜索结果"""
        response = client.get("/api/users/search?q=nonexistent_user_xyz", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0


class TestUserDeactivation:
    """用户停用测试"""
    
    def test_deactivate_account_success(self, client: TestClient, user_headers):
        """测试停用账户"""
        response = client.post("/api/users/deactivate", headers=user_headers)
        assert response.status_code == 200
        assert "Account deactivated successfully" in response.json()["message"]
    
    def test_deactivate_account_with_password(self, client: TestClient, user_headers):
        """测试使用密码停用账户"""
        deactivate_data = {
            "password": "testpass123",
            "reason": "No longer needed"
        }
        response = client.post("/api/users/deactivate", json=deactivate_data, headers=user_headers)
        assert response.status_code == 200
        assert "Account deactivated successfully" in response.json()["message"]
    
    def test_deactivate_account_wrong_password(self, client: TestClient, user_headers):
        """测试错误密码停用账户"""
        deactivate_data = {
            "password": "wrongpassword",
            "reason": "Test"
        }
        response = client.post("/api/users/deactivate", json=deactivate_data, headers=user_headers)
        assert response.status_code == 400
        assert "Invalid password" in response.json()["detail"]