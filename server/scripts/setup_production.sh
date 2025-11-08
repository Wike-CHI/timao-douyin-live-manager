#!/bin/bash
# ============================================
# 生产环境快速设置脚本
# 遵循：奥卡姆剃刀 - 最简单的设置
# ============================================

set -e

echo "🚀 设置生产环境配置..."
echo "=================================="

# 1. 复制生产环境模板
if [ ! -f ".env" ]; then
    if [ -f "env.production.template" ]; then
        cp env.production.template .env
        echo "✅ 已创建 .env 文件"
    else
        echo "❌ env.production.template 模板不存在"
        exit 1
    fi
else
    echo "⚠️  .env 文件已存在，跳过创建"
fi

# 2. 提示用户编辑配置
echo ""
echo "📝 请编辑 .env 文件，设置以下6个必需项："
echo "   1. BACKEND_PORT=11111"
echo "   2. MYSQL_HOST=你的数据库地址"
echo "   3. MYSQL_USER=timao"
echo "   4. MYSQL_PASSWORD=你的密码"
echo "   5. MYSQL_DATABASE=timao"
echo "   6. SECRET_KEY=你的密钥（必须修改）"
echo ""
echo "编辑完成后，运行验证："
echo "   python scripts/validate_deploy.py"
echo ""

