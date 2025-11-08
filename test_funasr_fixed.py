#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 FunASR 导入 - 修复环境变量设置"""

import os
import sys

# ⚠️ 关键：必须在导入任何其他模块之前设置环境变量
os.environ["UMAP_DONT_USE_NUMBA"] = "1"
os.environ["NUMBA_DISABLE_JIT"] = "1"

print("=" * 60)
print("环境变量设置:")
print(f"  UMAP_DONT_USE_NUMBA = {os.environ.get('UMAP_DONT_USE_NUMBA')}")
print(f"  NUMBA_DISABLE_JIT = {os.environ.get('NUMBA_DISABLE_JIT')}")
print()

print("Python 版本:", sys.version)
print("Python 路径:", sys.executable)
print()

print("=" * 60)
print("测试 FunASR 导入...")
try:
    import funasr
    print("✅ FunASR 导入成功")
    print("FunASR 模块路径:", funasr.__file__)
    if hasattr(funasr, '__version__'):
        print("FunASR 版本:", funasr.__version__)
    
    # 测试 AutoModel
    try:
        from funasr import AutoModel
        print("✅ AutoModel 导入成功")
        print()
        print("🎉 FunASR 完全可用！")
    except Exception as e:
        print(f"❌ AutoModel 导入失败: {e}")
except ImportError as e:
    print(f"❌ FunASR 导入失败: {e}")
except Exception as e:
    print(f"❌ FunASR 导入时发生错误: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)

