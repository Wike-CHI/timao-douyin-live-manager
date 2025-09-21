"""
DouyinLiveWebFetcher API封装 - 错误处理系统

本模块定义了API封装的错误处理机制，包括：
- 自定义异常类
- 错误码映射
- 错误处理装饰器
- 错误日志记录

提供统一的错误处理和响应格式。
"""

import logging
import traceback
import functools
import time
from typing import Dict, Any, Optional, Callable, Union, Tuple, Type
from datetime import datetime
import uuid

from .models import ErrorCode, ErrorInfo, APIResponse


# ================================
# 自定义异常类
# ================================

class DouyinAPIException(Exception):
    """抖音API基础异常类"""
    
    def __init__(
        self, 
        message: str, 
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.now()
        self.trace_id = str(uuid.uuid4())
    
    def to_error_info(self) -> ErrorInfo:
        """转换为错误信息对象"""
        return ErrorInfo(
            code=self.code,
            message=self.message,
            details=self.details,
            timestamp=self.timestamp,
            trace_id=self.trace_id
        )
    
    def to_api_response(self) -> APIResponse:
        """转换为API响应对象"""
        return APIResponse(
            success=False,
            code=self.code,
            message=self.message,
            data=self.details,
            timestamp=self.timestamp
        )


class ConfigurationError(DouyinAPIException):
    """配置错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCode.CONFIG_ERROR,
            details=details
        )


class ConnectionError(DouyinAPIException):
    """连接错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCode.CONNECTION_FAILED,
            details=details
        )


class WebSocketError(DouyinAPIException):
    """WebSocket错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCode.WEBSOCKET_ERROR,
            details=details
        )


class MessageParseError(DouyinAPIException):
    """消息解析错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCode.MESSAGE_PARSE_ERROR,
            details=details
        )


class ValidationError(DouyinAPIException):
    """数据验证错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            details=details
        )


class NetworkError(DouyinAPIException):
    """网络错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCode.NETWORK_ERROR,
            details=details
        )


class CacheError(DouyinAPIException):
    """缓存错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCode.CACHE_ERROR,
            details=details
        )


class StateError(DouyinAPIException):
    """状态错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCode.STATE_ERROR,
            details=details
        )


class StateManagerError(DouyinAPIException):
    """状态管理器错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCode.STATE_ERROR,
            details=details
        )


# ================================
# 错误处理装饰器和工具函数
# ================================

def handle_errors(func: Callable) -> Callable:
    """
    错误处理装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DouyinAPIException:
            # 重新抛出自定义异常
            raise
        except Exception as e:
            # 将其他异常包装为自定义异常
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise DouyinAPIException(
                message=f"Unexpected error in {func.__name__}: {str(e)}",
                code=ErrorCode.INTERNAL_ERROR,
                cause=e
            )
    return wrapper


