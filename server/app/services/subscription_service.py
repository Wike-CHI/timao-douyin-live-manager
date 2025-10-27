# -*- coding: utf-8 -*-
"""
订阅服务业务逻辑
"""

import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from server.app.database import DatabaseManager
from server.app.models.subscription import (
    SubscriptionPlan, UserSubscription, PaymentRecord,
    SubscriptionPlanTypeEnum, SubscriptionStatusEnum, 
    PaymentStatusEnum, PaymentMethodEnum
)
from server.app.models.permission import AuditLog
from server.app.models.user import User


class SubscriptionService:
    """订阅服务"""
    
    @staticmethod
    def get_subscription_plans(active_only: bool = True) -> List[SubscriptionPlan]:
        """获取订阅套餐列表"""
        with DatabaseManager.get_session() as session:
            query = session.query(SubscriptionPlan)
            
            if active_only:
                query = query.filter(SubscriptionPlan.is_active == True)
            
            return query.order_by(SubscriptionPlan.price).all()
    
    @staticmethod
    def get_subscription_plan(plan_id: int) -> Optional[SubscriptionPlan]:
        """获取订阅套餐"""
        with DatabaseManager.get_session() as session:
            return session.query(SubscriptionPlan).filter(
                SubscriptionPlan.id == plan_id,
                SubscriptionPlan.is_active == True
            ).first()
    
    @staticmethod
    def get_user_subscription(user_id: int) -> Optional[UserSubscription]:
        """获取用户当前订阅"""
        from server.app.database import db_session
        
        with db_session() as session:
            return session.query(UserSubscription).filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status == SubscriptionStatusEnum.ACTIVE
            ).first()
    
    @staticmethod
    def create_payment(
        user_id: int,
        plan_id: int,
        payment_method: PaymentMethodEnum,
        return_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        client_ip: Optional[str] = None
    ) -> PaymentRecord:
        """创建支付订单"""
        with DatabaseManager.get_session() as session:
            # 获取套餐信息
            plan = session.query(SubscriptionPlan).filter(
                SubscriptionPlan.id == plan_id,
                SubscriptionPlan.is_active == True
            ).first()
            
            if not plan:
                raise ValueError("套餐不存在或已下架")
            
            # 检查用户是否存在
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            # 创建支付记录
            payment = PaymentRecord(
                user_id=user_id,
                subscription_plan_id=plan_id,
                amount=plan.price,
                currency="CNY",
                payment_method=payment_method,
                status=PaymentStatusEnum.PENDING,
                payment_data={
                    "plan_name": plan.name,
                    "return_url": return_url,
                    "cancel_url": cancel_url,
                    "client_ip": client_ip,
                    "expires_at": (datetime.utcnow() + timedelta(minutes=30)).isoformat()
                }
            )
            
            # 根据支付方式生成支付信息
            if payment_method == PaymentMethodEnum.ALIPAY:
                payment.payment_data.update({
                    "payment_url": f"https://openapi.alipay.com/gateway.do?payment_id={payment.id}",
                    "qr_code": f"alipay://pay?payment_id={payment.id}"
                })
            elif payment_method == PaymentMethodEnum.WECHAT:
                payment.payment_data.update({
                    "payment_url": f"https://api.mch.weixin.qq.com/pay/unifiedorder?payment_id={payment.id}",
                    "qr_code": f"weixin://wxpay/bizpayurl?payment_id={payment.id}"
                })
            elif payment_method == PaymentMethodEnum.STRIPE:
                payment.payment_data.update({
                    "payment_url": f"https://checkout.stripe.com/pay?payment_id={payment.id}",
                    "session_id": f"cs_test_{payment.id}"
                })
            
            session.add(payment)
            session.commit()
            session.refresh(payment)
            
            # 记录审计日志
            AuditLog.log_action(
                user_id=user_id,
                action="CREATE_PAYMENT",
                resource_type="PaymentRecord",
                resource_id=payment.id,
                details={
                    "plan_id": plan_id,
                    "amount": plan.price,
                    "payment_method": payment_method.value
                },
                ip_address=client_ip
            )
            
            return payment
    
    @staticmethod
    def confirm_payment(
        payment_id: int,
        transaction_id: str,
        payment_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """确认支付"""
        with DatabaseManager.get_session() as session:
            payment = session.query(PaymentRecord).filter(
                PaymentRecord.id == payment_id
            ).first()
            
            if not payment:
                raise ValueError("支付记录不存在")
            
            if payment.status != PaymentStatusEnum.PENDING:
                raise ValueError("支付状态不正确")
            
            # 检查支付是否过期
            expires_at_str = payment.payment_data.get("expires_at")
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                if datetime.utcnow() > expires_at:
                    payment.status = PaymentStatusEnum.EXPIRED
                    session.commit()
                    raise ValueError("支付已过期")
            
            # 更新支付状态
            payment.status = PaymentStatusEnum.COMPLETED
            payment.transaction_id = transaction_id
            payment.paid_at = datetime.utcnow()
            
            if payment_data:
                payment.payment_data.update(payment_data)
            
            # 创建或更新用户订阅
            SubscriptionService._create_or_update_subscription(
                session, payment.user_id, payment.subscription_plan_id
            )
            
            session.commit()
            
            # 记录审计日志
            AuditLog.log_action(
                user_id=payment.user_id,
                action="CONFIRM_PAYMENT",
                resource_type="PaymentRecord",
                resource_id=payment.id,
                details={
                    "transaction_id": transaction_id,
                    "amount": payment.amount
                }
            )
            
            return True
    
    @staticmethod
    def _create_or_update_subscription(
        session: Session,
        user_id: int,
        plan_id: int
    ):
        """创建或更新用户订阅"""
        plan = session.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == plan_id
        ).first()
        
        if not plan:
            raise ValueError("套餐不存在")
        
        # 查找现有订阅
        existing_subscription = session.query(UserSubscription).filter(
            UserSubscription.user_id == user_id,
            UserSubscription.status == SubscriptionStatusEnum.ACTIVE
        ).first()
        
        now = datetime.utcnow()
        
        if existing_subscription:
            # 延长现有订阅
            if existing_subscription.end_date > now:
                # 从当前结束时间开始延长
                start_date = existing_subscription.end_date
            else:
                # 从现在开始延长
                start_date = now
            
            existing_subscription.subscription_plan_id = plan_id
            existing_subscription.start_date = start_date
            existing_subscription.end_date = start_date + timedelta(days=plan.duration_days)
            existing_subscription.status = SubscriptionStatusEnum.ACTIVE
            existing_subscription.auto_renew = True
            existing_subscription.usage_stats = {}
            
        else:
            # 创建新订阅
            subscription = UserSubscription(
                user_id=user_id,
                subscription_plan_id=plan_id,
                status=SubscriptionStatusEnum.ACTIVE,
                start_date=now,
                end_date=now + timedelta(days=plan.duration_days),
                auto_renew=True,
                usage_stats={}
            )
            session.add(subscription)
    
    @staticmethod
    def get_payment_history(
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[PaymentRecord]:
        """获取支付历史"""
        with DatabaseManager.get_session() as session:
            return session.query(PaymentRecord).filter(
                PaymentRecord.user_id == user_id
            ).order_by(
                PaymentRecord.created_at.desc()
            ).limit(limit).offset(offset).all()
    
    @staticmethod
    def update_auto_renew(subscription_id: int, auto_renew: bool) -> bool:
        """更新自动续费设置"""
        with DatabaseManager.get_session() as session:
            subscription = session.query(UserSubscription).filter(
                UserSubscription.id == subscription_id
            ).first()
            
            if not subscription:
                return False
            
            subscription.auto_renew = auto_renew
            session.commit()
            
            # 记录审计日志
            AuditLog.log_action(
                user_id=subscription.user_id,
                action="UPDATE_AUTO_RENEW",
                resource_type="UserSubscription",
                resource_id=subscription_id,
                details={"auto_renew": auto_renew}
            )
            
            return True
    
    @staticmethod
    def cancel_subscription(subscription_id: int) -> bool:
        """取消订阅"""
        with DatabaseManager.get_session() as session:
            subscription = session.query(UserSubscription).filter(
                UserSubscription.id == subscription_id
            ).first()
            
            if not subscription:
                return False
            
            subscription.status = SubscriptionStatusEnum.CANCELLED
            subscription.auto_renew = False
            session.commit()
            
            # 记录审计日志
            AuditLog.log_action(
                user_id=subscription.user_id,
                action="CANCEL_SUBSCRIPTION",
                resource_type="UserSubscription",
                resource_id=subscription_id,
                details={"cancelled_at": datetime.utcnow().isoformat()}
            )
            
            return True
    
    @staticmethod
    def record_ai_usage(user_id: int, tokens: int = 0, requests: int = 1) -> None:
        """记录用户的 AI 使用量"""
        tokens = max(0, int(tokens or 0))
        requests = max(0, int(requests or 0))
        if tokens == 0 and requests == 0:
            return
        
        with DatabaseManager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return
            
            current_used = user.ai_quota_used or 0
            if tokens > 0:
                user.ai_quota_used = current_used + tokens
            elif current_used < 1 and requests > 0:
                user.ai_quota_used = 1
            if not user.ai_quota_reset_at:
                user.ai_quota_reset_at = datetime.utcnow()
            
            subscription = session.query(UserSubscription).filter(
                and_(
                    UserSubscription.user_id == user_id,
                    UserSubscription.status == SubscriptionStatusEnum.ACTIVE
                )
            ).first()
            
            if subscription:
                if requests > 0:
                    subscription.ai_requests_used = (subscription.ai_requests_used or 0) + requests
                
                usage_stats = subscription.usage_stats or {}
                usage_stats = dict(usage_stats)
                if tokens > 0:
                    usage_stats["ai_tokens_used"] = usage_stats.get("ai_tokens_used", 0) + tokens
                if requests > 0:
                    usage_stats["ai_requests_used"] = usage_stats.get(
                        "ai_requests_used",
                        subscription.ai_requests_used or 0
                    )
                subscription.usage_stats = usage_stats
            
            session.commit()
    
    @staticmethod
    def get_usage_stats(user_id: int) -> Dict[str, Any]:
        """获取使用统计"""
        with DatabaseManager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "has_subscription": False,
                    "plan_name": None,
                    "usage_stats": {},
                    "limits": {},
                    "features": {},
                    "ai_usage": {
                        "tokens_used": 0,
                        "token_quota": 0,
                        "token_limit": None,
                        "requests_used": 0,
                        "request_limit": None,
                        "first_free_used": False,
                    },
                }
            
            subscription = session.query(UserSubscription).filter(
                and_(
                    UserSubscription.user_id == user_id,
                    UserSubscription.status == SubscriptionStatusEnum.ACTIVE
                )
            ).first()
            
            has_subscription = subscription is not None
            usage_stats: Dict[str, Any] = subscription.usage_stats or {} if subscription else {}
            limits = subscription.plan.usage_limits if subscription else {}
            features = subscription.plan.features if subscription else None
            
            ai_usage = {
                "tokens_used": int(user.ai_quota_used or 0),
                "token_quota": None if user.ai_unlimited else int(user.ai_quota_monthly or 0),
                "token_limit": None,
                "requests_used": 0,
                "request_limit": None,
                "first_free_used": (user.ai_quota_used or 0) > 0,
            }
            
            if subscription:
                stats = subscription.usage_stats or {}
                tokens_used = int(stats.get("ai_tokens_used", 0))
                if tokens_used:
                    ai_usage["tokens_used"] = max(ai_usage["tokens_used"], tokens_used)
                
                ai_usage["requests_used"] = int(stats.get("ai_requests_used", subscription.ai_requests_used or 0))
                ai_usage["request_limit"] = subscription.plan.max_ai_requests
                
                if isinstance(limits, dict):
                    ai_usage["token_limit"] = limits.get("ai_tokens")
            
            return {
                "has_subscription": has_subscription,
                "plan_name": subscription.plan.name if subscription else None,
                "plan_type": subscription.plan.plan_type.value if subscription else None,
                "status": subscription.status.value if subscription else None,
                "start_date": subscription.start_date.isoformat() if subscription else None,
                "end_date": subscription.end_date.isoformat() if subscription else None,
                "auto_renew": subscription.auto_renew if subscription else False,
                "usage_stats": usage_stats,
                "limits": limits,
                "features": features,
                "ai_usage": ai_usage,
            }
    
    @staticmethod
    def handle_payment_webhook(body: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        """处理支付回调webhook"""
        # 这里需要根据具体的支付提供商实现webhook验证和处理逻辑
        # 以下是示例实现
        
        try:
            # 解析请求体
            data = json.loads(body.decode('utf-8'))
            
            # 验证签名（示例）
            signature = headers.get('x-signature')
            if not SubscriptionService._verify_webhook_signature(body, signature):
                raise ValueError("Invalid webhook signature")
            
            # 处理不同类型的事件
            event_type = data.get('event_type')
            
            if event_type == 'payment.completed':
                payment_id = data.get('payment_id')
                transaction_id = data.get('transaction_id')
                
                if payment_id and transaction_id:
                    SubscriptionService.confirm_payment(
                        payment_id=payment_id,
                        transaction_id=transaction_id,
                        payment_data=data
                    )
            
            elif event_type == 'payment.failed':
                payment_id = data.get('payment_id')
                if payment_id:
                    with DatabaseManager.get_session() as session:
                        payment = session.query(PaymentRecord).filter(
                            PaymentRecord.id == payment_id
                        ).first()
                        
                        if payment:
                            payment.status = PaymentStatusEnum.FAILED
                            payment.payment_data.update(data)
                            session.commit()
            
            return {"status": "success", "event_type": event_type}
            
        except Exception as e:
            # 记录错误日志
            print(f"Webhook处理失败: {str(e)}")
            raise
    
    @staticmethod
    def _verify_webhook_signature(body: bytes, signature: str) -> bool:
        """验证webhook签名"""
        # 这里需要根据具体的支付提供商实现签名验证
        # 以下是示例实现
        
        if not signature:
            return False
        
        # 示例：使用HMAC-SHA256验证
        secret = "your_webhook_secret"  # 应该从配置中获取
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    @staticmethod
    def check_subscription_expiry():
        """检查订阅过期（定时任务）"""
        with DatabaseManager.get_session() as session:
            now = datetime.utcnow()
            
            # 查找即将过期的订阅
            expiring_subscriptions = session.query(UserSubscription).filter(
                UserSubscription.status == SubscriptionStatusEnum.ACTIVE,
                UserSubscription.end_date <= now + timedelta(days=3),
                UserSubscription.end_date > now
            ).all()
            
            # 发送过期提醒（这里可以集成邮件或短信服务）
            for subscription in expiring_subscriptions:
                print(f"订阅即将过期: 用户ID {subscription.user_id}, 过期时间 {subscription.end_date}")
            
            # 处理已过期的订阅
            expired_subscriptions = session.query(UserSubscription).filter(
                UserSubscription.status == SubscriptionStatusEnum.ACTIVE,
                UserSubscription.end_date <= now
            ).all()
            
            for subscription in expired_subscriptions:
                if subscription.auto_renew:
                    # 尝试自动续费
                    try:
                        SubscriptionService._auto_renew_subscription(session, subscription)
                    except Exception as e:
                        print(f"自动续费失败: 用户ID {subscription.user_id}, 错误: {str(e)}")
                        subscription.status = SubscriptionStatusEnum.EXPIRED
                else:
                    subscription.status = SubscriptionStatusEnum.EXPIRED
            
            session.commit()
    
    @staticmethod
    def _auto_renew_subscription(session: Session, subscription: UserSubscription):
        """自动续费订阅"""
        # 这里需要实现自动续费逻辑
        # 可能需要调用支付接口或使用保存的支付方式
        
        # 示例：直接延长订阅（实际应该先处理支付）
        plan = subscription.plan
        subscription.end_date = subscription.end_date + timedelta(days=plan.duration_days)
        
        # 记录自动续费日志
        AuditLog.log_action(
            user_id=subscription.user_id,
            action="AUTO_RENEW_SUBSCRIPTION",
            resource_type="UserSubscription",
            resource_id=subscription.id,
            details={
                "new_end_date": subscription.end_date.isoformat(),
                "plan_id": plan.id
            }
        )
