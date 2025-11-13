#!/bin/bash

################################################################################
# 前端构建和部署脚本
# 
# 功能：构建前端并自动部署到 Nginx 服务目录
# 
# 使用方法：
#   chmod +x scripts/build-and-deploy-frontend.sh
#   ./scripts/build-and-deploy-frontend.sh
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
print_title() { echo -e "${GREEN}========================================================================${NC}"; echo -e "${GREEN}$1${NC}"; echo -e "${GREEN}========================================================================${NC}"; }

################################################################################
# 配置区域
################################################################################

# 项目目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RENDERER_DIR="${PROJECT_ROOT}/electron/renderer"
DEPLOY_DIR="/www/wwwroot/timao-app"

# 后端 API 地址
BACKEND_URL="http://129.211.218.135"

################################################################################
# 步骤 1：清理旧构建
################################################################################

print_title "步骤 1/4: 清理旧构建"

log_info "清理前端构建目录..."
if [ -d "$RENDERER_DIR/dist" ]; then
    rm -rf "$RENDERER_DIR/dist"
    log_success "已删除旧的前端构建"
fi

################################################################################
# 步骤 2：创建环境配置
################################################################################

print_title "步骤 2/4: 创建环境配置"

log_info "创建前端环境配置文件..."

cat > "$RENDERER_DIR/.env.production" << EOF
# 生产环境配置 - 连接到公网后端
# 生成时间: $(date)

# API基础URL（公网地址）
VITE_FASTAPI_URL=${BACKEND_URL}
VITE_STREAMCAP_URL=${BACKEND_URL}
VITE_DOUYIN_URL=${BACKEND_URL}

# 环境标识
VITE_APP_ENV=production

# 构建信息
VITE_BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VITE_BUILD_VERSION=1.0.0
EOF

log_success "环境配置已创建: $RENDERER_DIR/.env.production"
log_info "配置摘要:"
log_info "  后端 API 地址: ${BACKEND_URL}"
log_info "  构建时间: $(date '+%Y-%m-%d %H:%M:%S')"

################################################################################
# 步骤 3：构建前端
################################################################################

print_title "步骤 3/4: 构建前端"

cd "$RENDERER_DIR"

log_info "开始构建前端（使用生产环境配置）..."
log_info "构建命令: npm run build"

if npm run build; then
    log_success "前端构建成功"
else
    log_error "前端构建失败"
    exit 1
fi

# 检查构建产物
if [ ! -f "$RENDERER_DIR/dist/index.html" ]; then
    log_error "构建产物不存在: $RENDERER_DIR/dist/index.html"
    exit 1
fi

log_success "构建产物验证通过"

################################################################################
# 步骤 4：部署到 Nginx
################################################################################

print_title "步骤 4/4: 部署到 Nginx"

log_info "准备部署目录..."
mkdir -p "$DEPLOY_DIR"

# 备份旧版本
if [ -d "$DEPLOY_DIR" ] && [ "$(ls -A $DEPLOY_DIR 2>/dev/null)" ]; then
    BACKUP_DIR="${DEPLOY_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    log_info "备份旧版本到: $BACKUP_DIR"
    cp -r "$DEPLOY_DIR" "$BACKUP_DIR"
fi

# 移除 .user.ini 的不可变属性（宝塔面板）
if [ -f "$DEPLOY_DIR/.user.ini" ]; then
    log_info "检测到宝塔面板配置文件，移除不可变属性..."
    chattr -i "$DEPLOY_DIR/.user.ini" 2>/dev/null || true
fi

# 清理旧文件
log_info "清理旧文件..."
rm -rf "$DEPLOY_DIR"/*

# 复制新文件
log_info "复制前端文件到部署目录..."
cp -r "$RENDERER_DIR/dist"/* "$DEPLOY_DIR/"

# 设置权限
log_info "设置文件权限..."
chmod -R 755 "$DEPLOY_DIR"

# 验证部署
log_info "验证部署..."
if [ -f "$DEPLOY_DIR/index.html" ]; then
    log_success "部署成功！"
else
    log_error "部署失败：index.html 不存在"
    exit 1
fi

# 显示文件列表
log_info "部署的文件："
ls -lh "$DEPLOY_DIR/" | grep -E "index\.html|assets"

################################################################################
# 完成
################################################################################

print_separator
log_success "🎉 前端构建和部署完成！"
print_separator
log_info "部署位置: $DEPLOY_DIR"
log_info "访问地址: $BACKEND_URL"
log_info "建议："
log_info "  1. 在浏览器中访问 $BACKEND_URL"
log_info "  2. 硬刷新（Ctrl+F5 或 Cmd+Shift+R）清除缓存"
log_info "  3. 检查控制台是否有错误"
print_separator

exit 0

