# -*- coding: utf-8 -*-
"""
server/modules/streamcap - 直播平台处理器模块
从 StreamCap 项目提取的核心平台处理和媒体构建功能
"""

# 平台处理器 - 用于解析直播间URL并获取真实推流地址
from .platforms import (
    get_platform_handler,
    get_platform_info,
    PlatformHandler,
    StreamData,
)

# 媒体构建器 - 用于构建 FFmpeg 命令
from .media import create_builder

__all__ = [
    "get_platform_handler",
    "get_platform_info",
    "PlatformHandler",
    "StreamData",
    "create_builder",
]

