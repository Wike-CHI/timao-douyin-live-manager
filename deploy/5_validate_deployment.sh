#!/bin/bash
# ============================================
# 部署验证器 (Deployment Validator)
# ============================================
# 职责：验证部署是否成功，测试核心功能
# 依赖：服务部署器已执行
# 输出：验证报告
# ============================================

set -e

echo "✅ 开始验证部署..."

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 配置文件
UPLOAD_CONFIG="deploy/upload_config.env"
VALIDATION_REPORT="deploy/validation_report.txt"

# 验证结果
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 记录测试结果
record_test() {
    local test_name=$1
    local status=$2
    local message=$3
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$status" = "pass" ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo -e "${GREEN}✅ $test_name${NC}"
        echo "[PASS] $test_name: $message" >> "$VALIDATION_REPORT"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo -e "${RED}❌ $test_name${NC}"
        echo "[FAIL] $test_name: $message" >> "$VALIDATION_REPORT"
    fi
}

# 检查配置
check_config() {
    echo -e "\n${YELLOW}准备验证环境...${NC}"
    
    if [ ! -f "$UPLOAD_CONFIG" ]; then
        echo -e "${RED}❌ 未找到上传配置文件${NC}"
        exit 1
    fi
    
    source "$UPLOAD_CONFIG"
    
    # 构建 SSH 命令
    SSH_CMD="ssh"
    if [ -n "$SSH_KEY_PATH" ]; then
        SSH_CMD="$SSH_CMD -i $SSH_KEY_PATH"
    fi
    SSH_CMD="$SSH_CMD -p ${SERVER_PORT:-22}"
    
    # 获取服务器IP
    SERVER_IP=$($SSH_CMD "$SERVER_USER@$SERVER_HOST" "curl -s ifconfig.me" || echo "$SERVER_HOST")
    
    echo "✅ 验证环境已准备"
    
    # 初始化报告
    cat > "$VALIDATION_REPORT" << EOF
====================================
部署验证报告
====================================
验证时间: $(date)
服务器: $SERVER_USER@$SERVER_HOST
公网IP: $SERVER_IP

测试结果:
====================================
EOF
}

# 测试1: 容器状态
test_containers() {
    echo -e "\n${YELLOW}[1/8] 测试容器状态...${NC}"
    
    # 检查后端容器
    if $SSH_CMD "$SERVER_USER@$SERVER_HOST" "docker ps | grep -q timao-backend"; then
        record_test "后端容器运行" "pass" "容器正在运行"
    else
        record_test "后端容器运行" "fail" "容器未运行"
    fi
    
    # 检查前端容器
    if $SSH_CMD "$SERVER_USER@$SERVER_HOST" "docker ps | grep -q timao-frontend"; then
        record_test "前端容器运行" "pass" "容器正在运行"
    else
        record_test "前端容器运行" "fail" "容器未运行"
    fi
}

# 测试2: 端口监听
test_ports() {
    echo -e "\n${YELLOW}[2/8] 测试端口监听...${NC}"
    
    # 检查后端端口
    if $SSH_CMD "$SERVER_USER@$SERVER_HOST" "netstat -tuln | grep -q ':11111'"; then
        record_test "后端端口监听" "pass" "端口 11111 正在监听"
    else
        record_test "后端端口监听" "fail" "端口 11111 未监听"
    fi
    
    # 检查前端端口
    if $SSH_CMD "$SERVER_USER@$SERVER_HOST" "netstat -tuln | grep -q ':80'"; then
        record_test "前端端口监听" "pass" "端口 80 正在监听"
    else
        record_test "前端端口监听" "fail" "端口 80 未监听"
    fi
}

# 测试3: 后端健康检查
test_backend_health() {
    echo -e "\n${YELLOW}[3/8] 测试后端健康...${NC}"
    
    # 本地健康检查
    if $SSH_CMD "$SERVER_USER@$SERVER_HOST" "curl -f -s http://localhost:11111/health > /dev/null"; then
        record_test "后端健康检查（本地）" "pass" "健康检查通过"
    else
        record_test "后端健康检查（本地）" "fail" "健康检查失败"
    fi
    
    # 外部健康检查
    if curl -f -s "http://$SERVER_IP:11111/health" > /dev/null 2>&1; then
        record_test "后端健康检查（外部）" "pass" "外部访问正常"
    else
        record_test "后端健康检查（外部）" "fail" "外部访问失败（检查防火墙）"
    fi
}

# 测试4: 前端访问
test_frontend_access() {
    echo -e "\n${YELLOW}[4/8] 测试前端访问...${NC}"
    
    # 本地访问
    if $SSH_CMD "$SERVER_USER@$SERVER_HOST" "curl -f -s http://localhost > /dev/null"; then
        record_test "前端访问（本地）" "pass" "前端页面可访问"
    else
        record_test "前端访问（本地）" "fail" "前端页面访问失败"
    fi
    
    # 外部访问
    if curl -f -s "http://$SERVER_IP" > /dev/null 2>&1; then
        record_test "前端访问（外部）" "pass" "外部访问正常"
    else
        record_test "前端访问（外部）" "fail" "外部访问失败（检查防火墙）"
    fi
}

# 测试5: API文档
test_api_docs() {
    echo -e "\n${YELLOW}[5/8] 测试API文档...${NC}"
    
    if $SSH_CMD "$SERVER_USER@$SERVER_HOST" "curl -f -s http://localhost:11111/docs > /dev/null"; then
        record_test "API文档访问" "pass" "API文档可访问"
    else
        record_test "API文档访问" "fail" "API文档访问失败"
    fi
}

