# 🔥 Redis 缓存配置指南

## 📌 为什么使用 Redis？

Redis 作为高性能内存数据库，为应用提供：

| 功能 | 说明 | 性能提升 |
|------|------|----------|
| 🚀 **会话管理** | 用户登录状态、JWT Token 黑名单 | 比数据库快 **100倍** |
| ⚡ **API 限流** | 防止恶意请求、保护服务稳定性 | 毫秒级响应 |
| 💾 **数据缓存** | 热点数据、配置信息、查询结果 | 减少 **80%** 数据库查询 |
| 📊 **实时计数** | 在线用户、消息队列、统计数据 | 原子操作，高并发 |
| 🔔 **消息订阅** | 实时通知、事件广播 | 发布/订阅模式 |

---

## 🚀 快速开始

### 方式一：Docker（推荐）

```bash
# 使用项目提供的 docker-compose 配置
docker-compose -f docker-compose.mysql.yml up -d redis

# 验证 Redis 启动
docker logs timao-redis
```

### 方式二：本地安装

#### Windows:
```bash
# Chocolatey
choco install redis-64

# 启动服务
redis-server

# 测试连接
redis-cli ping
# 输出: PONG
```

#### macOS:
```bash
# Homebrew
brew install redis

# 启动服务
brew services start redis

# 测试连接
redis-cli ping
```

#### Linux (Ubuntu/Debian):
```bash
# 安装
sudo apt update
sudo apt install redis-server

# 启动服务
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 测试连接
redis-cli ping
```

---

## ⚙️ 配置说明

### .env 配置

```bash
# Redis 基本配置
REDIS_ENABLED=true              # 启用 Redis（默认 true）
REDIS_HOST=localhost            # Redis 服务器地址
REDIS_PORT=6379                 # Redis 端口
REDIS_DB=0                      # 数据库编号（0-15）
REDIS_PASSWORD=                 # 密码（可选）

# 连接池配置
REDIS_MAX_CONNECTIONS=10        # 最大连接数
REDIS_CACHE_TTL=3600           # 默认缓存时间（秒）
```

### 生产环境配置

```bash
# 使用密码保护
REDIS_PASSWORD=your_strong_password

# 使用专用 Redis 服务器
REDIS_HOST=redis.production.com
REDIS_PORT=6379

# 增加连接池
REDIS_MAX_CONNECTIONS=50

# 调整缓存时间
REDIS_CACHE_TTL=7200  # 2小时
```

---

## 💻 代码示例

### 1. 基本使用

```python
from server.utils.redis_manager import get_redis

# 获取 Redis 实例
redis = get_redis()

# 检查是否可用
if not redis or not redis.is_enabled():
    print("Redis 未启用，使用内存存储")
    return

# 设置缓存
redis.set("user:1001", {"name": "张三", "role": "admin"}, ttl=3600)

# 获取缓存
user = redis.get("user:1001")
print(user)  # {'name': '张三', 'role': 'admin'}

# 删除缓存
redis.delete("user:1001")
```

### 2. 会话管理

```python
from server.utils.redis_manager import get_redis

redis = get_redis()

# 保存用户会话
def save_session(user_id: str, session_data: dict):
    """保存用户会话（24小时过期）"""
    redis.set(f"session:{user_id}", session_data, ttl=86400)

# 获取用户会话
def get_session(user_id: str):
    """获取用户会话"""
    return redis.get(f"session:{user_id}")

# 删除用户会话（登出）
def delete_session(user_id: str):
    """删除用户会话"""
    redis.delete(f"session:{user_id}")
```

### 3. API 限流

```python
from server.utils.redis_manager import get_redis

redis = get_redis()

def check_rate_limit(user_id: str, limit: int = 100, window: int = 60):
    """
    检查 API 调用频率
    
    Args:
        user_id: 用户 ID
        limit: 时间窗口内最大请求数
        window: 时间窗口（秒）
    
    Returns:
        是否允许请求
    """
    key = f"rate_limit:{user_id}"
    
    # 增加计数
    current = redis.incr(key)
    
    # 第一次设置过期时间
    if current == 1:
        redis.expire(key, window)
    
    # 检查是否超限
    return current <= limit

# 使用示例
if not check_rate_limit("user_123", limit=100, window=60):
    raise Exception("请求过于频繁，请稍后再试")
```

