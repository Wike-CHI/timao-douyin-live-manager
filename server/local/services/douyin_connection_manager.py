"""
抖音连接管理器
提供智能重试、降级和状态管理功能
"""

import time
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectionStatus(str, Enum):
    """连接状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RETRYING = "retrying"
    FAILED = "failed"
    DEGRADED = "degraded"  # 降级模式：连接不稳定但仍在运行


@dataclass
class ConnectionState:
    """连接状态"""
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    attempt: int = 0
    max_retries: int = 10
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    total_failures: int = 0
    success_count: int = 0
    last_success_time: Optional[float] = None
    start_time: float = 0
    
    def is_healthy(self) -> bool:
        """判断连接是否健康"""
        if self.status == ConnectionStatus.CONNECTED:
            return True
        if self.status == ConnectionStatus.DEGRADED:
            # 降级模式：成功率 > 30% 视为可用
            total = self.success_count + self.total_failures
            return total > 0 and (self.success_count / total) > 0.3
        return False
    
    def record_success(self):
        """记录成功"""
        self.success_count += 1
        self.consecutive_failures = 0
        self.last_success_time = time.time()
        
        # 如果连续成功，可以从降级模式恢复
        if self.status == ConnectionStatus.DEGRADED and self.success_count >= 5:
            self.status = ConnectionStatus.CONNECTED
            logger.info("📶 抖音连接已恢复正常")
    
    def record_failure(self, error: str):
        """记录失败"""
        self.consecutive_failures += 1
        self.total_failures += 1
        self.last_error = error
        
        # 如果连续失败超过阈值，进入降级模式
        if self.consecutive_failures >= 3 and self.status == ConnectionStatus.CONNECTED:
            self.status = ConnectionStatus.DEGRADED
            logger.warning(f"⚠️ 抖音连接不稳定，进入降级模式 (连续失败{self.consecutive_failures}次)")


class DouyinConnectionManager:
    """抖音连接管理器"""
    
    def __init__(self, max_retries: int = 10, base_delay: float = 2.0):
        self.state = ConnectionState(max_retries=max_retries)
        self.base_delay = base_delay
        self._status_callback: Optional[Callable] = None
    
    def set_status_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """设置状态回调"""
        self._status_callback = callback
    
    def _emit_status(self, event_type: str, payload: Dict[str, Any]):
        """发送状态事件"""
        if self._status_callback:
            self._status_callback({
                "type": event_type,
                "payload": payload,
                "timestamp": time.time(),
            })
    
    def should_retry(self) -> bool:
        """判断是否应该重试"""
        if self.state.attempt >= self.state.max_retries:
            return False
        
        # 如果处于降级模式，允许更多重试
        if self.state.status == ConnectionStatus.DEGRADED:
            return self.state.attempt < self.state.max_retries * 2
        
        return True
    
    def calculate_delay(self) -> float:
        """计算重试延迟（指数退避 + 抖动）"""
        import random
        
        # 基础延迟：指数退避
        base = self.base_delay * (1.5 ** (self.state.attempt - 1))
        
        # 添加随机抖动（±20%）避免雷同重试
        jitter = base * 0.2 * (random.random() * 2 - 1)
        
        # 限制最大延迟
        delay = min(base + jitter, 30.0)
        
        # 降级模式下延迟时间更短
        if self.state.status == ConnectionStatus.DEGRADED:
            delay *= 0.5
        
        return delay
    
    def start_attempt(self) -> int:
        """开始新的尝试"""
        self.state.attempt += 1
        self.state.status = ConnectionStatus.CONNECTING if self.state.attempt == 1 else ConnectionStatus.RETRYING
        
        logger.info(f"🔄 开始第 {self.state.attempt}/{self.state.max_retries} 次连接尝试")
        
        self._emit_status("status", {
            "stage": "connecting" if self.state.attempt == 1 else "retrying",
            "attempt": self.state.attempt,
            "max_retries": self.state.max_retries,
            "status": self.state.status,
        })
        
        return self.state.attempt
    
    def record_success(self, message: str = "连接成功"):
        """记录成功"""
        self.state.record_success()
        self.state.status = ConnectionStatus.CONNECTED
        self.state.attempt = 0  # 重置尝试次数
        
        success_rate = self.get_success_rate()
        total = self.state.success_count + self.state.total_failures
        if total > 0:
            logger.info(
                f"✅ {message} (成功{self.state.success_count}次/失败{self.state.total_failures}次, "
                f"成功率: {success_rate:.1%})"
            )
        else:
            logger.info(f"✅ {message}")
        
        self._emit_status("status", {
            "stage": "connected",
            "message": message,
            "success_count": self.state.success_count,
            "total_failures": self.state.total_failures,
            "success_rate": success_rate,
        })
    
    def record_failure(self, error: Exception | str, is_retryable: bool = True):
        """记录失败"""
        error_msg = str(error) if error else "未知错误"
        self.state.record_failure(error_msg)
        
        # 判断错误类型并生成友好的错误说明
        error_lower = error_msg.lower()
        is_network_error = any(keyword in error_lower for keyword in [
            "timeout", "connection", "网络", "noneType", "not iterable",
            "bogus", "signature", "403", "400", "请求失败"
        ])
        
        # 生成友好的错误说明
        error_description = self._get_error_description(error_msg)
        
        if not self.should_retry():
            self.state.status = ConnectionStatus.FAILED
            success_rate = self.get_success_rate()
            logger.error(
                f"❌ 连接失败（已达最大重试次数 {self.state.attempt}/{self.state.max_retries}）: {error_msg} "
                f"(成功率: {success_rate:.1%}, 成功{self.state.success_count}次/失败{self.state.total_failures}次)"
            )
            
            self._emit_status("error", {
                "message": f"连接失败: {error_description}",
                "attempt": self.state.attempt,
                "max_retries": self.state.max_retries,
                "can_retry": False,
                "success_rate": success_rate,
                "success_count": self.state.success_count,
                "total_failures": self.state.total_failures,
                "error_type": self._get_error_type(error_msg),
            })
        else:
            delay = self.calculate_delay()
            success_rate = self.get_success_rate()
            
            # 降级模式下使用警告而非错误
            if self.state.status == ConnectionStatus.DEGRADED:
                logger.warning(
                    f"⚠️ 连接不稳定 (尝试 {self.state.attempt}/{self.state.max_retries}, "
                    f"成功率: {success_rate:.1%}, 成功{self.state.success_count}次/失败{self.state.total_failures}次): {error_description}"
                )
            else:
                logger.warning(
                    f"⚠️ 连接失败 (尝试 {self.state.attempt}/{self.state.max_retries}, "
                    f"{delay:.1f}秒后重试, 成功率: {success_rate:.1%}): {error_description}"
                )
            
            self._emit_status("status", {
                "stage": "retrying",
                "attempt": self.state.attempt,
                "max_retries": self.state.max_retries,
                "error": error_description,
                "error_raw": error_msg,  # 保留原始错误信息用于调试
                "next_retry_in": delay,
                "is_network_error": is_network_error,
                "status": self.state.status,
                "success_rate": success_rate,
                "success_count": self.state.success_count,
                "total_failures": self.state.total_failures,
                "error_type": self._get_error_type(error_msg),
            })
        
        return is_retryable and self.should_retry()
    
    def _get_error_description(self, error_msg: str) -> str:
        """生成友好的错误说明"""
        error_lower = error_msg.lower()
        
        # NoneType 相关错误
        if "nonetype" in error_lower or "not iterable" in error_lower:
            return "抖音API响应异常（这是正常现象，系统会自动重试）"
        
        # a_bogus 签名错误
        if "bogus" in error_lower or "signature" in error_lower:
            return "签名验证失败（抖音API限制，系统会自动重试）"
        
        # HTTP 错误
        if "403" in error_msg:
            return "请求被拒绝（可能是抖音API限制，系统会自动重试）"
        if "400" in error_msg:
            return "请求参数错误（系统会自动重试）"
        
        # 网络错误
        if "timeout" in error_lower or "connection" in error_lower:
            return "网络连接超时（系统会自动重试）"
        
        # 默认返回原始错误，但添加说明
        return f"{error_msg}（系统会自动重试）"
    
    def _get_error_type(self, error_msg: str) -> str:
        """获取错误类型"""
        error_lower = error_msg.lower()
        if "nonetype" in error_lower or "not iterable" in error_lower:
            return "api_response_error"
        elif "bogus" in error_lower or "signature" in error_lower:
            return "signature_error"
        elif "403" in error_msg:
            return "forbidden"
        elif "400" in error_msg:
            return "bad_request"
        elif "timeout" in error_lower or "connection" in error_lower:
            return "network_error"
        else:
            return "unknown"
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        total = self.state.success_count + self.state.total_failures
        return self.state.success_count / total if total > 0 else 0.0
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "status": self.state.status,
            "attempt": self.state.attempt,
            "max_retries": self.state.max_retries,
            "last_error": self.state.last_error,
            "consecutive_failures": self.state.consecutive_failures,
            "total_failures": self.state.total_failures,
            "success_count": self.state.success_count,
            "success_rate": self.get_success_rate(),
            "is_healthy": self.state.is_healthy(),
            "uptime": time.time() - self.state.start_time if self.state.start_time > 0 else 0,
        }
    
    def reset(self):
        """重置状态"""
        self.state = ConnectionState(max_retries=self.state.max_retries)
        logger.info("🔄 连接管理器已重置")


# 全局连接管理器实例
_connection_manager: Optional[DouyinConnectionManager] = None


def get_connection_manager() -> DouyinConnectionManager:
    """获取全局连接管理器"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = DouyinConnectionManager()
    return _connection_manager


def reset_connection_manager():
    """重置全局连接管理器"""
    global _connection_manager
    _connection_manager = None

