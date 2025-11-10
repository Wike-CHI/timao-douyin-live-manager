#!/bin/bash
# 自动修改后端地址配置

echo "=========================================="
echo "修改后端地址配置"
echo "将本地地址改为远程服务器地址"
echo "=========================================="

cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 1. 备份原文件
echo ""
echo "1. 备份原文件..."
if [ ! -f "electron/main.js.backup" ]; then
    cp electron/main.js electron/main.js.backup
    echo "✓ 已备份：electron/main.js.backup"
else
    echo "⚠️  备份文件已存在，跳过"
fi

# 2. 读取 main.js
echo ""
echo "2. 分析当前配置..."
echo ""
echo "当前配置："
grep -A 15 "const serviceConfig" electron/main.js | head -20

# 3. 创建修改后的配置
echo ""
echo "3. 创建新配置..."

cat > /tmp/new_service_config.txt << 'EOF'
// 服务配置
const isDev = !app.isPackaged;  // 判断是否为开发环境

const serviceConfig = {
    main: {
        name: 'FastAPI',
        host: isDev ? '127.0.0.1' : '129.211.218.135',  // 开发用本地，生产用远程
        port: '8181',
        healthPath: '/health'
    },
    streamcap: {
        name: 'StreamCap',
        host: isDev ? '127.0.0.1' : '129.211.218.135',
        port: process.env.STREAMCAP_PORT || '8181',
        healthPath: '/health'
    },
    douyin: {
        name: 'DouyinLive',
        host: isDev ? '127.0.0.1' : '129.211.218.135',
        port: process.env.DOUYIN_PORT || '8181',
        healthPath: '/health'
    }
};
EOF

echo "✓ 新配置已准备"

# 4. 手动修改提示
echo ""
echo "=========================================="
echo "⚠️  需要手动修改"
echo "=========================================="
echo ""
echo "由于配置较复杂，建议手动修改 electron/main.js"
echo ""
echo "修改步骤："
echo "1. 打开文件：vi electron/main.js"
echo "2. 找到第 41-57 行的 serviceConfig"
echo "3. 替换为新配置（见下方）"
echo "4. 保存文件"
echo ""
echo "=========================================="
echo "新配置内容："
echo "=========================================="
cat /tmp/new_service_config.txt
echo ""
echo "=========================================="
echo ""
echo "关键修改点："
echo "1. 添加 const isDev = !app.isPackaged;"
echo "2. 每个服务添加 host 配置"
echo "3. host 使用三元运算符：开发环境用 127.0.0.1，生产环境用 129.211.218.135"
echo ""
echo "=========================================="
echo ""

# 5. 查找需要修改的其他位置
echo ""
echo "4. 检查其他需要修改的位置..."
echo ""
echo "需要替换的位置："
grep -n "127\.0\.0\.1.*serviceConfig" electron/main.js | while read line; do
    echo "  - $line"
done

echo ""
echo "这些位置需要将 127.0.0.1 替换为："
echo '  ${serviceConfig.main.host} 或 ${config.host}'
echo ""

# 6. 提供替换命令
echo ""
echo "=========================================="
echo "快速替换命令（谨慎使用）："
echo "=========================================="
echo ""
echo "# 方法1：使用 sed 批量替换（需要仔细检查）"
echo 'sed -i "s/127\.0\.0\.1:\${serviceConfig\.main\.port}/\${serviceConfig.main.host}:\${serviceConfig.main.port}/g" electron/main.js'
echo ""
echo "# 方法2：使用 vi 手动替换（推荐）"
echo 'vi electron/main.js'
echo '# 在 vi 中执行: :%s/127\.0\.0\.1:\${serviceConfig/\${serviceConfig.main.host}:\${serviceConfig/gc'
echo ""

# 7. 验证脚本
echo ""
echo "=========================================="
echo "验证配置脚本"
echo "=========================================="
cat > verify-config.sh << 'EOF'
#!/bin/bash
echo "检查配置修改..."
echo ""
echo "1. serviceConfig 应包含 host 字段："
grep -A 5 "serviceConfig = {" electron/main.js | grep "host:"
echo ""
echo "2. 检查剩余的 127.0.0.1（应该只剩前端开发服务器）："
grep -n "127\.0\.0\.1" electron/main.js | grep -v "10050" | grep -v "rendererDevServerURL"
echo ""
echo "如果上面没有输出，说明修改成功！"
EOF

chmod +x verify-config.sh

echo ""
echo "创建了验证脚本：verify-config.sh"
echo "修改后运行：./verify-config.sh"
echo ""

echo ""
echo "=========================================="
echo "总结"
echo "=========================================="
echo ""
echo "✅ 已完成："
echo "  - 备份原文件"
echo "  - 准备新配置"
echo "  - 创建验证脚本"
echo ""
echo "⏳ 待完成："
echo "  - 手动修改 electron/main.js"
echo "  - 运行 ./verify-config.sh 验证"
echo "  - 重新打包：./build-electron-only.sh"
echo ""
echo "📖 详细文档："
echo "  - 配置后端地址指南.md"
echo ""
echo "=========================================="

