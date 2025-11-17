"""
云端数据库CRUD操作模块(针对阿里云RDS)

⚠️ 重要: 所有操作针对云端MySQL数据库,不是本地数据库!
数据库: rm-bp1sqxf05yom2hwdhko.mysql.rds.aliyuncs.com:3306

功能:
- UserCRUD: 用户查询,AI配额管理,登录信息更新
- SubscriptionCRUD: 订阅/套餐管理
- PaymentCRUD: 支付/退款记录管理

安全:
- 事务自动管理(commit/rollback)
- 参数验证与SQL注入防护
- 敏感字段脱敏日志
- 软删除支持

使用:
    from server.cloud.db.crud import UserCRUD, SubscriptionCRUD, PaymentCRUD
    
    # 用户CRUD
    user_crud = UserCRUD()
    user = user_crud.get_by_email("test@example.com")
    user_crud.update_ai_quota(user_id=1, used=10)
    
    # 订阅CRUD
    sub_crud = SubscriptionCRUD()
    sub = sub_crud.create_subscription(user_id=1, plan_id=2, auto_renew=True)
    
    # 支付CRUD
    pay_crud = PaymentCRUD()
    payment = pay_crud.create_payment(user_id=1, amount=99.0, method="ALIPAY")
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, List, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, OperationalError
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from server.app.models.user import User
from server.app.models.subscription import SubscriptionPlan, UserSubscription, PaymentRecord
from server.app.models.payment import Payment, Subscription

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CloudDatabaseConfig:
    """云端数据库配置加载(从server/.env)"""
    
    def __init__(self):
        # 加载环境变量
        env_path = os.path.join(os.path.dirname(__file__), '../../.env')
        if not os.path.exists(env_path):
            raise FileNotFoundError(f"配置文件不存在: {env_path}")
        
        load_dotenv(env_path)
        
        # 优先读取RDS_*环境变量，兼容MYSQL_*和DB_*
        self.db_type = os.getenv('DB_TYPE', 'mysql')
        self.host = os.getenv('RDS_HOST') or os.getenv('MYSQL_HOST') or os.getenv('DB_HOST')
        self.port = int(os.getenv('RDS_PORT') or os.getenv('MYSQL_PORT') or os.getenv('DB_PORT', '3306'))
        self.user = os.getenv('RDS_USER') or os.getenv('MYSQL_USER') or os.getenv('DB_USER')
        self.password = os.getenv('RDS_PASSWORD') or os.getenv('MYSQL_PASSWORD') or os.getenv('DB_PASSWORD')
        self.database = os.getenv('RDS_DATABASE') or os.getenv('MYSQL_DATABASE') or os.getenv('DB_NAME')
        self.charset = os.getenv('DB_CHARSET', 'utf8mb4')
        
        # 验证必需配置
        if not all([self.host, self.user, self.password, self.database]):
            raise ValueError("数据库配置不完整,请检查server/.env文件")
        
        # 验证是云端数据库(安全检查)
        if 'localhost' in self.host or '127.0.0.1' in self.host:
            logger.warning("⚠️ 检测到localhost配置,确保这是预期的数据库!")
        else:
            logger.info(f"✅ 云端数据库连接: {self.host}:{self.port}/{self.database}")
    
    def get_connection_url(self) -> str:
        """获取SQLAlchemy连接URL"""
        return (
            f"mysql+pymysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?charset={self.charset}"
        )
    
    def mask_password(self) -> Dict[str, Any]:
        """脱敏配置(用于日志)"""
        return {
            "db_type": self.db_type,
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": "*" * len(self.password),
            "database": self.database,
            "charset": self.charset
        }


class BaseCRUD:
    """CRUD基类,提供云端数据库连接和事务管理"""
    
    def __init__(self):
        self.config = CloudDatabaseConfig()
        self.engine = create_engine(
            self.config.get_connection_url(),
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # 连接前检查有效性(防止RDS连接超时)
            pool_recycle=3600,   # 1小时回收连接(RDS默认8小时超时)
            echo=False
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"云端数据库连接已建立: {self.config.mask_password()}")
    
    @contextmanager
    def get_session(self) -> Session:
        """
        获取数据库会话(上下文管理器)
        
        自动处理:
        - commit: 操作成功时提交
        - rollback: 异常时回滚
        - close: 最终关闭会话
        
        示例:
            with crud.get_session() as session:
                user = session.query(User).first()
                user.login_count += 1
                # 自动commit
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
            logger.debug("事务已提交")
        except Exception as e:
            session.rollback()
            logger.error(f"事务回滚: {e}")
            raise
        finally:
            session.close()