# 测试6: 数据库连接
test_database() {
    echo -e "\n${YELLOW}[6/8] 测试数据库连接...${NC}"
    
    # 通过后端日志检查数据库连接
    DB_LOG=$($SSH_CMD "$SERVER_USER@$SERVER_HOST" "docker logs timao-backend 2>&1 | grep -i 'database\\|mysql' | tail -5")
    
    if echo "$DB_LOG" | grep -iq "error"; then
        record_test "数据库连接" "fail" "数据库连接可能有问题，请检查日志"
    else
        record_test "数据库连接" "pass" "数据库连接正常"
    fi
}

# 测试7: 容器资源使用
test_resources() {
    echo -e "\n${YELLOW}[7/8] 测试容器资源...${NC}"
    
    # 检查后端容器资源
    BACKEND_STATS=$($SSH_CMD "$SERVER_USER@$SERVER_HOST" "docker stats timao-backend --no-stream --format '{{.CPUPerc}} {{.MemUsage}}'")
    
    if [ -n "$BACKEND_STATS" ]; then
        record_test "后端资源使用" "pass" "资源监控正常: $BACKEND_STATS"
    else
        record_test "后端资源使用" "fail" "无法获取资源信息"
    fi
    
    # 检查前端容器资源
    FRONTEND_STATS=$($SSH_CMD "$SERVER_USER@$SERVER_HOST" "docker stats timao-frontend --no-stream --format '{{.CPUPerc}} {{.MemUsage}}'")
    
    if [ -n "$FRONTEND_STATS" ]; then
        record_test "前端资源使用" "pass" "资源监控正常: $FRONTEND_STATS"
    else
        record_test "前端资源使用" "fail" "无法获取资源信息"
    fi
}

# 测试8: 日志输出
test_logs() {
    echo -e "\n${YELLOW}[8/8] 测试日志输出...${NC}"
    
    # 检查后端日志
    BACKEND_LOG_COUNT=$($SSH_CMD "$SERVER_USER@$SERVER_HOST" "docker logs timao-backend 2>&1 | wc -l")
    
    if [ "$BACKEND_LOG_COUNT" -gt 10 ]; then
        record_test "后端日志输出" "pass" "日志正常（$BACKEND_LOG_COUNT 行）"
    else
        record_test "后端日志输出" "fail" "日志过少，服务可能未正常启动"
    fi
    
    # 检查前端日志
    FRONTEND_LOG_COUNT=$($SSH_CMD "$SERVER_USER@$SERVER_HOST" "docker logs timao-frontend 2>&1 | wc -l")
    
    if [ "$FRONTEND_LOG_COUNT" -gt 5 ]; then
        record_test "前端日志输出" "pass" "日志正常（$FRONTEND_LOG_COUNT 行）"
    else
        record_test "前端日志输出" "fail" "日志过少"
    fi
}

# 生成测试摘要
generate_summary() {
    echo -e "\n${YELLOW}生成测试摘要...${NC}"
    
    # 计算成功率
    SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    
    # 添加到报告
    cat >> "$VALIDATION_REPORT" << EOF

====================================
测试摘要
====================================
总测试数: $TOTAL_TESTS
通过: $PASSED_TESTS
失败: $FAILED_TESTS
成功率: $SUCCESS_RATE%

部署状态: $([ $SUCCESS_RATE -ge 80 ] && echo "✅ 成功" || echo "❌ 失败")
====================================
EOF
    
    # 显示摘要
    echo ""
    echo "======================================"
    echo "测试摘要"
    echo "======================================"
    echo "总测试数: $TOTAL_TESTS"
    echo "通过: $PASSED_TESTS"
    echo "失败: $FAILED_TESTS"
    echo "成功率: $SUCCESS_RATE%"
    echo "======================================"
    
    # 判断部署状态
    if [ $SUCCESS_RATE -ge 80 ]; then
        echo -e "${GREEN}✅ 部署验证通过${NC}"
        return 0
    else
        echo -e "${RED}❌ 部署验证失败${NC}"
        echo "请检查失败的测试项"
        return 1
    fi
}

# 显示访问信息
show_access_info() {
    echo ""
    echo "======================================"
    echo "服务访问信息"
    echo "======================================"
    echo "前端: http://$SERVER_IP"
    echo "后端: http://$SERVER_IP:11111"
    echo "API文档: http://$SERVER_IP:11111/docs"
    echo "======================================"
    echo ""
    echo "如果外部无法访问，请检查防火墙规则:"
    echo "  sudo ufw allow 80/tcp"
    echo "  sudo ufw allow 11111/tcp"
    echo "======================================"
}

# 主执行流程
main() {
    echo "======================================"
    echo "  部署验证器 (Deployment Validator)"
    echo "======================================"
    echo ""
    
    check_config
    test_containers
    test_ports
    test_backend_health
    test_frontend_access
    test_api_docs
    test_database
    test_resources
    test_logs
    
    if generate_summary; then
        show_access_info
        
        echo ""
        echo "验证报告: $VALIDATION_REPORT"
        echo ""
        echo "下一步: 配置运维监控"
        echo "  ./deploy/6_setup_monitoring.sh"
        exit 0
    else
        echo ""
        echo "验证报告: $VALIDATION_REPORT"
        exit 1
    fi
}

main

