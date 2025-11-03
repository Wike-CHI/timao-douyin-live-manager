#!/usr/bin/env python3
"""
科大讯飞 Lite 模型集成测试脚本
测试所有讯飞 AI 接口的功能和 Token 消耗
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from server.ai.xunfei_lite_client import get_xunfei_client, XUNFEI_MODELS


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_usage(usage_info: dict):
    """打印 Token 使用情况"""
    print(f"\n💰 Token 消耗:")
    print(f"   输入:  {usage_info.get('prompt_tokens', 0)} tokens")
    print(f"   输出:  {usage_info.get('completion_tokens', 0)} tokens")
    print(f"   总计:  {usage_info.get('total_tokens', 0)} tokens")
    print(f"   耗时:  {usage_info.get('request_time_ms', 0):.2f} ms")


def test_connection():
    """测试 1：连接测试"""
    print_section("测试 1: 连接测试")
    
    try:
        client = get_xunfei_client()
        print(f"✓ 客户端初始化成功")
        print(f"  模型: {client.model}")
        print(f"  URL:  {client.base_url}")
        
        content, usage = client.chat_completion(
            messages=[{"role": "user", "content": "你好"}],
            max_tokens=50
        )
        
        print(f"\n✓ API 调用成功")
        print(f"  响应: {content[:100]}...")
        print_usage({
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "request_time_ms": usage.request_time_ms
        })
        
        return True
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        return False


def test_atmosphere_analysis():
    """测试 2：氛围与情绪分析"""
    print_section("测试 2: 氛围与情绪分析")
    
    try:
        client = get_xunfei_client()
        
        # 测试数据
        transcript = """
        大家好，欢迎来到我的直播间！
        今天给大家带来了超级优惠的新品。
        这款产品真的太好用了，性价比超高！
        有没有想要了解的宝宝们？
        """
        
        comments = [
            {"user": "小明", "content": "主播好！"},
            {"user": "小红", "content": "这个多少钱？"},
            {"user": "小刚", "content": "666，主播讲得好！"},
            {"user": "小美", "content": "什么时候发货？"},
            {"user": "小李", "content": "支持主播！"}
        ]
        
        print("📝 输入数据:")
        print(f"  转写文本: {len(transcript)} 字符")
        print(f"  弹幕数量: {len(comments)} 条")
        
        result = client.analyze_live_atmosphere(
            transcript=transcript,
            comments=comments,
            context={"duration_minutes": 30, "viewer_count": 150}
        )
        
        print("\n✓ 分析完成")
        
        if "atmosphere" in result:
            atm = result["atmosphere"]
            print(f"\n🌡️  氛围评估:")
            print(f"   等级: {atm.get('level', '未知')}")
            print(f"   评分: {atm.get('score', 0)}/100")
            print(f"   描述: {atm.get('description', '无')}")
        
        if "emotion" in result:
            emo = result["emotion"]
            print(f"\n😊 情绪分析:")
            print(f"   主要: {emo.get('primary', '未知')}")
            print(f"   次要: {emo.get('secondary', '未知')}")
            print(f"   强度: {emo.get('intensity', 0)}/100")
        
        if "engagement" in result:
            eng = result["engagement"]
            print(f"\n👥 互动参与:")
            print(f"   互动率: {eng.get('interaction_rate', 0)}%")
            print(f"   正向率: {eng.get('positive_rate', 0)}%")
        
        if "suggestions" in result:
            print(f"\n💡 改善建议:")
            for i, sug in enumerate(result["suggestions"][:3], 1):
                print(f"   {i}. {sug}")
        
        print_usage(result.get("_usage", {}))
        
        return True
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        return False


def test_script_generation():
    """测试 3：话术生成"""
    print_section("测试 3: 话术生成")
    
    script_types = [
        ("interaction", "互动引导"),
        ("engagement", "关注点赞召唤"),
        ("clarification", "澄清回应"),
        ("humor", "幽默活跃")
    ]
    
    try:
        client = get_xunfei_client()
        
        for script_type, type_name in script_types:
            print(f"\n📢 生成 [{type_name}] 话术...")
            
            result = client.generate_script(
                script_type=script_type,
                context={
                    "current_topic": "产品介绍",
                    "atmosphere": "活跃",
                    "viewer_count": 200
                }
            )
            
            print(f"   话术: {result.get('line', '生成失败')}")
            print(f"   语气: {result.get('tone', '自然')}")
            if result.get('tags'):
                print(f"   标签: {', '.join(result.get('tags', []))}")
            
            usage = result.get("_usage", {})
            print(f"   Token: {usage.get('total_tokens', 0)} (耗时 {usage.get('request_time_ms', 0):.0f}ms)")
        
        return True
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        return False


def test_realtime_analysis():
    """测试 4：实时分析"""
    print_section("测试 4: 实时分析")
    
    try:
        client = get_xunfei_client()
        
        transcript = """
        刚才给大家详细介绍了这款新品的特点。
        它有三大核心优势：性能强、价格优、服务好。
        看到有很多宝宝在问价格和发货时间。
        """
        
        comments = [
            {"user": "观众1", "content": "价格多少？"},
            {"user": "观众2", "content": "什么时候发货？"},
            {"user": "观众3", "content": "有优惠吗？"},
            {"user": "观众4", "content": "支持！"},
        ]
        
        print("📊 执行实时分析...")
        print(f"  转写: {len(transcript)} 字符")
        print(f"  弹幕: {len(comments)} 条")
        
        result = client.analyze_realtime(
            transcript=transcript,
            comments=comments,
            previous_summary="上一窗口氛围良好，观众积极参与",
            anchor_id="test_anchor"
        )
        
        print("\n✓ 分析完成")
        
        if "summary" in result:
            print(f"\n📝 窗口摘要:")
            print(f"   {result['summary']}")
        
        if "highlight_points" in result:
            print(f"\n✨ 亮点:")
            for point in result["highlight_points"][:3]:
                print(f"   • {point}")
        
        if "risks" in result:
            print(f"\n⚠️  风险:")
            for risk in result["risks"][:3]:
                print(f"   • {risk}")
        
        if "suggestions" in result:
            print(f"\n💡 建议:")
            for sug in result["suggestions"][:3]:
                print(f"   • {sug}")
        
        if "scripts" in result:
            print(f"\n📢 推荐话术:")
            for i, script in enumerate(result["scripts"][:2], 1):
                print(f"   {i}. [{script.get('type', '通用')}] {script.get('text', '')}")
        
        if "atmosphere" in result:
            atm = result["atmosphere"]
            print(f"\n🌡️  氛围: {atm.get('level', '未知')} ({atm.get('score', 0)}/100)")
        
        print_usage(result.get("_usage", {}))
        
        return True
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        return False


def test_models_info():
    """测试 5：模型信息"""
    print_section("测试 5: 模型信息")
    
    print("📋 可用模型:")
    for model_id, model_name in XUNFEI_MODELS.items():
        print(f"   • {model_id:15s} - {model_name}")
    
    return True


def main():
    """主函数"""
    print("\n" + "🚀 " * 20)
    print("  科大讯飞 Lite 模型集成测试")
    print("🚀 " * 20)
    
    # 检查环境变量
    api_key = os.getenv("XUNFEI_API_KEY")
    if not api_key:
        print("\n❌ 错误: 未配置 XUNFEI_API_KEY 环境变量")
        print("\n请在 .env 文件中添加:")
        print("   XUNFEI_API_KEY=your_appid:your_api_secret")
        return
    
    print(f"\n✓ 环境变量已配置")
    print(f"  API Key: {api_key[:20]}...")
    
    # 运行测试
    tests = [
        ("连接测试", test_connection),
        ("氛围与情绪分析", test_atmosphere_analysis),
        ("话术生成", test_script_generation),
        ("实时分析", test_realtime_analysis),
        ("模型信息", test_models_info),
    ]
    
    results = []
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\n\n⏹️  测试中断")
            break
        except Exception as e:
            print(f"\n✗ 测试异常: {e}")
            results.append((test_name, False))
    
    # 统计结果
    print_section("测试结果汇总")
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    print(f"\n总计: {len(results)}/{total_tests} 个测试")
    print(f"✓ 通过: {passed}")
    print(f"✗ 失败: {failed}")
    
    print("\n" + "=" * 60)
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {status:8s} - {test_name}")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 所有测试通过！讯飞 Lite 模型集成成功！")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查配置和网络连接")
    
    print("\n💡 提示:")
    print("  - 查看 Token 使用统计: GET /api/ai_usage/stats/current")
    print("  - 查看模型定价: GET /api/ai_usage/models/pricing")
    print("  - API 文档: http://localhost:9019/docs")
    print()


if __name__ == "__main__":
    main()

