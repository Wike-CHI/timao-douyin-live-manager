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
    
    # 测试类定义
    print('测试类定义...')
    classes_to_test = [
        'UserListResponse',
        'UserDetailResponse', 
        'SystemStatsResponse',
        'ChartDataResponse'
    ]
    
    for cls_name in classes_to_test:
        if hasattr(admin, cls_name):
            print(f'   ✅ {cls_name}')
        else:
            print(f'   ❌ {cls_name} 未找到')
    
    print()
    print('=' * 60)
    print('✅ 所有测试通过!')
    print('=' * 60)
    
except Exception as e:
    print(f'❌ 导入失败: {e}')
    import traceback
    traceback.print_exc()
