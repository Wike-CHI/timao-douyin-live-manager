"""
AI 调用追踪装饰器
自动记录 AI API 调用的 Token 使用量和费用
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Optional

from .ai_usage_monitor import record_ai_usage

logger = logging.getLogger(__name__)


def track_ai_usage(
    function_name: str,
    model_name: Optional[str] = None,
    extract_tokens: Optional[Callable] = None
):
    """
    AI 使用追踪装饰器
    
    Args:
        function_name: 功能名称（如 "实时分析"、"话术生成"）
        model_name: 模型名称，如果为 None 则从返回值中提取
        extract_tokens: Token 提取函数，接收 AI 响应对象，返回 (input_tokens, output_tokens)
    
    用法示例:
        @track_ai_usage("实时分析", "qwen-plus")
        def generate_analysis(context):
            response = ai_client.chat.completions.create(...)
            return response
        
        # 或自定义 Token 提取
        def extract_qwen_tokens(response):
            return (response.usage.prompt_tokens, response.usage.completion_tokens)
        
        @track_ai_usage("话术生成", extract_tokens=extract_qwen_tokens)
        def generate_scripts(context):
            response = ai_client.chat.completions.create(...)
            return response
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = True
            error_msg = None
            result = None
            input_tokens = 0
            output_tokens = 0
            model = model_name
            
            try:
                result = func(*args, **kwargs)
                
                # 尝试从结果中提取 Token 信息
                if extract_tokens:
                    input_tokens, output_tokens = extract_tokens(result)
                elif hasattr(result, 'usage'):
                    # 标准 OpenAI 格式
                    input_tokens = getattr(result.usage, 'prompt_tokens', 0)
                    output_tokens = getattr(result.usage, 'completion_tokens', 0)
                
                # 尝试从结果中提取模型名称
                if not model and hasattr(result, 'model'):
                    model = result.model
                
                return result
                
            except Exception as exc:
                success = False
                error_msg = str(exc)
                logger.error(f"{function_name} 调用失败: {exc}")
                raise
                
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                # 记录使用情况
                try:
                    # 从 kwargs 中提取上下文信息
                    user_id = kwargs.get('user_id')
                    anchor_id = kwargs.get('anchor_id')
                    session_id = kwargs.get('session_id')
                    
                    # 如果还没提取到，尝试从 args[0]（通常是 context）中获取
                    if not anchor_id and len(args) > 0 and isinstance(args[0], dict):
                        context = args[0]
                        anchor_id = context.get('anchor_id')
                        user_id = context.get('user_id')
                        session_id = context.get('session_id')
                    
                    record_ai_usage(
                        model=model or "unknown",
                        function=function_name,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        duration_ms=duration_ms,
                        success=success,
                        user_id=user_id,
                        anchor_id=anchor_id,
                        session_id=session_id,
                        error_msg=error_msg
                    )
                except Exception as monitor_exc:
                    logger.error(f"记录 AI 使用情况失败: {monitor_exc}")
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = True
            error_msg = None
            result = None
            input_tokens = 0
            output_tokens = 0
            model = model_name
            
            try:
                result = await func(*args, **kwargs)
                
                # 尝试从结果中提取 Token 信息
                if extract_tokens:
                    input_tokens, output_tokens = extract_tokens(result)
                elif hasattr(result, 'usage'):
                    # 标准 OpenAI 格式
                    input_tokens = getattr(result.usage, 'prompt_tokens', 0)
                    output_tokens = getattr(result.usage, 'completion_tokens', 0)
                
                # 尝试从结果中提取模型名称
                if not model and hasattr(result, 'model'):
                    model = result.model
                
                return result
                
            except Exception as exc:
                success = False
                error_msg = str(exc)
                logger.error(f"{function_name} 调用失败: {exc}")
                raise
                
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                # 记录使用情况
                try:
                    # 从 kwargs 中提取上下文信息
                    user_id = kwargs.get('user_id')
                    anchor_id = kwargs.get('anchor_id')
                    session_id = kwargs.get('session_id')
                    
                    # 如果还没提取到，尝试从 args[0]（通常是 context）中获取
                    if not anchor_id and len(args) > 0 and isinstance(args[0], dict):
                        context = args[0]
                        anchor_id = context.get('anchor_id')
                        user_id = context.get('user_id')
                        session_id = context.get('session_id')
                    
                    record_ai_usage(
                        model=model or "unknown",
                        function=function_name,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        duration_ms=duration_ms,
                        success=success,
                        user_id=user_id,
                        anchor_id=anchor_id,
                        session_id=session_id,
                        error_msg=error_msg
                    )
                except Exception as monitor_exc:
                    logger.error(f"记录 AI 使用情况失败: {monitor_exc}")
        
        # 根据函数类型返回对应的 wrapper
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def extract_openai_tokens(response) -> tuple[int, int]:
    """提取 OpenAI 格式的 Token 信息"""
    if hasattr(response, 'usage'):
        return (
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )
    return (0, 0)


def extract_qwen_tokens(response) -> tuple[int, int]:
    """提取 Qwen 格式的 Token 信息"""
    # Qwen 使用 OpenAI 兼容格式
    return extract_openai_tokens(response)
