# -*- coding: utf-8 -*-
"""Lightweight phonetic correction for ASR outputs."""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Sequence, Set

try:  # pragma: no cover - optional dependency
    from pypinyin import lazy_pinyin  # type: ignore
except Exception:  # pragma: no cover - fallback when pypinyin missing
    lazy_pinyin = None  # type: ignore

try:
    from server.ai.knowledge_service import get_knowledge_base  # type: ignore
except Exception:  # pragma: no cover - keep import-time failures isolated
    get_knowledge_base = None  # type: ignore

logger = logging.getLogger(__name__)

_CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fa5]")
_WORD_PATTERN = re.compile(r"[\u4e00-\u9fa5]{2,4}")


class PhoneticCorrector:
    """Suggest replacements for homophonic errors using pinyin proximity."""

    def __init__(self, extra_terms: Optional[Iterable[str]] = None) -> None:
        self._enabled = bool(lazy_pinyin) and callable(get_knowledge_base or None)
        self._lexicon: Set[str] = set()
        self._pinyin_cache: Dict[str, str] = {}
        self._length_index: Dict[int, Set[str]] = defaultdict(set)
        self._context_terms: Set[str] = set()
        if not self._enabled:
            return

        base_terms: Sequence[str] = []
        try:
            kb = get_knowledge_base() if get_knowledge_base else None
            if kb is not None:
                base_terms = kb.candidate_terms()
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("PhoneticCorrector unable to preload knowledge terms: %s", exc)
        self._ingest_terms(base_terms)
        if extra_terms:
            self._ingest_terms(extra_terms)
        if not self._lexicon:
            # Without a lexicon there is nothing to correct; disable silently.
            self._enabled = False

    @staticmethod
    def _is_chinese(text: str) -> bool:
        return bool(_CHINESE_PATTERN.search(text))

    def _ingest_terms(self, terms: Iterable[str]) -> None:
        if not self._enabled:
            return
        for term in terms:
            if not term or not isinstance(term, str):
                continue
            word = term.strip()
            if not word:
                continue
            if not self._is_chinese(word):
                continue
            if word in self._lexicon:
                continue
            key = self._pinyin_key(word)
            if not key:
                continue
            self._lexicon.add(word)
            self._pinyin_cache[word] = key
            self._length_index[len(word)].add(word)

    def extend_context(self, terms: Iterable[str]) -> None:
        if not self._enabled:
            return
        normalized: List[str] = []
        for term in terms:
            if not term or not isinstance(term, str):
                continue
            word = term.strip()
            if not word or not self._is_chinese(word):
                continue
            normalized.append(word)
        if normalized:
            self._context_terms.update(normalized)
            self._ingest_terms(normalized)

    def correct(self, sentence: str, *, context_terms: Optional[Iterable[str]] = None) -> str:
        if not self._enabled or not sentence:
            return sentence
        if context_terms:
            self.extend_context(context_terms)
        context_set = set(self._context_terms)

        def _replace(match: re.Match[str]) -> str:
            original = match.group(0)
            candidate = self._choose_candidate(original, context_set)
            return candidate or original

        try:
            return _WORD_PATTERN.sub(_replace, sentence)
        except Exception:  # pragma: no cover - defensive
            return sentence

    def _choose_candidate(self, original: str, context_set: Set[str]) -> Optional[str]:
        if original in self._lexicon:
            return None
        orig_key = self._pinyin_key(original)
        if not orig_key:
            return None
        candidates = self._gather_candidates(len(original), context_set)
        if not candidates:
            return None
        best_term: Optional[str] = None
        best_score = 0.0
        for term in candidates:
            if term == original:
                continue
            cand_key = self._pinyin_cache.get(term)
            if not cand_key:
                continue
            distance = self._edit_distance(orig_key, cand_key)
            max_len = max(len(orig_key), len(cand_key))
            if max_len == 0:
                continue
            phonetic_similarity = (max_len - distance) / max_len
            if phonetic_similarity < 0.45:
                continue
            char_overlap = len(set(original) & set(term))
            score = phonetic_similarity * 6.0 + char_overlap * 1.5
            if len(term) == len(original):
                score += 1.2
            if distance <= 1:
                score += 1.5
            if term in context_set:
                score += 3.5
            if score > best_score:
                best_term = term
                best_score = score
        if best_term and best_score >= 6.0:
            return best_term
        return None

    def _gather_candidates(self, length: int, context_set: Set[str]) -> List[str]:
        seen: Set[str] = set()
        result: List[str] = []
        # Context terms take priority.
        for term in context_set:
            if abs(len(term) - length) <= 1 and term not in seen:
                result.append(term)
                seen.add(term)
        for delta in (0, -1, 1):
            pool = self._length_index.get(length + delta)
            if not pool:
                continue
            for term in pool:
                if term not in seen:
                    result.append(term)
                    seen.add(term)
        return result

    def _pinyin_key(self, text: str) -> str:
        if not lazy_pinyin:
            return ""
        try:
            return "".join(lazy_pinyin(text, errors="ignore"))
        except Exception:
            return ""

    @staticmethod
    def _edit_distance(a: str, b: str) -> int:
        """Classic Levenshtein distance; strings are short so O(n*m) is fine."""
        if a == b:
            return 0
        if not a:
            return len(b)
        if not b:
            return len(a)
        prev = list(range(len(b) + 1))
        curr = [0] * (len(b) + 1)
        for i, ca in enumerate(a, start=1):
            curr[0] = i
            prev_diagonal = i - 1
            for j, cb in enumerate(b, start=1):
                temp = prev[j]
                if ca == cb:
                    curr[j] = prev_diagonal
                else:
                    curr[j] = 1 + min(prev_diagonal, prev[j], curr[j - 1])
                prev_diagonal = temp
            prev, curr = curr, prev
        return prev[-1]


__all__ = ["PhoneticCorrector"]
