# -*- coding: utf-8 -*-
"""
本地化服务模块

提供本地JSON文件存储和配置管理功能，替代MySQL/Redis依赖。
"""

from .local_storage import LocalStorage, local_storage
from .local_config import LocalAIConfig

__all__ = ['LocalStorage', 'local_storage', 'LocalAIConfig']

