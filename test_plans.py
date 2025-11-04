#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试套餐查询"""
import sys
sys.path.insert(0, 'server')

from app.database import init_database, db_session
from app.models.payment import Plan
from config import config

# 初始化数据库
init_database(config.database)

# 使用上下文管理器获取会话
with db_session() as session:
    # 查询所有套餐
    all_plans = session.query(Plan).all()
    print(f"数据库中所有套餐数量: {len(all_plans)}")
    
    # 查询激活的套餐
    active_plans = session.query(Plan).filter_by(is_active=True).all()
    print(f"激活的套餐数量: {len(active_plans)}")
    
    print("\n套餐详情:")
    for plan in all_plans:
        print(f"  ID={plan.id}, 名称={plan.name}, 类型={plan.plan_type}, 价格={plan.price}, 激活={plan.is_active}")

