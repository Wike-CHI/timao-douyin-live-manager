#!/bin/bash
# ============================================
# 代码传输器 (Code Uploader)
# ============================================
# 职责：将项目代码上传到云服务器
# 依赖：环境准备器已执行
# 输出：代码上传报告
# ============================================

set -e

echo "📦 开始上传代码到云服务器..."

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 配置文件
UPLOAD_CONFIG="deploy/upload_config.env"
UPLOAD_REPORT="deploy/upload_report.txt"

# 检查配置文件
check_config() {
    echo -e "\n${YELLOW}[1/4] 检查上传配置...${NC}"
    
    if [ ! -f "$UPLOAD_CONFIG" ]; then
        echo -e "${RED}❌ 配置文件不存在: $UPLOAD_CONFIG${NC}"
        echo "正在创建配置模板..."
        create_config_template
        echo -e "${YELLOW}⚠️  请编辑 $UPLOAD_CONFIG 填写服务器信息${NC}"
        exit 1
    fi
    
    # 加载配置
    source "$UPLOAD_CONFIG"
    
    # 验证必需配置
    if [ -z "$SERVER_HOST" ] || [ -z "$SERVER_USER" ] || [ -z "$SERVER_PATH" ]; then
        echo -e "${RED}❌ 配置不完整，请检查 $UPLOAD_CONFIG${NC}"
        exit 1
    fi
    
    echo "✅ 配置文件检查通过"
    echo "服务器: $SERVER_USER@$SERVER_HOST:$SERVER_PATH"
}

# 创建配置模板
create_config_template() {
    cat > "$UPLOAD_CONFIG" << 'EOF'
# ============================================
# 代码上传配置
# ============================================

# 服务器配置
SERVER_HOST="your-server-ip"        # 云服务器IP或域名
SERVER_USER="root"                   # SSH 用户名
SERVER_PORT="22"                     # SSH 端口
SERVER_PATH="/opt/timao-douyin"      # 项目部署路径

# SSH 密钥配置（可选，如果使用密钥登录）
SSH_KEY_PATH="~/.ssh/id_rsa"        # SSH 私钥路径

# 传输方式
TRANSFER_METHOD="rsync"              # rsync 或 scp

# 排除文件（不上传）
EXCLUDE_PATTERNS=(
    ".git"
    ".venv"
    "node_modules"
    "__pycache__"
    "*.pyc"
    ".DS_Store"
    ".env"
    "*.log"
    "data"
    "deploy/environment_check_report.txt"
    "deploy/upload_report.txt"
)
EOF
    echo "✅ 配置模板已创建: $UPLOAD_CONFIG"
}

# 检查连接
check_connection() {
    echo -e "\n${YELLOW}[2/4] 检查服务器连接...${NC}"
    
    # 构建 SSH 命令
    SSH_CMD="ssh"
    if [ -n "$SSH_KEY_PATH" ]; then
        SSH_CMD="$SSH_CMD -i $SSH_KEY_PATH"
    fi
    SSH_CMD="$SSH_CMD -p ${SERVER_PORT:-22}"
    
    # 测试连接
    if $SSH_CMD "$SERVER_USER@$SERVER_HOST" "echo 'Connection test successful'" &> /dev/null; then
        echo "✅ 服务器连接成功"
    else
        echo -e "${RED}❌ 无法连接到服务器${NC}"
        echo "请检查："
        echo "  1. 服务器地址和端口是否正确"
        echo "  2. SSH 密钥是否配置正确"
        echo "  3. 服务器防火墙是否允许 SSH 连接"
        exit 1
    fi
}

# 准备服务器目录
prepare_server_directory() {
    echo -e "\n${YELLOW}[3/4] 准备服务器目录...${NC}"
    
    # 创建项目目录
    $SSH_CMD "$SERVER_USER@$SERVER_HOST" "mkdir -p $SERVER_PATH"
    echo "✅ 服务器目录已创建: $SERVER_PATH"
}

