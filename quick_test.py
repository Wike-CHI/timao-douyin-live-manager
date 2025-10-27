#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
print("Python路径:", sys.path[:3])

try:
    # 测试基础导入
    print("\n1. 测试基础模块...")
    from server.app.models.user import UserRoleEnum, UserStatusEnum
    print("   ✅ UserRoleEnum, UserStatusEnum")
    
    # 测试EmailStr
    print("\n2. 测试Pydantic...")
    try:
        from pydantic import EmailStr
        print("   ✅ EmailStr (from pydantic)")
    except ImportError:
        from pydantic.networks import EmailStr
        print("   ✅ EmailStr (from pydantic.networks)")
    
    # 测试admin模块
    print("\n3. 测试admin模块...")
    import server.app.api.admin as admin_module
    print("   ✅ admin模块导入成功")
    print(f"   Router: {admin_module.router.prefix}")
    
    print("\n" + "="*60)
    print("✅ 所有导入测试通过!")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
