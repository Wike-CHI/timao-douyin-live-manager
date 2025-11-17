#!/bin/bash
# timao-cloud 云端服务一键启动脚本
# 作者: 叶维哲
# 日期: 2025-11-16

set -e

echo "=========================================="
echo "🚀 启动timao-cloud云端服务"
echo "=========================================="
echo ""

# 进入项目目录
PROJECT_DIR="/www/wwwroot/wwwroot/timao-douyin-live-manager"
cd $PROJECT_DIR

echo "📁 当前目录: $(pwd)"
echo ""

# 激活虚拟环境（如果有）
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "⚠️  未找到虚拟环境，使用系统Python"
fi

# 检查Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "🐍 Python版本: $PYTHON_VERSION"
echo ""

# 停止已有进程
if pm2 list | grep -q "timao-cloud"; then
    echo "⚠️  发现已运行的timao-cloud进程，停止中..."
    pm2 stop timao-cloud 2>/dev/null || true
    pm2 delete timao-cloud 2>/dev/null || true
    echo "✅ 旧进程已停止"
    echo ""
fi

# 启动服务
echo "🚀 启动云端服务..."
pm2 start "uvicorn server.cloud.main:app --host 0.0.0.0 --port 15000 --workers 1" \
  --name timao-cloud \
  --interpreter python3 \
  --cwd $PROJECT_DIR \
  --max-memory-restart 600M \
  --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
  --merge-logs \
  --output logs/cloud-out.log \
  --error logs/cloud-error.log

echo ""
echo "⏳ 等待服务启动（3秒）..."
sleep 3

# 查看状态
echo ""
echo "📊 服务状态:"
pm2 status timao-cloud

# 测试健康检查
echo ""
echo "🏥 测试健康检查..."
sleep 2

HEALTH_CHECK=$(curl -s http://localhost:15000/health 2>&1)
if [ $? -eq 0 ]; then
    echo "✅ 健康检查通过:"
    echo $HEALTH_CHECK | python3 -m json.tool 2>/dev/null || echo $HEALTH_CHECK
else
    echo "❌ 健康检查失败，请查看日志:"
    pm2 logs timao-cloud --lines 10 --nostream
    exit 1
fi

# 测试控制台
echo ""
echo "🖥️  测试控制台..."
CONSOLE_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:15000/)
if [ "$CONSOLE_CHECK" = "200" ]; then
    echo "✅ 控制台可访问 (HTTP $CONSOLE_CHECK)"
else
    echo "⚠️  控制台返回 HTTP $CONSOLE_CHECK"
fi

# 保存PM2进程列表
echo ""
echo "💾 保存PM2进程列表..."
pm2 save

echo ""
echo "=========================================="
echo "🎉 启动完成！"
echo "=========================================="
echo ""
echo "📌 访问地址:"
echo "  - 控制台: http://localhost:15000/"
echo "  - 健康检查: http://localhost:15000/health"
echo "  - API文档: http://localhost:15000/docs"
echo ""
echo "🛠️  管理命令:"
echo "  - 查看状态: pm2 status timao-cloud"
echo "  - 查看日志: pm2 logs timao-cloud"
echo "  - 重启服务: pm2 restart timao-cloud"
echo "  - 停止服务: pm2 stop timao-cloud"
echo ""
echo "📝 日志文件:"
echo "  - 输出日志: logs/cloud-out.log"
echo "  - 错误日志: logs/cloud-error.log"
echo ""

# 显示最近5行日志
echo "📋 最近日志:"
pm2 logs timao-cloud --lines 5 --nostream

echo ""
echo "✅ 服务已成功启动并运行！"

