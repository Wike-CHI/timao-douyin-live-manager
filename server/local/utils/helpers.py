"""
提猫直播助手 - 辅助工具函数
包含各种通用的辅助函数和工具
"""

import os
import json
import time
import logging
import hashlib
import functools
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
import re


def format_time(timestamp: Union[float, datetime, str] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化时间"""
    if timestamp is None:
        timestamp = datetime.now()
    elif isinstance(timestamp, (int, float)):
        timestamp = datetime.fromtimestamp(timestamp)
    elif isinstance(timestamp, str):
        # 尝试解析ISO格式时间
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            return str(timestamp)
    
    return timestamp.strftime(format_str)


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """安全获取字典值"""
    try:
        keys = key.split('.')
        result = data
        for k in keys:
            if isinstance(result, dict):
                result = result.get(k)
            else:
                return default
        return result if result is not None else default
    except (KeyError, TypeError, AttributeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """安全转换为整数"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """安全转换为浮点数"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """安全转换为字符串"""
    try:
        if value is None:
            return default
        return str(value)
    except (ValueError, TypeError):
        return default


def clean_text(text: str) -> str:
    """清理文本内容"""
    if not text:
        return ""
    
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text.strip())
    
    # 移除特殊字符（保留中文、英文、数字、常用标点）
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s.,!?;:()（）。，！？；：]', '', text)
    
    return text


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断文本"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def generate_id(prefix: str = "", length: int = 8) -> str:
    """生成唯一ID"""
    timestamp = str(int(time.time() * 1000))
    hash_obj = hashlib.md5(timestamp.encode())
    hash_str = hash_obj.hexdigest()[:length]
    
    return f"{prefix}{hash_str}" if prefix else hash_str


def calculate_hash(data: Union[str, Dict, List]) -> str:
    """计算数据哈希值"""
    if isinstance(data, (dict, list)):
        data = json.dumps(data, sort_keys=True, ensure_ascii=False)
    
    return hashlib.md5(str(data).encode('utf-8')).hexdigest()


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logging.warning(f"函数 {func.__name__} 第{attempt + 1}次尝试失败: {e}")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logging.error(f"函数 {func.__name__} 重试{max_retries}次后仍然失败")
            
            raise last_exception
        
        return wrapper
    return decorator


def rate_limit(calls_per_second: float = 1.0):
    """限流装饰器"""
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator


def cache_result(ttl: int = 300):
    """结果缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key = calculate_hash(str(args) + str(sorted(kwargs.items())))
            current_time = time.time()
            
            # 检查缓存
            if key in cache:
                result, timestamp = cache[key]
                if current_time - timestamp < ttl:
                    return result
                else:
                    del cache[key]
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)
            
            # 清理过期缓存
            expired_keys = [
                k for k, (_, ts) in cache.items()
                if current_time - ts >= ttl
            ]
            for k in expired_keys:
                del cache[k]
            
            return result
        
        return wrapper
    return decorator


def ensure_dir(path: str) -> str:
    """确保目录存在"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path


def read_json_file(file_path: str, default: Any = None) -> Any:
    """读取JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.warning(f"读取JSON文件失败 {file_path}: {e}")
        return default


def write_json_file(file_path: str, data: Any, indent: int = 2) -> bool:
    """写入JSON文件"""
    try:
        ensure_dir(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        logging.error(f"写入JSON文件失败 {file_path}: {e}")
        return False


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """合并多个字典"""
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result


def filter_dict(data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """过滤字典键"""
    return {k: v for k, v in data.items() if k in keys}


def exclude_dict(data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """排除字典键"""
    return {k: v for k, v in data.items() if k not in keys}


def flatten_dict(data: Dict[str, Any], separator: str = '.') -> Dict[str, Any]:
    """扁平化字典"""
    def _flatten(obj, parent_key=''):
        items = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_key = f"{parent_key}{separator}{k}" if parent_key else k
                items.extend(_flatten(v, new_key).items())
        else:
            return {parent_key: obj}
        return dict(items)
    
    return _flatten(data)


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """分割列表"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def deduplicate_list(lst: List[Any], key: Callable = None) -> List[Any]:
    """去重列表"""
    if key is None:
        return list(dict.fromkeys(lst))
    
    seen = set()
    result = []
    for item in lst:
        k = key(item)
        if k not in seen:
            seen.add(k)
            result.append(item)
    return result


def sort_dict_by_value(data: Dict[str, Any], reverse: bool = True) -> Dict[str, Any]:
    """按值排序字典"""
    return dict(sorted(data.items(), key=lambda x: x[1], reverse=reverse))


def get_file_size(file_path: str) -> int:
    """获取文件大小（字节）"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def is_valid_url(url: str) -> bool:
    """验证URL格式"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def extract_numbers(text: str) -> List[float]:
    """从文本中提取数字"""
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    return [float(match) for match in matches if match]


def extract_chinese(text: str) -> str:
    """提取中文字符"""
    pattern = r'[\u4e00-\u9fa5]+'
    matches = re.findall(pattern, text)
    return ''.join(matches)


def extract_english(text: str) -> str:
    """提取英文字符"""
    pattern = r'[a-zA-Z]+'
    matches = re.findall(pattern, text)
    return ' '.join(matches)


def calculate_similarity(text1: str, text2: str) -> float:
    """计算文本相似度（简单版本）"""
    if not text1 or not text2:
        return 0.0
    
    # 转换为字符集合
    set1 = set(text1.lower())
    set2 = set(text2.lower())
    
    # 计算交集和并集
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0


def get_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    import platform
    import psutil
    
    try:
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
        }
    except ImportError:
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version()
        }


class Timer:
    """计时器工具类"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """开始计时"""
        self.start_time = time.time()
        return self
    
    def stop(self):
        """停止计时"""
        self.end_time = time.time()
        return self
    
    def elapsed(self) -> float:
        """获取耗时（秒）"""
        if self.start_time is None:
            return 0.0
        
        end = self.end_time or time.time()
        return end - self.start_time
    
    def __enter__(self):
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def is_allowed(self) -> bool:
        """检查是否允许调用"""
        now = time.time()
        
        # 清理过期记录
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        # 检查是否超过限制
        if len(self.calls) >= self.max_calls:
            return False
        
        # 记录本次调用
        self.calls.append(now)
        return True
    
    def wait_time(self) -> float:
        """获取需要等待的时间"""
        if len(self.calls) < self.max_calls:
            return 0.0
        
        oldest_call = min(self.calls)
        return self.time_window - (time.time() - oldest_call)


def setup_logging(level: str = "INFO", 
                 log_file: str = None, 
                 format_str: str = None) -> logging.Logger:
    """设置日志配置"""
    if format_str is None:
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_str,
        handlers=[]
    )
    
    logger = logging.getLogger()
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(format_str))
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        ensure_dir(os.path.dirname(log_file))
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(format_str))
        logger.addHandler(file_handler)
    
    return logger