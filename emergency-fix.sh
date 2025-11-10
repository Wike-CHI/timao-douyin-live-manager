#!/bin/bash
# 紧急诊断脚本 - 检查所有后端服务状态

echo "=========================================="
echo "后端服务诊断 - $(date)"
echo "=========================================="

# 1. 检查后端服务进程
echo ""
echo "1. 检查Python进程..."
ps aux | grep python | grep -v grep

# 2. 检查端口占用
echo ""
echo "2. 检查端口占用..."
echo "FastAPI主服务 (8000):"
netstat -tulnp | grep :8000 || echo "❌ 端口8000未被占用"

echo "StreamCap服务 (8001):"
netstat -tulnp | grep :8001 || echo "❌ 端口8001未被占用"

echo "Douyin服务 (8002):"
netstat -tulnp | grep :8002 || echo "❌ 端口8002未被占用"

# 3. 检查Nginx配置
echo ""
echo "3. 检查Nginx状态..."
systemctl status nginx | head -n 10

# 4. 检查Nginx配置文件
echo ""
echo "4. 检查Nginx配置..."
nginx -t

# 5. 查看最近的错误日志
echo ""
echo "5. 最近的错误日志..."
if [ -f "/www/wwwroot/wwwroot/timao-douyin-live-manager/logs/error.log" ]; then
    echo "应用错误日志（最后20行）："
    tail -n 20 /www/wwwroot/wwwroot/timao-douyin-live-manager/logs/error.log
fi

echo ""
echo "Nginx错误日志（最后20行）："
tail -n 20 /var/log/nginx/error.log 2>/dev/null || echo "无法访问Nginx错误日志"

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="