async def handle_errors_async(func: Callable) -> Callable:
    """
    异步错误处理装饰器
    
    Args:
        func: 被装饰的异步函数
        
    Returns:
        装饰后的异步函数
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DouyinAPIException:
            # 重新抛出自定义异常
            raise
        except Exception as e:
            # 将其他异常包装为自定义异常
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise DouyinAPIException(
                message=f"Unexpected error in {func.__name__}: {str(e)}",
                code=ErrorCode.INTERNAL_ERROR,
                cause=e
            )
    return wrapper


def create_error_response(
    error: Union[DouyinAPIException, Exception, str],
    code: ErrorCode = ErrorCode.INTERNAL_ERROR
) -> APIResponse:
    """
    创建错误响应
    
    Args:
        error: 错误对象、异常或错误消息
        code: 错误码
        
    Returns:
        APIResponse: 错误响应对象
    """
    if isinstance(error, DouyinAPIException):
        return error.to_api_response()
    elif isinstance(error, Exception):
        return APIResponse(
            success=False,
            code=code,
            message=str(error),
            timestamp=datetime.now()
        )
    else:
        return APIResponse(
            success=False,
            code=code,
            message=str(error),
            timestamp=datetime.now()
        )


def log_error(
    error: Union[DouyinAPIException, Exception],
    context: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    记录错误日志
    
    Args:
        error: 错误对象
        context: 上下文信息
        logger: 日志记录器
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    context_str = f" Context: {context}" if context else ""
    
    if isinstance(error, DouyinAPIException):
        logger.error(
            f"DouyinAPI Error [{error.code.name}]: {error.message}"
            f" TraceID: {error.trace_id}{context_str}"
        )
        if error.cause:
            logger.error(f"Caused by: {str(error.cause)}")
    else:
        logger.error(f"Unexpected Error: {str(error)}{context_str}")
        logger.error(f"Traceback: {traceback.format_exc()}")


# ================================
# 重试机制
# ================================

class RetryOnError:
    """
    错误重试装饰器类
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """
        初始化重试装饰器
        
        Args:
            max_attempts: 最大重试次数
            delay: 初始延迟时间（秒）
            backoff_factor: 退避因子
            exceptions: 需要重试的异常类型
        """
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions
    
    def __call__(self, func: Callable) -> Callable:
        """
        装饰器调用
        
        Args:
            func: 被装饰的函数
            
        Returns:
            装饰后的函数
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = self.delay
            
            for attempt in range(self.max_attempts):
                try:
                    return func(*args, **kwargs)
                except self.exceptions as e:
                    last_exception = e
                    if attempt < self.max_attempts - 1:
                        logger = logging.getLogger(__name__)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay} seconds..."
                        )
                        time.sleep(current_delay)
                        current_delay *= self.backoff_factor
                    else:
                        logger = logging.getLogger(__name__)
                        logger.error(
                            f"All {self.max_attempts} attempts failed for {func.__name__}: {str(e)}"
                        )
            
            # 如果所有重试都失败，抛出最后一个异常
            raise last_exception
        
        return wrapper
    
    def retry_on_error(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        手动重试方法
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
        """
        decorated_func = self.__call__(func)
        return decorated_func(*args, **kwargs)


# ================================
# 错误监控和统计
# ================================

class InvalidRoomIdError(DouyinAPIException):
    """无效房间ID错误"""
    
    def __init__(self, room_id: str):
        super().__init__(
            message=f"Invalid room ID: {room_id}",
            code=ErrorCode.INVALID_ROOM_ID,
            details={"room_id": room_id}
        )


class TimeoutError(DouyinAPIException):
    """超时错误"""
    
    def __init__(self, message: str, timeout: Optional[int] = None):
        details = {"timeout": timeout} if timeout is not None else {}
        super().__init__(
            message=message,
            code=ErrorCode.TIMEOUT_ERROR,
            details=details
        )


class PermissionDeniedError(DouyinAPIException):
    """权限拒绝错误"""
    
    def __init__(self, message: str, resource: Optional[str] = None):
        details = {"resource": resource} if resource is not None else {}
        super().__init__(
            message=message,
            code=ErrorCode.PERMISSION_DENIED,
            details=details
        )


class RateLimitExceededError(DouyinAPIException):
    """频率限制错误"""
    
    def __init__(self, message: str, limit: Optional[int] = None, window: Optional[int] = None):
        details = {}
        if limit is not None:
            details["limit"] = limit
        if window is not None:
            details["window"] = window
        
        super().__init__(
            message=message,
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            details=details
        )


# ================================
# 错误处理装饰器
# ================================

