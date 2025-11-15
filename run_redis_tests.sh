#!/bin/bash
# Redis优化测试运行脚本
# 确保从项目根目录运行测试

set -e

echo "============================================================"
echo "  Redis优化功能测试"
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

# 运行测试
echo "开始运行测试..."
echo ""

# 使用pytest运行测试
pytest tests/test_redis_optimization.py -v --tb=short --color=yes

# 捕获退出码
exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✅ 所有测试通过！"
else
    echo "❌ 部分测试失败，请检查上方错误信息"
fi

exit $exit_code

