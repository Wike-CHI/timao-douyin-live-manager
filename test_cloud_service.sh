#!/bin/bash
# timao-cloud 服务测试脚本
# 快速验证云端服务是否正常运行

echo "=========================================="
echo "🧪 测试timao-cloud云端服务"
echo "=========================================="
echo ""

# 检查PM2进程状态
echo "1️⃣  检查PM2进程..."
if pm2 list | grep -q "timao-cloud"; then
    if pm2 list | grep "timao-cloud" | grep -q "online"; then
        echo "   ✅ PM2进程运行中"
        pm2 status timao-cloud --no-daemon 2>/dev/null | grep "timao-cloud" || pm2 status timao-cloud
    else
        echo "   ❌ PM2进程未运行"
        exit 1
    fi
else
    echo "   ❌ 未找到timao-cloud进程"
    echo "   提示: 运行 ./start_cloud.sh 启动服务"
    exit 1
fi

echo ""

# 测试端口是否监听
echo "2️⃣  检查端口监听..."
if netstat -tlnp 2>/dev/null | grep -q ":15000"; then
    echo "   ✅ 端口15000正在监听"
else
    if ss -tlnp 2>/dev/null | grep -q ":15000"; then
        echo "   ✅ 端口15000正在监听"
    else
        echo "   ❌ 端口15000未监听"
        exit 1
    fi
fi

echo ""

# 测试健康检查
echo "3️⃣  测试健康检查 (GET /health)..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:15000/health 2>&1)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ 健康检查通过 (HTTP $HTTP_CODE)"
    echo "   响应: $BODY" | python3 -m json.tool 2>/dev/null || echo "   响应: $BODY"
else
    echo "   ❌ 健康检查失败 (HTTP $HTTP_CODE)"
    echo "   响应: $BODY"
    exit 1
fi

echo ""

# 测试控制台页面
echo "4️⃣  测试控制台页面 (GET /)..."
CONSOLE_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:15000/)
if [ "$CONSOLE_CODE" = "200" ]; then
    echo "   ✅ 控制台可访问 (HTTP $CONSOLE_CODE)"
else
    echo "   ⚠️  控制台返回 HTTP $CONSOLE_CODE"
fi

echo ""

# 测试静态文件
echo "5️⃣  测试静态文件 (GET /static/assets/icon.png)..."
STATIC_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:15000/static/assets/icon.png)
if [ "$STATIC_CODE" = "200" ]; then
    echo "   ✅ 静态文件可访问 (HTTP $STATIC_CODE)"
else
    echo "   ⚠️  静态文件返回 HTTP $STATIC_CODE"
fi

echo ""

# 测试API文档
echo "6️⃣  测试API文档 (GET /docs)..."
DOCS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:15000/docs)
if [ "$DOCS_CODE" = "200" ]; then
    echo "   ✅ API文档可访问 (HTTP $DOCS_CODE)"
else
    echo "   ⚠️  API文档返回 HTTP $DOCS_CODE"
fi

echo ""

# 检查内存占用
echo "7️⃣  检查内存占用..."
MEMORY=$(pm2 jlist | python3 -c "import sys, json; data=json.load(sys.stdin); print([p for p in data if p['name']=='timao-cloud'][0]['monit']['memory'] // 1024 // 1024)" 2>/dev/null || echo "未知")
if [ "$MEMORY" != "未知" ]; then
    echo "   📊 当前内存: ${MEMORY}MB"
    if [ "$MEMORY" -lt 600 ]; then
        echo "   ✅ 内存占用正常 (< 600MB)"
    else
        echo "   ⚠️  内存占用偏高 (>= 600MB)"
    fi
else
    echo "   ⚠️  无法获取内存信息"
fi

echo ""

# 检查重启次数
echo "8️⃣  检查重启次数..."
RESTARTS=$(pm2 jlist | python3 -c "import sys, json; data=json.load(sys.stdin); print([p for p in data if p['name']=='timao-cloud'][0]['pm2_env']['restart_time'])" 2>/dev/null || echo "未知")
if [ "$RESTARTS" != "未知" ]; then
    echo "   🔄 重启次数: $RESTARTS"
    if [ "$RESTARTS" -eq 0 ]; then
        echo "   ✅ 服务稳定运行"
    elif [ "$RESTARTS" -lt 5 ]; then
        echo "   ⚠️  有少量重启"
    else
        echo "   ❌ 重启次数过多，可能有问题"
    fi
else
    echo "   ⚠️  无法获取重启信息"
fi

echo ""
echo "=========================================="
echo "📊 测试总结"
echo "=========================================="
echo ""
echo "✅ 所有关键测试通过！"
echo ""
echo "🌐 访问地址:"
echo "  - 控制台: http://localhost:15000/"
echo "  - API文档: http://localhost:15000/docs"
echo "  - 健康检查: http://localhost:15000/health"
echo ""
echo "📝 查看详细日志:"
echo "  pm2 logs timao-cloud"
echo ""

