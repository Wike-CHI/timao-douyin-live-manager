#!/bin/bash
# ============================================
# 服务部署器 (Service Deployer)
# ============================================
# 职责：构建Docker镜像并启动服务
# 依赖：配置管理器已执行
# 输出：部署状态报告
# ============================================

set -e

echo "🚀 开始部署服务..."

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 配置文件
UPLOAD_CONFIG="deploy/upload_config.env"
DEPLOY_REPORT="deploy/deploy_report.txt"

# 检查配置
check_config() {
    echo -e "\n${YELLOW}[1/5] 检查部署配置...${NC}"
    
    if [ ! -f "$UPLOAD_CONFIG" ]; then
        echo -e "${RED}❌ 未找到上传配置文件${NC}"
        echo "请先运行: ./deploy/2_upload_code.sh"
        exit 1
    fi
    
    source "$UPLOAD_CONFIG"
    echo "✅ 部署配置已加载"
    echo "服务器: $SERVER_USER@$SERVER_HOST"
    echo "路径: $SERVER_PATH"
}

# 构建 Docker 镜像
build_images() {
    echo -e "\n${YELLOW}[2/5] 构建 Docker 镜像...${NC}"
    
    # 构建 SSH 命令
    SSH_CMD="ssh"
    if [ -n "$SSH_KEY_PATH" ]; then
        SSH_CMD="$SSH_CMD -i $SSH_KEY_PATH"
    fi
    SSH_CMD="$SSH_CMD -p ${SERVER_PORT:-22}"
    
    # 在服务器上构建镜像
    echo "正在构建后端镜像..."
    $SSH_CMD "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH && docker-compose -f docker-compose.full.yml build --no-cache backend" || {
        echo -e "${RED}❌ 后端镜像构建失败${NC}"
        exit 1
    }
    echo "✅ 后端镜像构建完成"
    
    echo ""
    echo "正在构建前端镜像..."
    $SSH_CMD "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH && docker-compose -f docker-compose.full.yml build --no-cache frontend" || {
        echo -e "${RED}❌ 前端镜像构建失败${NC}"
        exit 1
    }
    echo "✅ 前端镜像构建完成"
}

# 停止旧服务
stop_old_services() {
    echo -e "\n${YELLOW}[3/5] 停止旧服务...${NC}"
    
    # 检查是否有正在运行的容器
    $SSH_CMD "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH && docker-compose -f docker-compose.full.yml ps -q" | grep -q . && {
        echo "发现正在运行的容器，正在停止..."
        $SSH_CMD "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH && docker-compose -f docker-compose.full.yml down"
        echo "✅ 旧服务已停止"
    } || {
        echo "✅ 没有正在运行的服务"
    }
}

# 启动新服务
start_services() {
    echo -e "\n${YELLOW}[4/5] 启动服务...${NC}"
    
    # 启动所有服务
    $SSH_CMD "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH && docker-compose -f docker-compose.full.yml up -d" || {
        echo -e "${RED}❌ 服务启动失败${NC}"
        
        # 显示日志
        echo "查看错误日志..."
        $SSH_CMD "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH && docker-compose -f docker-compose.full.yml logs --tail=50"
        
        exit 1
    }
    
    echo "✅ 服务已启动"
    echo ""
    echo "等待服务就绪（30秒）..."
    sleep 30
}

# 检查服务状态
check_service_status() {
    echo -e "\n${YELLOW}[5/5] 检查服务状态...${NC}"
    
    # 检查容器状态
    echo "检查容器状态..."
    $SSH_CMD "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH && docker-compose -f docker-compose.full.yml ps"
    
    # 检查后端健康
    echo ""
    echo "检查后端健康..."
    $SSH_CMD "$SERVER_USER@$SERVER_HOST" "curl -f http://localhost:11111/health" && {
        echo -e "${GREEN}✅ 后端服务正常${NC}"
    } || {
        echo -e "${RED}❌ 后端服务异常${NC}"
        echo "查看后端日志:"
        $SSH_CMD "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH && docker logs timao-backend --tail=50"
    }
    
    # 检查前端健康
    echo ""
    echo "检查前端健康..."
    $SSH_CMD "$SERVER_USER@$SERVER_HOST" "curl -f http://localhost/health" && {
        echo -e "${GREEN}✅ 前端服务正常${NC}"
    } || {
        echo -e "${YELLOW}⚠️  前端健康检查失败（可能正常，如果没有 /health 端点）${NC}"
    }
}

# 显示服务信息
show_service_info() {
    echo -e "\n${YELLOW}显示服务信息...${NC}"
    
    # 获取服务器IP
    SERVER_IP=$($SSH_CMD "$SERVER_USER@$SERVER_HOST" "curl -s ifconfig.me")
    
    echo ""
    echo "======================================"
    echo "服务访问信息"
    echo "======================================"
    echo "前端地址: http://$SERVER_IP"
    echo "后端地址: http://$SERVER_IP:11111"
    echo "后端API文档: http://$SERVER_IP:11111/docs"
    echo "======================================"
}

# 生成部署报告
generate_deploy_report() {
    echo -e "\n${YELLOW}生成部署报告...${NC}"
    
    # 获取服务器IP
    SERVER_IP=$($SSH_CMD "$SERVER_USER@$SERVER_HOST" "curl -s ifconfig.me" || echo "$SERVER_HOST")
    
    # 获取容器状态
    CONTAINER_STATUS=$($SSH_CMD "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH && docker-compose -f docker-compose.full.yml ps")
    
    cat > "$DEPLOY_REPORT" << EOF
====================================
服务部署报告
====================================
部署时间: $(date)

服务器信息:
  地址: $SERVER_HOST
  路径: $SERVER_PATH
  公网IP: $SERVER_IP

服务访问:
  前端: http://$SERVER_IP
  后端: http://$SERVER_IP:11111
  API文档: http://$SERVER_IP:11111/docs

容器状态:
$CONTAINER_STATUS

部署状态: ✅ 完成
====================================
EOF
    
    echo "✅ 部署报告已生成: $DEPLOY_REPORT"
}

# 提供常用命令
show_useful_commands() {
    echo ""
    echo "======================================"
    echo "常用管理命令"
    echo "======================================"
    echo ""
    echo "查看所有容器:"
    echo "  ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && docker-compose -f docker-compose.full.yml ps'"
    echo ""
    echo "查看日志:"
    echo "  ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && docker-compose -f docker-compose.full.yml logs -f'"
    echo ""
    echo "重启服务:"
    echo "  ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && docker-compose -f docker-compose.full.yml restart'"
    echo ""
    echo "停止服务:"
    echo "  ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && docker-compose -f docker-compose.full.yml down'"
    echo ""
    echo "======================================"
}

# 主执行流程
main() {
    echo "======================================"
    echo "    服务部署器 (Service Deployer)"
    echo "======================================"
    echo ""
    
    check_config
    build_images
    stop_old_services
    start_services
    check_service_status
    show_service_info
    generate_deploy_report
    show_useful_commands
    
    echo ""
    echo "======================================"
    echo -e "${GREEN}✅ 服务部署完成${NC}"
    echo "======================================"
    echo "部署报告: $DEPLOY_REPORT"
    echo ""
    echo "下一步: 运行部署验证器"
    echo "  ./deploy/5_validate_deployment.sh"
}

main

