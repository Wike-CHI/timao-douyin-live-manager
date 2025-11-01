# -*- coding: utf-8 -*-
"""
StreamCap 工具模块
"""

from .utils import trace_error_decorator
import logging

# 使用标准 logging
logger = logging.getLogger(__name__)

__all__ = [
    "trace_error_decorator",
    "logger",
]

