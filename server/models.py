"""
提猫直播助手 - 数据模型
定义应用中使用的数据结构和模型
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import uuid


@dataclass
class Comment:
    """评论数据模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user: str = ""
    content: str = ""
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    platform: str = "douyin"  # 平台标识
    room_id: str = ""  # 直播间ID
    user_id: str = ""  # 用户ID
    user_level: int = 0  # 用户等级
    is_vip: bool = False  # 是否VIP
    gift_count: int = 0  # 礼物数量
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'user': self.user,
            'content': self.content,
            'timestamp': self.timestamp,
            'platform': self.platform,
            'room_id': self.room_id,
            'user_id': self.user_id,
            'user_level': self.user_level,
            'is_vip': self.is_vip,
            'gift_count': self.gift_count,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Comment':
        """从字典创建实例"""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user=data.get('user', ''),
            content=data.get('content', ''),
            timestamp=data.get('timestamp', int(datetime.now().timestamp() * 1000)),
            platform=data.get('platform', 'douyin'),
            room_id=data.get('room_id', ''),
            user_id=data.get('user_id', ''),
            user_level=data.get('user_level', 0),
            is_vip=data.get('is_vip', False),
            gift_count=data.get('gift_count', 0),
            metadata=data.get('metadata', {})
        )


@dataclass
class HotWord:
    """热词数据模型"""
    word: str = ""
    count: int = 0
    score: float = 0.0  # 热度评分
    trend: str = "stable"  # 趋势: up, down, stable
    category: str = "general"  # 分类: product, emotion, question, etc.
    first_seen: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    last_seen: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    related_comments: List[str] = field(default_factory=list)  # 相关评论ID
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'word': self.word,
            'count': self.count,
            'score': self.score,
            'trend': self.trend,
            'category': self.category,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'related_comments': self.related_comments
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HotWord':
        """从字典创建实例"""
        return cls(
            word=data.get('word', ''),
            count=data.get('count', 0),
            score=data.get('score', 0.0),
            trend=data.get('trend', 'stable'),
            category=data.get('category', 'general'),
            first_seen=data.get('first_seen', int(datetime.now().timestamp() * 1000)),
            last_seen=data.get('last_seen', int(datetime.now().timestamp() * 1000)),
            related_comments=data.get('related_comments', [])
        )


