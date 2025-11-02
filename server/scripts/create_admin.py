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
    # 先加载环境变量
    from dotenv import load_dotenv
    load_dotenv()
    
    from server.app.database import db_manager, init_database
    from server.app.models.user import User, UserRoleEnum, UserStatusEnum
    from server.app.services.user_service import UserService
    from server.config import config_manager
    import logging
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"请从项目根目录运行此脚本")
    print(f"当前工作目录: {Path.cwd()}")
    print(f"项目根目录: {PARENT_ROOT}")
    import traceback
    traceback.print_exc()
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
        
        # 硬编码的超级管理员账号
        hardcoded_admin = {
            "username": "tc1102Admin",
            "email": "tc1102admin@timao.com",
            "password": "xjystimao1115",
            "nickname": "超级管理员"
        }
        
        # 检查硬编码管理员账号是否存在
        existing_hardcoded = db.query(User).filter(
            User.username == hardcoded_admin["username"]
        ).first()
        
        if existing_hardcoded:
            # 如果存在，更新为超级管理员并重置密码
            logger.info(f"硬编码管理员账号已存在: {hardcoded_admin['username']}")
            existing_hardcoded.role = UserRoleEnum.SUPER_ADMIN
            existing_hardcoded.status = UserStatusEnum.ACTIVE
            existing_hardcoded.is_active = True
            existing_hardcoded.set_password(hardcoded_admin["password"])
            existing_hardcoded.email = hardcoded_admin["email"]
            existing_hardcoded.nickname = hardcoded_admin["nickname"]
            db.commit()
            db.refresh(existing_hardcoded)
            logger.info(f"✅ 硬编码管理员账号已更新为超级管理员")
            logger.info(f"用户名: {hardcoded_admin['username']}")
            logger.info(f"密码: {hardcoded_admin['password']}")
            return True
        
        # 创建硬编码管理员账号
        try:
            hardcoded_user = UserService.create_user(
                username=hardcoded_admin["username"],
                email=hardcoded_admin["email"],
                password=hardcoded_admin["password"],
                nickname=hardcoded_admin["nickname"],
                role=UserRoleEnum.SUPER_ADMIN,
                session=db
            )
            
            db.commit()
            db.refresh(hardcoded_user)
            
            logger.info("=" * 60)
            logger.info("✅ 硬编码超级管理员账号创建成功！")
            logger.info("=" * 60)
            logger.info(f"用户名: {hardcoded_admin['username']}")
            logger.info(f"邮箱: {hardcoded_admin['email']}")
            logger.info(f"密码: {hardcoded_admin['password']}")
            logger.info(f"角色: {hardcoded_user.role.value}")
            logger.info("=" * 60)
            
        except ValueError as e:
            logger.error(f"创建硬编码管理员失败: {str(e)}")
            db.rollback()
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"创建管理员账号失败: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    # 初始化数据库
    logger.info("=" * 60)
    logger.info("🚀 开始创建管理员账号")
    logger.info("=" * 60)
    logger.info("正在初始化数据库...")
    try:
        # 从配置管理器获取数据库配置
        db_config = config_manager.config.database
        logger.info(f"📊 数据库类型: {db_config.db_type}")
        logger.info(f"📊 数据库主机: {db_config.mysql_host}:{db_config.mysql_port}")
        logger.info(f"📊 数据库名: {db_config.mysql_database}")
        logger.info(f"📊 数据库用户: {db_config.mysql_user}")
        
        init_database(db_config)
        logger.info("✅ 数据库初始化完成")
        
        # 重新导入以获取更新后的db_manager
        from server.app.database import db_manager as updated_db_manager
        
        if not updated_db_manager:
            logger.error("❌ 数据库管理器未创建")
            sys.exit(1)
        
        # 使用更新后的db_manager
        global db_manager
        db_manager = updated_db_manager
        logger.info("✅ 数据库连接已建立")
            
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    logger.info("=" * 60)
    success = create_admin_user()
    logger.info("=" * 60)
    
    if success:
        logger.info("✅ 脚本执行成功！")
    else:
        logger.error("❌ 脚本执行失败！")
    
    sys.exit(0 if success else 1)

