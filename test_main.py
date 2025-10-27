#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试FastAPI启动"""
import sys
import os

# 确保工作目录正确
os.chdir(r'd:\gsxm\timao-douyin-live-manager')
sys.path.insert(0, r'd:\gsxm\timao-douyin-live-manager')

print("="*60)
print("测试管理员模块导入")
print("="*60)
print()

try:
    print("1. 导入server.app.main...")
    from server.app import main
    print("   ✅ main模块导入成功")
    
    print("\n2. 检查路由加载...")
    print(f"   App title: {main.app.title}")
    print(f"   已注册路由数: {len(main.app.routes)}")
    
    # 查找admin路由
    admin_routes = [r for r in main.app.routes if hasattr(r, 'path') and '/admin' in r.path]
    if admin_routes:
        print(f"   ✅ admin路由已加载: {len(admin_routes)}个端点")
        for route in admin_routes[:3]:
            print(f"      - {route.path}")
    else:
        print("   ⚠️ 未找到admin路由")
    
    print("\n" + "="*60)
    print("✅ 测试完成!")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