def handle_exceptions(
    logger: Optional[logging.Logger] = None,
    return_response: bool = True,
    reraise: bool = False
):
    """
    异常处理装饰器
    
    Args:
        logger: 日志记录器
        return_response: 是否返回APIResponse对象
        reraise: 是否重新抛出异常
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except DouyinAPIException as e:
                # 记录已知异常
                if logger:
                    logger.error(f"DouyinAPI Exception in {func.__name__}: {e.message}", 
                               extra={"trace_id": e.trace_id, "details": e.details})
                
                if reraise:
                    raise
                
                if return_response:
                    return e.to_api_response()
                else:
                    return None
                    
            except Exception as e:
                # 记录未知异常
                trace_id = str(uuid.uuid4())
                error_msg = f"Unexpected error in {func.__name__}: {str(e)}"
                
                if logger:
                    logger.error(error_msg, extra={
                        "trace_id": trace_id,
                        "traceback": traceback.format_exc()
                    })
                
                if reraise:
                    raise DouyinAPIException(
                        message=error_msg,
                        code=ErrorCode.INTERNAL_ERROR,
                        cause=e
                    )
                
                if return_response:
                    return APIResponse(
                        success=False,
                        code=ErrorCode.INTERNAL_ERROR,
                        message=error_msg,
                        timestamp=datetime.now()
                    )
                else:
                    return None
        
        return wrapper
    return decorator


def async_handle_exceptions(
    logger: Optional[logging.Logger] = None,
    return_response: bool = True,
    reraise: bool = False
):
    """
    异步异常处理装饰器
    
    Args:
        logger: 日志记录器
        return_response: 是否返回APIResponse对象
        reraise: 是否重新抛出异常
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except DouyinAPIException as e:
                # 记录已知异常
                if logger:
                    logger.error(f"DouyinAPI Exception in {func.__name__}: {e.message}", 
                               extra={"trace_id": e.trace_id, "details": e.details})
                
                if reraise:
                    raise
                
                if return_response:
                    return e.to_api_response()
                else:
                    return None
                    
            except Exception as e:
                # 记录未知异常
                trace_id = str(uuid.uuid4())
                error_msg = f"Unexpected error in {func.__name__}: {str(e)}"
                
                if logger:
                    logger.error(error_msg, extra={
                        "trace_id": trace_id,
                        "traceback": traceback.format_exc()
                    })
                
                if reraise:
                    raise DouyinAPIException(
                        message=error_msg,
                        code=ErrorCode.INTERNAL_ERROR,
                        cause=e
                    )
                
                if return_response:
                    return APIResponse(
                        success=False,
                        code=ErrorCode.INTERNAL_ERROR,
                        message=error_msg,
                        timestamp=datetime.now()
                    )
                else:
                    return None
        
        return wrapper
    return decorator


# ================================
# 错误处理工具函数
# ================================

