#!/bin/bash
# Protobuf 版本兼容性修复脚本
# 审查人：叶维哲
#
# 问题：tensorboardX 与 protobuf 4.x+ 不兼容
# 解决：降级 protobuf 到 3.20.3
#
# 使用方法：
# chmod +x scripts/诊断与排障/fix-protobuf.sh
# ./scripts/诊断与排障/fix-protobuf.sh

set -e  # 遇到错误立即退出

echo "========================================"
echo "Protobuf 版本兼容性修复"
echo "========================================"

# 切换到项目目录
cd "$(dirname "$0")"

# 激活虚拟环境
if [ -d ".venv" ]; then
    echo "✅ 激活虚拟环境..."
    source .venv/bin/activate
else
    echo "❌ 虚拟环境不存在，请先创建虚拟环境"
    exit 1
fi

# 检查当前 protobuf 版本
echo ""
echo "【步骤1】检查当前 protobuf 版本"
current_version=$(python3 -c "import google.protobuf; print(google.protobuf.__version__)" 2>/dev/null || echo "未安装")
echo "当前版本: $current_version"

# 卸载旧版本
echo ""
echo "【步骤2】卸载当前 protobuf"
pip uninstall -y protobuf || true

# 安装兼容版本
echo ""
echo "【步骤3】安装兼容版本 (protobuf<=3.20.3)"
pip install 'protobuf<=3.20.3'

# 验证安装
echo ""
echo "【步骤4】验证安装"
new_version=$(python3 -c "import google.protobuf; print(google.protobuf.__version__)")
echo "新版本: $new_version"

# 运行测试
echo ""
echo "【步骤5】运行兼容性测试"
python3 tests/regression/test_protobuf_fix.py

echo ""
echo "========================================"
echo "✅ 修复完成"
echo "========================================"
echo ""
echo "现在可以重启后端服务："
echo "  ./stop-backend.sh"
echo "  ./scripts/构建与启动/start-backend.sh"
echo ""
