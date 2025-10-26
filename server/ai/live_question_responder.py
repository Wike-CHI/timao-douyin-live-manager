"""
Live question responder for generating host-style scripts that answer
unresolved audience questions in real time.

This module uses a Qwen3-Max compatible endpoint via the OpenAI SDK.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# 使用统一网关
from .ai_gateway import get_gateway
from .knowledge_service import get_knowledge_base, preview_snippets

logger = logging.getLogger(__name__)


class LiveQuestionResponder:
    """Generate short, host-style answer scripts via AI Gateway."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.gateway = get_gateway()
        self.model: str = config.get("ai_model", "qwen-plus")
        self._examples_cache: Optional[str] = None
        logger.info("LiveQuestionResponder initialized with AI Gateway.")

    def _build_prompt(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        persona = context.get("persona") or {}
        vibe = context.get("vibe") or {}
        questions = context.get("questions") or []
        transcript = context.get("transcript") or ""
        max_items = min(3, len(questions))
        persona_notes = ""
        if persona:
            persona_notes = (
                "【主播风格画像】\n"
                + json.dumps(persona, ensure_ascii=False)
                + "\n\n"
            )
        vibe_line = (
            f"level={vibe.get('level', 'unknown')}, "
            f"score={vibe.get('score', 'N/A')}, "
            f"mood={context.get('mood', 'unknown')}"
        )
        knowledge_block = self._prepare_knowledge_block(context)
        samples_block = self._load_examples()
        system_prompt = (
            "你是主播的实时语音助理，需要用主播自己的口吻回答观众的难题或疑问。"
            "必须保持第一人称口语，语气、节奏、遣词贴近主播平时的习惯，同时可以做细微风格调整。"
            "每条话术 18~32 个汉字，避免模板化称呼、夸张宣传或敏感内容，更不能出现“垃圾”“有病”等攻击性词语。"
            "请将【知识库补充】与现场线索权重相当；只有在问题明确涉及当季/衣物等主题时，适度参考，不要过度重复或强行带入单一主题。"
            "输出为 JSON 数组，每个对象包含："
            '{"question":"原始问题","line":"主播可直接说的话","style":"暖心|直接|可爱|幽默|小调侃","notes":"可选解释"}。'
            "每个问题必须返回 3 条不重复的话术，依次满足：第 1 条是“暖心”风格，贴心且落地；第 2 条可选择“直接”或“可爱”，讲清观察到的问题；第 3 条可以是“幽默”或“小调侃”，但要带着笑点不带刺，像朋友打趣，避免过度讽刺或奇怪比喻。"
            "如问题信息不足，line 中要自然说明需要更多信息。"
        )
        user_prompt = (
            f"{persona_notes}"
            "【待解答的问题（按优先级排序）】\n"
            + "\n".join([f"{idx+1}. {q}" for idx, q in enumerate(questions[:max_items])])
            + "\n\n"
            "【当前氛围与节奏】\n"
            f"{vibe_line}\n\n"
            f"{knowledge_block}"
            "【近期口播节选】\n"
            f"{transcript or '（暂无口播文本，仅参考历史画像）'}\n\n"
            f"{samples_block}\n\n"
            "请针对问题逐条给出主播能直接上嘴的话术，严格贴合上述风格。"
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _parse_response_payload(self, raw: str) -> List[Dict[str, Any]]:
        """Best-effort parsing of the model JSON output."""
        raw = (raw or "").strip()
        if not raw:
            return []
        parsed = self._load_json_safely(raw)
        if parsed is None:
            parsed = self._recover_partial_array(raw)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        if isinstance(parsed, dict):
            for key in ("items", "scripts", "data"):
                value = parsed.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        return []

    def _load_json_safely(self, raw: str) -> Optional[Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("无法解析 Qwen 返回的 JSON，执行容错解析：%s", raw[:200])
            return None

    def _recover_partial_array(self, raw: str) -> List[Dict[str, Any]]:
        text = raw.lstrip()
        if not text.startswith("["):
            return []
        decoder = json.JSONDecoder()
        idx = 1
        length = len(text)
        items: List[Dict[str, Any]] = []
        while idx < length:
            # Skip whitespace or commas between objects
            while idx < length and text[idx] in " \t\r\n,":
                idx += 1
            if idx >= length or text[idx] == "]":
                break
            try:
                obj, next_idx = decoder.raw_decode(text, idx)
            except json.JSONDecodeError:
                break
            if isinstance(obj, dict):
                items.append(obj)
            idx = next_idx
        if items:
            logger.warning(
                "Qwen 返回的 JSON 可能被截断，仅恢复 %d 条话术。", len(items)
            )
        return items

    def generate(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        questions = context.get("questions") or []
        if not questions:
            return []
        
        messages = self._build_prompt(context)
        
        # 使用网关调用
        response = self.gateway.chat_completion(
            messages=messages,
            model=self.model,
            temperature=0.4,
            response_format={"type": "json_object"},
            max_tokens=900,
        )
        
        if not response.success:
            logger.error(f"AI调用失败: {response.error}")
            return []
        
        data = self._parse_response_payload(response.content)
        if not data:
            logger.warning(
                "智能话术生成返回为空，已尝试容错处理但未能恢复有效话术。原始片段：%s",
                response.content[:200],
            )
            return []
        scripts: List[Dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            line = str(item.get("line") or "").strip()
            question = str(item.get("question") or "").strip()
            if not line:
                continue
            style_raw = str(item.get("style") or "").strip()
            style_map = {
                "暖心": "warm",
                "warm": "warm",
                "直接": "direct",
                "direct": "direct",
                "可爱": "cute",
                "cute": "cute",
                "幽默": "humor",
                "humor": "humor",
                "小调侃": "tease",
                "调侃": "tease",
                "tease": "tease",
            }
            style = style_map.get(style_raw, "direct")
            scripts.append(
                {
                    "line": line,
                    "question": question,
                    "notes": str(item.get("notes") or "").strip(),
                    "style": style,
                }
            )
        if not scripts:
            return []

        ordered: List[Dict[str, Any]] = []
        style_groups = [
            ("warm", {"warm"}),
            ("direct_or_cute", {"direct", "cute"}),
            ("humor_or_tease", {"humor", "tease"}),
        ]
        used_idx: set[int] = set()
        for _, targets in style_groups:
            chosen_idx = None
            for idx, item in enumerate(scripts):
                if idx in used_idx:
                    continue
                if item["style"] in targets:
                    chosen_idx = idx
                    break
            if chosen_idx is not None:
                ordered.append(scripts[chosen_idx])
                used_idx.add(chosen_idx)

        # 如果缺项，用剩余话术补齐
        if len(ordered) < 3:
            for idx, item in enumerate(scripts):
                if idx in used_idx:
                    continue
                ordered.append(item)
                if len(ordered) >= 3:
                    break

        return ordered[:3]

    def _load_examples(self) -> str:
        if self._examples_cache is not None:
            return self._examples_cache
        base_dir = Path(__file__).resolve().parents[2]
        dataset_dir = base_dir / "docs" / "娱乐主播高情商话术大全"
        snippets: List[str] = []
        if dataset_dir.is_dir():
            text_files = sorted(dataset_dir.rglob("*.txt"))
            for path in text_files:
                try:
                    if not path.is_file():
                        continue
                    content = path.read_text("utf-8", errors="ignore")
                except Exception:
                    continue
                file_snippets = [
                    line.strip()
                    for line in content.splitlines()
                    if 6 <= len(line.strip()) <= 30
                ][:3]
                if file_snippets:
                    snippets.extend(file_snippets)
                if len(snippets) >= 18:
                    break
        if snippets:
            unique_snippets: List[str] = []
            seen = set()
            for snippet in snippets:
                if snippet and snippet not in seen:
                    unique_snippets.append(snippet)
                    seen.add(snippet)
                    if len(unique_snippets) >= 18:
                        break
            block = "【高情商话术示例】\n" + "\n".join(unique_snippets)
            self._examples_cache = block
            return block
        self._examples_cache = "【高情商话术示例】\n结婚？别闹，我才18 岁还在念书呢~"
        return self._examples_cache

    def _prepare_knowledge_block(self, context: Dict[str, Any]) -> str:
        try:
            kb = get_knowledge_base()
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("知识库初始化失败，继续使用默认示例：%s", exc)
            return ""

        def _extract_terms(text: Optional[str]) -> List[str]:
            if not text:
                return []
            return [term for term in re.findall(r"[\u4e00-\u9fa5]{2,}", str(text)) if term]

        questions = context.get("questions") or []
        persona = context.get("persona") or {}
        vibe = context.get("vibe") or {}
        queries: List[str] = []
        for q in questions:
            queries.extend(_extract_terms(q))
        transcript_terms = _extract_terms(context.get("transcript") if context.get("transcript") else "")
        if transcript_terms:
            queries.extend(transcript_terms[:5])
        if persona_name := persona.get("name"):
            queries.extend(_extract_terms(persona_name))
        if vibe_level := vibe.get("level"):
            queries.append(str(vibe_level))

        if vibe.get("level") == "cold":
            queries.extend(["冷场", "打招呼", "破冰", "互动"])
        elif vibe.get("level") == "hot":
            queries.extend(["控场", "节奏", "转化"])

        seen_terms = set()
        dedup_queries: List[str] = []
        for term in queries:
            if term and term not in seen_terms:
                dedup_queries.append(term)
                seen_terms.add(term)
        queries = dedup_queries or ["直播话术", "互动"]

        snippets = kb.query(
            queries,
            themes=[persona.get("style")] if persona.get("style") else None,
            tags=[vibe.get("level")] if vibe.get("level") else None,
            limit=2,
        )
        if not snippets:
            return ""
        preview = preview_snippets(snippets)
        return f"【知识库补充】\n{preview}\n\n"
