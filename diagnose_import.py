#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""诊断导入问题"""
import sys
import os

os.chdir(r'd:\gsxm\timao-douyin-live-manager')
sys.path.insert(0, r'd:\gsxm\timao-douyin-live-manager')

print("="*70)
print("诊断管理员模块导入问题")
print("="*70)
print()

try:
    print("Step 1: 导入 security...")
    from server.app.core import security
    print("   ✅ security 模块OK")
    
    print("\nStep 2: 导入 dependencies...")
    from server.app.core import dependencies
    print("   ✅ dependencies 模块OK")
    
    print("\nStep 3: 导入 admin...")
    from server.app.api import admin
    print("   ✅ admin 模块OK")
    print(f"   Router prefix: {admin.router.prefix}")
    
    print("\nStep 4: 导入 main...")
    from server.app import main
    print("   ✅ main 模块OK")
    
    print("\n" + "="*70)
    print("✅ 所有模块导入成功！")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ 导入失败: {e}")
    print("\n完整错误堆栈:")
    import traceback
    traceback.print_exc()
