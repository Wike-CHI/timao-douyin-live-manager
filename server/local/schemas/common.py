"""Common Pydantic schemas shared across FastAPI routes."""

from __future__ import annotations

from typing import Generic, Optional, TypeVar, List

from pydantic import BaseModel, Field


T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """Unified success response structure for REST APIs."""

    success: bool = True
    message: str = "ok"
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    """Standardised error payload."""

    success: bool = False
    message: str
    detail: Optional[str] = None
    data: Optional[dict] = None


class PaginationParams(BaseModel):
    """统一的分页参数"""

    skip: int = Field(0, ge=0, description="跳过的记录数")
    limit: int = Field(100, ge=1, le=1000, description="返回的记录数")


class PaginatedResponse(BaseModel, Generic[T]):
    """统一的分页响应容器"""

    success: bool = True
    message: str = "ok"
    items: List[T] = Field(description="数据项列表")
    total: int = Field(description="总记录数")
    skip: int = Field(description="跳过的记录数")
    limit: int = Field(description="返回的记录数")


def success_response(data: Optional[T] = None, message: str = "ok") -> BaseResponse[T]:
    """Helper to build a success response with unified shape."""

    return BaseResponse[T](data=data, message=message)

