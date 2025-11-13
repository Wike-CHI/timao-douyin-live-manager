# -*- coding: utf-8 -*-
"""直接测试数据库查询"""
import sys
sys.path.insert(0, 'server')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.app.models.user import User, UserStatusEnum
from sqlalchemy import or_

# 数据库连接
DATABASE_URL = "mysql+pymysql://root:xjystimao1115@rm-cn-61k3u9f7n00052o.rwlb.rds.aliyuncs.com:3306/live_manager"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

def test_query():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("测试1: 简单查询所有用户")
        print("=" * 60)
        users = db.query(User).limit(5).all()
        print(f"查询成功! 找到 {len(users)} 个用户")
        for user in users:
            print(f"  - {user.username} ({user.email})")
        
        print("\n" + "=" * 60)
        print("测试2: 带搜索条件查询")
        print("=" * 60)
        search = "tc"
        search_pattern = f"%{search}%"
        users = db.query(User).filter(
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.nickname.ilike(search_pattern),
                User.phone.ilike(search_pattern)
            )
        ).all()
        print(f"搜索 '{search}' 找到 {len(users)} 个用户")
        for user in users:
            print(f"  - {user.username} ({user.email})")
        
        print("\n" + "=" * 60)
        print("测试3: 带is_active筛选")
        print("=" * 60)
        users = db.query(User).filter(User.status == UserStatusEnum.ACTIVE).limit(5).all()
        print(f"激活用户: {len(users)} 个")
        
    except Exception as e:
        print(f"错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_query()
