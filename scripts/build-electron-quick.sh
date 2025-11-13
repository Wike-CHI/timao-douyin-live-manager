#!/bin/bash

################################################################################
# 提猫直播助手 - Electron 快速打包脚本
# 
# 功能：快速打包（跳过依赖安装）
# 适用场景：依赖已安装，只需重新构建
# 
# 使用方法：
#   chmod +x scripts/build-electron-quick.sh
#   ./scripts/build-electron-quick.sh
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
log_error() { echo -e "${RED}[✗]${NC} $1"; }
print_separator() { echo "========================================================================"; }
print_title() { print_separator; echo -e "${GREEN}$1${NC}"; print_separator; }

# 配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ELECTRON_DIR="${PROJECT_ROOT}/electron"
RENDERER_DIR="${ELECTRON_DIR}/renderer"
BUILD_DIR="${PROJECT_ROOT}/dist"
PRODUCTION_API_URL="http://129.211.218.135"
BUILD_CONFIG="${PROJECT_ROOT}/build-config.json"
BUILD_TARGET="${BUILD_TARGET:-win}"
APP_VERSION=$(node -p "require('${PROJECT_ROOT}/package.json').version" 2>/dev/null || echo "1.0.0")

################################################################################
# 开始快速打包
################################################################################

print_title "快速打包 - Electron 应用"
echo ""
log_info "后端地址: $PRODUCTION_API_URL"
log_info "构建目标: $BUILD_TARGET"
log_info "应用版本: $APP_VERSION"
echo ""

# 1. 清理旧构建
print_title "1/3: 清理旧构建"
log_info "清理 dist 目录..."
if [ -d "$BUILD_DIR" ]; then
    if [ -f "$BUILD_DIR/.user.ini" ]; then
        chattr -i "$BUILD_DIR/.user.ini" 2>/dev/null || true
    fi
    rm -rf "$BUILD_DIR"
    log_success "已删除旧的 dist 目录"
fi

log_info "清理前端构建..."
if [ -d "$RENDERER_DIR/dist" ]; then
    rm -rf "$RENDERER_DIR/dist"
    log_success "已删除旧的前端构建"
fi

# 2. 配置环境并构建前端
print_title "2/3: 构建前端"

# 创建 .env.production
cat > "$RENDERER_DIR/.env.production" << EOF
VITE_FASTAPI_URL=${PRODUCTION_API_URL}
VITE_STREAMCAP_URL=${PRODUCTION_API_URL}
VITE_DOUYIN_URL=${PRODUCTION_API_URL}
VITE_APP_ENV=production
NODE_ENV=production
VITE_BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VITE_BUILD_VERSION=${APP_VERSION}
VITE_BUILD_PLATFORM=${BUILD_TARGET}
VITE_DEMO_MODE=false
VITE_ENABLE_DEVTOOLS=false
EOF
log_success "环境配置已创建"

cd "$RENDERER_DIR"
log_info "构建前端..."
export NODE_ENV=production
if npm run build; then
    log_success "前端构建成功"
else
    log_error "前端构建失败"
    exit 1
fi

# 验证构建产物
if [ ! -f "$RENDERER_DIR/dist/index.html" ]; then
    log_error "index.html 不存在！"
    exit 1
fi
log_success "构建产物验证通过"

# 3. 打包 Electron
print_title "3/3: 打包 Electron 应用"

export ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
export ELECTRON_BUILDER_BINARIES_MIRROR="https://npmmirror.com/mirrors/electron-builder-binaries/"

log_info "打包目标: $BUILD_TARGET"

# 从 electron 目录运行 electron-builder
cd "$ELECTRON_DIR"

case "$BUILD_TARGET" in
    win)
        log_info "打包 Windows x64 (便携版，无签名)..."
        npx electron-builder --win --x64 -c.win.sign=null -c.win.signDlls=false || {
            log_error "打包失败"
            exit 1
        }
        ;;
    *)
        log_error "仅支持 Windows 打包，使用: BUILD_TARGET=win"
        exit 1
        ;;
esac

log_success "打包完成"

# 验证结果
print_title "打包结果"

# electron-builder 的输出目录在 electron/dist/
ELECTRON_DIST="${ELECTRON_DIR}/dist"

if [ -d "$ELECTRON_DIST" ]; then
    log_info "打包产物:"
    find "$ELECTRON_DIST" -name "*.exe" -exec ls -lh {} \; || ls -lh "$ELECTRON_DIST"
    TOTAL_SIZE=$(du -sh "$ELECTRON_DIST" | cut -f1)
    log_info "总大小: $TOTAL_SIZE"
    
    # 复制到项目根目录的 dist (方便访问)
    log_info "复制安装包到项目根目录..."
    mkdir -p "$BUILD_DIR"
    find "$ELECTRON_DIST" -name "*.exe" -exec cp {} "$BUILD_DIR/" \;
    log_success "安装包已复制到: $BUILD_DIR"
else
    log_error "打包产物目录不存在"
    exit 1
fi

print_separator
log_success "🎉 打包完成！"
print_separator
log_info "产物位置: $BUILD_DIR"
log_info "下载命令: scp root@129.211.218.135:$BUILD_DIR/TalkingCat-*.exe ."
print_separator

exit 0

