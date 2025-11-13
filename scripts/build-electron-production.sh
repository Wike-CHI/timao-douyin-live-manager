#!/bin/bash

################################################################################
# 提猫直播助手 - Electron 应用生产环境打包脚本（简化版）
# 
# 功能：构建连接到公网后端的 Electron 桌面应用
# 后端地址：http://129.211.218.135
# 
# 特点：
#   - 仅打包 Electron + 前端，不包含后端
#   - 直接连接公网后端服务
#   - 支持在 Linux 服务器上构建 Windows 安装包
# 
# 使用方法：
#   chmod +x scripts/build-electron-production.sh
#   ./scripts/build-electron-production.sh
#
# 作者：提猫直播助手团队
# 日期：2025-11-13
################################################################################

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# 打印分隔线
print_separator() {
    echo "========================================================================"
}

# 打印标题
print_title() {
    print_separator
    echo -e "${GREEN}$1${NC}"
    print_separator
}

################################################################################
# 配置区域
################################################################################

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ELECTRON_DIR="${PROJECT_ROOT}/electron"
RENDERER_DIR="${ELECTRON_DIR}/renderer"
BUILD_DIR="${PROJECT_ROOT}/dist"

# 生产环境 API 配置（连接到公网后端）
PRODUCTION_API_URL="http://129.211.218.135"

# Electron 构建配置
BUILD_CONFIG="${PROJECT_ROOT}/build-config.json"

# 构建目标平台（可选：win, mac, linux, all）
BUILD_TARGET="${BUILD_TARGET:-win}"

# 应用版本（从 package.json 读取）
APP_VERSION=$(node -p "require('${PROJECT_ROOT}/package.json').version" 2>/dev/null || echo "1.0.0")

################################################################################
# 步骤 1：环境检查
################################################################################

print_title "步骤 1/6: 环境检查"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    log_error "Node.js 未安装！请先安装 Node.js"
    exit 1
fi
log_success "Node.js 版本: $(node -v)"

# 检查 npm
if ! command -v npm &> /dev/null; then
    log_error "npm 未安装！"
    exit 1
fi
log_success "npm 版本: $(npm -v)"

# 检查项目目录
if [ ! -d "$PROJECT_ROOT" ]; then
    log_error "项目目录不存在: $PROJECT_ROOT"
    exit 1
fi
log_success "项目目录: $PROJECT_ROOT"

# 检查 Electron 目录
if [ ! -d "$ELECTRON_DIR" ]; then
    log_error "Electron 目录不存在: $ELECTRON_DIR"
    exit 1
fi
log_success "Electron 目录: $ELECTRON_DIR"

# 检查前端目录
if [ ! -d "$RENDERER_DIR" ]; then
    log_error "前端目录不存在: $RENDERER_DIR"
    exit 1
fi
log_success "前端目录: $RENDERER_DIR"

################################################################################
# 步骤 2：清理旧构建
################################################################################

print_title "步骤 2/6: 清理旧构建"

log_info "清理 dist 目录..."
if [ -d "$BUILD_DIR" ]; then
    # 移除宝塔面板创建的 .user.ini 文件的不可变属性
    if [ -f "$BUILD_DIR/.user.ini" ]; then
        log_info "检测到宝塔面板配置文件，移除不可变属性..."
        chattr -i "$BUILD_DIR/.user.ini" 2>/dev/null || true
    fi
    
    rm -rf "$BUILD_DIR"
    log_success "已删除旧的 dist 目录"
fi

log_info "清理前端构建目录..."
if [ -d "$RENDERER_DIR/dist" ]; then
    rm -rf "$RENDERER_DIR/dist"
    log_success "已删除旧的前端构建"
fi

log_success "清理完成"

################################################################################
# 步骤 3：配置生产环境
################################################################################

print_title "步骤 3/6: 配置生产环境"

log_info "创建前端环境配置文件..."

# 创建 .env.production 文件
cat > "$RENDERER_DIR/.env.production" << EOF
# 生产环境配置 - 连接到公网后端
# 生成时间: $(date '+%Y-%m-%d %H:%M:%S')
# 构建版本: ${APP_VERSION}

