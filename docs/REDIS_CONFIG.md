# Redis配置和环境变量

本文档说明Redis相关的环境变量配置。

## 环境变量配置

在 `.env` 文件中添加或修改以下配置：

### Redis基础配置

```env
# Redis启用开关
REDIS_ENABLED=true

# Redis服务器地址
REDIS_HOST=localhost

# Redis端口
REDIS_PORT=6379

# Redis密码（如果设置了）
REDIS_PASSWORD=

# Redis数据库编号
REDIS_DB=0

# Redis连接池大小
REDIS_MAX_CONNECTIONS=50

# Redis默认缓存过期时间（秒）
REDIS_CACHE_TTL=3600
```

### 批量入库配置

```env
# Redis批量写入开关（转写和弹幕）
REDIS_BATCH_ENABLED=1

# 音频转写批量大小（条）
REDIS_BATCH_SIZE=100

# 音频转写批量间隔（秒）
REDIS_BATCH_INTERVAL=10.0

# 弹幕批量大小（条）
DANMU_BATCH_SIZE=500

# 弹幕批量间隔（秒）
DANMU_BATCH_INTERVAL=5.0
```

### AI分析缓存配置

```env
# AI分析结果缓存开关
AI_CACHE_ENABLED=1

# AI分析结果缓存时间（秒）
AI_CACHE_TTL=3600
```

### 性能监控配置

```env
# 性能监控开关
MONITOR_ENABLED=1

# 性能监控间隔（秒）
MONITOR_INTERVAL=30.0

# MySQL连接数告警阈值
MYSQL_CONN_WARNING=45

# Redis内存告警阈值（MB）
REDIS_MEMORY_WARNING_MB=1800

# 进程内存告警阈值（MB）
PROCESS_MEMORY_WARNING_MB=4000
```

## Redis键设计

### 1. 音频转写数据

```
格式: transcription:{session_id}:stream
类型: List
过期: 24小时
示例: transcription:live_douyin_anchor_20250114_1234567890:stream
```

### 2. 弹幕数据

```
格式: danmu:{live_id}:queue
类型: List
过期: 24小时
示例: danmu:123456789:queue
```

### 3. 礼物数据

```
格式: gift:{live_id}:queue
类型: List
过期: 24小时
示例: gift:123456789:queue
```

### 4. 点赞计数

```
格式: like:{live_id}:count
类型: String (计数器)
过期: 24小时
示例: like:123456789:count
```

### 5. 热词统计

```
格式: hotwords:{live_id}:sorted_set
类型: Sorted Set
过期: 24小时
示例: hotwords:123456789:sorted_set
```

### 6. 会话状态

```
格式: session:{session_id}:state
类型: Hash
过期: 48小时
示例: session:live_douyin_anchor_20250114_1234567890:state
```

### 7. 活跃会话集合

```
格式: active_sessions
类型: Set
无过期
```

### 8. AI分析结果

```
格式: ai_analysis:{session_id}:{content_hash}
类型: String (JSON)
过期: 1小时
示例: ai_analysis:default:abc123def456
```

### 9. 性能监控指标

```
格式: system:performance:latest
类型: String (JSON)
过期: 2分钟
```

## 部署步骤

### 1. 安装Redis

运行部署脚本（自动安装和配置）：

```bash
cd /www/wwwroot/timao-douyin-live-manager
chmod +x scripts/deploy_redis.sh
sudo ./scripts/deploy_redis.sh
```

### 2. 验证Redis运行

```bash
# 测试连接
redis-cli ping
# 应该返回: PONG

# 查看内存使用
redis-cli info memory

# 查看键数量
redis-cli dbsize
```

### 3. 配置环境变量

编辑 `.env` 文件，确保Redis配置正确：

```bash
vim /www/wwwroot/timao-douyin-live-manager/server/.env
```

### 4. 重启后端服务

```bash
# 方法1：通过systemd（如果配置了）
sudo systemctl restart timao-live-manager

# 方法2：手动重启
# 停止现有进程
ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}' | xargs kill

# 启动新进程
cd /www/wwwroot/timao-douyin-live-manager/server
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/server.log 2>&1 &
```

## 监控和维护

### 查看Redis状态

```bash
# 连接Redis CLI
redis-cli

# 查看所有键
KEYS *

# 查看指定模式的键
KEYS transcription:*
KEYS danmu:*

# 查看键的过期时间
TTL <key_name>

# 查看内存使用
INFO memory

# 查看连接数
INFO clients

# 查看统计信息
INFO stats
```

### 清理Redis数据

```bash
# 清理所有键（危险操作，仅在测试环境使用）
redis-cli FLUSHDB

# 清理特定模式的键
redis-cli --scan --pattern "transcription:*" | xargs redis-cli DEL
redis-cli --scan --pattern "danmu:*" | xargs redis-cli DEL
```

### 性能优化建议

1. **内存监控**
   - 定期检查 `INFO memory` 输出
   - 确保 `used_memory` 不超过 `maxmemory` 设置

2. **慢查询日志**
   ```bash
   # 查看慢查询
   redis-cli SLOWLOG GET 10
   ```

3. **持久化策略**
   - 当前配置：关闭持久化（优先性能）
   - 如需持久化，修改 `/etc/redis/redis.conf`

4. **连接池优化**
   - 根据并发量调整 `REDIS_MAX_CONNECTIONS`
   - 监控连接池使用率

## 故障排查

### Redis无法启动

```bash
# 查看日志
sudo tail -f /var/log/redis/redis-server.log

# 检查配置文件
redis-server /etc/redis/redis.conf --test-memory 2048

# 检查端口占用
sudo netstat -tulpn | grep 6379
```

### 连接被拒绝

```bash
# 检查Redis状态
sudo systemctl status redis-server

# 检查bind配置
grep "^bind" /etc/redis/redis.conf

# 检查防火墙
sudo firewall-cmd --list-ports  # CentOS
sudo ufw status  # Ubuntu
```

### 内存不足

```bash
# 增加maxmemory限制
redis-cli CONFIG SET maxmemory 2gb

# 永久修改
sudo vim /etc/redis/redis.conf
# 修改 maxmemory 行
sudo systemctl restart redis-server
```

## 安全建议

1. **设置密码**（生产环境必须）
   ```bash
   # 编辑配置文件
   sudo vim /etc/redis/redis.conf
   # 取消注释并设置密码
   requirepass your_strong_password_here
   
   # 重启Redis
   sudo systemctl restart redis-server
   
   # 更新.env文件
   REDIS_PASSWORD=your_strong_password_here
   ```

2. **限制网络访问**
   ```bash
   # 仅允许本地访问（默认）
   bind 127.0.0.1
   
   # 如需远程访问，使用防火墙限制IP
   sudo ufw allow from 192.168.1.0/24 to any port 6379
   ```

3. **禁用危险命令**
   ```bash
   # 编辑配置文件
   sudo vim /etc/redis/redis.conf
   # 添加以下行
   rename-command FLUSHDB ""
   rename-command FLUSHALL ""
   rename-command CONFIG ""
   ```

## 预期效果

实施Redis优化后，预期达到以下效果：

- ✅ MySQL写入量减少 **70%**
- ✅ 内存使用降低 **50%**
- ✅ 死锁和重启问题基本消除
- ✅ 支持 **100+场直播** 同时运行
- ✅ 转写延迟降低至 **<2秒**
- ✅ 弹幕处理延迟 **<1秒**

## 性能基准测试

参考 `scripts/stress_test.py` 进行性能测试。

