#!/bin/bash
# 只打包 Electron 前端应用（后端已部署到服务器）

echo "=========================================="
echo "提猫直播助手 - Electron 前端打包"
echo "只打包前端应用，连接到已部署的后端服务器"
echo "=========================================="

set -e  # 遇到错误立即退出

cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 1. 检查 Node.js 环境
echo ""
echo "1. 检查 Node.js 环境..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi

NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
echo "✓ Node.js: $NODE_VERSION"
echo "✓ npm: $NPM_VERSION"

# 2. 检查 electron-builder
echo ""
echo "2. 检查 electron-builder..."
if ! npm list electron-builder --depth=0 &> /dev/null; then
    echo "正在安装 electron-builder..."
    npm install --save-dev electron-builder
else
    echo "✓ electron-builder 已安装"
fi

# 3. 安装依赖（如果需要）
echo ""
echo "3. 检查项目依赖..."
if [ ! -d "node_modules" ]; then
    echo "正在安装根目录依赖..."
    npm install
else
    echo "✓ 根目录依赖已存在"
fi

if [ ! -d "electron/renderer/node_modules" ]; then
    echo "正在安装前端依赖..."
    cd electron/renderer
    npm install
    cd ../..
else
    echo "✓ 前端依赖已存在"
fi

# 4. 清理旧的前端构建
echo ""
echo "4. 清理旧的构建文件..."
rm -rf dist
rm -rf electron/renderer/dist
echo "✓ 清理完成"

# 5. 构建前端
echo ""
echo "5. 构建前端..."
cd electron/renderer
npm run build
if [ $? -eq 0 ]; then
    echo "✓ 前端构建成功"
    cd ../..
else
    echo "❌ 前端构建失败"
    cd ../..
    exit 1
fi

# 6. 检查后端连接配置
echo ""
echo "6. 后端配置检查..."
echo "⚠️  请确保应用配置了正确的后端服务器地址："
echo "   - 服务器IP: 129.211.218.135"
echo "   - 后端端口: 8181"
echo "   - 前端端口: 10050"
echo ""
read -p "配置已确认？按回车继续，或 Ctrl+C 取消..."

# 7. 打包 Windows 应用
echo ""
echo "7. 打包 Windows 应用..."
echo "这可能需要几分钟时间..."

# 设置环境变量
export ELECTRON_BUILDER_ALLOW_UNRESOLVED_DEPENDENCIES=true

# 只打包前端，不包含后端文件
npx electron-builder --win --x64 \
  --config.files='["electron/**/*", "package.json", "!electron/renderer/node_modules/**", "!server/**", "!backend_dist/**", "!**/__pycache__/**", "!**/*.pyc"]' \
  --config.win.target=portable \
  --config.artifactName='提猫直播助手-${version}-${arch}.exe'

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ 打包成功！"
    echo "=========================================="
    echo ""
    echo "输出文件："
    ls -lh dist/*.exe 2>/dev/null || ls -lh dist/
    echo ""
    echo "📦 应用配置："
    echo "   - 前端：Electron 桌面应用"
    echo "   - 后端：连接到 http://129.211.218.135:8181"
    echo ""
    echo "🔄 版本更新："
    echo "   - 应用已包含自动更新检查逻辑"
    echo "   - 用户启动时会检查新版本"
    echo ""
    echo "📥 下载文件："
    find dist -name "*.exe" -exec ls -lh {} \;
else
    echo ""
    echo "=========================================="
    echo "❌ 打包失败"
    echo "=========================================="
    exit 1
fi

echo ""
echo "=========================================="
echo "打包完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 下载 dist/*.exe 文件到本地"
echo "2. 在 Windows 上测试应用"
echo "3. 验证后端连接正常"
echo "4. 发布给用户"

