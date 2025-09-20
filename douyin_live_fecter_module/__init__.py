# -*- coding: utf-8 -*-
"""
抖音直播抓取模块（基于 F2）
对外暴露:
- DouyinLiveFetcher: 直播互动数据抓取器
- 适配器: LiveDataAdapter, NoopAdapter, CallbackAdapter, WebsocketBroadcasterAdapter
"""

from .service import DouyinLiveFetcher
from .adapters import LiveDataAdapter, NoopAdapter, CallbackAdapter, WebsocketBroadcasterAdapter, CompositeAdapter