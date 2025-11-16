"""
服务日志记录工具
提供统一的日志记录接口，用于记录服务启动、停止、生成等关键事件
"""

import logging
import time
from typing import Optional, Dict, Any
from functools import wraps
from datetime import datetime


logger = logging.getLogger(__name__)


class ServiceLogger:
    """服务日志记录器"""
    
    @staticmethod
    def log_service_start(service_name: str, **kwargs) -> None:
        """记录服务启动
        
        Args:
            service_name: 服务名称
            **kwargs: 额外信息（如 live_id, session_id 等）
        """
        extra_info = ", ".join([f"{k}={v}" for k, v in kwargs.items() if v is not None])
        info_str = f"🚀 [服务启动] {service_name}"
        if extra_info:
            info_str += f" | {extra_info}"
        logger.info(info_str)
    
    @staticmethod
    def log_service_stop(service_name: str, **kwargs) -> None:
        """记录服务停止
        
        Args:
            service_name: 服务名称
            **kwargs: 额外信息（如 live_id, session_id, duration 等）
        """
        extra_info = ", ".join([f"{k}={v}" for k, v in kwargs.items() if v is not None])
        info_str = f"🛑 [服务停止] {service_name}"
        if extra_info:
            info_str += f" | {extra_info}"
        logger.info(info_str)
    
    @staticmethod
    def log_service_error(service_name: str, error: str, **kwargs) -> None:
        """记录服务错误
        
        Args:
            service_name: 服务名称
            error: 错误信息
            **kwargs: 额外信息
        """
        extra_info = ", ".join([f"{k}={v}" for k, v in kwargs.items() if v is not None])
        error_str = f"❌ [服务错误] {service_name} | 错误: {error}"
        if extra_info:
            error_str += f" | {extra_info}"
        logger.error(error_str)
    
    @staticmethod
    def log_generation_start(service_name: str, target: str, **kwargs) -> None:
        """记录生成服务开始
        
        Args:
            service_name: 服务名称（如 "复盘报告"、"话术生成"）
            target: 目标对象（如 session_id, report_id）
            **kwargs: 额外信息
        """
        extra_info = ", ".join([f"{k}={v}" for k, v in kwargs.items() if v is not None])
        info_str = f"📝 [生成开始] {service_name} | 目标: {target}"
        if extra_info:
            info_str += f" | {extra_info}"
        logger.info(info_str)
    
    @staticmethod
    def log_generation_complete(service_name: str, target: str, duration: Optional[float] = None, **kwargs) -> None:
        """记录生成服务完成
        
        Args:
            service_name: 服务名称
            target: 目标对象
            duration: 耗时（秒）
            **kwargs: 额外信息（如 cost, tokens 等）
        """
        extra_info = ", ".join([f"{k}={v}" for k, v in kwargs.items() if v is not None])
        info_str = f"✅ [生成完成] {service_name} | 目标: {target}"
        if duration is not None:
            info_str += f" | 耗时: {duration:.2f}秒"
        if extra_info:
            info_str += f" | {extra_info}"
        logger.info(info_str)
    
    @staticmethod
    def log_generation_error(service_name: str, target: str, error: str, **kwargs) -> None:
        """记录生成服务错误
        
        Args:
            service_name: 服务名称
            target: 目标对象
            error: 错误信息
            **kwargs: 额外信息
        """
        extra_info = ", ".join([f"{k}={v}" for k, v in kwargs.items() if v is not None])
        error_str = f"❌ [生成失败] {service_name} | 目标: {target} | 错误: {error}"
        if extra_info:
            error_str += f" | {extra_info}"
        logger.error(error_str)
    
    @staticmethod
    def log_user_action(action: str, user_id: Optional[int] = None, username: Optional[str] = None, **kwargs) -> None:
        """记录用户操作
        
        Args:
            action: 操作类型（如 "登录"、"注册"、"订阅"）
            user_id: 用户ID
            username: 用户名
            **kwargs: 额外信息
        """
        user_info = []
        if user_id:
            user_info.append(f"user_id={user_id}")
        if username:
            user_info.append(f"username={username}")
        user_str = ", ".join(user_info) if user_info else "未知用户"
        
        extra_info = ", ".join([f"{k}={v}" for k, v in kwargs.items() if v is not None])
        info_str = f"👤 [用户操作] {action} | {user_str}"
        if extra_info:
            info_str += f" | {extra_info}"
        logger.info(info_str)
    
    @staticmethod
    def log_subscription_event(event_type: str, user_id: Optional[int] = None, **kwargs) -> None:
        """记录订阅事件
        
        Args:
            event_type: 事件类型（如 "订阅"、"续费"、"取消"、"升级"）
            user_id: 用户ID
            **kwargs: 额外信息（如 plan, amount, duration 等）
        """
        extra_info = ", ".join([f"{k}={v}" for k, v in kwargs.items() if v is not None])
        info_str = f"💳 [订阅事件] {event_type}"
        if user_id:
            info_str += f" | user_id={user_id}"
        if extra_info:
            info_str += f" | {extra_info}"
        logger.info(info_str)


