"""
DouyinLiveWebFetcher API封装模块

这是一个高性能的抖音直播数据获取API封装，提供：
- 异步API接口
- 消息适配和标准化
- 多层缓存策略
- 状态管理和监控
- 错误处理和重试
- 配置管理
- 工具函数

主要组件：
- DouyinLiveAPI: 主要API接口类
- MessageAdapter: 消息适配器
- StateManager: 状态管理器
- CacheManager: 缓存管理器
- ConfigManager: 配置管理器

使用示例：
    ```python
    from douyin_live_fecter_module import DouyinLiveAPI, create_api
    
    # 方式1：使用工厂函数
    api = create_api()
    
    # 方式2：直接创建
    api = DouyinLiveAPI()
    
    # 连接到直播间
    await api.connect("123456789")
    
    # 订阅消息
    async def on_message(message):
        print(f"收到消息: {message}")
    
    api.subscribe("chat", on_message)
    
    # 启动监听
    await api.start_listening()
    ```
"""

from .models import (
    # 枚举
    MessageType,
    ConnectionStatus,
    ErrorSeverity,
    CacheLevel,
    
    # 数据模型
    DouyinMessage,
    ConnectionState,
    APIResponse,
    CacheConfig,
    ErrorInfo,
    
    # 消息类型
    BaseMessage,
    ChatMessage,
    GiftMessage,
    LikeMessage,
    FollowMessage,
    MemberMessage,
    ShareMessage,
    ControlMessage,
    RoomStatus,
    
    # 工厂和验证
    MessageFactory,
    ModelValidator
)

from .config import (
    ConfigManager,
    get_config_manager,
    load_config,
    validate_config
)

from .exceptions import (
    # 基础异常
    DouyinAPIException,
    ConfigurationError,
    ValidationError,
    NetworkError,
    CacheError,
    StateError,
    
    # 错误处理工具
    handle_errors,
    handle_errors_async,
    create_error_response,
    log_error,
    RetryOnError,
    ErrorMonitor
)

from .adapters import (
    MessageAdapter,
    ChatMessageAdapter,
    GiftMessageAdapter,
    LikeMessageAdapter,
    FollowMessageAdapter,
    AdapterManager,
    MessageFilter,
    MessageAdapterManager,
    get_adapter_manager,
    reset_adapter_manager
)

from .state_manager import (
    StateStorage,
    MemoryStateStorage,
    RedisStateStorage,
    StateObserver,
    RoomStateManager,
    GlobalStateManager,
    get_state_manager,
    init_state_manager
)

from .cache import (
    CacheBackend,
    MemoryCacheBackend,
    RedisCacheBackend,
    MultiLevelCacheManager,
    MessageCacheManager,
    UserCacheManager,
    RoomCacheManager,
    GlobalCacheManager,
    cache_result,
    cache_async_result,
    CachePreloader,
    get_cache_manager
)

from .api import (
    MessageHandler,
    ConnectionManager,
    MessageStreamManager,
    DouyinLiveAPI,
    APIFactory,
    create_api,
    create_connection_manager,
    create_message_stream_manager
)

from .utils import (
    # 时间工具
    TimeUtils,
    time_utils,
    now,
    timestamp,
    format_duration,
    
    # 字符串工具
    StringUtils,
    string_utils,
    generate_id,
    
    # 验证工具
    ValidationUtils,
    validation_utils,
    
    # 网络工具
    NetworkUtils,
    network_utils,
    
    # 异步工具
    AsyncUtils,
    async_utils,
    run_with_timeout,
    
    # 数据工具
    DataUtils,
    data_utils,
    safe_get,
    calculate_hash,
    
    # 调试工具
    DebugUtils,
    debug_utils,
    
    # 文件工具
    FileUtils,
    file_utils,
    
    # 性能监控
    PerformanceMonitor,
    PerformanceMetrics,
    performance_monitor,
    
    # 装饰器
    debug_calls
)

from .service import (
    DouyinLiveWebFetcher
)


# 版本信息
__version__ = "1.0.0"
__author__ = "DouyinLive Team"
__email__ = "support@douyinlive.com"
__description__ = "高性能抖音直播数据获取API封装"


