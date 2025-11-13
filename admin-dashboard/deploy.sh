#!/bin/bash

# 管理后台部署脚本
# 部署到公网IP: 129.211.218.135

set -e

echo "===================================="
echo "提猫直播助手 - 管理后台部署"
echo "===================================="
echo ""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未找到 Node.js，请先安装 Node.js${NC}"
    exit 1
fi

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}错误: 未找到 npm，请先安装 npm${NC}"
    exit 1
fi

echo -e "${GREEN}[1/4] 检查依赖...${NC}"
if [ ! -d "node_modules" ]; then
    echo "正在安装依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}依赖安装失败！${NC}"
        exit 1
    fi
    echo -e "${GREEN}依赖安装完成！${NC}"
else
    echo -e "${GREEN}依赖已存在${NC}"
fi
echo ""

echo -e "${GREEN}[2/4] 检查环境变量...${NC}"
if [ ! -f ".env.production" ]; then
    echo -e "${YELLOW}警告: 未找到 .env.production 文件，使用默认配置${NC}"
    echo "创建 .env.production 文件..."
    cat > .env.production << EOF
# 生产环境配置
VITE_FASTAPI_URL=http://129.211.218.135:10090
VITE_ADMIN_PORT=10065
EOF
    echo -e "${GREEN}.env.production 文件已创建${NC}"
else
    echo -e "${GREEN}环境变量文件已存在${NC}"
fi
echo ""

echo -e "${GREEN}[3/4] 构建生产版本...${NC}"
npm run build
if [ $? -ne 0 ]; then
    echo -e "${RED}构建失败！${NC}"
    exit 1
fi
echo -e "${GREEN}构建完成！${NC}"
echo ""

echo -e "${GREEN}[4/4] 检查构建产物...${NC}"
if [ ! -d "dist" ]; then
    echo -e "${RED}错误: dist 目录不存在！${NC}"
    exit 1
fi

# 检查关键文件
if [ ! -f "dist/index.html" ]; then
    echo -e "${RED}错误: dist/index.html 不存在！${NC}"
    exit 1
fi

echo -e "${GREEN}构建产物检查通过！${NC}"
echo ""

echo "===================================="
echo -e "${GREEN}部署准备完成！${NC}"
echo "===================================="
echo ""
echo "构建产物位于: $(pwd)/dist"
echo ""
echo "下一步操作："
echo "1. 如果使用 Nginx，请配置 Nginx 指向 dist 目录"
echo "2. 如果使用 PM2，请运行: pm2 start ecosystem.config.js"
echo "3. 访问地址: http://129.211.218.135/admin/"
echo ""
echo "详细部署说明请查看 DEPLOY.md"

