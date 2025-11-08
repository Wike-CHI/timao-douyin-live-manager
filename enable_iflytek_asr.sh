#!/bin/bash
# 快速启用科大讯飞ASR临时方案

echo "================================================"
echo "        启用科大讯飞ASR临时方案"
echo "================================================"
echo ""

# 检查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo "创建 .env 文件..."
    touch .env
fi

# 检查配置
echo "请输入科大讯飞凭证（从 https://www.xfyun.cn/ 获取）："
echo ""

read -p "APP_ID: " APP_ID
read -p "API_KEY: " API_KEY
read -p "API_SECRET: " API_SECRET

echo ""
echo "正在配置..."

# 检查是否已存在配置
if grep -q "IFLYTEK_APP_ID" .env; then
    # 更新配置
    sed -i "s/^IFLYTEK_APP_ID=.*/IFLYTEK_APP_ID=$APP_ID/" .env
    sed -i "s/^IFLYTEK_API_KEY=.*/IFLYTEK_API_KEY=$API_KEY/" .env
    sed -i "s/^IFLYTEK_API_SECRET=.*/IFLYTEK_API_SECRET=$API_SECRET/" .env
else
    # 添加配置
    echo "" >> .env
    echo "# 科大讯飞ASR配置" >> .env
    echo "IFLYTEK_APP_ID=$APP_ID" >> .env
    echo "IFLYTEK_API_KEY=$API_KEY" >> .env
    echo "IFLYTEK_API_SECRET=$API_SECRET" >> .env
fi

# 启用科大讯飞
if grep -q "USE_IFLYTEK_ASR" .env; then
    sed -i "s/^USE_IFLYTEK_ASR=.*/USE_IFLYTEK_ASR=1/" .env
else
    echo "USE_IFLYTEK_ASR=1" >> .env
fi

echo "✅ 配置已保存到 .env 文件"
echo ""

# 测试配置
echo "正在测试配置..."
source .venv/bin/activate 2>/dev/null || true
python test_iflytek_asr.py

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "✅ 科大讯飞ASR配置成功！"
    echo "================================================"
    echo ""
    echo "下一步："
    echo "  1. 重启服务: pm2 restart backend"
    echo "  2. 查看日志: pm2 logs backend"
    echo ""
    echo "查找以下日志确认启用："
    echo "  🔄 使用科大讯飞ASR服务（临时替代方案）"
    echo "  ✅ 科大讯飞ASR已启用"
    echo ""
else
    echo ""
    echo "================================================"
    echo "❌ 配置测试失败"
    echo "================================================"
    echo ""
    echo "请检查："
    echo "  1. 凭证是否正确"
    echo "  2. 网络连接是否正常"
    echo "  3. 是否开通了实时语音识别服务"
    echo ""
fi

