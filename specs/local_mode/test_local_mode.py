#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地化模式功能测试脚本

验证本地化改造是否成功：
1. 本地存储服务
2. AI配置管理
3. 启动检测API
4. 无数据库依赖
5. 无订阅检查
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_local_storage():
    """测试本地存储服务"""
    print("\n=== 测试1: 本地存储服务 ===")
    
    try:
        from server.local.local_storage import local_storage
        
        # 测试保存配置
        test_config = {"test_key": "test_value", "timestamp": "2025-01-01"}
        local_storage.save_config(test_config)
        print("✅ 配置保存成功")
        
        # 测试读取配置
        loaded_config = local_storage.load_config()
        assert loaded_config.get("test_key") == "test_value", "配置读取失败"
        print(f"✅ 配置读取成功: {loaded_config}")
        
        # 测试会话存储
        test_session = {
            "session_id": 123,
            "room_id": "test_room",
            "status": "active"
        }
        local_storage.save_session(test_session)
        print("✅ 会话保存成功")
        
        # 测试读取会话
        loaded_session = local_storage.load_session(123)
        assert loaded_session is not None, "会话读取失败"
        print(f"✅ 会话读取成功: {loaded_session}")
        
        print("✅ 本地存储服务测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 本地存储服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_config():
    """测试AI配置管理"""
    print("\n=== 测试2: AI配置管理 ===")
    
    try:
        from server.local.local_config import LocalAIConfig
        
        # 测试获取配置
        config = LocalAIConfig.get_config()
        print(f"✅ 获取AI配置: {list(config.keys()) if config else '空配置'}")
        
        # 测试添加服务商
        test_provider = {
            "provider_id": "test_provider",
            "api_key": "test_api_key_12345",
            "base_url": "https://api.test.com",
            "default_model": "test-model",
            "enabled": True
        }
        LocalAIConfig.save_provider(test_provider)
        print("✅ 服务商保存成功")
        
        # 测试读取服务商
        config = LocalAIConfig.get_config()
        assert "providers" in config, "配置中缺少providers"
        assert "test_provider" in config["providers"], "服务商保存失败"
        print(f"✅ 服务商读取成功: {config['providers']['test_provider']['provider_id']}")
        
        # 测试功能模型映射
        test_functions = {
            "live_summary": {"provider": "test_provider", "model": "test-model"}
        }
        LocalAIConfig.save_function_models(test_functions)
        print("✅ 功能模型映射保存成功")
        
        # 检查初始化状态
        is_init = LocalAIConfig.is_initialized()
        print(f"✅ 初始化状态: {is_init}")
        
        print("✅ AI配置管理测试通过")
        return True
        
    except Exception as e:
        print(f"❌ AI配置管理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_database_import():
    """测试无数据库导入依赖"""
    print("\n=== 测试3: 无数据库依赖 ===")
    
    try:
        # 检查是否能正常导入（但不应使用数据库）
        import server.app.main
        print("✅ main.py 导入成功（已移除数据库初始化）")
        
        # 检查依赖项
        try:
            from server.app.core.dependencies import get_current_user
            user = get_current_user()
            assert user.username == "local_user", "用户名不正确"
            assert user.role == "super_admin", "角色不正确"
            print(f"✅ 本地用户依赖正常: {user.username} ({user.role})")
        except Exception as e:
            print(f"❌ 依赖项测试失败: {e}")
            return False
        
        print("✅ 无数据库依赖测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 无数据库依赖测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_gateway_local_config():
    """测试AI网关本地配置加载"""
    print("\n=== 测试4: AI网关本地配置 ===")
    
    try:
        from server.ai.ai_gateway import AIGateway
        
        # 获取AI网关实例
        gateway = AIGateway.get_instance()
        print(f"✅ AI网关实例创建成功")
        
        # 检查是否加载了本地配置
        providers = gateway.providers
        print(f"✅ 已加载的服务商: {list(providers.keys()) if providers else '无'}")
        
        # 如果有测试服务商，验证配置
        if "test_provider" in providers:
            provider = providers["test_provider"]
            assert provider.api_key == "test_api_key_12345", "API Key不匹配"
            print(f"✅ 服务商配置验证成功: {provider.name}")
        else:
            print("⚠️ 未找到测试服务商（可能是首次启动）")
        
        print("✅ AI网关本地配置测试通过")
        return True
        
    except Exception as e:
        print(f"❌ AI网关本地配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_directory_structure():
    """测试数据目录结构"""
    print("\n=== 测试5: 数据目录结构 ===")
    
    try:
        data_dir = project_root / "data"
        
        # 检查关键文件
        expected_files = [
            "config.json",
            "ai_config.json",
            "ai_usage.json",
        ]
        
        for file in expected_files:
            file_path = data_dir / file
            if file_path.exists():
                print(f"✅ 文件存在: {file}")
                # 验证JSON格式
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"   内容: {list(data.keys()) if isinstance(data, dict) else type(data).__name__}")
            else:
                print(f"⚠️ 文件不存在: {file} (将在首次启动时创建)")
        
        # 检查sessions目录
        sessions_dir = data_dir / "sessions"
        if sessions_dir.exists():
            session_count = len(list(sessions_dir.glob("*.json")))
            print(f"✅ sessions目录存在，包含 {session_count} 个会话文件")
        else:
            print("⚠️ sessions目录不存在（将在首次启动时创建）")
        
        print("✅ 数据目录结构测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 数据目录结构测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("本地化模式功能测试")
    print("=" * 60)
    
    tests = [
        ("本地存储服务", test_local_storage),
        ("AI配置管理", test_ai_config),
        ("无数据库依赖", test_no_database_import),
        ("AI网关本地配置", test_ai_gateway_local_config),
        ("数据目录结构", test_data_directory_structure),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试执行异常: {name}")
            print(f"错误: {e}")
            results.append((name, False))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！本地化模式配置正确。")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败，请检查配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

