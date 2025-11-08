#!/bin/bash
# ONNX 与 Protobuf 版本冲突解决脚本
# 审查人：叶维哲
#
# 问题：onnx 1.19.1 要求 protobuf>=4.25.1
# 解决：降级 onnx 到兼容 protobuf 3.20.3 的版本
#
# 使用方法：
# chmod +x fix-onnx-protobuf-conflict.sh
# ./fix-onnx-protobuf-conflict.sh

set -e

echo "========================================"
echo "解决 ONNX 与 Protobuf 版本冲突"
echo "========================================"

cd "$(dirname "$0")"

# 激活虚拟环境
if [ -d ".venv" ]; then
    echo "✅ 激活虚拟环境..."
    source .venv/bin/activate
else
    echo "❌ 虚拟环境不存在"
    exit 1
fi

# 检查当前版本
echo ""
echo "【检查当前版本】"
onnx_version=$(python3 -c "import onnx; print(onnx.__version__)" 2>/dev/null || echo "未安装")
protobuf_version=$(python3 -c "import google.protobuf; print(google.protobuf.__version__)" 2>/dev/null || echo "未安装")
echo "ONNX 当前版本: $onnx_version"
echo "Protobuf 当前版本: $protobuf_version"

# 卸载 onnx
echo ""
echo "【卸载 ONNX】"
pip uninstall -y onnx || true

# 安装兼容版本的 onnx
# onnx 1.12.0 是最后一个支持 protobuf 3.20.x 的版本
echo ""
echo "【安装兼容版本】"
echo "安装 onnx==1.12.0（兼容 protobuf 3.20.3）"
pip install onnx==1.12.0

# 验证安装
echo ""
echo "【验证安装】"
new_onnx_version=$(python3 -c "import onnx; print(onnx.__version__)")
new_protobuf_version=$(python3 -c "import google.protobuf; print(google.protobuf.__version__)")
echo "ONNX 新版本: $new_onnx_version"
echo "Protobuf 版本: $new_protobuf_version"

# 测试导入
echo ""
echo "【测试导入】"
python3 -c "
import onnx
import google.protobuf
print('✅ ONNX 导入成功')
print('✅ Protobuf 导入成功')
print('✅ 版本兼容')
"

echo ""
echo "========================================"
echo "✅ 冲突解决完成"
echo "========================================"
echo ""
echo "当前版本："
echo "  ONNX: $new_onnx_version"
echo "  Protobuf: $new_protobuf_version"
echo ""

