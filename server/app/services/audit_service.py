# -*- coding: utf-8 -*-
"""
审计日志服务
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta
import json
import logging
from enum import Enum

from app.models import AuditLog, User
from app.database import DatabaseManager

logger = logging.getLogger(__name__)


class AuditLevel(str, Enum):
    """审计级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditCategory(str, Enum):
    """审计分类"""
    AUTH = "auth"  # 认证相关
    USER = "user"  # 用户管理
    SUBSCRIPTION = "subscription"  # 订阅管理
    PAYMENT = "payment"  # 支付相关
    ADMIN = "admin"  # 管理员操作
    SECURITY = "security"  # 安全相关
    SYSTEM = "system"  # 系统操作
    DATA = "data"  # 数据操作


class AuditService:
    """审计日志服务"""
    
    def __init__(self, db_manager=None):
        # 如果没有提供db_manager，则使用全局的数据库连接
        if db_manager is None:
            from app.database import db_manager as global_db_manager
            self.db_manager = global_db_manager
        else:
            self.db_manager = db_manager
        
        # 高风险操作定义
        self.high_risk_actions = {
            "delete_user", "ban_user", "change_user_role", "delete_subscription",
            "refund_payment", "system_config_change", "database_operation",
            "security_setting_change", "admin_login", "password_reset"
        }
        
        # 关键资源定义
        self.critical_resources = {
            "user", "admin", "payment", "subscription_plan", "system_config"
        }
    
    async def log_action(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        level: Optional[AuditLevel] = None,
        category: Optional[AuditCategory] = None
    ) -> bool:
        """记录审计日志"""
        try:
            # 自动确定审计级别
            if level is None:
                level = self._determine_audit_level(action, resource_type)
            
            # 自动确定审计分类
            if category is None:
                category = self._determine_audit_category(action, resource_type)
            
            with self.db_manager.get_session() as db:
                audit_log = AuditLog(
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    details=details,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                    level=level.value,
                    category=category.value,
                    timestamp=datetime.utcnow()
                )
                
                db.add(audit_log)
                db.commit()
                
                # 对于高风险操作，记录额外日志
                if level in [AuditLevel.HIGH, AuditLevel.CRITICAL]:
                    logger.warning(
                        f"高风险操作: 用户{user_id} 执行{action} "
                        f"资源{resource_type}:{resource_id} "
                        f"详情:{details} IP:{ip_address}"
                    )
                
                return True
                
        except Exception as e:
            logger.error(f"记录审计日志失败: {e}")
            return False
    
    def _determine_audit_level(self, action: str, resource_type: str) -> AuditLevel:
        """确定审计级别"""
        if action in self.high_risk_actions:
            return AuditLevel.HIGH
        
        if resource_type in self.critical_resources:
            return AuditLevel.MEDIUM
        
        if action.startswith(("delete", "remove", "ban", "disable")):
            return AuditLevel.MEDIUM
        
        if action.startswith(("create", "update", "change")):
            return AuditLevel.LOW
        
        return AuditLevel.LOW
    
    def _determine_audit_category(self, action: str, resource_type: str) -> AuditCategory:
        """确定审计分类"""
        if "auth" in action or "login" in action or "logout" in action:
            return AuditCategory.AUTH
        
        if "user" in resource_type:
            return AuditCategory.USER
        
        if "subscription" in resource_type:
            return AuditCategory.SUBSCRIPTION
        
        if "payment" in resource_type:
            return AuditCategory.PAYMENT
        
        if "admin" in action or "admin" in resource_type:
            return AuditCategory.ADMIN
        
        if "security" in resource_type or "2fa" in action:
            return AuditCategory.SECURITY
        
        if "system" in resource_type:
            return AuditCategory.SYSTEM
        
        return AuditCategory.DATA
    
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        level: Optional[AuditLevel] = None,
        category: Optional[AuditCategory] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """获取审计日志"""
        try:
            with self.db_manager.get_session() as db:
                query = db.query(AuditLog)
                
                # 构建过滤条件
                filters = []
                
                if user_id:
                    filters.append(AuditLog.user_id == user_id)
                
                if action:
                    filters.append(AuditLog.action.ilike(f"%{action}%"))
                
                if resource_type:
                    filters.append(AuditLog.resource_type == resource_type)
                
                if resource_id:
                    filters.append(AuditLog.resource_id == resource_id)
                
                if level:
                    filters.append(AuditLog.level == level.value)
                
                if category:
                    filters.append(AuditLog.category == category.value)
                
                if start_time:
                    filters.append(AuditLog.timestamp >= start_time)
                
                if end_time:
                    filters.append(AuditLog.timestamp <= end_time)
                
                if ip_address:
                    filters.append(AuditLog.ip_address == ip_address)
                
                if filters:
                    query = query.filter(and_(*filters))
                
                # 获取总数
                total = query.count()
                
                # 分页和排序
                logs = query.order_by(desc(AuditLog.timestamp))\
                           .offset((page - 1) * page_size)\
                           .limit(page_size)\
                           .all()
                
                # 格式化结果
                result_logs = []
                for log in logs:
                    log_dict = {
                        "id": log.id,
                        "user_id": log.user_id,
                        "action": log.action,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id,
                        "details": log.details,
                        "ip_address": log.ip_address,
                        "user_agent": log.user_agent,
                        "request_id": log.request_id,
                        "level": log.level,
                        "category": log.category,
                        "timestamp": log.timestamp
                    }
                    
                    # 添加用户信息
                    if log.user_id:
                        user = db.query(User).filter(User.id == log.user_id).first()
                        if user:
                            log_dict["username"] = user.username
                            log_dict["user_email"] = user.email
                    
                    result_logs.append(log_dict)
                
                return {
                    "logs": result_logs,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size
                }
                
        except Exception as e:
            logger.error(f"获取审计日志失败: {e}")
            return {"logs": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}
    
    async def get_user_activity(
        self,
        user_id: str,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取用户活动记录"""
        try:
            start_time = datetime.utcnow() - timedelta(days=days)
            
            with self.db_manager.get_session() as db:
                logs = db.query(AuditLog)\
                        .filter(
                            AuditLog.user_id == user_id,
                            AuditLog.timestamp >= start_time
                        )\
                        .order_by(desc(AuditLog.timestamp))\
                        .limit(limit)\
                        .all()
                
                return [
                    {
                        "action": log.action,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id,
                        "details": log.details,
                        "timestamp": log.timestamp,
                        "level": log.level,
                        "category": log.category
                    }
                    for log in logs
                ]
                
        except Exception as e:
            logger.error(f"获取用户活动记录失败: {e}")
            return []
    
    async def get_security_events(
        self,
        hours: int = 24,
        level: Optional[AuditLevel] = None
    ) -> List[Dict[str, Any]]:
        """获取安全事件"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            with self.db_manager.get_session() as db:
                query = db.query(AuditLog)\
                         .filter(
                             AuditLog.timestamp >= start_time,
                             or_(
                                 AuditLog.category == AuditCategory.SECURITY.value,
                                 AuditLog.level.in_([AuditLevel.HIGH.value, AuditLevel.CRITICAL.value])
                             )
                         )
                
                if level:
                    query = query.filter(AuditLog.level == level.value)
                
                events = query.order_by(desc(AuditLog.timestamp)).all()
                
                return [
                    {
                        "id": event.id,
                        "user_id": event.user_id,
                        "action": event.action,
                        "resource_type": event.resource_type,
                        "resource_id": event.resource_id,
                        "details": event.details,
                        "ip_address": event.ip_address,
                        "timestamp": event.timestamp,
                        "level": event.level,
                        "category": event.category
                    }
                    for event in events
                ]
                
        except Exception as e:
            logger.error(f"获取安全事件失败: {e}")
            return []
    
    async def get_audit_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取审计统计信息"""
        try:
            if not start_time:
                start_time = datetime.utcnow() - timedelta(days=30)
            if not end_time:
                end_time = datetime.utcnow()
            
            with self.db_manager.get_session() as db:
                base_query = db.query(AuditLog).filter(
                    AuditLog.timestamp >= start_time,
                    AuditLog.timestamp <= end_time
                )
                
                # 总日志数
                total_logs = base_query.count()
                
                # 按级别统计
                level_stats = db.query(
                    AuditLog.level,
                    func.count(AuditLog.id).label('count')
                ).filter(
                    AuditLog.timestamp >= start_time,
                    AuditLog.timestamp <= end_time
                ).group_by(AuditLog.level).all()
                
                # 按分类统计
                category_stats = db.query(
                    AuditLog.category,
                    func.count(AuditLog.id).label('count')
                ).filter(
                    AuditLog.timestamp >= start_time,
                    AuditLog.timestamp <= end_time
                ).group_by(AuditLog.category).all()
                
                # 按操作统计
                action_stats = db.query(
                    AuditLog.action,
                    func.count(AuditLog.id).label('count')
                ).filter(
                    AuditLog.timestamp >= start_time,
                    AuditLog.timestamp <= end_time
                ).group_by(AuditLog.action)\
                .order_by(desc(func.count(AuditLog.id)))\
                .limit(10).all()
                
                # 活跃用户统计
                active_users = db.query(
                    func.count(func.distinct(AuditLog.user_id))
                ).filter(
                    AuditLog.timestamp >= start_time,
                    AuditLog.timestamp <= end_time,
                    AuditLog.user_id.isnot(None)
                ).scalar()
                
                # 按日期统计
                daily_stats = db.query(
                    func.date(AuditLog.timestamp).label('date'),
                    func.count(AuditLog.id).label('count')
                ).filter(
                    AuditLog.timestamp >= start_time,
                    AuditLog.timestamp <= end_time
                ).group_by(func.date(AuditLog.timestamp))\
                .order_by(func.date(AuditLog.timestamp)).all()
                
                return {
                    "total_logs": total_logs,
                    "active_users": active_users,
                    "level_distribution": {
                        level: count for level, count in level_stats
                    },
                    "category_distribution": {
                        category: count for category, count in category_stats
                    },
                    "top_actions": [
                        {"action": action, "count": count}
                        for action, count in action_stats
                    ],
                    "daily_activity": [
                        {"date": str(date), "count": count}
                        for date, count in daily_stats
                    ],
                    "period": {
                        "start_time": start_time,
                        "end_time": end_time
                    }
                }
                
        except Exception as e:
            logger.error(f"获取审计统计信息失败: {e}")
            return {}
    
    async def cleanup_old_logs(self, days: int = 90) -> int:
        """清理旧的审计日志"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            
            with self.db_manager.get_session() as db:
                # 只清理低级别的日志，保留高级别日志
                deleted_count = db.query(AuditLog)\
                                 .filter(
                                     AuditLog.timestamp < cutoff_time,
                                     AuditLog.level == AuditLevel.LOW.value
                                 )\
                                 .delete()
                
                db.commit()
                
                logger.info(f"清理了 {deleted_count} 条旧审计日志")
                return deleted_count
                
        except Exception as e:
            logger.error(f"清理旧审计日志失败: {e}")
            return 0
    
    async def export_audit_logs(
        self,
        start_time: datetime,
        end_time: datetime,
        format: str = "json"
    ) -> Optional[str]:
        """导出审计日志"""
        try:
            logs_data = await self.get_audit_logs(
                start_time=start_time,
                end_time=end_time,
                page_size=10000  # 大批量导出
            )
            
            if format == "json":
                return json.dumps(logs_data, default=str, ensure_ascii=False, indent=2)
            elif format == "csv":
                # 简单的CSV格式
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # 写入标题行
                writer.writerow([
                    "时间", "用户ID", "用户名", "操作", "资源类型", "资源ID",
                    "级别", "分类", "IP地址", "详情"
                ])
                
                # 写入数据行
                for log in logs_data["logs"]:
                    writer.writerow([
                        log["timestamp"],
                        log["user_id"],
                        log.get("username", ""),
                        log["action"],
                        log["resource_type"],
                        log["resource_id"],
                        log["level"],
                        log["category"],
                        log["ip_address"],
                        json.dumps(log["details"], ensure_ascii=False) if log["details"] else ""
                    ])
                
                return output.getvalue()
            
            return None
            
        except Exception as e:
            logger.error(f"导出审计日志失败: {e}")
            return None


# 全局审计服务实例
audit_service = AuditService()