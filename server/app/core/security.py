# -*- coding: utf-8 -*-
"""
安全功能模块
简化版 - 仅保留数据加密功能
"""

import hashlib
import secrets
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import logging

logger = logging.getLogger(__name__)


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


# 全局加密器实例
encryptor = DataEncryption()
