"""
DouyinLiveWebFetcher API封装 - 工具函数模块

本模块提供通用的辅助功能：
- 异步工具函数
- 数据验证和转换
- 时间处理工具
- 字符串处理工具
- 网络工具
- 性能监控工具
- 调试工具
"""

import logging
import asyncio
import time
import hashlib
import json
import re
import uuid
from typing import Dict, Any, Optional, List, Union, Callable, TypeVar, Generic, Tuple
from datetime import datetime, timedelta, timezone
from functools import wraps, partial
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, asdict
import inspect
import traceback
from pathlib import Path

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

from .exceptions import ValidationError, NetworkError


T = TypeVar('T')
F = TypeVar('F', bound=Callable)


# ================================
# 时间工具
# ================================

class TimeUtils:
    """时间处理工具"""
    
    @staticmethod
    def now() -> datetime:
        """获取当前时间（UTC）"""
        return datetime.now(timezone.utc)
    
    @staticmethod
    def now_local() -> datetime:
        """获取当前本地时间"""
        return datetime.now()
    
    @staticmethod
    def timestamp() -> float:
        """获取当前时间戳"""
        return time.time()
    
    @staticmethod
    def timestamp_ms() -> int:
        """获取当前时间戳（毫秒）"""
        return int(time.time() * 1000)
    
    @staticmethod
    def from_timestamp(timestamp: Union[int, float]) -> datetime:
        """从时间戳创建datetime对象"""
        if isinstance(timestamp, int) and timestamp > 1e10:
            # 毫秒时间戳
            timestamp = timestamp / 1000
        
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    
    @staticmethod
    def to_timestamp(dt: datetime) -> float:
        """将datetime转换为时间戳"""
        return dt.timestamp()
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """格式化持续时间"""
        if seconds < 1:
            return f"{seconds*1000:.1f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m{secs:.1f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}h{minutes}m{secs:.1f}s"
    
    @staticmethod
    def parse_iso_datetime(iso_string: str) -> datetime:
        """解析ISO格式的日期时间字符串"""
        try:
            return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        except ValueError as e:
            raise ValidationError(f"Invalid ISO datetime format: {iso_string}") from e
    
    @staticmethod
    def is_expired(created_at: datetime, ttl_seconds: int) -> bool:
        """检查是否过期"""
        if ttl_seconds <= 0:
            return False
        
        expiry_time = created_at + timedelta(seconds=ttl_seconds)
        return TimeUtils.now() > expiry_time


# ================================
# 字符串工具
# ================================

