#!/bin/bash
# ============================================
# 配置管理器 (Config Manager)
# ============================================
# 职责：在云服务器上配置环境变量和数据库连接
# 依赖：代码传输器已执行
# 输出：配置完成报告
# ============================================

set -e

echo "⚙️  开始配置环境..."

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 配置文件
UPLOAD_CONFIG="deploy/upload_config.env"
CONFIG_TEMPLATE="deploy/production.env.template"
CONFIG_REPORT="deploy/configure_report.txt"

# 检查上传配置
check_upload_config() {
    echo -e "\n${YELLOW}[1/4] 检查服务器配置...${NC}"
    
    if [ ! -f "$UPLOAD_CONFIG" ]; then
        echo -e "${RED}❌ 未找到上传配置文件${NC}"
        echo "请先运行: ./deploy/2_upload_code.sh"
        exit 1
    fi
    
    source "$UPLOAD_CONFIG"
    echo "✅ 服务器配置已加载"
}

# 创建配置模板
create_config_template() {
    echo -e "\n${YELLOW}[2/4] 创建配置模板...${NC}"
    
    cat > "$CONFIG_TEMPLATE" << 'EOF'
# ============================================
# 生产环境配置模板
# ============================================
# 请根据实际情况修改以下配置

# 后端端口
BACKEND_PORT=11111

# 数据库配置
MYSQL_HOST=your-database-host          # 数据库地址
MYSQL_PORT=3306                        # 数据库端口
MYSQL_USER=timao                       # 数据库用户名
MYSQL_PASSWORD=your-password           # 数据库密码
MYSQL_DATABASE=timao                   # 数据库名称

# 安全配置
SECRET_KEY=change-this-in-production   # JWT密钥（生产环境必须改）
CORS_ORIGINS=*                         # CORS配置

# Redis配置（可选）
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_PASSWORD=

# AI服务配置（可选）
# GEMINI_API_KEY=your-gemini-api-key
# OPENAI_API_KEY=your-openai-api-key

# 日志配置
LOG_LEVEL=INFO
EOF
    
    echo "✅ 配置模板已创建: $CONFIG_TEMPLATE"
}

# 交互式配置
interactive_config() {
    echo -e "\n${YELLOW}[3/4] 交互式配置...${NC}"
    echo "请输入生产环境配置（留空使用默认值）:"
    echo ""
    
    # 后端端口
    read -p "后端端口 [11111]: " BACKEND_PORT
    BACKEND_PORT=${BACKEND_PORT:-11111}
    
    # 数据库配置
    echo ""
    echo "数据库配置:"
    read -p "  数据库地址 [localhost]: " MYSQL_HOST
    MYSQL_HOST=${MYSQL_HOST:-localhost}
    
    read -p "  数据库端口 [3306]: " MYSQL_PORT
    MYSQL_PORT=${MYSQL_PORT:-3306}
    
    read -p "  数据库用户名 [timao]: " MYSQL_USER
    MYSQL_USER=${MYSQL_USER:-timao}
    
    read -sp "  数据库密码: " MYSQL_PASSWORD
    echo ""
    
    read -p "  数据库名称 [timao]: " MYSQL_DATABASE
    MYSQL_DATABASE=${MYSQL_DATABASE:-timao}
    
    # 安全配置
    echo ""
    echo "安全配置:"
    read -sp "  JWT密钥（留空自动生成）: " SECRET_KEY
    echo ""
    if [ -z "$SECRET_KEY" ]; then
        SECRET_KEY=$(openssl rand -hex 32)
        echo "  ✅ 已自动生成密钥"
    fi
    
    # CORS配置
    read -p "  CORS源（多个用逗号分隔，* 表示全部）[*]: " CORS_ORIGINS
    CORS_ORIGINS=${CORS_ORIGINS:-*}
    
    # 日志级别
    echo ""
    read -p "日志级别 [INFO]: " LOG_LEVEL
    LOG_LEVEL=${LOG_LEVEL:-INFO}
    
    echo ""
    echo "✅ 配置信息已收集"
}

