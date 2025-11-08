#!/bin/bash
# ============================================
# 一键部署脚本 (All-in-One Deployer)
# ============================================
# 职责：协调所有部署步骤，按顺序执行
# 依赖：各个独立模块脚本
# 输出：完整部署报告
# ============================================

set -e

echo "🚀 开始一键部署到云服务器..."

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 部署状态
CURRENT_STEP=0
TOTAL_STEPS=6

# 显示步骤信息
show_step() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    echo ""
    echo "======================================"
    echo -e "${BLUE}步骤 $CURRENT_STEP/$TOTAL_STEPS: $1${NC}"
    echo "======================================"
    echo ""
}

# 检查是否在项目根目录
check_project_root() {
    if [ ! -f "docker-compose.full.yml" ] || [ ! -d "server" ] || [ ! -d "admin-dashboard" ]; then
        echo -e "${RED}❌ 错误：请在项目根目录运行此脚本${NC}"
        echo "当前目录: $(pwd)"
        exit 1
    fi
}

# 检查部署脚本是否存在
check_deploy_scripts() {
    local scripts=(
        "deploy/1_prepare_environment.sh"
        "deploy/2_upload_code.sh"
        "deploy/3_configure_environment.sh"
        "deploy/4_deploy_services.sh"
        "deploy/5_validate_deployment.sh"
        "deploy/6_setup_monitoring.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ ! -f "$script" ]; then
            echo -e "${RED}❌ 错误：部署脚本不存在: $script${NC}"
            exit 1
        fi
        chmod +x "$script"
    done
}

# 显示欢迎信息
show_welcome() {
    echo ""
    echo "======================================"
    echo "  欢迎使用一键部署脚本"
    echo "======================================"
    echo ""
    echo "本脚本将按顺序执行以下步骤："
    echo "  1. 准备云服务器环境"
    echo "  2. 上传项目代码"
    echo "  3. 配置环境变量"
    echo "  4. 部署服务"
    echo "  5. 验证部署"
    echo "  6. 配置运维监控"
    echo ""
    echo "预计耗时：10-30 分钟"
    echo ""
    echo -e "${YELLOW}注意：${NC}"
    echo "  - 请确保已配置 deploy/upload_config.env"
    echo "  - 部署过程中会有交互式配置"
    echo "  - 请保持网络连接稳定"
    echo ""
    read -p "按回车键开始部署，或 Ctrl+C 取消..."
}

# 执行部署步骤
execute_step() {
    local step_script=$1
    local step_name=$2
    
    show_step "$step_name"
    
    if bash "$step_script"; then
        echo ""
        echo -e "${GREEN}✅ $step_name 完成${NC}"
        return 0
    else
        echo ""
        echo -e "${RED}❌ $step_name 失败${NC}"
        echo "请检查错误信息并修复问题"
        exit 1
    fi
}

# 生成完整报告
generate_final_report() {
    echo -e "\n${YELLOW}生成完整部署报告...${NC}"
    
    FINAL_REPORT="deploy/final_deployment_report.txt"
    
    cat > "$FINAL_REPORT" << EOF
====================================
完整部署报告
====================================
部署时间: $(date)

执行步骤:
  1. ✅ 环境准备
  2. ✅ 代码上传
  3. ✅ 环境配置
  4. ✅ 服务部署
  5. ✅ 部署验证
  6. ✅ 运维监控

详细报告:
  - 环境检查: deploy/environment_check_report.txt
  - 代码上传: deploy/upload_report.txt
  - 环境配置: deploy/configure_report.txt
  - 服务部署: deploy/deploy_report.txt
  - 部署验证: deploy/validation_report.txt
  - 运维监控: deploy/monitoring_report.txt

部署状态: ✅ 成功
====================================
EOF
    
    echo "✅ 完整部署报告已生成: $FINAL_REPORT"
}

# 显示部署成功信息
show_success() {
    # 读取服务器信息
    if [ -f "deploy/upload_config.env" ]; then
        source "deploy/upload_config.env"
        
        # 获取服务器IP（从部署报告中读取）
        if [ -f "deploy/deploy_report.txt" ]; then
            SERVER_IP=$(grep "公网IP:" deploy/deploy_report.txt | awk '{print $2}')
        else
            SERVER_IP="$SERVER_HOST"
        fi
    fi
    
    echo ""
    echo "======================================"
    echo -e "${GREEN}🎉 部署成功！${NC}"
    echo "======================================"
    echo ""
    echo "服务访问地址:"
    echo "  前端: http://$SERVER_IP"
    echo "  后端: http://$SERVER_IP:11111"
    echo "  API文档: http://$SERVER_IP:11111/docs"
    echo ""
    echo "运维管理:"
    echo "  健康检查: ssh $SERVER_USER@$SERVER_HOST '$SERVER_PATH/health_check.sh'"
    echo "  查看日志: ssh $SERVER_USER@$SERVER_HOST '$SERVER_PATH/view_logs.sh all'"
    echo ""
    echo "完整报告: deploy/final_deployment_report.txt"
    echo ""
    echo "======================================"
    echo ""
}

# 显示帮助信息
show_help() {
    cat << 'EOF'
====================================
一键部署脚本使用说明
====================================

用法:
  ./deploy/deploy_all.sh [选项]

选项:
  -h, --help              显示此帮助信息
  -s, --skip-prepare      跳过环境准备步骤
  -c, --check-only        仅检查环境，不执行部署

示例:
  # 完整部署
  ./deploy/deploy_all.sh

  # 跳过环境准备（如果已经准备好）
  ./deploy/deploy_all.sh --skip-prepare

  # 仅检查环境
  ./deploy/deploy_all.sh --check-only

====================================
EOF
}

# 主执行流程
main() {
    # 解析参数
    SKIP_PREPARE=false
    CHECK_ONLY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -s|--skip-prepare)
                SKIP_PREPARE=true
                shift
                ;;
            -c|--check-only)
                CHECK_ONLY=true
                shift
                ;;
            *)
                echo -e "${RED}未知选项: $1${NC}"
                echo "使用 --help 查看帮助"
                exit 1
                ;;
        esac
    done
    
    # 检查环境
    check_project_root
    check_deploy_scripts
    
    # 如果仅检查
    if [ "$CHECK_ONLY" = true ]; then
        echo "执行环境检查..."
        bash deploy/1_prepare_environment.sh
        exit 0
    fi
    
    # 显示欢迎信息
    show_welcome
    
    # 执行部署步骤
    if [ "$SKIP_PREPARE" = false ]; then
        execute_step "deploy/1_prepare_environment.sh" "准备云服务器环境"
    else
        echo "跳过环境准备步骤"
        CURRENT_STEP=$((CURRENT_STEP + 1))
    fi
    
    execute_step "deploy/2_upload_code.sh" "上传项目代码"
    execute_step "deploy/3_configure_environment.sh" "配置环境变量"
    execute_step "deploy/4_deploy_services.sh" "部署服务"
    execute_step "deploy/5_validate_deployment.sh" "验证部署"
    execute_step "deploy/6_setup_monitoring.sh" "配置运维监控"
    
    # 生成报告
    generate_final_report
    
    # 显示成功信息
    show_success
}

main "$@"

