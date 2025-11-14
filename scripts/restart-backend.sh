#!/bin/bash
# ============================================
# 提猫直播助手 - 后端重启脚本
# 重启后端服务并显示日志
# ============================================

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 重启后端服务...${NC}"

cd /www/wwwroot

# 重启服务
pm2 restart timao-backend

echo -e "${GREEN}✅ 服务已重启${NC}"
echo ""
echo -e "${BLUE}📋 显示最近20行日志：${NC}"
echo ""

# 等待服务启动
sleep 2

# 显示日志
pm2 logs timao-backend --lines 20 --nostream

echo ""
echo -e "${GREEN}✅ 完成！${NC}"
echo -e "${BLUE}提示: 使用 'pm2 logs timao-backend' 查看实时日志${NC}"

