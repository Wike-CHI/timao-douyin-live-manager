"""
Style memory management powered by LangChain VectorStore memory.

Each anchor has a dedicated vector store persisted under ``records/style_memory``.
We ingest highlights/catchphrases from live summaries and retrieve the most
relevant snippets to prime downstream prompts (Qwen analysis, tip generation).
"""

from __future__ import annotations

import importlib
import json
import logging
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from langchain.memory import VectorStoreRetrieverMemory
    from langchain_community.vectorstores import DocArrayInMemorySearch
    from langchain_core.embeddings import Embeddings
    from langchain_core.vectorstores import VectorStore
    LANGCHAIN_AVAILABLE = True
except Exception as exc:  # pragma: no cover - graceful fallback
    LANGCHAIN_AVAILABLE = False
    VectorStore = object  # type: ignore[misc,assignment]
    Embeddings = object  # type: ignore[misc,assignment]
    VectorStoreRetrieverMemory = object  # type: ignore[misc,assignment]
    DocArrayInMemorySearch = None  # type: ignore[misc,assignment]
    logger.warning("LangChain components unavailable: %s", exc)

if TYPE_CHECKING:
    from langchain.memory import VectorStoreRetrieverMemory as _VectorStoreRetrieverMemoryT
    from langchain_core.embeddings import Embeddings as _EmbeddingsT
    from langchain_core.vectorstores import VectorStore as _VectorStoreT


def _sanitize_anchor_id(anchor_id: Optional[str]) -> str:
    if not anchor_id:
        return "default"
    cleaned = re.sub(r"[\\s/]+", "_", anchor_id.strip())
    cleaned = re.sub(r"[^0-9A-Za-z_\\-]+", "_", cleaned)
    cleaned = cleaned.strip("_") or "default"
    return cleaned[:120]


