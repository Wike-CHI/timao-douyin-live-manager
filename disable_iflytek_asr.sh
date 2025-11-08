#!/bin/bash
# 禁用科大讯飞ASR，切换回SenseVoice

echo "================================================"
echo "      禁用科大讯飞ASR，切换回SenseVoice"
echo "================================================"
echo ""

# 检查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo "✅ 科大讯飞ASR未启用（.env文件不存在）"
    exit 0
fi

# 禁用科大讯飞
if grep -q "USE_IFLYTEK_ASR" .env; then
    sed -i "s/^USE_IFLYTEK_ASR=.*/USE_IFLYTEK_ASR=0/" .env
    echo "✅ 已禁用科大讯飞ASR"
else
    echo "✅ 科大讯飞ASR未启用"
fi

echo ""
echo "================================================"
echo "🔄 即将切换回SenseVoice"
echo "================================================"
echo ""
echo "下一步："
echo "  1. 重启服务: pm2 restart backend"
echo "  2. 查看日志: pm2 logs backend"
echo ""
echo "确认看到以下日志说明切换成功："
echo "  ✅ SenseVoice model loaded successfully"
echo ""

