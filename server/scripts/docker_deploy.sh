#!/bin/bash
# ============================================
# Docker 快速部署脚本
# 遵循：奥卡姆剃刀 + 希克定律
# ============================================

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🐳 提猫直播助手 - Docker 快速部署${NC}"
echo "=================================="

# 1. 检查 Docker
echo -e "\n${YELLOW}1. 检查 Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    echo "请访问 https://docs.docker.com/get-docker/ 安装 Docker"
    exit 1
fi
echo -e "${GREEN}✅ Docker $(docker --version)${NC}"

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose 已安装${NC}"

# 2. 检查 .env 文件
echo -e "\n${YELLOW}2. 检查配置文件...${NC}"
if [ ! -f ".env" ]; then
    if [ -f "env.production.template" ]; then
        echo "复制配置模板..."
        cp env.production.template .env
        echo -e "${YELLOW}⚠️  请编辑 .env 文件，设置数据库密码和密钥${NC}"
        echo "按 Enter 继续，或 Ctrl+C 取消..."
        read
    else
        echo -e "${RED}❌ .env 文件不存在，请先创建${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env 文件已存在${NC}"
fi

# 3. 创建必要的目录
echo -e "\n${YELLOW}3. 创建目录...${NC}"
mkdir -p models logs records
echo -e "${GREEN}✅ 目录已创建${NC}"

# 4. 构建镜像（包含模型下载）
echo -e "\n${YELLOW}4. 构建 Docker 镜像...${NC}"
echo "这可能需要几分钟（下载模型文件）..."
docker build -t timao-backend:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 镜像构建成功${NC}"
else
    echo -e "${RED}❌ 镜像构建失败${NC}"
    exit 1
fi

# 5. 启动服务
echo -e "\n${YELLOW}5. 启动服务...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    docker compose up -d
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 服务已启动${NC}"
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    exit 1
fi

# 6. 等待服务就绪
echo -e "\n${YELLOW}6. 等待服务就绪...${NC}"
sleep 5

# 7. 检查服务状态
echo -e "\n${YELLOW}7. 检查服务状态...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    docker compose ps
fi

# 8. 健康检查
echo -e "\n${YELLOW}8. 健康检查...${NC}"
sleep 10
BACKEND_PORT=$(grep BACKEND_PORT .env | cut -d '=' -f2 || echo "11111")
if curl -f "http://localhost:${BACKEND_PORT}/health" &> /dev/null; then
    echo -e "${GREEN}✅ 服务健康检查通过${NC}"
else
    echo -e "${YELLOW}⚠️  健康检查失败，请查看日志: docker logs timao-backend${NC}"
fi

# 完成
echo -e "\n${GREEN}=================================="
echo "✅ Docker 部署完成！"
echo "==================================${NC}"
echo ""
echo "常用命令："
echo "  查看日志: docker logs -f timao-backend"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  查看状态: docker-compose ps"
echo ""

