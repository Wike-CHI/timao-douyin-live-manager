# -*- coding: utf-8 -*-
"""
通用数据模型定义

包含所有 API 共享的基础响应模型、分页参数等。
"""

from typing import Optional, Generic, TypeVar, Union, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """
    统一的基础响应模型
    
    所有 API 响应都应该使用此模型，确保格式一致。
    
    示例:
        return BaseResponse[dict](data={"key": "value"})
        return BaseResponse[LoginResponse](data=login_data)
    """
    success: bool = Field(default=True, description="操作是否成功")
    message: str = Field(default="ok", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")


class PaginationParams(BaseModel):
    """
    统一的分页参数模型
    
    所有列表查询 API 都应该使用此模型。
    """
    skip: int = Field(default=0, ge=0, description="跳过的记录数")
    limit: int = Field(default=100, ge=1, le=1000, description="每页记录数")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    统一的分页响应模型
    
    所有分页查询 API 都应该使用此模型。
    """
    items: List[T] = Field(..., description="数据列表")
    total: int = Field(..., ge=0, description="总记录数")
    skip: int = Field(..., ge=0, description="跳过的记录数")
    limit: int = Field(..., ge=1, description="每页记录数")


class ErrorResponse(BaseModel):
    """
    统一的错误响应模型
    
    用于标准化错误响应格式。
    """
    success: bool = Field(default=False, description="操作失败")
    message: str = Field(..., description="错误消息")
    detail: Optional[Union[str, Dict[str, Any], List[Dict[str, Any]]]] = Field(
        default=None, 
        description="详细错误信息"
    )
    code: Optional[str] = Field(default=None, description="错误代码")

