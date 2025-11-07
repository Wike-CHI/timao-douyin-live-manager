# -*- coding: utf-8 -*-
"""
统一的 API 错误处理工具

提供统一的错误处理函数和装饰器，减少重复代码。
"""

from typing import Callable, Any, Optional
from functools import wraps
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class APIError(Exception):
    """API 错误基类"""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or message
        super().__init__(self.message)


def handle_service_errors(func: Callable) -> Callable:
    """
    统一的错误处理装饰器
    
    自动捕获服务层异常并转换为 HTTPException。
    
    示例:
        @handle_service_errors
        async def my_api():
            # 服务层抛出异常会自动转换为 HTTPException
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except APIError as e:
            raise HTTPException(
                status_code=e.status_code,
                detail=e.detail
            )
        except ValueError as e:
            error_msg = str(e).lower()
            if "already running" in error_msg or "already started" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=str(e)
                )
            elif "invalid" in error_msg or "unsupported" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            elif "not found" in error_msg or "不存在" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        except Exception as e:
            logger.error(f"API 错误: {type(e).__name__}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"服务器内部错误: {str(e)}"
            )
    return wrapper


def normalize_error_message(error: Exception) -> tuple[int, str]:
    """
    标准化错误消息，返回 (status_code, detail)
    
    根据错误消息内容自动判断 HTTP 状态码。
    """
    error_msg = str(error).lower()
    
    # 冲突错误（409）
    if any(keyword in error_msg for keyword in [
        "already running", "already started", "already exists",
        "已在运行", "已启动", "已存在"
    ]):
        return status.HTTP_409_CONFLICT, str(error)
    
    # 无效请求（400）
    if any(keyword in error_msg for keyword in [
        "invalid", "unsupported", "不支持的", "无效的"
    ]):
        return status.HTTP_400_BAD_REQUEST, str(error)
    
    # 未找到（404）
    if any(keyword in error_msg for keyword in [
        "not found", "不存在", "未找到"
    ]):
        return status.HTTP_404_NOT_FOUND, str(error)
    
    # 未开播（400）
    if any(keyword in error_msg for keyword in [
        "not live", "未开播", "未直播"
    ]):
        return status.HTTP_400_BAD_REQUEST, str(error)
    
    # 服务初始化失败（500）
    if any(keyword in error_msg for keyword in [
        "initialize failed", "初始化失败", "sensevoice", "ffmpeg"
    ]):
        return status.HTTP_500_INTERNAL_SERVER_ERROR, str(error)
    
    # 默认错误（400）
    return status.HTTP_400_BAD_REQUEST, str(error)