class StringUtils:
    """字符串处理工具"""
    
    @staticmethod
    def generate_id(prefix: str = "", length: int = 8) -> str:
        """生成唯一ID"""
        if prefix:
            return f"{prefix}_{uuid.uuid4().hex[:length]}"
        return uuid.uuid4().hex[:length]
    
    @staticmethod
    def generate_uuid() -> str:
        """生成UUID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名中的非法字符"""
        # 移除或替换非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(illegal_chars, '_', filename)
        
        # 移除前后空格和点
        sanitized = sanitized.strip(' .')
        
        # 限制长度
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
        
        return sanitized or "unnamed"
    
    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """截断文本"""
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def mask_sensitive(text: str, mask_char: str = "*", 
                      keep_start: int = 2, keep_end: int = 2) -> str:
        """遮蔽敏感信息"""
        if len(text) <= keep_start + keep_end:
            return mask_char * len(text)
        
        start = text[:keep_start]
        end = text[-keep_end:] if keep_end > 0 else ""
        middle = mask_char * (len(text) - keep_start - keep_end)
        
        return start + middle + end
    
    @staticmethod
    def extract_numbers(text: str) -> List[int]:
        """提取文本中的数字"""
        numbers = re.findall(r'\d+', text)
        return [int(num) for num in numbers]
    
    @staticmethod
    def camel_to_snake(name: str) -> str:
        """驼峰命名转下划线命名"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    @staticmethod
    def snake_to_camel(name: str) -> str:
        """下划线命名转驼峰命名"""
        components = name.split('_')
        return components[0] + ''.join(word.capitalize() for word in components[1:])


# ================================
# 数据验证工具
# ================================

class ValidationUtils:
    """数据验证工具"""
    
    @staticmethod
    def validate_room_id(room_id: str) -> bool:
        """验证房间ID格式"""
        if not room_id or not isinstance(room_id, str):
            return False
        
        # 房间ID应该是数字字符串
        return room_id.isdigit() and len(room_id) > 0
    
    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """验证用户ID格式"""
        if not user_id or not isinstance(user_id, str):
            return False
        
        # 用户ID应该是数字字符串
        return user_id.isdigit() and len(user_id) > 0
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """验证URL格式"""
        if not url or not isinstance(url, str):
            return False
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return url_pattern.match(url) is not None
    
    @staticmethod
    def validate_json(json_str: str) -> bool:
        """验证JSON格式"""
        try:
            json.loads(json_str)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    @staticmethod
    def validate_config_dict(config: Dict[str, Any], required_keys: List[str]) -> List[str]:
        """验证配置字典，返回缺失的键"""
        missing_keys = []
        
        for key in required_keys:
            if key not in config:
                missing_keys.append(key)
            elif config[key] is None:
                missing_keys.append(f"{key} (null value)")
        
        return missing_keys
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any], 
                     allowed_keys: Optional[List[str]] = None,
                     remove_none: bool = True) -> Dict[str, Any]:
        """清理字典数据"""
        result = {}
        
        for key, value in data.items():
            # 检查允许的键
            if allowed_keys and key not in allowed_keys:
                continue
            
            # 移除None值
            if remove_none and value is None:
                continue
            
            result[key] = value
        
        return result


# ================================
# 网络工具
# ================================

class NetworkUtils:
    """网络工具"""
    
    @staticmethod
    async def check_connectivity(url: str = "https://www.baidu.com", 
                               timeout: int = 5) -> bool:
        """检查网络连通性"""
        if not AIOHTTP_AVAILABLE:
            return False
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    return response.status == 200
        except Exception:
            return False
    
    @staticmethod
    async def get_public_ip() -> Optional[str]:
        """获取公网IP"""
        if not AIOHTTP_AVAILABLE:
            return None
        
        urls = [
            "https://api.ipify.org",
            "https://httpbin.org/ip",
            "https://api.ip.sb/ip"
        ]
        
        for url in urls:
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            text = await response.text()
                            
                            # 不同API返回格式不同
                            if url == "https://httpbin.org/ip":
                                data = json.loads(text)
                                return data.get("origin", "").split(",")[0].strip()
                            else:
                                return text.strip()
            except Exception:
                continue
        
        return None
    
    @staticmethod
    def parse_user_agent(user_agent: str) -> Dict[str, str]:
        """解析User-Agent字符串"""
        # 简单的User-Agent解析
        result = {
            'browser': 'Unknown',
            'version': 'Unknown',
            'os': 'Unknown'
        }
        
        # 检测浏览器
        if 'Chrome' in user_agent:
            result['browser'] = 'Chrome'
            match = re.search(r'Chrome/(\d+\.\d+)', user_agent)
            if match:
                result['version'] = match.group(1)
        elif 'Firefox' in user_agent:
            result['browser'] = 'Firefox'
            match = re.search(r'Firefox/(\d+\.\d+)', user_agent)
            if match:
                result['version'] = match.group(1)
        elif 'Safari' in user_agent and 'Chrome' not in user_agent:
            result['browser'] = 'Safari'
            match = re.search(r'Version/(\d+\.\d+)', user_agent)
            if match:
                result['version'] = match.group(1)
        
        # 检测操作系统
        if 'Windows' in user_agent:
            result['os'] = 'Windows'
        elif 'Mac OS X' in user_agent:
            result['os'] = 'macOS'
        elif 'Linux' in user_agent:
            result['os'] = 'Linux'
        elif 'Android' in user_agent:
            result['os'] = 'Android'
        elif 'iOS' in user_agent:
            result['os'] = 'iOS'
        
        return result


# ================================
# 性能监控工具
# ================================

@dataclass
class PerformanceMetrics:
    """性能指标"""
    duration: float
    memory_usage: Optional[int] = None
    cpu_usage: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.logger = logging.getLogger(f"{__name__}.Performance")
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        duration = self.end_time - self.start_time
        
        if exc_type is None:
            self.logger.info(f"{self.name} completed in {TimeUtils.format_duration(duration)}")
        else:
            self.logger.warning(f"{self.name} failed after {TimeUtils.format_duration(duration)}: {exc_val}")
    
    @property
    def duration(self) -> Optional[float]:
        """获取执行时间"""
        if self.start_time is None:
            return None
        
        end_time = self.end_time or time.perf_counter()
        return end_time - self.start_time


def performance_monitor(name: Optional[str] = None):
    """性能监控装饰器"""
    
    def decorator(func: F) -> F:
        func_name = name or f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with PerformanceMonitor(func_name):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with PerformanceMonitor(func_name):
                    return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator


# ================================
# 异步工具
# ================================

class AsyncUtils:
    """异步工具"""
    
    @staticmethod
    async def run_with_timeout(coro, timeout: float, 
                              default_value: Any = None) -> Any:
        """带超时的协程执行"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logging.getLogger(__name__).warning(f"Operation timed out after {timeout}s")
            return default_value
    
    @staticmethod
    async def gather_with_limit(coroutines: List, limit: int = 10) -> List[Any]:
        """限制并发数的gather"""
        semaphore = asyncio.Semaphore(limit)
        
        async def limited_coro(coro):
            async with semaphore:
                return await coro
        
        limited_coroutines = [limited_coro(coro) for coro in coroutines]
        return await asyncio.gather(*limited_coroutines, return_exceptions=True)
    
    @staticmethod
    async def retry_async(func: Callable, max_retries: int = 3, 
                         delay: float = 1.0, backoff: float = 2.0,
                         exceptions: Tuple = (Exception,)) -> Any:
        """异步重试机制"""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func()
                else:
                    return func()
            except exceptions as e:
                last_exception = e
                
                if attempt < max_retries:
                    wait_time = delay * (backoff ** attempt)
                    logging.getLogger(__name__).warning(
                        f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logging.getLogger(__name__).error(
                        f"All {max_retries + 1} attempts failed. Last error: {e}"
                    )
        
        raise last_exception
    
    @staticmethod
    @asynccontextmanager
    async def timeout_context(timeout: float):
        """超时上下文管理器"""
        try:
            async with asyncio.timeout(timeout):
                yield
        except asyncio.TimeoutError:
            logging.getLogger(__name__).warning(f"Operation timed out after {timeout}s")
            raise


# ================================
# 数据转换工具
# ================================

class DataUtils:
    """数据转换工具"""
    
    @staticmethod
    def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DataUtils.deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """扁平化字典"""
        items = []
        
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(DataUtils.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        
        return dict(items)
    
    @staticmethod
    def unflatten_dict(d: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
        """反扁平化字典"""
        result = {}
        
        for key, value in d.items():
            keys = key.split(sep)
            current = result
            
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            current[keys[-1]] = value
        
        return result
    
    @staticmethod
    def safe_get(data: Dict[str, Any], path: str, default: Any = None, sep: str = '.') -> Any:
        """安全获取嵌套字典值"""
        keys = path.split(sep)
        current = data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    @staticmethod
    def safe_set(data: Dict[str, Any], path: str, value: Any, sep: str = '.') -> None:
        """安全设置嵌套字典值"""
        keys = path.split(sep)
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    @staticmethod
    def convert_size(size_bytes: int) -> str:
        """转换字节大小为可读格式"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
    
    @staticmethod
    def calculate_hash(data: Union[str, bytes, Dict[str, Any]], 
                      algorithm: str = 'md5') -> str:
        """计算数据哈希值"""
        if isinstance(data, dict):
            # 对字典进行排序后序列化
            data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
            data_bytes = data_str.encode('utf-8')
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = data
        
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(data_bytes)
        return hash_obj.hexdigest()


# ================================
# 调试工具
# ================================

class DebugUtils:
    """调试工具"""
    
    @staticmethod
    def get_caller_info(depth: int = 1) -> Dict[str, Any]:
        """获取调用者信息"""
        frame = inspect.currentframe()
        
        try:
            # 向上查找指定深度的调用栈
            for _ in range(depth + 1):
                frame = frame.f_back
                if frame is None:
                    break
            
            if frame is None:
                return {}
            
            return {
                'filename': frame.f_code.co_filename,
                'function': frame.f_code.co_name,
                'lineno': frame.f_lineno,
                'locals': dict(frame.f_locals),
                'globals_keys': list(frame.f_globals.keys())
            }
        finally:
            del frame
    
    @staticmethod
    def format_exception(exc: Exception) -> Dict[str, Any]:
        """格式化异常信息"""
        return {
            'type': type(exc).__name__,
            'message': str(exc),
            'traceback': traceback.format_exception(type(exc), exc, exc.__traceback__),
            'traceback_str': ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        }
    
    @staticmethod
    def log_function_call(func: Callable, args: tuple, kwargs: dict, 
                         result: Any = None, exception: Exception = None) -> None:
        """记录函数调用"""
        logger = logging.getLogger(f"{__name__}.FunctionCall")
        
        # 构建调用信息
        call_info = {
            'function': f"{func.__module__}.{func.__name__}",
            'args_count': len(args),
            'kwargs_keys': list(kwargs.keys()),
            'timestamp': TimeUtils.now().isoformat()
        }
        
        if exception:
            call_info['exception'] = DebugUtils.format_exception(exception)
            logger.error(f"Function call failed: {json.dumps(call_info, indent=2)}")
        else:
            call_info['result_type'] = type(result).__name__
            logger.debug(f"Function call succeeded: {json.dumps(call_info, indent=2)}")


def debug_calls(include_args: bool = False, include_result: bool = False):
    """调试函数调用装饰器"""
    
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            exception = None
            result = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                exception = e
                raise
            finally:
                duration = time.perf_counter() - start_time
                
                # 记录调用信息
                call_info = {
                    'function': f"{func.__module__}.{func.__name__}",
                    'duration': duration,
                    'timestamp': TimeUtils.now().isoformat()
                }
                
                if include_args:
                    call_info['args'] = args
                    call_info['kwargs'] = kwargs
                
                if include_result and result is not None:
                    call_info['result'] = result
                
                if exception:
                    call_info['exception'] = str(exception)
                
                logger = logging.getLogger(f"{__name__}.DebugCalls")
                logger.debug(f"Call info: {json.dumps(call_info, default=str, indent=2)}")
        
        return wrapper
    
    return decorator


# ================================
# 文件工具
# ================================

class FileUtils:
    """文件处理工具"""
    
    @staticmethod
    def ensure_dir(path: Union[str, Path]) -> Path:
        """确保目录存在"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def safe_write_json(file_path: Union[str, Path], data: Any, 
                       backup: bool = True) -> bool:
        """安全写入JSON文件"""
        file_path = Path(file_path)
        
        try:
            # 创建备份
            if backup and file_path.exists():
                backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                backup_path.write_bytes(file_path.read_bytes())
            
            # 写入临时文件
            temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")
            
            with temp_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 原子性替换
            temp_path.replace(file_path)
            
            return True
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to write JSON file {file_path}: {e}")
            return False
    
    @staticmethod
    def safe_read_json(file_path: Union[str, Path], default: Any = None) -> Any:
        """安全读取JSON文件"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return default
        
        try:
            with file_path.open('r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to read JSON file {file_path}: {e}")
            return default
    
    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """获取文件大小"""
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return 0
    
    @staticmethod
    def get_file_hash(file_path: Union[str, Path], algorithm: str = 'md5') -> Optional[str]:
        """获取文件哈希值"""
        try:
            hash_obj = hashlib.new(algorithm)
            
            with Path(file_path).open('rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to calculate file hash: {e}")
            return None


# ================================
# 全局工具实例
# ================================

# 创建全局工具实例
time_utils = TimeUtils()
string_utils = StringUtils()
validation_utils = ValidationUtils()
network_utils = NetworkUtils()
async_utils = AsyncUtils()
data_utils = DataUtils()
debug_utils = DebugUtils()
file_utils = FileUtils()


# ================================
# 便捷函数
# ================================

def now() -> datetime:
    """获取当前时间"""
    return TimeUtils.now()


def timestamp() -> float:
    """获取当前时间戳"""
    return TimeUtils.timestamp()


def generate_id(prefix: str = "") -> str:
    """生成唯一ID"""
    return StringUtils.generate_id(prefix)


def format_duration(seconds: float) -> str:
    """格式化持续时间"""
    return TimeUtils.format_duration(seconds)


def safe_get(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """安全获取嵌套字典值"""
    return DataUtils.safe_get(data, path, default)


def calculate_hash(data: Union[str, bytes, Dict[str, Any]]) -> str:
    """计算数据哈希值"""
    return DataUtils.calculate_hash(data)


async def run_with_timeout(coro, timeout: float, default_value: Any = None) -> Any:
    """带超时的协程执行"""
    return await AsyncUtils.run_with_timeout(coro, timeout, default_value)