# ===================================================================
# API 基础 URL（公网地址，通过 Nginx 反向代理）
# ===================================================================
VITE_FASTAPI_URL=${PRODUCTION_API_URL}
VITE_STREAMCAP_URL=${PRODUCTION_API_URL}
VITE_DOUYIN_URL=${PRODUCTION_API_URL}

# ===================================================================
# 环境标识
# ===================================================================
VITE_APP_ENV=production
NODE_ENV=production

# ===================================================================
# 构建信息
# ===================================================================
VITE_BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VITE_BUILD_VERSION=${APP_VERSION}
VITE_BUILD_PLATFORM=${BUILD_TARGET}

# ===================================================================
# 功能开关
# ===================================================================
VITE_DEMO_MODE=false
VITE_ENABLE_DEVTOOLS=false
EOF

log_success "环境配置文件已创建: $RENDERER_DIR/.env.production"
echo ""
log_info "配置摘要:"
log_info "  后端 API 地址: ${PRODUCTION_API_URL}"
log_info "  应用版本: ${APP_VERSION}"
log_info "  构建目标: ${BUILD_TARGET}"
log_info "  构建时间: $(date '+%Y-%m-%d %H:%M:%S')"

################################################################################
# 步骤 4：安装依赖
################################################################################

print_title "步骤 4/6: 安装依赖"

# 设置 npm 镜像（国内加速）
log_info "配置 npm 镜像源..."
export ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
export ELECTRON_BUILDER_BINARIES_MIRROR="https://npmmirror.com/mirrors/electron-builder-binaries/"
export SASS_BINARY_SITE="https://npmmirror.com/mirrors/node-sass"

# 检查 Electron 是否已安装
log_info "检查 Electron 依赖..."
cd "$ELECTRON_DIR"
if [ -d "node_modules/electron" ]; then
    log_success "Electron 已安装，跳过重新安装"
else
    log_info "安装 Electron 依赖..."
    npm install --legacy-peer-deps || {
        log_warning "Electron 安装失败，尝试使用已缓存的版本..."
    }
fi

# 安装前端依赖
log_info "安装前端依赖..."
cd "$RENDERER_DIR"
if npm install --legacy-peer-deps; then
    log_success "前端依赖已安装"
else
    log_error "前端依赖安装失败"
    exit 1
fi

################################################################################
# 步骤 5：构建前端
################################################################################

print_title "步骤 5/6: 构建前端"

cd "$RENDERER_DIR"

log_info "开始构建前端（使用生产环境配置）..."
log_info "构建命令: npm run build"

# 设置环境变量并构建
export NODE_ENV=production

if npm run build; then
    log_success "前端构建成功"
else
    log_error "前端构建失败"
    exit 1
fi

# 检查构建产物
if [ ! -d "$RENDERER_DIR/dist" ]; then
    log_error "前端构建产物不存在: $RENDERER_DIR/dist"
    exit 1
fi

# 验证关键文件
if [ ! -f "$RENDERER_DIR/dist/index.html" ]; then
    log_error "index.html 不存在！"
    exit 1
fi
log_success "index.html 验证通过"

# 显示构建产物信息
log_info ""
log_info "前端构建产物:"
log_info "  位置: $RENDERER_DIR/dist"
log_info "  大小: $(du -sh "$RENDERER_DIR/dist" | cut -f1)"
log_info "  文件数: $(find "$RENDERER_DIR/dist" -type f | wc -l)"

################################################################################
# 步骤 6：打包 Electron 应用
################################################################################

print_title "步骤 6/6: 打包 Electron 应用"

cd "$PROJECT_ROOT"

log_info "打包目标平台: $BUILD_TARGET"
log_info "构建配置文件: $BUILD_CONFIG"

# 设置 electron-builder 环境变量（国内镜像加速）
export ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
export ELECTRON_BUILDER_BINARIES_MIRROR=https://npmmirror.com/mirrors/electron-builder-binaries/

# 检查是否安装了 electron-builder
cd "$ELECTRON_DIR"
if ! npm list electron-builder &> /dev/null; then
    log_warning "electron-builder 未安装，正在安装..."
    npm install --save-dev electron-builder
fi

log_info "开始打包 Electron 应用..."

# 根据目标平台打包
case "$BUILD_TARGET" in
    win)
        log_info "打包 Windows 版本（x64）..."
        log_info "在 Linux 服务器上构建 Windows 安装包..."
        
        # 安装 wine 依赖（如果需要）
        if ! command -v wine &> /dev/null; then
            log_warning "wine 未安装，Windows 安装包可能无法正确签名"
            log_info "继续构建（跳过签名）..."
        fi
        
        npx electron-builder --win --x64 --config "$BUILD_CONFIG" || {
            log_error "Windows 打包失败"
            exit 1
        }
        ;;
    mac)
        log_info "打包 macOS 版本..."
        npx electron-builder --mac --config "$BUILD_CONFIG" || {
            log_error "macOS 打包失败"
            exit 1
        }
        ;;
    linux)
        log_info "打包 Linux 版本..."
        npx electron-builder --linux --config "$BUILD_CONFIG" || {
            log_error "Linux 打包失败"
            exit 1
        }
        ;;
    all)
        log_info "打包所有平台..."
        npx electron-builder --win --mac --linux --config "$BUILD_CONFIG" || {
            log_error "多平台打包失败"
            exit 1
        }
        ;;
    *)
        log_error "未知的打包目标: $BUILD_TARGET"
        log_info "支持的目标: win, mac, linux, all"
        exit 1
        ;;
esac

log_success "Electron 应用打包成功"

################################################################################
# 验证和总结
################################################################################

print_title "打包结果验证"

cd "$PROJECT_ROOT"

# 检查 dist 目录
if [ ! -d "$BUILD_DIR" ]; then
    log_error "打包产物目录不存在: $BUILD_DIR"
    exit 1
fi

log_info "打包产物目录: $BUILD_DIR"
echo ""

# 列出打包产物
log_info "生成的文件:"
find "$BUILD_DIR" -type f \( -name "*.exe" -o -name "*.dmg" -o -name "*.AppImage" -o -name "*.deb" \) -exec ls -lh {} \; || {
    log_warning "未找到标准安装包文件"
    log_info "目录内容:"
    ls -lh "$BUILD_DIR"
}

# 计算总大小
TOTAL_SIZE=$(du -sh "$BUILD_DIR" | cut -f1)

################################################################################
# 完成
################################################################################

echo ""
print_separator
log_success "🎉 打包完成！"
print_separator

echo ""
log_info "📦 打包摘要:"
log_info "  应用名称: 提猫直播助手"
log_info "  应用版本: ${APP_VERSION}"
log_info "  后端地址: ${PRODUCTION_API_URL}"
log_info "  打包目标: ${BUILD_TARGET}"
log_info "  产物目录: ${BUILD_DIR}"
log_info "  总大小: ${TOTAL_SIZE}"

echo ""
log_info "🚀 下一步操作:"
log_info "  1. 下载安装包到 Windows 电脑"
log_info "  2. 双击运行安装包"
log_info "  3. 验证应用能否连接到后端 (${PRODUCTION_API_URL})"
log_info "  4. 测试所有功能是否正常"

echo ""
log_info "📥 下载命令（在本地 Windows 电脑执行）:"
log_info "  scp user@129.211.218.135:${BUILD_DIR}/TalkingCat-*.exe ."

echo ""
log_info "🔍 验证清单:"
log_info "  ☐ 应用可以正常启动"
log_info "  ☐ 能连接到公网后端 (${PRODUCTION_API_URL})"
log_info "  ☐ 健康检查通过"
log_info "  ☐ 用户登录功能正常"
log_info "  ☐ 数据加载正常"
log_info "  ☐ 关闭应用时请求被正确清理"

echo ""
print_separator
log_success "✅ 所有步骤完成！"
print_separator

exit 0
