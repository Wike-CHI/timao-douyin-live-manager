#!/bin/bash
# 检查后端服务状态

SERVER_IP="129.211.218.135"
BACKEND_PORT="10050"

echo "🔍 检查后端服务状态..."
echo ""

# 1. 检查端口是否开放
echo "1️⃣ 检查端口 ${BACKEND_PORT} 是否开放..."
if timeout 3 bash -c "echo > /dev/tcp/${SERVER_IP}/${BACKEND_PORT}" 2>/dev/null; then
    echo "   ✅ 端口 ${BACKEND_PORT} 已开放"
else
    echo "   ❌ 端口 ${BACKEND_PORT} 未开放或服务未运行"
fi

# 2. 检查健康检查接口
echo ""
echo "2️⃣ 检查健康检查接口..."
HEALTH_URL="http://${SERVER_IP}:${BACKEND_PORT}/health"
if curl -f -s --max-time 5 "${HEALTH_URL}" > /dev/null 2>&1; then
    echo "   ✅ 健康检查通过: ${HEALTH_URL}"
    curl -s "${HEALTH_URL}" | head -5
else
    echo "   ❌ 健康检查失败: ${HEALTH_URL}"
    echo "   可能原因："
    echo "   - 服务未启动"
    echo "   - 服务启动失败"
    echo "   - 防火墙阻止"
    echo "   - 服务监听地址错误"
fi

echo ""
echo "📋 诊断完成"

