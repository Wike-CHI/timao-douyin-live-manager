#!/bin/bash
# ============================================
# 环境准备器 (Environment Preparator)
# ============================================
# 职责：检查和安装云服务器所需的基础环境
# 依赖：无
# 输出：环境检查报告
# ============================================

set -e

echo "🔍 开始检查云服务器环境..."

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查结果记录
ENV_CHECK_RESULT="deploy/environment_check_report.txt"
mkdir -p deploy
echo "环境检查报告 - $(date)" > "$ENV_CHECK_RESULT"

# 1. 检查操作系统
check_os() {
    echo -e "\n${YELLOW}[1/6] 检查操作系统...${NC}"
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "✅ 操作系统: $NAME $VERSION"
        echo "操作系统: $NAME $VERSION" >> "$ENV_CHECK_RESULT"
    else
        echo -e "${RED}❌ 无法识别操作系统${NC}"
        exit 1
    fi
}

# 2. 检查 Docker
check_docker() {
    echo -e "\n${YELLOW}[2/6] 检查 Docker...${NC}"
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        echo "✅ Docker 已安装: $DOCKER_VERSION"
        echo "Docker: $DOCKER_VERSION" >> "$ENV_CHECK_RESULT"
    else
        echo -e "${RED}❌ Docker 未安装${NC}"
        echo "是否安装 Docker? (y/n)"
        read -r install_docker
        if [ "$install_docker" = "y" ]; then
            install_docker
        else
            exit 1
        fi
    fi
}

# 3. 检查 Docker Compose
check_docker_compose() {
    echo -e "\n${YELLOW}[3/6] 检查 Docker Compose...${NC}"
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version)
        echo "✅ Docker Compose 已安装: $COMPOSE_VERSION"
        echo "Docker Compose: $COMPOSE_VERSION" >> "$ENV_CHECK_RESULT"
    else
        echo -e "${RED}❌ Docker Compose 未安装${NC}"
        echo "是否安装 Docker Compose? (y/n)"
        read -r install_compose
        if [ "$install_compose" = "y" ]; then
            install_docker_compose
        else
            exit 1
        fi
    fi
}

# 4. 检查端口占用
check_ports() {
    echo -e "\n${YELLOW}[4/6] 检查端口占用...${NC}"
    
    PORTS=(80 11111)
    PORT_OK=true
    
    for port in "${PORTS[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            echo -e "${RED}❌ 端口 $port 已被占用${NC}"
            lsof -Pi :$port -sTCP:LISTEN
            PORT_OK=false
        else
            echo "✅ 端口 $port 可用"
        fi
    done
    
    if [ "$PORT_OK" = false ]; then
        echo -e "${YELLOW}⚠️  请先释放被占用的端口${NC}"
    fi
}

# 5. 检查磁盘空间
check_disk_space() {
    echo -e "\n${YELLOW}[5/6] 检查磁盘空间...${NC}"
    
    AVAILABLE=$(df -h / | awk 'NR==2 {print $4}')
    echo "✅ 可用磁盘空间: $AVAILABLE"
    echo "可用磁盘空间: $AVAILABLE" >> "$ENV_CHECK_RESULT"
    
    # 检查是否至少有 5GB 空间
    AVAILABLE_GB=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$AVAILABLE_GB" -lt 5 ]; then
        echo -e "${YELLOW}⚠️  磁盘空间不足 5GB，建议清理磁盘${NC}"
    fi
}

# 6. 检查内存
check_memory() {
    echo -e "\n${YELLOW}[6/6] 检查内存...${NC}"
    
    TOTAL_MEM=$(free -h | awk 'NR==2 {print $2}')
    AVAILABLE_MEM=$(free -h | awk 'NR==2 {print $7}')
    echo "✅ 总内存: $TOTAL_MEM"
    echo "✅ 可用内存: $AVAILABLE_MEM"
    echo "总内存: $TOTAL_MEM" >> "$ENV_CHECK_RESULT"
    echo "可用内存: $AVAILABLE_MEM" >> "$ENV_CHECK_RESULT"
}

# 安装 Docker
install_docker() {
    echo -e "\n${YELLOW}正在安装 Docker...${NC}"
    
    # Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y \
            ca-certificates \
            curl \
            gnupg \
            lsb-release
        
        # 添加 Docker 官方 GPG 密钥
        sudo mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        
        # 添加 Docker 仓库
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # 安装 Docker
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        
        # 启动 Docker
        sudo systemctl start docker
        sudo systemctl enable docker
        
        # 添加当前用户到 docker 组
        sudo usermod -aG docker $USER
        
        echo -e "${GREEN}✅ Docker 安装完成${NC}"
        echo "⚠️  请退出当前终端重新登录，使 docker 组权限生效"
    else
        echo -e "${RED}❌ 不支持的系统，请手动安装 Docker${NC}"
        exit 1
    fi
}

# 安装 Docker Compose
install_docker_compose() {
    echo -e "\n${YELLOW}正在安装 Docker Compose...${NC}"
    
    # 下载最新版本
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    echo -e "${GREEN}✅ Docker Compose 安装完成${NC}"
}

# 主执行流程
main() {
    echo "======================================"
    echo "    环境准备器 (Environment Preparator)"
    echo "======================================"
    echo ""
    
    check_os
    check_docker
    check_docker_compose
    check_ports
    check_disk_space
    check_memory
    
    echo ""
    echo "======================================"
    echo -e "${GREEN}✅ 环境检查完成${NC}"
    echo "======================================"
    echo "详细报告: $ENV_CHECK_RESULT"
    echo ""
}

main

