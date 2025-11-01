#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 StreamCap 导入
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("测试 StreamCap 模块导入...")

try:
    # 测试 utils
    from server.modules.streamcap.utils.utils import trace_error_decorator
    print("  [OK] utils.utils")
except Exception as e:
    print(f"  [FAIL] utils.utils: {e}")
    import traceback
    traceback.print_exc()

try:
    # 测试 handlers
    from server.modules.streamcap.platforms.platform_handlers.handlers import CustomHandler
    print("  [OK] platform_handlers.handlers")
except Exception as e:
    print(f"  [FAIL] handlers: {e}")
    import traceback
    traceback.print_exc()

try:
    # 测试 platforms 顶层
    from server.modules.streamcap.platforms import get_platform_handler
    print("  [OK] platforms")
except Exception as e:
    print(f"  [FAIL] platforms: {e}")
    import traceback
    traceback.print_exc()

try:
    # 测试 media
    from server.modules.streamcap.media import create_builder
    print("  [OK] media")
except Exception as e:
    print(f"  [FAIL] media: {e}")
    import traceback
    traceback.print_exc()

try:
    # 测试顶层
    from server.modules.streamcap import get_platform_handler
    print("  [OK] streamcap (顶层)")
except Exception as e:
    print(f"  [FAIL] streamcap: {e}")
    import traceback
    traceback.print_exc()

print("\n测试完成!")