class _BagOfWordsEmbeddings(Embeddings):  # pragma: no cover - deterministic fallback
    """Lightweight embedding fallback when HuggingFace models are unavailable."""

    def __init__(self, dim: int = 256):
        self.dim = dim

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[\\w']+", text.lower())

    def _embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        for token in self._tokenize(text):
            idx = hash(token) % self.dim
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


@dataclass
class _StoreBundle:
    store: Any
    embedding_name: str


class StyleMemoryManager:
    """Manage per-anchor style memory backed by LangChain vector stores."""

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.base_dir = Path(base_dir or Path("records") / "style_memory").resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name
        self._stores: Dict[str, _StoreBundle] = {}

    # ------------------------------------------------------------------ public
    def ingest_summary(self, anchor_id: Optional[str], summary: Dict[str, object]) -> None:
        """Persist highlights/suggestions/scripts from the summary into memory."""
        if not LANGCHAIN_AVAILABLE:
            return
        anchor_key = _sanitize_anchor_id(anchor_id)
        texts = self._extract_summary_snippets(summary)
        if not texts:
            return
        bundle = self._load_store(anchor_key, create=True)
        memory = self._build_memory(bundle.store)
        for text in texts:
            memory.save_context(
                {"prompt": f"style_update::{anchor_key}"},
                {"style_notes": text},
            )
        self._persist_store(anchor_key, bundle)

    def ingest_scripts(self, anchor_id: Optional[str], scripts: Iterable[Dict[str, object]]) -> None:
        """Persist manually curated scripts (e.g., AI outputs validated by ops)."""
        if not LANGCHAIN_AVAILABLE:
            return
        anchor_key = _sanitize_anchor_id(anchor_id)
        texts = [str(s.get("text") or s.get("content") or "").strip() for s in scripts or []]
        texts = [t for t in texts if t]
        if not texts:
            return
        bundle = self._load_store(anchor_key, create=True)
        memory = self._build_memory(bundle.store)
        for text in texts:
            memory.save_context(
                {"prompt": f"script::{anchor_key}"},
                {"style_notes": text},
            )
        self._persist_store(anchor_key, bundle)

    def fetch_context(self, anchor_id: Optional[str], k: int = 5) -> str:
        """Retrieve condensed style notes for prompt priming."""
        if not LANGCHAIN_AVAILABLE:
            return ""
        anchor_key = _sanitize_anchor_id(anchor_id)
        bundle = self._load_store(anchor_key, create=False)
        if bundle is None:
            return ""
        memory = self._build_memory(bundle.store, k=k)
        data = memory.load_memory_variables({"prompt": "主播语言风格&口头禅"})
        return data.get("style_notes", "")

    def available(self) -> bool:
        return LANGCHAIN_AVAILABLE

    # ------------------------------------------------------------------ internals
    def _build_memory(
        self,
        store: Any,
        k: int = 5,
    ) -> Any:
        retriever = store.as_retriever(search_kwargs={"k": k})
        return VectorStoreRetrieverMemory(
            retriever=retriever,
            memory_key="style_notes",
            input_key="prompt",
        )

    def _load_store(self, anchor_key: str, create: bool) -> Optional[_StoreBundle]:
        if anchor_key in self._stores:
            return self._stores[anchor_key]
        path = self._store_path(anchor_key)
        embedding = self._resolve_embedding()
        if not LANGCHAIN_AVAILABLE:
            return None
        store: Optional[Any] = None
        if path.exists():
            try:
                store = DocArrayInMemorySearch.load_local(str(path), embeddings=embedding)
            except Exception as exc:
                logger.warning("Failed to load style memory for %s: %s", anchor_key, exc)
        if store is None and create:
            store = DocArrayInMemorySearch([], embedding=embedding)
        if store is None:
            return None
        bundle = _StoreBundle(store=store, embedding_name=self.model_name)
        self._stores[anchor_key] = bundle
        return bundle

    def _persist_store(self, anchor_key: str, bundle: _StoreBundle) -> None:
        path = self._store_path(anchor_key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            bundle.store.save_local(str(path))
        except Exception as exc:
            logger.warning("Failed to persist style memory for %s: %s", anchor_key, exc)

    def _store_path(self, anchor_key: str) -> Path:
        return self.base_dir / anchor_key / "vector_store"

    def _resolve_embedding(self) -> Any:
        if hasattr(self, "_embedding") and self._embedding is not None:
            return self._embedding  # type: ignore[attr-defined]
        embedding: Optional[Any] = None
        if LANGCHAIN_AVAILABLE:
            last_exc: Optional[Exception] = None
            providers = (
                ("langchain_huggingface", "HuggingFaceEmbeddings"),
                ("langchain_huggingface.embeddings", "HuggingFaceEmbeddings"),
                ("langchain_community.embeddings", "HuggingFaceEmbeddings"),
            )
            for module_path, attr in providers:
                try:
                    module = importlib.import_module(module_path)
                    hf_cls = getattr(module, attr)
                    embedding = hf_cls(model_name=self.model_name)
                    break
                except Exception as exc:  # pragma: no cover - optional dependency
                    last_exc = exc
                    continue
            if embedding is None:
                if last_exc:
                    logger.warning(
                        "HuggingFace embeddings unavailable (%s); falling back to bag-of-words.",
                        last_exc,
                    )
                embedding = _BagOfWordsEmbeddings()
        else:
            embedding = _BagOfWordsEmbeddings()
        self._embedding = embedding  # type: ignore[attr-defined]
        return embedding

    def _extract_summary_snippets(self, summary: Dict[str, object]) -> List[str]:
        snippets: List[str] = []
        if not isinstance(summary, dict):
            return snippets
        # structured keys
        for key in ("highlight_points", "suggestions", "risks", "top_questions"):
            values = summary.get(key)
            if isinstance(values, list):
                snippets.extend(str(v).strip() for v in values if v)
        scripts = summary.get("scripts")
        if isinstance(scripts, list):
            for item in scripts:
                if isinstance(item, dict):
                    text = item.get("text") or item.get("content")
                else:
                    text = item
                if text:
                    snippets.append(str(text).strip())
        profile = summary.get("style_profile")
        if isinstance(profile, dict):
            persona = profile.get("persona")
            tone = profile.get("tone")
            catchphrases = profile.get("catchphrases")
            if persona:
                snippets.append(f"Persona: {persona}")
            if tone:
                snippets.append(f"Tone: {tone}")
            if isinstance(catchphrases, list):
                snippets.extend(f"Catchphrase: {c}" for c in catchphrases if c)
        vibe = summary.get("vibe")
        if isinstance(vibe, dict):
            level = vibe.get("level")
            score = vibe.get("score")
            if level:
                snippets.append(f"Room vibe {level} (score={score})")
        return [s for s in snippets if s]


def load_latest_summary(path: Path) -> Optional[Dict[str, object]]:
    """Utility helper for loading summary JSON when ingesting offline artifacts."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to load summary %s: %s", path, exc)
        return None
