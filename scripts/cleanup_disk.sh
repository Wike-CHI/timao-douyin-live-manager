#!/bin/bash
# -*- coding: utf-8 -*-
# 磁盘清理脚本 - 释放服务器磁盘空间

set -e

echo "=================================================="
echo "🧹 服务器磁盘清理工具"
echo "=================================================="

# 检查当前磁盘使用情况
echo -e "\n📊 当前磁盘使用情况:"
df -h | grep -E "Filesystem|/$" || df -h

# 进入项目目录
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)
echo -e "\n📁 项目目录: $PROJECT_ROOT"

# 1. 清理pip缓存
echo -e "\n" 
echo "=" * 50
echo "1️⃣  清理pip缓存"
echo "=" * 50

if command -v pip &> /dev/null; then
    echo "🔄 清理pip缓存..."
    BEFORE_SIZE=$(du -sh ~/.cache/pip 2>/dev/null | cut -f1 || echo "0")
    echo "   清理前: $BEFORE_SIZE"
    
    pip cache purge || echo "⚠️  pip cache purge 失败"
    
    AFTER_SIZE=$(du -sh ~/.cache/pip 2>/dev/null | cut -f1 || echo "0")
    echo "   清理后: $AFTER_SIZE"
    echo "✅ pip缓存已清理"
else
    echo "⚠️  pip未安装，跳过"
fi

# 2. 清理Python __pycache__
echo -e "\n"
echo "=" * 50
echo "2️⃣  清理Python __pycache__"
echo "=" * 50

echo "🔄 查找 __pycache__ 目录..."
PYCACHE_COUNT=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
echo "   发现 $PYCACHE_COUNT 个目录"

if [ "$PYCACHE_COUNT" -gt 0 ]; then
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    echo "✅ __pycache__ 已清理"
else
    echo "✅ 无需清理"
fi

# 3. 清理.pyc文件
echo -e "\n"
echo "=" * 50
echo "3️⃣  清理.pyc文件"
echo "=" * 50

echo "🔄 查找 .pyc 文件..."
PYC_COUNT=$(find . -type f -name "*.pyc" 2>/dev/null | wc -l)
echo "   发现 $PYC_COUNT 个文件"

if [ "$PYC_COUNT" -gt 0 ]; then
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    echo "✅ .pyc文件已清理"
else
    echo "✅ 无需清理"
fi

# 4. 清理ModelScope临时文件
echo -e "\n"
echo "=" * 50
echo "4️⃣  清理ModelScope临时文件"
echo "=" * 50

TEMP_DIR="$PROJECT_ROOT/server/models/.cache/modelscope/._____temp"
if [ -d "$TEMP_DIR" ]; then
    TEMP_SIZE=$(du -sh "$TEMP_DIR" 2>/dev/null | cut -f1)
    echo "   临时目录大小: $TEMP_SIZE"
    echo "🔄 删除临时文件..."
    rm -rf "$TEMP_DIR"
    echo "✅ ModelScope临时文件已清理"
else
    echo "✅ 无临时文件"
fi

# 5. 清理日志文件（超过30天）
echo -e "\n"
echo "=" * 50
echo "5️⃣  清理旧日志文件"
echo "=" * 50

echo "🔄 查找超过30天的日志..."
OLD_LOGS=$(find . -name "*.log" -mtime +30 2>/dev/null | wc -l)
echo "   发现 $OLD_LOGS 个旧日志"

if [ "$OLD_LOGS" -gt 0 ]; then
    find . -name "*.log" -mtime +30 -delete 2>/dev/null || true
    echo "✅ 旧日志已清理"
else
    echo "✅ 无需清理"
fi

# 6. 截断大日志文件
echo -e "\n"
echo "=" * 50
echo "6️⃣  截断大日志文件"
echo "=" * 50

for logfile in backend.log nohup.out; do
    if [ -f "$logfile" ]; then
        SIZE=$(du -h "$logfile" 2>/dev/null | cut -f1)
        echo "   $logfile: $SIZE"
        if [ -s "$logfile" ]; then
            echo "🔄 截断 $logfile..."
            truncate -s 0 "$logfile" || > "$logfile"
            echo "✅ 已截断"
        fi
    fi
done

# 7. 清理node_modules缓存（可选）
echo -e "\n"
echo "=" * 50
echo "7️⃣  清理npm缓存（可选）"
echo "=" * 50

if command -v npm &> /dev/null; then
    NPM_CACHE_SIZE=$(du -sh ~/.npm 2>/dev/null | cut -f1 || echo "未知")
    echo "   npm缓存大小: $NPM_CACHE_SIZE"
    read -p "   是否清理npm缓存? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        npm cache clean --force
        echo "✅ npm缓存已清理"
    else
        echo "⏭️  跳过npm缓存清理"
    fi
else
    echo "⚠️  npm未安装，跳过"
fi

# 8. 列出最大的目录（参考）
echo -e "\n"
echo "=" * 50
echo "8️⃣  最大的目录（前10）"
echo "=" * 50

echo "🔍 扫描中（可能需要几分钟）..."
du -h --max-depth=2 . 2>/dev/null | sort -rh | head -10 || echo "⚠️  扫描失败"

# 9. 最终磁盘使用情况
echo -e "\n"
echo "=================================================="
echo "📊 清理后磁盘使用情况"
echo "=================================================="

df -h | grep -E "Filesystem|/$" || df -h

echo -e "\n✅ 磁盘清理完成!"
echo ""
echo "💡 进一步清理建议:"
echo "   1. 卸载不需要的依赖包"
echo "   2. 删除旧的模型文件"
echo "   3. 压缩或归档旧数据"
echo ""
echo "   查看大文件: du -ah . | sort -rh | head -20"
echo ""

