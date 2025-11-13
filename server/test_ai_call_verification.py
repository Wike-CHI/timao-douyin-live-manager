#!/usr/bin/env python3
"""
验证AI工作流是否真实调用AI
"""

import os
import sys
import time
import json
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]
    load_dotenv(project_root / ".env")
except ImportError:
    pass

from ai.ai_gateway import get_gateway
from ai.langgraph_live_workflow import LangGraphLiveWorkflow, LiveWorkflowConfig
from ai.live_analysis_generator import LiveAnalysisGenerator
from ai.live_question_responder import LiveQuestionResponder

# 创建测试数据
def create_test_state():
    return {
        "anchor_id": "test_anchor_001",
        "broadcaster_id": "test_anchor_001",
        "window_start": time.time(),
        "sentences": [
            "大家好，欢迎来到直播间",
            "今天给大家推荐一款非常好用的产品",
            "这个产品性价比很高，大家可以看看",
            "有什么问题可以在弹幕里问我",
            "等下会有抽奖活动，大家不要走开"
        ],
        "comments": [
            {"type": "chat", "content": "这个产品怎么样？", "user": "用户A"},
            {"type": "chat", "content": "价格是多少？", "user": "用户B"},
            {"type": "chat", "content": "有优惠吗？", "user": "用户C"},
        ],
        "user_scores": {},
    }

def create_profile(anchor_id: str, memory_root: Path):
    profile_dir = memory_root / anchor_id
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_file = profile_dir / "profile.json"
    profile_data = {
        "tone": "专业陪伴",
        "taboo": ["垃圾", "有病", "骗子"],
    }
    with open(profile_file, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=2)

print("=" * 70)
print("  AI调用验证测试")
print("=" * 70)
print()

# 1. 验证AI Gateway
print("1. 验证AI Gateway...")
gateway = get_gateway()
providers = gateway.list_providers()
print(f"   已注册提供商: {list(providers.keys())}")

if "xunfei" in providers:
    xunfei_info = providers["xunfei"]
    print(f"   xunfei状态: 启用={xunfei_info.get('enabled')}, 模型={xunfei_info.get('default_model')}")
    
    # 测试直接调用
    print("\n2. 测试AI Gateway直接调用...")
    test_messages = [{"role": "user", "content": "请回复：测试成功"}]
    start = time.time()
    response = gateway.chat_completion(messages=test_messages, provider="xunfei", model="lite")
    elapsed = time.time() - start
    
    print(f"   响应时间: {elapsed:.2f}秒")
    print(f"   成功: {response.success}")
    if response.success:
        print(f"   响应内容: {response.content[:100]}")
        print(f"   ✅ AI Gateway真实调用成功")
    else:
        print(f"   ❌ AI Gateway调用失败: {response.error}")
        sys.exit(1)
else:
    print("   ❌ xunfei提供商未注册")
    sys.exit(1)

# 3. 验证LiveAnalysisGenerator
print("\n3. 验证LiveAnalysisGenerator...")
analysis_gen = LiveAnalysisGenerator({})

# 创建测试上下文
test_context = {
    "transcript": "大家好，欢迎来到直播间。今天给大家推荐一款非常好用的产品。",
    "chat_signals": [
        {"text": "这个产品怎么样？", "weight": 0.9, "category": "question"},
        {"text": "价格是多少？", "weight": 0.85, "category": "question"},
    ],
    "chat_stats": {"total_messages": 2, "category_counts": {"question": 2}},
    "speech_stats": {"sentence_count": 2, "total_chars": 30},
    "topics": [{"topic": "产品", "confidence": 0.8}],
    "vibe": {"level": "cold", "score": 36.4},
    "persona": {"tone": "专业陪伴"},
    "planner_focus": "重点观察观众提问",
}

print("   调用generate方法...")
start = time.time()
result = analysis_gen.generate(test_context)
elapsed = time.time() - start

print(f"   响应时间: {elapsed:.2f}秒")
print(f"   结果类型: {type(result)}")
if isinstance(result, dict):
    print(f"   结果键: {list(result.keys())}")
    if "analysis_overview" in result:
        print(f"   analysis_overview: {result['analysis_overview'][:100]}")
        if result['analysis_overview'] == "生成失败，请稍后重试":
            print("   ⚠️  警告：返回了错误消息，可能AI调用失败")
        else:
            print("   ✅ LiveAnalysisGenerator真实调用AI成功")
    else:
        print("   ⚠️  警告：结果中没有analysis_overview字段")
else:
    print(f"   ❌ 结果格式错误: {result}")

# 4. 验证工作流中的AI调用
print("\n4. 验证工作流中的AI调用...")
memory_root = Path("/tmp/test_ai_workflow_memory")
memory_root.mkdir(parents=True, exist_ok=True)
create_profile("test_anchor_001", memory_root)

config = LiveWorkflowConfig(anchor_id="test_anchor_001", memory_root=memory_root)
workflow = LangGraphLiveWorkflow(
    analysis_generator=LiveAnalysisGenerator({}),
    question_responder=LiveQuestionResponder({}),
    config=config
)

test_state = create_test_state()
print("   执行工作流（只执行到analysis_generator节点）...")
print("   注意：这将进行真实的AI调用，可能需要30-50秒...")

start = time.time()
result = workflow.invoke(test_state)
elapsed = time.time() - start

print(f"   工作流执行时间: {elapsed:.2f}秒")
if "analysis_card" in result:
    analysis_card = result["analysis_card"]
    if isinstance(analysis_card, dict) and "analysis_overview" in analysis_card:
        overview = analysis_card["analysis_overview"]
        print(f"   analysis_overview: {overview[:100]}")
        if overview == "生成失败，请稍后重试":
            print("   ❌ 工作流中AI调用失败")
        elif len(overview) > 20:
            print("   ✅ 工作流中AI调用成功，生成了详细内容")
        else:
            print("   ⚠️  工作流返回了简短内容，可能是回退结果")
    else:
        print("   ⚠️  分析卡片格式异常")
else:
    print("   ❌ 工作流结果中没有analysis_card")

print("\n" + "=" * 70)
print("  验证完成")
print("=" * 70)