# 生成配置文件
generate_config() {
    echo -e "\n${YELLOW}[4/4] 生成配置文件...${NC}"
    
    # 生成 .env 文件内容
    ENV_CONTENT="# ============================================
# 生产环境配置
# 生成时间: $(date)
# ============================================

# 后端配置
BACKEND_PORT=$BACKEND_PORT

# 数据库配置
MYSQL_HOST=$MYSQL_HOST
MYSQL_PORT=$MYSQL_PORT
MYSQL_USER=$MYSQL_USER
MYSQL_PASSWORD=$MYSQL_PASSWORD
MYSQL_DATABASE=$MYSQL_DATABASE

# 安全配置
SECRET_KEY=$SECRET_KEY
CORS_ORIGINS=$CORS_ORIGINS

# 日志配置
LOG_LEVEL=$LOG_LEVEL
"
    
    # 保存到临时文件
    TEMP_ENV="deploy/temp_production.env"
    echo "$ENV_CONTENT" > "$TEMP_ENV"
    
    echo "✅ 配置文件已生成: $TEMP_ENV"
}

# 上传配置到服务器
upload_config() {
    echo -e "\n${YELLOW}上传配置到服务器...${NC}"
    
    # 构建 SSH 命令
    SSH_CMD="ssh"
    if [ -n "$SSH_KEY_PATH" ]; then
        SSH_CMD="$SSH_CMD -i $SSH_KEY_PATH"
    fi
    SSH_CMD="$SSH_CMD -p ${SERVER_PORT:-22}"
    
    # 构建 SCP 命令
    SCP_CMD="scp -P ${SERVER_PORT:-22}"
    if [ -n "$SSH_KEY_PATH" ]; then
        SCP_CMD="$SCP_CMD -i $SSH_KEY_PATH"
    fi
    
    # 上传配置文件
    $SCP_CMD "$TEMP_ENV" "$SERVER_USER@$SERVER_HOST:$SERVER_PATH/server/.env"
    
    if [ $? -eq 0 ]; then
        echo "✅ 配置文件已上传到服务器"
        
        # 验证配置文件
        $SSH_CMD "$SERVER_USER@$SERVER_HOST" "cat $SERVER_PATH/server/.env | head -5"
        
        # 删除临时文件
        rm "$TEMP_ENV"
    else
        echo -e "${RED}❌ 配置文件上传失败${NC}"
        exit 1
    fi
}

# 测试数据库连接
test_database_connection() {
    echo -e "\n${YELLOW}测试数据库连接...${NC}"
    
    # 在服务器上测试数据库连接
    TEST_SCRIPT="
import pymysql
import sys

try:
    connection = pymysql.connect(
        host='$MYSQL_HOST',
        port=$MYSQL_PORT,
        user='$MYSQL_USER',
        password='$MYSQL_PASSWORD',
        database='$MYSQL_DATABASE'
    )
    print('✅ 数据库连接成功')
    connection.close()
    sys.exit(0)
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    sys.exit(1)
"
    
    # 构建 SSH 命令
    SSH_CMD="ssh"
    if [ -n "$SSH_KEY_PATH" ]; then
        SSH_CMD="$SSH_CMD -i $SSH_KEY_PATH"
    fi
    SSH_CMD="$SSH_CMD -p ${SERVER_PORT:-22}"
    
    # 执行测试
    $SSH_CMD "$SERVER_USER@$SERVER_HOST" "python3 -c \"$TEST_SCRIPT\"" || {
        echo -e "${YELLOW}⚠️  数据库连接测试失败，请检查配置${NC}"
        echo "继续部署? (y/n)"
        read -r continue_deploy
        if [ "$continue_deploy" != "y" ]; then
            exit 1
        fi
    }
}

# 生成配置报告
generate_report() {
    echo -e "\n${YELLOW}生成配置报告...${NC}"
    
    cat > "$CONFIG_REPORT" << EOF
====================================
配置管理报告
====================================
生成时间: $(date)

服务器配置:
  地址: $SERVER_HOST
  路径: $SERVER_PATH

应用配置:
  后端端口: $BACKEND_PORT
  数据库地址: $MYSQL_HOST:$MYSQL_PORT
  数据库名称: $MYSQL_DATABASE
  日志级别: $LOG_LEVEL

配置文件位置:
  服务器: $SERVER_PATH/server/.env

状态: ✅ 配置完成
====================================
EOF
    
    echo "✅ 配置报告已生成: $CONFIG_REPORT"
}

# 主执行流程
main() {
    echo "======================================"
    echo "    配置管理器 (Config Manager)"
    echo "======================================"
    echo ""
    
    check_upload_config
    create_config_template
    interactive_config
    generate_config
    upload_config
    test_database_connection
    generate_report
    
    echo ""
    echo "======================================"
    echo -e "${GREEN}✅ 环境配置完成${NC}"
    echo "======================================"
    echo "配置报告: $CONFIG_REPORT"
    echo ""
    echo "下一步: 运行服务部署器"
    echo "  ./deploy/4_deploy_services.sh"
}

main

