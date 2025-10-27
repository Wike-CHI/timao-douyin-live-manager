# -*- coding: utf-8 -*-
"""
用户服务层
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from server.app.models import User, UserSession, UserSubscription, AuditLog
from server.app.models.user import UserRoleEnum, UserStatusEnum
from server.app.models.subscription import SubscriptionStatusEnum
from server.app.database import db_session


class UserService:
    """用户服务"""
    
    @staticmethod
    def create_user(
        username: str,
        email: str,
        password: str,
        phone: Optional[str] = None,
        nickname: Optional[str] = None,
        role: UserRoleEnum = UserRoleEnum.USER,
        session: Optional[Session] = None
    ) -> User:
        """创建用户"""
        def _create_user_impl(session: Session) -> User:
            # 检查用户名和邮箱是否已存在
            existing_user = session.query(User).filter(
                or_(User.username == username, User.email == email)
            ).first()
            
            if existing_user:
                if existing_user.username == username:
                    raise ValueError("用户名已存在")
                if existing_user.email == email:
                    raise ValueError("邮箱已存在")
            
            # 检查手机号是否已存在
            if phone:
                existing_phone = session.query(User).filter(User.phone == phone).first()
                if existing_phone:
                    raise ValueError("手机号已存在")
            
            # 创建用户
            user = User(
                username=username,
                email=email,
                phone=phone,
                nickname=nickname or username,
                role=role,
                status=UserStatusEnum.ACTIVE  # 默认激活状态
            )
            user.set_password(password)
            user.generate_email_verify_token()
            
            session.add(user)
            session.flush()  # 获取用户ID
            
            # 记录审计日志
            audit_log = AuditLog.log_action(
                user_id=user.id,
                action="user_register",
                resource_type="user",
                resource_id=str(user.id),
                description=f"用户注册: {username}"
            )
            session.add(audit_log)
            
            return user
        
        if session:
            return _create_user_impl(session)
        else:
            with db_session() as session:
                user = _create_user_impl(session)
                session.commit()  # 确保提交事务
                session.refresh(user)  # 刷新对象状态
                # 将对象从会话中分离，避免DetachedInstanceError
                session.expunge(user)
                return user
    
    @staticmethod
    def authenticate_user(username_or_email: str, password: str, ip_address: str = None) -> Optional[User]:
        """用户认证"""
        with db_session() as session:
            # 查找用户
            user = session.query(User).filter(
                and_(
                    or_(User.username == username_or_email, User.email == username_or_email),
                    User.is_deleted == False
                )
            ).first()
            
            if not user:
                return None
            
            # 检查账户是否被锁定
            if user.is_locked():
                raise ValueError("账户已被锁定，请稍后再试")
            
            # 验证密码
            if not user.verify_password(password):
                # 增加失败登录次数
                user.failed_login_count += 1
                
                # 如果失败次数过多，锁定账户
                if user.failed_login_count >= 5:
                    user.lock_account(30)  # 锁定30分钟
                    
                    # 记录审计日志
                    audit_log = AuditLog.log_action(
                        user_id=user.id,
                        action="account_locked",
                        resource_type="user",
                        resource_id=str(user.id),
                        description="账户因多次登录失败被锁定",
                        ip_address=ip_address,
                        success=False
                    )
                    session.add(audit_log)
                    
                    raise ValueError("登录失败次数过多，账户已被锁定30分钟")
                
                session.commit()
                return None
            
            # 检查账户状态
            if user.status == UserStatusEnum.BANNED:
                raise ValueError("账户已被封禁")
            elif user.status == UserStatusEnum.SUSPENDED:
                raise ValueError("账户已被暂停")
            
            # 登录成功，重置失败次数
            user.failed_login_count = 0
            user.last_login_at = datetime.utcnow()
            user.last_login_ip = ip_address
            user.login_count += 1
            
            # 记录审计日志
            audit_log = AuditLog.log_action(
                user_id=user.id,
                action="user_login",
                resource_type="user",
                resource_id=str(user.id),
                description="用户登录",
                ip_address=ip_address
            )
            session.add(audit_log)
            
            # 提交事务
            session.commit()
            # 刷新用户对象以获取最新状态
            session.refresh(user)
            # 将用户对象从会话中分离，避免DetachedInstanceError
            session.expunge(user)
            
            return user
    
    @staticmethod
    def create_session(user: User, ip_address: str = None, user_agent: str = None, 
                      device_info: str = None) -> UserSession:
        """创建用户会话"""
        with db_session() as session:
            # 生成会话令牌
            session_token = secrets.token_urlsafe(32)
            refresh_token = secrets.token_urlsafe(32)
            
            # 创建会话
            user_session = UserSession(
                user_id=user.id,
                session_token=session_token,
                refresh_token=refresh_token,
                expires_at=datetime.utcnow() + timedelta(hours=24),  # 24小时过期
                refresh_expires_at=datetime.utcnow() + timedelta(days=7),  # 刷新令牌7天过期
                ip_address=ip_address,
                user_agent=user_agent,
                device_info=device_info
            )
            
            session.add(user_session)
            session.commit()  # 提交事务
            session.refresh(user_session)  # 刷新对象状态
            # 将对象从会话中分离，避免DetachedInstanceError
            session.expunge(user_session)
            return user_session
    
    @staticmethod
    def validate_session(session_token: str) -> Optional[User]:
        """验证会话令牌"""
        with db_session() as session:
            user_session = session.query(UserSession).filter(
                and_(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True
                )
            ).first()
            
            if not user_session or user_session.is_expired():
                return None
            
            # 获取用户信息
            user = session.query(User).filter(
                and_(
                    User.id == user_session.user_id,
                    User.is_deleted == False
                )
            ).first()
            
            if not user or user.status in [UserStatusEnum.BANNED, UserStatusEnum.SUSPENDED]:
                return None
            
            return user
    
    @staticmethod
    def refresh_session(refresh_token: str) -> Optional[UserSession]:
        """刷新会话令牌"""
        with db_session() as session:
            user_session = session.query(UserSession).filter(
                and_(
                    UserSession.refresh_token == refresh_token,
                    UserSession.is_active == True
                )
            ).first()
            
            if not user_session or user_session.is_refresh_expired():
                return None
            
            # 生成新的会话令牌
            user_session.session_token = secrets.token_urlsafe(32)
            user_session.expires_at = datetime.utcnow() + timedelta(hours=24)
            
            return user_session
    
    @staticmethod
    def logout_user(session_token: str) -> bool:
        """用户登出"""
        with db_session() as session:
            user_session = session.query(UserSession).filter(
                UserSession.session_token == session_token
            ).first()
            
            if user_session:
                user_session.revoke()
                
                # 记录审计日志
                audit_log = AuditLog.log_action(
                    user_id=user_session.user_id,
                    action="user_logout",
                    resource_type="user",
                    resource_id=str(user_session.user_id),
                    description="用户登出"
                )
                session.add(audit_log)
                
                return True
            
            return False
    
    @staticmethod
    def get_user_by_username(username: str, session: Optional[Session] = None) -> Optional[User]:
        """根据用户名获取用户"""
        def _get_user_impl(session: Session) -> Optional[User]:
            return session.query(User).filter(
                and_(User.username == username, User.is_deleted == False)
            ).first()
        
        if session:
            return _get_user_impl(session)
        else:
            with db_session() as session:
                return _get_user_impl(session)
    
    @staticmethod
    def get_user_by_email(email: str, session: Optional[Session] = None) -> Optional[User]:
        """根据邮箱获取用户"""
        def _get_user_impl(session: Session) -> Optional[User]:
            return session.query(User).filter(
                and_(User.email == email, User.is_deleted == False)
            ).first()
        
        if session:
            return _get_user_impl(session)
        else:
            with db_session() as session:
                return _get_user_impl(session)
    
    @staticmethod
    def get_user_by_id(user_id: int, session: Optional[Session] = None) -> Optional[User]:
        """根据ID获取用户"""
        def _get_user_impl(session: Session) -> Optional[User]:
            return session.query(User).filter(
                and_(User.id == user_id, User.is_deleted == False)
            ).first()
        
        if session:
            return _get_user_impl(session)
        else:
            with db_session() as session:
                return _get_user_impl(session)
    
    @staticmethod
    def update_user_profile(user_id: int, profile_data: Dict[str, Any], session: Optional[Session] = None) -> bool:
        """更新用户资料"""
        def _update_profile_impl(session: Session) -> bool:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # 更新允许的字段
            allowed_fields = ['nickname', 'phone', 'avatar_url', 'bio', 'location']
            for field, value in profile_data.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            
            # 记录审计日志
            audit_log = AuditLog.log_action(
                user_id=user_id,
                action="profile_updated",
                resource_type="user",
                resource_id=str(user_id),
                description="用户资料更新"
            )
            session.add(audit_log)
            
            return True
        
        if session:
            return _update_profile_impl(session)
        else:
            with db_session() as session:
                return _update_profile_impl(session)

    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str, session: Optional[Session] = None) -> bool:
        """修改密码"""
        def _change_password_impl(session: Session) -> bool:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # 验证旧密码
            if not user.verify_password(old_password):
                return False
            
            # 设置新密码
            user.set_password(new_password)
            user.updated_at = datetime.utcnow()
            
            # 记录审计日志
            audit_log = AuditLog.log_action(
                user_id=user_id,
                action="password_changed",
                resource_type="user",
                resource_id=str(user_id),
                description="用户修改密码"
            )
            session.add(audit_log)
            
            return True
        
        if session:
            return _change_password_impl(session)
        else:
            with db_session() as session:
                return _change_password_impl(session)

    @staticmethod
    def verify_email(token: str, session: Optional[Session] = None) -> bool:
        """验证邮箱"""
        def _verify_email_impl(session: Session) -> bool:
            user = session.query(User).filter(
                and_(
                    User.email_verify_token == token,
                    User.is_deleted == False
                )
            ).first()
            
            if not user:
                return False
            
            # 检查令牌是否过期
            if user.email_verify_expires_at and user.email_verify_expires_at < datetime.utcnow():
                return False
            
            # 激活用户
            user.status = UserStatusEnum.ACTIVE
            user.email_verified_at = datetime.utcnow()
            user.email_verify_token = None
            user.email_verify_expires_at = None
            
            # 记录审计日志
            audit_log = AuditLog.log_action(
                user_id=user.id,
                action="email_verified",
                resource_type="user",
                resource_id=str(user.id),
                description="邮箱验证成功"
            )
            session.add(audit_log)
            
            return True
        
        if session:
            return _verify_email_impl(session)
        else:
            with db_session() as session:
                return _verify_email_impl(session)

    @staticmethod
    def update_user_password(user_id: int, new_password: str, session: Optional[Session] = None) -> bool:
        """更新用户密码"""
        def _update_password_impl(session: Session) -> bool:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.set_password(new_password)
            
            # 记录审计日志
            audit_log = AuditLog.log_action(
                user_id=user_id,
                action="password_update",
                resource_type="user",
                resource_id=str(user_id),
                description="管理员更新密码"
            )
            session.add(audit_log)
            
            return True
        
        if session:
            return _update_password_impl(session)
        else:
            with db_session() as session:
                return _update_password_impl(session)
    
    @staticmethod
    def verify_user_email(user_id: int, session: Optional[Session] = None) -> bool:
        """验证用户邮箱"""
        def _verify_user_email_impl(session: Session) -> bool:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.status = UserStatusEnum.ACTIVE
            user.email_verified_at = datetime.utcnow()
            
            # 记录审计日志
            audit_log = AuditLog.log_action(
                user_id=user_id,
                action="email_verified",
                resource_type="user",
                resource_id=str(user_id),
                description="邮箱验证成功"
            )
            session.add(audit_log)
            
            return True
        
        if session:
            return _verify_user_email_impl(session)
        else:
            with db_session() as session:
                return _verify_user_email_impl(session)
    
    @staticmethod
    def deactivate_user(user_id: int, session: Optional[Session] = None) -> bool:
        """停用用户"""
        def _deactivate_user_impl(session: Session) -> bool:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.status = UserStatusEnum.INACTIVE
            
            # 记录审计日志
            audit_log = AuditLog.log_action(
                user_id=user_id,
                action="user_deactivated",
                resource_type="user",
                resource_id=str(user_id),
                description="用户被停用"
            )
            session.add(audit_log)
            
            return True
        
        if session:
            return _deactivate_user_impl(session)
        else:
            with db_session() as session:
                return _deactivate_user_impl(session)
    
    @staticmethod
    def activate_user(user_id: int, session: Optional[Session] = None) -> bool:
        """激活用户"""
        def _activate_user_impl(session: Session) -> bool:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.status = UserStatusEnum.ACTIVE
            
            # 记录审计日志
            audit_log = AuditLog.log_action(
                user_id=user_id,
                action="user_activated",
                resource_type="user",
                resource_id=str(user_id),
                description="用户被激活"
            )
            session.add(audit_log)
            
            return True
        
        if session:
            return _activate_user_impl(session)
        else:
            with db_session() as session:
                return _activate_user_impl(session)
    
    @staticmethod
    def delete_user(user_id: int, session: Optional[Session] = None) -> bool:
        """删除用户（软删除）"""
        def _delete_user_impl(session: Session) -> bool:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.is_deleted = True
            user.deleted_at = datetime.utcnow()
            
            # 记录审计日志
            audit_log = AuditLog.log_action(
                user_id=user_id,
                action="user_deleted",
                resource_type="user",
                resource_id=str(user_id),
                description="用户被删除"
            )
            session.add(audit_log)
            
            return True
        
        if session:
            return _delete_user_impl(session)
        else:
            with db_session() as session:
                return _delete_user_impl(session)
    
    @staticmethod
    def get_users_with_pagination(skip: int = 0, limit: int = 10, session: Optional[Session] = None) -> List[User]:
        """分页获取用户列表"""
        def _get_users_impl(session: Session) -> List[User]:
            return session.query(User).filter(
                User.is_deleted == False
            ).offset(skip).limit(limit).all()
        
        if session:
            return _get_users_impl(session)
        else:
            with db_session() as session:
                return _get_users_impl(session)
    
    @staticmethod
    def search_users(query: str, skip: int = 0, limit: int = 10, session: Optional[Session] = None) -> List[User]:
        """搜索用户"""
        def _search_users_impl(session: Session) -> List[User]:
            search_pattern = f"%{query}%"
            return session.query(User).filter(
                and_(
                    User.is_deleted == False,
                    or_(
                        User.username.ilike(search_pattern),
                        User.email.ilike(search_pattern),
                        User.nickname.ilike(search_pattern)
                    )
                )
            ).offset(skip).limit(limit).all()
        
        if session:
            return _search_users_impl(session)
        else:
            with db_session() as session:
                return _search_users_impl(session)
    
    @staticmethod
    def get_active_users(limit: int = 100, session: Optional[Session] = None) -> List[User]:
        """获取活跃用户列表"""
        def _get_active_users_impl(session: Session) -> List[User]:
            return session.query(User).filter(
                and_(
                    User.is_deleted == False,
                    User.status == UserStatusEnum.ACTIVE
                )
            ).limit(limit).all()
        
        if session:
            return _get_active_users_impl(session)
        else:
            with db_session() as session:
                return _get_active_users_impl(session)

    @staticmethod
    def record_login(user_id: int, ip_address: str = None) -> bool:
        """记录用户登录"""
        with db_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.login_count += 1
            user.last_login_at = datetime.utcnow()
            
            # 记录审计日志
            audit_log = AuditLog.log_action(
                user_id=user_id,
                action="user_login",
                resource_type="user",
                resource_id=str(user_id),
                description="用户登录",
                ip_address=ip_address
            )
            session.add(audit_log)
            
            return True
    
    @staticmethod
    def update_last_activity(user_id: int) -> bool:
        """更新用户最后活动时间"""
        with db_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.last_activity_at = datetime.utcnow()
            return True
    
    @staticmethod
    def get_user_login_history(user_id: int, limit: int = 10) -> List[AuditLog]:
        """获取用户登录历史"""
        with db_session() as session:
            return session.query(AuditLog).filter(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.action == "user_login"
                )
            ).order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def check_password_strength(password: str) -> Dict[str, Any]:
        """检查密码强度"""
        import re
        
        score = 0
        feedback = []
        
        # 长度检查
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("密码长度至少8位")
        
        # 包含小写字母
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("需要包含小写字母")
        
        # 包含大写字母
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("需要包含大写字母")
        
        # 包含数字
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("需要包含数字")
        
        # 包含特殊字符
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("需要包含特殊字符")
        
        strength_levels = ["很弱", "弱", "一般", "强", "很强"]
        strength = strength_levels[min(score, 4)]
        
        return {
            "score": score,
            "strength": strength,
            "feedback": feedback,
            "is_strong": score >= 4
        }
    
    @staticmethod
    def get_user_subscription(user_id: int) -> Optional[UserSubscription]:
        """获取用户当前订阅"""
        with db_session() as session:
            return session.query(UserSubscription).filter(
                and_(
                    UserSubscription.user_id == user_id,
                    UserSubscription.status == SubscriptionStatusEnum.ACTIVE
                )
            ).first()
    
    @staticmethod
    def get_user_stats(user_id: int) -> Dict[str, Any]:
        """获取用户统计信息"""
        with db_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            # 获取订阅信息
            subscription = session.query(UserSubscription).filter(
                and_(
                    UserSubscription.user_id == user_id,
                    UserSubscription.status == SubscriptionStatusEnum.ACTIVE
                )
            ).first()
            
            # 获取登录统计
            active_sessions = session.query(UserSession).filter(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            ).count()
            
            return {
                "user_id": user_id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "status": user.status.value,
                "login_count": user.login_count,
                "last_login_at": user.last_login_at,
                "active_sessions": active_sessions,
                "subscription": {
                    "plan_name": subscription.plan.name if subscription else None,
                    "expires_at": subscription.expires_at if subscription else None,
                    "auto_renew": subscription.auto_renew if subscription else False
                } if subscription else None,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }

    @staticmethod
    def send_verification_email(user_id: int) -> bool:
        """发送验证邮件"""
        with db_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # 生成新的验证令牌
            user.generate_email_verify_token()
            
            # 这里应该集成邮件服务发送邮件
            # 暂时只记录审计日志
            audit_log = AuditLog.log_action(
                user_id=user_id,
                action="verification_email_sent",
                resource_type="user",
                resource_id=str(user_id),
                description="发送验证邮件"
            )
            session.add(audit_log)
            
            return True

    @staticmethod
    def send_password_reset_email(email: str) -> bool:
        """发送密码重置邮件"""
        with db_session() as session:
            user = session.query(User).filter(
                and_(User.email == email, User.is_deleted == False)
            ).first()
            
            if not user:
                # 即使用户不存在也返回True，避免泄露用户信息
                return True
            
            # 生成密码重置令牌
            user.generate_password_reset_token()
            
            # 这里应该集成邮件服务发送邮件
            # 暂时只记录审计日志
            audit_log = AuditLog.log_action(
                user_id=user.id,
                action="password_reset_email_sent",
                resource_type="user",
                resource_id=str(user.id),
                description="发送密码重置邮件"
            )
            session.add(audit_log)
            
            return True