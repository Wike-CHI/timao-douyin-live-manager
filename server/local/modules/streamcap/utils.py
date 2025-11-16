"""
StreamCap 模块工具函数
从 StreamCap/app/utils/utils.py 迁移的必要函数
"""

import functools
import traceback
from typing import Any, Callable

from .logger import logger


def trace_error_decorator(func: Callable) -> Callable:
    """
    异步函数错误跟踪装饰器
    捕获并记录函数执行过程中的错误
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            try:
                # 尝试获取错误行号
                error_line = traceback.extract_tb(e.__traceback__)[-1].lineno
                error_info = f"Type: {type(e).__name__}, {e} in function {func.__name__} at line: {error_line}"
            except Exception:
                # 如果获取行号失败，使用简化的错误信息
                error_info = f"Error in {func.__name__}: {type(e).__name__}: {e}"
            
            logger.error(error_info)
            return []
    
    return wrapper
