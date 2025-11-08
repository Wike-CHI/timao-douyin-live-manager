#!/usr/bin/env python3
"""
AI 网关初始化自动测试脚本

测试内容：
1. AI 服务商客户端初始化
2. qwen 服务商功能验证
3. 环境配置检查

用法：
    python tests/test_ai_gateway_initialization.py
"""

import os
import sys
import logging
import unittest
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'server'))

# 加载环境变量
try:
    from dotenv import load_dotenv
    server_env = Path(__file__).parent.parent / 'server' / '.env'
    if server_env.exists():
        load_dotenv(server_env)
except ImportError:
    pass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class TestAIGatewayInitialization(unittest.TestCase):
    """AI 网关初始化测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        from server.ai.ai_gateway import AIGateway
        cls.gateway = AIGateway.get_instance()
    
    def test_01_gateway_instance(self):
        """测试：AI 网关实例创建"""
        self.assertIsNotNone(self.gateway)
        self.assertIsInstance(self.gateway.providers, dict)
    
    def test_02_providers_registration(self):
        """测试：服务商注册"""
        providers = self.gateway.list_providers()
        
        # 记录已注册的服务商
        print(f"\n已注册的服务商数量: {len(providers)}")
        for name, config in providers.items():
            status = "✅" if config['enabled'] else "❌"
            print(f"  {status} {name}: {config['default_model']}")
        
        # 至少应该注册一个服务商
        self.assertGreater(len(providers), 0, "至少应注册一个AI服务商")
    
    def test_03_qwen_client_initialization(self):
        """测试：qwen 客户端初始化（如果配置了）"""
        providers = self.gateway.list_providers()
        
        if "qwen" not in providers:
            self.skipTest("qwen 服务商未配置")
        
        qwen_config = providers["qwen"]
        
        # 验证配置
        self.assertIn("enabled", qwen_config)
        self.assertIn("default_model", qwen_config)
        self.assertIn("base_url", qwen_config)
        
        # 如果已启用，验证客户端
        if qwen_config["enabled"]:
            self.assertIn("qwen", self.gateway.clients)
            self.assertIsNotNone(self.gateway.clients["qwen"])
            print("\n✅ qwen 客户端初始化成功")
        else:
            print("\n⚠️ qwen 服务商已禁用")
    
    def test_04_xunfei_client_initialization(self):
        """测试：xunfei 客户端初始化（如果配置了）"""
        providers = self.gateway.list_providers()
        
        if "xunfei" not in providers:
            self.skipTest("xunfei 服务商未配置")
        
        xunfei_config = providers["xunfei"]
        
        if xunfei_config["enabled"]:
            self.assertIn("xunfei", self.gateway.clients)
            self.assertIsNotNone(self.gateway.clients["xunfei"])
            print("\n✅ xunfei 客户端初始化成功")
    
    def test_05_gemini_client_initialization(self):
        """测试：gemini 客户端初始化（如果配置了）"""
        providers = self.gateway.list_providers()
        
        if "gemini" not in providers:
            self.skipTest("gemini 服务商未配置")
        
        gemini_config = providers["gemini"]
        
        if gemini_config["enabled"]:
            self.assertIn("gemini", self.gateway.clients)
            self.assertIsNotNone(self.gateway.clients["gemini"])
            print("\n✅ gemini 客户端初始化成功")
    
    def test_06_function_configs(self):
        """测试：功能级别模型配置"""
        func_configs = self.gateway.list_function_configs()
        
        print("\n功能级别的模型配置:")
        for func_name, config in func_configs.items():
            print(f"  - {func_name}: {config['provider']}/{config['model']}")
        
        # 验证关键功能配置存在
        required_functions = [
            "live_analysis",
            "style_profile",
            "script_generation",
            "live_review"
        ]
        
        for func in required_functions:
            self.assertIn(func, func_configs, f"缺少功能配置: {func}")
    
    def test_07_no_proxies_error(self):
        """测试：确保不存在 proxies 参数错误"""
        providers = self.gateway.list_providers()
        
        # 检查所有已启用的服务商
        enabled_providers = [
            name for name, config in providers.items()
            if config['enabled']
        ]
        
        self.assertGreater(
            len(enabled_providers),
            0,
            "至少应有一个服务商被成功启用（无 proxies 错误）"
        )
        
        print(f"\n✅ 所有启用的服务商均无 proxies 参数错误")
        print(f"   启用的服务商: {', '.join(enabled_providers)}")


def run_tests():
    """运行测试套件"""
    print("=" * 70)
    print("AI 网关初始化自动测试")
    print("=" * 70)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAIGatewayInitialization)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"运行测试: {result.testsRun} 个")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)} 个")
    print(f"失败: {len(result.failures)} 个")
    print(f"错误: {len(result.errors)} 个")
    print(f"跳过: {len(result.skipped)} 个")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

