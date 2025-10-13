"""
情感分析模块空实现。

接口保留，以便历史调用保持兼容；所有分析结果均为空或默认值。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from server.utils.logger import LoggerMixin


class SentimentAnalyzer(LoggerMixin):
    """不执行实际情感分析的占位实现。"""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.logger.info("情感分析功能已禁用，返回默认中性结果。")

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        return {
            "sentiment": "neutral",
            "confidence": 0.5,
            "emotions": {},
            "keywords": [],
        }

    def analyze_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "overall_sentiment": "neutral",
            "sentiment_distribution": {},
            "average_confidence": 0.0,
            "total_comments": len(comments or []),
            "emotion_stats": {},
        }
