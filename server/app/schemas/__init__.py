# -*- coding: utf-8 -*-
"""
统一的数据模型定义（Schemas）

所有 Pydantic 模型定义统一在此目录，按模块组织。
API 文件只导入类型，不定义类型。
"""

from .common import (
    BaseResponse,
    PaginationParams,
    PaginatedResponse,
)

__all__ = [
    'BaseResponse',
    'PaginationParams',
    'PaginatedResponse',
]

