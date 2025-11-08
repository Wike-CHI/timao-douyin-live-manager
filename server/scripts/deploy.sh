#!/bin/bash
# ============================================
# 提猫直播助手 - 快速部署脚本（Linux）
# 遵循：奥卡姆剃刀 + 希克定律
# ============================================

set -e  # 遇到错误立即退出

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 提猫直播助手 - 快速部署${NC}"
echo "=================================="

# 1. 检查 Python 环境
echo -e "\n${YELLOW}1. 检查 Python 环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ ${PYTHON_VERSION}${NC}"

# 2. 检查虚拟环境
echo -e "\n${YELLOW}2. 检查虚拟环境...${NC}"
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi
source .venv/bin/activate
echo -e "${GREEN}✅ 虚拟环境已激活${NC}"

# 3. 安装依赖
echo -e "\n${YELLOW}3. 安装依赖...${NC}"
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✅ 依赖安装完成${NC}"

# 4. 检查 .env 文件
echo -e "\n${YELLOW}4. 检查配置文件...${NC}"
if [ ! -f ".env" ]; then
    if [ -f "env.production.template" ]; then
        echo "复制生产环境配置模板..."
        cp env.production.template .env
        echo -e "${YELLOW}⚠️  请编辑 .env 文件，设置数据库密码和密钥${NC}"
    else
        echo -e "${RED}❌ .env 文件不存在，请先创建${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env 文件已存在${NC}"
fi

# 5. 验证配置
echo -e "\n${YELLOW}5. 验证配置...${NC}"
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

required = ['BACKEND_PORT', 'DB_TYPE', 'MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
missing = [k for k in required if not os.getenv(k)]
if missing:
    print(f'❌ 缺少必需配置: {missing}')
    exit(1)
print('✅ 配置验证通过')
"

# 6. 测试数据库连接
echo -e "\n${YELLOW}6. 测试数据库连接...${NC}"
python3 -c "
import sys
sys.path.insert(0, '.')
from server.app.database import engine
try:
    with engine.connect() as conn:
        print('✅ 数据库连接成功')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    exit(1)
" || exit 1

# 7. 创建 systemd 服务文件（可选）
echo -e "\n${YELLOW}7. 创建 systemd 服务...${NC}"
SERVICE_FILE="/etc/systemd/system/timao-backend.service"
CURRENT_DIR=$(pwd)
PYTHON_PATH="$CURRENT_DIR/.venv/bin/python"
MAIN_PATH="$CURRENT_DIR/server/app/main.py"

cat > /tmp/timao-backend.service << EOF
[Unit]
Description=提猫直播助手后端服务
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR
Environment="PATH=$CURRENT_DIR/.venv/bin"
ExecStart=$PYTHON_PATH -m uvicorn server.app.main:app --host 0.0.0.0 --port 11111
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "服务文件已创建: /tmp/timao-backend.service"
echo -e "${YELLOW}如需安装为系统服务，请执行:${NC}"
echo "  sudo cp /tmp/timao-backend.service $SERVICE_FILE"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable timao-backend"
echo "  sudo systemctl start timao-backend"

# 8. 完成
echo -e "\n${GREEN}=================================="
echo "✅ 部署准备完成！"
echo "==================================${NC}"
echo ""
echo "启动服务："
echo "  source .venv/bin/activate"
echo "  python server/app/main.py"
echo ""
echo "或使用 systemd："
echo "  sudo systemctl start timao-backend"
echo "  sudo systemctl status timao-backend"
echo ""

