"""
DouyinLiveWebFetcher API封装 - 数据模型定义

本模块定义了API封装所需的所有数据模型，包括：
- 消息类型模型
- API响应模型  
- 配置模型
- 错误模型

所有模型支持JSON序列化/反序列化，包含数据验证逻辑。
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union, Literal
from datetime import datetime
from enum import Enum
import json
import uuid
from abc import ABC, abstractmethod


# ================================
# 基础枚举定义
# ================================

class MessageType(Enum):
    """消息类型枚举"""
    CHAT = "chat"                    # 聊天消息
    GIFT = "gift"                    # 礼物消息
    LIKE = "like"                    # 点赞消息
    MEMBER = "member"                # 进场消息
    FOLLOW = "follow"                # 关注消息
    SHARE = "share"                  # 分享消息
    SOCIAL = "social"                # 社交消息
    ROOM_USER_SEQ = "room_user_seq"  # 房间用户序列
    UPDATE_FAN_TICKET = "update_fan_ticket"  # 粉丝票更新
    COMMON_TEXT = "common_text"      # 通用文本
    CONTROL = "control"              # 控制消息
    UNKNOWN = "unknown"              # 未知消息


class FetcherStatus(Enum):
    """抓取器状态枚举"""
    IDLE = "idle"                    # 空闲状态
    CONNECTING = "connecting"        # 连接中
    CONNECTED = "connected"          # 已连接
    FETCHING = "fetching"           # 抓取中
    DISCONNECTED = "disconnected"    # 已断开
    ERROR = "error"                  # 错误状态
    STOPPED = "stopped"              # 已停止


class ConnectionStatus(Enum):
    """连接状态枚举"""
    DISCONNECTED = "disconnected"    # 未连接
    CONNECTING = "connecting"        # 连接中
    CONNECTED = "connected"          # 已连接
    RECONNECTING = "reconnecting"    # 重连中
    FAILED = "failed"                # 连接失败
    CLOSED = "closed"                # 连接关闭


class ErrorCode(Enum):
    """错误码枚举"""
    SUCCESS = 0                      # 成功
    INVALID_ROOM_ID = 1001          # 无效房间ID
    CONNECTION_FAILED = 1002         # 连接失败
    WEBSOCKET_ERROR = 1003          # WebSocket错误
    MESSAGE_PARSE_ERROR = 1004      # 消息解析错误
    CONFIG_ERROR = 1005             # 配置错误
    TIMEOUT_ERROR = 1006            # 超时错误
    PERMISSION_DENIED = 1007        # 权限拒绝
    RATE_LIMIT_EXCEEDED = 1008      # 频率限制
    INTERNAL_ERROR = 9999           # 内部错误


class ErrorSeverity(Enum):
    """错误严重程度枚举"""
    LOW = "low"                      # 低级错误
    MEDIUM = "medium"                # 中级错误
    HIGH = "high"                    # 高级错误
    CRITICAL = "critical"            # 严重错误


class CacheLevel(Enum):
    """缓存级别枚举"""
    L1 = "l1"                        # 一级缓存（内存）
    L2 = "l2"                        # 二级缓存（Redis）
    L3 = "l3"                        # 三级缓存（持久化）


class RoomStatus(Enum):
    """房间状态枚举"""
    UNKNOWN = "unknown"              # 未知状态
    LIVE = "live"                    # 直播中
    OFFLINE = "offline"              # 离线
    PREPARING = "preparing"          # 准备中
    ENDED = "ended"                  # 已结束
    BANNED = "banned"                # 被封禁
    ERROR = "error"                  # 错误状态
    ACTIVE = "active"                # 活跃状态（兼容测试用例）


# ================================
# 基础数据模型
# ================================

@dataclass
class BaseModel:
    """基础模型类，提供通用功能"""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建实例"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str):
        """从JSON字符串创建实例"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def validate(self) -> bool:
        """验证数据有效性"""
        return True


# ================================
# 消息模型定义
# ================================

