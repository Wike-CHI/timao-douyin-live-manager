#!/bin/bash
# 测试云端服务控制台页面
# 审查人：叶维哲

echo "========================================"
echo "🧪 测试云端服务控制台"
echo "========================================"
echo ""

# 检测服务端口
CLOUD_PORT=${CLOUD_PORT:-15000}
NGINX_PORT=80

echo "1️⃣  测试直接访问云端服务..."
echo "   端口: $CLOUD_PORT"

HEALTH_CHECK=$(curl -s http://localhost:$CLOUD_PORT/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ 云端服务健康检查通过"
    echo "$HEALTH_CHECK" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_CHECK"
else
    echo "❌ 云端服务未响应"
    echo "   请启动服务: pm2 start ecosystem.cloud.config.js"
    exit 1
fi

echo ""
echo "2️⃣  测试控制台页面..."

# 测试HTML页面
HTML_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:$CLOUD_PORT/)
HTTP_CODE=$(echo "$HTML_RESPONSE" | tail -n 1)
CONTENT=$(echo "$HTML_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    if echo "$CONTENT" | grep -q "提猫直播助手"; then
        echo "✅ 控制台页面加载成功"
        echo "   内容包含: 提猫直播助手标题"
    else
        echo "⚠️  页面返回200但内容可能不正确"
    fi
else
    echo "❌ 控制台页面加载失败 (HTTP $HTTP_CODE)"
fi

echo ""
echo "3️⃣  测试静态资源..."

# 测试logo
LOGO_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$CLOUD_PORT/static/assets/logo_cat_headset.jpg)
if [ "$LOGO_CHECK" = "200" ]; then
    echo "✅ Logo加载成功"
else
    echo "⚠️  Logo加载失败 (HTTP $LOGO_CHECK)"
fi

echo ""
echo "4️⃣  测试通过Nginx访问..."

NGINX_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$NGINX_PORT/)
if [ "$NGINX_CHECK" = "200" ]; then
    echo "✅ Nginx代理正常"
    echo "   可通过 http://localhost/ 访问控制台"
else
    echo "⚠️  Nginx代理未配置或未启动 (HTTP $NGINX_CHECK)"
    echo "   运行: sudo ./scripts/setup_nginx_cloud.sh"
fi

echo ""
echo "========================================"
echo "📊 测试结果汇总"
echo "========================================"
echo ""
echo "访问地址:"
echo "  - 直接访问: http://localhost:$CLOUD_PORT/"
echo "  - 通过Nginx: http://localhost/"
echo "  - 公网访问: http://服务器IP/"
echo ""
echo "API文档:"
echo "  - Swagger UI: http://localhost:$CLOUD_PORT/docs"
echo "  - 健康检查: http://localhost:$CLOUD_PORT/health"
echo ""
echo "🎉 测试完成！"