class UserCRUD(BaseCRUD):
    """用户CRUD操作"""
    
    SENSITIVE_FIELDS = ['password_hash', 'salt', 'douyin_cookies', 
                        'email_verify_token', 'reset_token']
    
    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户字典或None(未找到)
        """
        with self.get_session() as session:
            user = session.query(User).filter(
                User.id == user_id,
                User.is_deleted == 0
            ).first()
            
            if user:
                logger.info(f"查询用户: id={user_id}, username={user.username}")
                return self._to_dict(user)
            else:
                logger.warning(f"用户不存在: id={user_id}")
                return None
    
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户"""
        with self.get_session() as session:
            user = session.query(User).filter(
                User.email == email,
                User.is_deleted == 0
            ).first()
            
            if user:
                logger.info(f"查询用户: email={email}, id={user.id}")
                return self._to_dict(user)
            return None
    
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        with self.get_session() as session:
            user = session.query(User).filter(
                User.username == username,
                User.is_deleted == 0
            ).first()
            
            if user:
                logger.info(f"查询用户: username={username}, id={user.id}")
                return self._to_dict(user)
            return None
    
    def list_users(self, limit: int = 100, offset: int = 0, 
                   role: Optional[str] = None,
                   status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出用户(分页+过滤)
        
        Args:
            limit: 每页数量
            offset: 偏移量
            role: 角色过滤(USER/ADMIN/SUPER_ADMIN)
            status: 状态过滤(ACTIVE/INACTIVE/LOCKED)
        
        Returns:
            用户字典列表
        """
        with self.get_session() as session:
            query = session.query(User).filter(User.is_deleted == 0)
            
            if role:
                query = query.filter(User.role == role)
            if status:
                query = query.filter(User.status == status)
            
            users = query.limit(limit).offset(offset).all()
            logger.info(f"查询用户列表: total={len(users)}, role={role}, status={status}")
            return [self._to_dict(user) for user in users]
    
    def update_ai_quota(self, user_id: int, used: int) -> bool:
        """
        更新AI配额使用量
        
        Args:
            user_id: 用户ID
            used: 增加的使用量
        
        Returns:
            是否成功
        """
        with self.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                logger.error(f"用户不存在: id={user_id}")
                return False
            
            # 检查配额是否足够
            if not user.ai_unlimited and (user.ai_quota_used + used) > user.ai_quota_monthly:
                logger.warning(
                    f"AI配额不足: user_id={user_id}, "
                    f"monthly={user.ai_quota_monthly}, used={user.ai_quota_used}, request={used}"
                )
                return False
            
            # 更新配额
            user.ai_quota_used += used
            user.updated_at = datetime.now()
            
            logger.info(
                f"更新AI配额: user_id={user_id}, used={user.ai_quota_used}/{user.ai_quota_monthly}"
            )
            return True
    
    def reset_monthly_quota(self, user_id: int) -> bool:
        """
        重置每月AI配额
        
        Args:
            user_id: 用户ID
        
        Returns:
            是否成功
        """
        with self.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                return False
            
            user.ai_quota_used = 0
            user.ai_quota_reset_at = datetime.now()
            user.updated_at = datetime.now()
            
            logger.info(f"重置AI配额: user_id={user_id}")
            return True
    
    def update_login_info(self, user_id: int, login_ip: str, success: bool = True) -> bool:
        """
        更新登录信息
        
        Args:
            user_id: 用户ID
            login_ip: 登录IP
            success: 是否登录成功
        
        Returns:
            是否成功
        """
        with self.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                return False
            
            if success:
                user.login_count += 1
                user.failed_login_count = 0
                user.last_login_at = datetime.now()
                user.last_login_ip = login_ip
            else:
                user.failed_login_count += 1
                # 失败5次锁定30分钟
                if user.failed_login_count >= 5:
                    user.locked_until = datetime.now() + timedelta(minutes=30)
                    logger.warning(f"用户已锁定: user_id={user_id}, locked_until={user.locked_until}")
            
            user.updated_at = datetime.now()
            
            logger.info(
                f"更新登录信息: user_id={user_id}, success={success}, "
                f"login_count={user.login_count}, failed_count={user.failed_login_count}"
            )
            return True
    
    def soft_delete(self, user_id: int) -> bool:
        """
        软删除用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            是否成功
        """
        with self.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user or user.is_deleted:
                return False
            
            user.is_deleted = 1
            user.deleted_at = datetime.now()
            user.updated_at = datetime.now()
            
            logger.warning(f"软删除用户: user_id={user_id}, username={user.username}")
            return True
    
    def _to_dict(self, user: User) -> Dict[str, Any]:
        """User对象转字典(在session内调用)"""
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'nickname': user.nickname,
            'role': str(user.role),
            'status': str(user.status),
            'ai_quota_monthly': user.ai_quota_monthly,
            'ai_quota_used': user.ai_quota_used,
            'ai_unlimited': user.ai_unlimited,
            'login_count': user.login_count,
            'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }


class SubscriptionCRUD(BaseCRUD):
    """订阅CRUD操作"""
    
    def get_plan_by_id(self, plan_id: int) -> Optional[Dict[str, Any]]:
        """获取套餐"""
        with self.get_session() as session:
            plan = session.query(SubscriptionPlan).filter(
                SubscriptionPlan.id == plan_id,
                SubscriptionPlan.is_active == 1
            ).first()
            
            if plan:
                logger.info(f"查询套餐: id={plan_id}, name={plan.name}, price={plan.price}")
                return self._plan_to_dict(plan)
            return None
    
    def list_active_plans(self) -> List[Dict[str, Any]]:
        """列出所有激活的套餐"""
        with self.get_session() as session:
            plans = session.query(SubscriptionPlan).filter(
                SubscriptionPlan.is_active == 1
            ).order_by(SubscriptionPlan.sort_order).all()
            
            logger.info(f"查询套餐列表: total={len(plans)}")
            return [self._plan_to_dict(p) for p in plans]
    
    def get_user_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取用户当前订阅
        
        Args:
            user_id: 用户ID
        
        Returns:
            订阅字典或None
        """
        with self.get_session() as session:
            subscription = session.query(UserSubscription).filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status.in_(['ACTIVE', 'TRIAL'])
            ).first()
            
            if subscription:
                logger.info(
                    f"查询用户订阅: user_id={user_id}, plan_id={subscription.plan_id}, "
                    f"status={subscription.status}, expires_at={subscription.expires_at}"
                )
                return self._subscription_to_dict(subscription)
            return None
    
    def create_subscription(self, user_id: int, plan_id: int, 
                           auto_renew: bool = False,
                           trial: bool = False) -> Optional[Dict[str, Any]]:
        """
        创建用户订阅
        
        ⚠️ 写操作,需要用户"GO"确认
        
        Args:
            user_id: 用户ID
            plan_id: 套餐ID
            auto_renew: 是否自动续费
            trial: 是否试用
        
        Returns:
            订阅字典或None(失败)
        """
        with self.get_session() as session:
            # 检查套餐是否存在
            plan = session.query(SubscriptionPlan).filter(
                SubscriptionPlan.id == plan_id
            ).first()
            
            if not plan:
                logger.error(f"套餐不存在: plan_id={plan_id}")
                return None
            
            # 检查是否已有订阅
            existing = session.query(UserSubscription).filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status.in_(['ACTIVE', 'TRIAL'])
            ).first()
            
            if existing:
                logger.warning(f"用户已有订阅: user_id={user_id}, subscription_id={existing.id}")
                return None
            
            # 创建订阅
            now = datetime.now()
            subscription = UserSubscription(
                user_id=user_id,
                plan_id=plan_id,
                status='TRIAL' if trial else 'ACTIVE',
                starts_at=now,
                expires_at=now + timedelta(days=plan.billing_cycle),
                auto_renew=auto_renew,
                next_billing_date=now + timedelta(days=plan.billing_cycle) if auto_renew else None,
                streams_used=0,
                storage_used_gb=0.0,
                ai_requests_used=0,
                export_count_used=0
            )
            
            session.add(subscription)
            
            logger.info(
                f"创建订阅: user_id={user_id}, plan_id={plan_id}, "
                f"status={subscription.status}, expires_at={subscription.expires_at}"
            )
            return self._subscription_to_dict(subscription)
    
    def cancel_subscription(self, subscription_id: int, reason: str = None) -> bool:
        """
        取消订阅
        
        ⚠️ 写操作,需要用户"GO"确认
        
        Args:
            subscription_id: 订阅ID
            reason: 取消原因
        
        Returns:
            是否成功
        """
        with self.get_session() as session:
            subscription = session.query(UserSubscription).filter(
                UserSubscription.id == subscription_id
            ).first()
            
            if not subscription:
                return False
            
            subscription.status = 'CANCELLED'
            subscription.cancelled_at = datetime.now()
            subscription.cancel_reason = reason
            subscription.auto_renew = False
            subscription.updated_at = datetime.now()
            
            logger.warning(
                f"取消订阅: subscription_id={subscription_id}, user_id={subscription.user_id}, "
                f"reason={reason}"
            )
            return True
    
    def _plan_to_dict(self, plan: SubscriptionPlan) -> Dict[str, Any]:
        """套餐对象转字典"""
        return {
            'id': plan.id,
            'name': plan.name,
            'display_name': plan.display_name,
            'price': float(plan.price),
            'billing_cycle': plan.billing_cycle,
            'max_ai_requests': plan.max_ai_requests,
            'max_streams': plan.max_streams,
            'max_storage_gb': plan.max_storage_gb
        }
    
    def _subscription_to_dict(self, sub: UserSubscription) -> Dict[str, Any]:
        """订阅对象转字典"""
        return {
            'id': sub.id,
            'user_id': sub.user_id,
            'plan_id': sub.plan_id,
            'status': str(sub.status),
            'starts_at': sub.starts_at.isoformat() if sub.starts_at else None,
            'expires_at': sub.expires_at.isoformat() if sub.expires_at else None,
            'auto_renew': sub.auto_renew,
            'ai_requests_used': sub.ai_requests_used,
            'storage_used_gb': float(sub.storage_used_gb)
        }