@dataclass
class BaseMessage(BaseModel):
    """基础消息模型"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.UNKNOWN
    timestamp: datetime = field(default_factory=datetime.now)
    room_id: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """验证消息基础字段"""
        return bool(self.message_id and self.room_id)


@dataclass
class ChatMessage(BaseMessage):
    """聊天消息模型"""
    message_type: MessageType = MessageType.CHAT
    user_id: str = ""
    user_name: str = ""
    user_level: int = 0
    user_avatar: str = ""
    content: str = ""
    
    def validate(self) -> bool:
        """验证聊天消息"""
        return super().validate() and bool(self.user_id and self.content)


@dataclass
class GiftMessage(BaseMessage):
    """礼物消息模型"""
    message_type: MessageType = MessageType.GIFT
    user_id: str = ""
    user_name: str = ""
    user_level: int = 0
    user_avatar: str = ""
    gift_id: str = ""
    gift_name: str = ""
    gift_count: int = 0
    gift_price: float = 0.0
    total_price: float = 0.0
    
    def validate(self) -> bool:
        """验证礼物消息"""
        return (super().validate() and 
                bool(self.user_id and self.gift_id) and 
                self.gift_count > 0)


@dataclass
class LikeMessage(BaseMessage):
    """点赞消息模型"""
    message_type: MessageType = MessageType.LIKE
    user_id: str = ""
    user_name: str = ""
    user_level: int = 0
    user_avatar: str = ""
    like_count: int = 1
    total_likes: int = 0
    
    def validate(self) -> bool:
        """验证点赞消息"""
        return (super().validate() and 
                bool(self.user_id) and 
                self.like_count > 0)


@dataclass
class MemberMessage(BaseMessage):
    """进场消息模型"""
    message_type: MessageType = MessageType.MEMBER
    user_id: str = ""
    user_name: str = ""
    user_level: int = 0
    user_avatar: str = ""
    member_level: int = 0
    
    def validate(self) -> bool:
        """验证进场消息"""
        return super().validate() and bool(self.user_id)


@dataclass
class FollowMessage(BaseMessage):
    """关注消息模型"""
    message_type: MessageType = MessageType.FOLLOW
    user_id: str = ""
    user_name: str = ""
    user_level: int = 0
    user_avatar: str = ""
    
    def validate(self) -> bool:
        """验证关注消息"""
        return super().validate() and bool(self.user_id)


@dataclass
class ShareMessage(BaseMessage):
    """分享消息模型"""
    message_type: MessageType = MessageType.SHARE
    user_id: str = ""
    user_name: str = ""
    user_level: int = 0
    user_avatar: str = ""
    
    def validate(self) -> bool:
        """验证分享消息"""
        return super().validate() and bool(self.user_id)


@dataclass
class ControlMessage(BaseMessage):
    """控制消息模型"""
    message_type: MessageType = MessageType.CONTROL
    action: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """验证控制消息"""
        return super().validate() and bool(self.action)


# ================================
# 状态和统计模型
# ================================

@dataclass
class FetcherStatusInfo(BaseModel):
    """抓取器状态信息"""
    status: FetcherStatus = FetcherStatus.IDLE
    room_id: str = ""
    start_time: Optional[datetime] = None
    last_message_time: Optional[datetime] = None
    total_messages: int = 0
    message_counts: Dict[str, int] = field(default_factory=dict)
    error_message: str = ""
    connection_info: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """验证状态信息"""
        return bool(self.status)


@dataclass
class RoomInfo(BaseModel):
    """直播间信息"""
    room_id: str = ""
    room_title: str = ""
    owner_id: str = ""
    owner_name: str = ""
    owner_avatar: str = ""
    viewer_count: int = 0
    like_count: int = 0
    is_live: bool = False
    start_time: Optional[datetime] = None
    
    def validate(self) -> bool:
        """验证房间信息"""
        return bool(self.room_id)


@dataclass
class UserStatistics(BaseModel):
    """用户统计信息"""
    user_id: str = ""
    user_name: str = ""
    message_count: int = 0
    gift_count: int = 0
    like_count: int = 0
    total_gift_value: float = 0.0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    def validate(self) -> bool:
        """验证用户统计"""
        return bool(self.user_id)


# ================================
# API响应模型
# ================================

@dataclass
class APIResponse(BaseModel):
    """API响应基础模型"""
    success: bool = True
    code: ErrorCode = ErrorCode.SUCCESS
    message: str = ""
    data: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def validate(self) -> bool:
        """验证API响应"""
        return bool(self.request_id)


@dataclass
class StartFetchResponse(APIResponse):
    """开始抓取响应"""
    data: Optional[FetcherStatusInfo] = None


@dataclass
class StopFetchResponse(APIResponse):
    """停止抓取响应"""
    data: Optional[FetcherStatusInfo] = None


@dataclass
class StatusResponse(APIResponse):
    """状态查询响应"""
    data: Optional[FetcherStatusInfo] = None


@dataclass
class RoomInfoResponse(APIResponse):
    """房间信息响应"""
    data: Optional[RoomInfo] = None


@dataclass
class MessagesResponse(APIResponse):
    """消息列表响应"""
    data: Optional[List[BaseMessage]] = None
    total: int = 0
    page: int = 1
    page_size: int = 50


# ================================
# 配置模型
# ================================

@dataclass
class DatabaseConfig(BaseModel):
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    database: str = "douyin_live"
    username: str = "postgres"
    password: str = ""
    pool_size: int = 10
    pool_timeout: int = 30
    
    def validate(self) -> bool:
        """验证数据库配置"""
        return bool(self.host and self.database and self.username)


@dataclass
class RedisConfig(BaseModel):
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: str = ""
    max_connections: int = 20
    socket_timeout: int = 5
    
    def validate(self) -> bool:
        """验证Redis配置"""
        return bool(self.host and 0 <= self.port <= 65535)


@dataclass
class FetcherConfig(BaseModel):
    """抓取器配置"""
    reconnect_interval: int = 5
    max_reconnect_times: int = 3
    message_buffer_size: int = 1000
    timeout: int = 30
    enable_heartbeat: bool = True
    heartbeat_interval: int = 30
    
    def validate(self) -> bool:
        """验证抓取器配置"""
        return (self.reconnect_interval > 0 and 
                self.max_reconnect_times >= 0 and
                self.message_buffer_size > 0 and
                self.timeout > 0)


@dataclass
class APIConfig(BaseModel):
    """API配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: List[str] = field(default_factory=list)
    rate_limit: int = 100
    
    def validate(self) -> bool:
        """验证API配置"""
        return bool(self.host and 0 <= self.port <= 65535)


