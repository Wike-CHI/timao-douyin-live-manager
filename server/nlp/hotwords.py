# -*- coding: utf-8 -*-
"""Simple hotword post-processing.

Loads a JSON dictionary from data/hotwords.json and applies replacements to
final sentences. The JSON structure:

{
  "replace": {
    "正确词": ["常见误写1", "常见误写2"],
    "品牌名": ["拼写变体", "口音近音"],
    "地名": ["别名"]
  }
}

This is intentionally minimal and fast; later we can extend with pinyin/fuzzy.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List


class HotwordReplacer:
    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path) if path else Path("data/hotwords.json")
        self.rules: Dict[str, List[str]] = {}
        self._regexes: List[tuple[re.Pattern, str]] = []
        self._load()

    def _load(self) -> None:
        try:
            if not self.path.exists():
                return
            data = json.loads(self.path.read_text(encoding="utf-8")) or {}
            repl = data.get("replace") or {}
            if not isinstance(repl, dict):
                return
            self.rules = {str(k): list(v) for k, v in repl.items() if isinstance(v, list)}
            # Compile regex pairs (variant -> canonical)
            pairs: List[tuple[str, str]] = []
            for canonical, variants in self.rules.items():
                for v in variants:
                    if not v:
                        continue
                    pairs.append((v, canonical))
            # Sort longer variants first to reduce partial overshadow
            pairs.sort(key=lambda x: len(x[0]), reverse=True)
            self._regexes = []
            for v, cano in pairs:
                # plain substring replace; escape regex specials
                pat = re.escape(v)
                self._regexes.append((re.compile(pat), cano))
        except Exception:
            self.rules = {}
            self._regexes = []

    def apply(self, text: str) -> str:
        if not text or not self._regexes:
            return text
        out = text
        for rgx, cano in self._regexes:
            out = rgx.sub(cano, out)
        return out

    def set_rules(self, replace: Dict[str, List[str]]) -> None:
        if not isinstance(replace, dict):
            return
        self.rules = {str(k): list(v) for k, v in replace.items() if isinstance(v, list)}
        pairs: List[tuple[str, str]] = []
        for canonical, variants in self.rules.items():
            for v in variants:
                if not v:
                    continue
                pairs.append((v, canonical))
        pairs.sort(key=lambda x: len(x[0]), reverse=True)
        self._regexes = []
        for v, cano in pairs:
            pat = re.escape(v)
            self._regexes.append((re.compile(pat), cano))
