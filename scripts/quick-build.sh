#!/bin/bash

################################################################################
# 快速构建脚本 - 跳过依赖安装
# 
# 适用场景：依赖已安装，只需要重新构建
# 速度：比完整构建快3-5倍
################################################################################

set -e

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================================================"
echo -e "提猫直播助手 - 快速构建"
echo -e "========================================================================${NC}"
echo ""

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RENDERER_DIR="${PROJECT_ROOT}/electron/renderer"
PRODUCTION_API_URL="http://129.211.218.135"

# 创建环境配置
echo -e "${BLUE}[1/3]${NC} 配置环境..."
cat > "$RENDERER_DIR/.env.production" << EOF
VITE_FASTAPI_URL=${PRODUCTION_API_URL}
VITE_STREAMCAP_URL=${PRODUCTION_API_URL}
VITE_DOUYIN_URL=${PRODUCTION_API_URL}
VITE_APP_ENV=production
VITE_BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VITE_BUILD_VERSION=1.0.0
EOF
echo -e "${GREEN}✓${NC} 环境配置完成"
echo ""

# 构建前端
echo -e "${BLUE}[2/3]${NC} 构建前端..."
cd "$RENDERER_DIR"
npm run build
echo -e "${GREEN}✓${NC} 前端构建完成"
echo ""

# 打包Electron
echo -e "${BLUE}[3/3]${NC} 打包Electron..."
cd "$PROJECT_ROOT"
export ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
export ELECTRON_BUILDER_BINARIES_MIRROR=https://npmmirror.com/mirrors/electron-builder-binaries/
npm run build:win64
echo -e "${GREEN}✓${NC} Electron打包完成"
echo ""

echo -e "${GREEN}========================================================================" echo -e "✅ 快速构建完成！"
echo -e "========================================================================${NC}"
echo ""
echo "📦 安装包位置: dist/"
ls -lh dist/*.exe 2>/dev/null || echo "   查看 dist/ 目录获取安装包"
echo ""

