#!/bin/bash

################################################################################
# 提猫直播助手 - 使用 Docker Wine 打包 Windows 应用
# 
# 功能：在 Linux 服务器上使用 Docker Wine 构建 Windows 安装包
# 
# 前置条件：
#   - Docker 已安装
#   - scottyhardy/docker-wine 镜像已拉取
#
# 使用方法：
#   chmod +x scripts/build-electron-docker-wine.sh
#   ./scripts/build-electron-docker-wine.sh
################################################################################

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
print_separator() { echo "========================================================================"; }
print_title() { print_separator; echo -e "${GREEN}$1${NC}"; print_separator; }

# 配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ELECTRON_DIR="${PROJECT_ROOT}/electron"
RENDERER_DIR="${ELECTRON_DIR}/renderer"
BUILD_DIR="${PROJECT_ROOT}/dist"
PRODUCTION_API_URL="http://129.211.218.135"
APP_VERSION=$(node -p "require('${PROJECT_ROOT}/package.json').version" 2>/dev/null || echo "1.0.0")

################################################################################
# 步骤 1：准备构建环境
################################################################################

print_title "使用 Docker Wine 打包 Electron 应用"
echo ""
log_info "后端地址: $PRODUCTION_API_URL"
log_info "应用版本: $APP_VERSION"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker 未安装！"
    exit 1
fi
log_success "Docker 已安装"

# 检查 Docker Wine 镜像
if ! docker images | grep -q "scottyhardy/docker-wine"; then
    log_warning "Docker Wine 镜像未找到，正在拉取..."
    docker pull scottyhardy/docker-wine
fi
log_success "Docker Wine 镜像已就绪"

################################################################################
# 步骤 2：构建前端
################################################################################

print_title "步骤 1/2: 构建前端"

# 清理旧构建
log_info "清理旧构建..."
if [ -d "$RENDERER_DIR/dist" ]; then
    rm -rf "$RENDERER_DIR/dist"
fi

# 创建环境配置
log_info "配置生产环境..."
cat > "$RENDERER_DIR/.env.production" << EOF
VITE_FASTAPI_URL=${PRODUCTION_API_URL}
VITE_STREAMCAP_URL=${PRODUCTION_API_URL}
VITE_DOUYIN_URL=${PRODUCTION_API_URL}
VITE_APP_ENV=production
NODE_ENV=production
VITE_BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VITE_BUILD_VERSION=${APP_VERSION}
VITE_DEMO_MODE=false
EOF
log_success "环境配置已创建"

# 构建前端
cd "$RENDERER_DIR"
log_info "构建前端..."
export NODE_ENV=production
npm run build || {
    log_error "前端构建失败"
    exit 1
}
log_success "前端构建成功"

################################################################################
# 步骤 3：使用 Docker 打包
################################################################################

print_title "步骤 2/2: 使用 Docker Wine 打包"

cd "$PROJECT_ROOT"

log_info "方案：在容器内安装依赖并打包"
log_warning "注意：此过程可能需要 10-20 分钟，请耐心等待..."
echo ""

# 创建临时打包脚本
cat > /tmp/electron-build-in-docker.sh << 'SCRIPT_EOF'
#!/bin/bash
set -e

echo "======================================================================"
echo "[Docker] 开始在容器内打包"
echo "======================================================================"

cd /workspace/electron

# 安装 Node.js（如果没有）
if ! command -v node &> /dev/null; then
    echo "[Docker] 安装 Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

echo "[Docker] Node 版本: $(node -v)"
echo "[Docker] npm 版本: $(npm -v)"

# 安装依赖
echo "[Docker] 安装 Electron 依赖..."
export ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
npm install --legacy-peer-deps

# 打包
echo "[Docker] 开始打包 Windows x64..."
npx electron-builder --win --x64 -c.win.sign=null -c.win.signDlls=false

echo "[Docker] 打包完成！"
ls -lh dist/
SCRIPT_EOF

chmod +x /tmp/electron-build-in-docker.sh

# 在 Docker 容器中运行打包
log_info "启动 Docker 容器进行打包..."
docker run --rm \
    -v "${PROJECT_ROOT}:/workspace" \
    -v "/tmp/electron-build-in-docker.sh:/build.sh" \
    -e ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/" \
    -e ELECTRON_BUILDER_BINARIES_MIRROR="https://npmmirror.com/mirrors/electron-builder-binaries/" \
    --workdir /workspace \
    scottyhardy/docker-wine \
    bash /build.sh

################################################################################
# 步骤 4：验证结果
################################################################################

print_title "打包结果验证"

ELECTRON_DIST="${ELECTRON_DIR}/dist"

if [ -d "$ELECTRON_DIST" ]; then
    log_info "打包产物:"
    find "$ELECTRON_DIST" -name "*.exe" -exec ls -lh {} \; || ls -lh "$ELECTRON_DIST"
    
    # 复制到项目根目录
    log_info "复制安装包到项目根目录..."
    mkdir -p "$BUILD_DIR"
    find "$ELECTRON_DIST" -name "*.exe" -exec cp {} "$BUILD_DIR/" \;
    
    TOTAL_SIZE=$(du -sh "$ELECTRON_DIST" | cut -f1)
    log_info "总大小: $TOTAL_SIZE"
    log_success "安装包已复制到: $BUILD_DIR"
else
    log_error "打包产物目录不存在"
    exit 1
fi

################################################################################
# 完成
################################################################################

print_separator
log_success "🎉 打包完成！"
print_separator
log_info "产物位置: $BUILD_DIR"
log_info "下载命令: scp root@129.211.218.135:$BUILD_DIR/TalkingCat-*.exe ."
print_separator

exit 0

