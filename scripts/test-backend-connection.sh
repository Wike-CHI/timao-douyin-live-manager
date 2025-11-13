#!/bin/bash

################################################################################
# 后端连接测试脚本
# 
# 功能：测试前端能否连接到公网后端
# 后端地址：http://129.211.218.135
# 
# 使用方法：
#   chmod +x scripts/test-backend-connection.sh
#   ./scripts/test-backend-connection.sh
################################################################################

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 后端地址
BACKEND_URL="http://129.211.218.135"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_separator() {
    echo "========================================================================"
}

print_title() {
    print_separator
    echo -e "${GREEN}$1${NC}"
    print_separator
}

################################################################################
# 测试开始
################################################################################

print_title "后端连接测试"

log_info "测试目标: $BACKEND_URL"
log_info "开始测试..."
echo ""

# 1. 测试网络连通性
print_title "1. 测试网络连通性"
log_info "Ping 测试..."
if ping -c 3 129.211.218.135 &> /dev/null; then
    log_success "网络连通正常"
else
    log_error "网络连通失败"
    log_info "提示：请检查网络连接或防火墙设置"
fi
echo ""

# 2. 测试主服务健康检查
print_title "2. 测试 FastAPI 主服务"
log_info "请求: GET ${BACKEND_URL}/health"

response=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/health" 2>/dev/null || echo -e "\n000")
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" = "200" ]; then
    log_success "主服务健康检查通过 (HTTP $http_code)"
    log_info "响应内容:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    log_error "主服务健康检查失败 (HTTP $http_code)"
    log_info "响应内容: $body"
    exit 1
fi
echo ""

# 3. 测试 StreamCap 服务
print_title "3. 测试 StreamCap 服务"
log_info "请求: GET ${BACKEND_URL}/api/streamcap/health"

response=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/api/streamcap/health" 2>/dev/null || echo -e "\n000")
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" = "200" ]; then
    log_success "StreamCap 服务健康检查通过 (HTTP $http_code)"
    log_info "响应内容:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    log_error "StreamCap 服务健康检查失败 (HTTP $http_code)"
    log_info "响应内容: $body"
fi
echo ""

# 4. 测试 Douyin 服务
print_title "4. 测试 Douyin 服务"
log_info "请求: GET ${BACKEND_URL}/api/douyin/health"

response=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/api/douyin/health" 2>/dev/null || echo -e "\n000")
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" = "200" ]; then
    log_success "Douyin 服务健康检查通过 (HTTP $http_code)"
    log_info "响应内容:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    log_error "Douyin 服务健康检查失败 (HTTP $http_code)"
    log_info "响应内容: $body"
fi
echo ""

# 5. 测试响应时间
print_title "5. 测试响应时间"
log_info "测量 API 响应速度..."

start_time=$(date +%s%N)
curl -s "${BACKEND_URL}/health" > /dev/null 2>&1
end_time=$(date +%s%N)

elapsed_ms=$(( (end_time - start_time) / 1000000 ))

if [ $elapsed_ms -lt 1000 ]; then
    log_success "响应时间: ${elapsed_ms}ms (优秀)"
elif [ $elapsed_ms -lt 3000 ]; then
    log_success "响应时间: ${elapsed_ms}ms (良好)"
else
    log_error "响应时间: ${elapsed_ms}ms (较慢)"
fi
echo ""

# 6. 检查 Nginx 配置
print_title "6. 检查 Nginx 反向代理"
log_info "测试 Nginx Headers..."

headers=$(curl -sI "${BACKEND_URL}/health" 2>/dev/null || echo "")

if echo "$headers" | grep -qi "nginx"; then
    log_success "Nginx 反向代理正常工作"
    log_info "服务器信息:"
    echo "$headers" | grep -i "server:" || echo "  (未找到 Server header)"
else
    log_error "未检测到 Nginx (可能直连后端)"
fi
echo ""

################################################################################
# 总结
################################################################################

print_separator
log_success "🎉 连接测试完成！"
print_separator

echo ""
log_info "📊 测试总结:"
log_info "  ✓ 后端地址: $BACKEND_URL"
log_info "  ✓ 主服务状态: 正常"
log_info "  ✓ 响应时间: ${elapsed_ms}ms"

echo ""
log_info "✅ 前端可以正常连接到公网后端"
log_info "✅ 可以继续进行打包操作"

echo ""
log_info "📦 下一步："
log_info "  ./scripts/build-electron-production.sh"

exit 0

