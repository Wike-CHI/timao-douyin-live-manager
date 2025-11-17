"""
云端认证路由 - 直接使用CRUD操作
不依赖UserService，直接操作数据库
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import or_

from ..db.crud import UserCRUD
from ...app.models.user import User, UserRoleEnum, UserStatusEnum
from ...app.core.security import JWTManager

router = APIRouter(prefix="/api/auth", tags=["认证"])
logger = logging.getLogger(__name__)


# 请求/响应模型
class LoginRequest(BaseModel):
    username_or_email: str
    password: str
    remember_me: bool = True


class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    nickname: Optional[str] = None
    role: str
    status: str
    ai_quota_monthly: int
    ai_quota_used: int
    created_at: Optional[str] = None


class LoginResponse(BaseModel):
    success: bool
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserInfo


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    nickname: Optional[str] = None


class RegisterResponse(BaseModel):
    success: bool
    user: UserInfo


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, req: Request):
    """用户登录"""
    try:
        logger.info(f"🔍 登录请求: {request.username_or_email}")
        
        user_crud = UserCRUD()
        client_ip = req.client.host if req.client else "unknown"
        
        # 查询用户
        with user_crud.get_session() as session:
            user = session.query(User).filter(
                or_(User.username == request.username_or_email, User.email == request.username_or_email),
                User.is_deleted == False
            ).first()
            
            if not user:
                logger.warning(f"❌ 用户不存在: {request.username_or_email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名/邮箱或密码错误"
                )
            
            # 检查账户是否被锁定
            if user.locked_until and user.locked_until > datetime.utcnow():
                logger.warning(f"❌ 账户已锁定: {request.username_or_email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"账户已被锁定，请{int((user.locked_until - datetime.utcnow()).total_seconds() / 60)}分钟后再试"
                )
            
            # 验证密码
            if not user.verify_password(request.password):
                logger.warning(f"❌ 密码错误: {request.username_or_email}")
                user.failed_login_count += 1
                
                # 失败5次锁定30分钟
                if user.failed_login_count >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                    logger.warning(f"⚠️  账户已锁定: {request.username_or_email}")
                
                session.commit()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名/邮箱或密码错误"
                )
            
            # 检查账户状态
            if user.status == UserStatusEnum.BANNED:
                raise HTTPException(status_code=403, detail="账户已被封禁")
            elif user.status == UserStatusEnum.SUSPENDED:
                raise HTTPException(status_code=403, detail="账户已被暂停")
            
            # 登录成功，更新登录信息
            user.failed_login_count = 0
            user.locked_until = None
            user.last_login_at = datetime.utcnow()
            user.last_login_ip = client_ip
            user.login_count += 1
            
            # 提交更新
            session.commit()
            session.refresh(user)
            
            # 生成JWT token
            access_token_expires = timedelta(hours=8 if request.remember_me else 1)
            refresh_token_expires = timedelta(days=30 if request.remember_me else 7)
            
            access_token = JWTManager.create_access_token(
                data={"sub": str(user.id), "username": user.username},
                expires_delta=access_token_expires
            )
            
            refresh_token = JWTManager.create_refresh_token(
                data={"sub": str(user.id)},
                expires_delta=refresh_token_expires
            )
            
            logger.info(f"✅ 登录成功: {user.username} (ID: {user.id})")
            
            return LoginResponse(
                success=True,
                access_token=access_token,
                refresh_token=refresh_token,
                user=UserInfo(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    nickname=user.nickname,
                    role=user.role.value if hasattr(user.role, 'value') else str(user.role),
                    status=user.status.value if hasattr(user.status, 'value') else str(user.status),
                    ai_quota_monthly=user.ai_quota_monthly or 0,
                    ai_quota_used=user.ai_quota_used or 0,
                    created_at=user.created_at.isoformat() if user.created_at else None
                )
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 登录失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """用户注册"""
    try:
        logger.info(f"📝 注册请求: {request.username}, {request.email}")
        
        user_crud = UserCRUD()
        
        with user_crud.get_session() as session:
            # 检查用户名和邮箱是否已存在
            existing = session.query(User).filter(
                or_(User.username == request.username, User.email == request.email),
                User.is_deleted == False
            ).first()
            
            if existing:
                if existing.username == request.username:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="用户名已存在"
                    )
                if existing.email == request.email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="邮箱已被注册"
                    )
            
            # 创建新用户
            user = User(
                username=request.username,
                email=request.email,
                phone=request.phone,
                nickname=request.nickname or request.username,
                role=UserRoleEnum.USER,
                status=UserStatusEnum.ACTIVE,
                ai_quota_monthly=1000,  # 默认每月1000次
                ai_quota_used=0
            )
            user.set_password(request.password)
            
            session.add(user)
            session.flush()
            
            logger.info(f"✅ 注册成功: {user.username} (ID: {user.id})")
            
            return RegisterResponse(
                success=True,
                user=UserInfo(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    nickname=user.nickname,
                    role=user.role.value if hasattr(user.role, 'value') else str(user.role),
                    status=user.status.value if hasattr(user.status, 'value') else str(user.status),
                    ai_quota_monthly=user.ai_quota_monthly or 0,
                    ai_quota_used=user.ai_quota_used or 0,
                    created_at=user.created_at.isoformat() if user.created_at else None
                )
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 注册失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


@router.get("/test-db")
async def test_database():
    """测试数据库连接"""
    try:
        user_crud = UserCRUD()
        with user_crud.get_session() as session:
            from sqlalchemy import func
            count = session.query(func.count(User.id)).filter(User.is_deleted == False).scalar()
            return {
                "success": True,
                "message": "数据库连接正常",
                "user_count": count
            }
    except Exception as e:
        logger.error(f"数据库测试失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据库连接失败: {str(e)}"
        )
