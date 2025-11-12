#!/bin/bash
# ============================================
# 前后端完整 Docker 部署脚本
# 遵循：奥卡姆剃刀 + 希克定律
# ============================================

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🐳 提猫直播助手 - 完整 Docker 部署${NC}"
echo "=================================="

# 1. 检查 Docker
echo -e "\n${YELLOW}1. 检查 Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker $(docker --version)${NC}"

# 2. 检查后端配置
echo -e "\n${YELLOW}2. 检查后端配置...${NC}"
if [ ! -f "server/.env" ]; then
    if [ -f "server/env.production.template" ]; then
        echo "复制后端配置模板..."
        cp server/env.production.template server/.env
        echo -e "${YELLOW}⚠️  请编辑 server/.env 文件，设置数据库密码和密钥${NC}"
        echo "按 Enter 继续，或 Ctrl+C 取消..."
        read
    else
        echo -e "${RED}❌ server/.env 文件不存在，请先创建${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ server/.env 文件已存在${NC}"
fi

# 3. 创建必要目录
echo -e "\n${YELLOW}3. 创建目录...${NC}"
mkdir -p server/models server/logs server/records
echo -e "${GREEN}✅ 目录已创建${NC}"

# 4. 构建和启动服务
echo -e "\n${YELLOW}4. 构建和启动服务...${NC}"
echo "这可能需要几分钟（构建镜像和下载模型）..."
docker-compose -f docker-compose.full.yml up -d --build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 服务已启动${NC}"
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    exit 1
fi

# 5. 等待服务就绪
echo -e "\n${YELLOW}5. 等待服务就绪...${NC}"
echo "等待后端服务启动（可能需要1-2分钟）..."
sleep 30

# 6. 检查服务状态
echo -e "\n${YELLOW}6. 检查服务状态...${NC}"
docker-compose -f docker-compose.full.yml ps

# 7. 健康检查
echo -e "\n${YELLOW}7. 健康检查...${NC}"
sleep 10

# 后端健康检查
if curl -f "http://localhost:11111/health" &> /dev/null; then
    echo -e "${GREEN}✅ 后端健康检查通过${NC}"
else
    echo -e "${YELLOW}⚠️  后端健康检查失败，请查看日志: docker logs timao-backend${NC}"
fi

# 前端健康检查
if curl -f "http://localhost/health" &> /dev/null; then
    echo -e "${GREEN}✅ 前端健康检查通过${NC}"
else
    echo -e "${YELLOW}⚠️  前端健康检查失败，请查看日志: docker logs timao-frontend${NC}"
fi

# 完成
echo -e "\n${GREEN}=================================="
echo "✅ Docker 部署完成！"
echo "==================================${NC}"
echo ""
echo "访问地址："
echo "  前端: http://localhost"
echo "  后端: http://localhost:11111"
echo "  API文档: http://localhost:11111/docs"
echo ""
echo "常用命令："
echo "  查看日志: docker-compose -f docker-compose.full.yml logs -f"
echo "  停止服务: docker-compose -f docker-compose.full.yml down"
echo "  重启服务: docker-compose -f docker-compose.full.yml restart"
echo ""

