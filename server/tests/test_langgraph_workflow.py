import time
from pathlib import Path

import pytest

from server.ai.generator import AIScriptGenerator
from server.ai.langgraph_live_workflow import LiveWorkflowConfig, ensure_workflow


def test_workflow_generates_scripts_with_qwen(tmp_path: Path) -> None:
    cfg = {
        "ai_service": "qwen",
        "ai_api_key": "",
        "ai_base_url": "",
        "ai_model": "qwen-plus",
    }
    generator = AIScriptGenerator(cfg)
    if generator.client is None:
        pytest.skip("Qwen Max client unavailable in test environment")
    workflow = ensure_workflow(
        generator,
        LiveWorkflowConfig(anchor_id="unit_test_anchor", memory_root=tmp_path / "memory"),
    )

    result = workflow.invoke(
        {
            "anchor_id": "unit_test_anchor",
            "broadcaster_id": "unit_test_anchor",
            "window_start": time.time(),
            "sentences": ["今天聊互动问题", "等下抽奖别走开"],
            "comments": [
                {"type": "chat", "content": "怎么买才划算？"},
                {"type": "chat", "content": "有满减吗？"},
            ],
        }
    )
    scripts = result.get("scripts") or []
    assert isinstance(scripts, list)
    assert scripts, "workflow should return scripts when Qwen Max is available"
