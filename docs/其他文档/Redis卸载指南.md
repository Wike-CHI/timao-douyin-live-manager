# Redis 卸载指南

## 当前Redis状态
- 版本：redis-7.2.7-5.tl4.x86_64
- 状态：运行中
- 开机自启：已禁用

## 完整卸载步骤

### 1. 停止Redis服务
```bash
# 停止Redis服务
sudo systemctl stop redis

# 确认已停止
sudo systemctl status redis
```

### 2. 禁用开机自启（已禁用可跳过）
```bash
# 禁用开机自启
sudo systemctl disable redis
```

### 3. 卸载Redis软件包
```bash
# 使用yum卸载（推荐，会保留配置）
sudo yum remove redis

# 或者完全卸载（包括配置文件）
sudo yum remove redis -y
sudo yum autoremove -y
```

### 4. 清理Redis数据和配置（可选）
```bash
# 删除Redis数据目录
sudo rm -rf /var/lib/redis

# 删除Redis配置文件
sudo rm -f /etc/redis.conf
sudo rm -f /etc/redis-sentinel.conf

# 删除Redis日志文件
sudo rm -rf /var/log/redis

# 删除systemd服务文件
sudo rm -f /etc/systemd/system/redis.service.d/*
sudo rm -f /usr/lib/systemd/system/redis.service

# 重新加载systemd
sudo systemctl daemon-reload
```

### 5. 验证卸载
```bash
# 检查Redis服务
systemctl status redis

# 检查Redis进程
ps aux | grep redis

# 检查Redis软件包
rpm -qa | grep redis

# 检查Redis命令
which redis-server
which redis-cli
```

## 卸载前备份（推荐）

### 备份Redis数据
```bash
# 备份RDB文件
sudo cp /var/lib/redis/dump.rdb ~/redis_backup_$(date +%Y%m%d).rdb

# 备份配置文件
sudo cp /etc/redis.conf ~/redis.conf.backup
```

### 导出数据
```bash
# 使用redis-cli导出所有数据
redis-cli --rdb /tmp/redis_backup.rdb

# 或使用bgsave命令
redis-cli BGSAVE
```

## 项目影响评估

### 检查项目是否使用Redis
```bash
# 检查Python代码中的Redis引用
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
grep -r "redis" server/ --include="*.py"

# 检查配置文件
grep -r "REDIS" . --include="*.json" --include="*.env"

# 检查requirements.txt
grep redis server/requirements.txt
```

### 项目Redis使用情况
根据 `server/config.py`，Redis在本项目中的使用：
- 缓存服务（可选）
- 如果Redis不可用，系统会自动降级到内存缓存

### 卸载影响
- ✅ **项目仍可正常运行**：系统已实现Redis降级机制
- ⚠️ **性能可能下降**：内存缓存在多进程环境下无法共享
- ⚠️ **重启后数据丢失**：内存缓存不持久化

## 替代方案

### 方案1：保留但停止服务
如果不确定是否需要Redis，可以只停止服务：
```bash
sudo systemctl stop redis
sudo systemctl disable redis
```

### 方案2：使用Docker Redis
如果未来可能需要Redis，可以使用Docker：
```bash
# 卸载系统Redis后，使用Docker
docker run -d -p 6379:6379 --name redis redis:7.2-alpine
```

### 方案3：完全移除Redis依赖
修改项目配置，禁用Redis：
```bash
# 编辑 .env 文件
REDIS_ENABLED=false

# 或在 config.py 中设置
redis:
  enabled: false
```

## 安全建议

### 卸载前
1. **确认没有其他服务依赖Redis**
2. **备份重要数据**
3. **通知团队成员**

### 卸载后
1. **测试项目功能**
2. **监控错误日志**
3. **更新部署文档**

## 快速卸载命令（谨慎使用）
```bash
# 一键卸载（会丢失所有数据）
sudo systemctl stop redis && \
sudo systemctl disable redis && \
sudo yum remove redis -y && \
sudo rm -rf /var/lib/redis /etc/redis.conf /var/log/redis
```

## 恢复Redis
如果卸载后需要恢复：
```bash
# 重新安装
sudo yum install redis -y

# 恢复配置
sudo cp ~/redis.conf.backup /etc/redis.conf

# 恢复数据
sudo cp ~/redis_backup_*.rdb /var/lib/redis/dump.rdb

# 启动服务
sudo systemctl start redis
sudo systemctl enable redis
```

