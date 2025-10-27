# -*- coding: utf-8 -*-
"""
管理员服务
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
from server.app.models.user import User, UserRoleEnum
from server.app.models.payment import Subscription, Payment, Plan
from server.app.models.permission import AuditLog
from server.app.database import get_db
from server.app.core.security import hash_password
import logging

logger = logging.getLogger(__name__)


class AdminService:
    """管理员服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 用户管理 ====================
    
    def get_users(
        self,
        search: Optional[str] = None,
        role: Optional[UserRoleEnum] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[User], int]:
        """获取用户列表"""
        query = self.db.query(User)
        
        # 搜索条件
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.full_name.ilike(search_pattern)
                )
            )
        
        # 筛选条件
        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if is_verified is not None:
            query = query.filter(User.is_verified == is_verified)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
        
        return users, total
    
    def get_user_detail(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户详细信息"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # 获取用户订阅信息
        subscriptions = self.db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(desc(Subscription.created_at)).limit(5).all()
        
        # 获取用户支付记录
        payments = self.db.query(Payment).filter(
            Payment.user_id == user_id
        ).order_by(desc(Payment.created_at)).limit(5).all()
        
        # 获取用户活动日志
        audit_logs = self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(desc(AuditLog.created_at)).limit(10).all()
        
        return {
            "user": user,
            "subscriptions": subscriptions,
            "payments": payments,
            "audit_logs": audit_logs,
            "stats": {
                "total_subscriptions": len(subscriptions),
                "total_payments": len(payments),
                "total_spent": sum(p.amount for p in payments if p.status == "completed"),
                "last_login": user.last_login_at,
                "registration_date": user.created_at
            }
        }
    
    def update_user(
        self,
        user_id: int,
        **kwargs
    ) -> Optional[User]:
        """更新用户信息"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # 特殊处理密码
        if 'password' in kwargs:
            kwargs['password_hash'] = hash_password(kwargs.pop('password'))
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def ban_user(
        self,
        user_id: int,
        reason: Optional[str] = None,
        duration_days: Optional[int] = None
    ) -> Optional[User]:
        """封禁用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        user.is_active = False
        user.ban_reason = reason
        
        if duration_days:
            user.ban_until = datetime.utcnow() + timedelta(days=duration_days)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def unban_user(self, user_id: int) -> Optional[User]:
        """解封用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        user.is_active = True
        user.ban_reason = None
        user.ban_until = None
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户（软删除）"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_active = False
        user.deleted_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    # ==================== 系统监控 ====================
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # 用户统计
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        new_users_today = self.db.query(User).filter(User.created_at >= today).count()
        new_users_week = self.db.query(User).filter(User.created_at >= week_ago).count()
        new_users_month = self.db.query(User).filter(User.created_at >= month_ago).count()
        
        # 订阅统计
        total_subscriptions = self.db.query(Subscription).count()
        active_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.status == "active",
                Subscription.end_date > now
            )
        ).count()
        
        # 支付统计
        total_payments = self.db.query(Payment).count()
        completed_payments = self.db.query(Payment).filter(
            Payment.status == "completed"
        ).count()
        
        total_revenue = self.db.query(func.sum(Payment.amount)).filter(
            Payment.status == "completed"
        ).scalar() or 0
        
        revenue_today = self.db.query(func.sum(Payment.amount)).filter(
            and_(
                Payment.status == "completed",
                Payment.paid_at >= today
            )
        ).scalar() or 0
        
        revenue_week = self.db.query(func.sum(Payment.amount)).filter(
            and_(
                Payment.status == "completed",
                Payment.paid_at >= week_ago
            )
        ).scalar() or 0
        
        revenue_month = self.db.query(func.sum(Payment.amount)).filter(
            and_(
                Payment.status == "completed",
                Payment.paid_at >= month_ago
            )
        ).scalar() or 0
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "new_today": new_users_today,
                "new_week": new_users_week,
                "new_month": new_users_month
            },
            "subscriptions": {
                "total": total_subscriptions,
                "active": active_subscriptions
            },
            "payments": {
                "total": total_payments,
                "completed": completed_payments,
                "success_rate": completed_payments / total_payments if total_payments > 0 else 0
            },
            "revenue": {
                "total": float(total_revenue),
                "today": float(revenue_today),
                "week": float(revenue_week),
                "month": float(revenue_month)
            }
        }
    
    def get_user_growth_chart(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取用户增长图表数据"""
        end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=days)
        
        # 使用原生SQL查询每日新增用户数
        sql = text("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count
            FROM users 
            WHERE created_at >= :start_date AND created_at < :end_date
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        
        result = self.db.execute(sql, {"start_date": start_date, "end_date": end_date})
        data = [{"date": row.date.isoformat(), "count": row.count} for row in result]
        
        return data
    
    def get_revenue_chart(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取收入图表数据"""
        end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=days)
        
        # 使用原生SQL查询每日收入
        sql = text("""
            SELECT 
                DATE(paid_at) as date,
                SUM(amount) as revenue
            FROM payments 
            WHERE status = 'completed' 
                AND paid_at >= :start_date 
                AND paid_at < :end_date
            GROUP BY DATE(paid_at)
            ORDER BY date
        """)
        
        result = self.db.execute(sql, {"start_date": start_date, "end_date": end_date})
        data = [{"date": row.date.isoformat(), "revenue": float(row.revenue)} for row in result]
        
        return data
    
    def get_plan_distribution(self) -> List[Dict[str, Any]]:
        """获取套餐分布统计"""
        sql = text("""
            SELECT 
                p.name as plan_name,
                p.plan_type,
                COUNT(s.id) as subscription_count,
                COUNT(CASE WHEN s.status = 'active' AND s.end_date > NOW() THEN 1 END) as active_count
            FROM plans p
            LEFT JOIN subscriptions s ON p.id = s.plan_id
            WHERE p.is_active = true
            GROUP BY p.id, p.name, p.plan_type
            ORDER BY subscription_count DESC
        """)
        
        result = self.db.execute(sql)
        data = [
            {
                "plan_name": row.plan_name,
                "plan_type": row.plan_type,
                "subscription_count": row.subscription_count,
                "active_count": row.active_count
            }
            for row in result
        ]
        
        return data
    
    def get_payment_method_stats(self) -> List[Dict[str, Any]]:
        """获取支付方式统计"""
        sql = text("""
            SELECT 
                payment_method,
                COUNT(*) as count,
                SUM(amount) as total_amount,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as success_count
            FROM payments
            GROUP BY payment_method
            ORDER BY count DESC
        """)
        
        result = self.db.execute(sql)
        data = [
            {
                "payment_method": row.payment_method,
                "count": row.count,
                "total_amount": float(row.total_amount),
                "success_count": row.success_count,
                "success_rate": row.success_count / row.count if row.count > 0 else 0
            }
            for row in result
        ]
        
        return data
    
    # ==================== 内容管理 ====================
    
    def get_recent_activities(self, limit: int = 50) -> List[AuditLog]:
        """获取最近活动"""
        return self.db.query(AuditLog).order_by(
            desc(AuditLog.created_at)
        ).limit(limit).all()
    
    def get_security_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """获取安全事件"""
        query = self.db.query(AuditLog).filter(
            AuditLog.category.in_(["security", "authentication"])
        )
        
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        return query.order_by(desc(AuditLog.created_at)).limit(limit).all()
    
    def get_failed_login_attempts(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[AuditLog]:
        """获取失败登录尝试"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        return self.db.query(AuditLog).filter(
            and_(
                AuditLog.action == "login_failed",
                AuditLog.created_at >= start_time
            )
        ).order_by(desc(AuditLog.created_at)).limit(limit).all()
    
    # ==================== 系统配置 ====================
    
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        try:
            # 数据库连接测试
            self.db.execute(text("SELECT 1"))
            db_status = "healthy"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # 检查过期订阅
        expired_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.status == "active",
                Subscription.end_date <= datetime.utcnow()
            )
        ).count()
        
        # 检查待处理支付
        pending_payments = self.db.query(Payment).filter(
            Payment.status == "pending"
        ).count()
        
        return {
            "database": db_status,
            "expired_subscriptions": expired_subscriptions,
            "pending_payments": pending_payments,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """清理过期数据"""
        now = datetime.utcnow()
        
        # 更新过期订阅状态
        expired_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.status == "active",
                Subscription.end_date <= now
            )
        ).all()
        
        for subscription in expired_subscriptions:
            subscription.status = "expired"
        
        # 清理过期的审计日志（保留90天）
        cutoff_date = now - timedelta(days=90)
        deleted_logs = self.db.query(AuditLog).filter(
            and_(
                AuditLog.created_at < cutoff_date,
                AuditLog.level == "info"  # 只删除info级别的日志
            )
        ).delete()
        
        self.db.commit()
        
        return {
            "expired_subscriptions": len(expired_subscriptions),
            "deleted_audit_logs": deleted_logs
        }
    
    # ==================== 导出功能 ====================
    
    def export_users(
        self,
        format: str = "csv",
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """导出用户数据"""
        query = self.db.query(User)
        
        if filters:
            if filters.get("role"):
                query = query.filter(User.role == filters["role"])
            if filters.get("is_active") is not None:
                query = query.filter(User.is_active == filters["is_active"])
            if filters.get("start_date"):
                query = query.filter(User.created_at >= filters["start_date"])
            if filters.get("end_date"):
                query = query.filter(User.created_at <= filters["end_date"])
        
        users = query.all()
        
        if format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入标题行
            writer.writerow([
                "ID", "用户名", "邮箱", "全名", "角色", "状态", 
                "已验证", "注册时间", "最后登录"
            ])
            
            # 写入数据行
            for user in users:
                writer.writerow([
                    user.id,
                    user.username,
                    user.email,
                    user.full_name or "",
                    user.role,
                    "活跃" if user.is_active else "禁用",
                    "是" if user.is_verified else "否",
                    user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    user.last_login_at.strftime("%Y-%m-%d %H:%M:%S") if user.last_login_at else ""
                ])
            
            return output.getvalue()
        
        # 其他格式可以在这里扩展
        raise ValueError(f"Unsupported format: {format}")
    
    def export_payments(
        self,
        format: str = "csv",
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """导出支付数据"""
        query = self.db.query(Payment)
        
        if filters:
            if filters.get("status"):
                query = query.filter(Payment.status == filters["status"])
            if filters.get("payment_method"):
                query = query.filter(Payment.payment_method == filters["payment_method"])
            if filters.get("start_date"):
                query = query.filter(Payment.created_at >= filters["start_date"])
            if filters.get("end_date"):
                query = query.filter(Payment.created_at <= filters["end_date"])
        
        payments = query.all()
        
        if format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入标题行
            writer.writerow([
                "ID", "用户ID", "金额", "货币", "支付方式", "状态",
                "交易ID", "创建时间", "支付时间"
            ])
            
            # 写入数据行
            for payment in payments:
                writer.writerow([
                    payment.id,
                    payment.user_id,
                    float(payment.amount),
                    payment.currency,
                    payment.payment_method,
                    payment.status,
                    payment.transaction_id,
                    payment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    payment.paid_at.strftime("%Y-%m-%d %H:%M:%S") if payment.paid_at else ""
                ])
            
            return output.getvalue()
        
        raise ValueError(f"Unsupported format: {format}")