# 模块级别配置
__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    
    # 核心API
    "DouyinLiveAPI",
    "create_api",
    "APIFactory",
    
    # 连接和消息管理
    "ConnectionManager",
    "MessageStreamManager",
    "create_connection_manager",
    "create_message_stream_manager",
    
    # 数据模型
    "MessageType",
    "ConnectionStatus",
    "ErrorSeverity",
    "CacheLevel",
    "DouyinMessage",
    "ConnectionState",
    "APIResponse",
    "CacheConfig",
    "ErrorInfo",
    "MessageFactory",
    "ModelValidator",
    
    # 配置管理
    "ConfigManager",
    "get_config_manager",
    "load_config",
    "validate_config",
    
    # 异常处理
    "DouyinAPIException",
    "ConfigurationError",
    "ValidationError",
    "NetworkError",
    "CacheError",
    "StateError",
    "handle_errors",
    "handle_errors_async",
    "create_error_response",
    "log_error",
    "RetryOnError",
    "ErrorMonitor",
    
    # 消息适配
    "MessageAdapter",
    "ChatMessageAdapter",
    "GiftMessageAdapter",
    "LikeMessageAdapter",
    "FollowMessageAdapter",
    "AdapterManager",
    "MessageFilter",
    "get_adapter_manager",
    
    # 状态管理
    "StateStorage",
    "MemoryStateStorage",
    "RedisStateStorage",
    "StateObserver",
    "RoomStateManager",
    "GlobalStateManager",
    "get_state_manager",
    "init_state_manager",
    
    # 缓存管理
    "CacheBackend",
    "MemoryCacheBackend",
    "RedisCacheBackend",
    "MultiLevelCacheManager",
    "MessageCacheManager",
    "UserCacheManager",
    "RoomCacheManager",
    "GlobalCacheManager",
    "cache_result",
    "cache_async_result",
    "CachePreloader",
    "get_cache_manager",
    
    # 工具函数
    "TimeUtils",
    "StringUtils",
    "ValidationUtils",
    "NetworkUtils",
    "AsyncUtils",
    "DataUtils",
    "DebugUtils",
    "FileUtils",
    "PerformanceMonitor",
    "PerformanceMetrics",
    "performance_monitor",
    "debug_calls",
    
    # 便捷函数
    "now",
    "timestamp",
    "format_duration",
    "generate_id",
    "safe_get",
    "calculate_hash",
    "run_with_timeout",
    
    # 工具实例
    "time_utils",
    "string_utils",
    "validation_utils",
    "network_utils",
    "async_utils",
    "data_utils",
    "debug_utils",
    "file_utils",
    
    # 原始服务
    "DouyinLiveWebFetcher"
]


# 模块初始化函数
def init_module(config_path: str = None, 
               redis_url: str = None,
               log_level: str = "INFO") -> None:
    """
    初始化模块
    
    Args:
        config_path: 配置文件路径
        redis_url: Redis连接URL
        log_level: 日志级别
    """
    import logging
    
    # 设置日志级别
    logging.getLogger(__name__).setLevel(getattr(logging, log_level.upper()))
    
    # 初始化配置管理器
    if config_path:
        config_manager = get_config_manager()
        config_manager.load_from_file(config_path)
    
    # 初始化状态管理器
    if redis_url:
        init_state_manager(redis_url=redis_url)
    
    logging.getLogger(__name__).info(f"DouyinLiveWebFetcher API封装模块 v{__version__} 初始化完成")


# 快速开始函数
async def quick_start(room_id: str, 
                     message_handler: callable = None,
                     config_path: str = None) -> DouyinLiveAPI:
    """
    快速开始函数
    
    Args:
        room_id: 直播间ID
        message_handler: 消息处理函数
        config_path: 配置文件路径
    
    Returns:
        DouyinLiveAPI实例
    
    Example:
        ```python
        async def handle_message(message):
            print(f"收到消息: {message}")
        
        api = await quick_start("123456789", handle_message)
        await api.start_listening()
        ```
    """
    # 初始化模块
    if config_path:
        init_module(config_path=config_path)
    
    # 创建API实例
    api = create_api()
    
    # 连接到直播间
    await api.connect(room_id)
    
    # 设置消息处理器
    if message_handler:
        api.subscribe("all", message_handler)
    
    return api


# 健康检查函数
async def health_check() -> dict:
    """
    健康检查函数
    
    Returns:
        健康状态信息
    """
    from .utils import NetworkUtils
    
    status = {
        "module": "DouyinLiveWebFetcher API封装",
        "version": __version__,
        "timestamp": now().isoformat(),
        "status": "healthy",
        "checks": {}
    }
    
    # 检查网络连通性
    try:
        connectivity = await NetworkUtils.check_connectivity()
        status["checks"]["network"] = "ok" if connectivity else "failed"
    except Exception as e:
        status["checks"]["network"] = f"error: {e}"
    
    # 检查配置管理器
    try:
        config_manager = get_config_manager()
        status["checks"]["config"] = "ok" if config_manager else "failed"
    except Exception as e:
        status["checks"]["config"] = f"error: {e}"
    
    # 检查状态管理器
    try:
        state_manager = get_state_manager()
        status["checks"]["state"] = "ok" if state_manager else "failed"
    except Exception as e:
        status["checks"]["state"] = f"error: {e}"
    
    # 检查缓存管理器
    try:
        cache_manager = get_cache_manager()
        status["checks"]["cache"] = "ok" if cache_manager else "failed"
    except Exception as e:
        status["checks"]["cache"] = f"error: {e}"
    
    # 检查适配器管理器
    try:
        adapter_manager = get_adapter_manager()
        status["checks"]["adapter"] = "ok" if adapter_manager else "failed"
    except Exception as e:
        status["checks"]["adapter"] = f"error: {e}"
    
    # 判断整体状态
    failed_checks = [k for k, v in status["checks"].items() if v != "ok"]
    if failed_checks:
        status["status"] = "degraded"
        status["failed_checks"] = failed_checks
    
    return status


# 模块级别日志记录器
import logging
logger = logging.getLogger(__name__)
logger.info(f"DouyinLiveWebFetcher API封装模块 v{__version__} 已加载")