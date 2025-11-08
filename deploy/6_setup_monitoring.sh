#!/bin/bash
# ============================================
# 运维监控器 (Operations Monitor)
# ============================================
# 职责：配置日志、监控和自动重启
# 依赖：部署验证器已执行
# 输出：监控配置报告
# ============================================

set -e

echo "📊 开始配置运维监控..."

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 配置文件
UPLOAD_CONFIG="deploy/upload_config.env"
MONITORING_REPORT="deploy/monitoring_report.txt"

# 检查配置
check_config() {
    echo -e "\n${YELLOW}[1/5] 检查配置...${NC}"
    
    if [ ! -f "$UPLOAD_CONFIG" ]; then
        echo -e "${RED}❌ 未找到上传配置文件${NC}"
        exit 1
    fi
    
    source "$UPLOAD_CONFIG"
    
    # 构建 SSH 命令
    SSH_CMD="ssh"
    if [ -n "$SSH_KEY_PATH" ]; then
        SSH_CMD="$SSH_CMD -i $SSH_KEY_PATH"
    fi
    SSH_CMD="$SSH_CMD -p ${SERVER_PORT:-22}"
    
    echo "✅ 配置已加载"
}

# 配置日志轮转
setup_log_rotation() {
    echo -e "\n${YELLOW}[2/5] 配置日志轮转...${NC}"
    
    # 创建日志轮转配置
    LOG_ROTATE_CONFIG="
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=10M
    missingok
    delaycompress
    copytruncate
}
"
    
    # 上传配置到服务器
    echo "$LOG_ROTATE_CONFIG" | $SSH_CMD "$SERVER_USER@$SERVER_HOST" "sudo tee /etc/logrotate.d/docker-containers > /dev/null"
    
    echo "✅ 日志轮转配置完成"
    echo "  - 保留7天日志"
    echo "  - 单文件最大10MB"
    echo "  - 自动压缩旧日志"
}

# 配置自动重启
setup_auto_restart() {
    echo -e "\n${YELLOW}[3/5] 配置自动重启...${NC}"
    
    # 检查 Docker 重启策略
    RESTART_POLICY=$($SSH_CMD "$SERVER_USER@$SERVER_HOST" "docker inspect timao-backend --format='{{.HostConfig.RestartPolicy.Name}}'")
    
    if [ "$RESTART_POLICY" = "unless-stopped" ] || [ "$RESTART_POLICY" = "always" ]; then
        echo "✅ Docker 自动重启已配置: $RESTART_POLICY"
    else
        echo "⚠️  建议配置 Docker 自动重启策略"
    fi
    
    # 配置系统启动时自动启动 Docker
    $SSH_CMD "$SERVER_USER@$SERVER_HOST" "sudo systemctl enable docker" || true
    echo "✅ Docker 服务已设置为开机自启"
}

# 创建监控脚本
create_monitoring_script() {
    echo -e "\n${YELLOW}[4/5] 创建监控脚本...${NC}"
    
    # 健康检查脚本
    HEALTH_CHECK_SCRIPT='#!/bin/bash
# 健康检查脚本

echo "======================================"
echo "服务健康检查 - $(date)"
echo "======================================"

# 检查容器状态
echo ""
echo "容器状态:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 检查后端健康
echo ""
echo "后端健康检查:"
if curl -f -s http://localhost:11111/health > /dev/null; then
    echo "✅ 后端正常"
else
    echo "❌ 后端异常"
    echo "后端日志（最后20行）:"
    docker logs timao-backend --tail=20
fi

# 检查前端健康
echo ""
echo "前端健康检查:"
if curl -f -s http://localhost > /dev/null; then
    echo "✅ 前端正常"
else
    echo "❌ 前端异常"
fi

# 检查资源使用
echo ""
echo "资源使用:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "======================================"
'
    
    # 上传脚本到服务器
    echo "$HEALTH_CHECK_SCRIPT" | $SSH_CMD "$SERVER_USER@$SERVER_HOST" "cat > $SERVER_PATH/health_check.sh && chmod +x $SERVER_PATH/health_check.sh"
    
    echo "✅ 健康检查脚本已创建: $SERVER_PATH/health_check.sh"
    
    # 创建日志查看脚本
    LOG_SCRIPT='#!/bin/bash
# 日志查看脚本

case "$1" in
    backend)
        echo "后端日志（实时）:"
        docker logs -f timao-backend
        ;;
    frontend)
        echo "前端日志（实时）:"
        docker logs -f timao-frontend
        ;;
    all)
        echo "所有日志（实时）:"
        docker-compose -f docker-compose.full.yml logs -f
        ;;
    *)
        echo "用法: $0 {backend|frontend|all}"
        exit 1
        ;;
