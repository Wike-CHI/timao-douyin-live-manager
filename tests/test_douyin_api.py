"""
DouyinLiveWebFetcher API封装 - 测试套件

测试覆盖：
- 数据模型验证
- 配置管理
- 异常处理
- 消息适配
- 状态管理
- 缓存功能
- API接口
- 工具函数
- 集成测试
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

# 导入被测试的模块
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from douyin_live_fecter_module import (
    # 核心API
    DouyinLiveAPI,
    create_api,
    APIFactory,
    
    # 数据模型
    MessageType,
    ConnectionStatus,
    DouyinMessage,
    ConnectionState,
    APIResponse,
    MessageFactory,
    ModelValidator,
    
    # 配置管理
    ConfigManager,
    get_config_manager,
    
    # 异常处理
    DouyinAPIException,
    ConfigurationError,
    ValidationError,
    NetworkError,
    handle_errors,
    handle_errors_async,
    
    # 消息适配
    MessageAdapter,
    ChatMessageAdapter,
    AdapterManager,
    get_adapter_manager,
    
    # 状态管理
    MemoryStateStorage,
    RoomStateManager,
    GlobalStateManager,
    get_state_manager,
    
    # 缓存管理
    MemoryCacheBackend,
    MultiLevelCacheManager,
    get_cache_manager,
    cache_result,
    
    # 工具函数
    TimeUtils,
    StringUtils,
    ValidationUtils,
    DataUtils,
    AsyncUtils,
    PerformanceMonitor,
    now,
    timestamp,
    generate_id,
    safe_get,
    run_with_timeout,
    
    # 模块函数
    init_module,
    quick_start,
    health_check
)


# ================================
# 测试夹具
# ================================

@pytest.fixture
def sample_config():
    """示例配置"""
    return {
        "api": {
            "timeout": 30,
            "retry_count": 3,
            "retry_delay": 1.0
        },
        "cache": {
            "ttl": 300,
            "max_size": 1000
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }


@pytest.fixture
def sample_message():
    """示例消息"""
    return {
        "type": "chat",
        "user_id": "123456",
        "username": "测试用户",
        "content": "Hello World",
        "timestamp": int(time.time() * 1000),
        "room_id": "789012"
    }


@pytest.fixture
def mock_websocket():
    """模拟WebSocket连接"""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
async def api_instance():
    """API实例夹具"""
    api = create_api()
    yield api
    # 清理
    if hasattr(api, 'cleanup'):
        await api.cleanup()


# ================================
# 数据模型测试
# ================================

class TestDataModels:
    """数据模型测试"""
    
    def test_message_type_enum(self):
        """测试消息类型枚举"""
        assert MessageType.CHAT.value == "chat"
        assert MessageType.GIFT.value == "gift"
        assert MessageType.LIKE.value == "like"
        assert MessageType.FOLLOW.value == "follow"
    
    def test_connection_status_enum(self):
        """测试连接状态枚举"""
        assert ConnectionStatus.DISCONNECTED.value == "disconnected"
        assert ConnectionStatus.CONNECTING.value == "connecting"
        assert ConnectionStatus.CONNECTED.value == "connected"
        assert ConnectionStatus.RECONNECTING.value == "reconnecting"
    
    def test_douyin_message_creation(self, sample_message):
        """测试抖音消息创建"""
        message = DouyinMessage(
            message_type=MessageType.CHAT,
            user_id=sample_message["user_id"],
            username=sample_message["username"],
            content=sample_message["content"],
            timestamp=datetime.fromtimestamp(sample_message["timestamp"] / 1000),
            room_id=sample_message["room_id"]
        )
        
        assert message.message_type == MessageType.CHAT
        assert message.user_id == sample_message["user_id"]
        assert message.username == sample_message["username"]
        assert message.content == sample_message["content"]
        assert message.room_id == sample_message["room_id"]
    
    def test_message_factory(self, sample_message):
        """测试消息工厂"""
        message = MessageFactory.create_from_dict(sample_message)
        
        assert isinstance(message, DouyinMessage)
        assert message.message_type == MessageType.CHAT
        assert message.user_id == sample_message["user_id"]
    
    def test_model_validator(self, sample_message):
        """测试模型验证器"""
        # 有效消息
        assert ModelValidator.validate_message_dict(sample_message) == []
        
        # 无效消息
        invalid_message = sample_message.copy()
        del invalid_message["user_id"]
        
        errors = ModelValidator.validate_message_dict(invalid_message)
        assert len(errors) > 0
        assert any("user_id" in error for error in errors)
    
    def test_connection_state(self):
        """测试连接状态"""
        state = ConnectionState(
            status=ConnectionStatus.CONNECTED,
            room_id="123456",
            connected_at=now(),
            last_heartbeat=now()
        )
        
        assert state.status == ConnectionStatus.CONNECTED
        assert state.room_id == "123456"
        assert state.is_connected()
    
    def test_api_response(self):
        """测试API响应"""
        response = APIResponse(
            success=True,
            data={"message": "success"},
            timestamp=now()
        )
        
        assert response.success is True
        assert response.data["message"] == "success"
        assert response.error is None


# ================================
# 配置管理测试
# ================================

class TestConfigManager:
    """配置管理测试"""
    
    def test_config_manager_creation(self):
        """测试配置管理器创建"""
        config_manager = ConfigManager()
        assert config_manager is not None
    
    def test_load_from_dict(self, sample_config):
        """测试从字典加载配置"""
        config_manager = ConfigManager()
        config_manager.load_from_dict(sample_config)
        
        assert config_manager.get("api.timeout") == 30
        assert config_manager.get("cache.ttl") == 300
    
    def test_get_with_default(self):
        """测试获取配置（带默认值）"""
        config_manager = ConfigManager()
        
        # 不存在的配置项
        assert config_manager.get("nonexistent.key", "default") == "default"
        
        # 存在的配置项
        config_manager.set("test.key", "value")
        assert config_manager.get("test.key", "default") == "value"
    
    def test_environment_override(self):
        """测试环境变量覆盖"""
        config_manager = ConfigManager()
        config_manager.load_from_dict({"api": {"timeout": 30}})
        
        # 模拟环境变量
        with patch.dict(os.environ, {"API_TIMEOUT": "60"}):
            config_manager.apply_env_overrides()
            assert config_manager.get("api.timeout") == "60"
    
    def test_config_validation(self, sample_config):
        """测试配置验证"""
        config_manager = ConfigManager()
        config_manager.load_from_dict(sample_config)
        
        # 验证必需的配置项
        required_keys = ["api.timeout", "cache.ttl"]
        missing = config_manager.validate_required_keys(required_keys)
        assert len(missing) == 0
        
        # 测试缺失配置项
        incomplete_config = {"api": {"timeout": 30}}
        config_manager.load_from_dict(incomplete_config)
        missing = config_manager.validate_required_keys(required_keys)
        assert len(missing) > 0
    
    def test_global_config_manager(self):
        """测试全局配置管理器"""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        # 应该是同一个实例
        assert manager1 is manager2


# ================================
# 异常处理测试
# ================================

class TestExceptionHandling:
    """异常处理测试"""
    
    def test_custom_exceptions(self):
        """测试自定义异常"""
        # DouyinAPIException
        with pytest.raises(DouyinAPIException):
            raise DouyinAPIException("API error")
        
        # ConfigurationError
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Config error")
        
        # ValidationError
        with pytest.raises(ValidationError):
            raise ValidationError("Validation error")
        
        # NetworkError
        with pytest.raises(NetworkError):
            raise NetworkError("Network error")
    
    def test_error_handling_decorator(self):
        """测试错误处理装饰器"""
        @handle_errors(default_return="error")
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        assert result == "error"
    
    @pytest.mark.asyncio
    async def test_async_error_handling_decorator(self):
        """测试异步错误处理装饰器"""
        @handle_errors_async(default_return="async_error")
        async def failing_async_function():
            raise ValueError("Test async error")
        
        result = await failing_async_function()
        assert result == "async_error"
    
    def test_error_response_creation(self):
        """测试错误响应创建"""
        from douyin_live_fecter_module.exceptions import create_error_response
        
        error = ValueError("Test error")
        response = create_error_response(error, "Operation failed")
        
        assert response.success is False
        assert response.error is not None
        assert "Test error" in response.error


# ================================
# 消息适配测试
# ================================

class TestMessageAdapter:
    """消息适配测试"""
    
    def test_chat_message_adapter(self, sample_message):
        """测试聊天消息适配器"""
        adapter = ChatMessageAdapter()
        
        # 测试适配
        adapted = adapter.adapt(sample_message)
        assert isinstance(adapted, DouyinMessage)
        assert adapted.message_type == MessageType.CHAT
        assert adapted.content == sample_message["content"]
        
        # 测试验证
        assert adapter.validate(sample_message) is True
        
        # 测试无效消息
        invalid_message = sample_message.copy()
        del invalid_message["content"]
        assert adapter.validate(invalid_message) is False
    
    def test_adapter_manager(self, sample_message):
        """测试适配器管理器"""
        manager = AdapterManager()
        
        # 注册适配器
        chat_adapter = ChatMessageAdapter()
        manager.register_adapter(MessageType.CHAT, chat_adapter)
        
        # 测试适配
        adapted = manager.adapt_message(sample_message)
        assert isinstance(adapted, DouyinMessage)
        assert adapted.message_type == MessageType.CHAT
    
    def test_global_adapter_manager(self):
        """测试全局适配器管理器"""
        manager1 = get_adapter_manager()
        manager2 = get_adapter_manager()
        
        # 应该是同一个实例
        assert manager1 is manager2


# ================================
# 状态管理测试
# ================================

class TestStateManager:
    """状态管理测试"""
    
    def test_memory_state_storage(self):
        """测试内存状态存储"""
        storage = MemoryStateStorage()
        
        # 测试设置和获取
        storage.set("test_key", "test_value")
        assert storage.get("test_key") == "test_value"
        
        # 测试不存在的键
        assert storage.get("nonexistent") is None
        assert storage.get("nonexistent", "default") == "default"
        
        # 测试删除
        storage.delete("test_key")
        assert storage.get("test_key") is None
        
        # 测试清空
        storage.set("key1", "value1")
        storage.set("key2", "value2")
        storage.clear()
        assert storage.get("key1") is None
        assert storage.get("key2") is None
    
    @pytest.mark.asyncio
    async def test_room_state_manager(self):
        """测试房间状态管理器"""
        storage = MemoryStateStorage()
        manager = RoomStateManager("123456", storage)
        
        # 测试连接状态
        await manager.set_connection_status(ConnectionStatus.CONNECTED)
        status = await manager.get_connection_status()
        assert status == ConnectionStatus.CONNECTED
        
        # 测试会话信息
        session_info = {"user_count": 100, "duration": 3600}
        await manager.update_session_info(session_info)
        
        retrieved_info = await manager.get_session_info()
        assert retrieved_info["user_count"] == 100
        assert retrieved_info["duration"] == 3600
        
        # 测试统计信息
        await manager.increment_message_count()
        await manager.increment_message_count()
        
        stats = await manager.get_statistics()
        assert stats["message_count"] == 2
    
    @pytest.mark.asyncio
    async def test_global_state_manager(self):
        """测试全局状态管理器"""
        storage = MemoryStateStorage()
        manager = GlobalStateManager(storage)
        
        # 测试房间管理
        room_manager = await manager.get_room_manager("123456")
        assert room_manager is not None
        assert room_manager.room_id == "123456"
        
        # 测试房间列表
        await manager.get_room_manager("789012")  # 创建另一个房间
        rooms = await manager.get_active_rooms()
        assert len(rooms) == 2
        assert "123456" in rooms
        assert "789012" in rooms


# ================================
# 缓存管理测试
# ================================

class TestCacheManager:
    """缓存管理测试"""
    
    def test_memory_cache_backend(self):
        """测试内存缓存后端"""
        cache = MemoryCacheBackend(max_size=100, default_ttl=60)
        
        # 测试设置和获取
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # 测试TTL
        cache.set("key2", "value2", ttl=1)
        time.sleep(1.1)
        assert cache.get("key2") is None
        
        # 测试删除
        cache.delete("key1")
        assert cache.get("key1") is None
        
        # 测试清空
        cache.set("key3", "value3")
        cache.clear()
        assert cache.get("key3") is None
    
    def test_multi_level_cache_manager(self):
        """测试多级缓存管理器"""
        l1_cache = MemoryCacheBackend(max_size=50, default_ttl=60)
        l2_cache = MemoryCacheBackend(max_size=200, default_ttl=300)
        
        manager = MultiLevelCacheManager([l1_cache, l2_cache])
        
        # 测试设置（应该设置到所有级别）
        manager.set("key1", "value1")
        assert manager.get("key1") == "value1"
        assert l1_cache.get("key1") == "value1"
        assert l2_cache.get("key1") == "value1"
        
        # 测试L1缓存失效，L2缓存命中
        l1_cache.delete("key1")
        assert manager.get("key1") == "value1"  # 应该从L2获取并回填L1
        assert l1_cache.get("key1") == "value1"  # L1应该被回填
    
    @pytest.mark.asyncio
    async def test_cache_decorator(self):
        """测试缓存装饰器"""
        call_count = 0
        
        @cache_result(ttl=60, key_prefix="test")
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # 第一次调用
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # 第二次调用（应该从缓存获取）
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # 调用次数不应该增加
        
        # 不同参数的调用
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2


# ================================
# API接口测试
# ================================

class TestDouyinLiveAPI:
    """抖音直播API测试"""
    
    @pytest.mark.asyncio
    async def test_api_creation(self):
        """测试API创建"""
        api = create_api()
        assert isinstance(api, DouyinLiveAPI)
    
    @pytest.mark.asyncio
    async def test_api_factory(self):
        """测试API工厂"""
        factory = APIFactory()
        api = factory.create_api()
        assert isinstance(api, DouyinLiveAPI)
    
    @pytest.mark.asyncio
    async def test_connection_management(self, api_instance, mock_websocket):
        """测试连接管理"""
        api = api_instance
        
        # 模拟连接
        with patch.object(api.connection_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = True
            
            result = await api.connect("123456")
            assert result is True
            mock_connect.assert_called_once_with("123456")
    
    @pytest.mark.asyncio
    async def test_message_subscription(self, api_instance):
        """测试消息订阅"""
        api = api_instance
        
        # 订阅消息
        handler_called = False
        
        def message_handler(message):
            nonlocal handler_called
            handler_called = True
        
        api.subscribe(MessageType.CHAT, message_handler)
        
        # 模拟消息处理
        test_message = DouyinMessage(
            message_type=MessageType.CHAT,
            user_id="123",
            username="test",
            content="hello",
            timestamp=now(),
            room_id="456"
        )
        
        # 触发消息处理
        await api.message_stream_manager._handle_message(test_message)
        assert handler_called is True
    
    @pytest.mark.asyncio
    async def test_error_handling_in_api(self, api_instance):
        """测试API中的错误处理"""
        api = api_instance
        
        # 测试连接失败
        with patch.object(api.connection_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.side_effect = NetworkError("Connection failed")
            
            with pytest.raises(NetworkError):
                await api.connect("123456")


# ================================
# 工具函数测试
# ================================

class TestUtils:
    """工具函数测试"""
    
    def test_time_utils(self):
        """测试时间工具"""
        # 测试当前时间
        current_time = TimeUtils.now()
        assert isinstance(current_time, datetime)
        
        # 测试时间戳
        ts = TimeUtils.timestamp()
        assert isinstance(ts, float)
        assert ts > 0
        
        # 测试时间戳转换
        dt = TimeUtils.from_timestamp(ts)
        assert isinstance(dt, datetime)
        
        # 测试持续时间格式化
        assert TimeUtils.format_duration(0.5) == "500.0ms"
        assert TimeUtils.format_duration(65) == "1m5.0s"
        assert TimeUtils.format_duration(3665) == "1h1m5.0s"
    
    def test_string_utils(self):
        """测试字符串工具"""
        # 测试ID生成
        id1 = StringUtils.generate_id("test")
        id2 = StringUtils.generate_id("test")
        assert id1 != id2
        assert id1.startswith("test_")
        
        # 测试文件名清理
        filename = StringUtils.sanitize_filename("test<>file?.txt")
        assert "<" not in filename
        assert ">" not in filename
        assert "?" not in filename
        
        # 测试文本截断
        text = StringUtils.truncate("Hello World", 5)
        assert text == "He..."
        
        # 测试敏感信息遮蔽
        masked = StringUtils.mask_sensitive("1234567890", keep_start=2, keep_end=2)
        assert masked == "12******90"
    
    def test_validation_utils(self):
        """测试验证工具"""
        # 测试房间ID验证
        assert ValidationUtils.validate_room_id("123456") is True
        assert ValidationUtils.validate_room_id("abc123") is False
        assert ValidationUtils.validate_room_id("") is False
        
        # 测试URL验证
        assert ValidationUtils.validate_url("https://www.example.com") is True
        assert ValidationUtils.validate_url("invalid-url") is False
        
        # 测试JSON验证
        assert ValidationUtils.validate_json('{"key": "value"}') is True
        assert ValidationUtils.validate_json('invalid json') is False
    
    def test_data_utils(self):
        """测试数据工具"""
        # 测试字典合并
        dict1 = {"a": 1, "b": {"c": 2}}
        dict2 = {"b": {"d": 3}, "e": 4}
        merged = DataUtils.deep_merge(dict1, dict2)
        
        assert merged["a"] == 1
        assert merged["b"]["c"] == 2
        assert merged["b"]["d"] == 3
        assert merged["e"] == 4
        
        # 测试字典扁平化
        nested = {"a": {"b": {"c": 1}}}
        flattened = DataUtils.flatten_dict(nested)
        assert flattened["a.b.c"] == 1
        
        # 测试安全获取
        data = {"a": {"b": {"c": 1}}}
        assert DataUtils.safe_get(data, "a.b.c") == 1
        assert DataUtils.safe_get(data, "a.b.d", "default") == "default"
        
        # 测试哈希计算
        hash1 = DataUtils.calculate_hash("test")
        hash2 = DataUtils.calculate_hash("test")
        assert hash1 == hash2
        
        hash3 = DataUtils.calculate_hash("different")
        assert hash1 != hash3
    
    @pytest.mark.asyncio
    async def test_async_utils(self):
        """测试异步工具"""
        # 测试超时执行
        async def quick_task():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await AsyncUtils.run_with_timeout(quick_task(), 1.0)
        assert result == "success"
        
        # 测试超时
        async def slow_task():
            await asyncio.sleep(2.0)
            return "too slow"
        
        result = await AsyncUtils.run_with_timeout(slow_task(), 0.1, "timeout")
        assert result == "timeout"
        
        # 测试重试机制
        attempt_count = 0
        
        async def failing_task():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError("Not ready yet")
            return "success"
        
        result = await AsyncUtils.retry_async(failing_task, max_retries=3, delay=0.01)
        assert result == "success"
        assert attempt_count == 3
    
    def test_performance_monitor(self):
        """测试性能监控"""
        with PerformanceMonitor("test_operation") as monitor:
            time.sleep(0.1)
        
        assert monitor.duration is not None
        assert monitor.duration >= 0.1
    
    def test_convenience_functions(self):
        """测试便捷函数"""
        # 测试全局函数
        current_time = now()
        assert isinstance(current_time, datetime)
        
        ts = timestamp()
        assert isinstance(ts, float)
        
        id_str = generate_id("test")
        assert isinstance(id_str, str)
        assert id_str.startswith("test_")
        
        duration_str = format_duration(1.5)
        assert duration_str == "1.5s"
        
        data = {"a": {"b": 1}}
        value = safe_get(data, "a.b")
        assert value == 1
        
        hash_str = calculate_hash("test")
        assert isinstance(hash_str, str)
        assert len(hash_str) == 32  # MD5 hash length


# ================================
# 集成测试
# ================================

class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_module_initialization(self, sample_config, tmp_path):
        """测试模块初始化"""
        # 创建临时配置文件
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps(sample_config))
        
        # 初始化模块
        init_module(config_path=str(config_file), log_level="DEBUG")
        
        # 验证配置已加载
        config_manager = get_config_manager()
        assert config_manager.get("api.timeout") == 30
    
    @pytest.mark.asyncio
    async def test_quick_start(self):
        """测试快速开始功能"""
        message_received = False
        
        async def test_handler(message):
            nonlocal message_received
            message_received = True
        
        # 模拟快速开始（不实际连接）
        with patch('douyin_live_fecter_module.api.DouyinLiveAPI.connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = True
            
            api = await quick_start("123456", test_handler)
            assert isinstance(api, DouyinLiveAPI)
            mock_connect.assert_called_once_with("123456")
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        # 模拟网络连通性检查
        with patch('douyin_live_fecter_module.utils.NetworkUtils.check_connectivity', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = True
            
            status = await health_check()
            
            assert status["module"] == "DouyinLiveWebFetcher API封装"
            assert status["version"] == "1.0.0"
            assert status["status"] in ["healthy", "degraded"]
            assert "checks" in status
    
    @pytest.mark.asyncio
    async def test_end_to_end_message_flow(self, sample_message):
        """测试端到端消息流"""
        # 创建API实例
        api = create_api()
        
        # 设置消息处理器
        received_messages = []
        
        def message_handler(message):
            received_messages.append(message)
        
        api.subscribe(MessageType.CHAT, message_handler)
        
        # 模拟消息适配和处理
        adapter_manager = get_adapter_manager()
        adapted_message = adapter_manager.adapt_message(sample_message)
        
        # 直接调用消息处理器
        await api.message_stream_manager._handle_message(adapted_message)
        
        # 验证消息已被处理
        assert len(received_messages) == 1
        assert received_messages[0].message_type == MessageType.CHAT
        assert received_messages[0].content == sample_message["content"]
    
    @pytest.mark.asyncio
    async def test_error_recovery_flow(self):
        """测试错误恢复流程"""
        api = create_api()
        
        # 模拟连接失败和重试
        connection_attempts = 0
        
        async def mock_connect(room_id):
            nonlocal connection_attempts
            connection_attempts += 1
            if connection_attempts < 3:
                raise NetworkError("Connection failed")
            return True
        
        with patch.object(api.connection_manager, 'connect', side_effect=mock_connect):
            # 使用重试机制
            result = await AsyncUtils.retry_async(
                lambda: api.connection_manager.connect("123456"),
                max_retries=3,
                delay=0.01
            )
            
            assert result is True
            assert connection_attempts == 3
    
    def test_component_integration(self):
        """测试组件集成"""
        # 测试所有管理器都能正常获取
        config_manager = get_config_manager()
        state_manager = get_state_manager()
        cache_manager = get_cache_manager()
        adapter_manager = get_adapter_manager()
        
        assert config_manager is not None
        assert state_manager is not None
        assert cache_manager is not None
        assert adapter_manager is not None
        
        # 测试管理器之间的协作
        # 配置管理器设置缓存配置
        config_manager.set("cache.ttl", 300)
        
        # 缓存管理器应该能读取配置
        cache_ttl = config_manager.get("cache.ttl")
        assert cache_ttl == 300


# ================================
# 性能测试
# ================================

class TestPerformance:
    """性能测试"""
    
    def test_message_adaptation_performance(self, sample_message):
        """测试消息适配性能"""
        adapter = ChatMessageAdapter()
        
        # 测试大量消息适配
        start_time = time.perf_counter()
        
        for _ in range(1000):
            adapter.adapt(sample_message)
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # 应该在合理时间内完成
        assert duration < 1.0  # 1秒内完成1000次适配
        
        # 平均每次适配时间
        avg_time = duration / 1000
        assert avg_time < 0.001  # 每次适配少于1毫秒
    
    def test_cache_performance(self):
        """测试缓存性能"""
        cache = MemoryCacheBackend(max_size=10000)
        
        # 测试大量写入
        start_time = time.perf_counter()
        
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}")
        
        write_time = time.perf_counter() - start_time
        
        # 测试大量读取
        start_time = time.perf_counter()
        
        for i in range(1000):
            cache.get(f"key_{i}")
        
        read_time = time.perf_counter() - start_time
        
        # 性能断言
        assert write_time < 0.1  # 写入应该很快
        assert read_time < 0.05  # 读取应该更快
        
        print(f"Cache write time: {write_time:.4f}s")
        print(f"Cache read time: {read_time:.4f}s")
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """测试并发操作性能"""
        api = create_api()
        
        # 模拟并发消息处理
        async def process_message(message_id):
            message = DouyinMessage(
                message_type=MessageType.CHAT,
                user_id=str(message_id),
                username=f"user_{message_id}",
                content=f"message_{message_id}",
                timestamp=now(),
                room_id="123456"
            )
            
            # 模拟消息处理
            await asyncio.sleep(0.001)  # 模拟处理时间
            return message
        
        # 并发处理100条消息
        start_time = time.perf_counter()
        
        tasks = [process_message(i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        assert len(results) == 100
        assert duration < 1.0  # 应该在1秒内完成
        
        print(f"Concurrent processing time: {duration:.4f}s")


# ================================
# 运行测试
# ================================

if __name__ == "__main__":
    # 运行所有测试
    pytest.main([
        __file__,
        "-v",  # 详细输出
        "-s",  # 显示print输出
        "--tb=short",  # 简短的traceback
        "--durations=10",  # 显示最慢的10个测试
    ])