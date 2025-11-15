#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存优化功能测试脚本
审查人：叶维哲

验证所有内存优化功能是否正确实现
"""

import sys
import os
import importlib.util
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_memory_monitor_exists():
    """测试内存监控服务模块是否存在"""
    print("测试1: 检查内存监控服务模块...")
    try:
        module_path = project_root / "server" / "app" / "services" / "memory_monitor.py"
        if not module_path.exists():
            print("  ❌ 内存监控服务文件不存在")
            return False
        print("  ✅ 内存监控服务文件存在")
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False


def test_memory_monitor_imports():
    """测试内存监控服务是否可以导入"""
    print("测试2: 检查内存监控服务导入...")
    try:
        from server.app.services.memory_monitor import get_memory_monitor, MemoryMonitor
        print("  ✅ 内存监控服务可以正确导入")
        
        # 测试创建实例
        monitor = get_memory_monitor()
        if monitor is None:
            print("  ❌ 无法创建内存监控实例")
            return False
        print("  ✅ 内存监控实例创建成功")
        
        # 测试获取状态
        status = monitor.get_status()
        print(f"  ✅ 获取状态成功: {status.get('enabled', False)}")
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False


def test_ai_analyzer_optimization():
    """测试AI分析服务内存优化"""
    print("测试3: 检查AI分析服务内存优化...")
    try:
        module_path = project_root / "server" / "app" / "services" / "ai_live_analyzer.py"
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键优化代码
        checks = [
            ("user_scores限制", "len(s.user_scores) > 500"),
            ("user_scores清理", "s.user_scores = dict(sorted_users[:300])"),
            ("垃圾回收", "gc.collect()"),
        ]
        
        all_passed = True
        for name, keyword in checks:
            if keyword in content:
                print(f"  ✅ {name}已实现")
            else:
                print(f"  ❌ {name}未找到")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False


def test_audio_service_optimization():
    """测试转写服务内存优化"""
    print("测试4: 检查转写服务内存优化...")
    try:
        module_path = project_root / "server" / "app" / "services" / "live_audio_stream_service.py"
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键优化代码
        checks = [
            ("转写计数器", "self._transcription_count"),
            ("定期GC", "if self._transcription_count % 100 == 0:"),
            ("垃圾回收", "gc.collect()"),
        ]
        
        all_passed = True
        for name, keyword in checks:
            if keyword in content:
                print(f"  ✅ {name}已实现")
            else:
                print(f"  ❌ {name}未找到")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False


def test_report_service_optimization():
    """测试录制服务内存优化"""
    print("测试5: 检查录制服务内存优化...")
    try:
        module_path = project_root / "server" / "app" / "services" / "live_report_service.py"
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键优化代码
        checks = [
            ("comments限制", "if len(self._comments) > 10000:"),
            ("comments清理", "self._comments = self._comments[-5000:]"),
            ("analysis限制", "if len(self._analysis) > 100:"),
            ("analysis清理", "self._analysis = self._analysis[-50:]"),
        ]
        
        all_passed = True
        for name, keyword in checks:
            if keyword in content:
                print(f"  ✅ {name}已实现")
            else:
                print(f"  ❌ {name}未找到")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False


def test_frontend_optimization():
    """测试前端内存优化"""
    print("测试6: 检查前端存储优化...")
    try:
        module_path = project_root / "electron" / "renderer" / "src" / "store" / "useLiveConsoleStore.ts"
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键优化代码
        checks = [
            ("log限制注释", "// 🆕 内存优化：限制日志最多1000条"),
            ("log限制逻辑", "currentLog.length >= 1000"),
            ("aiEvents限制注释", "// 🆕 内存优化：限制AI事件最多100条"),
            ("aiEvents限制逻辑", "currentEvents.length >= 100"),
        ]
        
        all_passed = True
        for name, keyword in checks:
            if keyword in content:
                print(f"  ✅ {name}已实现")
            else:
                print(f"  ❌ {name}未找到")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False


def test_pm2_config():
    """测试PM2配置优化"""
    print("测试7: 检查PM2配置优化...")
    try:
        config_path = project_root / "ecosystem.config.js"
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键配置
        checks = [
            ("内存限制4.5G", "max_memory_restart: '4.5G'"),
            ("min_uptime 30s", "min_uptime: '30s'"),
            ("max_restarts 5", "max_restarts: 5"),
            ("restart_delay 10000", "restart_delay: 10000"),
        ]
        
        all_passed = True
        for name, keyword in checks:
            if keyword in content:
                print(f"  ✅ {name}已配置")
            else:
                print(f"  ❌ {name}未找到")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False


def test_main_integration():
    """测试main.py中的内存监控集成"""
    print("测试8: 检查main.py内存监控集成...")
    try:
        main_path = project_root / "server" / "app" / "main.py"
        with open(main_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查启动和停止集成
        checks = [
            ("导入内存监控", "from server.app.services.memory_monitor import get_memory_monitor"),
            ("启动内存监控", "await memory_monitor.start()"),
            ("停止内存监控", "await memory_monitor.stop()"),
        ]
        
        all_passed = True
        for name, keyword in checks:
            if keyword in content:
                print(f"  ✅ {name}已集成")
            else:
                print(f"  ❌ {name}未找到")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False


def test_api_endpoint():
    """测试内存监控API端点"""
    print("测试9: 检查内存监控API端点...")
    try:
        api_path = project_root / "server" / "app" / "api" / "model_status.py"
        with open(api_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查API端点
        checks = [
            ("API路由", '@router.get("/memory-status")'),
            ("API函数", "async def get_memory_status()"),
            ("获取状态", "monitor.get_status()"),
            ("获取快照", "monitor.get_recent_snapshots"),
        ]
        
        all_passed = True
        for name, keyword in checks:
            if keyword in content:
                print(f"  ✅ {name}已实现")
            else:
                print(f"  ❌ {name}未找到")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 80)
    print("内存优化功能测试")
    print("=" * 80)
    print()
    
    tests = [
        test_memory_monitor_exists,
        test_memory_monitor_imports,
        test_ai_analyzer_optimization,
        test_audio_service_optimization,
        test_report_service_optimization,
        test_frontend_optimization,
        test_pm2_config,
        test_main_integration,
        test_api_endpoint,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
            results.append(False)
        print()
    
    # 汇总结果
    print("=" * 80)
    print("测试汇总")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    print(f"失败: {total - passed}/{total}")
    
    if passed == total:
        print("\n✅ 所有测试通过！内存优化功能已正确实现。")
        return 0
    else:
        print(f"\n⚠️ {total - passed}个测试失败，请检查实现。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

