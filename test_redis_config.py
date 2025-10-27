#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis配置测试脚本
用于验证Redis配置是否正确加载和连接
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from server.config import ConfigManager, RedisConfig
from server.utils.redis_manager import RedisManager, init_redis

def test_redis_config():
    """测试Redis配置加载"""
    print("=" * 50)
    print("🔧 测试Redis配置加载")
    print("=" * 50)
    
    try:
        # 创建配置管理器
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        print(f"Redis配置:")
        print(f"  - enabled: {config.redis.enabled}")
        print(f"  - host: {config.redis.host}")
        print(f"  - port: {config.redis.port}")
        print(f"  - db: {config.redis.db}")
        print(f"  - password: {'***' if config.redis.password else '(空)'}")
        print(f"  - max_connections: {config.redis.max_connections}")
        print(f"  - socket_timeout: {config.redis.socket_timeout}")
        print(f"  - default_ttl: {config.redis.default_ttl}")
        
        return config.redis
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return None

def test_redis_connection(redis_config: RedisConfig):
    """测试Redis连接"""
    print("\n" + "=" * 50)
    print("🔗 测试Redis连接")
    print("=" * 50)
    
    try:
        # 创建Redis管理器
        redis_manager = RedisManager(redis_config)
        
        print(f"Redis管理器状态:")
        print(f"  - 是否启用: {redis_manager.is_enabled()}")
        
        if redis_manager.is_enabled():
            # 测试ping
            ping_result = redis_manager.ping()
            print(f"  - Ping测试: {'✅ 成功' if ping_result else '❌ 失败'}")
            
            if ping_result:
                # 测试基本操作
                test_key = "test:config_check"
                test_value = "hello_redis"
                
                # 设置值
                set_result = redis_manager.set(test_key, test_value, ttl=60)
                print(f"  - 设置测试键: {'✅ 成功' if set_result else '❌ 失败'}")
                
                # 获取值
                get_result = redis_manager.get(test_key)
                print(f"  - 获取测试键: {'✅ 成功' if get_result == test_value else '❌ 失败'}")
                print(f"    值: {get_result}")
                
                # 删除测试键
                del_result = redis_manager.delete(test_key)
                print(f"  - 删除测试键: {'✅ 成功' if del_result > 0 else '❌ 失败'}")
                
                return True
            else:
                print("  - 连接失败，无法进行进一步测试")
                return False
        else:
            print("  - Redis未启用或连接失败")
            return False
            
    except Exception as e:
        print(f"❌ Redis连接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_variables():
    """测试环境变量"""
    print("\n" + "=" * 50)
    print("🌍 检查环境变量")
    print("=" * 50)
    
    redis_env_vars = [
        'REDIS_ENABLED',
        'REDIS_HOST', 
        'REDIS_PORT',
        'REDIS_DB',
        'REDIS_PASSWORD',
        'REDIS_MAX_CONNECTIONS',
        'REDIS_CACHE_TTL'
    ]
    
    for var in redis_env_vars:
        value = os.getenv(var)
        print(f"  - {var}: {value if value else '(未设置)'}")

def main():
    """主函数"""
    print("🚀 Redis配置和连接测试")
    
    # 测试环境变量
    test_environment_variables()
    
    # 测试配置加载
    redis_config = test_redis_config()
    
    if redis_config:
        # 测试连接
        connection_success = test_redis_connection(redis_config)
        
        print("\n" + "=" * 50)
        print("📊 测试结果总结")
        print("=" * 50)
        
        if connection_success:
            print("✅ Redis配置和连接测试全部通过")
        else:
            print("❌ Redis连接测试失败")
            print("\n可能的解决方案:")
            print("1. 检查Redis服务是否正在运行")
            print("2. 验证.env文件中的Redis配置")
            print("3. 确认防火墙设置")
            print("4. 检查Redis密码设置")
    else:
        print("\n❌ 配置加载失败，无法进行连接测试")
    
    print("\n🏁 测试完成!")

if __name__ == "__main__":
    main()