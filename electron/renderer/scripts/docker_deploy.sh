#!/bin/bash
# ============================================
# 前端 Docker 快速部署脚本
# 遵循：奥卡姆剃刀 + 希克定律
# ============================================

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🐳 提猫直播助手前端 - Docker 快速部署${NC}"
echo "=================================="

# 1. 检查 Docker
echo -e "\n${YELLOW}1. 检查 Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker $(docker --version)${NC}"

# 2. 检查 .env 文件
echo -e "\n${YELLOW}2. 检查配置文件...${NC}"
if [ ! -f ".env" ]; then
    if [ -f "env.production.template" ]; then
        echo "复制配置模板..."
        cp env.production.template .env
        echo -e "${YELLOW}⚠️  请编辑 .env 文件，设置后端地址（BACKEND_URL）${NC}"
        echo "按 Enter 继续，或 Ctrl+C 取消..."
        read
    else
        echo -e "${RED}❌ .env 文件不存在，请先创建${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env 文件已存在${NC}"
fi

# 3. 加载环境变量
source .env 2>/dev/null || true
BACKEND_URL=${BACKEND_URL:-http://backend:11111}
FRONTEND_PORT=${FRONTEND_PORT:-80}

echo -e "\n${YELLOW}配置信息:${NC}"
echo "  后端地址: $BACKEND_URL"
echo "  前端端口: $FRONTEND_PORT"

# 4. 构建镜像
echo -e "\n${YELLOW}3. 构建 Docker 镜像...${NC}"
echo "这可能需要几分钟（安装依赖和构建）..."
docker build \
    --build-arg VITE_FASTAPI_URL=$BACKEND_URL \
    --build-arg VITE_STREAMCAP_URL=$BACKEND_URL \
    --build-arg VITE_DOUYIN_URL=$BACKEND_URL \
    -t timao-frontend:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 镜像构建成功${NC}"
else
    echo -e "${RED}❌ 镜像构建失败${NC}"
    exit 1
fi

# 5. 启动服务
echo -e "\n${YELLOW}4. 启动服务...${NC}"
BACKEND_URL=$BACKEND_URL FRONTEND_PORT=$FRONTEND_PORT docker-compose up -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 服务已启动${NC}"
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    exit 1
fi

# 6. 等待服务就绪
echo -e "\n${YELLOW}5. 等待服务就绪...${NC}"
sleep 5

# 7. 检查服务状态
echo -e "\n${YELLOW}6. 检查服务状态...${NC}"
docker-compose ps

# 8. 健康检查
echo -e "\n${YELLOW}7. 健康检查...${NC}"
sleep 5
if curl -f "http://localhost:${FRONTEND_PORT}/health" &> /dev/null; then
    echo -e "${GREEN}✅ 服务健康检查通过${NC}"
else
    echo -e "${YELLOW}⚠️  健康检查失败，请查看日志: docker logs timao-frontend${NC}"
fi

# 完成
echo -e "\n${GREEN}=================================="
echo "✅ Docker 部署完成！"
echo "==================================${NC}"
echo ""
echo "前端访问地址: http://localhost:${FRONTEND_PORT}"
echo ""
echo "常用命令："
echo "  查看日志: docker logs -f timao-frontend"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo ""

