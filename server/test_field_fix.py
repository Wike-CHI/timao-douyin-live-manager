#!/usr/bin/env python3
"""
快速验证字段修复
"""

import os
import sys
import time
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]
    load_dotenv(project_root / ".env")
except ImportError:
    pass

from ai.langgraph_live_workflow import LangGraphLiveWorkflow, LiveWorkflowConfig
from ai.live_analysis_generator import LiveAnalysisGenerator
from ai.live_question_responder import LiveQuestionResponder

def create_test_state():
    return {
        "anchor_id": "test_anchor_001",
        "broadcaster_id": "test_anchor_001",
        "window_start": time.time(),
        "sentences": [
            "大家好，欢迎来到直播间",
            "今天给大家推荐一款非常好用的产品",
            "这个产品性价比很高，大家可以看看",
        ],
        "comments": [
            {"type": "chat", "content": "这个产品怎么样？", "user": "用户A"},
            {"type": "chat", "content": "价格是多少？", "user": "用户B"},
        ],
        "user_scores": {},
    }

def create_profile(anchor_id: str, memory_root: Path):
    profile_dir = memory_root / anchor_id
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_file = profile_dir / "profile.json"
    profile_data = {"tone": "专业陪伴", "taboo": []}
    with open(profile_file, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=2)

print("=" * 70)
print("  字段修复验证")
print("=" * 70)

memory_root = Path("/tmp/test_ai_workflow_memory")
memory_root.mkdir(parents=True, exist_ok=True)
create_profile("test_anchor_001", memory_root)

config = LiveWorkflowConfig(anchor_id="test_anchor_001", memory_root=memory_root)
workflow = LangGraphLiveWorkflow(
    analysis_generator=LiveAnalysisGenerator({}),
    question_responder=None,  # 不使用问题响应器，加快测试
    config=config
)

test_state = create_test_state()

print("\n执行工作流（简化版，不包含question_responder）...")
start = time.time()
result = workflow.invoke(test_state)
elapsed = time.time() - start

print(f"\n✅ 工作流执行完成，耗时: {elapsed:.2f}秒\n")

# 检查字段
print("字段检查:")
required_fields = {
    "topics": "话题列表",
    "style_profile": "风格画像",
    "persona": "主播画像",
    "chat_signals": "弹幕信号",
    "vibe": "氛围分析",
    "analysis_card": "分析卡片",
    "summary": "摘要",
}

all_present = True
for field, desc in required_fields.items():
    if field in result:
        value = result[field]
        if isinstance(value, dict):
            print(f"  ✅ {field} ({desc}): dict, 键数={len(value)}")
        elif isinstance(value, list):
            print(f"  ✅ {field} ({desc}): list, 长度={len(value)}")
        elif isinstance(value, str):
            print(f"  ✅ {field} ({desc}): str, 长度={len(value)}")
        else:
            print(f"  ✅ {field} ({desc}): {type(value).__name__}")
    else:
        print(f"  ❌ {field} ({desc}): 缺失")
        all_present = False

if all_present:
    print("\n✅ 所有必需字段都存在！")
else:
    print("\n⚠️  部分字段缺失")

# 显示部分内容
if "topics" in result and result["topics"]:
    print(f"\n📋 topics 示例: {result['topics'][:2]}")
if "style_profile" in result and result["style_profile"]:
    print(f"\n🎨 style_profile 键: {list(result['style_profile'].keys())[:5]}")

