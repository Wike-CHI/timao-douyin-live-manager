#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("测试 base.py 导入...")
try:
    from server.modules.streamcap.platforms.platform_handlers.base import PlatformHandler
    print("  [OK] PlatformHandler")
except Exception as e:
    print(f"  [FAIL]: {e}")
    import traceback
    traceback.print_exc()