def create_error_response(
    code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> APIResponse:
    """
    创建错误响应
    
    Args:
        code: 错误码
        message: 错误消息
        details: 错误详情
        
    Returns:
        APIResponse: 错误响应对象
    """
    return APIResponse(
        success=False,
        code=code,
        message=message,
        data=details,
        timestamp=datetime.now()
    )


def log_error(
    logger: logging.Logger,
    error: Union[Exception, DouyinAPIException],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    记录错误日志
    
    Args:
        logger: 日志记录器
        error: 异常对象
        context: 上下文信息
        
    Returns:
        str: 跟踪ID
    """
    trace_id = str(uuid.uuid4())
    
    if isinstance(error, DouyinAPIException):
        # 记录已知异常
        logger.error(
            f"DouyinAPI Error: {error.message}",
            extra={
                "trace_id": error.trace_id,
                "error_code": error.code.value,
                "details": error.details,
                "context": context or {}
            }
        )
        return error.trace_id
    else:
        # 记录未知异常
        logger.error(
            f"Unexpected Error: {str(error)}",
            extra={
                "trace_id": trace_id,
                "error_type": type(error).__name__,
                "traceback": traceback.format_exc(),
                "context": context or {}
            }
        )
        return trace_id


def validate_room_id(room_id: str) -> None:
    """
    验证房间ID
    
    Args:
        room_id: 房间ID
        
    Raises:
        InvalidRoomIdError: 房间ID无效时抛出
    """
    if not room_id:
        raise InvalidRoomIdError("Room ID cannot be empty")
    
    if not isinstance(room_id, str):
        raise InvalidRoomIdError(f"Room ID must be string, got {type(room_id)}")
    
    # 检查房间ID格式（根据抖音实际规则调整）
    if not room_id.isdigit():
        raise InvalidRoomIdError(f"Room ID must be numeric, got {room_id}")
    
    if len(room_id) < 1 or len(room_id) > 20:
        raise InvalidRoomIdError(f"Room ID length must be between 1 and 20, got {len(room_id)}")


def validate_config_value(
    value: Any,
    expected_type: type,
    field_name: str,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None
) -> None:
    """
    验证配置值
    
    Args:
        value: 要验证的值
        expected_type: 期望的类型
        field_name: 字段名称
        min_value: 最小值（可选）
        max_value: 最大值（可选）
        
    Raises:
        ConfigurationError: 配置值无效时抛出
    """
    if not isinstance(value, expected_type):
        raise ConfigurationError(
            f"Invalid {field_name}: expected {expected_type.__name__}, got {type(value).__name__}",
            details={"field": field_name, "value": value, "expected_type": expected_type.__name__}
        )
    
    if min_value is not None and isinstance(value, (int, float)) and value < min_value:
        raise ConfigurationError(
            f"Invalid {field_name}: value {value} is less than minimum {min_value}",
            details={"field": field_name, "value": value, "min_value": min_value}
        )
    
    if max_value is not None and isinstance(value, (int, float)) and value > max_value:
        raise ConfigurationError(
            f"Invalid {field_name}: value {value} is greater than maximum {max_value}",
            details={"field": field_name, "value": value, "max_value": max_value}
        )


# ================================
# 错误恢复机制
# ================================

class ErrorRecovery:
    """错误恢复机制"""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.0):
        """
        初始化错误恢复机制
        
        Args:
            max_retries: 最大重试次数
            backoff_factor: 退避因子
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.logger = logging.getLogger(__name__)
    
    def retry_on_error(
        self,
        func: Callable,
        *args,
        retry_on: tuple = (ConnectionError, TimeoutError, WebSocketError),
        **kwargs
    ):
        """
        在特定错误时重试执行函数
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            retry_on: 需要重试的异常类型
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            最后一次执行的异常
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except retry_on as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    wait_time = self.backoff_factor * (2 ** attempt)
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}"
                    )
                    import time
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"All {self.max_retries + 1} attempts failed")
                    break
            except Exception as e:
                # 对于不在重试列表中的异常，直接抛出
                self.logger.error(f"Non-retryable error: {str(e)}")
                raise
        
        # 如果所有重试都失败，抛出最后一个异常
        if last_exception:
            raise last_exception


# ================================
# 错误监控和统计
# ================================

class ErrorMonitor:
    """错误监控器"""
    
    def __init__(self):
        """初始化错误监控器"""
        self.error_counts: Dict[ErrorCode, int] = {}
        self.error_history: list = []
        self.logger = logging.getLogger(__name__)
    
    def record_error(self, error: Union[DouyinAPIException, ErrorCode], context: Optional[Dict[str, Any]] = None):
        """
        记录错误
        
        Args:
            error: 错误对象或错误码
            context: 上下文信息
        """
        if isinstance(error, DouyinAPIException):
            error_code = error.code
        else:
            error_code = error
        
        # 更新错误计数
        self.error_counts[error_code] = self.error_counts.get(error_code, 0) + 1
        
        # 记录错误历史
        error_record = {
            "timestamp": datetime.now(),
            "error_code": error_code,
            "context": context or {}
        }
        
        if isinstance(error, DouyinAPIException):
            error_record.update({
                "message": error.message,
                "details": error.details,
                "trace_id": error.trace_id
            })
        
        self.error_history.append(error_record)
        
        # 保持历史记录在合理范围内
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-500:]
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        total_errors = sum(self.error_counts.values())
        
        return {
            "total_errors": total_errors,
            "error_counts": {code.name: count for code, count in self.error_counts.items()},
            "recent_errors": self.error_history[-10:] if self.error_history else []
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self.error_counts.clear()
        self.error_history.clear()
        self.logger.info("Error statistics reset")


# ================================
# 全局错误监控器实例
# ================================

# 创建全局错误监控器实例
_error_monitor: Optional[ErrorMonitor] = None


def get_error_monitor() -> ErrorMonitor:
    """获取全局错误监控器实例"""
    global _error_monitor
    
    if _error_monitor is None:
        _error_monitor = ErrorMonitor()
    
    return _error_monitor