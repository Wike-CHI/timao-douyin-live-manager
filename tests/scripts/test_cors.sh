#!/bin/bash
# CORS配置测试脚本
# 审查人: 叶维哲
# 创建日期: 2025-11-09

echo "======================================================"
echo "🌐 CORS配置测试"
echo "======================================================"
echo ""

# 测试1: 后端直连
echo "1️⃣  测试后端直连 (127.0.0.1:8000)"
echo "------------------------------------------------------"
response1=$(curl -I http://127.0.0.1:8000/api/cors-test 2>&1 | grep -E "HTTP|access-control")
echo "$response1"
if echo "$response1" | grep -q "access-control-allow-origin: \*"; then
    echo "✅ 后端CORS配置正确"
else
    echo "❌ 后端CORS配置错误"
fi
echo ""

# 测试2: Nginx代理
echo "2️⃣  测试Nginx代理 (129.211.218.135:80)"
echo "------------------------------------------------------"
response2=$(curl -I http://129.211.218.135/api/cors-test 2>&1 | grep -E "HTTP|access-control")
echo "$response2"
if echo "$response2" | grep -q "access-control-allow-origin: \*"; then
    echo "✅ Nginx代理CORS配置正确"
else
    echo "❌ Nginx代理CORS配置错误"
fi
echo ""

# 测试3: OPTIONS预检请求
echo "3️⃣  测试OPTIONS预检请求"
echo "------------------------------------------------------"
response3=$(curl -X OPTIONS -I http://129.211.218.135/api/live_audio/start \
  -H "Origin: http://127.0.0.1:10050" \
  -H "Access-Control-Request-Method: POST" 2>&1 | grep -E "HTTP|access-control")
echo "$response3"
if echo "$response3" | grep -q "access-control-allow-origin: \*"; then
    echo "✅ OPTIONS预检请求正确"
else
    echo "❌ OPTIONS预检请求错误"
fi
echo ""

# 测试4: 健康检查
echo "4️⃣  测试健康检查端点"
echo "------------------------------------------------------"
health=$(curl -s http://129.211.218.135/health 2>&1)
if echo "$health" | grep -q "status"; then
    echo "✅ 健康检查端点正常"
    echo "$health" | head -5
else
    echo "❌ 健康检查端点异常"
fi
echo ""

# 总结
echo "======================================================"
echo "📊 测试总结"
echo "======================================================"
if echo "$response1" | grep -q "access-control-allow-origin: \*" && \
   echo "$response2" | grep -q "access-control-allow-origin: \*" && \
   echo "$response3" | grep -q "access-control-allow-origin: \*"; then
    echo "✅ 所有CORS测试通过！"
    echo ""
    echo "🎉 前端现在可以正常访问后端API了"
    echo ""
    echo "前端访问地址: http://127.0.0.1:10050"
    echo "后端API地址:   http://129.211.218.135/api/..."
else
    echo "❌ 部分测试失败，请检查配置"
    echo ""
    echo "排查步骤:"
    echo "1. 检查后端是否运行: ps aux | grep uvicorn"
    echo "2. 检查后端监听地址: lsof -i :8000"
    echo "3. 检查nginx配置: cat /www/server/panel/vhost/nginx/129.211.218.135.conf"
    echo "4. 重新加载nginx: nginx -s reload"
fi
echo "======================================================"

