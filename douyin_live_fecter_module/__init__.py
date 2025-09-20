# -*- coding: utf-8 -*-
"""
抖音直播抓取模块（基于 F2）
对外暴露:
- 适配器: LiveDataAdapter, NoopAdapter, CallbackAdapter, WebsocketBroadcasterAdapter

说明：为避免在包导入阶段触发 F2 依赖（如 browser_cookie3），不在此处导入 service。
需要 DouyinLiveFetcher 时请从子模块导入：
from douyin_live_fecter_module.service import DouyinLiveFetcher
"""

from .adapters import (
    LiveDataAdapter,
    NoopAdapter,
    CallbackAdapter,
    WebsocketBroadcasterAdapter,
    CompositeAdapter,
)