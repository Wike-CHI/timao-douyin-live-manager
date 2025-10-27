# -*- coding: utf-8 -*-
"""
用户认证API路由
"""

from datetime import datetime
import secrets
from typing import Optional, Dict, Any
import re
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session

from server.app.database import get_db_session
from server.app.services.user_service import UserService
from server.app.services.subscription_service import SubscriptionService
from server.app.models.user import UserRoleEnum, UserStatusEnum


# 创建路由器
router = APIRouter(prefix="/api/auth", tags=["认证"])

# HTTP Bearer 认证
security = HTTPBearer()


# Pydantic 模型
class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    email: EmailStr
    password: str
    nickname: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None
    
    @validator('username', pre=True, always=True)
    def validate_or_generate_username(cls, v, values):
        candidate = (v or "").strip()
        email = values.get("email")
        nickname = (values.get("nickname") or "").strip()
        
        if not candidate:
            if nickname:
                candidate = nickname
            elif email:
                candidate = email.split("@")[0]
        
        candidate = re.sub(r"[^A-Za-z0-9_-]", "", candidate or "")
        if len(candidate) < 3:
            candidate = f"user_{secrets.token_hex(3)}"
        candidate = candidate[:50]
        
        if len(candidate) < 3 or len(candidate) > 50:
            raise ValueError('用户名长度必须在3-50个字符之间')
        if not candidate.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return candidate
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6个字符')
        return v


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username_or_email: str
    password: str


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    nickname: Optional[str]
    avatar_url: Optional[str]
    role: str
    status: str
    email_verified: bool
    phone_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录响应模型"""
    success: bool = True
    token: str  # 前端期望的字段名
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24小时
    user: UserResponse
    isPaid: bool = False
    firstFreeUsed: bool = False
    aiUsage: Optional[Dict[str, Any]] = None


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6个字符')
        return v


class EmailVerifyRequest(BaseModel):
    """邮箱验证请求"""
    token: str


# 依赖注入：获取当前用户
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session)
) -> Optional[dict]:
    """获取当前认证用户"""
    try:
        token = credentials.credentials
        print(f"[DEBUG] 收到token: {token[:50]}...")
        
        # 首先尝试JWT token验证
        from server.app.core.security import JWTManager
        try:
            print("[DEBUG] 开始JWT token验证...")
            payload = JWTManager.verify_token(token, "access")
            print(f"[DEBUG] JWT payload: {payload}")
            
            user_id = payload.get("sub")
            print(f"[DEBUG] 从JWT获取user_id: {user_id} (类型: {type(user_id)})")
            
            if user_id:
                # 从数据库获取用户信息，确保user_id是整数类型，并传递session
                print(f"[DEBUG] 正在查询用户ID: {int(user_id)}")
                user = UserService.get_user_by_id(int(user_id), session=db)
                print(f"[DEBUG] 查询到用户: {user.username if user else 'None'}")
                
                if user and user.status not in [UserStatusEnum.BANNED, UserStatusEnum.SUSPENDED]:
                    print("[DEBUG] JWT验证成功，返回用户信息")
                    try:
                        user_data = {
                            "id": user.id,
                            "user_id": user.id,  # 添加 user_id 字段以兼容 useFree 接口
                            "username": user.username,
                            "email": user.email,
                            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                            "status": user.status.value if hasattr(user.status, 'value') else str(user.status)
                        }
                        print(f"[DEBUG] 构造的用户数据: {user_data}")
                        return user_data
                    except Exception as e:
                        print(f"[DEBUG] 构造用户数据时出错: {e}")
                        raise HTTPException(status_code=500, detail=f"构造用户数据失败: {str(e)}")
                else:
                    print(f"[DEBUG] 用户状态无效或被禁用: {user.status if user else 'None'}")
            else:
                print("[DEBUG] JWT payload中没有找到sub字段")
                
        except Exception as jwt_error:
            # JWT验证失败，尝试session token验证（向后兼容）
            print(f"[DEBUG] JWT验证失败: {str(jwt_error)}")
            print("[DEBUG] 尝试session token验证...")
            
            user = UserService.validate_session(token)
            if user:
                print("[DEBUG] Session token验证成功")
                return {
                    "id": user.id,
                    "user_id": user.id,  # 添加 user_id 字段以兼容 useFree 接口
                    "username": user.username,
                    "email": user.email,
                    "role": user.role.value,
                    "status": user.status.value
                }
            else:
                print("[DEBUG] Session token验证也失败")
        
        print("[DEBUG] 所有验证方式都失败，抛出401错误")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] 认证过程中发生异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )


# API 路由
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: UserRegisterRequest,
    req: Request,
    db: Session = Depends(get_db_session)
):
    """用户注册"""
    try:
        user = UserService.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            phone=request.phone,
            nickname=request.nickname
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
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
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
        logger.info(f"🔍 开始登录流程，用户名/邮箱: {request.username_or_email}")
        
        # 获取客户端IP
        client_ip = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent")
        logger.info(f"🌐 客户端信息 - IP: {client_ip}, User-Agent: {user_agent}")
        
        # 认证用户
        logger.info("🔐 开始用户认证...")
        user = UserService.authenticate_user(
            username_or_email=request.username_or_email,
            password=request.password,
            ip_address=client_ip
        )
        
        if not user:
            logger.warning(f"❌ 用户认证失败: {request.username_or_email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名/邮箱或密码错误"
            )
        
        logger.info(f"✅ 用户认证成功: {user.username} (ID: {user.id})")
        
        # 创建JWT token而不是session token
        logger.info("🔑 开始创建JWT token...")
        from server.app.core.security import JWTManager
        
        # 生成JWT access token和refresh token
        access_token = JWTManager.create_access_token(data={"sub": str(user.id)})
        refresh_token = JWTManager.create_refresh_token(data={"sub": str(user.id)})
        logger.info("✅ JWT token创建成功")
        
        # 获取用户订阅信息
        logger.info("📊 获取用户订阅信息...")
        # subscription_info = SubscriptionService.get_usage_stats(user.id)
        # logger.info(f"✅ 订阅信息获取成功: {subscription_info}")
        
        # 临时跳过订阅系统检查，直接设置为已付费状态
        subscription_info = {
            'has_subscription': True,
            'subscription_type': 'premium',
            'subscription_status': 'active',
            'ai_usage': {
                'requests_used': 0,
                'requests_limit': 10000,
                'tokens_used': 0,
                'tokens_limit': 1000000,
                'first_free_used': False
            }
        }
        logger.info("✅ 临时跳过订阅检查，设置为已付费状态")
        
        # 计算用户支付状态
        has_subscription = True  # 临时设置为True
        is_paid = True  # 临时设置为True
        ai_usage = subscription_info.get("ai_usage")
        first_free_used = False  # 临时设置为False，允许使用AI服务
        
        logger.info("📦 构建登录响应...")
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


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db_session)
):
    """刷新访问令牌"""
    try:
        from server.app.core.security import JWTManager
        
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
        
        # 临时跳过订阅系统检查，直接设置为已付费状态
        subscription_info = {
            'has_subscription': True,
            'subscription_type': 'premium',
            'subscription_status': 'active',
            'ai_usage': {
                'requests_used': 0,
                'requests_limit': 10000,
                'tokens_used': 0,
                'tokens_limit': 1000000,
                'first_free_used': False
            }
        }
        has_subscription = True
        ai_usage = subscription_info.get("ai_usage")
        first_free_used = False
        
        return LoginResponse(
            success=True,
            token=new_access_token,
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=86400,
            isPaid=has_subscription,
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
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌失败"
        )


@router.post("/logout")
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
            return {"message": "登出成功"}
        else:
            return {"message": "登出失败"}
            
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


@router.post("/change-password")
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
            return {"message": "密码修改成功，请重新登录"}
        else:
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


@router.post("/verify-email")
async def verify_email(
    request: EmailVerifyRequest,
    db: Session = Depends(get_db_session)
):
    """验证邮箱"""
    try:
        success = UserService.verify_email(request.token)
        
        if success:
            return {"message": "邮箱验证成功"}
        else:
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





@router.post("/useFree")
async def use_first_free(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """使用首次免费额度"""
    try:
        user_id = current_user["id"]
        # 临时跳过首次免费检查，直接返回成功
        return {
            "success": True,
            "firstFreeUsed": False,  # 临时设置为False，允许继续使用
            "aiUsage": {
                'requests_used': 0,
                'requests_limit': 10000,
                'tokens_used': 0,
                'tokens_limit': 1000000,
                'first_free_used': False
            }
        }
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="使用首次免费额度失败"
        )


@router.get("/stats")
async def get_user_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取用户统计信息"""
    try:
        stats = UserService.get_user_stats(current_user["id"])
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )
