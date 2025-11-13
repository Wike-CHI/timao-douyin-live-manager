#!/usr/bin/env python3
"""
AI工作流功能测试脚本

测试AI Gateway下的AI工作流功能，包括：
1. 工作流初始化
2. 完整工作流执行（所有节点）
3. 工作流输出验证
4. AI Gateway集成测试
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]
    load_dotenv(project_root / ".env")
except ImportError:
    print("⚠️  dotenv未安装，跳过环境变量加载")

# 导入AI相关模块
try:
    from ai.ai_gateway import get_gateway
    from ai.langgraph_live_workflow import LangGraphLiveWorkflow, LiveWorkflowConfig
    from ai.live_analysis_generator import LiveAnalysisGenerator
    from ai.live_question_responder import LiveQuestionResponder
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保在server目录下运行此脚本")
    sys.exit(1)


# ==================== 工具函数 ====================

def print_section(title: str):
    """打印测试章节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_success(message: str):
    """打印成功消息"""
    print(f"✅ {message}")


def print_error(message: str):
    """打印错误消息"""
    print(f"❌ {message}")


def print_info(message: str):
    """打印信息消息"""
    print(f"ℹ️  {message}")


def print_warning(message: str):
    """打印警告消息"""
    print(f"⚠️  {message}")


# ==================== 测试数据准备 ====================

def create_test_state() -> Dict[str, Any]:
    """创建测试用的工作流状态"""
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


def create_test_memory_profile(anchor_id: str, memory_root: Path) -> None:
    """创建测试用的主播画像文件"""
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
    
    print_info(f"已创建测试画像文件: {profile_file}")


# ==================== 测试函数 ====================

def test_ai_gateway() -> bool:
    """测试1: AI Gateway初始化"""
    print_section("测试1: AI Gateway初始化")
    
    try:
        gateway = get_gateway()
        print_success("AI Gateway实例获取成功")
        
        # 检查当前配置
        current_config = gateway.get_current_config()
        if "error" not in current_config:
            print_info(f"当前提供商: {current_config.get('provider', 'N/A')}")
            print_info(f"当前模型: {current_config.get('model', 'N/A')}")
        else:
            print_warning(f"当前配置: {current_config.get('error', 'N/A')}")
        
        # 检查已注册的提供商
        providers = gateway.list_providers()
        print_info(f"已注册提供商: {list(providers.keys())}")
        
        # 检查xunfei提供商状态
        if "xunfei" in providers:
            xunfei_info = providers["xunfei"]
            print_success("xunfei提供商已注册")
            print_info(f"  启用状态: {xunfei_info.get('enabled', False)}")
            print_info(f"  默认模型: {xunfei_info.get('default_model', 'N/A')}")
            print_info(f"  支持模型: {xunfei_info.get('models', [])}")
        else:
            print_warning("xunfei提供商未注册")
        
        return True
    except Exception as e:
        print_error(f"AI Gateway初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_initialization() -> bool:
    """测试2: 工作流初始化"""
    print_section("测试2: 工作流初始化")
    
    try:
        # 创建临时内存目录
        memory_root = Path("/tmp/test_ai_workflow_memory")
        memory_root.mkdir(parents=True, exist_ok=True)
        
        # 创建测试画像
        create_test_memory_profile("test_anchor_001", memory_root)
        
        # 初始化配置
        config = LiveWorkflowConfig(
            anchor_id="test_anchor_001",
            memory_root=memory_root
        )
        
        # 初始化生成器
        analysis_config = {}
        analysis_generator = LiveAnalysisGenerator(analysis_config)
        print_success("LiveAnalysisGenerator初始化成功")
        
        question_config = {}
        question_responder = LiveQuestionResponder(question_config)
        print_success("LiveQuestionResponder初始化成功")
        
        # 创建工作流
        workflow = LangGraphLiveWorkflow(
            analysis_generator=analysis_generator,
            question_responder=question_responder,
            config=config
        )
        print_success("LangGraphLiveWorkflow初始化成功")
        
        # 检查工作流是否可用
        if workflow._workflow is None:
            print_warning("LangGraph不可用，将使用顺序回退模式")
        else:
            print_success("LangGraph工作流已编译")
        
        return True
    except Exception as e:
        print_error(f"工作流初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_execution() -> bool:
    """测试3: 完整工作流执行"""
    print_section("测试3: 完整工作流执行")
    
    try:
        # 创建临时内存目录
        memory_root = Path("/tmp/test_ai_workflow_memory")
        memory_root.mkdir(parents=True, exist_ok=True)
        
        # 创建测试画像
        create_test_memory_profile("test_anchor_001", memory_root)
        
        # 初始化配置
        config = LiveWorkflowConfig(
            anchor_id="test_anchor_001",
            memory_root=memory_root
        )
        
        # 初始化生成器
        analysis_config = {}
        analysis_generator = LiveAnalysisGenerator(analysis_config)
        
        question_config = {}
        question_responder = LiveQuestionResponder(question_config)
        
        # 创建工作流
        workflow = LangGraphLiveWorkflow(
            analysis_generator=analysis_generator,
            question_responder=question_responder,
            config=config
        )
        
        # 创建测试状态
        test_state = create_test_state()
        
        print_info("开始执行工作流...")
        print_info(f"  输入句子数: {len(test_state['sentences'])}")
        print_info(f"  输入弹幕数: {len(test_state['comments'])}")
        
        start_time = time.time()
        
        # 执行工作流
        result = workflow.invoke(test_state)
        
        execution_time = time.time() - start_time
        print_success(f"工作流执行完成，耗时: {execution_time:.2f}秒")
        
        # 验证输出
        print_info("\n工作流输出验证:")
        
        # 检查关键字段
        required_fields = [
            "persona",           # 主播画像
            "chat_signals",      # 弹幕信号
            "topics",            # 话题
            "vibe",              # 氛围
            "analysis_focus",    # 分析焦点
            "analysis_card",     # 分析卡片
            "style_profile",     # 风格画像
            "summary"            # 摘要
        ]
        
        for field in required_fields:
            if field in result:
                print_success(f"  {field}: ✅")
                # 打印部分内容
                value = result[field]
                if isinstance(value, dict):
                    print_info(f"    类型: dict, 键数: {len(value)}")
                elif isinstance(value, list):
                    print_info(f"    类型: list, 长度: {len(value)}")
                else:
                    print_info(f"    类型: {type(value).__name__}")
            else:
                print_warning(f"  {field}: ⚠️  缺失")
        
        # 检查scripts（可选）
        if "scripts" in result:
            scripts = result["scripts"]
            if scripts:
                print_success(f"  scripts: ✅ ({len(scripts)}条)")
            else:
                print_info("  scripts: 空列表")
        else:
            print_info("  scripts: 未生成（可选功能）")
        
        # 打印详细结果
        print_section("AI生成结果详情")
        
        # 1. 分析卡片 (analysis_card)
        if "analysis_card" in result:
            analysis_card = result["analysis_card"]
            if isinstance(analysis_card, dict):
                print_success("📊 分析卡片 (analysis_card):")
                print(json.dumps(analysis_card, ensure_ascii=False, indent=2))
                print()
        
        # 2. 风格画像 (style_profile)
        if "style_profile" in result:
            style_profile = result["style_profile"]
            if isinstance(style_profile, dict):
                print_success("🎨 风格画像 (style_profile):")
                print(json.dumps(style_profile, ensure_ascii=False, indent=2))
                print()
        else:
            print_warning("⚠️  style_profile 字段缺失")
        
        # 3. 摘要 (summary)
        if "summary" in result:
            summary = result["summary"]
            print_success("📝 摘要 (summary):")
            print(summary)
            print()
        
        # 4. 氛围 (vibe)
        if "vibe" in result:
            vibe = result["vibe"]
            if isinstance(vibe, dict):
                print_success("🌊 氛围分析 (vibe):")
                print(json.dumps(vibe, ensure_ascii=False, indent=2))
                print()
        
        # 5. 话题 (topics)
        if "topics" in result:
            topics = result["topics"]
            if isinstance(topics, list):
                print_success("💬 话题检测 (topics):")
                print(json.dumps(topics, ensure_ascii=False, indent=2))
                print()
        else:
            print_warning("⚠️  topics 字段缺失")
        
        # 6. 弹幕信号 (chat_signals)
        if "chat_signals" in result:
            chat_signals = result["chat_signals"]
            if isinstance(chat_signals, list) and len(chat_signals) > 0:
                print_success(f"💭 弹幕信号 (chat_signals) - 共{len(chat_signals)}条:")
                # 只显示前5条
                for i, signal in enumerate(chat_signals[:5], 1):
                    print(f"  {i}. {json.dumps(signal, ensure_ascii=False)}")
                if len(chat_signals) > 5:
                    print(f"  ... 还有 {len(chat_signals) - 5} 条")
                print()
        
        # 7. 分析焦点 (analysis_focus)
        if "analysis_focus" in result:
            analysis_focus = result["analysis_focus"]
            print_success("🎯 分析焦点 (analysis_focus):")
            print(analysis_focus)
            print()
        
        # 8. 主播画像 (persona)
        if "persona" in result:
            persona = result["persona"]
            if isinstance(persona, dict):
                print_success("👤 主播画像 (persona):")
                print(json.dumps(persona, ensure_ascii=False, indent=2))
                print()
        
        # 9. 话术脚本 (scripts) - 可选
        if "scripts" in result:
            scripts = result["scripts"]
            if isinstance(scripts, list) and len(scripts) > 0:
                print_success(f"📜 话术脚本 (scripts) - 共{len(scripts)}条:")
                for i, script in enumerate(scripts[:3], 1):  # 只显示前3条
                    print(f"\n  脚本 {i}:")
                    print(json.dumps(script, ensure_ascii=False, indent=4))
                if len(scripts) > 3:
                    print(f"\n  ... 还有 {len(scripts) - 3} 条脚本")
                print()
        
        # 10. 完整结果JSON（可选，用于调试）
        print_info("💾 完整结果已保存到: /tmp/test_ai_workflow_result.json")
        try:
            with open("/tmp/test_ai_workflow_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            print_success("结果已保存")
        except Exception as e:
            print_warning(f"保存结果失败: {e}")
        
        return True
    except Exception as e:
        print_error(f"工作流执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_without_question_responder() -> bool:
    """测试4: 不带问题响应器的工作流"""
    print_section("测试4: 不带问题响应器的工作流")
    
    try:
        # 创建临时内存目录
        memory_root = Path("/tmp/test_ai_workflow_memory")
        memory_root.mkdir(parents=True, exist_ok=True)
        
        # 创建测试画像
        create_test_memory_profile("test_anchor_002", memory_root)
        
        # 初始化配置
        config = LiveWorkflowConfig(
            anchor_id="test_anchor_002",
            memory_root=memory_root
        )
        
        # 只初始化分析生成器，不初始化问题响应器
        analysis_config = {}
        analysis_generator = LiveAnalysisGenerator(analysis_config)
        
        # 创建工作流（不包含question_responder）
        workflow = LangGraphLiveWorkflow(
            analysis_generator=analysis_generator,
            question_responder=None,  # 不包含问题响应器
            config=config
        )
        
        # 创建测试状态
        test_state = create_test_state()
        test_state["anchor_id"] = "test_anchor_002"
        test_state["broadcaster_id"] = "test_anchor_002"
        
        print_info("开始执行工作流（无问题响应器）...")
        
        start_time = time.time()
        result = workflow.invoke(test_state)
        execution_time = time.time() - start_time
        
        print_success(f"工作流执行完成，耗时: {execution_time:.2f}秒")
        
        # 验证scripts不存在（因为没有question_responder）
        if "scripts" in result:
            print_warning("scripts字段存在（不应该存在）")
        else:
            print_success("scripts字段不存在（符合预期）")
        
        return True
    except Exception as e:
        print_error(f"工作流执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_ai_calls() -> bool:
    """测试5: 验证工作流中的AI调用"""
    print_section("测试5: 验证工作流中的AI调用")
    
    try:
        gateway = get_gateway()
        
        # 检查AI Gateway是否可用
        if not gateway:
            print_error("AI Gateway不可用")
            return False
        
        # 测试简单的AI调用
        print_info("测试AI Gateway直接调用...")
        
        test_messages = [
            {"role": "user", "content": "你好，请回复测试成功"}
        ]
        
        response = gateway.chat_completion(
            messages=test_messages,
            provider="xunfei",
            model="lite"
        )
        
        if response and hasattr(response, 'content') and response.content:
            print_success("AI Gateway调用成功")
            print_info(f"  响应: {response.content[:50]}...")
            print_info(f"  模型: {response.model}")
            print_info(f"  提供商: {response.provider}")
            print_info(f"  耗时: {response.duration_ms:.0f}ms")
            return True
        else:
            print_error("AI Gateway调用失败：无响应内容")
            if response and hasattr(response, 'error'):
                print_error(f"  错误: {response.error}")
            return False
            
    except Exception as e:
        print_error(f"AI调用测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==================== 主函数 ====================

def main():
    """主测试函数"""
    print_section("AI工作流功能测试")
    
    print_info("测试环境检查:")
    print_info(f"  工作目录: {os.getcwd()}")
    print_info(f"  Python版本: {sys.version}")
    
    # 检查环境变量
    xunfei_key = os.getenv("XUNFEI_API_KEY")
    if xunfei_key:
        print_success(f"XUNFEI_API_KEY已设置: {xunfei_key[:20]}...")
    else:
        print_warning("XUNFEI_API_KEY未设置")
    
    # 运行测试
    tests = [
        ("AI Gateway初始化", test_ai_gateway),
        ("工作流初始化", test_workflow_initialization),
        ("AI调用验证", test_workflow_ai_calls),
        ("完整工作流执行", test_workflow_execution),
        ("无问题响应器工作流", test_workflow_without_question_responder),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"测试 '{test_name}' 异常: {e}")
            results.append((test_name, False))
    
    # 打印测试总结
    print_section("测试总结")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    failed = total - passed
    
    print_info(f"总测试数: {total}")
    print_info(f"通过数: {passed}")
    print_info(f"失败数: {failed}")
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name:<30} : {status}")
    
    if failed == 0:
        print_success("\n🎉 所有测试通过！AI工作流功能正常。")
        return 0
    else:
        print_error(f"\n⚠️  有 {failed} 个测试失败，请检查上述错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

