# -*- coding: utf-8 -*-
"""
用户认证API路由
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]

from ...app.database import get_db_session
from ...app.services.user_service import UserService
from ...app.services.subscription_service import SubscriptionService
from ...app.models.user import UserRoleEnum, UserStatusEnum
from ...config import get_config
from ...utils.service_logger import log_user_action
from ...app.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    LoginResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    EmailVerifyRequest,
    RegisterResponse,
)
from ...app.schemas.common import BaseResponse
from ...app.utils.api import success_response


# 创建路由器
router = APIRouter(prefix="/api/auth", tags=["认证"])

# 创建logger
logger = logging.getLogger(__name__)

# HTTP Bearer 认证 (auto_error=False 允许query参数token)
security = HTTPBearer(auto_error=False)


# 依赖注入：获取当前用户
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token: Optional[str] = Query(None),  # 支持 URL query 参数（SSE/WebSocket）
    db: Session = Depends(get_db_session)
) -> Optional[dict]:
    """
    获取当前认证用户
    
    简化后的鉴权逻辑（KISS原则）：
    - 只使用JWT验证
    - 支持Header（标准）和Query参数（SSE/WebSocket）
    - 清晰的错误信息
    """
    # 1. 获取token（优先Header，其次Query参数）
    token_value = None
    if credentials:
        token_value = credentials.credentials
    elif token:
        token_value = token
    
    if not token_value:
        raise HTTPException(status_code=401, detail="未提供认证token")
    
    # 2. JWT验证
    try:
        from ...app.core.security import JWTManager
        
        payload = JWTManager.verify_token(token_value, "access")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Token中缺少用户ID")
        
        # 3. 获取用户信息
        user = UserService.get_user_by_id(int(user_id), session=db)
        
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        
        if user.status in [UserStatusEnum.BANNED, UserStatusEnum.SUSPENDED]:
            raise HTTPException(status_code=403, detail=f"用户账号已{user.status.value}")
        
        # 4. 返回用户数据
        return {
            "id": user.id,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "status": user.status.value if hasattr(user.status, 'value') else str(user.status)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JWT验证失败: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )


# API 路由
@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: UserRegisterRequest,
    req: Request,
    db: Session = Depends(get_db_session)
):
    """用户注册"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"📝 开始注册用户: {request.username}, {request.email}")
        
        user = UserService.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            phone=request.phone,
            nickname=request.nickname,
            session=db  # 使用传入的数据库会话
        )
        
        db.commit()  # 提交事务
        db.refresh(user)  # 刷新用户对象
        
        logger.info(f"✅ 用户注册成功: {user.username} (ID: {user.id})")
        log_user_action("注册", user_id=user.id, username=user.username, email=user.email)
        
        return RegisterResponse(
            success=True,
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
        
    except ValueError as e:
        logger.warning(f"⚠️ 注册失败 - 业务错误: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ 注册失败 - 系统错误: {type(e).__name__}: {e}", exc_info=True)
        db.rollback()
        
        # 处理数据库唯一性约束错误
        error_str = str(e)
        if "Duplicate entry" in error_str:
            if "username" in error_str.lower():
                detail = "用户名已存在，请选择其他用户名"
            elif "email" in error_str.lower():
                detail = "邮箱已被注册，请使用其他邮箱"
            elif "phone" in error_str.lower():
                detail = "手机号已被注册，请使用其他手机号"
            else:
                detail = "注册信息已存在，请检查用户名、邮箱或手机号"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
async def login_user(
    request: UserLoginRequest,
    req: Request,
    db: Session = Depends(get_db_session)
):
    """用户登录"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # 开发模式：强制禁用演示模式，使用真实用户系统
        # 不再检查 config.demo.enabled，始终使用真实用户登录
        
        logger.info(f"🔍 开始登录流程，用户名/邮箱: {request.username_or_email}")
        
        # 获取客户端IP
        client_ip = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent")
        logger.info(f"🌐 客户端信息 - IP: {client_ip}, User-Agent: {user_agent}")
        logger.info(f"📝 登录请求详情 - 用户名/邮箱: {request.username_or_email}, 记住我: {request.remember_me}")
        
        # 认证用户
        logger.info("🔐 开始用户认证...")
        try:
            user = UserService.authenticate_user(
                username_or_email=request.username_or_email,
                password=request.password,
                ip_address=client_ip
            )
        except ValueError as e:
            # 账户被锁定或其他业务错误
            logger.warning(f"❌ 用户认证失败（业务错误）: {request.username_or_email} - {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
        
        if not user:
            logger.warning(f"❌ 用户认证失败: {request.username_or_email}（用户名/密码错误或用户不存在）")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名/邮箱或密码错误"
            )
        
        logger.info(f"✅ 用户认证成功: {user.username} (ID: {user.id})")
        
        # 创建JWT token而不是session token
        logger.info(f"🔑 开始创建JWT token... (记住我: {request.remember_me})")
        from ...app.core.security import JWTManager
        from datetime import timedelta
        
        # 根据 remember_me 设置不同的 token 有效期
        if request.remember_me:
            # 勾选"记住我"：长期有效
            access_token_expires = timedelta(hours=8)  # 8小时
            refresh_token_expires = timedelta(days=3650)  # 10年
            logger.info("✅ 长期登录模式：Access Token 8小时，Refresh Token 10年")
        else:
            # 未勾选"记住我"：短期有效
            access_token_expires = timedelta(hours=1)  # 1小时
            refresh_token_expires = timedelta(days=1)  # 1天
            logger.info("✅ 短期登录模式：Access Token 1小时，Refresh Token 1天")
        
        # 生成JWT access token和refresh token
        access_token = JWTManager.create_access_token(
            data={"sub": str(user.id)}, 
            expires_delta=access_token_expires
        )
        refresh_token = JWTManager.create_refresh_token(
            data={"sub": str(user.id)},
            expires_delta=refresh_token_expires
        )
        logger.info("✅ JWT token创建成功")
        
        # 获取用户订阅信息
        logger.info("📊 获取用户订阅信息...")
        subscription_info = SubscriptionService.get_usage_stats(user.id)
        logger.info(f"✅ 订阅信息获取成功: {subscription_info}")
        
        # 计算用户支付状态
        has_subscription = subscription_info.get('has_subscription', False)
        subscription_status = subscription_info.get('status') or subscription_info.get('subscription_status')
        is_paid = has_subscription or subscription_status == 'active'
        ai_usage = subscription_info.get("ai_usage", {
            'requests_used': 0,
            'requests_limit': 0,
            'tokens_used': 0,
            'tokens_limit': 0,
            'first_free_used': False
        })
        first_free_used = ai_usage.get('first_free_used', False)
        
        logger.info("📦 构建登录响应...")
        log_user_action("登录", user_id=user.id, username=user.username, is_paid=is_paid)
        return LoginResponse(
            success=True,
            token=access_token,  # 前端期望的字段名
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=86400,
            isPaid=is_paid,
            firstFreeUsed=first_free_used,
            aiUsage=ai_usage,
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
        
    except HTTPException:
        # HTTPException 应该直接传播，不能被捕获
        raise
    except ValueError as e:
        logger.error(f"❌ 登录验证错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"💥 登录过程中发生未知错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.get("/demo-status", response_model=BaseResponse[Dict[str, Any]])
async def demo_status():
    """检查演示模式状态（开发模式：强制禁用）"""
    # 开发模式：强制禁用演示模式
    logging.info("📊 演示模式状态检查: 强制禁用演示模式（开发模式）")
    return success_response({
        "demo_enabled": False,
        "demo_user_name": None,
        "demo_user_email": None,
        "demo_user_nickname": None,
    })


@router.post("/demo-login", response_model=LoginResponse)
async def demo_login():
    """演示模式登录（已禁用）"""
    # 开发模式：强制禁用演示模式登录
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="演示模式已禁用，请使用真实用户账号登录"
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db_session)
):
    """刷新访问令牌"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from ...app.core.security import JWTManager
        config = get_config()
        
        # 验证refresh token
        try:
            payload = JWTManager.verify_token(request.refresh_token, "refresh")
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的刷新令牌"
                )
        except:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        # 开发模式：不再支持演示模式用户，所有用户都必须真实注册
        
        # 获取用户信息
        user = UserService.get_user_by_id(int(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )
        
        # 生成新的JWT tokens
        new_access_token = JWTManager.create_access_token(data={"sub": str(user.id)})
        new_refresh_token = JWTManager.create_refresh_token(data={"sub": str(user.id)})
        
        # 获取用户订阅信息
        subscription_info = SubscriptionService.get_usage_stats(user.id)
        has_subscription = subscription_info.get('has_subscription', False)
        subscription_status = subscription_info.get('status') or subscription_info.get('subscription_status')
        is_paid = has_subscription or subscription_status == 'active'
        ai_usage = subscription_info.get("ai_usage", {
            'requests_used': 0,
            'requests_limit': 0,
            'tokens_used': 0,
            'tokens_limit': 0,
            'first_free_used': False
        })
        first_free_used = ai_usage.get('first_free_used', False)
        
        return LoginResponse(
            success=True,
            token=new_access_token,
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=86400,
            isPaid=is_paid,
            firstFreeUsed=first_free_used,
            aiUsage=ai_usage,
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
        
    except HTTPException:
        # HTTPException 应该直接传播
        raise
    except Exception as e:
        # 添加详细的日志记录
        logger.error(f"❌ 刷新令牌失败: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"刷新令牌失败: {str(e)}"
        )


@router.post("/logout", response_model=BaseResponse[Dict[str, Any]])
async def logout_user(
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session)
):
    """用户登出"""
    try:
        token = credentials.credentials
        success = UserService.logout_user(token)
        
        if success:
            return success_response({"logout": True}, message="登出成功")
        return success_response({"logout": False}, message="登出失败")
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失败"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取当前用户信息"""
    try:
        user = UserService.get_user_by_id(current_user["id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return UserResponse(
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
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )


@router.post("/change-password", response_model=BaseResponse[Dict[str, Any]])
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """修改密码"""
    try:
        success = UserService.change_password(
            user_id=current_user["id"],
            old_password=request.old_password,
            new_password=request.new_password
        )
        
        if success:
            return success_response({"password_changed": True}, message="密码修改成功，请重新登录")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码修改失败"
        )


@router.post("/verify-email", response_model=BaseResponse[Dict[str, Any]])
async def verify_email(
    request: EmailVerifyRequest,
    db: Session = Depends(get_db_session)
):
    """验证邮箱"""
    try:
        success = UserService.verify_email(request.token)
        
        if success:
            return success_response({"email_verified": True}, message="邮箱验证成功")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的验证令牌"
        )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="邮箱验证失败"
        )





@router.post("/useFree", response_model=BaseResponse[Dict[str, Any]])
async def use_first_free(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """使用首次免费额度"""
    try:
        user_id = current_user["id"]
        # 检查用户订阅信息
        subscription_info = SubscriptionService.get_usage_stats(user_id)
        ai_usage = subscription_info.get("ai_usage", {})
        first_free_used = ai_usage.get('first_free_used', False)
        
        return success_response(
            {
                "firstFreeUsed": first_free_used,
                "aiUsage": ai_usage,
            },
            message="首次免费额度已使用" if first_free_used else "首次免费额度可用",
        )
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="使用首次免费额度失败"
        )


@router.get("/stats", response_model=BaseResponse[Dict[str, Any]])
async def get_user_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取用户统计信息"""
    try:
        stats = UserService.get_user_stats(current_user["id"])
        return success_response(stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )
