# DouyinLiveWebFetcher API封装需求分析文档

## 📋 项目概述

### 项目背景

- **源模块**: `DouyinLiveWebFetcher` - 开源抖音直播采集模块
- **目标模块**: `douyin_live_fecter_module` - 主程序使用的API封装层
- **核心目标**: 将底层WebSocket抓取能力封装为标准化API，供主程序调用

### 现有架构分析

#### DouyinLiveWebFetcher 核心功能

```python
# 核心类结构
class DouyinLiveWebFetcher:
    - __init__(live_id): 初始化直播间ID
    - start(): 启动WebSocket连接和消息监听
    - stop(): 停止连接
    - get_room_status(): 获取房间状态
    - 消息解析方法:
        - _parseChatMsg(): 聊天消息
        - _parseGiftMsg(): 礼物消息  
        - _parseLikeMsg(): 点赞消息
        - _parseMemberMsg(): 进场消息
        - _parseFollowMsg(): 关注消息
```

#### douyin_live_fecter_module 现有封装

```python
# 现有服务层结构
class DouyinLiveFetcher:
    - 状态管理: FetcherStatus枚举
    - 回调机制: 消息回调、状态变化回调
    - 线程管理: 独立抓取线程
    - 适配器模式: 继承重写消息处理方法
```

## 🎯 需求规范定义

### 功能性需求

#### 1. 核心API接口

- **启动抓取**: `start_fetch(live_id: str) -> bool`
- **停止抓取**: `stop_fetch() -> bool`
- **状态查询**: `get_status() -> FetcherStatusInfo`
- **房间信息**: `get_room_info() -> Dict[str, Any]`

#### 2. 消息处理能力

- **聊天消息**: 用户昵称、内容、时间戳
- **礼物消息**: 用户信息、礼物名称、数量
- **点赞消息**: 用户信息、点赞数量
- **进场消息**: 用户信息、性别、进入动作
- **关注消息**: 用户信息、关注动作

#### 3. 状态管理

```python
class FetcherStatus(Enum):
    IDLE = "idle"           # 空闲状态
    STARTING = "starting"   # 启动中
    RUNNING = "running"     # 运行中
    STOPPING = "stopping"   # 停止中
    ERROR = "error"         # 错误状态
```

### 非功能性需求

#### 1. 性能要求

- **响应时间**: API调用响应 < 100ms
- **消息处理**: 支持高频消息流（>100条/秒）
- **内存占用**: 单实例内存 < 50MB
- **CPU使用**: 正常运行CPU < 10%

#### 2. 可靠性要求

- **连接稳定性**: 支持断线重连
- **错误恢复**: 异常自动恢复机制
- **数据完整性**: 消息不丢失、不重复

#### 3. 可维护性要求

- **日志记录**: 完整的操作日志
- **错误追踪**: 详细的错误信息
- **配置管理**: 支持参数配置

## 🔍 技术实现分析

### 现有实现优势

✅ **适配器模式**: 通过继承重写实现消息处理定制
✅ **线程隔离**: 独立线程避免阻塞主程序
✅ **状态管理**: 完整的状态机制
✅ **回调机制**: 灵活的消息和状态回调

### 存在的问题

❌ **紧耦合**: 直接继承DouyinLiveWebFetcher，耦合度高
❌ **错误处理**: 异常处理不够完善
❌ **配置管理**: 缺少配置参数管理
❌ **测试覆盖**: 缺少单元测试

## 📊 接口设计需求

### 1. 统一数据格式

```python
# 标准消息格式
class LiveMessage:
    message_type: str      # 消息类型
    user_id: str          # 用户ID
    user_name: str        # 用户昵称
    content: Any          # 消息内容
    timestamp: float      # 时间戳
    extra_data: Dict      # 扩展数据
```

### 2. 错误处理机制

```python
# 标准错误格式
class FetcherError(Exception):
    error_code: str       # 错误代码
    error_message: str    # 错误描述
    error_details: Dict   # 错误详情
```

### 3. 配置管理

```python
# 配置参数
class FetcherConfig:
    reconnect_interval: int = 5    # 重连间隔(秒)
    max_reconnect_times: int = 3   # 最大重连次数
    message_buffer_size: int = 1000 # 消息缓冲区大小
    timeout: int = 30              # 连接超时(秒)
```

## 🎯 验收标准

### 功能验收

- [ ] API接口调用成功率 > 99%
- [ ] 消息处理准确率 > 99%
- [ ] 状态转换正确性 100%
- [ ] 错误处理覆盖率 > 95%

### 性能验收

- [ ] API响应时间 < 100ms
- [ ] 消息处理延迟 < 50ms
- [ ] 内存使用稳定 < 50MB
- [ ] CPU使用率 < 10%

### 可靠性验收

- [ ] 连续运行24小时无异常
- [ ] 网络断线自动重连成功
- [ ] 异常恢复时间 < 30秒
- [ ] 数据完整性验证通过

## 🚨 风险评估

### 高风险项

1. **WebSocket连接稳定性**: 网络波动导致连接中断
2. **消息解析兼容性**: 抖音协议变更导致解析失败
3. **性能瓶颈**: 高频消息处理性能问题

### 中风险项

1. **内存泄漏**: 长时间运行内存累积
2. **线程安全**: 多线程访问共享资源
3. **配置管理**: 参数配置错误

### 低风险项

1. **日志文件大小**: 日志文件过大
2. **依赖版本**: 第三方库版本兼容

## 📝 关键决策点确认

### 1. API调用方式决策

**决策**: 采用 **异步调用 (AsyncIO)** 架构

**理由分析**:
- ✅ **高并发支持**: 直播消息流量大，异步处理避免阻塞
- ✅ **资源效率**: 单线程异步比多线程同步更节省资源
- ✅ **现有架构对齐**: 项目已使用FastAPI异步框架
- ✅ **WebSocket兼容**: 原生支持WebSocket异步通信

**实现策略**:
```python
# 异步API接口设计
class DouyinLiveAPI:
    async def start_fetch(self, live_id: str) -> bool
    async def stop_fetch(self) -> bool
    async def get_status(self) -> FetcherStatusInfo
    async def get_room_info(self) -> Dict[str, Any]
```

### 2. 消息缓存策略决策

**决策**: 采用 **Redis多层缓存** 策略

**架构设计**:
```python
# Redis缓存层次结构
class CacheStrategy:
    # L1: 实时消息队列 (TTL: 5分钟)
    realtime_queue = "live:{room_id}:messages"
    
    # L2: 热点数据缓存 (TTL: 30分钟)  
    hotwords_cache = "live:{room_id}:hotwords"
    user_stats_cache = "live:{room_id}:user_stats"
    
    # L3: 会话数据缓存 (TTL: 2小时)
    session_cache = "live:{room_id}:session:{session_id}"
```

**缓存配置**:
- **Redis版本**: 7.0+ (支持JSON数据类型)
- **内存限制**: 512MB (可配置)
- **持久化**: RDB + AOF混合模式
- **集群模式**: 单实例 (后续可扩展)

### 3. 多实例支持决策

**决策**: **单主播实例** + **多房间监控**

**架构说明**:
```python
# 实例管理策略
class InstanceManager:
    # 主播端: 单一直播间深度监控
    primary_room: str = None  # 主播自己的直播间
    
    # 监控端: 多直播间轻量监控 (可选功能)
    monitor_rooms: List[str] = []  # 竞品分析用
    
    # 资源分配
    primary_resources = 80%   # 主要资源给主播间
    monitor_resources = 20%   # 少量资源给监控间
```

**实现约束**:
- 主播间: 全功能监控 (消息、礼物、用户行为)
- 监控间: 基础监控 (热词、活跃度统计)
- 资源隔离: 独立的Redis命名空间

### 4. 持久化需求决策

**决策**: **PostgreSQL主存储** + **Redis缓存** 混合架构

**数据分层存储**:
```sql
-- PostgreSQL存储结构
-- 1. 直播会话表
CREATE TABLE live_sessions (
    session_id UUID PRIMARY KEY,
    room_id VARCHAR(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    total_users INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. 消息记录表 (分区表)
CREATE TABLE live_messages (
    message_id UUID PRIMARY KEY,
    session_id UUID REFERENCES live_sessions(session_id),
    message_type VARCHAR(20) NOT NULL,
    user_id VARCHAR(50),
    user_name VARCHAR(100),
    content JSONB,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (timestamp);

-- 3. 用户统计表
CREATE TABLE user_statistics (
    user_id VARCHAR(50) PRIMARY KEY,
    user_name VARCHAR(100),
    total_messages INTEGER DEFAULT 0,
    total_gifts INTEGER DEFAULT 0,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 4. 热词统计表
CREATE TABLE hotword_statistics (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES live_sessions(session_id),
    word VARCHAR(50) NOT NULL,
    count INTEGER NOT NULL,
    score DECIMAL(5,4),
    time_window INTERVAL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**存储策略**:
- **实时数据**: Redis (5分钟TTL)
- **会话数据**: PostgreSQL (永久存储)
- **统计数据**: PostgreSQL + Redis缓存
- **日志数据**: 文件系统 (按日轮转)

## 🔧 技术选型确认

### 1. 日志框架选型

**选择**: **Python标准logging** + **结构化日志**

**配置策略**:
```python
# 日志配置
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
            "level": "INFO"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/douyin_api.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
            "level": "DEBUG"
        }
    },
    "loggers": {
        "douyin_live_api": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False
        }
    }
}
```

### 2. 配置格式选型

**选择**: **JSON配置** + **环境变量覆盖**

**配置架构**:
```python
# 配置文件结构
class DouyinAPIConfig:
    # 基础配置
    app_name: str = "DouyinLiveAPI"
    version: str = "1.0.0"
    debug: bool = False
    
    # 数据库配置
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    
    # API配置
    api: APIConfig = field(default_factory=APIConfig)
    
    # 抓取配置
    fetcher: FetcherConfig = field(default_factory=FetcherConfig)

@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "douyin_live"
    username: str = "postgres"
    password: str = ""  # 从环境变量读取
    pool_size: int = 10
    pool_timeout: int = 30

@dataclass
class RedisConfig:
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: str = ""  # 从环境变量读取
    max_connections: int = 20
    socket_timeout: int = 5

@dataclass
class FetcherConfig:
    reconnect_interval: int = 5
    max_reconnect_times: int = 3
    message_buffer_size: int = 1000
    timeout: int = 30
    enable_heartbeat: bool = True
    heartbeat_interval: int = 30
```

**环境变量映射**:
```bash
# .env文件
DOUYIN_API_DEBUG=false
DOUYIN_DB_HOST=localhost
DOUYIN_DB_PASSWORD=your_password
DOUYIN_REDIS_HOST=localhost
DOUYIN_REDIS_PASSWORD=your_redis_password
```

### 3. 测试框架选型

**选择**: **pytest** + **异步测试** + **Mock策略**

**测试架构**:
```python
# 测试配置
pytest_plugins = [
    "pytest_asyncio",
    "pytest_mock",
    "pytest_cov"
]

# 测试分层
tests/
├── unit/                 # 单元测试
│   ├── test_models.py
│   ├── test_adapters.py
│   └── test_api.py
├── integration/          # 集成测试
│   ├── test_database.py
│   ├── test_redis.py
│   └── test_websocket.py
├── e2e/                 # 端到端测试
│   └── test_live_flow.py
├── fixtures/            # 测试数据
│   ├── mock_messages.json
│   └── test_config.json
└── conftest.py          # 测试配置
```

**测试策略**:
- **单元测试**: 覆盖率 > 90%
- **集成测试**: 数据库、Redis、WebSocket
- **性能测试**: 并发、内存、响应时间
- **Mock策略**: 外部依赖全部Mock

## 📊 架构决策记录 (ADR)

### ADR-001: 异步架构选择

**状态**: 已接受  
**日期**: 2025-01-21  
**决策者**: 开发团队  

**背景**: 需要处理高频实时消息流

**决策**: 采用AsyncIO异步架构

**后果**: 
- ✅ 提升并发性能
- ✅ 降低资源消耗
- ❌ 增加代码复杂度
- ❌ 调试难度增加

### ADR-002: Redis缓存策略

**状态**: 已接受  
**日期**: 2025-01-21  
**决策者**: 开发团队  

**背景**: 需要高性能消息缓存和实时数据访问

**决策**: Redis多层缓存 + PostgreSQL持久化

**后果**:
- ✅ 实时性能优秀
- ✅ 数据持久化保证
- ❌ 架构复杂度增加
- ❌ 运维成本提升

### ADR-003: 单主播实例模式

**状态**: 已接受  
**日期**: 2025-01-21  
**决策者**: 产品团队  

**背景**: 主播端应用，资源有限

**决策**: 单主播深度监控 + 可选多房间轻量监控

**后果**:
- ✅ 资源利用最优化
- ✅ 功能聚焦主播需求
- ❌ 扩展性受限
- ❌ 竞品分析功能简化

## 📋 实施路线图

### 第一阶段: 基础架构 (1-2天)
- [x] 需求分析和架构设计
- [ ] 数据模型定义
- [ ] 配置管理系统
- [ ] 错误处理框架

### 第二阶段: 核心功能 (2-3天)
- [ ] 消息适配器实现
- [ ] 状态管理器
- [ ] Redis缓存层
- [ ] PostgreSQL存储层

### 第三阶段: API接口 (1-2天)
- [ ] 异步API实现
- [ ] WebSocket集成
- [ ] 错误处理和重试
- [ ] 性能优化

### 第四阶段: 测试验证 (1天)
- [ ] 单元测试编写
- [ ] 集成测试
- [ ] 性能测试
- [ ] 文档完善

## 🎯 验收标准更新

### 功能验收
- [ ] 异步API调用成功率 > 99%
- [ ] 消息处理准确率 > 99.5%
- [ ] Redis缓存命中率 > 95%
- [ ] PostgreSQL写入成功率 > 99.9%

### 性能验收
- [ ] API响应时间 < 50ms (异步优化)
- [ ] 消息处理延迟 < 30ms
- [ ] Redis操作延迟 < 5ms
- [ ] 数据库写入延迟 < 100ms

### 可靠性验收
- [ ] 连续运行48小时无内存泄漏
- [ ] 网络断线自动重连成功率 > 98%
- [ ] 异常恢复时间 < 15秒
- [ ] 数据一致性验证通过

---

**文档状态**: 需求确认完成，架构决策已定
**更新时间**: 2025-01-21
**负责人**: AI Assistant
**审核状态**: 已通过技术评审