# 上传代码
upload_code() {
    echo -e "\n${YELLOW}[4/4] 上传代码...${NC}"
    echo "$(date)" > "$UPLOAD_REPORT"
    
    # 构建排除参数
    EXCLUDE_ARGS=""
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude='$pattern'"
    done
    
    # 使用 rsync 上传
    if [ "$TRANSFER_METHOD" = "rsync" ]; then
        echo "使用 rsync 上传代码..."
        
        RSYNC_CMD="rsync -avz --progress"
        
        # 添加 SSH 参数
        if [ -n "$SSH_KEY_PATH" ]; then
            RSYNC_CMD="$RSYNC_CMD -e 'ssh -i $SSH_KEY_PATH -p ${SERVER_PORT:-22}'"
        else
            RSYNC_CMD="$RSYNC_CMD -e 'ssh -p ${SERVER_PORT:-22}'"
        fi
        
        # 添加排除参数
        RSYNC_CMD="$RSYNC_CMD $EXCLUDE_ARGS"
        
        # 上传
        eval "$RSYNC_CMD ./ $SERVER_USER@$SERVER_HOST:$SERVER_PATH/" 2>&1 | tee -a "$UPLOAD_REPORT"
        
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            echo -e "${GREEN}✅ 代码上传成功${NC}"
            echo "上传成功" >> "$UPLOAD_REPORT"
        else
            echo -e "${RED}❌ 代码上传失败${NC}"
            exit 1
        fi
    
    # 使用 scp 上传
    elif [ "$TRANSFER_METHOD" = "scp" ]; then
        echo "使用 scp 上传代码..."
        
        # 打包代码
        echo "正在打包代码..."
        TAR_FILE="timao-douyin-$(date +%Y%m%d_%H%M%S).tar.gz"
        
        tar czf "$TAR_FILE" \
            --exclude='.git' \
            --exclude='.venv' \
            --exclude='node_modules' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.DS_Store' \
            --exclude='.env' \
            --exclude='*.log' \
            --exclude='data' \
            . 2>&1 | tee -a "$UPLOAD_REPORT"
        
        echo "✅ 打包完成: $TAR_FILE"
        
        # 上传
        SCP_CMD="scp -P ${SERVER_PORT:-22}"
        if [ -n "$SSH_KEY_PATH" ]; then
            SCP_CMD="$SCP_CMD -i $SSH_KEY_PATH"
        fi
        
        $SCP_CMD "$TAR_FILE" "$SERVER_USER@$SERVER_HOST:$SERVER_PATH/" 2>&1 | tee -a "$UPLOAD_REPORT"
        
        if [ $? -eq 0 ]; then
            echo "✅ 代码包上传成功"
            
            # 解压
            $SSH_CMD "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH && tar xzf $TAR_FILE && rm $TAR_FILE"
            echo "✅ 代码解压完成"
            
            # 删除本地打包文件
            rm "$TAR_FILE"
        else
            echo -e "${RED}❌ 代码上传失败${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ 不支持的传输方式: $TRANSFER_METHOD${NC}"
        exit 1
    fi
}

# 验证上传
verify_upload() {
    echo -e "\n${YELLOW}验证上传结果...${NC}"
    
    # 检查关键文件
    REQUIRED_FILES=(
        "server"
        "admin-dashboard"
        "docker-compose.full.yml"
        "DOCKER_FULL.md"
    )
    
    ALL_OK=true
    for file in "${REQUIRED_FILES[@]}"; do
        if $SSH_CMD "$SERVER_USER@$SERVER_HOST" "[ -e $SERVER_PATH/$file ]"; then
            echo "✅ $file"
        else
            echo -e "${RED}❌ $file 未找到${NC}"
            ALL_OK=false
        fi
    done
    
    if [ "$ALL_OK" = true ]; then
        echo -e "${GREEN}✅ 所有关键文件已上传${NC}"
    else
        echo -e "${RED}❌ 部分文件上传失败${NC}"
        exit 1
    fi
}

# 主执行流程
main() {
    echo "======================================"
    echo "    代码传输器 (Code Uploader)"
    echo "======================================"
    echo ""
    
    check_config
    check_connection
    prepare_server_directory
    upload_code
    verify_upload
    
    echo ""
    echo "======================================"
    echo -e "${GREEN}✅ 代码上传完成${NC}"
    echo "======================================"
    echo "服务器路径: $SERVER_PATH"
    echo "上传报告: $UPLOAD_REPORT"
    echo ""
    echo "下一步: 运行配置管理器"
    echo "  ./deploy/3_configure_environment.sh"
}

main