@dataclass
class AIScript:
    """AI话术数据模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    type: str = "general"  # 话术类型: welcome, product, interaction, closing
    score: float = 0.0  # 质量评分
    used: bool = False  # 是否已使用
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    context: List[str] = field(default_factory=list)  # 生成上下文（热词等）
    source: str = "ai"  # 来源: ai, manual, template
    tags: List[str] = field(default_factory=list)  # 标签
    usage_count: int = 0  # 使用次数
    effectiveness: float = 0.0  # 效果评分
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'content': self.content,
            'type': self.type,
            'score': self.score,
            'used': self.used,
            'timestamp': self.timestamp,
            'context': self.context,
            'source': self.source,
            'tags': self.tags,
            'usage_count': self.usage_count,
            'effectiveness': self.effectiveness
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIScript':
        """从字典创建实例"""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            content=data.get('content', ''),
            type=data.get('type', 'general'),
            score=data.get('score', 0.0),
            used=data.get('used', False),
            timestamp=data.get('timestamp', int(datetime.now().timestamp() * 1000)),
            context=data.get('context', []),
            source=data.get('source', 'ai'),
            tags=data.get('tags', []),
            usage_count=data.get('usage_count', 0),
            effectiveness=data.get('effectiveness', 0.0)
        )


@dataclass
class AppConfig:
    """应用配置数据模型"""
    # AI服务配置
    ai_service: str = "deepseek"  # deepseek, openai, doubao
    ai_api_key: str = ""
    ai_base_url: str = ""
    ai_model: str = ""
    
    # 抖音直播配置
    douyin_room_id: str = ""
    douyin_cookie: str = ""
    
    # 应用配置
    max_comments: int = 1000
    hot_words_limit: int = 50
    script_generation_interval: int = 300  # 秒
    comment_fetch_interval: int = 5  # 秒
    
    # 性能配置
    enable_cache: bool = True
    cache_ttl: int = 300  # 秒
    max_memory_usage: int = 512  # MB
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    max_log_size: int = 10  # MB
    
    # 开发模式
    debug_mode: bool = False
    mock_data: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'ai_service': self.ai_service,
            'ai_api_key': self.ai_api_key,
            'ai_base_url': self.ai_base_url,
            'ai_model': self.ai_model,
            'douyin_room_id': self.douyin_room_id,
            'douyin_cookie': self.douyin_cookie,
            'max_comments': self.max_comments,
            'hot_words_limit': self.hot_words_limit,
            'script_generation_interval': self.script_generation_interval,
            'comment_fetch_interval': self.comment_fetch_interval,
            'enable_cache': self.enable_cache,
            'cache_ttl': self.cache_ttl,
            'max_memory_usage': self.max_memory_usage,
            'log_level': self.log_level,
            'log_file': self.log_file,
            'max_log_size': self.max_log_size,
            'debug_mode': self.debug_mode,
            'mock_data': self.mock_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """从字典创建实例"""
        return cls(
            ai_service=data.get('ai_service', 'deepseek'),
            ai_api_key=data.get('ai_api_key', ''),
            ai_base_url=data.get('ai_base_url', ''),
            ai_model=data.get('ai_model', ''),
            douyin_room_id=data.get('douyin_room_id', ''),
            douyin_cookie=data.get('douyin_cookie', ''),
            max_comments=data.get('max_comments', 1000),
            hot_words_limit=data.get('hot_words_limit', 50),
            script_generation_interval=data.get('script_generation_interval', 300),
            comment_fetch_interval=data.get('comment_fetch_interval', 5),
            enable_cache=data.get('enable_cache', True),
            cache_ttl=data.get('cache_ttl', 300),
            max_memory_usage=data.get('max_memory_usage', 512),
            log_level=data.get('log_level', 'INFO'),
            log_file=data.get('log_file', 'logs/app.log'),
            max_log_size=data.get('max_log_size', 10),
            debug_mode=data.get('debug_mode', False),
            mock_data=data.get('mock_data', False)
        )


@dataclass
class APIResponse:
    """API响应数据模型"""
    success: bool = True
    message: str = ""
    data: Any = None
    error_code: Optional[str] = None
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'success': self.success,
            'message': self.message,
            'timestamp': self.timestamp
        }
        
        if self.data is not None:
            result['data'] = self.data
        
        if self.error_code:
            result['error_code'] = self.error_code
            
        return result
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# 数据存储管理器
class DataManager:
    """数据管理器，负责数据的存储和检索"""
    
    def __init__(self):
        self.comments: List[Comment] = []
        self.hot_words: List[HotWord] = []
        self.scripts: List[AIScript] = []
        self.config: AppConfig = AppConfig()
        
        # 内存限制
        self.max_comments = 1000
        self.max_scripts = 100
    
    def add_comment(self, comment: Comment) -> None:
        """添加评论"""
        self.comments.insert(0, comment)
        
        # 限制数量
        if len(self.comments) > self.max_comments:
            self.comments = self.comments[:self.max_comments]
    
    def get_comments(self, limit: int = 50, offset: int = 0) -> List[Comment]:
        """获取评论列表"""
        start = offset
        end = offset + limit
        return self.comments[start:end]
    
    def get_recent_comments(self, minutes: int = 10) -> List[Comment]:
        """获取最近的评论"""
        cutoff_time = int((datetime.now().timestamp() - minutes * 60) * 1000)
        return [c for c in self.comments if c.timestamp > cutoff_time]
    
    def update_hot_words(self, hot_words: List[HotWord]) -> None:
        """更新热词列表"""
        self.hot_words = hot_words
    
    def get_hot_words(self, limit: int = 20) -> List[HotWord]:
        """获取热词列表"""
        return sorted(self.hot_words, key=lambda x: x.score, reverse=True)[:limit]
    
    def add_script(self, script: AIScript) -> None:
        """添加AI话术"""
        self.scripts.insert(0, script)
        
        # 限制数量
        if len(self.scripts) > self.max_scripts:
            self.scripts = self.scripts[:self.max_scripts]
    
    def get_scripts(self, limit: int = 10, unused_only: bool = False) -> List[AIScript]:
        """获取AI话术列表"""
        scripts = self.scripts
        
        if unused_only:
            scripts = [s for s in scripts if not s.used]
        
        return scripts[:limit]
    
    def get_script_by_id(self, script_id: str) -> Optional[AIScript]:
        """根据ID获取话术"""
        for script in self.scripts:
            if script.id == script_id:
                return script
        return None
    
    def mark_script_used(self, script_id: str) -> bool:
        """标记话术为已使用"""
        script = self.get_script_by_id(script_id)
        if script:
            script.used = True
            script.usage_count += 1
            return True
        return False
    
    def update_config(self, config: AppConfig) -> None:
        """更新配置"""
        self.config = config
        self.max_comments = config.max_comments
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        recent_comments = self.get_recent_comments(10)
        
        return {
            'total_comments': len(self.comments),
            'recent_comments': len(recent_comments),
            'comments_per_minute': len(self.get_recent_comments(1)),
            'total_hot_words': len(self.hot_words),
            'total_scripts': len(self.scripts),
            'unused_scripts': len([s for s in self.scripts if not s.used]),
            'memory_usage': self._calculate_memory_usage()
        }
    
    def _calculate_memory_usage(self) -> Dict[str, int]:
        """计算内存使用情况"""
        import sys
        
        return {
            'comments': sys.getsizeof(self.comments),
            'hot_words': sys.getsizeof(self.hot_words),
            'scripts': sys.getsizeof(self.scripts),
            'total': sys.getsizeof(self.comments) + sys.getsizeof(self.hot_words) + sys.getsizeof(self.scripts)
        }
    
    def clear_old_data(self, days: int = 7) -> None:
        """清理旧数据"""
        cutoff_time = int((datetime.now().timestamp() - days * 24 * 3600) * 1000)
        
        # 清理旧评论
        self.comments = [c for c in self.comments if c.timestamp > cutoff_time]
        
        # 清理旧话术
        self.scripts = [s for s in self.scripts if s.timestamp > cutoff_time]


# 全局数据管理器实例
data_manager = DataManager()


# 工具函数
def create_success_response(data: Any = None, message: str = "操作成功") -> APIResponse:
    """创建成功响应"""
    return APIResponse(success=True, message=message, data=data)


def create_error_response(message: str, error_code: str = None, data: Any = None) -> APIResponse:
    """创建错误响应"""
    return APIResponse(success=False, message=message, error_code=error_code, data=data)


def validate_comment_data(data: Dict[str, Any]) -> bool:
    """验证评论数据"""
    required_fields = ['user', 'content']
    return all(field in data and data[field] for field in required_fields)


def validate_config_data(data: Dict[str, Any]) -> bool:
    """验证配置数据"""
    # 基本验证
    if 'max_comments' in data and not isinstance(data['max_comments'], int):
        return False
    
    if 'hot_words_limit' in data and not isinstance(data['hot_words_limit'], int):
        return False
    
    return True