# 便捷函数
def log_service_start(service_name: str, **kwargs) -> None:
    """记录服务启动"""
    ServiceLogger.log_service_start(service_name, **kwargs)


def log_service_stop(service_name: str, **kwargs) -> None:
    """记录服务停止"""
    ServiceLogger.log_service_stop(service_name, **kwargs)


def log_service_error(service_name: str, error: str, **kwargs) -> None:
    """记录服务错误"""
    ServiceLogger.log_service_error(service_name, error, **kwargs)


def log_generation_start(service_name: str, target: str, **kwargs) -> None:
    """记录生成服务开始"""
    ServiceLogger.log_generation_start(service_name, target, **kwargs)


def log_generation_complete(service_name: str, target: str, duration: Optional[float] = None, **kwargs) -> None:
    """记录生成服务完成"""
    ServiceLogger.log_generation_complete(service_name, target, duration, **kwargs)


def log_generation_error(service_name: str, target: str, error: str, **kwargs) -> None:
    """记录生成服务错误"""
    ServiceLogger.log_generation_error(service_name, target, error, **kwargs)


def log_user_action(action: str, user_id: Optional[int] = None, username: Optional[str] = None, **kwargs) -> None:
    """记录用户操作"""
    ServiceLogger.log_user_action(action, user_id, username, **kwargs)


def log_subscription_event(event_type: str, user_id: Optional[int] = None, **kwargs) -> None:
    """记录订阅事件"""
    ServiceLogger.log_subscription_event(event_type, user_id, **kwargs)


def timed_generation(service_name: str):
    """装饰器：自动记录生成服务的开始和完成时间
    
    Usage:
        @timed_generation("复盘报告")
        def generate_review(self, session_id):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 尝试从参数中提取 target（通常是第一个参数或 session_id）
            target = None
            if args and len(args) > 1:
                target = str(args[1])  # 通常是第二个参数（第一个是 self）
            elif 'session_id' in kwargs:
                target = str(kwargs['session_id'])
            elif 'report_id' in kwargs:
                target = str(kwargs['report_id'])
            else:
                target = "未知"
            
            start_time = time.time()
            log_generation_start(service_name, target)
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # 尝试提取额外信息
                extra = {}
                if hasattr(result, 'generation_cost'):
                    extra['cost'] = f"${result.generation_cost:.6f}"
                if hasattr(result, 'generation_tokens'):
                    extra['tokens'] = result.generation_tokens
                
                log_generation_complete(service_name, target, duration, **extra)
                return result
            except Exception as e:
                duration = time.time() - start_time
                ServiceLogger.log_generation_error(service_name, target, str(e), duration=f"{duration:.2f}秒")
                raise
        return wrapper
    return decorator

