"""
问题提取模块空实现。

接口保留但不再依赖分词或 NLP 逻辑，统一返回空结果，
避免影响依赖方的调用流程。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from server.utils.logger import LoggerMixin


class QuestionExtractor(LoggerMixin):
    """空实现：不再分析或分类弹幕问题。"""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.logger.info("问题提取功能已禁用，所有接口返回空列表。")

    def extract_questions(self, text: str) -> List[Dict[str, Any]]:
        return []

    def extract_from_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "total_questions": 0,
            "questions": [],
            "category_distribution": {},
            "priority_distribution": {},
        }
