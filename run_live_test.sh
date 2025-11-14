#!/bin/bash
# 直播间完整功能和性能测试运行脚本
# 审查人: 叶维哲

set -e

echo "============================================================"
echo "  直播间完整功能和性能测试"
echo "  审查人: 叶维哲"
echo "============================================================"
echo ""

# 切换到项目根目录
cd "$(dirname "$0")"

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在，请先创建虚拟环境"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 设置PYTHONPATH
export PYTHONPATH="${PWD}:${PYTHONPATH}"

echo "✅ 环境配置完成"
echo "   PYTHONPATH: $PYTHONPATH"
echo ""

# 检查Redis是否运行
echo "检查Redis状态..."
if redis-cli ping &>/dev/null; then
    echo "✅ Redis运行正常"
else
    echo "⚠️  Redis未运行，部分测试可能失败"
fi
echo ""

# 检查测试参数
ROOM_URL=${1:-"https://live.douyin.com/932546434419?room_id=7572532254115826451"}
DURATION=${2:-10}

echo "测试配置:"
echo "  直播间URL: $ROOM_URL"
echo "  测试时长: ${DURATION}分钟"
echo ""

# 创建测试报告目录
mkdir -p test_reports

# 运行测试
echo "开始运行测试..."
echo ""

python tests/test_live_integration.py

# 捕获退出码
exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "============================================================"
    echo "  ✅ 测试完成"
    echo "============================================================"
else
    echo "============================================================"
    echo "  ❌ 测试失败 (退出码: $exit_code)"
    echo "============================================================"
fi

# 显示报告位置
echo ""
echo "📄 测试报告保存在: test_reports/"
ls -lt test_reports/ | head -5

exit $exit_code

