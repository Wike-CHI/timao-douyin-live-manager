"""Knowledge base loader and retriever for live analysis and scripting."""
from __future__ import annotations

import ast
import functools
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

logger = logging.getLogger(__name__)


KNOWLEDGE_ROOT = Path("docs/直播运营和主播话术/主题分类")


@dataclass(frozen=True)
class KnowledgeSnippet:
    """Represents a single knowledge entry prepared for prompts."""

    title: str
    date: str
    theme: str
    tags: List[str]
    summary: str
    highlights: List[str]
    content: str
    source_path: Path

    def to_prompt_block(self) -> str:
        bullet_lines = [f"- {point}" for point in self.highlights[:3] if point]
        bullets = "\n".join(bullet_lines) or "- （暂无概括）"
        return (
            f"《{self.title}》 ({self.date or '未知日期'} · {self.theme})\n"
            f"关键要点：\n{bullets}\n"
            f"摘要：{self.summary}"
        )


class KnowledgeBase:
    """Loads markdown knowledge documents and offers lightweight retrieval."""

    def __init__(self, root: Path = KNOWLEDGE_ROOT) -> None:
        self.root = root
        self._documents: List[KnowledgeSnippet] = []
        self._index: List[Dict[str, any]] = []
        if not self.root.exists():
            logger.warning("知识库目录不存在：%s", self.root)
            return
        self._load_documents()

    def _load_documents(self) -> None:
        pattern = re.compile(r"[\u4e00-\u9fa5a-zA-Z0-9]+")
        for path in sorted(self.root.rglob("*.md")):
            try:
                snippet = self._parse_markdown(path)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("知识库文件解析失败 %s: %s", path, exc)
                continue
            tokens = set(pattern.findall((snippet.title + " " + snippet.content).lower()))
            tokens.update(tag.lower() for tag in snippet.tags)
            entry = {
                "snippet": snippet,
                "tokens": tokens,
                "tags": {tag.lower() for tag in snippet.tags},
                "theme": (snippet.theme or "").lower(),
            }
            self._documents.append(snippet)
            self._index.append(entry)
        logger.info("知识库加载完成，共 %d 篇文档", len(self._documents))

    def _parse_markdown(self, path: Path) -> KnowledgeSnippet:
        text = path.read_text(encoding="utf-8")
        yaml_block, body = self._split_front_matter(text)
        meta = self._parse_yaml_block(yaml_block)
        title = str(meta.get("title") or path.stem).strip()
        date = str(meta.get("date") or "").strip()
        theme = str(meta.get("theme") or meta.get("category") or "").strip()
        tags = meta.get("tags")
        if isinstance(tags, list):
            tag_list = [str(t).strip() for t in tags if str(t).strip()]
        elif isinstance(tags, str):
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        else:
            tag_list = []
        summary, highlights = self._extract_sections(body)
        return KnowledgeSnippet(
            title=title,
            date=date,
            theme=theme,
            tags=tag_list,
            summary=summary,
            highlights=highlights,
            content=body,
            source_path=path,
        )

    def _split_front_matter(self, text: str) -> (List[str], str):
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            return [], text
        yaml_lines: List[str] = []
        for line in lines[1:]:
            if line.strip() == "---":
                break
            yaml_lines.append(line)
        else:
            return [], text
        yaml_end = len(yaml_lines) + 2
        rest = "\n".join(lines[yaml_end:])
        return yaml_lines, rest

    def _parse_yaml_block(self, lines: List[str]) -> Dict[str, object]:
        data: Dict[str, object] = {}
        for raw in lines:
            if not raw or raw.strip().startswith("#"):
                continue
            if ":" not in raw:
                continue
            key, value = raw.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                try:
                    parsed = ast.literal_eval(value)
                except Exception:
                    parsed = [v.strip() for v in value[1:-1].split(",") if v.strip()]
                data[key] = parsed
            else:
                data[key] = value
        return data

    def _extract_sections(self, body: str) -> (str, List[str]):
        summary = ""
        highlights: List[str] = []
        lines = body.splitlines()
        current_section = None
        buffer: List[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## "):
                if current_section == "core" and buffer:
                    highlights = [item.strip("- ") for item in buffer if item.strip()]
                buffer = []
                title = stripped[3:]
                if "核心要点" in title:
                    current_section = "core"
                elif "详细记录" in title:
                    current_section = "detail"
                else:
                    current_section = None
                continue
            if current_section == "core":
                buffer.append(stripped)
            if not summary and stripped:
                summary = stripped
        if current_section == "core" and buffer and not highlights:
            highlights = [item.strip("- ") for item in buffer if item.strip()]
        summary = summary[:120]
        highlights = [h[:160] for h in highlights[:5]]
        return summary, highlights

    def query(
        self,
        queries: Sequence[str],
        *,
        themes: Optional[Sequence[str]] = None,
        tags: Optional[Sequence[str]] = None,
        limit: int = 3,
    ) -> List[KnowledgeSnippet]:
        if not self._index:
            return []
        query_terms = [q.lower() for q in queries if q]
        theme_terms = [t.lower() for t in (themes or []) if t]
        tag_terms = [t.lower() for t in (tags or []) if t]
        scores: List[tuple[int, KnowledgeSnippet]] = []
        for entry in self._index:
            score = 0
            tokens = entry["tokens"]
            entry_tags = entry["tags"]
            entry_theme = entry["theme"]
            for term in query_terms:
                if term in tokens:
                    score += 6
                elif term in entry_tags:
                    score += 8
                else:
                    # partial match
                    score += sum(1 for token in tokens if token.startswith(term[:4]))
            for theme in theme_terms:
                if theme and theme == entry_theme:
                    score += 5
            for tag in tag_terms:
                if tag in entry_tags:
                    score += 4
            if score:
                scores.append((score, entry["snippet"]))
        scores.sort(key=lambda item: item[0], reverse=True)
        return [snippet for _, snippet in scores[:limit]]


@functools.lru_cache(maxsize=1)
def get_knowledge_base() -> KnowledgeBase:
    """Return a cached knowledge base instance."""

    return KnowledgeBase()


def preview_snippets(snippets: Iterable[KnowledgeSnippet]) -> str:
    blocks = [snippet.to_prompt_block() for snippet in snippets]
    return "\n\n".join(blocks)
