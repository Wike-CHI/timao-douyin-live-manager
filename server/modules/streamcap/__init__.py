# -*- coding: utf-8 -*-
"""
server/modules/streamcap - 直播平台处理器模块
从 StreamCap 项目提取的核心平台处理和媒体构建功能
"""

# 延迟导入，避免 streamget 依赖导致的导入错误
__all__ = [
    "get_platform_handler",
    "get_platform_info",
    "PlatformHandler",
    "StreamData",
    "create_builder",
]

def __getattr__(name):
    """延迟导入属性"""
    if name in ["get_platform_handler", "get_platform_info", "PlatformHandler", "StreamData"]:
        from .platforms import get_platform_handler, get_platform_info, PlatformHandler, StreamData
        # 缓存导入的对象
        module_attrs = {
            "get_platform_handler": get_platform_handler,
            "get_platform_info": get_platform_info,
            "PlatformHandler": PlatformHandler,
            "StreamData": StreamData,
        }
        value = module_attrs[name]
        globals()[name] = value
        return value
    elif name == "create_builder":
        from .media import create_builder
        globals()[name] = create_builder
        return create_builder
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

