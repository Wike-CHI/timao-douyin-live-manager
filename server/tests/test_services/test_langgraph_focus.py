import pytest

from server.ai.langgraph_live_workflow import (
    LangGraphLiveWorkflow,
    LiveWorkflowConfig,
)


class _StubGenerator:
    def generate(self, context):
        return context.get("analysis_card", {}) or {}


class _StubSummarizer:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def summarize(self, **kwargs):
        self.calls += 1
        return self.result


@pytest.mark.parametrize(
    "ai_focus,expected_focus",
    [
        ("夏日穿搭分享", "夏日穿搭分享"),
        ("ue3f", "好物推荐"),
    ],
)
def test_summary_uses_clean_chat_focus(ai_focus: str, expected_focus: str):
    summarizer = _StubSummarizer(ai_focus)
    workflow = LangGraphLiveWorkflow(
        analysis_generator=_StubGenerator(),
        question_responder=None,
        config=LiveWorkflowConfig(enable_chat_focus_ai=True),
        chat_focus_summarizer=summarizer,
    )

    state = {
        "analysis_card": {
            "analysis_overview": "直播热度不错，观众反馈积极",
            "engagement_highlights": [],
            "risks": [],
            "next_actions": [],
            "next_topic_direction": "夏日新款",
        },
        "planner_notes": {
            "selected_topic": {"topic": "好物推荐"},
            "lead_candidates": [],
            "speech_stats": {
                "sentence_count": 3,
                "speaking_ratio": 0.5,
                "other_like_ratio": 0.1,
                "host_like_ratio": 0.8,
            },
        },
        "speech_stats": {
            "sentence_count": 3,
            "speaking_ratio": 0.5,
            "other_like_ratio": 0.1,
            "host_like_ratio": 0.8,
        },
        "chat_signals": [
            {"text": "想看夏日穿搭呀", "category": "chat", "weight": 1.0},
            {"text": "好物推荐还有吗", "category": "chat", "weight": 1.0},
        ],
        "vibe": {"level": "hot", "score": 78},
        "analysis_focus": "测试聚焦",
    }

    result = workflow._summary_node(state)

    assert result["chat_focus"] == expected_focus
    assert f"大家此刻主要在聊{expected_focus}" in result["summary"]
    assert summarizer.calls == 1
