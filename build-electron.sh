#!/bin/bash
# 打包Electron应用脚本
# 使用方法: ./build-electron.sh

set -e

echo "📦 开始打包Electron应用..."

# 设置环境变量
export VITE_FASTAPI_URL="http://129.211.218.135:10050"
export VITE_STREAMCAP_URL="http://129.211.218.135:10050"
export VITE_DOUYIN_URL="http://129.211.218.135:10050"
export ELECTRON_START_API="false"

# 1. 安装依赖
echo "📥 安装依赖..."
npm install

# 2. 构建前端
echo "🔨 构建前端..."
cd electron/renderer
npm install
npm run build
cd ../..

# 3. 打包Electron
echo "📦 打包Electron应用..."
npm run build:win

echo ""
echo "✅ 打包完成！"
echo "📁 安装包位置: dist/TalkingCat-Portable-*.exe"
echo ""

