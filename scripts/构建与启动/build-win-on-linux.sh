#!/bin/bash
# 在 Linux 云服务器上打包 Windows 应用

echo "=========================================="
echo "提猫直播助手 - Windows 打包脚本"
echo "在 Linux 服务器上打包 Windows 应用"
echo "=========================================="

set -e  # 遇到错误立即退出

cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 1. 检查 Node.js 环境
echo ""
echo "1. 检查 Node.js 环境..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    echo "请先安装 Node.js: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✓ Node.js 版本: $NODE_VERSION"

NPM_VERSION=$(npm --version)
echo "✓ npm 版本: $NPM_VERSION"

# 2. 安装 Wine（用于在 Linux 上打包 Windows 应用）
echo ""
echo "2. 检查 Wine 环境..."
if ! command -v wine &> /dev/null; then
    echo "⚠️  Wine 未安装，正在安装..."
    echo "Wine 用于在 Linux 上构建 Windows 可执行文件"
    
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        sudo dpkg --add-architecture i386
        sudo apt-get update
        sudo apt-get install -y wine wine32 wine64
    elif [ -f /etc/redhat-release ]; then
        # CentOS/RHEL
        sudo yum install -y epel-release
        sudo yum install -y wine
    else
        echo "❌ 不支持的系统，请手动安装 Wine"
        exit 1
    fi
    
    if [ $? -eq 0 ]; then
        echo "✓ Wine 安装成功"
    else
        echo "❌ Wine 安装失败"
        exit 1
    fi
else
    WINE_VERSION=$(wine --version)
    echo "✓ Wine 已安装: $WINE_VERSION"
fi

# 3. 安装项目依赖
echo ""
echo "3. 安装项目依赖..."

# 检查是否已安装
if [ ! -d "node_modules" ]; then
    echo "正在安装根目录依赖..."
    npm install
else
    echo "✓ 根目录依赖已存在"
fi

# 检查前端依赖
if [ ! -d "electron/renderer/node_modules" ]; then
    echo "正在安装前端依赖..."
    cd electron/renderer
    npm install
    cd ../..
else
    echo "✓ 前端依赖已存在"
fi

# 4. 确保 electron-builder 已安装
echo ""
echo "4. 检查 electron-builder..."
if ! npm list electron-builder --depth=0 &> /dev/null; then
    echo "正在安装 electron-builder..."
    npm install --save-dev electron-builder
else
    echo "✓ electron-builder 已安装"
fi

# 5. 清理旧的构建文件
echo ""
echo "5. 清理旧的构建文件..."
rm -rf dist
rm -rf backend_dist
rm -rf electron/renderer/dist
echo "✓ 清理完成"

# 6. 构建后端
echo ""
echo "6. 构建后端服务..."
if [ -f "scripts/构建与启动/build_backend.py" ]; then
    python scripts/构建与启动/build_backend.py
    if [ $? -eq 0 ]; then
        echo "✓ 后端构建成功"
    else
        echo "❌ 后端构建失败"
        exit 1
    fi
else
    echo "⚠️  未找到 build_backend.py，跳过后端构建"
fi

# 7. 构建前端
echo ""
echo "7. 构建前端..."
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

# 8. 打包 Windows 应用
echo ""
echo "8. 打包 Windows 应用..."
echo "这可能需要几分钟时间..."

# 设置环境变量（禁用沙箱，避免 Wine 问题）
export ELECTRON_BUILDER_ALLOW_UNRESOLVED_DEPENDENCIES=true

# 使用 electron-builder 打包
npx electron-builder --win --x64 --config build-config.json

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ 打包成功！"
    echo "=========================================="
    echo ""
    echo "输出文件位置："
    ls -lh dist/*.exe 2>/dev/null || ls -lh dist/
    echo ""
    echo "可以下载文件："
    find dist -name "*.exe" -o -name "*.zip"
else
    echo ""
    echo "=========================================="
    echo "❌ 打包失败"
    echo "=========================================="
    echo ""
    echo "请查看错误日志，常见问题："
    echo "1. Wine 配置问题 - 尝试: winecfg"
    echo "2. 依赖缺失 - 运行: npm install"
    echo "3. 内存不足 - 需要至少 2GB RAM"
    exit 1
fi

echo ""
echo "=========================================="
echo "打包完成"
echo "=========================================="

