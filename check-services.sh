#!/bin/bash
# 服务健康检查和自动恢复脚本
# 可以添加到crontab中定期执行

LOG_FILE="/www/wwwroot/wwwroot/timao-douyin-live-manager/logs/monitor.log"
PROJECT_DIR="/www/wwwroot/wwwroot/timao-douyin-live-manager"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

check_and_restart_service() {
    local service_name=$1
    local port=$2
    local start_command=$3
    
    if ! netstat -tulnp | grep ":$port" > /dev/null 2>&1; then
        log_message "❌ $service_name (端口$port) 未运行，正在重启..."
        
        cd "$PROJECT_DIR"
        source venv/bin/activate
        
        eval "$start_command" > /dev/null 2>&1 &
        sleep 3
        
        if netstat -tulnp | grep ":$port" > /dev/null 2>&1; then
            log_message "✓ $service_name 重启成功"
        else
            log_message "❌ $service_name 重启失败"
        fi
    fi
}

# 检查FastAPI主服务
check_and_restart_service "FastAPI主服务" 8000 \
    "nohup python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 > logs/main.log 2>&1"

# 检查StreamCap服务
check_and_restart_service "StreamCap服务" 8001 \
    "nohup python -m uvicorn server.streamcap_service:app --host 0.0.0.0 --port 8001 > logs/streamcap.log 2>&1"

# 检查Douyin服务
check_and_restart_service "Douyin服务" 8002 \
    "nohup python -m uvicorn server.douyin_service:app --host 0.0.0.0 --port 8002 > logs/douyin.log 2>&1"

# 检查Nginx
if ! systemctl is-active --quiet nginx; then
    log_message "❌ Nginx未运行，正在重启..."
    systemctl restart nginx
    if systemctl is-active --quiet nginx; then
        log_message "✓ Nginx重启成功"
    else
        log_message "❌ Nginx重启失败"
    fi
fi

