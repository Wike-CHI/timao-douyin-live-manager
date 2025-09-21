"""
pytest配置文件

提供全局测试配置、夹具和工具函数
"""

import pytest
import asyncio
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ================================
# pytest配置
# ================================

def pytest_configure(config):
    """pytest配置"""
    # 设置测试标记
    config.addinivalue_line(
        "markers", "integration: 标记集成测试"
    )
    config.addinivalue_line(
        "markers", "performance: 标记性能测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记慢速测试"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 为异步测试添加asyncio标记
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


# ================================
# 异步测试支持
# ================================

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ================================
# 临时目录和文件
# ================================

@pytest.fixture
def temp_dir():
    """临时目录夹具"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_config_file(temp_dir):
    """临时配置文件"""
    config_data = {
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
        },
        "douyin": {
            "room_id": "123456",
            "fetch_interval": 1.0
        }
    }
    
    config_file = temp_dir / "test_config.json"
    import json
    config_file.write_text(json.dumps(config_data, indent=2))
    
    return config_file


# ================================
# 模拟对象
# ================================

@pytest.fixture
def mock_websocket():
    """模拟WebSocket连接"""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock()
    ws.close = AsyncMock()
    ws.closed = False
    
    # 模拟消息接收
    messages = [
        '{"type": "chat", "user_id": "123", "username": "test", "content": "hello", "timestamp": 1234567890000, "room_id": "456"}',
        '{"type": "gift", "user_id": "456", "username": "giver", "gift_name": "rose", "timestamp": 1234567891000, "room_id": "456"}'
    ]
    
    async def mock_recv():
        if messages:
            return messages.pop(0)
        await asyncio.sleep(0.1)
        return '{"type": "heartbeat"}'
    
    ws.recv.side_effect = mock_recv
    return ws


@pytest.fixture
def mock_redis():
    """模拟Redis客户端"""
    redis_mock = AsyncMock()
    
    # 内存存储模拟Redis行为
    storage = {}
    
    async def mock_get(key):
        return storage.get(key)
    
    async def mock_set(key, value, ex=None):
        storage[key] = value
        return True
    
    async def mock_delete(key):
        return storage.pop(key, None) is not None
    
    async def mock_exists(key):
        return key in storage
    
    async def mock_keys(pattern="*"):
        if pattern == "*":
            return list(storage.keys())
        # 简单模式匹配
        import fnmatch
        return [k for k in storage.keys() if fnmatch.fnmatch(k, pattern)]
    
    redis_mock.get.side_effect = mock_get
    redis_mock.set.side_effect = mock_set
    redis_mock.delete.side_effect = mock_delete
    redis_mock.exists.side_effect = mock_exists
    redis_mock.keys.side_effect = mock_keys
    
    return redis_mock


@pytest.fixture
def mock_database():
    """模拟数据库连接"""
    db_mock = AsyncMock()
    
    # 内存存储模拟数据库
    tables = {
        "messages": [],
        "sessions": [],
        "statistics": []
    }
    
    async def mock_execute(query, *args):
        # 简单的SQL模拟
        if "INSERT" in query.upper():
            return {"rowcount": 1}
        elif "SELECT" in query.upper():
            return {"rows": []}
        elif "UPDATE" in query.upper():
            return {"rowcount": 1}
        elif "DELETE" in query.upper():
            return {"rowcount": 1}
        return {"rowcount": 0}
    
    async def mock_fetch_one(query, *args):
        return {"id": 1, "data": "test"}
    
    async def mock_fetch_all(query, *args):
        return [{"id": 1, "data": "test1"}, {"id": 2, "data": "test2"}]
    
    db_mock.execute.side_effect = mock_execute
    db_mock.fetch_one.side_effect = mock_fetch_one
    db_mock.fetch_all.side_effect = mock_fetch_all
    
    return db_mock


# ================================
# 测试数据
# ================================

@pytest.fixture
def sample_messages():
    """示例消息数据"""
    import time
    
    return [
        {
            "type": "chat",
            "user_id": "123456",
            "username": "测试用户1",
            "content": "Hello World",
            "timestamp": int(time.time() * 1000),
            "room_id": "789012"
        },
        {
            "type": "gift",
            "user_id": "654321",
            "username": "测试用户2",
            "gift_name": "玫瑰花",
            "gift_count": 1,
            "timestamp": int(time.time() * 1000),
            "room_id": "789012"
        },
        {
            "type": "like",
            "user_id": "111222",
            "username": "测试用户3",
            "timestamp": int(time.time() * 1000),
            "room_id": "789012"
        },
        {
            "type": "follow",
            "user_id": "333444",
            "username": "测试用户4",
            "timestamp": int(time.time() * 1000),
            "room_id": "789012"
        }
    ]


@pytest.fixture
def sample_config():
    """示例配置数据"""
    return {
        "api": {
            "timeout": 30,
            "retry_count": 3,
            "retry_delay": 1.0,
            "max_connections": 10
        },
        "cache": {
            "ttl": 300,
            "max_size": 1000,
            "cleanup_interval": 60
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "douyin_api.log"
        },
        "douyin": {
            "room_id": "123456",
            "fetch_interval": 1.0,
            "reconnect_delay": 5.0,
            "max_reconnect_attempts": 5
        },
        "database": {
            "host": "localhost",
            "port": 5432,
            "database": "douyin_test",
            "username": "test_user",
            "password": "test_pass"
        },
        "redis": {
            "host": "localhost",
            "port": 6379,
            "database": 0,
            "password": None
        }
    }


# ================================
# 环境设置
# ================================

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """设置测试环境"""
    # 设置测试环境变量
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    
    # 禁用实际的网络连接
    monkeypatch.setenv("DISABLE_NETWORK", "true")
    
    # 设置测试数据目录
    test_data_dir = Path(__file__).parent / "data"
    monkeypatch.setenv("TEST_DATA_DIR", str(test_data_dir))


@pytest.fixture
def isolated_module():
    """隔离的模块环境"""
    # 保存原始状态
    original_modules = sys.modules.copy()
    
    yield
    
    # 恢复原始状态
    modules_to_remove = []
    for module_name in sys.modules:
        if module_name.startswith('douyin_live_fecter_module'):
            modules_to_remove.append(module_name)
    
    for module_name in modules_to_remove:
        if module_name in original_modules:
            sys.modules[module_name] = original_modules[module_name]
        else:
            del sys.modules[module_name]


# ================================
# 性能测试工具
# ================================

@pytest.fixture
def performance_monitor():
    """性能监控工具"""
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.duration = None
        
        def start(self):
            self.start_time = time.perf_counter()
        
        def stop(self):
            self.end_time = time.perf_counter()
            if self.start_time:
                self.duration = self.end_time - self.start_time
        
        def __enter__(self):
            self.start()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.stop()
    
    return PerformanceMonitor


# ================================
# 日志捕获
# ================================

@pytest.fixture
def log_capture():
    """日志捕获工具"""
    import logging
    from io import StringIO
    
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)
    
    # 获取根日志记录器
    logger = logging.getLogger('douyin_live_fecter_module')
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    yield log_stream
    
    # 清理
    logger.removeHandler(handler)


# ================================
# 异步测试工具
# ================================

@pytest.fixture
def async_test_timeout():
    """异步测试超时设置"""
    return 10.0  # 10秒超时


@pytest.fixture
async def async_cleanup():
    """异步清理工具"""
    cleanup_tasks = []
    
    def add_cleanup(coro):
        cleanup_tasks.append(coro)
    
    yield add_cleanup
    
    # 执行清理任务
    for task in cleanup_tasks:
        try:
            await task
        except Exception as e:
            print(f"清理任务失败: {e}")


# ================================
# 测试标记
# ================================

# 集成测试标记
integration = pytest.mark.integration

# 性能测试标记
performance = pytest.mark.performance

# 慢速测试标记
slow = pytest.mark.slow

# 需要网络的测试标记
requires_network = pytest.mark.skipif(
    os.getenv("DISABLE_NETWORK") == "true",
    reason="网络测试被禁用"
)

# 需要Redis的测试标记
requires_redis = pytest.mark.skipif(
    os.getenv("REDIS_URL") is None,
    reason="需要Redis连接"
)

# 需要数据库的测试标记
requires_database = pytest.mark.skipif(
    os.getenv("DATABASE_URL") is None,
    reason="需要数据库连接"
)


# ================================
# 测试工具函数
# ================================

def assert_message_equal(msg1, msg2, ignore_timestamp=True):
    """断言消息相等"""
    if ignore_timestamp:
        # 忽略时间戳比较
        fields_to_compare = ['message_type', 'user_id', 'username', 'content', 'room_id']
        for field in fields_to_compare:
            if hasattr(msg1, field) and hasattr(msg2, field):
                assert getattr(msg1, field) == getattr(msg2, field)
    else:
        assert msg1 == msg2


def create_test_message(message_type="chat", **kwargs):
    """创建测试消息"""
    import time
    from douyin_live_fecter_module.models import MessageType
    
    default_data = {
        "type": message_type,
        "user_id": "123456",
        "username": "测试用户",
        "content": "测试消息",
        "timestamp": int(time.time() * 1000),
        "room_id": "789012"
    }
    
    default_data.update(kwargs)
    return default_data


async def wait_for_condition(condition_func, timeout=5.0, interval=0.1):
    """等待条件满足"""
    import asyncio
    
    start_time = asyncio.get_event_loop().time()
    
    while True:
        if condition_func():
            return True
        
        current_time = asyncio.get_event_loop().time()
        if current_time - start_time > timeout:
            return False
        
        await asyncio.sleep(interval)


def mock_async_context_manager(mock_obj):
    """将模拟对象转换为异步上下文管理器"""
    async def aenter():
        return mock_obj
    
    async def aexit(exc_type, exc_val, exc_tb):
        pass
    
    mock_obj.__aenter__ = aenter
    mock_obj.__aexit__ = aexit
    
    return mock_obj