### 4. 数据缓存

```python
from server.utils.redis_manager import get_redis
from server.app.database import DatabaseManager

redis = get_redis()
db = DatabaseManager()

def get_user_by_id(user_id: str):
    """获取用户信息（带缓存）"""
    cache_key = f"user:{user_id}"
    
    # 先从缓存获取
    user = redis.get(cache_key)
    if user:
        print("✅ 从缓存获取")
        return user
    
    # 缓存未命中，从数据库查询
    print("⚠️ 缓存未命中，查询数据库")
    with db.get_session() as session:
        user = session.query(User).filter_by(id=user_id).first()
    
    if user:
        # 保存到缓存（1小时）
        redis.set(cache_key, user.to_dict(), ttl=3600)
    
    return user
```

### 5. 计数器

```python
from server.utils.redis_manager import get_redis

redis = get_redis()

# 增加在线用户数
def user_online(user_id: str):
    """用户上线"""
    redis.sadd("online_users", user_id)
    return redis.scard("online_users")  # 返回在线人数

# 减少在线用户数
def user_offline(user_id: str):
    """用户下线"""
    redis.srem("online_users", user_id)
    return redis.scard("online_users")

# 获取在线用户列表
def get_online_users():
    """获取所有在线用户"""
    return list(redis.smembers("online_users"))
```

### 6. 列表操作（消息队列）

```python
from server.utils.redis_manager import get_redis

redis = get_redis()

# 添加任务到队列
def add_task(task_data: dict):
    """添加任务"""
    redis.lpush("task_queue", task_data)

# 获取任务
def get_task():
    """获取任务（FIFO）"""
    tasks = redis.lrange("task_queue", -1, -1)
    if tasks:
        redis.ltrim("task_queue", 0, -2)  # 删除最后一个
        return tasks[0]
    return None
```

### 7. 哈希表操作

```python
from server.utils.redis_manager import get_redis

redis = get_redis()

# 保存用户配置
def save_user_config(user_id: str, config_key: str, config_value: any):
    """保存用户配置"""
    redis.hset(f"user_config:{user_id}", config_key, config_value)

# 获取用户配置
def get_user_config(user_id: str, config_key: str):
    """获取用户配置"""
    return redis.hget(f"user_config:{user_id}", config_key)

# 获取所有配置
def get_all_user_config(user_id: str):
    """获取用户所有配置"""
    return redis.hgetall(f"user_config:{user_id}")
```

---

## 🔧 高级配置

### Redis 持久化

在 `redis.conf` 中配置：

```conf
# RDB 快照（默认）
save 900 1      # 900秒内至少1个键变化则保存
save 300 10     # 300秒内至少10个键变化则保存
save 60 10000   # 60秒内至少10000个键变化则保存

# AOF 日志（更安全）
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec  # 每秒同步一次
```

### Redis 内存管理

```conf
# 最大内存
maxmemory 256mb

# 内存淘汰策略
maxmemory-policy allkeys-lru  # LRU 淘汰最少使用的键
```

### Docker Redis 配置

```yaml
redis:
  image: redis:7-alpine
  command: >
    redis-server
    --appendonly yes
    --appendfilename appendonly.aof
    --maxmemory 256mb
    --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data
```

---

## 📊 监控与调优

### 查看 Redis 状态

```bash
# 连接到 Redis
redis-cli

# 查看信息
INFO

# 查看内存使用
INFO memory

# 查看连接数
INFO clients

# 查看慢查询
SLOWLOG GET 10
```

### 性能监控

```python
from server.utils.redis_manager import get_redis

redis = get_redis()

# 测试连接
if redis.ping():
    print("✅ Redis 连接正常")

# 查看键数量
info = redis._client.info()
print(f"键数量: {info['db0']['keys']}")
print(f"内存使用: {info['used_memory_human']}")
```

---

## 🐛 故障排查

### Q1: Redis 连接失败

**检查服务是否运行：**

```bash
# Windows
tasklist | findstr redis

# macOS/Linux
ps aux | grep redis
```

**检查端口是否开放：**

