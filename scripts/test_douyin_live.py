#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音直播间快速测试脚本

用法:
    python scripts/test_douyin_live.py
    
或指定参数:
    python scripts/test_douyin_live.py --url https://live.douyin.com/191495446158 --duration 300
"""

import sys
import os
import asyncio
import argparse

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入测试模块
from server.tests.integration.test_douyin_live_integration import main as run_test


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='抖音直播间集成测试')
    
    parser.add_argument(
        '--url',
        default='https://live.douyin.com/191495446158',
        help='直播间URL (默认: https://live.douyin.com/191495446158)'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=300,
        help='测试时长(秒) (默认: 300秒 = 5分钟)'
    )
    
    parser.add_argument(
        '--backend',
        default='http://localhost:10090',
        help='后端服务地址 (默认: http://localhost:10090)'
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    print("=" * 70)
    print("抖音直播间自动化测试")
    print("=" * 70)
    print(f"📺 直播间URL: {args.url}")
    print(f"⏱️  测试时长: {args.duration}秒 ({args.duration//60}分{args.duration%60}秒)")
    print(f"🖥️  后端服务: {args.backend}")
    print("=" * 70)
    print("")
    print("测试流程:")
    print("  1. ✅ 启动抖音直播监控")
    print("  2. 🎤 启动音频转写")
    print("  3. 🤖 启动AI实时分析")
    print("  4. 📊 监控并收集数据")
    print("  5. 📝 生成报告并停止")
    print("")
    print("=" * 70)
    print("")
    
    # 更新全局配置
    from server.tests.integration import test_douyin_live_integration
    if hasattr(test_douyin_live_integration, 'LIVE_ROOM_URL'):
        test_douyin_live_integration.LIVE_ROOM_URL = args.url
    if hasattr(test_douyin_live_integration, 'TEST_DURATION_SECONDS'):
        test_douyin_live_integration.TEST_DURATION_SECONDS = args.duration
    if hasattr(test_douyin_live_integration, 'BASE_URL'):
        test_douyin_live_integration.BASE_URL = args.backend
    
    # 运行测试
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试失败: {str(e)}")
        sys.exit(1)

