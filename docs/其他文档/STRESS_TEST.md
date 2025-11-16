# 压力测试指南

本文档说明如何进行压力测试，验证Redis优化效果。

## 测试目标

验证以下优化效果：

1. ✅ MySQL写入量减少 70%
2. ✅ 内存使用降低 50%
3. ✅ 死锁和重启问题基本消除
4. ✅ 支持 100+场直播同时运行
5. ✅ 转写延迟 <2秒
6. ✅ 弹幕处理延迟 <1秒

## 准备工作

### 1. 安装依赖

```bash
cd /www/wwwroot/timao-douyin-live-manager
pip install aiohttp psutil
```

### 2. 确保服务运行

```bash
# 检查后端服务
curl http://localhost:8000/health

# 检查Redis
redis-cli ping

# 检查MySQL连接
mysql -h rm-bp1sqxf05yom2hwdhko.mysql.rds.aliyuncs.com -u timao -p
```

## 运行压力测试

### 基础测试（10场直播，60秒）

```bash
cd /www/wwwroot/timao-douyin-live-manager
python scripts/stress_test.py
```

### 中等压力测试（50场直播，120秒）

```bash
python scripts/stress_test.py --streams 50 --duration 120
```

### 高压力测试（100场直播，180秒）

```bash
python scripts/stress_test.py --streams 100 --duration 180
```

### 自定义测试

```bash
python scripts/stress_test.py --streams <直播数> --duration <时长秒> --url <API地址>
```

## 测试参数

- `--streams`: 模拟直播数量（默认10）
- `--duration`: 测试时长（秒，默认60）
- `--url`: API地址（默认 http://localhost:8000）

## 测试场景

每场模拟直播会产生：

- **转写数据**: 2条/秒 × 时长
- **弹幕数据**: 10条/秒 × 时长

例如，10场直播运行60秒会产生：

- 转写：10 × 2 × 60 = **1,200条**
- 弹幕：10 × 10 × 60 = **6,000条**
- 总请求：**7,200次**

## 监控指标

### 实时监控（测试期间）

在另一个终端窗口运行：

```bash
# 监控Redis内存
watch -n 1 'redis-cli info memory | grep used_memory_human'

# 监控MySQL连接数
watch -n 1 'mysql -h <host> -u <user> -p<password> -e "SHOW STATUS LIKE \"Threads_connected\""'

# 监控进程内存
watch -n 1 'ps aux | grep "python.*main.py" | grep -v grep'

# 监控系统资源
htop
```

### 查看Redis数据

```bash
# 连接Redis
redis-cli

# 查看所有键
KEYS *

# 查看转写队列长度
LLEN transcription:*

# 查看弹幕队列长度
LLEN danmu:*

# 查看热词统计
ZRANGE hotwords:*:sorted_set 0 -1 WITHSCORES

# 查看内存使用
INFO memory
```

### 查看日志

```bash
# 后端日志
tail -f /www/wwwroot/timao-douyin-live-manager/server/logs/server.log

# Redis日志
sudo tail -f /var/log/redis/redis-server.log

# MySQL慢查询日志
sudo tail -f /var/log/mysql/slow-query.log
```

## 结果评估

### 成功标准

测试通过需满足：

1. **成功率** ≥ 95%
2. **QPS** ≥ 100
3. **MySQL连接数** < 45
4. **Redis内存** < 1.5GB
5. **进程内存** < 4GB
6. **无死锁或重启**

### 性能指标对比

#### 优化前（预期）

- MySQL连接数：60+ / 30（池满，溢出）
- 进程内存：6-8GB
- 转写延迟：5-10秒
- 弹幕延迟：3-5秒
- 支持直播数：20-30场
- 频繁死锁和重启

#### 优化后（目标）

- MySQL连接数：20-30 / 70（池充足）
- 进程内存：2-3GB
- 转写延迟：<2秒
- 弹幕延迟：<1秒
- 支持直播数：100+场
- 无死锁和重启

## 故障排查

### 1. 测试脚本无法连接

```bash
# 检查后端服务
curl http://localhost:8000/health

# 检查端口
sudo netstat -tulpn | grep 8000

# 检查防火墙
sudo ufw status
```

### 2. Redis内存不足

```bash
# 查看当前内存使用
redis-cli info memory

# 增加内存限制（临时）
redis-cli CONFIG SET maxmemory 3gb

# 清理旧数据
redis-cli --scan --pattern "*" | xargs redis-cli DEL
```

### 3. MySQL连接池耗尽

```bash
# 查看当前连接数
mysql -h <host> -u <user> -p<password> -e "SHOW STATUS LIKE 'Threads_connected'"

# 杀死空闲连接
mysql -h <host> -u <user> -p<password> -e "SHOW PROCESSLIST" | grep Sleep | awk '{print $1}' | xargs -I {} mysql -h <host> -u <user> -p<password> -e "KILL {}"
```

### 4. 进程内存过高

```bash
# 查看内存占用
ps aux | grep "python.*main.py"

# 查看Python对象统计
# 在Python代码中添加：
import gc
import sys
print(sys.getsizeof(gc.get_objects()))

# 重启服务释放内存
sudo systemctl restart timao-live-manager
```

## 优化建议

根据测试结果调整配置：

### 1. 调整批量大小

如果延迟过高，减小批量间隔：

```env
# .env
REDIS_BATCH_INTERVAL=5.0  # 改为 3.0
DANMU_BATCH_INTERVAL=3.0   # 改为 2.0
```

### 2. 调整内存限制

如果Redis内存不足，增加限制：

```bash
# /etc/redis/redis.conf
maxmemory 3gb  # 改为更大的值
```

### 3. 调整连接池

如果MySQL连接不足，增加池大小：

```python
# server/config.py
pool_size: int = 50  # 改为 70
max_overflow: int = 20  # 改为 30
```

### 4. 启用持久化（可选）

如果需要数据持久化：

```bash
# /etc/redis/redis.conf
save 900 1
save 300 10
save 60 10000
```

## 持续监控

部署后，建议设置持续监控：

### 1. Prometheus + Grafana

```bash
# 安装监控栈（示例）
docker run -d -p 9090:9090 prom/prometheus
docker run -d -p 3000:3000 grafana/grafana
```

### 2. 告警规则

配置告警规则（Prometheus）：

```yaml
groups:
  - name: timao_live
    rules:
      - alert: MySQLConnectionHigh
        expr: mysql_connections > 45
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "MySQL连接数过高"
      
      - alert: RedisMemoryHigh
        expr: redis_memory_used_bytes > 1.8e9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis内存使用过高"
      
      - alert: ProcessMemoryHigh
        expr: process_memory_bytes > 4e9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "进程内存使用过高"
```

### 3. 日志分析

使用 ELK Stack 或 Loki 进行日志聚合和分析。

## 总结

完成压力测试后：

1. ✅ 记录测试结果和性能指标
2. ✅ 对比优化前后的差异
3. ✅ 根据结果调整配置
4. ✅ 部署到生产环境
5. ✅ 持续监控和优化

如有问题，请参考：

- Redis配置：`docs/REDIS_CONFIG.md`
- 优化方案：`redis.plan.md`
- 性能监控：`server/utils/performance_monitor.py`

