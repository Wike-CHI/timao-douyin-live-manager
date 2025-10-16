"""
Live question responder for generating host-style scripts that answer
unresolved audience questions in real time.

This module uses a Qwen3-Max compatible endpoint via the OpenAI SDK.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)


class LiveQuestionResponder:
    """Generate short, host-style answer scripts for open audience questions."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.client: Optional[OpenAI] = None
        self.model: str = config.get("ai_model", "qwen3-max")
        self._examples_cache: Optional[str] = None
        self._init_client()

    def _init_client(self) -> None:
        try:
            api_key = self.config.get("ai_api_key")
            base_url = self.config.get("ai_base_url")
            if not api_key:
                raise ValueError("缺少 AI API 密钥，无法生成智能话术")
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
            logger.info("LiveQuestionResponder initialized with Qwen endpoint.")
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to initialize LiveQuestionResponder: %s", exc)
            self.client = None

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
        samples_block = self._load_examples()
        system_prompt = (
            "你是主播的实时语音助理，需要用主播自己的口吻回答观众的难题或疑问。"
            "必须保持第一人称口语，语气、节奏、遣词贴近主播平时的习惯，同时可以根据需求做风格化发挥。"
            "每条话术 18~32 个汉字，避免模板化称呼、夸张宣传或敏感内容。"
            "输出为 JSON 数组，每个对象包含："
            '{"question":"原始问题","line":"主播可直接说的话","style":"humor|cute|tease|direct|warm","notes":"可选解释"}。'
            "请为每个问题给出 2~3 条不重复的风格变体，至少包括幽默(humor)或轻调侃(tease)在内的一条，以满足“反常规”的需求。"
            "如问题信息不足，line 中要自然说明需要更多信息。"
        )
        user_prompt = (
            f"{persona_notes}"
            "【待解答的问题（按优先级排序）】\n"
            + "\n".join([f"{idx+1}. {q}" for idx, q in enumerate(questions[:max_items])])
            + "\n\n"
            "【当前氛围与节奏】\n"
            f"{vibe_line}\n\n"
            "【近期口播节选】\n"
            f"{transcript or '（暂无口播文本，仅参考历史画像）'}\n\n"
            f"{samples_block}\n\n"
            "请针对问题逐条给出主播能直接上嘴的话术，严格贴合上述风格。"
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def generate(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.client:
            raise RuntimeError("LiveQuestionResponder 未初始化成功")
        questions = context.get("questions") or []
        if not questions:
            return []
        messages = self._build_prompt(context)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.4,
            response_format={"type": "json_object"},
            max_tokens=600,
        )
        raw = response.choices[0].message.content or "[]"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("无法解析 Qwen 返回的 JSON：%s", raw)
            return []
        if isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
            data = data["items"]
        if not isinstance(data, list):
            return []
        scripts: List[Dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            line = str(item.get("line") or "").strip()
            question = str(item.get("question") or "").strip()
            if not line:
                continue
            style = str(item.get("style") or "").strip().lower()
            if style not in {"humor", "cute", "tease", "direct", "warm"}:
                style = "direct"
            scripts.append(
                {
                    "line": line,
                    "question": question,
                    "notes": str(item.get("notes") or "").strip(),
                    "style": style,
                }
            )
        return scripts[:3]

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
