#!/bin/bash
# ============================================
# 提猫直播助手 - 前端构建和部署脚本
# 自动构建前端并部署到公网访问目录
# ============================================

set -e  # 遇到错误立即退出

# ==================== 配置 ====================
PROJECT_ROOT="/www/wwwroot/wwwroot/timao-douyin-live-manager"
FRONTEND_DIR="$PROJECT_ROOT/electron/renderer"
DEPLOY_DIR="/www/wwwroot/timao-app"
BACKUP_DIR="/www/wwwroot/timao-app-backups"
LOG_FILE="$PROJECT_ROOT/build-deploy.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==================== 函数 ====================

log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $@${NC}"
    log "INFO" "$@"
}

error() {
    echo -e "${RED}❌ $@${NC}"
    log "ERROR" "$@"
}

warning() {
    echo -e "${YELLOW}⚠️  $@${NC}"
    log "WARN" "$@"
}

info() {
    echo -e "${BLUE}ℹ️  $@${NC}"
    log "INFO" "$@"
}

# ==================== 主流程 ====================

echo ""
echo "================================================"
echo "  提猫直播助手 - 前端构建和部署"
echo "================================================"
echo ""

# 1. 检查项目目录
info "步骤 1/8: 检查项目目录..."
if [ ! -d "$FRONTEND_DIR" ]; then
    error "前端目录不存在: $FRONTEND_DIR"
    exit 1
fi
cd "$FRONTEND_DIR"
success "前端目录检查通过: $FRONTEND_DIR"

# 2. 检查环境变量配置
info "步骤 2/8: 检查环境变量配置..."
if [ ! -f ".env.production" ]; then
    error ".env.production 文件不存在"
    exit 1
fi

# 显示配置信息
echo ""
echo "当前生产环境配置:"
grep "^VITE_" .env.production || true
echo ""

# 3. 检查 Node.js 和 npm
info "步骤 3/8: 检查 Node.js 环境..."
if ! command -v node &> /dev/null; then
    error "Node.js 未安装"
    exit 1
fi
if ! command -v npm &> /dev/null; then
    error "npm 未安装"
    exit 1
fi
success "Node.js 版本: $(node -v)"
success "npm 版本: $(npm -v)"

# 4. 安装依赖
info "步骤 4/8: 检查并安装依赖..."
if [ ! -d "node_modules" ]; then
    warning "node_modules 不存在，开始安装依赖..."
    npm install
    success "依赖安装完成"
else
    info "依赖已存在，跳过安装（如需重新安装，请手动删除 node_modules）"
fi

# 5. 清理旧的构建产物
info "步骤 5/8: 清理旧的构建产物..."
if [ -d "dist" ]; then
    rm -rf dist
    success "旧构建产物已清理"
fi

# 6. 构建前端
info "步骤 6/8: 开始构建前端（生产模式）..."
echo ""
echo "构建命令: npm run build"
echo ""

# 使用生产环境配置构建
if npm run build; then
    success "前端构建成功！"
else
    error "前端构建失败"
    exit 1
fi

# 检查构建产物
if [ ! -d "dist" ] || [ ! -f "dist/index.html" ]; then
    error "构建产物不完整，缺少 dist 目录或 index.html"
    exit 1
fi
success "构建产物验证通过"

# 7. 备份旧版本
info "步骤 7/8: 备份旧版本..."
mkdir -p "$BACKUP_DIR"

if [ -d "$DEPLOY_DIR" ] && [ "$(ls -A $DEPLOY_DIR)" ]; then
    BACKUP_NAME="timao-app-backup-$(date +%Y%m%d_%H%M%S)"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    
    cp -r "$DEPLOY_DIR" "$BACKUP_PATH"
    success "旧版本已备份到: $BACKUP_PATH"
    
    # 只保留最近5个备份
    BACKUP_COUNT=$(ls -1 "$BACKUP_DIR" | wc -l)
    if [ "$BACKUP_COUNT" -gt 5 ]; then
        warning "备份数量超过5个，删除最旧的备份..."
        ls -1t "$BACKUP_DIR" | tail -n +6 | xargs -I {} rm -rf "$BACKUP_DIR/{}"
        success "已清理旧备份，保留最近5个"
    fi
else
    info "部署目录为空或不存在，跳过备份"
fi

# 8. 部署到公网目录
info "步骤 8/8: 部署到公网目录..."

# 创建部署目录
mkdir -p "$DEPLOY_DIR"

# 清空目录
rm -rf "$DEPLOY_DIR"/*

# 复制构建产物
cp -r dist/* "$DEPLOY_DIR/"

# 验证部署
if [ -f "$DEPLOY_DIR/index.html" ]; then
    success "部署成功！"
else
    error "部署失败，index.html 不存在"
    exit 1
fi

# 设置权限
chmod -R 755 "$DEPLOY_DIR"
success "文件权限已设置"

# ==================== 部署总结 ====================

echo ""
echo "================================================"
echo "  🎉 部署完成"
echo "================================================"
echo ""
echo "部署信息："
echo "  📁 部署目录: $DEPLOY_DIR"
echo "  📊 文件数量: $(find $DEPLOY_DIR -type f | wc -l)"
echo "  💾 总大小: $(du -sh $DEPLOY_DIR | cut -f1)"
echo ""
echo "访问地址："
echo "  🌐 公网访问: http://129.211.218.135/app/"
echo "  🔗 本地访问: http://127.0.0.1/app/"
echo ""

# 检查 Nginx 配置
echo "Nginx 配置检查："
if nginx -t &> /dev/null; then
    success "Nginx 配置正确"
else
    warning "Nginx 配置可能有问题，请检查"
fi

# 显示访问说明
echo ""
echo "📝 注意事项："
echo "  1. 确保 Nginx 已配置 /app/ 路径指向 $DEPLOY_DIR"
echo "  2. 如需重新加载 Nginx: sudo nginx -s reload"
echo "  3. 备份位置: $BACKUP_DIR"
echo "  4. 日志文件: $LOG_FILE"
echo ""

# 显示最近的备份
if [ -d "$BACKUP_DIR" ] && [ "$(ls -A $BACKUP_DIR)" ]; then
    echo "最近的备份："
    ls -lt "$BACKUP_DIR" | head -6
fi

echo ""
success "部署脚本执行完成！"
echo ""

