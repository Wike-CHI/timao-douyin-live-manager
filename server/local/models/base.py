# -*- coding: utf-8 -*-
"""
数据库模型基类
"""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Column, DateTime, Integer, String, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr
import uuid

Base = declarative_base()


class TimestampMixin:
    """时间戳混入类"""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")


class BaseModel(Base, TimestampMixin):
    """基础模型类"""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    
    @declared_attr
    def __tablename__(cls):
        """自动生成表名"""
        return cls.__name__.lower()
    
    def to_dict(self, exclude: Optional[list] = None) -> Dict[str, Any]:
        """转换为字典"""
        exclude = exclude or []
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude: Optional[list] = None) -> None:
        """从字典更新属性"""
        exclude = exclude or ['id', 'created_at', 'updated_at']
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)


class UUIDMixin:
    """UUID混入类"""
    
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, comment="UUID")


class SoftDeleteMixin:
    """软删除混入类"""
    
    is_deleted = Column(Boolean, default=False, nullable=False, comment="是否已删除")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """恢复"""
        self.is_deleted = False
        self.deleted_at = None