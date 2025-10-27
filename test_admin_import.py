#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试admin模块导入"""

try:
    print('测试导入 admin 模块...')
    from server.app.api import admin
    print('✅ admin 模块导入成功!')
    print(f'   Router prefix: {admin.router.prefix}')
    print(f'   Tags: {admin.router.tags}')
    print()
    
    print('测试其他API模块...')
    from server.app.api import auth
    print('✅ auth 模块导入成功')
    
    from server.app.api import payment
    print('✅ payment 模块导入成功')
    
    from server.app.api import subscription
    print('✅ subscription 模块导入成功')
    
    print()
    print('=' * 60)
    print('✅ 所有管理相关模块导入测试通过!')
    print('=' * 60)
    
except ImportError as e:
    print(f'❌ 导入失败: {e}')
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f'❌ 发生错误: {e}')
    import traceback
    traceback.print_exc()