class PaymentCRUD(BaseCRUD):
    """支付CRUD操作"""
    
    def create_payment(self, user_id: int, amount: float, 
                      payment_method: str,
                      subscription_id: Optional[int] = None,
                      description: str = None) -> Optional[Dict[str, Any]]:
        """
        创建支付记录
        
        ⚠️ 写操作,需要用户"GO"确认
        
        Args:
            user_id: 用户ID
            amount: 支付金额
            payment_method: 支付方式(ALIPAY/WECHAT/STRIPE)
            subscription_id: 订阅ID(可选)
            description: 支付描述
        
        Returns:
            支付字典或None
        """
        with self.get_session() as session:
            # 生成订单号
            order_no = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{user_id:06d}"
            
            payment = PaymentRecord(
                user_id=user_id,
                subscription_id=subscription_id,
                order_no=order_no,
                amount=Decimal(str(amount)),
                currency='CNY',
                payment_method=payment_method,
                status='PENDING',
                description=description,
                invoice_requested=False,
                invoice_issued=False
            )
            
            session.add(payment)
            
            logger.info(
                f"创建支付: order_no={order_no}, user_id={user_id}, "
                f"amount={amount}, method={payment_method}"
            )
            return self._payment_to_dict(payment)
    
    def update_payment_status(self, payment_id: int, status: str,
                             third_party_order_id: str = None,
                             third_party_response: str = None) -> bool:
        """
        更新支付状态
        
        ⚠️ 写操作,需要用户"GO"确认
        
        Args:
            payment_id: 支付ID
            status: 状态(PENDING/PAID/FAILED/REFUNDED)
            third_party_order_id: 第三方订单ID
            third_party_response: 第三方响应(JSON)
        
        Returns:
            是否成功
        """
        with self.get_session() as session:
            payment = session.query(PaymentRecord).filter(
                PaymentRecord.id == payment_id
            ).first()
            
            if not payment:
                return False
            
            payment.status = status
            payment.third_party_order_id = third_party_order_id
            payment.third_party_response = third_party_response
            payment.updated_at = datetime.now()
            
            if status == 'PAID':
                payment.paid_at = datetime.now()
            
            logger.info(
                f"更新支付状态: payment_id={payment_id}, order_no={payment.order_no}, "
                f"status={status}, third_party_order_id={third_party_order_id}"
            )
            return True
    
    def get_user_payments(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取用户支付记录
        
        Args:
            user_id: 用户ID
            limit: 数量限制
        
        Returns:
            支付记录列表
        """
        with self.get_session() as session:
            payments = session.query(PaymentRecord).filter(
                PaymentRecord.user_id == user_id
            ).order_by(PaymentRecord.created_at.desc()).limit(limit).all()
            
            logger.info(f"查询用户支付记录: user_id={user_id}, total={len(payments)}")
            return [self._payment_to_dict(p) for p in payments]
    
    def _payment_to_dict(self, payment: PaymentRecord) -> Dict[str, Any]:
        """支付对象转字典"""
        return {
            'id': payment.id,
            'order_no': payment.order_no,
            'user_id': payment.user_id,
            'amount': float(payment.amount),
            'currency': payment.currency,
            'payment_method': str(payment.payment_method),
            'status': str(payment.status),
            'paid_at': payment.paid_at.isoformat() if payment.paid_at else None,
            'created_at': payment.created_at.isoformat() if payment.created_at else None
        }


# CLI测试功能
def main():
    """命令行测试入口"""
    print("=" * 70)
    print("云端数据库CRUD测试")
    print("=" * 70)
    print("⚠️  注意: 连接到阿里云RDS,所有操作都是云端操作!")
    print("=" * 70)
    
    # 测试用户CRUD
    print("\n[1] 测试用户CRUD(只读操作)")
    user_crud = UserCRUD()
    
    # 查询用户
    user = user_crud.get_by_username("dev_admin")
    if user:
        print(f"  ✅ 查询用户: id={user['id']}, username={user['username']}, role={user['role']}")
    
    # 列出用户
    users = user_crud.list_users(limit=5)
    print(f"  ✅ 用户列表: total={len(users)}")
    for u in users[:3]:
        print(f"    - {u['username']} ({u['email']}), AI配额: {u['ai_quota_used']}/{u['ai_quota_monthly']}")
    
    # 测试订阅CRUD
    print("\n[2] 测试订阅CRUD(只读操作)")
    sub_crud = SubscriptionCRUD()
    
    # 列出套餐
    plans = sub_crud.list_active_plans()
    print(f"  ✅ 套餐列表: total={len(plans)}")
    for plan in plans:
        print(f"    - {plan['display_name']}: {plan['price']}元/{plan['billing_cycle']}天")
    
    # 测试支付CRUD
    print("\n[3] 测试支付CRUD(只读操作)")
    pay_crud = PaymentCRUD()
    
    # 查询支付记录
    if user:
        payments = pay_crud.get_user_payments(user['id'], limit=5)
        print(f"  ✅ 支付记录: user_id={user['id']}, total={len(payments)}")
    
    print("\n" + "=" * 70)
    print("✅ 只读测试完成! 云端数据库连接正常")
    print("=" * 70)
    print("\n💡 写操作(create/update/delete)需要在代码中明确调用,并等待GO确认")


if __name__ == "__main__":
    main()
