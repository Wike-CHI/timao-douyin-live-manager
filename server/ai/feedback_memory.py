"""
LangChain-powered feedback memory for AI script generation.

This module collects human ratings of generated scripts, persists them in
vector stores (DocArrayInMemorySearch) and exposes guidance aggregated from
positive/negative feedback so the LLM prompt can be tuned dynamically.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import shutil

try:  # pragma: no cover - optional dependency
    from langchain_community.vectorstores import DocArrayInMemorySearch
    from langchain_core.documents import Document
    LANGCHAIN_AVAILABLE = True
except Exception as exc:  # pragma: no cover
    LANGCHAIN_AVAILABLE = False
    DocArrayInMemorySearch = None  # type: ignore
    Document = None  # type: ignore

# Re-use helper utilities from style memory module to keep conventions aligned.
try:  # pragma: no cover - optional dependency
    from .style_memory import (
        LANGCHAIN_AVAILABLE as STYLE_MEMORY_AVAILABLE,
        _sanitize_anchor_id,
        _BagOfWordsEmbeddings,
    )
except Exception:  # pragma: no cover
    STYLE_MEMORY_AVAILABLE = LANGCHAIN_AVAILABLE and False  # default to False

    def _sanitize_anchor_id(anchor_id: Optional[str]) -> Optional[str]:
        if anchor_id is None:
            return None
        text = str(anchor_id).strip()
        if not text:
            return None
        return text.replace(" ", "_")[:120] or None

    class _BagOfWordsEmbeddings:  # type: ignore
        """Fallback embedding identical to style memory fallback."""

        def __init__(self, dim: int = 256) -> None:
            self.dim = dim

        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            return [[0.0] * self.dim for _ in texts]

        def embed_query(self, text: str) -> List[float]:
            return [0.0] * self.dim


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


@dataclass
class _StoreBundle:
    store: Any
    embedding_name: str


class FeedbackMemoryManager:
    """Manage human feedback for AI scripts with LangChain vector stores."""

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.base_dir = Path(base_dir or Path("records") / "feedback_memory").resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name
        self._stores: Dict[str, Dict[str, _StoreBundle]] = {}
        self._embedding = None
        self._log_path = self.base_dir / "feedback_log.jsonl"

    # ------------------------------------------------------------------ helpers
    def available(self) -> bool:
        return LANGCHAIN_AVAILABLE and STYLE_MEMORY_AVAILABLE

    def _resolve_embedding(self) -> Any:
        if self._embedding is not None:
            return self._embedding
        embedding: Any = None
        last_exc: Optional[Exception] = None
        if self.available():
            providers = (
                ("langchain_huggingface", "HuggingFaceEmbeddings"),
                ("langchain_huggingface.embeddings", "HuggingFaceEmbeddings"),
                ("langchain_community.embeddings", "HuggingFaceEmbeddings"),
            )
            for module_path, attr in providers:
                try:
                    module = __import__(module_path, fromlist=[attr])
                    embedding_cls = getattr(module, attr)
                    embedding = embedding_cls(model_name=self.model_name)
                    break
                except Exception as exc:  # pragma: no cover
                    last_exc = exc
                    continue
            if embedding is None and last_exc is not None:
                # Fallback to deterministic embedding to keep pipeline working.
                embedding = _BagOfWordsEmbeddings()
        else:
            embedding = _BagOfWordsEmbeddings()
        self._embedding = embedding
        return embedding

    def _store_path(self, anchor_key: str, sentiment: str) -> Path:
        return self.base_dir / anchor_key / sentiment / "vector_store"

    def _load_store(
        self, anchor_key: str, sentiment: str, create: bool
    ) -> Optional[_StoreBundle]:
        if anchor_key in self._stores and sentiment in self._stores[anchor_key]:
            return self._stores[anchor_key][sentiment]
        if not self.available():
            return None
        embedding = self._resolve_embedding()
        path = self._store_path(anchor_key, sentiment)
        store: Optional[Any] = None
        if path.exists():
            try:
                store = DocArrayInMemorySearch.load_local(  # type: ignore[arg-type]
                    str(path), embeddings=embedding
                )
            except Exception:
                store = None
        if store is None and create:
            store = DocArrayInMemorySearch([], embedding=embedding)  # type: ignore[call-arg]
        if store is None:
            return None
        bundle = _StoreBundle(store=store, embedding_name=self.model_name)
        self._stores.setdefault(anchor_key, {})[sentiment] = bundle
        return bundle

    def _persist_store(self, anchor_key: str, sentiment: str, bundle: _StoreBundle) -> None:
        path = self._store_path(anchor_key, sentiment)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            bundle.store.save_local(str(path))
        except Exception:
            pass

    # ------------------------------------------------------------------ public
    def record_feedback(
        self,
        anchor_id: Optional[str],
        script_id: str,
        script_text: str,
        score: int,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist a feedback entry and keep a JSONL audit log."""
        if not script_text:
            return
        tags = tags or []
        anchor_key = _sanitize_anchor_id(anchor_id)
        if not anchor_key:
            return
        sentiment = self._score_to_sentiment(score)
        bundle = self._load_store(anchor_key, sentiment, create=True)
        if self.available() and bundle and Document is not None:
            doc = Document(
                page_content=script_text.strip(),
                metadata={
                    "script_id": script_id,
                    "score": score,
                    "tags": tags,
                    "timestamp": _now_iso(),
                    **(metadata or {}),
                },
            )
            bundle.store.add_documents([doc])
            self._persist_store(anchor_key, sentiment, bundle)
        # 记录日志（即便 LangChain 不可用也能回溯）
        payload = {
            "anchor_id": anchor_key,
            "script_id": script_id,
            "score": score,
            "tags": tags,
            "sentiment": sentiment,
            "text": script_text,
            "timestamp": _now_iso(),
            "metadata": metadata or {},
        }
        try:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def build_guidance(self, anchor_id: Optional[str], top_k: int = 4) -> str:
        """Aggregate positive/negative feedback into prompt-ready guidance."""
        if not self.available():
            return ""
        anchor_key = _sanitize_anchor_id(anchor_id)
        if not anchor_key:
            return ""
        sections: List[str] = []
        for sentiment, title_positive, title_negative in (
            ("positive", "偏受欢迎的话术特征：", "常见优点标签："),
            ("negative", "需要避免的表达：", "常见风险标签："),
        ):
            bundle = self._load_store(anchor_key, sentiment, create=False)
            if not bundle:
                continue
            retriever = bundle.store.as_retriever(search_kwargs={"k": top_k})
            query = (
                "live streaming script strengths"
                if sentiment == "positive"
                else "live streaming script weaknesses"
            )
            docs = retriever.get_relevant_documents(query)
            if not docs:
                continue
            tag_counter: Counter[str] = Counter()
            bullet_lines: List[str] = []
            for doc in docs:
                text = doc.page_content.strip()
                if text:
                    bullet_lines.append(text)
                tag_counter.update((doc.metadata or {}).get("tags") or [])
            if bullet_lines:
                sections.append(title_positive + "\n- " + "\n- ".join(bullet_lines[:top_k]))
            if tag_counter:
                top_tags = ", ".join(
                    f"{tag}×{count}" for tag, count in tag_counter.most_common(3)
                )
                sections.append(f"{title_negative} {top_tags}")
        return "\n".join(sections)

    def _score_to_sentiment(self, score: int) -> str:
        if score >= 4:
            return "positive"
        if score <= 2:
            return "negative"
        return "neutral"

    def reset_anchor_memory(self, anchor_id: Optional[str]) -> None:
        """Remove cached and on-disk feedback memory for the specified anchor."""
        anchor_key = _sanitize_anchor_id(anchor_id)
        if not anchor_key:
            return
        self._stores.pop(anchor_key, None)
        target_dir = self.base_dir / anchor_key
        try:
            shutil.rmtree(target_dir, ignore_errors=True)
        except Exception:
            pass


_feedback_manager: Optional[FeedbackMemoryManager] = None


def get_feedback_manager() -> FeedbackMemoryManager:
    global _feedback_manager
    if _feedback_manager is None:
        _feedback_manager = FeedbackMemoryManager()
    return _feedback_manager
