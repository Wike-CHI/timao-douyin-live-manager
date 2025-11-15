#!/bin/bash
# 验证 SenseVoice + VAD 模型配置
# 审查人：叶维哲

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}SenseVoice + VAD 模型配置验证${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 获取项目根目录
PROJECT_ROOT="/www/wwwroot/wwwroot/timao-douyin-live-manager"
cd "$PROJECT_ROOT"

# 检查计数器
TOTAL_CHECKS=0
PASSED_CHECKS=0

# 检查函数
check_item() {
    local item_name="$1"
    local check_command="$2"
    local expected="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "${YELLOW}[$TOTAL_CHECKS] 检查: $item_name${NC}"
    
    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ 通过${NC} - $expected"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}   ❌ 失败${NC} - $expected"
        return 1
    fi
}

echo -e "${BLUE}=== 1. 模型文件检查 ===${NC}"
echo ""

# SenseVoice 模型
check_item "SenseVoice 模型目录" \
    "test -d server/models/models/iic/SenseVoiceSmall" \
    "目录应存在"

check_item "SenseVoice model.pt" \
    "test -f server/models/models/iic/SenseVoiceSmall/model.pt" \
    "文件应存在（~2.3GB）"

# VAD 模型
check_item "VAD 模型目录" \
    "test -d server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch" \
    "目录应存在"

check_item "VAD model.pt" \
    "test -f server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/model.pt" \
    "文件应存在（~140MB）"

echo ""
echo -e "${BLUE}=== 2. 模型文件大小检查 ===${NC}"
echo ""

# 检查 SenseVoice 模型大小
SENSEVOICE_SIZE=$(du -sh server/models/models/iic/SenseVoiceSmall 2>/dev/null | awk '{print $1}')
if [ -n "$SENSEVOICE_SIZE" ]; then
    echo -e "${GREEN}   ✅ SenseVoice 模型大小: $SENSEVOICE_SIZE${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}   ❌ 无法获取 SenseVoice 模型大小${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# 检查 VAD 模型大小
VAD_SIZE=$(du -sh server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch 2>/dev/null | awk '{print $1}')
if [ -n "$VAD_SIZE" ]; then
    echo -e "${GREEN}   ✅ VAD 模型大小: $VAD_SIZE${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}   ❌ 无法获取 VAD 模型大小${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""
echo -e "${BLUE}=== 3. PM2 配置检查 ===${NC}"
echo ""

# 检查 PM2 是否运行
if pm2 list 2>/dev/null | grep -q "timao-backend"; then
    echo -e "${GREEN}   ✅ PM2 进程运行中${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    
    # 检查进程状态
    PM2_STATUS=$(pm2 jlist 2>/dev/null | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
    if [ "$PM2_STATUS" = "online" ]; then
        echo -e "${GREEN}   ✅ 进程状态: online${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}   ❌ 进程状态: $PM2_STATUS${NC}"
    fi
else
    echo -e "${RED}   ❌ PM2 进程未运行${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 2))

echo ""
echo -e "${BLUE}=== 4. 环境变量检查 ===${NC}"
echo ""

# 检查环境变量（从 PM2）
if pm2 env 0 2>/dev/null | grep -q "SENSEVOICE_MODEL_PATH"; then
    SENSEVOICE_PATH=$(pm2 env 0 2>/dev/null | grep "SENSEVOICE_MODEL_PATH" | cut -d'=' -f2)
    echo -e "${GREEN}   ✅ SENSEVOICE_MODEL_PATH: $SENSEVOICE_PATH${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${YELLOW}   ⚠️  SENSEVOICE_MODEL_PATH 未设置（使用默认路径）${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

if pm2 env 0 2>/dev/null | grep -q "VAD_MODEL_PATH"; then
    VAD_PATH=$(pm2 env 0 2>/dev/null | grep "VAD_MODEL_PATH" | cut -d'=' -f2)
    echo -e "${GREEN}   ✅ VAD_MODEL_PATH: $VAD_PATH${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${YELLOW}   ⚠️  VAD_MODEL_PATH 未设置（使用默认路径）${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""
echo -e "${BLUE}=== 5. 系统资源检查 ===${NC}"
echo ""

# 内存检查
TOTAL_MEM=$(free -h | grep "Mem:" | awk '{print $2}')
AVAILABLE_MEM=$(free -h | grep "Mem:" | awk '{print $7}')
echo -e "${BLUE}   总内存: $TOTAL_MEM, 可用: $AVAILABLE_MEM${NC}"

# 检查可用内存是否足够（至少 3GB）
AVAILABLE_MB=$(free -m | grep "Mem:" | awk '{print $7}')
if [ "$AVAILABLE_MB" -gt 3000 ]; then
    echo -e "${GREEN}   ✅ 内存充足 (${AVAILABLE_MB}MB 可用)${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${YELLOW}   ⚠️  内存紧张 (${AVAILABLE_MB}MB 可用，建议至少 3GB)${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# 磁盘空间检查
DISK_USAGE=$(df -h "$PROJECT_ROOT" | tail -1 | awk '{print $5}' | sed 's/%//')
DISK_AVAIL=$(df -h "$PROJECT_ROOT" | tail -1 | awk '{print $4}')
echo -e "${BLUE}   磁盘使用率: ${DISK_USAGE}%, 可用: $DISK_AVAIL${NC}"

if [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${GREEN}   ✅ 磁盘空间充足${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${YELLOW}   ⚠️  磁盘空间紧张 (${DISK_USAGE}% 已使用)${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""
echo -e "${BLUE}=== 6. 模型加载状态检查 ===${NC}"
echo ""

# 检查 PM2 日志中的模型初始化信息
if pm2 logs timao-backend --nostream --lines 200 2>/dev/null | grep -q "✅ SenseVoice"; then
    echo -e "${GREEN}   ✅ 在日志中找到模型初始化成功标志${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    
    # 显示最近的模型相关日志
    echo -e "${BLUE}   最近的模型日志:${NC}"
    pm2 logs timao-backend --nostream --lines 50 2>/dev/null | grep -i "sensevoice\|vad" | tail -3 | sed 's/^/   /'
else
    echo -e "${YELLOW}   ⚠️  未在日志中找到模型初始化成功标志${NC}"
    echo -e "${YELLOW}   可能需要重启服务或等待模型加载完成${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""
echo -e "${BLUE}=== 7. API 健康检查 ===${NC}"
echo ""

# 检查后端 API
if curl -s -f http://127.0.0.1:11111/health > /dev/null 2>&1; then
    echo -e "${GREEN}   ✅ 后端 API 响应正常${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    
    # 显示健康检查响应
    HEALTH_RESPONSE=$(curl -s http://127.0.0.1:11111/health 2>/dev/null)
    echo -e "${BLUE}   健康检查响应:${NC}"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null | head -10 | sed 's/^/   /' || echo "$HEALTH_RESPONSE" | sed 's/^/   /'
else
    echo -e "${RED}   ❌ 后端 API 无响应${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}检查完成${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 总结
echo -e "${BLUE}检查结果: ${GREEN}$PASSED_CHECKS${NC}/${BLUE}$TOTAL_CHECKS${NC} 项通过"
echo ""

# 根据结果给出建议
if [ "$PASSED_CHECKS" -eq "$TOTAL_CHECKS" ]; then
    echo -e "${GREEN}✅ 所有检查通过！模型配置正常。${NC}"
    exit 0
elif [ "$PASSED_CHECKS" -gt $((TOTAL_CHECKS * 2 / 3)) ]; then
    echo -e "${YELLOW}⚠️  大部分检查通过，但有些项目需要注意。${NC}"
    echo ""
    echo -e "${YELLOW}建议操作：${NC}"
    echo -e "  1. 查看上述警告信息"
    echo -e "  2. 检查 PM2 日志: ${BLUE}pm2 logs timao-backend${NC}"
    echo -e "  3. 如需重启: ${BLUE}pm2 restart timao-backend${NC}"
    exit 1
else
    echo -e "${RED}❌ 多项检查失败，需要修复。${NC}"
    echo ""
    echo -e "${RED}故障排除步骤：${NC}"
    echo -e "  1. 检查模型文件是否完整下载"
    echo -e "  2. 检查系统内存是否充足（至少 4GB）"
    echo -e "  3. 检查 PM2 进程状态: ${BLUE}pm2 list${NC}"
    echo -e "  4. 查看错误日志: ${BLUE}pm2 logs timao-backend --err${NC}"
    echo -e "  5. 尝试重启服务: ${BLUE}pm2 restart timao-backend${NC}"
    echo ""
    echo -e "  详细文档: ${BLUE}docs/PM2使用指南.md${NC}"
    exit 2
fi

