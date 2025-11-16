"""
热词替换工具的空实现。

保留接口，直接返回原文本，不再加载或应用替换规则。
"""

from __future__ import annotations

from typing import Dict, List


class HotwordReplacer:
    """直接返回传入文本，不执行任何替换。"""

    def __init__(self, path: str | None = None) -> None:
        self.path = path
        self.rules: Dict[str, List[str]] = {}

    def apply(self, text: str) -> str:
        return text

    def set_rules(self, replace: Dict[str, List[str]]) -> None:
        self.rules = {}
