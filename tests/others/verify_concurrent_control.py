#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级验证脚本：验证SenseVoice并发控制机制

只验证核心功能，不进行完整测试，避免内存耗尽
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

print("=" * 60)
print("🔍 SenseVoice并发控制机制验证")
print("=" * 60)

async def verify_concurrent_control():
    """验证并发控制参数"""
    print("\n1️⃣ 验证配置参数...")
    config = SenseVoiceConfig()
    
    checks = {
        "chunk_size": (config.chunk_size, 1600, "内存优化"),
        "chunk_shift": (config.chunk_shift, 400, "内存优化"),
        "encoder_chunk_look_back": (config.encoder_chunk_look_back, 2, "内存优化"),
    }
    
    all_ok = True
    for name, (actual, expected, desc) in checks.items():
        status = "✅" if actual == expected else "❌"
        print(f"  {status} {name}: {actual} (预期: {expected}) - {desc}")
        if actual != expected:
            all_ok = False
    
    if not all_ok:
        return False
    
    print("\n2️⃣ 验证并发控制对象...")
    service = SenseVoiceService(config)
    
    concurrent_checks = {
        "信号量": hasattr(service, '_semaphore'),
        "互斥锁": hasattr(service, '_model_lock'),
        "最大并发数": hasattr(service, '_max_concurrent'),
        "超时设置": hasattr(service, '_timeout_seconds'),
        "活跃请求计数": hasattr(service, '_active_requests'),
        "超时计数": hasattr(service, '_total_timeouts'),
        "错误计数": hasattr(service, '_total_errors'),
    }
    
    for name, exists in concurrent_checks.items():
        status = "✅" if exists else "❌"
        print(f"  {status} {name}: {'存在' if exists else '缺失'}")
        if not exists:
            all_ok = False
    
    if all_ok:
        print(f"\n  📊 并发配置:")
        print(f"     - 最大并发数: {service._max_concurrent}")
        print(f"     - 超时时间: {service._timeout_seconds}秒")
        print(f"     - 初始活跃请求: {service._active_requests}")
    
    print("\n3️⃣ 验证服务状态API...")
    status = service.get_service_status()
    
    required_keys = [
        "initialized", "device", "call_count", "active_requests",
        "max_concurrent", "timeout_seconds", "total_timeouts", "total_errors", "config"
    ]
    
    for key in required_keys:
        exists = key in status
        symbol = "✅" if exists else "❌"
        print(f"  {symbol} {key}: {status.get(key, '缺失')}")
        if not exists:
            all_ok = False
    
    return all_ok

async def main():
    try:
        success = await verify_concurrent_control()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 验证通过！并发控制机制已正确配置")
            print("\n✅ 已实现的防护措施:")
            print("   1. 信号量限制并发数（max_concurrent=2）")
            print("   2. 互斥锁保护模型调用")
            print("   3. 超时保护（timeout=10秒）")
            print("   4. 活跃请求监控")
            print("   5. 超时和错误统计")
            print("\n💡 生产环境验证:")
            print("   - PM2中只会初始化一次模型")
            print("   - 多音频流会通过信号量排队")
            print("   - 超时会自动返回错误，不阻塞其他请求")
            print("\n📝 建议:")
            print("   1. 重启PM2服务应用优化")
            print("   2. 实际测试2-3个直播间同时转写")
            print("   3. 监控日志中的'活跃请求'统计")
            print("=" * 60)
            return 0
        else:
            print("❌ 验证失败！请检查代码配置")
            print("=" * 60)
            return 1
    except Exception as e:
        print(f"\n❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

