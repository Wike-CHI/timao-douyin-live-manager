#!/bin/bash
# 自动切换为后端显示模式（仅生成配置，需手动应用到宝塔）
# 审查人：叶维哲

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}切换为后端显示模式${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查配置文件是否存在
CONFIG_FILE="$PROJECT_ROOT/nginx-config-backend-only.conf"

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}✗ 配置文件不存在: $CONFIG_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 找到配置文件: $CONFIG_FILE${NC}"
echo ""

# 检查后端服务
echo -e "${YELLOW}检查后端服务状态...${NC}"
if curl -s -f http://127.0.0.1:11111/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端服务运行正常${NC}"
else
    echo -e "${RED}✗ 后端服务未运行${NC}"
    echo -e "${YELLOW}  请先启动后端服务！${NC}"
    echo ""
    exit 1
fi
echo ""

# 显示配置文件内容
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}配置文件内容（需复制到宝塔面板）${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
cat "$CONFIG_FILE"
echo ""

# 使用说明
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}使用说明${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}请按以下步骤在宝塔面板中应用配置:${NC}"
echo ""
echo -e "1. 登录宝塔面板: ${BLUE}http://你的服务器IP:8888${NC}"
echo ""
echo -e "2. 网站 → 选择站点 ${BLUE}129.211.218.135${NC} → 设置"
echo ""
echo -e "3. 配置文件 → 找到 ${YELLOW}server { ... }${NC} 块"
echo ""
echo -e "4. 复制上面的配置内容，替换整个 server 块"
echo ""
echo -e "5. 保存 → 重载配置"
echo ""
echo -e "6. 访问 ${BLUE}http://129.211.218.135${NC} 验证"
echo ""

# 复制到剪贴板（如果可能）
if command -v xclip &> /dev/null; then
    cat "$CONFIG_FILE" | xclip -selection clipboard
    echo -e "${GREEN}✓ 配置已复制到剪贴板${NC}"
    echo ""
elif command -v pbcopy &> /dev/null; then
    cat "$CONFIG_FILE" | pbcopy
    echo -e "${GREEN}✓ 配置已复制到剪贴板${NC}"
    echo ""
fi

# 提供直接查看配置的命令
echo -e "如需再次查看配置，运行:"
echo -e "${YELLOW}cat $CONFIG_FILE${NC}"
echo ""

# 提供详细文档链接
echo -e "详细操作步骤请查看:"
echo -e "${BLUE}$PROJECT_ROOT/docs/宝塔面板-切换后端显示.md${NC}"
echo ""

