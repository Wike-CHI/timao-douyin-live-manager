#!/bin/bash
# 提猫直播助手 - 一站式安装启动器 (Linux/macOS版本)

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 参数解析
SKIP_DEPENDENCIES=false
PRODUCTION_MODE=false
QUICK_START=false
SHOW_HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-dependencies)
            SKIP_DEPENDENCIES=true
            shift
            ;;
        --production)
            PRODUCTION_MODE=true
            shift
            ;;
        --quick-start)
            QUICK_START=true
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

# 显示帮助信息
if [ "$SHOW_HELP" = true ]; then
    cat << EOF
提猫直播助手 - 一站式安装启动器

用法: ./scripts/构建与启动/install_and_start.sh [选项]

选项:
  --skip-dependencies    跳过依赖安装，直接启动
  --production          以生产模式启动
  --quick-start         快速启动，跳过环境检查
  --help, -h            显示此帮助信息

示例:
  ./scripts/构建与启动/install_and_start.sh                      # 完整安装和启动
  ./scripts/构建与启动/install_and_start.sh --skip-dependencies  # 跳过依赖安装
  ./scripts/构建与启动/install_and_start.sh --quick-start        # 快速启动
EOF
    exit 0
fi

# 工具函数
print_step() {
    echo -e "${MAGENTA}📋 步骤 $1: $2${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}🔧 $1${NC}"
}

check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

check_port() {
    local port=$1
    if nc -z 127.0.0.1 "$port" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

install_python_dependencies() {
    print_info "安装Python依赖包..."
    
    # 升级pip
    python -m pip install --upgrade pip
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        python -m pip install -r requirements.txt
        print_success "Python依赖安装成功"
    else
        print_warning "未找到requirements.txt文件"
    fi
}

install_node_dependencies() {
    print_info "安装Node.js依赖..."
    
    # 安装项目依赖
    if [ -f "package.json" ]; then
        npm install
        print_success "项目依赖安装成功"
    fi
    
    # 安装前端依赖
    if [ -f "electron/renderer/package.json" ]; then
        cd electron/renderer
        npm install
        cd ../..
        print_success "前端依赖安装成功"
    fi
}

# 主程序开始
clear
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}提猫直播助手 - 一站式安装启动器${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 设置项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

print_info "🚀 开始安装和配置环境..."
echo ""

if [ "$QUICK_START" != true ]; then
    # ========================================
    # 1. 检查Python环境
    # ========================================
    print_step "1/6" "检查Python环境"
    
    if ! check_command python && ! check_command python3; then
        print_error "未找到Python"
        echo -e "${CYAN}请先安装Python 3.8+${NC}"
        echo -e "${CYAN}Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv${NC}"
        echo -e "${CYAN}CentOS/RHEL: sudo yum install python3 python3-pip${NC}"
        echo -e "${CYAN}macOS: brew install python3${NC}"
        exit 1
    fi
    
    # 优先使用python3
    if check_command python3; then
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
    else
        PYTHON_CMD="python"
        PIP_CMD="pip"
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
    print_success "Python版本: $PYTHON_VERSION"
    echo ""
    
    # ========================================
    # 2. 创建和激活虚拟环境
    # ========================================
    print_step "2/6" "配置Python虚拟环境"
    
    if [ ! -d ".venv" ]; then
        print_info "创建Python虚拟环境..."
        $PYTHON_CMD -m venv .venv
        print_success "虚拟环境创建成功"
    else
        print_success "虚拟环境已存在"
    fi
    
    # 激活虚拟环境
    print_info "激活虚拟环境..."
    source .venv/bin/activate
    print_success "虚拟环境激活成功"
    echo ""
    
    # ========================================
    # 3. 安装Python依赖
    # ========================================
    if [ "$SKIP_DEPENDENCIES" != true ]; then
        print_step "3/6" "安装Python依赖"
        install_python_dependencies
        echo ""
    fi
    
    # ========================================
    # 4. 检查Node.js环境
    # ========================================
    print_step "4/6" "检查Node.js环境"
    
    if ! check_command node; then
        print_error "未找到Node.js"
        echo -e "${CYAN}请先安装Node.js LTS版本${NC}"
        echo -e "${CYAN}Ubuntu/Debian: curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs${NC}"
        echo -e "${CYAN}CentOS/RHEL: curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash - && sudo yum install -y nodejs${NC}"
        echo -e "${CYAN}macOS: brew install node${NC}"
        exit 1
    fi
    
    NODE_VERSION=$(node --version 2>&1)
    print_success "Node.js版本: $NODE_VERSION"
    
    if ! check_command npm; then
        print_error "未找到npm"
        echo -e "${CYAN}请确保Node.js已正确安装（包含npm）${NC}"
        exit 1
    fi
    
    NPM_VERSION=$(npm --version 2>&1)
    print_success "npm版本: $NPM_VERSION"
    echo ""
    
    # ========================================
    # 5. 安装Node.js依赖
    # ========================================
    if [ "$SKIP_DEPENDENCIES" != true ]; then
        print_step "5/6" "安装Node.js依赖"
        install_node_dependencies
        echo ""
    fi
fi

# ========================================
# 6. 启动应用
# ========================================
print_step "6/6" "启动应用"
echo ""

# 检查端口占用
PORTS=(9019 9020 9021 10030)
OCCUPIED_PORTS=()

for port in "${PORTS[@]}"; do
    if check_port "$port"; then
        OCCUPIED_PORTS+=("$port")
    fi
done

if [ ${#OCCUPIED_PORTS[@]} -gt 0 ]; then
    print_warning "以下端口已被占用: ${OCCUPIED_PORTS[*]}"
    echo -n -e "${CYAN}是否继续启动？某些服务可能无法正常工作。(y/N): ${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_warning "启动已取消"
        exit 0
    fi
fi

print_success "🎉 环境配置完成！正在启动应用..."
echo ""
echo -e "${CYAN}📝 启动信息:${NC}"
echo -e "${CYAN}   - 后端服务: http://127.0.0.1:9019${NC}"
echo -e "${CYAN}   - 前端开发服务器: http://127.0.0.1:10030${NC}"
echo -e "${CYAN}   - 健康检查: http://127.0.0.1:9019/health${NC}"
echo ""
print_info "🔄 启动中，请稍候..."
echo ""

# 启动应用
if [ "$PRODUCTION_MODE" = true ]; then
    npm run services:prod
else
    npm run dev
fi

# 错误处理
if [ $? -ne 0 ]; then
    echo ""
    print_error "应用启动失败"
    echo ""
    echo -e "${CYAN}🔍 故障排除建议:${NC}"
    echo -e "${CYAN}1. 检查网络连接${NC}"
    echo -e "${CYAN}2. 检查端口是否被占用 (9019, 9020, 9021, 10030)${NC}"
    echo -e "${CYAN}3. 检查防火墙设置${NC}"
    echo -e "${CYAN}4. 查看详细错误信息${NC}"
    echo -e "${CYAN}5. 尝试手动启动: npm run dev${NC}"
    echo ""
    echo -e "${CYAN}💡 获取帮助: ./scripts/构建与启动/install_and_start.sh --help${NC}"
    exit 1
fi

echo ""
print_success "应用启动成功！"
echo -e "${CYAN}💡 按 Ctrl+C 停止应用${NC}"