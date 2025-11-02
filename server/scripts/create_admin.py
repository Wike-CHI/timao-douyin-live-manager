#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建默认管理员账号脚本
使用方法: 
  1. 从项目根目录: python server/scripts/create_admin.py
  2. 或: python -m server.scripts.create_admin
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 再添加项目父目录（server的父目录）
PARENT_ROOT = PROJECT_ROOT.parent
if str(PARENT_ROOT) not in sys.path:
    sys.path.insert(0, str(PARENT_ROOT))

try:
    from server.app.database import db_manager, init_database
    from server.app.models.user import User, UserRoleEnum, UserStatusEnum
    from server.app.services.user_service import UserService
    import logging
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"请从项目根目录运行此脚本")
    print(f"当前工作目录: {Path.cwd()}")
    print(f"项目根目录: {PARENT_ROOT}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_user():
    """创建默认管理员账号"""
    if not db_manager:
        logger.error("数据库未初始化")
        return False
    
    # 获取数据库会话
    db = db_manager.get_session_sync()
    
    try:
        # 检查是否已存在管理员账号
        existing_admin = db.query(User).filter(
            User.role.in_([UserRoleEnum.ADMIN, UserRoleEnum.SUPER_ADMIN])
        ).first()
        
        if existing_admin:
            logger.info(f"已存在管理员账号: {existing_admin.username} (角色: {existing_admin.role.value})")
            logger.info(f"邮箱: {existing_admin.email}")
            return True
        
        # 创建默认超级管理员账号
        default_username = "admin"
        default_email = "admin@timao.com"
        default_password = "admin123456"
        default_nickname = "超级管理员"
        
        # 检查用户名和邮箱是否已存在
        existing_user = db.query(User).filter(
            (User.username == default_username) | (User.email == default_email)
        ).first()
        
        if existing_user:
            logger.warning(f"用户名或邮箱已存在: {existing_user.username}")
            # 更新为超级管理员
            existing_user.role = UserRoleEnum.SUPER_ADMIN
            existing_user.status = UserStatusEnum.ACTIVE
            existing_user.is_active = True
            db.commit()
            logger.info(f"已将用户 {existing_user.username} 更新为超级管理员")
            logger.info(f"默认密码: {default_password}")
            return True
        
        # 创建新管理员账号
        admin_user = UserService.create_user(
            username=default_username,
            email=default_email,
            password=default_password,
            nickname=default_nickname,
            role=UserRoleEnum.SUPER_ADMIN,
            session=db
        )
        
        db.commit()
        db.refresh(admin_user)
        
        logger.info("=" * 50)
        logger.info("✅ 超级管理员账号创建成功！")
        logger.info("=" * 50)
        logger.info(f"用户名: {default_username}")
        logger.info(f"邮箱: {default_email}")
        logger.info(f"密码: {default_password}")
        logger.info(f"角色: {admin_user.role.value}")
        logger.info("=" * 50)
        logger.info("⚠️  请尽快登录并修改默认密码！")
        logger.info("=" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"创建管理员账号失败: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    # 初始化数据库
    logger.info("正在初始化数据库...")
    try:
        init_database()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        sys.exit(1)
    
    if not db_manager:
        logger.error("数据库管理器未创建")
        sys.exit(1)
    
    success = create_admin_user()
    sys.exit(0 if success else 1)

