#!/bin/bash

echo "===================================="
echo "提猫直播助手 - 管理后台"
echo "===================================="
echo ""

if [ ! -d "node_modules" ]; then
    echo "[1/2] 正在安装依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "依赖安装失败！"
        exit 1
    fi
    echo "依赖安装完成！"
    echo ""
fi

echo "[2/2] 启动开发服务器..."
echo "访问地址: http://localhost:3000"
echo ""
npm run dev

