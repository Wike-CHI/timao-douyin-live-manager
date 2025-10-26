"""
Unit tests for AuditService.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.services.audit_service import AuditService, AuditLevel, AuditCategory
from app.models.permission import AuditLog


class TestAuditService:
    """Test cases for AuditService."""

    def test_log_action_basic(self, audit_service, test_user):
        """Test basic action logging."""
        audit_service.log_action(
            user_id=test_user.id,
            action="test_action",
            resource_type="test_resource",
            resource_id="123",
            details={"key": "value"},
            ip_address="192.168.1.1"
        )
        
        # Verify log was created
        logs = audit_service.get_audit_logs(limit=1)
        assert len(logs) == 1
        
        log = logs[0]
        assert log.user_id == test_user.id
        assert log.action == "test_action"
        assert log.resource_type == "test_resource"
        assert log.resource_id == "123"
        assert log.details["key"] == "value"
        assert log.ip_address == "192.168.1.1"

    def test_log_action_auto_level_high_risk(self, audit_service, test_user):
        """Test automatic level assignment for high-risk actions."""
        audit_service.log_action(
            user_id=test_user.id,
            action="delete_user",
            resource_type="user",
            resource_id="123"
        )
        
        logs = audit_service.get_audit_logs(limit=1)
        log = logs[0]
        
        # delete_user should be automatically assigned HIGH level
        assert log.level == AuditLevel.HIGH

    def test_log_action_auto_level_critical_resource(self, audit_service, test_user):
        """Test automatic level assignment for critical resources."""
        audit_service.log_action(
            user_id=test_user.id,
            action="update",
            resource_type="payment",
            resource_id="123"
        )
        
        logs = audit_service.get_audit_logs(limit=1)
        log = logs[0]
        
        # payment resource should be automatically assigned HIGH level
        assert log.level == AuditLevel.HIGH

    def test_log_action_auto_category_security(self, audit_service, test_user):
        """Test automatic category assignment for security actions."""
        audit_service.log_action(
            user_id=test_user.id,
            action="login_failed",
            resource_type="auth",
            resource_id="123"
        )
        
        logs = audit_service.get_audit_logs(limit=1)
        log = logs[0]
        
        # login_failed should be automatically assigned SECURITY category
        assert log.category == AuditCategory.SECURITY

    def test_log_action_manual_level_category(self, audit_service, test_user):
        """Test manual level and category assignment."""
        audit_service.log_action(
            user_id=test_user.id,
            action="custom_action",
            resource_type="custom",
            resource_id="123",
            level=AuditLevel.CRITICAL,
            category=AuditCategory.SYSTEM
        )
        
        logs = audit_service.get_audit_logs(limit=1)
        log = logs[0]
        
        assert log.level == AuditLevel.CRITICAL
        assert log.category == AuditCategory.SYSTEM

    def test_get_audit_logs_basic(self, audit_service, test_user, db_session):
        """Test getting audit logs with basic parameters."""
        # Create multiple logs
        for i in range(5):
            audit_service.log_action(
                user_id=test_user.id,
                action=f"action_{i}",
                resource_type="test",
                resource_id=str(i)
            )
        
        logs = audit_service.get_audit_logs(skip=1, limit=3)
        
        assert len(logs) == 3
        # Should be ordered by timestamp desc (newest first)
        assert logs[0].timestamp > logs[1].timestamp > logs[2].timestamp

    def test_get_audit_logs_filter_user(self, audit_service, test_user, admin_user, db_session):
        """Test filtering audit logs by user."""
        # Create logs for different users
        audit_service.log_action(
            user_id=test_user.id,
            action="user_action",
            resource_type="test",
            resource_id="1"
        )
        
        audit_service.log_action(
            user_id=admin_user.id,
            action="admin_action",
            resource_type="test",
            resource_id="2"
        )
        
        # Filter by test_user
        logs = audit_service.get_audit_logs(user_id=test_user.id)
        
        assert len(logs) == 1
        assert logs[0].user_id == test_user.id
        assert logs[0].action == "user_action"

    def test_get_audit_logs_filter_action(self, audit_service, test_user):
        """Test filtering audit logs by action."""
        # Create logs with different actions
        audit_service.log_action(
            user_id=test_user.id,
            action="login",
            resource_type="auth",
            resource_id="1"
        )
        
        audit_service.log_action(
            user_id=test_user.id,
            action="logout",
            resource_type="auth",
            resource_id="2"
        )
        
        # Filter by action
        logs = audit_service.get_audit_logs(action="login")
        
        assert len(logs) == 1
        assert logs[0].action == "login"

    def test_get_audit_logs_filter_level(self, audit_service, test_user):
        """Test filtering audit logs by level."""
        # Create logs with different levels
        audit_service.log_action(
            user_id=test_user.id,
            action="info_action",
            resource_type="test",
            resource_id="1",
            level=AuditLevel.INFO
        )
        
        audit_service.log_action(
            user_id=test_user.id,
            action="high_action",
            resource_type="test",
            resource_id="2",
            level=AuditLevel.HIGH
        )
        
        # Filter by level
        logs = audit_service.get_audit_logs(level=AuditLevel.HIGH)
        
        assert len(logs) == 1
        assert logs[0].level == AuditLevel.HIGH

    def test_get_audit_logs_filter_time_range(self, audit_service, test_user, db_session):
        """Test filtering audit logs by time range."""
        now = datetime.utcnow()
        
        # Create log from yesterday
        old_log = AuditLog(
            user_id=test_user.id,
            action="old_action",
            resource_type="test",
            resource_id="1",
            timestamp=now - timedelta(days=1)
        )
        db_session.add(old_log)
        
        # Create log from today
        audit_service.log_action(
            user_id=test_user.id,
            action="new_action",
            resource_type="test",
            resource_id="2"
        )
        
        db_session.commit()
        
        # Filter by time range (last 12 hours)
        start_time = now - timedelta(hours=12)
        logs = audit_service.get_audit_logs(start_time=start_time)
        
        assert len(logs) == 1
        assert logs[0].action == "new_action"

    def test_get_user_activity(self, audit_service, test_user, db_session):
        """Test getting user activity."""
        # Create activity logs
        actions = ["login", "view_profile", "update_profile", "logout"]
        
        for action in actions:
            audit_service.log_action(
                user_id=test_user.id,
                action=action,
                resource_type="user",
                resource_id=str(test_user.id)
            )
        
        activity = audit_service.get_user_activity(test_user.id, days=1)
        
        assert len(activity) == 4
        assert all(log.user_id == test_user.id for log in activity)

    def test_get_security_events(self, audit_service, test_user, db_session):
        """Test getting security events."""
        # Create security-related logs
        security_actions = [
            ("login_failed", AuditLevel.MEDIUM),
            ("password_changed", AuditLevel.HIGH),
            ("account_locked", AuditLevel.CRITICAL)
        ]
        
        for action, level in security_actions:
            audit_service.log_action(
                user_id=test_user.id,
                action=action,
                resource_type="auth",
                resource_id="1",
                level=level,
                category=AuditCategory.SECURITY
            )
        
        # Create non-security log
        audit_service.log_action(
            user_id=test_user.id,
            action="view_page",
            resource_type="page",
            resource_id="1",
            level=AuditLevel.INFO,
            category=AuditCategory.USER
        )
        
        security_events = audit_service.get_security_events(days=1)
        
        # Should only return security events
        assert len(security_events) == 3
        assert all(
            log.category == AuditCategory.SECURITY or log.level in [AuditLevel.HIGH, AuditLevel.CRITICAL]
            for log in security_events
        )

    def test_get_audit_stats(self, audit_service, test_user, admin_user, db_session):
        """Test getting audit statistics."""
        # Create logs with different levels and categories
        log_data = [
            (AuditLevel.INFO, AuditCategory.USER),
            (AuditLevel.MEDIUM, AuditCategory.SECURITY),
            (AuditLevel.HIGH, AuditCategory.ADMIN),
            (AuditLevel.CRITICAL, AuditCategory.SYSTEM)
        ]
        
        for level, category in log_data:
            audit_service.log_action(
                user_id=test_user.id,
                action="test_action",
                resource_type="test",
                resource_id="1",
                level=level,
                category=category
            )
        
        # Add logs for different user
        audit_service.log_action(
            user_id=admin_user.id,
            action="admin_action",
            resource_type="admin",
            resource_id="1"
        )
        
        stats = audit_service.get_audit_stats(days=1)
        
        assert "total_logs" in stats
        assert "active_users" in stats
        assert "level_distribution" in stats
        assert "category_distribution" in stats
        assert "top_actions" in stats
        assert "daily_activity" in stats
        
        assert stats["total_logs"] >= 5
        assert stats["active_users"] >= 2

    def test_cleanup_old_logs(self, audit_service, test_user, db_session):
        """Test cleaning up old audit logs."""
        now = datetime.utcnow()
        
        # Create old INFO level logs (should be deleted)
        for i in range(3):
            old_log = AuditLog(
                user_id=test_user.id,
                action=f"old_info_{i}",
                resource_type="test",
                resource_id=str(i),
                level=AuditLevel.INFO,
                timestamp=now - timedelta(days=100)
            )
            db_session.add(old_log)
        
        # Create old HIGH level log (should be kept)
        old_high_log = AuditLog(
            user_id=test_user.id,
            action="old_high",
            resource_type="test",
            resource_id="high",
            level=AuditLevel.HIGH,
            timestamp=now - timedelta(days=100)
        )
        db_session.add(old_high_log)
        
        # Create recent INFO log (should be kept)
        recent_log = AuditLog(
            user_id=test_user.id,
            action="recent_info",
            resource_type="test",
            resource_id="recent",
            level=AuditLevel.INFO,
            timestamp=now - timedelta(days=1)
        )
        db_session.add(recent_log)
        
        db_session.commit()
        
        # Cleanup logs older than 90 days with INFO level
        deleted_count = audit_service.cleanup_old_logs(days=90, level=AuditLevel.INFO)
        
        assert deleted_count == 3
        
        # Verify remaining logs
        remaining_logs = audit_service.get_audit_logs()
        actions = [log.action for log in remaining_logs]
        
        assert "old_high" in actions  # HIGH level log should remain
        assert "recent_info" in actions  # Recent log should remain
        assert not any(action.startswith("old_info_") for action in actions)

    def test_export_audit_logs_json(self, audit_service, test_user):
        """Test exporting audit logs in JSON format."""
        # Create some logs
        for i in range(3):
            audit_service.log_action(
                user_id=test_user.id,
                action=f"action_{i}",
                resource_type="test",
                resource_id=str(i),
                details={"index": i}
            )
        
        # Export logs
        export_data = audit_service.export_audit_logs(
            format="json",
            start_time=datetime.utcnow() - timedelta(hours=1)
        )
        
        assert isinstance(export_data, str)
        
        # Parse JSON to verify structure
        import json
        logs = json.loads(export_data)
        
        assert isinstance(logs, list)
        assert len(logs) == 3
        
        # Verify log structure
        log = logs[0]
        assert "user_id" in log
        assert "action" in log
        assert "resource_type" in log
        assert "timestamp" in log

    def test_export_audit_logs_csv(self, audit_service, test_user):
        """Test exporting audit logs in CSV format."""
        # Create some logs
        audit_service.log_action(
            user_id=test_user.id,
            action="test_action",
            resource_type="test",
            resource_id="1",
            ip_address="192.168.1.1"
        )
        
        # Export logs
        export_data = audit_service.export_audit_logs(
            format="csv",
            start_time=datetime.utcnow() - timedelta(hours=1)
        )
        
        assert isinstance(export_data, str)
        
        # Verify CSV structure
        lines = export_data.strip().split('\n')
        assert len(lines) >= 2  # Header + at least 1 data row
        
        # Check header
        header = lines[0]
        assert "user_id" in header
        assert "action" in header
        assert "resource_type" in header
        
        # Check data row
        data_row = lines[1]
        assert str(test_user.id) in data_row
        assert "test_action" in data_row

    def test_get_failed_login_attempts(self, audit_service, test_user, db_session):
        """Test getting failed login attempts."""
        # Create failed login logs
        for i in range(3):
            audit_service.log_action(
                user_id=test_user.id,
                action="login_failed",
                resource_type="auth",
                resource_id=str(test_user.id),
                ip_address=f"192.168.1.{i+1}",
                level=AuditLevel.MEDIUM,
                category=AuditCategory.SECURITY
            )
        
        # Create successful login (should not be included)
        audit_service.log_action(
            user_id=test_user.id,
            action="login_success",
            resource_type="auth",
            resource_id=str(test_user.id),
            category=AuditCategory.SECURITY
        )
        
        failed_attempts = audit_service.get_failed_login_attempts(hours=24)
        
        assert len(failed_attempts) == 3
        assert all(log.action == "login_failed" for log in failed_attempts)

    def test_get_recent_activities(self, audit_service, test_user, admin_user):
        """Test getting recent activities."""
        # Create activities for different users
        audit_service.log_action(
            user_id=test_user.id,
            action="user_activity",
            resource_type="profile",
            resource_id="1"
        )
        
        audit_service.log_action(
            user_id=admin_user.id,
            action="admin_activity",
            resource_type="admin",
            resource_id="1"
        )
        
        activities = audit_service.get_recent_activities(limit=10)
        
        assert len(activities) == 2
        # Should be ordered by timestamp desc
        assert activities[0].timestamp >= activities[1].timestamp

    def test_audit_level_enum(self):
        """Test AuditLevel enum values."""
        assert AuditLevel.INFO.value == "info"
        assert AuditLevel.MEDIUM.value == "medium"
        assert AuditLevel.HIGH.value == "high"
        assert AuditLevel.CRITICAL.value == "critical"

    def test_audit_category_enum(self):
        """Test AuditCategory enum values."""
        assert AuditCategory.USER.value == "user"
        assert AuditCategory.ADMIN.value == "admin"
        assert AuditCategory.SECURITY.value == "security"
        assert AuditCategory.SYSTEM.value == "system"
        assert AuditCategory.PAYMENT.value == "payment"