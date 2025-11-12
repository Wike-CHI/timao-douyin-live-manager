#!/bin/bash
# 项目垃圾文件清理脚本
# 审查人: 叶维哲
# 创建日期: 2025-11-09
# 原则: KISS - 安全清理，保留必要文件

set -e

echo "======================================================"
echo "🧹 项目垃圾文件清理"
echo "======================================================"
echo ""

# 计算清理前的大小
echo "📊 计算清理前的项目大小..."
BEFORE_SIZE=$(du -sh . 2>/dev/null | cut -f1)
echo "清理前: $BEFORE_SIZE"
echo ""

# 1. Python缓存文件
echo "1️⃣  清理Python缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true
echo "✅ Python缓存已清理"
echo ""

# 2. 日志文件（保留目录结构）
echo "2️⃣  清理日志文件..."
find . -type f -name "*.log" -size +10M -delete 2>/dev/null || true
find logs/ -type f -name "*.log" -mtime +7 -delete 2>/dev/null || true
echo "✅ 大于10M的日志和7天前的日志已清理"
echo ""

# 3. 临时文件
echo "3️⃣  清理临时文件..."
find . -type f -name "*.tmp" -delete 2>/dev/null || true
find . -type f -name "*.temp" -delete 2>/dev/null || true
find . -type f -name "*~" -delete 2>/dev/null || true
find . -type f -name "*.swp" -delete 2>/dev/null || true
find . -type f -name "*.swo" -delete 2>/dev/null || true
echo "✅ 临时文件已清理"
echo ""

# 4. 系统文件
echo "4️⃣  清理系统文件..."
find . -type f -name ".DS_Store" -delete 2>/dev/null || true
find . -type f -name "Thumbs.db" -delete 2>/dev/null || true
find . -type f -name "desktop.ini" -delete 2>/dev/null || true
echo "✅ 系统文件已清理"
echo ""

# 5. 空目录
echo "5️⃣  清理空目录..."
find . -type d -empty -delete 2>/dev/null || true
echo "✅ 空目录已清理"
echo ""

# 6. npm缓存
echo "6️⃣  清理npm缓存..."
if [ -d "node_modules/.cache" ]; then
    rm -rf node_modules/.cache
    echo "✅ npm缓存已清理"
else
    echo "✅ 无npm缓存"
fi
echo ""

# 7. 测试覆盖率文件
echo "7️⃣  清理测试覆盖率文件..."
find . -type f -name ".coverage" -delete 2>/dev/null || true
find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
echo "✅ 测试覆盖率文件已清理"
echo ""

# 8. IDE缓存（可选）
echo "8️⃣  清理IDE缓存..."
read -p "是否清理IDE缓存（.vscode, .idea）? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    find . -type d -name ".vscode" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".idea" -exec rm -rf {} + 2>/dev/null || true
    echo "✅ IDE缓存已清理"
else
    echo "⏭️  跳过IDE缓存清理"
fi
echo ""

# 9. Docker构建缓存（可选）
echo "9️⃣  清理Docker构建缓存..."
read -p "是否清理Docker构建缓存? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker system prune -f 2>/dev/null || true
    echo "✅ Docker构建缓存已清理"
else
    echo "⏭️  跳过Docker缓存清理"
fi
echo ""

# 10. 大文件检测（可选删除）
echo "🔍 检测大文件（>100M）..."
echo "以下文件较大，可手动检查是否需要删除："
find . -type f -size +100M -exec du -sh {} \; 2>/dev/null | sort -rh | head -10
echo ""

# 计算清理后的大小
echo "📊 计算清理后的项目大小..."
AFTER_SIZE=$(du -sh . 2>/dev/null | cut -f1)
echo "清理后: $AFTER_SIZE"
echo ""

echo "======================================================"
echo "🎉 清理完成！"
echo "======================================================"
echo ""
echo "清理前: $BEFORE_SIZE"
echo "清理后: $AFTER_SIZE"
echo ""
echo "💡 建议定期运行此脚本保持项目整洁"
echo "======================================================"

