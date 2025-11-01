# -*- coding: utf-8 -*-
"""
平台处理器模块
"""

__all__ = [
    "get_platform_handler",
    "get_platform_info",
    "PlatformHandler",
    "StreamData",
]

def __getattr__(name):
    """延迟导入属性"""
    if name in ["get_platform_handler", "get_platform_info", "PlatformHandler", "StreamData"]:
        from .platform_handlers import get_platform_handler, get_platform_info, PlatformHandler, StreamData
        module_attrs = {
            "get_platform_handler": get_platform_handler,
            "get_platform_info": get_platform_info,
            "PlatformHandler": PlatformHandler,
            "StreamData": StreamData,
        }
        value = module_attrs[name]
        globals()[name] = value
        return value
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

