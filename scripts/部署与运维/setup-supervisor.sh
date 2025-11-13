#!/bin/bash
# 安装和配置Supervisor进程管理器

echo "=========================================="
echo "安装和配置Supervisor"
echo "=========================================="

# 1. 安装Supervisor
echo ""
echo "1. 安装Supervisor..."
if command -v supervisord &> /dev/null; then
    echo "✓ Supervisor已安装"
else
    apt-get update
    apt-get install -y supervisor
    echo "✓ Supervisor安装完成"
fi

# 2. 复制配置文件
echo ""
echo "2. 配置Supervisor..."
cp supervisor-config.ini /etc/supervisor/conf.d/timao.conf
echo "✓ 配置文件已复制"

# 3. 重新加载配置
echo ""
echo "3. 重新加载Supervisor配置..."
supervisorctl reread
supervisorctl update

# 4. 启动服务
echo ""
echo "4. 启动所有服务..."
supervisorctl start timao-services:*

# 5. 检查状态
echo ""
echo "5. 服务状态检查..."
supervisorctl status timao-services:*

echo ""
echo "=========================================="
echo "Supervisor配置完成"
echo "=========================================="
echo ""
echo "常用命令："
echo "  查看状态:    supervisorctl status"
echo "  启动所有:    supervisorctl start timao-services:*"
echo "  停止所有:    supervisorctl stop timao-services:*"
echo "  重启所有:    supervisorctl restart timao-services:*"
echo "  查看日志:    supervisorctl tail -f timao-main"
echo ""
echo "Web界面（可选）："
echo "  访问: http://YOUR_IP:9001"
echo "  需要在/etc/supervisor/supervisord.conf中配置[inet_http_server]"

