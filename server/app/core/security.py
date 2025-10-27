# -*- coding: utf-8 -*-
"""
安全功能模块
包括密码策略、登录限制、会话管理、数据加密等
"""

import re
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from server.utils.redis_manager import get_redis, RedisManager
from server.config import RedisConfig
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    import warnings
    warnings.warn(
        "SECRET_KEY 未设置！使用默认值存在安全风险！\n"
        "请在 .env 文件中设置: SECRET_KEY=<64位随机字符串>",
        UserWarning
    )
    SECRET_KEY = "dev-secret-key-please-change-in-production-" + secrets.token_urlsafe(32)
    logger.warning("⚠️ SECRET_KEY 未设置，使用临时密钥（仅供开发使用）")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 统一通过 RedisManager 访问缓存（带内存回退）
# 注意：应用启动时会在 startup_event 中初始化 RedisManager
# 这里在运行期按需获取，若尚未初始化则临时使用内存字典

# 内存模式回退：若未初始化全局 RedisManager，则创建一个禁用Redis的本地实例
_fallback_rm: Optional[RedisManager] = None

def _get_rm() -> RedisManager:
    rm = get_redis()
    if rm:
        return rm
    global _fallback_rm
    if _fallback_rm is None:
        _fallback_rm = RedisManager(RedisConfig(enabled=False))
    return _fallback_rm


