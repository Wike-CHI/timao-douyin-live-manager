"""
精简版热词分析器

按需求关闭 NLP 热词分析，保持接口不变以避免调用方崩溃。
所有方法返回空结果或不执行实际处理。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from server.utils.logger import LoggerMixin


class HotwordAnalyzer(LoggerMixin):
    """空实现：不再做任何热词统计，返回空结果。"""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.is_running = False
        self.logger.info("热词分析功能已禁用，所有接口返回空结果。")

    def analyze_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """返回空热词分析结果。"""
        return self._empty_result()

    def get_hotwords(self, limit: int = 10, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """返回空列表，保持兼容。"""
        return []

    def get_trending_words(self, time_window: int = 300) -> List[Dict[str, Any]]:
        """返回空列表。"""
        return []

    def clear_cache(self) -> None:
        """无缓存可清理，仅记录日志。"""
        self.logger.debug("热词缓存已禁用，无需清理。")

    def start_analyzing(self) -> None:
        """标记运行状态，便于健康检查。"""
        self.is_running = True
        self.logger.info("热词分析任务已启动（空实现，无分析逻辑）。")

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "hot_words": [],
            "hot_phrases": [],
            "word_cloud_data": [],
            "stats": {
                "total_comments": 0,
                "total_words": 0,
                "unique_words": 0,
                "last_update": 0,
            },
        }