@dataclass
class DouyinAPIConfig(BaseModel):
    """抖音API总配置"""
    app_name: str = "DouyinLiveAPI"
    version: str = "1.0.0"
    debug: bool = False
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    api: APIConfig = field(default_factory=APIConfig)
    fetcher: FetcherConfig = field(default_factory=FetcherConfig)
    
    def validate(self) -> bool:
        """验证总配置"""
        return (bool(self.app_name and self.version) and
                self.database.validate() and
                self.redis.validate() and
                self.api.validate() and
                self.fetcher.validate())


# ================================
# 缓存配置模型
# ================================

@dataclass
class CacheConfig(BaseModel):
    """缓存配置"""
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    default_ttl: int = 3600
    max_memory_cache_size: int = 1000
    key_prefix: str = "douyin_live"
    
    def validate(self) -> bool:
        """验证缓存配置"""
        return bool(self.redis_host and 0 <= self.redis_port <= 65535)


# ================================
# 错误模型
# ================================

@dataclass
class ErrorInfo(BaseModel):
    """错误信息模型"""
    code: ErrorCode = ErrorCode.INTERNAL_ERROR
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def validate(self) -> bool:
        """验证错误信息"""
        return bool(self.code and self.message)


# ================================
# 消息工厂
# ================================

# DouyinMessage 别名，指向 BaseMessage
DouyinMessage = BaseMessage

# 创建一个简单的ConnectionState类
@dataclass
class ConnectionState(BaseModel):
    """连接状态信息"""
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    room_id: str = ""
    connected_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    error_message: str = ""
    
    def validate(self) -> bool:
        """验证连接状态"""
        return bool(self.room_id)

