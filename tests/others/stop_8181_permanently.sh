#!/bin/bash
# 彻底停止8181端口服务

echo "=========================================="
echo "彻底停止8181端口服务"
echo "=========================================="
echo ""

# 1. 查找并停止8181端口的所有进程
echo "1. 停止8181端口的所有进程..."
while true; do
    PID=$(lsof -ti:8181 2>/dev/null)
    if [ -z "$PID" ]; then
        echo "✓ 8181端口已无进程监听"
        break
    fi
    echo "   找到进程 PID: $PID，正在停止..."
    kill -9 $PID 2>/dev/null
    sleep 1
done
echo ""

# 2. 检查nohup进程
echo "2. 检查nohup后台进程..."
ps aux | grep "nohup.*uvicorn.*8181" | grep -v grep | awk '{print $2}' | while read pid; do
    echo "   停止nohup进程: $pid"
    kill -9 $pid 2>/dev/null
done
echo ""

# 3. 检查当前状态
echo "3. 当前uvicorn进程状态："
ps aux | grep uvicorn | grep -v grep
echo ""

# 4. 检查端口监听
echo "4. 当前端口监听状态："
netstat -tulnp | grep -E ":(8181|11111)" | grep LISTEN
echo ""

echo "=========================================="
echo "✅ 清理完成"
echo "=========================================="
echo ""
echo "如果8181端口再次被启动，请检查："
echo "1. PM2服务配置"
echo "2. crontab定时任务"
echo "3. systemd服务"
echo "4. 宝塔面板的计划任务"

