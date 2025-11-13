#!/bin/bash
# 诊断502错误

echo "🔍 诊断502错误..."
echo ""

# 1. 检查服务是否还在运行
echo "1️⃣ 检查服务进程..."
ps aux | grep uvicorn | grep -v grep
if [ $? -eq 0 ]; then
    echo "   ✅ 服务进程存在"
else
    echo "   ❌ 服务进程不存在！服务可能已崩溃"
fi

# 2. 检查端口监听
echo ""
echo "2️⃣ 检查端口10050监听状态..."
netstat -tlnp | grep 10050 || ss -tlnp | grep 10050
if [ $? -eq 0 ]; then
    echo "   ✅ 端口正在监听"
else
    echo "   ❌ 端口未监听！"
fi

# 3. 检查是否有Nginx或其他反向代理
echo ""
echo "3️⃣ 检查是否有Nginx..."
if command -v nginx &> /dev/null; then
    echo "   ⚠️  检测到Nginx，可能是反向代理配置问题"
    echo "   检查Nginx配置..."
    sudo nginx -t 2>&1 | head -10
    echo ""
    echo "   检查Nginx是否运行..."
    systemctl status nginx 2>&1 | head -5
else
    echo "   ✅ 未检测到Nginx"
fi

# 4. 检查是否有其他Web服务器
echo ""
echo "4️⃣ 检查其他Web服务器..."
if systemctl is-active --quiet apache2 2>/dev/null; then
    echo "   ⚠️  Apache2正在运行"
fi
if systemctl is-active --quiet httpd 2>/dev/null; then
    echo "   ⚠️  Httpd正在运行"
fi

# 5. 本地测试服务
echo ""
echo "5️⃣ 本地测试服务..."
if curl -f -s http://127.0.0.1:10050/health > /dev/null 2>&1; then
    echo "   ✅ 本地访问正常"
    curl -s http://127.0.0.1:10050/health | head -3
else
    echo "   ❌ 本地访问失败！服务可能已停止"
fi

# 6. 检查防火墙
echo ""
echo "6️⃣ 检查防火墙..."
if command -v ufw &> /dev/null; then
    sudo ufw status | grep 10050 || echo "   ⚠️  端口10050未在ufw规则中"
fi

echo ""
echo "📋 诊断完成"
echo ""
echo "💡 如果服务进程不存在，请重新启动："
echo "   cd /www/wwwroot/wwwroot/timao-douyin-live-manager/server"
echo "   source ../.venv/bin/activate"
echo "   export BACKEND_PORT=10050"
echo "   python -m uvicorn app.main:app --host 0.0.0.0 --port 10050"