class PasswordPolicy:
    """密码策略类"""
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL_CHARS = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    @classmethod
    def validate_password(cls, password: str) -> tuple[bool, List[str]]:
        """
        验证密码是否符合策略
        
        Args:
            password: 待验证的密码
            
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 长度检查
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"密码长度至少{cls.MIN_LENGTH}位")
        if len(password) > cls.MAX_LENGTH:
            errors.append(f"密码长度不能超过{cls.MAX_LENGTH}位")
        
        # 字符类型检查
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("密码必须包含大写字母")
        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("密码必须包含小写字母")
        if cls.REQUIRE_DIGITS and not re.search(r'\d', password):
            errors.append("密码必须包含数字")
        if cls.REQUIRE_SPECIAL_CHARS and not re.search(f'[{re.escape(cls.SPECIAL_CHARS)}]', password):
            errors.append(f"密码必须包含特殊字符: {cls.SPECIAL_CHARS}")
        
        # 常见弱密码检查
        weak_patterns = [
            r'(.)\1{2,}',  # 连续相同字符
            r'(012|123|234|345|456|567|678|789|890)',  # 连续数字
            r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # 连续字母
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, password.lower()):
                errors.append("密码不能包含连续的字符或数字")
                break
        
        return len(errors) == 0, errors
    
    @classmethod
    def generate_secure_password(cls, length: int = 12) -> str:
        """生成安全密码"""
        if length < cls.MIN_LENGTH:
            length = cls.MIN_LENGTH
        
        # 确保包含所有必需的字符类型
        chars = ""
        password = ""
        
        if cls.REQUIRE_UPPERCASE:
            chars += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            password += secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        
        if cls.REQUIRE_LOWERCASE:
            chars += "abcdefghijklmnopqrstuvwxyz"
            password += secrets.choice("abcdefghijklmnopqrstuvwxyz")
        
        if cls.REQUIRE_DIGITS:
            chars += "0123456789"
            password += secrets.choice("0123456789")
        
        if cls.REQUIRE_SPECIAL_CHARS:
            chars += cls.SPECIAL_CHARS
            password += secrets.choice(cls.SPECIAL_CHARS)
        
        # 填充剩余长度
        for _ in range(length - len(password)):
            password += secrets.choice(chars)
        
        # 随机打乱
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        return ''.join(password_list)


class LoginLimiter:
    """登录限制器"""
    
    MAX_ATTEMPTS = 5  # 最大尝试次数
    LOCKOUT_DURATION = 900  # 锁定时间（秒）
    ATTEMPT_WINDOW = 300  # 尝试窗口时间（秒）
    
    @classmethod
    def _get_key(cls, identifier: str, attempt_type: str = "login") -> str:
        """获取存储键"""
        return f"limiter:{attempt_type}:{identifier}"
    
    @classmethod
    def _get_lockout_key(cls, identifier: str, attempt_type: str = "login") -> str:
        """获取锁定键"""
        return f"lockout:{attempt_type}:{identifier}"
    
    @classmethod
    def _store_get(cls, key: str) -> Optional[str]:
        """从存储获取值"""
        rm = _get_rm()
        return rm.get(key)
    
    @classmethod
    def _store_set(cls, key: str, value: str, expire: int = None):
        """存储值"""
        rm = _get_rm()
        rm.set(key, value, ttl=expire)
    
    @classmethod
    def _store_incr(cls, key: str, expire: int = None) -> int:
        """递增计数"""
        rm = _get_rm()
        count = rm.incr(key) or 0
        if expire and count == 1:
            rm.expire(key, expire)
        return count
    
    @classmethod
    def is_locked(cls, identifier: str, attempt_type: str = "login") -> bool:
        """检查是否被锁定"""
        lockout_key = cls._get_lockout_key(identifier, attempt_type)
        lockout_time = cls._store_get(lockout_key)
        
        if lockout_time:
            if time.time() < float(lockout_time):
                return True
            else:
                # 锁定时间已过，清除锁定
                rm = _get_rm()
                rm.delete(lockout_key)
        
        return False
    
    @classmethod
    def record_attempt(cls, identifier: str, success: bool, attempt_type: str = "login") -> Dict[str, Any]:
        """记录尝试"""
        if success:
            # 成功时清除计数
            attempt_key = cls._get_key(identifier, attempt_type)
            rm = _get_rm()
            rm.delete(attempt_key)
            return {"locked": False, "attempts": 0, "remaining": cls.MAX_ATTEMPTS}
        
        # 失败时增加计数
        attempt_key = cls._get_key(identifier, attempt_type)
        attempts = cls._store_incr(attempt_key, cls.ATTEMPT_WINDOW)
        
        remaining = max(0, cls.MAX_ATTEMPTS - attempts)
        
        if attempts >= cls.MAX_ATTEMPTS:
            # 达到最大尝试次数，锁定账户
            lockout_key = cls._get_lockout_key(identifier, attempt_type)
            lockout_until = time.time() + cls.LOCKOUT_DURATION
            cls._store_set(lockout_key, str(lockout_until), cls.LOCKOUT_DURATION)
            
            logger.warning(f"账户 {identifier} 因多次失败尝试被锁定")
            
            return {
                "locked": True,
                "attempts": attempts,
                "remaining": 0,
                "lockout_until": datetime.fromtimestamp(lockout_until).isoformat()
            }
        
        return {"locked": False, "attempts": attempts, "remaining": remaining}
    
    @classmethod
    def get_status(cls, identifier: str, attempt_type: str = "login") -> Dict[str, Any]:
        """获取限制状态"""
        if cls.is_locked(identifier, attempt_type):
            lockout_key = cls._get_lockout_key(identifier, attempt_type)
            lockout_time = cls._store_get(lockout_key)
            return {
                "locked": True,
                "lockout_until": datetime.fromtimestamp(float(lockout_time)).isoformat()
            }
        
        attempt_key = cls._get_key(identifier, attempt_type)
        attempts = int(cls._store_get(attempt_key) or 0)
        remaining = max(0, cls.MAX_ATTEMPTS - attempts)
        
        return {
            "locked": False,
            "attempts": attempts,
            "remaining": remaining
        }


class SessionManager:
    """会话管理器"""
    
    @classmethod
    def _get_session_key(cls, session_id: str) -> str:
        """获取会话键"""
        return f"session:{session_id}"
    
    @classmethod
    def _get_user_sessions_key(cls, user_id: str) -> str:
        """获取用户会话键"""
        return f"user_sessions:{user_id}"
    
    @classmethod
    def create_session(cls, user_id: str, user_data: Dict[str, Any], 
                      expire_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
        """创建会话"""
        session_id = secrets.token_urlsafe(32)
        session_key = cls._get_session_key(session_id)
        user_sessions_key = cls._get_user_sessions_key(user_id)
        
        session_data = {
            "user_id": user_id,
            "created_at": time.time(),
            "last_activity": time.time(),
            "user_data": user_data
        }
        
        expire_seconds = expire_minutes * 60
        rm = _get_rm()
        # 存储会话数据（统一用 JSON 序列化）
        rm.set(session_key, session_data, ttl=expire_seconds)
        # 添加到用户会话集合
        rm.sadd(user_sessions_key, session_id)
        rm.expire(user_sessions_key, expire_seconds)
        
        return session_id
    
    @classmethod
    def get_session(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        session_key = cls._get_session_key(session_id)
        rm = _get_rm()
        session_data = rm.get(session_key)
        if session_data:
            return session_data
        return None
    
    @classmethod
    def update_session_activity(cls, session_id: str) -> bool:
        """更新会话活动时间"""
        session_data = cls.get_session(session_id)
        if not session_data:
            return False
        
        session_data["last_activity"] = time.time()
        session_key = cls._get_session_key(session_id)
        rm = _get_rm()
        # 获取剩余过期时间
        ttl = rm.ttl(session_key)
        if ttl > 0:
            rm.set(session_key, session_data, ttl)
        else:
            rm.set(session_key, session_data)
        
        return True
    
    @classmethod
    def delete_session(cls, session_id: str) -> bool:
        """删除会话"""
        session_data = cls.get_session(session_id)
        if not session_data:
            return False
        
        user_id = session_data["user_id"]
        session_key = cls._get_session_key(session_id)
        user_sessions_key = cls._get_user_sessions_key(user_id)
        rm = _get_rm()
        rm.delete(session_key)
        rm.srem(user_sessions_key, session_id)
        
        return True
    
    @classmethod
    def delete_user_sessions(cls, user_id: str) -> int:
        """删除用户所有会话"""
        user_sessions_key = cls._get_user_sessions_key(user_id)
        rm = _get_rm()
        session_ids = rm.smembers(user_sessions_key)
        count = 0
        for session_id in session_ids:
            session_key = cls._get_session_key(session_id)
            if rm.delete(session_key):
                count += 1
        rm.delete(user_sessions_key)
        return count


class DataEncryption:
    """数据加密类"""
    
    def __init__(self, password: bytes = None):
        """初始化加密器"""
        if password is None:
            password = os.getenv("ENCRYPTION_KEY", "default-encryption-key").encode()
        
        # 使用PBKDF2生成密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'salt_',  # 在生产环境中应使用随机盐
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """加密数据"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    @staticmethod
    def hash_data(data: str, salt: str = None) -> str:
        """哈希数据"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        hash_obj = hashlib.sha256()
        hash_obj.update((data + salt).encode())
        return f"{salt}:{hash_obj.hexdigest()}"
    
    @staticmethod
    def verify_hash(data: str, hashed_data: str) -> bool:
        """验证哈希"""
        try:
            salt, hash_value = hashed_data.split(':', 1)
            hash_obj = hashlib.sha256()
            hash_obj.update((data + salt).encode())
            return hash_obj.hexdigest() == hash_value
        except ValueError:
            return False


class JWTManager:
    """JWT管理器"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict):
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> dict:
        """验证令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )


# 全局加密器实例
encryptor = DataEncryption()

# 密码相关函数
def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def generate_verification_token() -> str:
    """生成验证令牌"""
    return secrets.token_urlsafe(32)