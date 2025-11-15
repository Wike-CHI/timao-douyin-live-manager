#!/bin/bash
# 检查后端服务状态
# 审查人：叶维哲

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}提猫直播助手 - 后端服务状态检查${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查端口11111是否被占用
echo -e "${YELLOW}[1/4] 检查端口 11111...${NC}"
if netstat -tlnp 2>/dev/null | grep -q ':11111' || ss -tlnp 2>/dev/null | grep -q ':11111'; then
    echo -e "${GREEN}✓ 端口 11111 已被占用（服务可能在运行）${NC}"
    
    # 显示占用端口的进程
    if command -v netstat &> /dev/null; then
        netstat -tlnp 2>/dev/null | grep ':11111' || true
    else
        ss -tlnp 2>/dev/null | grep ':11111' || true
    fi
else
    echo -e "${RED}✗ 端口 11111 未被占用（服务未运行）${NC}"
fi
echo ""

# 检查健康检查接口
echo -e "${YELLOW}[2/4] 检查健康检查接口...${NC}"
if curl -s -f http://127.0.0.1:11111/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 健康检查通过${NC}"
    echo -e "   响应内容:"
    curl -s http://127.0.0.1:11111/health | python3 -m json.tool 2>/dev/null || curl -s http://127.0.0.1:11111/health
else
    echo -e "${RED}✗ 健康检查失败（后端服务未正常运行）${NC}"
fi
echo ""

# 检查根路径
echo -e "${YELLOW}[3/4] 检查根路径响应...${NC}"
if curl -s -f http://127.0.0.1:11111/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 根路径可访问${NC}"
    echo -e "   页面标题:"
    curl -s http://127.0.0.1:11111/ | grep -o '<title>.*</title>' || echo "   (无法提取标题)"
else
    echo -e "${RED}✗ 根路径无法访问${NC}"
fi
echo ""

# 检查API文档
echo -e "${YELLOW}[4/4] 检查API文档...${NC}"
if curl -s -f http://127.0.0.1:11111/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API文档可访问${NC}"
    echo -e "   URL: http://127.0.0.1:11111/docs"
else
    echo -e "${RED}✗ API文档无法访问${NC}"
fi
echo ""

# 总结
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}检查完成${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 提供建议
if curl -s -f http://127.0.0.1:11111/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端服务运行正常！${NC}"
    echo -e "${GREEN}  可以进行 Nginx 配置切换${NC}"
    echo ""
    echo -e "访问地址:"
    echo -e "  本地: ${BLUE}http://127.0.0.1:11111${NC}"
    echo -e "  公网: ${BLUE}http://129.211.218.135${NC} (配置 Nginx 后)"
else
    echo -e "${RED}✗ 后端服务未运行或异常${NC}"
    echo ""
    echo -e "启动建议:"
    echo -e "  1. 进入项目目录:"
    echo -e "     ${YELLOW}cd /www/wwwroot/wwwroot/timao-douyin-live-manager${NC}"
    echo -e ""
    echo -e "  2. 启动后端服务:"
    echo -e "     ${YELLOW}python3 -m server.app.main${NC}"
    echo -e ""
    echo -e "  3. 或使用 PM2 启动:"
    echo -e "     ${YELLOW}pm2 start ecosystem.config.js${NC}"
fi

echo ""

