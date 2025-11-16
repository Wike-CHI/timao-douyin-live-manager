#!/bin/bash
# 提猫直播助手 - 云端服务一键部署脚本
# 功能：用户系统、订阅系统、支付系统、积分系统
# 审查人：叶维哲

set -e  # 遇到错误立即退出

echo "========================================"
echo "🚀 提猫直播助手 - 云端服务部署"
echo "========================================"
echo ""

# 检查运行权限
if [ "$EUID" -eq 0 ]; then 
   echo "⚠️  请勿使用root用户运行此脚本"
   exit 1
fi

# 1. 检查环境
echo "1️⃣  检查运行环境..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未安装Python3，请先安装"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✅ Python: $PYTHON_VERSION"

# 检查PM2
if ! command -v pm2 &> /dev/null; then
    echo "❌ 未安装PM2，正在安装..."
    npm install -g pm2
fi
PM2_VERSION=$(pm2 --version)
echo "✅ PM2: v$PM2_VERSION"

# 2. 进入项目目录
echo ""
echo "2️⃣  进入项目目录..."
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
echo "✅ 当前目录: $(pwd)"

# 3. 拉取最新代码（可选）
echo ""
echo "3️⃣  更新代码（可选）..."
read -p "是否拉取最新代码？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git pull origin main
    echo "✅ 代码已更新"
else
    echo "⏭️  跳过代码更新"
fi

# 4. 安装Python依赖
echo ""
echo "4️⃣  安装Python依赖..."
if [ -d "venv" ]; then
    echo "检测到虚拟环境，正在激活..."
    source venv/bin/activate
fi

pip install -q fastapi uvicorn[standard] sqlalchemy pymysql python-jose[cryptography] passlib[bcrypt] python-multipart redis pydantic[email]
echo "✅ Python依赖已安装"

# 5. 检查环境变量
echo ""
echo "5️⃣  检查环境变量..."
if [ ! -f "server/.env" ]; then
    echo "❌ 缺少 server/.env 文件"
    echo "请从 server/.env.example 复制并配置"
    exit 1
fi
echo "✅ 环境变量文件存在"

# 6. 停止旧服务（如果存在）
echo ""
echo "6️⃣  停止旧服务..."
if pm2 show timao-cloud &> /dev/null; then
    echo "发现运行中的服务，正在停止..."
    pm2 stop timao-cloud
    pm2 delete timao-cloud
    echo "✅ 旧服务已停止"
else
    echo "⏭️  无运行中的服务"
fi

# 7. 启动云端服务
echo ""
echo "7️⃣  启动云端服务..."
pm2 start ecosystem.cloud.config.js
echo "✅ 服务已启动"

# 8. 等待服务就绪
echo ""
echo "8️⃣  等待服务就绪..."
sleep 5

# 9. 健康检查
echo ""
echo "9️⃣  健康检查..."
HEALTH_CHECK=$(curl -s http://localhost:15000/health)
if [ $? -eq 0 ]; then
    echo "✅ 健康检查通过"
    echo "$HEALTH_CHECK" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_CHECK"
else
    echo "❌ 健康检查失败"
    echo "查看日志: pm2 logs timao-cloud"
    exit 1
fi

# 10. 查看服务状态
echo ""
echo "🔟 服务状态..."
pm2 status timao-cloud

# 11. 保存PM2配置（开机自启）
echo ""
echo "1️⃣1️⃣  保存PM2配置..."
pm2 save
echo "✅ PM2配置已保存"

# 完成
echo ""
echo "========================================"
echo "🎉 云端服务部署完成！"
echo "========================================"
echo ""
echo "📊 服务信息："
echo "  - 服务名称: timao-cloud"
echo "  - 端口: 15000"
echo "  - 状态: online"
echo ""
echo "📝 常用命令："
echo "  - 查看日志: pm2 logs timao-cloud"
echo "  - 重启服务: pm2 restart timao-cloud"
echo "  - 停止服务: pm2 stop timao-cloud"
echo "  - 监控面板: pm2 monit"
echo ""
echo "🔗 API端点："
echo "  - 健康检查: http://localhost:15000/health"
echo "  - 用户登录: http://localhost:15000/api/auth/login"
echo "  - 套餐列表: http://localhost:15000/api/subscription/plans"
echo ""
echo "📖 完整文档: docs/部署文档/云端服务部署指南.md"
echo ""

