"""
Style profile summariser: condense ASR transcripts into long-term style memory.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from openai import OpenAI

try:
    from .qwen_openai_compatible import (
        DEFAULT_OPENAI_API_KEY,
        DEFAULT_OPENAI_BASE_URL,
        DEFAULT_OPENAI_MODEL,
    )
except Exception:  # pragma: no cover - fallback defaults
    DEFAULT_OPENAI_API_KEY = os.getenv("AI_API_KEY", "")
    DEFAULT_OPENAI_BASE_URL = os.getenv("AI_BASE_URL", "")
    DEFAULT_OPENAI_MODEL = os.getenv("AI_MODEL", "qwen-plus")

logger = logging.getLogger(__name__)


@dataclass
class StyleProfileBuilderConfig:
    api_key: str
    base_url: str
    model: str
    max_chars: int = 8000
    min_tokens: int = 200


class StyleProfileBuilder:
    """Use Qwen3-Max to derive a stable style profile from ASR transcripts."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        cfg = StyleProfileBuilderConfig(
            api_key=api_key or os.getenv("AI_API_KEY", "") or DEFAULT_OPENAI_API_KEY,
            base_url=base_url or os.getenv("AI_BASE_URL", "") or DEFAULT_OPENAI_BASE_URL,
            model=model or os.getenv("AI_MODEL", "") or DEFAULT_OPENAI_MODEL,
        )
        if not cfg.api_key:
            raise RuntimeError("StyleProfileBuilder 初始化失败：未配置 AI_API_KEY")
        self.config = cfg
        self.client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url or None)

    def build_profile(
        self,
        anchor_id: Optional[str],
        transcript: str,
        session_date: str,
        session_index: int,
    ) -> Dict[str, Any]:
        """Summarise ASR transcript into structured style guidance."""
        excerpt = transcript.strip()
        if not excerpt:
            return {}
        if len(excerpt) > self.config.max_chars:
            excerpt = excerpt[: self.config.max_chars]
        prompt = self._build_prompt(anchor_id, session_date, session_index, excerpt)
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=prompt,
            max_tokens=800,
            temperature=0.4,
        )
        raw = response.choices[0].message.content.strip()
        summary = self._parse_json(raw)
        profile = summary.get("style_profile")
        if not isinstance(profile, dict):
            profile = {
                "persona": summary.get("persona"),
                "tone": summary.get("tone"),
                "tempo": summary.get("tempo"),
                "register": summary.get("register"),
                "catchphrases": summary.get("catchphrases"),
                "slang": summary.get("slang"),
                "signature_openers": summary.get("signature_openers"),
                "signature_closings": summary.get("signature_closings"),
                "vocal_traits": summary.get("vocal_traits"),
            }
            summary["style_profile"] = profile
        guidelines = summary.get("style_guidelines")
        if isinstance(guidelines, dict):
            dos = guidelines.get("dos")
            donts = guidelines.get("donts")
            if isinstance(dos, list):
                summary.setdefault("highlight_points", [])
                summary["highlight_points"].extend(dos)
                summary.setdefault("suggestions", [])
                summary["suggestions"].extend(dos)
            if isinstance(donts, list):
                summary.setdefault("risks", [])
                summary["risks"].extend(donts)
        if not isinstance(summary.get("suggestions"), list):
            summary["suggestions"] = []
        self._dedupe_and_limit(summary)
        summary.setdefault("session", {})
        summary["session"].update(
            {
                "date": session_date,
                "index": int(session_index),
                "anchor": anchor_id or "",
            }
        )
        return summary

    def _build_prompt(
        self,
        anchor_id: Optional[str],
        session_date: str,
        session_index: int,
        excerpt: str,
    ) -> list[Dict[str, Any]]:
        system = (
            "你是一名直播内容分析师，负责从主播的口播里学习其语言风格与习惯。"
            "请只输出一个 JSON，结构必须为：\n"
            "{\n"
            '  "style_profile": {\n'
            '    "persona": "", "tone": "", "tempo": "", "register": "",\n'
            '    "catchphrases": [], "slang": [], "signature_openers": [],\n'
            '    "signature_closings": [], "vocal_traits": []\n'
            "  },\n"
            '  "style_guidelines": {"dos": [], "donts": []},\n'
            '  "highlight_points": [],\n'
            '  "suggestions": [],\n'
            '  "style_insights": []\n'
            "}\n"
            "所有列表最多 6 条，元素为简短中文短语。若信息不足，也请根据语气和内容进行推断，不要留空数组。"
        )
        user = (
            f"【主播】{anchor_id or 'unknown'}\n"
            f"【日期】{session_date} 第 {session_index} 场\n"
            "【口播转写节选】\n"
            f"{excerpt}"
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def _parse_json(self, payload: str) -> Dict[str, Any]:
        try:
            candidate = payload.strip()
            start = candidate.find("{")
            end = candidate.rfind("}")
            if start != -1 and end != -1:
                candidate = candidate[start : end + 1]
            data = json.loads(candidate)
            if not isinstance(data, dict):
                raise ValueError("响应非对象类型")
            return data
        except Exception as exc:
            logger.warning("Failed to parse style summary JSON: %s", payload)
            raise RuntimeError("Qwen 样式总结解析失败") from exc

    def _dedupe_and_limit(self, summary: Dict[str, Any], limit: int = 6) -> None:
        for key in ("highlight_points", "risks", "suggestions", "style_insights"):
            values = summary.get(key)
            if isinstance(values, list):
                unique: list[str] = []
                for item in values:
                    text = str(item).strip()
                    if not text or text in unique:
                        continue
                    unique.append(text)
                    if len(unique) >= limit:
                        break
                summary[key] = unique
        profile = summary.get("style_profile")
        if isinstance(profile, dict):
            for field in ("catchphrases", "slang", "signature_openers", "signature_closings", "vocal_traits"):
                values = profile.get(field)
                if isinstance(values, list):
                    dedup: list[str] = []
                    for item in values:
                        text = str(item).strip()
                        if not text or text in dedup:
                            continue
                        dedup.append(text)
                        if len(dedup) >= limit:
                            break
                    profile[field] = dedup
