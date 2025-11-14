#!/bin/bash
# 重启所有后端服务

echo "=========================================="
echo "重启所有后端服务 - $(date)"
echo "=========================================="

cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 1. 停止所有Python服务
echo ""
echo "1. 停止现有Python服务..."
pkill -f "python.*uvicorn.*server.app.main" || echo "无FastAPI主服务进程"
pkill -f "python.*server/streamcap_service.py" || echo "无StreamCap服务进程"
pkill -f "python.*server/douyin_service.py" || echo "无Douyin服务进程"
sleep 3

# 2. 检查是否还有残留进程
echo ""
echo "2. 检查残留进程..."
ps aux | grep python | grep -v grep | grep server

# 3. 激活虚拟环境
echo ""
echo "3. 激活虚拟环境..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ 虚拟环境已激活"
else
    echo "❌ 虚拟环境不存在"
    exit 1
fi

# 4. 启动FastAPI主服务
echo ""
echo "4. 启动FastAPI主服务 (端口11111)..."
nohup python -m uvicorn server.app.main:app --host 0.0.0.0 --port 11111 > logs/main.log 2>&1 &
sleep 2
if netstat -tulnp | grep :11111 > /dev/null; then
    echo "✓ FastAPI主服务启动成功"
else
    echo "❌ FastAPI主服务启动失败"
fi

# 5. 启动StreamCap服务
echo ""
echo "5. 启动StreamCap服务 (端口8001)..."
nohup python -m uvicorn server.streamcap_service:app --host 0.0.0.0 --port 8001 > logs/streamcap.log 2>&1 &
sleep 2
if netstat -tulnp | grep :8001 > /dev/null; then
    echo "✓ StreamCap服务启动成功"
else
    echo "❌ StreamCap服务启动失败"
fi

# 6. 启动Douyin服务
echo ""
echo "6. 启动Douyin服务 (端口8002)..."
nohup python -m uvicorn server.douyin_service:app --host 0.0.0.0 --port 8002 > logs/douyin.log 2>&1 &
sleep 2
if netstat -tulnp | grep :8002 > /dev/null; then
    echo "✓ Douyin服务启动成功"
else
    echo "❌ Douyin服务启动失败"
fi

# 7. 重启Nginx
echo ""
echo "7. 重启Nginx..."
systemctl restart nginx
if systemctl is-active --quiet nginx; then
    echo "✓ Nginx重启成功"
else
    echo "❌ Nginx重启失败"
fi

# 8. 最终检查
echo ""
echo "8. 最终状态检查..."
echo "端口监听状态："
netstat -tulnp | grep -E ":(8000|8001|8002|80|443)" | grep LISTEN

echo ""
echo "Python进程："
ps aux | grep python | grep server | grep -v grep

echo ""
echo "=========================================="
echo "服务重启完成"
echo "=========================================="
echo ""
echo "请等待30秒后测试前端连接"
echo "如果仍然失败，请检查日志："
echo "  - logs/main.log"
echo "  - logs/streamcap.log"
echo "  - logs/douyin.log"
echo "  - /var/log/nginx/error.log"

