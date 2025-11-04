#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建超级管理员开发账号脚本
用于开发和调试测试功能
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from server.app.services.user_service import UserService
from server.app.models.user import UserRoleEnum, UserStatusEnum
from server.app.database import db_session, init_database
from server.config import config_manager


def create_super_admin():
    """创建超级管理员开发账号"""
    
    # 超级管理员账号信息
    admin_data = {
        "username": "dev_admin",
        "email": "dev_admin@timao.local",
        "password": "DevAdmin@2024!",
        "nickname": "开发超级管理员",
        "phone": None,
        "role": UserRoleEnum.SUPER_ADMIN
    }
    
    print("🚀 开始创建超级管理员开发账号...")
    print(f"用户名: {admin_data['username']}")
    print(f"邮箱: {admin_data['email']}")
    print(f"角色: {admin_data['role'].value}")
    print("-" * 50)
    
    try:
        # 检查是否已存在
        with db_session() as session:
            existing_user = UserService.get_user_by_username(admin_data["username"], session)
            if existing_user:
                print(f"❌ 用户名 '{admin_data['username']}' 已存在")
                print(f"   用户ID: {existing_user.id}")
                print(f"   角色: {existing_user.role.value}")
                print(f"   状态: {existing_user.status.value}")
                print(f"   创建时间: {existing_user.created_at}")
                
                # 询问是否更新为超级管理员
                if existing_user.role != UserRoleEnum.SUPER_ADMIN:
                    response = input("\n是否将现有用户升级为超级管理员? (y/N): ").strip().lower()
                    if response == 'y':
                        existing_user.role = UserRoleEnum.SUPER_ADMIN
                        existing_user.status = UserStatusEnum.ACTIVE
                        existing_user.ai_unlimited = True  # 无限AI配额
                        session.commit()
                        print("✅ 用户已升级为超级管理员")
                    else:
                        print("❌ 操作已取消")
                else:
                    print("✅ 用户已经是超级管理员")
                return existing_user
            
            existing_email = UserService.get_user_by_email(admin_data["email"], session)
            if existing_email:
                print(f"❌ 邮箱 '{admin_data['email']}' 已存在")
                return None
        
        # 创建新的超级管理员
        print("📝 创建新的超级管理员账号...")
        
        user = UserService.create_user(
            username=admin_data["username"],
            email=admin_data["email"],
            password=admin_data["password"],
            phone=admin_data["phone"],
            nickname=admin_data["nickname"],
            role=admin_data["role"]
        )
        
        # 设置特殊权限
        with db_session() as session:
            db_user = session.query(UserService.get_user_by_id.__annotations__['return'].__args__[0]).filter_by(id=user.id).first()
            if db_user:
                db_user.ai_unlimited = True  # 无限AI配额
                db_user.status = UserStatusEnum.ACTIVE  # 确保激活状态
                session.commit()
        
        print("✅ 超级管理员账号创建成功!")
        print(f"   用户ID: {user.id}")
        print(f"   用户名: {user.username}")
        print(f"   邮箱: {user.email}")
        print(f"   昵称: {user.nickname}")
        print(f"   角色: {user.role.value}")
        print(f"   状态: {user.status.value}")
        print(f"   创建时间: {user.created_at}")
        print(f"   无限AI配额: 是")
        
        print("\n🔐 登录信息:")
        print(f"   用户名/邮箱: {user.username} 或 {user.email}")
        print(f"   密码: {admin_data['password']}")
        
        print("\n🎯 权限说明:")
        print("   - 超级管理员拥有系统所有权限")
        print("   - 可以管理所有用户和数据")
        print("   - 拥有无限AI配额")
        print("   - 可以访问所有管理功能")
        
        return user
        
    except ValueError as e:
        print(f"❌ 创建失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 创建过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def verify_admin_login():
    """验证超级管理员登录"""
    print("\n🔍 验证超级管理员登录...")
    
    try:
        user = UserService.authenticate_user("dev_admin", "DevAdmin@2024!")
        if user:
            print("✅ 登录验证成功!")
            print(f"   用户ID: {user.id}")
            print(f"   用户名: {user.username}")
            print(f"   角色: {user.role.value}")
            print(f"   状态: {user.status.value}")
            
            # 检查权限
            if user.has_permission("admin"):
                print("✅ 管理员权限验证通过")
            else:
                print("⚠️  管理员权限验证失败")
                
            return True
        else:
            print("❌ 登录验证失败")
            return False
            
    except Exception as e:
        print(f"❌ 登录验证过程中发生错误: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🐱 提猫直播助手 - 超级管理员开发账号创建工具")
    print("=" * 60)
    
    # 初始化数据库
    try:
        print("🔧 初始化数据库连接...")
        db_config = config_manager.config.database
        init_database(db_config)
        print("✅ 数据库初始化成功")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)
    
    # 创建超级管理员
    admin_user = create_super_admin()
    
    if admin_user:
        # 验证登录
        verify_admin_login()
        
        print("\n" + "=" * 60)
        print("🎉 超级管理员开发账号设置完成!")
        print("现在可以使用此账号进行开发和调试测试")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 超级管理员账号创建失败")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()