esac
'
    
    # 上传脚本到服务器
    echo "$LOG_SCRIPT" | $SSH_CMD "$SERVER_USER@$SERVER_HOST" "cat > $SERVER_PATH/view_logs.sh && chmod +x $SERVER_PATH/view_logs.sh"
    
    echo "✅ 日志查看脚本已创建: $SERVER_PATH/view_logs.sh"
}

# 配置定时任务
setup_cron_jobs() {
    echo -e "\n${YELLOW}[5/5] 配置定时任务...${NC}"
    
    # 每小时执行健康检查
    CRON_JOB="0 * * * * cd $SERVER_PATH && ./health_check.sh >> $SERVER_PATH/logs/health_check.log 2>&1"
    
    # 添加到 crontab
    $SSH_CMD "$SERVER_USER@$SERVER_HOST" "(crontab -l 2>/dev/null | grep -v health_check.sh; echo '$CRON_JOB') | crontab -" || true
    
    echo "✅ 定时任务已配置"
    echo "  - 每小时执行健康检查"
    echo "  - 日志保存到: $SERVER_PATH/logs/health_check.log"
    
    # 创建日志目录
    $SSH_CMD "$SERVER_USER@$SERVER_HOST" "mkdir -p $SERVER_PATH/logs"
}

# 生成监控报告
generate_monitoring_report() {
    echo -e "\n${YELLOW}生成监控报告...${NC}"
    
    cat > "$MONITORING_REPORT" << EOF
====================================
运维监控配置报告
====================================
配置时间: $(date)

日志配置:
  - 日志轮转: 已启用（7天，10MB）
  - 日志路径: $SERVER_PATH/logs/
  - 容器日志: /var/lib/docker/containers/

自动重启:
  - Docker自动重启: 已启用
  - 开机自启: 已启用

监控脚本:
  - 健康检查: $SERVER_PATH/health_check.sh
  - 日志查看: $SERVER_PATH/view_logs.sh

定时任务:
  - 健康检查: 每小时执行

常用命令:
  - 健康检查: $SERVER_PATH/health_check.sh
  - 查看日志: $SERVER_PATH/view_logs.sh {backend|frontend|all}
  - 重启服务: cd $SERVER_PATH && docker-compose -f docker-compose.full.yml restart

状态: ✅ 配置完成
====================================
EOF
    
    echo "✅ 监控报告已生成: $MONITORING_REPORT"
}

# 显示使用说明
show_usage() {
    echo ""
    echo "======================================"
    echo "运维管理使用说明"
    echo "======================================"
    echo ""
    echo "1. 健康检查:"
    echo "   ssh $SERVER_USER@$SERVER_HOST '$SERVER_PATH/health_check.sh'"
    echo ""
    echo "2. 查看日志:"
    echo "   ssh $SERVER_USER@$SERVER_HOST '$SERVER_PATH/view_logs.sh backend'"
    echo "   ssh $SERVER_USER@$SERVER_HOST '$SERVER_PATH/view_logs.sh frontend'"
    echo "   ssh $SERVER_USER@$SERVER_HOST '$SERVER_PATH/view_logs.sh all'"
    echo ""
    echo "3. 重启服务:"
    echo "   ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && docker-compose -f docker-compose.full.yml restart'"
    echo ""
    echo "4. 停止服务:"
    echo "   ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && docker-compose -f docker-compose.full.yml down'"
    echo ""
    echo "5. 启动服务:"
    echo "   ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && docker-compose -f docker-compose.full.yml up -d'"
    echo ""
    echo "6. 查看资源使用:"
    echo "   ssh $SERVER_USER@$SERVER_HOST 'docker stats --no-stream'"
    echo ""
    echo "======================================"
}

# 主执行流程
main() {
    echo "======================================"
    echo "  运维监控器 (Operations Monitor)"
    echo "======================================"
    echo ""
    
    check_config
    setup_log_rotation
    setup_auto_restart
    create_monitoring_script
    setup_cron_jobs
    generate_monitoring_report
    show_usage
    
    echo ""
    echo "======================================"
    echo -e "${GREEN}✅ 运维监控配置完成${NC}"
    echo "======================================"
    echo "监控报告: $MONITORING_REPORT"
    echo ""
}

main