```bash
netstat -tuln | grep 6379
telnet localhost 6379
```

### Q2: Redis 内存占用过高

**清理过期键：**

```bash
redis-cli
> FLUSHDB  # 清空当前数据库（谨慎使用）
> FLUSHALL  # 清空所有数据库（谨慎使用）
```

**设置过期时间：**

```python
# 所有缓存都设置过期时间
redis.set("key", "value", ttl=3600)
```

### Q3: Redis 密码错误

```bash
# .env 配置密码
REDIS_PASSWORD=your_password

# 连接测试
redis-cli -a your_password ping
```

---

## ✅ 最佳实践

### 1. 键命名规范

```python
# 使用命名空间
user:1001:profile
user:1001:settings
session:abc123
cache:product:5678
```

### 2. 设置合理的 TTL

```python
# 会话：24小时
redis.set("session:xxx", data, ttl=86400)

# 缓存：1小时
redis.set("cache:xxx", data, ttl=3600)

# 临时数据：5分钟
redis.set("temp:xxx", data, ttl=300)
```

### 3. 优雅降级

```python
def get_data(key: str):
    """获取数据（优雅降级）"""
    redis = get_redis()
    
    # Redis 可用时使用缓存
    if redis and redis.is_enabled():
        cached = redis.get(key)
        if cached:
            return cached
    
    # Redis 不可用或缓存未命中，从数据库获取
    data = query_from_database(key)
    
    # 尝试写入缓存
    if redis and redis.is_enabled():
        redis.set(key, data, ttl=3600)
    
    return data
```

### 4. 批量操作

```python
# ❌ 不好的做法（多次网络请求）
for user_id in user_ids:
    redis.set(f"user:{user_id}", get_user(user_id))

# ✅ 好的做法（使用管道）
pipe = redis._client.pipeline()
for user_id in user_ids:
    pipe.set(f"user:{user_id}", get_user(user_id))
pipe.execute()
```

---

## 🎯 应用场景

### 1. JWT Token 黑名单

```python
def logout(token: str):
    """登出，将 Token 加入黑名单"""
    redis = get_redis()
    # Token 过期时间
    redis.set(f"blacklist:{token}", "1", ttl=86400)

def is_token_blacklisted(token: str) -> bool:
    """检查 Token 是否在黑名单"""
    redis = get_redis()
    return redis.exists(f"blacklist:{token}") > 0
```

### 2. 短信验证码

```python
def send_sms_code(phone: str):
    """发送短信验证码"""
    redis = get_redis()
    
    # 检查发送频率（60秒内只能发一次）
    if redis.exists(f"sms:rate:{phone}"):
        raise Exception("发送过于频繁")
    
    # 生成验证码
    code = generate_code()
    
    # 保存验证码（5分钟有效）
    redis.set(f"sms:code:{phone}", code, ttl=300)
    
    # 设置发送频率限制
    redis.set(f"sms:rate:{phone}", "1", ttl=60)
    
    # 发送短信
    send_sms(phone, code)

def verify_sms_code(phone: str, code: str) -> bool:
    """验证短信验证码"""
    redis = get_redis()
    saved_code = redis.get(f"sms:code:{phone}")
    
    if saved_code == code:
        # 验证成功后删除
        redis.delete(f"sms:code:{phone}")
        return True
    
    return False
```

### 3. 分布式锁

```python
def acquire_lock(lock_key: str, timeout: int = 10) -> bool:
    """获取分布式锁"""
    redis = get_redis()
    return redis.set(f"lock:{lock_key}", "1", ttl=timeout, nx=True)

def release_lock(lock_key: str):
    """释放分布式锁"""
    redis = get_redis()
    redis.delete(f"lock:{lock_key}")

# 使用示例
if acquire_lock("payment_123"):
    try:
        # 执行业务逻辑
        process_payment()
    finally:
        release_lock("payment_123")
```

---

## 📚 参考资料

- 📘 [Redis 官方文档](https://redis.io/documentation)
- 📗 [Redis 命令参考](https://redis.io/commands)
- 📕 [redis-py 文档](https://redis-py.readthedocs.io/)

---

**现在开始使用 Redis 加速你的应用吧！** 🚀

```bash
# 启动应用
npm run dev
```
