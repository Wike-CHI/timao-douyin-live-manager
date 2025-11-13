#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
科大讯飞星火大模型接口测试脚本

功能：
1. 测试环境变量配置
2. 测试直接调用OpenAI兼容接口
3. 测试通过AI Gateway调用
4. 测试不同模型
5. 显示详细的测试结果

使用方法：
    python server/test_xunfei_spark.py

审查人: 叶维哲
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
env_file = project_root / "server" / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
    print(f"✅ 已加载环境变量文件: {env_file}")
else:
    print(f"⚠️  未找到环境变量文件: {env_file}")
    print("   请确保 server/.env 文件存在并包含 XUNFEI_API_KEY 配置")

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_section(title: str):
    """打印章节标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")


def print_success(msg: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")


def print_error(msg: str):
    """打印错误消息"""
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")


def print_warning(msg: str):
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")


def print_info(msg: str):
    """打印信息消息"""
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")


def test_environment_variables() -> bool:
    """测试环境变量配置"""
    print_section("测试1: 环境变量配置检查")
    
    api_key = os.getenv("XUNFEI_API_KEY")
    base_url = os.getenv("XUNFEI_BASE_URL", "https://spark-api-open.xf-yun.com/v1")
    model = os.getenv("XUNFEI_MODEL", "lite")
    
    # 检查API Key
    if not api_key:
        print_error("XUNFEI_API_KEY 未设置")
        print_info("请在 server/.env 文件中添加：")
        print_info("XUNFEI_API_KEY=你的APPID:你的APISecret")
        print_info("或者使用单独的配置：")
        print_info("XUNFEI_APPID=你的APPID")
        print_info("XUNFEI_API_KEY=你的APIKey")
        print_info("XUNFEI_API_SECRET=你的APISecret")
        return False
    
    print_success(f"XUNFEI_API_KEY 已设置: {api_key[:20]}...{api_key[-10:]}")
    
    # 检查API Key格式
    if ":" not in api_key:
        print_error("XUNFEI_API_KEY 格式错误")
        print_info("正确格式: APPID:APISecret")
        print_info(f"当前值: {api_key}")
        print_warning("如果使用OpenAI兼容接口，可能需要APIKey而不是APISecret")
        return False
    
    appid, api_secret = api_key.split(":", 1)
    if not appid or not api_secret:
        print_error("XUNFEI_API_KEY 格式错误：APPID 或 APISecret 为空")
        return False
    
    print_success(f"API Key 格式正确")
    print_info(f"  APPID: {appid}")
    print_info(f"  APISecret: {api_secret[:10]}...{api_secret[-5:]}")
    
    # 检查是否有单独的APIKey配置
    separate_api_key = os.getenv("XUNFEI_APIKEY") or os.getenv("XUNFEI_API_KEY_VALUE")
    if separate_api_key:
        print_info(f"  检测到单独的APIKey配置: {separate_api_key[:10]}...")
    
    # 检查是否有APIPassword配置
    api_password = os.getenv("XUNFEI_API_PASSWORD") or os.getenv("XUNFEI_APIPASSWORD")
    if api_password:
        print_info(f"  检测到APIPassword配置: {api_password[:10]}...")
        print_info("  APIPassword通常用于批处理API认证")
    
    # 检查Base URL
    print_success(f"XUNFEI_BASE_URL: {base_url}")
    
    # 检查模型
    print_success(f"XUNFEI_MODEL: {model}")
    
    # 诊断信息
    print_info("\n⚠️  如果遇到认证错误，可能需要：")
    print_info("1. 确认使用的是APIKey或APIPassword（而不是APISecret）")
    print_info("2. 确认控制台中获取的是正确的凭证类型")
    print_info("3. 检查接口地址是否正确")
    print_info("4. 批处理API通常使用APIPassword进行认证")
    
    return True


def test_openai_client() -> bool:
    """测试直接调用OpenAI兼容客户端"""
    print_section("测试2: 直接调用OpenAI兼容接口")
    
    try:
        from openai import OpenAI  # pyright: ignore[reportMissingImports]
    except ImportError:
        print_error("openai 库未安装")
        print_info("请运行: pip install openai")
        return False
    
    api_key = os.getenv("XUNFEI_API_KEY")
    base_url = os.getenv("XUNFEI_BASE_URL", "https://spark-api-open.xf-yun.com/v1")
    model = os.getenv("XUNFEI_MODEL", "lite")
    
    if not api_key:
        print_error("XUNFEI_API_KEY 未设置，跳过测试")
        return False
    
    # 尝试不同的API Key格式
    test_configs = []
    
    # 配置1: 使用原始格式 (APPID:APISecret)
    if ":" in api_key:
        appid, api_secret = api_key.split(":", 1)
        test_configs.append({
            "name": "格式1: APPID:APISecret",
            "api_key": api_key,
            "description": "使用组合格式"
        })
        
        # 配置2: 尝试只使用APISecret
        test_configs.append({
            "name": "格式2: 仅APISecret",
            "api_key": api_secret,
            "description": "尝试只使用APISecret部分"
        })
    
    # 配置3: 如果有单独的APIKey
    separate_api_key = os.getenv("XUNFEI_APIKEY") or os.getenv("XUNFEI_API_KEY_VALUE")
    if separate_api_key:
        test_configs.append({
            "name": "格式3: 单独的APIKey",
            "api_key": separate_api_key,
            "description": "使用单独的APIKey环境变量"
        })
    
    # 配置4: 如果有APIPassword（批处理API使用）
    api_password = os.getenv("XUNFEI_API_PASSWORD") or os.getenv("XUNFEI_APIPASSWORD")
    if api_password:
        test_configs.append({
            "name": "格式4: APIPassword",
            "api_key": api_password,
            "description": "使用APIPassword（批处理API认证方式）"
        })
    
    # 配置5: 如果当前配置是APPID:APIPassword格式
    if ":" in api_key:
        appid, secret_part = api_key.split(":", 1)
        # 如果第二部分可能是APIPassword
        test_configs.append({
            "name": "格式5: APPID:APIPassword",
            "api_key": api_key,
            "description": "尝试APPID:APIPassword组合格式"
        })
    
    success = False
    for i, config in enumerate(test_configs, 1):
        print_info(f"\n尝试配置 {i}: {config['name']}")
        print_info(f"  说明: {config['description']}")
        
        try:
            client = OpenAI(
                api_key=config["api_key"],
                base_url=base_url
            )
            
            print_info(f"正在调用模型: {model}")
            print_info("测试消息: '你好，请回复测试成功'")
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "你好，请回复测试成功"}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            print_success(f"✅ 配置 {i} 成功！")
            print_info(f"响应内容: {content}")
            print_success(f"推荐使用配置: {config['name']}")
            print_info(f"建议在 .env 中使用: XUNFEI_API_KEY={config['api_key'][:20]}...")
            
            success = True
            break
            
        except Exception as e:
            error_str = str(e)
            if "401" in error_str or "Authentication" in error_str or "HMAC" in error_str:
                print_warning(f"配置 {i} 认证失败: {type(e).__name__}")
            else:
                print_error(f"配置 {i} 失败: {e}")
            continue
    
    if not success:
        print_error("\n所有配置都失败了")
        print_warning("\n🔍 认证错误诊断：")
        print_info("科大讯飞星火大模型的OpenAI兼容接口可能需要：")
        print_info("1. 使用 APIKey（而不是 APISecret）")
        print_info("2. 或者需要特殊的认证头")
        print_info("3. 或者该接口不支持OpenAI兼容方式")
        print_info("\n建议检查：")
        print_info("- 控制台中获取的是 APIKey 还是 APISecret？")
        print_info("- 是否应该使用 WebSocket 接口而不是 HTTP 接口？")
        print_info("- 接口地址是否正确：https://spark-api-open.xf-yun.com/v1")
        print_info("\n参考文档：")
        print_info("- HTTP调用文档: https://www.xfyun.cn/doc/spark/HTTP调用文档.html")
        print_info("- WebSocket文档: https://www.xfyun.cn/doc/spark/Web.html")
        print_info("\n⚠️  注意：科大讯飞星火大模型可能主要支持WebSocket接口")
        print_info("    OpenAI兼容的HTTP接口可能不完全支持或需要特殊配置")
    
    return success


def test_ai_gateway() -> bool:
    """测试通过AI Gateway调用"""
    print_section("测试3: 通过AI Gateway调用")
    
    try:
        from server.ai.ai_gateway import AIGateway
    except ImportError as e:
        print_error(f"无法导入AI Gateway: {e}")
        return False
    
    try:
        print_info("正在获取AI Gateway实例...")
        gateway = AIGateway.get_instance()
        print_success("AI Gateway实例获取成功")
        
        # 检查提供商是否注册
        print_info("检查xunfei提供商状态...")
        providers = gateway.list_providers()
        
        if "xunfei" not in providers:
            print_error("xunfei提供商未注册")
            print_info("可能的原因:")
            print_info("1. XUNFEI_API_KEY 未设置或格式错误")
            print_info("2. 服务启动时未加载环境变量")
            return False
        
        provider_info = providers["xunfei"]
        print_success(f"xunfei提供商已注册")
        print_info(f"  启用状态: {provider_info.get('enabled', False)}")
        print_info(f"  默认模型: {provider_info.get('default_model', 'N/A')}")
        print_info(f"  支持模型: {provider_info.get('models', [])}")
        
        if not provider_info.get("enabled", False):
            print_error("xunfei提供商已注册但未启用")
            return False
        
        # 测试调用
        model = os.getenv("XUNFEI_MODEL", "lite")
        print_info(f"正在通过Gateway调用模型: {model}")
        print_info("测试消息: '你好，你是谁'")
        
        response = gateway.chat_completion(
            messages=[
                {"role": "user", "content": "你好，你是谁"}
            ],
            provider="xunfei",
            model=model,
            max_tokens=100
        )
        
        if not response.success:
            print_error(f"Gateway调用失败: {response.error}")
            return False
        
        print_success("Gateway调用成功！")
        print_info(f"  使用的模型: {response.model}")
        print_info(f"  响应内容: {response.content}")
        
        if "测试成功" in response.content or "成功" in response.content:
            print_success("响应内容验证通过")
            return True
        else:
            print_warning("响应内容未包含预期关键词，但调用成功")
            return True
            
    except Exception as e:
        print_error(f"Gateway测试失败: {e}")
        import traceback
        print_info("详细错误信息:")
        print(traceback.format_exc())
        return False


def test_different_models() -> bool:
    """测试不同的模型"""
    print_section("测试4: 测试不同模型")
    
    models = ["lite", "generalv3", "generalv3.5", "4.0Ultra"]
    api_key = os.getenv("XUNFEI_API_KEY")
    
    if not api_key:
        print_error("XUNFEI_API_KEY 未设置，跳过测试")
        return False
    
    try:
        from openai import OpenAI  # pyright: ignore[reportMissingImports]
        
        base_url = os.getenv("XUNFEI_BASE_URL", "https://spark-api-open.xf-yun.com/v1")
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        results = {}
        
        for model in models:
            print_info(f"测试模型: {model}")
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "说'你好'"}],
                    max_tokens=50
                )
                content = response.choices[0].message.content
                results[model] = {"success": True, "content": content}
                print_success(f"  {model}: ✅ 可用")
            except Exception as e:
                results[model] = {"success": False, "error": str(e)}
                print_error(f"  {model}: ❌ 失败 - {e}")
        
        # 统计结果
        success_count = sum(1 for r in results.values() if r.get("success"))
        print_info(f"\n模型测试结果: {success_count}/{len(models)} 个模型可用")
        
        return success_count > 0
        
    except Exception as e:
        print_error(f"模型测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("="*70)
    print("  科大讯飞星火大模型接口测试".center(70))
    print("="*70)
    print(f"{Colors.RESET}")
    
    results = {}
    
    # 测试1: 环境变量
    results["env"] = test_environment_variables()
    
    if not results["env"]:
        print_error("\n环境变量配置失败，请先配置 XUNFEI_API_KEY")
        print_info("配置方法:")
        print_info("1. 在 server/.env 文件中添加:")
        print_info("   XUNFEI_API_KEY=你的APPID:你的APISecret")
        print_info("   XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1")
        print_info("   XUNFEI_MODEL=lite")
        print_info("2. 重启服务或重新运行此脚本")
        return
    
    # 测试2: 直接调用OpenAI客户端
    results["openai"] = test_openai_client()
    
    # 测试3: AI Gateway
    results["gateway"] = test_ai_gateway()
    
    # 测试4: 不同模型（可选）
    print_info("\n是否测试所有模型？这可能需要一些时间...")
    test_all = input("输入 y 测试所有模型，其他键跳过: ").strip().lower() == 'y'
    if test_all:
        results["models"] = test_different_models()
    
    # 总结
    print_section("测试总结")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print_info(f"总测试数: {total}")
    print_info(f"通过数: {passed}")
    print_info(f"失败数: {total - passed}")
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name:15s}: {status}")
    
    if passed == total:
        print_success("\n🎉 所有测试通过！科大讯飞星火大模型接口可用。")
    elif passed > 0:
        print_warning(f"\n⚠️  部分测试通过 ({passed}/{total})，请检查失败的测试项。")
    else:
        print_error("\n❌ 所有测试失败，请检查配置和网络连接。")
    
    print()


if __name__ == "__main__":
    main()

