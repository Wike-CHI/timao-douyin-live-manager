#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试登录API错误的脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from server.app.services.user_service import UserService
from server.app.services.subscription_service import SubscriptionService
from server.config import ConfigManager
from server.app.database import init_database, db_manager

def debug_login_process():
    """调试登录过程"""
    print("🚀 开始调试登录过程...")
    
    try:
        # 1. 初始化配置和数据库
        print("🔍 初始化配置和数据库...")
        config_manager = ConfigManager()
        init_database(config_manager.config.database)
        print("✅ 数据库已初始化")
        
        # 2. 测试用户认证
        print("\n🔍 测试用户认证...")
        try:
            user = UserService.authenticate_user(
                username_or_email="admin",
                password="admin123",
                ip_address="127.0.0.1"
            )
            
            if user:
                print(f"✅ 用户认证成功:")
                print(f"   - 用户ID: {user.id}")
                print(f"   - 用户名: {user.username}")
                print(f"   - 邮箱: {user.email}")
                print(f"   - 角色: {user.role}")
                print(f"   - 状态: {user.status}")
            else:
                print("❌ 用户认证失败")
                return
                
        except Exception as e:
            print(f"❌ 用户认证异常: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 3. 测试创建会话
        print("\n🔍 测试创建会话...")
        try:
            session = UserService.create_session(
                user=user,
                ip_address="127.0.0.1",
                user_agent="test-agent"
            )
            
            if session:
                print(f"✅ 会话创建成功:")
                print(f"   - 会话ID: {session.id}")
                print(f"   - 会话令牌: {session.session_token[:20]}...")
                print(f"   - 刷新令牌: {session.refresh_token[:20] if session.refresh_token else 'None'}...")
                print(f"   - 过期时间: {session.expires_at}")
            else:
                print("❌ 会话创建失败")
                return
                
        except Exception as e:
            print(f"❌ 会话创建异常: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 4. 测试订阅服务
        print("\n🔍 测试订阅服务...")
        try:
            subscription_info = SubscriptionService.get_usage_stats(user.id)
            print(f"✅ 订阅信息获取成功:")
            print(f"   - 订阅信息: {subscription_info}")
            
        except Exception as e:
            print(f"❌ 订阅信息获取异常: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 5. 测试完整登录响应构建
        print("\n🔍 测试完整登录响应构建...")
        try:
            from server.app.api.auth import LoginResponse, UserResponse
            
            # 计算用户支付状态
            has_subscription = subscription_info.get("has_subscription", False)
            is_paid = has_subscription
            
            response = LoginResponse(
                success=True,
                token=session.session_token,
                access_token=session.session_token,
                refresh_token=session.refresh_token,
                isPaid=is_paid,
                user=UserResponse(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    nickname=user.nickname,
                    avatar_url=user.avatar_url,
                    role=user.role.value,
                    status=user.status.value,
                    email_verified=user.email_verified,
                    phone_verified=user.phone_verified,
                    created_at=user.created_at
                )
            )
            
            print(f"✅ 登录响应构建成功:")
            print(f"   - 成功状态: {response.success}")
            print(f"   - 令牌: {response.token[:20]}...")
            print(f"   - 用户ID: {response.user.id}")
            print(f"   - 用户名: {response.user.username}")
            print(f"   - 支付状态: {response.isPaid}")
            
        except Exception as e:
            print(f"❌ 登录响应构建异常: {e}")
            import traceback
            traceback.print_exc()
            return
        
        print("\n✅ 所有登录步骤测试成功！")
        
    except Exception as e:
        print(f"❌ 调试过程异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_login_process()
    print("\n✅ 调试完成")