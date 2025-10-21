"""Knowledge base loader and retriever for live analysis and scripting."""
from __future__ import annotations

import ast
import functools
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


KNOWLEDGE_ROOT = Path("docs/直播运营和主播话术/主题分类")
TOPIC_LIBRARY_PATH = Path("docs/直播运营和主播话术/话题.txt")
HIGH_EQ_LIBRARY_ROOT = Path("docs/娱乐主播高情商话术大全")
TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fa5a-zA-Z0-9]+")


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
        self._topic_entries: List[Tuple[str, str]] = []
        self._topics_by_category: Dict[str, List[str]] = {}
        self._documents: List[KnowledgeSnippet] = []
        self._index: List[Dict[str, any]] = []
        if not self.root.exists():
            logger.warning("知识库目录不存在：%s", self.root)
            return
        self._load_documents()
        self._load_topic_snippets()
        self._load_high_eq_responses()

    def _load_documents(self) -> None:
        for path in sorted(self.root.rglob("*.md")):
            try:
                snippet = self._parse_markdown(path)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("知识库文件解析失败 %s: %s", path, exc)
                continue
            self._register_snippet(snippet)
        logger.info("知识库加载完成，共 %d 篇文档", len(self._documents))

    def _register_snippet(self, snippet: KnowledgeSnippet) -> None:
        tokens = set(TOKEN_PATTERN.findall((snippet.title + " " + snippet.content).lower()))
        tokens.update(tag.lower() for tag in snippet.tags)
        entry = {
            "snippet": snippet,
            "tokens": tokens,
            "tags": {tag.lower() for tag in snippet.tags},
            "theme": (snippet.theme or "").lower(),
        }
        self._documents.append(snippet)
        self._index.append(entry)

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

    def _load_topic_snippets(self) -> None:
        if not TOPIC_LIBRARY_PATH.exists():
            return
        try:
            text = TOPIC_LIBRARY_PATH.read_text(encoding="utf-8")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("话题库读取失败 %s: %s", TOPIC_LIBRARY_PATH, exc)
            return

        current_category: Optional[str] = None
        buffer: List[str] = []

        def flush_category() -> None:
            if not current_category or not buffer:
                return
            items = [item for item in buffer if item]
            if not items:
                return
            self._topics_by_category.setdefault(current_category, [])
            self._topics_by_category[current_category].extend(items)
            title = f"{current_category}互动话题"
            summary = items[0][:120]
            content = "\n".join(items)
            snippet = KnowledgeSnippet(
                title=title,
                date="",
                theme=current_category,
                tags=[current_category, "话题"],
                summary=summary,
                highlights=items[:5],
                content=content,
                source_path=TOPIC_LIBRARY_PATH,
            )
            self._register_snippet(snippet)
            for topic in items:
                self._topic_entries.append((current_category, topic))

        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            if re.match(r"^\d+\.", line):
                topic = line.split(".", 1)[1].strip() if "." in line else line
                if topic:
                    buffer.append(topic)
                continue
            # new category encountered
            flush_category()
            current_category = line
            buffer = []
        flush_category()
        if self._topic_entries:
            logger.info("话题库加载完成，共 %d 条话题", len(self._topic_entries))

    def _load_high_eq_responses(self) -> None:
        if not HIGH_EQ_LIBRARY_ROOT.exists():
            return
        total = 0
        for path in sorted(HIGH_EQ_LIBRARY_ROOT.rglob("*.txt")):
            try:
                raw = path.read_text(encoding="utf-8")
            except Exception:
                try:
                    raw = path.read_text(encoding="utf-8", errors="ignore")
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning("高情商话术文件读取失败 %s: %s", path, exc)
                    continue
            lines: List[str] = []
            for line in raw.splitlines():
                cleaned = line.strip()
                if not cleaned:
                    continue
                cleaned = re.sub(r"^[0-9]+[.\-、)]\s*", "", cleaned)
                if cleaned:
                    lines.append(cleaned)
            if not lines:
                continue
            relative_parent = path.parent
            try:
                relative_parent = path.parent.relative_to(HIGH_EQ_LIBRARY_ROOT)
            except ValueError:
                relative_parent = Path(".")
            theme = str(relative_parent).replace("\\", "/") if str(relative_parent) != "." else "高情商话术"
            tags = ["高情商话术"]
            if theme and theme != "高情商话术":
                tags.extend(theme.split("/"))
            title = f"高情商话术 · {path.stem}"
            summary = lines[0][:120]
            highlights = lines[:5]
            snippet = KnowledgeSnippet(
                title=title,
                date="",
                theme=theme,
                tags=tags,
                summary=summary,
                highlights=highlights,
                content="\n".join(lines[:200]),
                source_path=path,
            )
            self._register_snippet(snippet)
            total += 1
        if total:
            logger.info("高情商话术库加载完成，共 %d 条片段", total)

    def topic_suggestions(
        self,
        *,
        limit: int = 6,
        keywords: Optional[Sequence[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        use_ai: bool = True,
    ) -> List[Dict[str, str]]:
        """
        生成话题建议，优先使用AI智能生成，备用固定话题库
        
        Args:
            limit: 话题数量限制
            keywords: 关键词列表
            context: 直播上下文信息（转录、弹幕、人设等）
            use_ai: 是否使用AI生成（默认True）
        """
        # 优先尝试AI智能生成
        if use_ai and context:
            try:
                from .smart_topic_generator import create_smart_topic_generator
                
                # 尝试获取AI客户端
                ai_client = None
                try:
                    from .qwen_openai_compatible import get_qwen_client
                    ai_client = get_qwen_client()
                    logger.info("成功获取AI客户端，准备生成智能话题")
                except Exception as e:
                    logger.warning("无法获取AI客户端: %s，使用备用话题", e)
                
                if ai_client:
                    generator = create_smart_topic_generator(ai_client)
                    ai_topics = generator.generate_contextual_topics(
                        transcript=context.get('transcript', ''),
                        chat_messages=context.get('chat_messages', []),
                        persona=context.get('persona', {}),
                        vibe=context.get('vibe', {}),
                        current_topics=keywords,
                        limit=limit
                    )
                    
                    logger.info("AI生成话题结果: %s", ai_topics)
                    
                    if ai_topics and len(ai_topics) > 0:  # 只要有生成就使用
                        logger.info("使用AI生成话题，共 %d 条", len(ai_topics))
                        return ai_topics[:limit]
                    else:
                        logger.warning("AI生成话题为空，回退到固定话题库")
                        
            except Exception as exc:
                logger.warning("AI话题生成失败，回退到固定话题库: %s", exc)
        
        # 回退到原有的固定话题库逻辑
        return self._get_fallback_topic_suggestions(limit=limit, keywords=keywords)
    
    def _get_fallback_topic_suggestions(
        self,
        *,
        limit: int = 6,
        keywords: Optional[Sequence[str]] = None,
    ) -> List[Dict[str, str]]:
        """从固定话题库获取话题建议（备用方法）"""
        if not self._topic_entries:
            return self._get_default_topics(limit)
            
        keywords_norm: List[str] = []
        if keywords:
            for kw in keywords:
                if not kw:
                    continue
                for token in TOKEN_PATTERN.findall(str(kw).lower()):
                    if token and token not in keywords_norm:
                        keywords_norm.append(token)

        scored: List[Tuple[float, str, str]] = []
        for category, topics in self._topics_by_category.items():
            for topic in topics:
                candidate = topic.lower()
                score = 0.0
                for kw in keywords_norm:
                    if kw and kw in candidate:
                        score += 1.5
                    elif kw and kw in category.lower():
                        score += 1.0
                scored.append((score, category, topic))

        scored.sort(key=lambda item: item[0], reverse=True)
        suggestions: List[Dict[str, str]] = []
        seen: set[str] = set()
        
        # 扩展敏感话题过滤
        sensitive_keywords = {
            "彩礼", "结婚", "离婚", "收入", "工资", "房价", "城市地域", 
            "地域", "差异", "多少钱", "价格", "费用", "成本", "多少岁", 
            "年龄", "教育重视", "重视", "看重", "在意"
        }
        
        for score, category, topic in scored:
            if keywords_norm and score <= 0:
                continue
            if topic in seen:
                continue
                
            # 检查是否为敏感话题或固定模板
            topic_lower = topic.lower()
            is_sensitive = any(sensitive in topic_lower for sensitive in sensitive_keywords)
            
            # 检查是否包含固定模板格式
            if '#' in topic or '地域' in topic or ('差异' in topic and '城市' in topic):
                is_sensitive = True
                
            if is_sensitive:
                continue
                
            suggestions.append({"category": category, "topic": topic})
            seen.add(topic)
            if len(suggestions) >= limit:
                return suggestions

        if len(suggestions) < limit:
            for category, topics in self._topics_by_category.items():
                for topic in topics:
                    if topic in seen:
                        continue
                    
                    # 再次检查敏感话题和固定模板
                    topic_lower = topic.lower()
                    is_sensitive = any(sensitive in topic_lower for sensitive in sensitive_keywords)
                    
                    # 检查固定模板格式
                    if '#' in topic or '地域' in topic or ('差异' in topic and '城市' in topic):
                        is_sensitive = True
                        
                    if is_sensitive:
                        continue
                        
                    suggestions.append({"category": category, "topic": topic})
                    seen.add(topic)
                    if len(suggestions) >= limit:
                        return suggestions
        
        # 如果还是不够，使用默认话题
        if len(suggestions) < limit:
            default_topics = self._get_default_topics(limit - len(suggestions))
            suggestions.extend(default_topics)
            
        return suggestions[:limit]
    
    def _get_default_topics(self, limit: int) -> List[Dict[str, str]]:
        """获取默认安全话题"""
        default_topics = [
            {"topic": "今天心情怎么样", "category": "日常互动"},
            {"topic": "最近在看什么剧", "category": "娱乐分享"},
            {"topic": "喜欢什么类型的音乐", "category": "兴趣爱好"},
            {"topic": "有什么推荐的美食", "category": "美食分享"},
            {"topic": "周末一般做什么", "category": "生活方式"},
            {"topic": "最想去的旅行地点", "category": "旅行话题"},
            {"topic": "有什么有趣的爱好", "category": "兴趣交流"},
            {"topic": "最近学了什么新技能", "category": "学习成长"},
            {"topic": "喜欢什么运动", "category": "运动健康"},
            {"topic": "推荐一本好书", "category": "阅读分享"}
        ]
        return default_topics[:limit]

    def candidate_terms(self, *, min_len: int = 2, max_len: int = 6) -> List[str]:
        """Return Chinese terms for downstream phonetic correction."""
        if not self._index:
            return []
        chinese = re.compile(r"[\u4e00-\u9fa5]")
        terms: set[str] = set()
        for entry in self._index:
            tokens = entry.get("tokens", set())
            for token in tokens:
                if not isinstance(token, str):
                    continue
                if len(token) < min_len or len(token) > max_len:
                    continue
                if not chinese.search(token):
                    continue
                terms.add(token)
            tags = entry.get("tags", set())
            for tag in tags:
                if not isinstance(tag, str):
                    continue
                if len(tag) < min_len or len(tag) > max_len:
                    continue
                if not chinese.search(tag):
                    continue
                terms.add(tag)
        for _, topic in self._topic_entries:
            if not topic:
                continue
            if len(topic) < min_len or len(topic) > max_len:
                continue
            if not chinese.search(topic):
                continue
            terms.add(topic)
        return sorted(terms)


@functools.lru_cache(maxsize=1)
def get_knowledge_base() -> KnowledgeBase:
    """Return a cached knowledge base instance."""

    return KnowledgeBase()


def preview_snippets(snippets: Iterable[KnowledgeSnippet]) -> str:
    blocks = [snippet.to_prompt_block() for snippet in snippets]
    return "\n\n".join(blocks)
