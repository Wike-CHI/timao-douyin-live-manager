#!/bin/bash
# Redis部署和优化配置脚本

set -e

echo "==============================================="
echo "  Redis部署和优化配置"
echo "==============================================="

# 检测操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "❌ 无法检测操作系统"
    exit 1
fi

echo "检测到操作系统: $OS"

# 安装Redis
echo ""
echo "步骤 1: 安装Redis服务..."
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    sudo apt-get update
    sudo apt-get install -y redis-server redis-tools
    REDIS_CONF="/etc/redis/redis.conf"
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
    sudo yum install -y redis
    REDIS_CONF="/etc/redis.conf"
else
    echo "❌ 不支持的操作系统: $OS"
    exit 1
fi

echo "✅ Redis安装完成"

# 备份原配置文件
echo ""
echo "步骤 2: 备份原配置文件..."
if [ -f "$REDIS_CONF" ]; then
    sudo cp "$REDIS_CONF" "${REDIS_CONF}.backup.$(date +%Y%m%d%H%M%S)"
    echo "✅ 配置文件已备份"
else
    echo "⚠️  配置文件不存在，将创建新配置"
fi

# 优化Redis配置
echo ""
echo "步骤 3: 优化Redis配置..."

# 读取服务器内存大小（GB）
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
echo "检测到服务器内存: ${TOTAL_MEM}GB"

# 计算Redis内存限制（总内存的20%，最少2GB）
if [ $TOTAL_MEM -gt 10 ]; then
    REDIS_MEM="2gb"
else
    REDIS_MEM="1gb"
fi

echo "设置Redis内存限制: $REDIS_MEM"

# 写入优化配置
sudo tee "$REDIS_CONF" > /dev/null <<EOF
# Redis配置 - 优化用于直播数据缓存
# 生成时间: $(date)

# 网络配置
bind 127.0.0.1
port 6379
tcp-backlog 511
timeout 300
tcp-keepalive 60

# 通用配置
daemonize yes
supervised systemd
pidfile /var/run/redis/redis-server.pid
loglevel notice
logfile /var/log/redis/redis-server.log

# 内存管理
maxmemory $REDIS_MEM
maxmemory-policy allkeys-lru
maxclients 10000

# 持久化配置（优先性能，关闭持久化）
# 直播数据主要用于临时缓存，不需要持久化
save ""
stop-writes-on-bgsave-error no
rdbcompression no
rdbchecksum no
dbfilename dump.rdb
dir /var/lib/redis

# AOF持久化（关闭）
appendonly no

# 性能优化
slowlog-log-slower-than 10000
slowlog-max-len 128
latency-monitor-threshold 100

# 安全配置（如果需要密码，请取消下行注释并设置密码）
# requirepass your_redis_password_here

# 危险命令重命名（可选）
# rename-command FLUSHDB ""
# rename-command FLUSHALL ""
# rename-command CONFIG ""
EOF

echo "✅ Redis配置已优化"

# 创建必要的目录
echo ""
echo "步骤 4: 创建必要的目录..."
sudo mkdir -p /var/lib/redis /var/log/redis /var/run/redis
sudo chown -R redis:redis /var/lib/redis /var/log/redis /var/run/redis
echo "✅ 目录创建完成"

# 启动并启用Redis服务
echo ""
echo "步骤 5: 启动Redis服务..."
sudo systemctl enable redis-server 2>/dev/null || sudo systemctl enable redis
sudo systemctl restart redis-server 2>/dev/null || sudo systemctl restart redis
echo "✅ Redis服务已启动"

# 检查Redis状态
echo ""
echo "步骤 6: 检查Redis运行状态..."
sleep 2
if redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo "✅ Redis运行正常"
else
    echo "❌ Redis未正常运行"
    sudo systemctl status redis-server 2>/dev/null || sudo systemctl status redis
    exit 1
fi

# 显示Redis配置信息
echo ""
echo "==============================================="
echo "  Redis部署完成！"
echo "==============================================="
echo ""
echo "📊 配置信息："
echo "  - 内存限制: $REDIS_MEM"
echo "  - 最大连接数: 10000"
echo "  - 持久化: 关闭（优先性能）"
echo "  - 淘汰策略: allkeys-lru"
echo ""
echo "🔧 管理命令："
echo "  - 查看状态: sudo systemctl status redis-server"
echo "  - 重启服务: sudo systemctl restart redis-server"
echo "  - 查看日志: sudo tail -f /var/log/redis/redis-server.log"
echo "  - 连接测试: redis-cli ping"
echo ""
echo "⚠️  注意事项："
echo "  1. 如需设置密码，请编辑 $REDIS_CONF 中的 requirepass 配置"
echo "  2. 如需外部访问，请修改 bind 配置并配置防火墙"
echo "  3. 配置文件备份位置: ${REDIS_CONF}.backup.*"
echo ""
echo "==============================================="

