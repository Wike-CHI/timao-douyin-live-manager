import unittest
import json
from typing import Any, Dict

from server.ai.live_analysis_generator import LiveAnalysisGenerator


class DummyAIResponse:
    def __init__(self, content: str, success: bool = True, model: str = "qwen3-max", provider: str = "qwen"):
        self.content = content
        self.success = success
        self.model = model
        self.provider = provider
        self.usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.cost = 0.0
        self.duration_ms = 0.0
        self.error = None if success else "error"


class DummyGateway:
    def __init__(self):
        self._next_response = None
        self.calls: Dict[str, int] = {}

    def set_response(self, resp: DummyAIResponse):
        self._next_response = resp

    def chat_completion(self, *_, **kwargs) -> DummyAIResponse:  # signature compatible subset
        func = kwargs.get("function") or "unknown"
        self.calls[func] = self.calls.get(func, 0) + 1
        if self._next_response is None:
            raise RuntimeError("No dummy response set")
        return self._next_response


class TestLiveAnalysisGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = LiveAnalysisGenerator(config={})
        # 替换真实 gateway 为 dummy，避免真实外部调用
        self.dummy_gateway = DummyGateway()
        self.generator.gateway = self.dummy_gateway  # type: ignore

        self.context: Dict[str, Any] = {
            "transcript": "主播刚刚分享了一个有趣的故事，大家反应热烈。",
            "chat_signals": [
                {"text": "哈哈哈太好笑了", "category": "emotion"},
                {"text": "讲的不错继续", "category": "support"},
            ],
            "topics": [{"topic": "故事与成长", "confidence": 0.85}],
            "chat_stats": {"total_messages": 20, "category_counts": {"emotion": 8, "support": 6, "other": 6}},
            "speech_stats": {"sentence_count": 12, "total_chars": 120},
            "vibe": {"level": "hot", "score": 0.9},
            "mood": "active",
            "persona": {"style": "幽默互动"},
            "lead_candidates": [{"user": "粉丝A", "text": "讲讲转折点", "reason": "高互动"}],
        }

    def test_generate_success_json(self):
        payload = {
            "analysis_overview": "节奏紧凑气氛活跃",
            "audience_sentiment": {"label": "热", "signals": ["弹幕密度提升"]},
            "engagement_highlights": ["弹幕密度高"],
            "risks": ["可能话题深度不足"],
            "next_actions": ["顺势追问观众亲身经历"],
            "next_topic_direction": "聊聊转折经历",
            "confidence": 0.82,
        }
        self.dummy_gateway.set_response(DummyAIResponse(json.dumps(payload)))
        result = self.generator.generate(self.context)
        self.assertIn("analysis_overview", result)
        self.assertEqual(result["analysis_overview"], payload["analysis_overview"])
        self.assertIn("audience_sentiment", result)
        self.assertAlmostEqual(result["confidence"], payload["confidence"], places=2)
        self.assertEqual(self.dummy_gateway.calls.get("live_analysis"), 1)

    def test_generate_parse_error_fallback(self):
        # 返回不可解析 JSON，需要走 fallback 逻辑
        invalid = "分析如下: 氛围热烈，互动多。"
        self.dummy_gateway.set_response(DummyAIResponse(invalid))
        result = self.generator.generate(self.context)
        self.assertIn("analysis_overview", result)
        # 解析失败时，返回包含提示文本（非严格 JSON 字段）
        self.assertTrue(len(result["analysis_overview"]) > 0)

    def test_generate_api_failure(self):
        # success=False 模拟网关失败（如 404）
        self.dummy_gateway.set_response(DummyAIResponse("", success=False))
        result = self.generator.generate(self.context)
        self.assertEqual(result.get("analysis_overview"), "生成失败，请稍后重试")

    def test_generate_minimal_context(self):
        # 缺少大部分上下文时仍应返回字段（健壮性）
        minimal_context = {"transcript": "简单一句话"}
        payload = {"analysis_overview": "信息不足", "audience_sentiment": {"label": "平稳", "signals": []}, "engagement_highlights": [], "risks": [], "next_actions": [], "next_topic_direction": "继续互动", "confidence": 0.3}
        self.dummy_gateway.set_response(DummyAIResponse(json.dumps(payload)))
        result = self.generator.generate(minimal_context)
        self.assertIn("analysis_overview", result)
        self.assertEqual(result["audience_sentiment"]["label"], "平稳")


if __name__ == "__main__":
    unittest.main()
