#!/usr/bin/env python3
"""
快速测试AI工作流输出效果
"""

import os
import sys
import time
import json
from pathlib import Path

# 添加项目根目录到路径
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
            {"type": "chat", "content": "质量好不好？", "user": "用户D"},
            {"type": "chat", "content": "什么时候发货？", "user": "用户E"},
        ],
        "user_scores": {},
    }

# 创建测试画像
def create_profile(anchor_id: str, memory_root: Path):
    profile_dir = memory_root / anchor_id
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_file = profile_dir / "profile.json"
    profile_data = {
        "tone": "专业陪伴",
        "taboo": ["垃圾", "有病", "骗子"],
        "style": "温暖专业",
        "personality": "亲和力强，专业度高"
    }
    with open(profile_file, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=2)

print("=" * 70)
print("  AI工作流输出效果展示")
print("=" * 70)
print()

# 初始化
memory_root = Path("/tmp/test_ai_workflow_memory")
memory_root.mkdir(parents=True, exist_ok=True)
create_profile("test_anchor_001", memory_root)

config = LiveWorkflowConfig(
    anchor_id="test_anchor_001",
    memory_root=memory_root
)

analysis_generator = LiveAnalysisGenerator({})
question_responder = LiveQuestionResponder({})

workflow = LangGraphLiveWorkflow(
    analysis_generator=analysis_generator,
    question_responder=question_responder,
    config=config
)

test_state = create_test_state()

print("🚀 开始执行工作流...")
print(f"   输入句子: {len(test_state['sentences'])}条")
print(f"   输入弹幕: {len(test_state['comments'])}条")
print()

start_time = time.time()
result = workflow.invoke(test_state)
execution_time = time.time() - start_time

print(f"✅ 工作流执行完成，耗时: {execution_time:.2f}秒")
print()
print("=" * 70)
print("  AI生成结果详情")
print("=" * 70)
print()

# 1. 分析卡片
if "analysis_card" in result:
    print("📊 分析卡片 (analysis_card):")
    print(json.dumps(result["analysis_card"], ensure_ascii=False, indent=2))
    print()

# 2. 摘要
if "summary" in result:
    print("📝 摘要 (summary):")
    print(result["summary"])
    print()

# 3. 氛围
if "vibe" in result:
    print("🌊 氛围分析 (vibe):")
    print(json.dumps(result["vibe"], ensure_ascii=False, indent=2))
    print()

# 4. 分析焦点
if "analysis_focus" in result:
    print("🎯 分析焦点 (analysis_focus):")
    print(result["analysis_focus"])
    print()

# 5. 主播画像
if "persona" in result:
    print("👤 主播画像 (persona):")
    print(json.dumps(result["persona"], ensure_ascii=False, indent=2))
    print()

# 6. 弹幕信号（前3条）
if "chat_signals" in result and result["chat_signals"]:
    print(f"💭 弹幕信号 (chat_signals) - 前3条:")
    for i, signal in enumerate(result["chat_signals"][:3], 1):
        print(f"  {i}. {json.dumps(signal, ensure_ascii=False)}")
    print()

# 7. 风格画像
if "style_profile" in result:
    print("🎨 风格画像 (style_profile):")
    print(json.dumps(result["style_profile"], ensure_ascii=False, indent=2))
    print()
else:
    print("⚠️  style_profile 字段缺失")
    print()

# 8. 话题
if "topics" in result:
    print("💬 话题检测 (topics):")
    print(json.dumps(result["topics"], ensure_ascii=False, indent=2))
    print()
else:
    print("⚠️  topics 字段缺失")
    print()

# 9. 话术脚本
if "scripts" in result and result["scripts"]:
    print(f"📜 话术脚本 (scripts) - 共{len(result['scripts'])}条:")
    for i, script in enumerate(result["scripts"][:3], 1):
        print(f"\n  脚本 {i}:")
        print(json.dumps(script, ensure_ascii=False, indent=4))
    print()

# 保存完整结果
output_file = "/tmp/test_ai_workflow_result.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"💾 完整结果已保存到: {output_file}")

