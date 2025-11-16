#!/bin/bash
# 测试模型前临时释放内存

echo "=================================================="
echo "内存清理和模型测试脚本"
echo "=================================================="
echo ""

# 显示当前内存
echo "当前内存状态："
free -h
echo ""

# 1. 停止不必要的 uvicorn 服务（临时）
echo "正在停止临时服务以释放内存..."
echo ""

# 找出非 8181 端口的 uvicorn 进程并停止
UVICORN_PIDS=$(ps aux | grep 'uvicorn.*11111' | grep -v grep | awk '{print $2}')
if [ ! -z "$UVICORN_PIDS" ]; then
    echo "停止 11111 端口的 uvicorn 进程: $UVICORN_PIDS"
    echo $UVICORN_PIDS | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# 2. 清理系统缓存
echo "清理系统缓存..."
sync
echo 3 > /proc/sys/vm/drop_caches
sleep 1
echo ""

# 显示清理后的内存
echo "清理后的内存状态："
free -h
echo ""

# 3. 运行测试
echo "=================================================="
echo "开始测试模型..."
echo "=================================================="
echo ""

cd /www/wwwroot/wwwroot/timao-douyin-live-manager
source .venv/bin/activate
python test_vad_model.py

TEST_RESULT=$?

# 4. 测试完成后的信息
echo ""
echo "=================================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ 测试成功完成"
else
    echo "❌ 测试失败（退出码: $TEST_RESULT）"
fi
echo "=================================================="
echo ""

# 显示最终内存
echo "测试后的内存状态："
free -h
echo ""

exit $TEST_RESULT

