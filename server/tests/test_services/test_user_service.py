"""
Unit tests for UserService.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError

from app.services.user_service import UserService
from app.models.user import User
from app.core.security import verify_password, hash_password


class TestUserService:
    """Test cases for UserService."""

    def test_create_user_success(self, user_service, db_session):
        """Test successful user creation."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "nickname": "New User",
            "session": db_session
        }
        
        user = user_service.create_user(**user_data)
        
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.nickname == "New User"
        assert user.is_active is True
        assert user.is_verified is False
        assert verify_password("password123", user.password_hash)

    def test_create_user_duplicate_username(self, user_service, test_user):
        """Test user creation with duplicate username."""
        user_data = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "password123"
        }
        
        with pytest.raises(ValueError, match="Username already exists"):
            user_service.create_user(**user_data)

    def test_create_user_duplicate_email(self, user_service, test_user):
        """Test user creation with duplicate email."""
        user_data = {
            "username": "different",
            "email": test_user.email,
            "password": "password123"
        }
        
        with pytest.raises(ValueError, match="Email already exists"):
            user_service.create_user(**user_data)

    def test_get_user_by_username(self, user_service, test_user):
        """Test getting user by username."""
        user = user_service.get_user_by_username(test_user.username)
        
        assert user is not None
        assert user.username == test_user.username
        assert user.email == test_user.email

    def test_get_user_by_username_not_found(self, user_service, db_session):
        """Test getting non-existent user by username."""
        user = user_service.get_user_by_username("nonexistent", session=db_session)
        
        assert user is None

    def test_get_user_by_email(self, user_service, test_user):
        """Test getting user by email."""
        user = user_service.get_user_by_email(test_user.email)
        
        assert user is not None
        assert user.username == test_user.username
        assert user.email == test_user.email

    def test_get_user_by_email_not_found(self, user_service):
        """Test getting non-existent user by email."""
        user = user_service.get_user_by_email("nonexistent@example.com")
        
        assert user is None

    def test_authenticate_user_success(self, user_service, test_user):
        """Test successful user authentication."""
        user = user_service.authenticate_user(test_user.username, "testpassword")
        
        assert user is not None
        assert user.username == test_user.username

    def test_authenticate_user_wrong_password(self, user_service, test_user):
        """Test authentication with wrong password."""
        user = user_service.authenticate_user(test_user.username, "wrongpassword")
        
        assert user is None

    def test_authenticate_user_not_found(self, user_service):
        """Test authentication with non-existent user."""
        user = user_service.authenticate_user("nonexistent", "password")
        
        assert user is None

    def test_authenticate_user_inactive(self, user_service, db_session):
        """Test authentication with inactive user."""
        from app.models.user import UserStatusEnum
        # Create inactive user
        inactive_user = User(
            username="inactive",
            email="inactive@example.com",
            password_hash=hash_password("password"),
            status=UserStatusEnum.INACTIVE
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        user = user_service.authenticate_user("inactive", "password")
        
        assert user is None

    def test_update_user_password(self, user_service, test_user):
        """Test updating user password."""
        new_password = "newpassword123"
        
        updated_user = user_service.update_user_password(test_user.id, new_password)
        
        assert verify_password(new_password, updated_user.password_hash)
        assert updated_user.password_changed_at is not None

    def test_update_user_password_not_found(self, user_service):
        """Test updating password for non-existent user."""
        with pytest.raises(ValueError, match="User not found"):
            user_service.update_user_password(999, "newpassword")

    def test_verify_user_email(self, user_service, test_user):
        """Test email verification."""
        # Make user unverified first
        test_user.is_verified = False
        test_user.email_verified = False
        
        updated_user = user_service.verify_user_email(test_user.id)
        
        assert updated_user.is_verified is True
        assert updated_user.email_verified is True
        assert updated_user.email_verified_at is not None

    def test_verify_user_email_not_found(self, user_service):
        """Test email verification for non-existent user."""
        with pytest.raises(ValueError, match="User not found"):
            user_service.verify_user_email(999)

    def test_update_user_profile(self, user_service, test_user):
        """Test updating user profile."""
        profile_data = {
            "full_name": "Updated Name",
            "bio": "Updated bio",
            "location": "New Location"
        }
        
        updated_user = user_service.update_user_profile(test_user.id, profile_data)
        
        assert updated_user.full_name == "Updated Name"
        assert updated_user.bio == "Updated bio"
        assert updated_user.location == "New Location"

    def test_update_user_profile_not_found(self, user_service):
        """Test updating profile for non-existent user."""
        with pytest.raises(ValueError, match="User not found"):
            user_service.update_user_profile(999, {"full_name": "Test"})

    def test_deactivate_user(self, user_service, test_user):
        """Test user deactivation."""
        updated_user = user_service.deactivate_user(test_user.id)
        
        assert updated_user.is_active is False

    def test_deactivate_user_not_found(self, user_service):
        """Test deactivating non-existent user."""
        with pytest.raises(ValueError, match="User not found"):
            user_service.deactivate_user(999)

    def test_activate_user(self, user_service, db_session):
        """Test user activation."""
        # Create inactive user
        inactive_user = User(
            username="inactive",
            email="inactive@example.com",
            password_hash=hash_password("password"),
            status=UserStatusEnum.INACTIVE
        )
        db_session.add(inactive_user)
        db_session.commit()
        db_session.refresh(inactive_user)
        
        updated_user = user_service.activate_user(inactive_user.id)
        
        assert updated_user.is_active is True

    def test_activate_user_not_found(self, user_service):
        """Test activating non-existent user."""
        with pytest.raises(ValueError, match="User not found"):
            user_service.activate_user(999)

    def test_delete_user(self, user_service, test_user):
        """Test user deletion (soft delete)."""
        user_service.delete_user(test_user.id)
        
        # User should still exist but be marked as deleted
        user = user_service.get_user_by_id(test_user.id)
        assert user.deleted_at is not None
        assert user.is_active is False

    def test_delete_user_not_found(self, user_service):
        """Test deleting non-existent user."""
        with pytest.raises(ValueError, match="User not found"):
            user_service.delete_user(999)

    def test_get_users_with_pagination(self, user_service, db_session):
        """Test getting users with pagination."""
        # Create additional users
        for i in range(5):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password_hash=hash_password("password")
            )
            db_session.add(user)
        db_session.commit()
        
        users, total = user_service.get_users(skip=0, limit=3)
        
        assert len(users) == 3
        assert total >= 5  # At least 5 users (plus test_user)

    def test_search_users(self, user_service, db_session):
        """Test searching users."""
        # Create users with searchable names
        search_user = User(
            username="searchable",
            email="search@example.com",
            nickname="Searchable User",
            password_hash=hash_password("password")
        )
        db_session.add(search_user)
        db_session.commit()
        
        users, total = user_service.search_users("searchable")
        
        assert total >= 1
        assert any(user.username == "searchable" for user in users)

    def test_get_user_stats(self, user_service, db_session):
        """Test getting user statistics."""
        # Create users with different statuses
        for i in range(3):
            user = User(
                username=f"stats_user{i}",
                email=f"stats{i}@example.com",
                password_hash=hash_password("password"),
                email_verified=i % 2 == 0
            )
            db_session.add(user)
        db_session.commit()
        
        stats = user_service.get_user_stats()
        
        assert "total_users" in stats
        assert "active_users" in stats
        assert "verified_users" in stats
        assert "new_users_today" in stats
        assert stats["total_users"] >= 4  # At least test_user + 3 new users

    @patch('app.services.user_service.send_verification_email')
    def test_send_verification_email(self, mock_send_email, user_service, test_user):
        """Test sending verification email."""
        user_service.send_verification_email(test_user.id)
        
        mock_send_email.assert_called_once()
        args = mock_send_email.call_args[0]
        assert args[0] == test_user.email

    @patch('app.services.user_service.send_password_reset_email')
    def test_send_password_reset_email(self, mock_send_email, user_service, test_user):
        """Test sending password reset email."""
        user_service.send_password_reset_email(test_user.email)
        
        mock_send_email.assert_called_once()
        args = mock_send_email.call_args[0]
        assert args[0] == test_user.email

    def test_check_password_strength(self, user_service):
        """Test password strength validation."""
        # Strong password
        assert user_service.check_password_strength("StrongPass123!") is True
        
        # Weak passwords
        assert user_service.check_password_strength("weak") is False
        assert user_service.check_password_strength("12345678") is False
        assert user_service.check_password_strength("password") is False

    def test_get_user_login_history(self, user_service, test_user, db_session):
        """Test getting user login history."""
        # Add some login records
        from app.models.user import UserLoginHistory
        
        for i in range(3):
            login_record = UserLoginHistory(
                user_id=test_user.id,
                ip_address=f"192.168.1.{i+1}",
                user_agent="Test Browser",
                login_at=datetime.utcnow() - timedelta(days=i)
            )
            db_session.add(login_record)
        db_session.commit()
        
        history = user_service.get_user_login_history(test_user.id, limit=2)
        
        assert len(history) == 2
        assert all(record.user_id == test_user.id for record in history)

    def test_record_login(self, user_service, test_user):
        """Test recording user login."""
        ip_address = "192.168.1.100"
        user_agent = "Test Browser"
        
        user_service.record_login(test_user.id, ip_address, user_agent)
        
        # Verify login was recorded
        history = user_service.get_user_login_history(test_user.id, limit=1)
        assert len(history) == 1
        assert history[0].ip_address == ip_address
        assert history[0].user_agent == user_agent

    def test_update_last_activity(self, user_service, test_user):
        """Test updating user's last activity."""
        original_activity = test_user.last_activity_at
        
        user_service.update_last_activity(test_user.id)
        
        # Refresh user from database
        updated_user = user_service.get_user_by_id(test_user.id)
        assert updated_user.last_activity_at > original_activity

    def test_get_active_users(self, user_service, db_session):
        """Test getting recently active users."""
        # Create users with different activity times
        now = datetime.utcnow()
        
        active_user = User(
            username="active",
            email="active@example.com",
            password_hash=hash_password("password"),
            last_activity_at=now - timedelta(minutes=5)
        )
        
        inactive_user = User(
            username="inactive",
            email="inactive@example.com",
            password_hash=hash_password("password"),
            last_activity_at=now - timedelta(days=2)
        )
        
        db_session.add_all([active_user, inactive_user])
        db_session.commit()
        
        # Get users active in last hour
        active_users = user_service.get_active_users(minutes=60)
        
        assert any(user.username == "active" for user in active_users)
        assert not any(user.username == "inactive" for user in active_users)