class MessageFactory:
    """消息工厂类，用于创建不同类型的消息"""
    
    _message_classes = {
        MessageType.CHAT: ChatMessage,
        MessageType.GIFT: GiftMessage,
        MessageType.LIKE: LikeMessage,
        MessageType.MEMBER: MemberMessage,
        MessageType.FOLLOW: FollowMessage,
        MessageType.SHARE: ShareMessage,
        MessageType.CONTROL: ControlMessage,
    }
    
    @classmethod
    def create_message(cls, message_type: MessageType, **kwargs) -> BaseMessage:
        """创建指定类型的消息"""
        message_class = cls._message_classes.get(message_type, BaseMessage)
        return message_class(message_type=message_type, **kwargs)
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, Any]) -> BaseMessage:
        """从原始数据创建消息"""
        # 这里需要根据原始数据的格式来判断消息类型
        # 具体实现将在适配器中完成
        message_type = MessageType.UNKNOWN
        return cls.create_message(message_type, raw_data=raw_data)


# ================================
# 模型验证工具
# ================================

class ModelValidator:
    """模型验证器"""
    
    @staticmethod
    def validate_model(model: BaseModel) -> tuple[bool, str]:
        """验证模型数据"""
        try:
            if not model.validate():
                return False, "Model validation failed"
            return True, "Validation passed"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def serialize_model(model: BaseModel) -> Dict[str, Any]:
        """序列化模型"""
        try:
            return model.to_dict()
        except Exception as e:
            raise ValueError(f"Serialization failed: {str(e)}")


def validate_model(model: BaseModel) -> tuple[bool, str]:
    """验证模型数据"""
    return ModelValidator.validate_model(model)


def serialize_model(model: BaseModel) -> Dict[str, Any]:
    """序列化模型"""
    return ModelValidator.serialize_model(model)


def deserialize_model(model_class: type, data: Dict[str, Any]) -> BaseModel:
    """反序列化模型"""
    try:
        return model_class.from_dict(data)
    except Exception as e:
        raise ValueError(f"Deserialization failed: {str(e)}")


# ================================
# 状态管理相关数据类
# ================================

@dataclass
class SessionState:
    """
    会话状态数据类
    记录直播会话的状态信息
    """
    session_id: str
    room_id: str
    user_id: str
    start_time: datetime
    last_activity: datetime
    is_active: bool = True
    connection_count: int = 0
    message_count: int = 0
    error_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "session_id": self.session_id,
            "room_id": self.room_id,
            "user_id": self.user_id,
            "start_time": self.start_time.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_active": self.is_active,
            "connection_count": self.connection_count,
            "message_count": self.message_count,
            "error_count": self.error_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        """从字典创建实例"""
        return cls(
            session_id=data["session_id"],
            room_id=data["room_id"],
            user_id=data["user_id"],
            start_time=datetime.fromisoformat(data["start_time"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            is_active=data.get("is_active", True),
            connection_count=data.get("connection_count", 0),
            message_count=data.get("message_count", 0),
            error_count=data.get("error_count", 0)
        )


@dataclass
class StateChangeEvent:
    """
    状态变更事件数据类
    记录状态变更的详细信息
    """
    event_id: str
    event_type: str
    old_state: Optional[str]
    new_state: str
    timestamp: datetime
    context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "old_state": self.old_state,
            "new_state": self.new_state,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateChangeEvent':
        """从字典创建实例"""
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            old_state=data.get("old_state"),
            new_state=data["new_state"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            context=data.get("context", {})
        )


@dataclass
class StateSnapshot:
    """
    状态快照数据类
    保存某个时间点的完整状态信息
    """
    snapshot_id: str
    timestamp: datetime
    connection_state: ConnectionState
    session_state: Optional['SessionState']
    room_status: RoomStatus
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp.isoformat(),
            "connection_state": self.connection_state.value,
            "session_state": self.session_state.to_dict() if self.session_state else None,
            "room_status": self.room_status.value,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateSnapshot':
        """从字典创建实例"""
        session_state = None
        if data.get("session_state"):
            session_state = SessionState.from_dict(data["session_state"])
        
        return cls(
            snapshot_id=data["snapshot_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            connection_state=ConnectionState(data["connection_state"]),
            session_state=session_state,
            room_status=RoomStatus(data["room_status"]),
            metadata=data.get("metadata", {})
        )