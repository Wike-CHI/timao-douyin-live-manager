#!/bin/bash
# ============================================
# 部署脚本自动测试
# ============================================
# 职责：测试所有部署脚本的语法和基本功能
# 审查人：叶维哲
# ============================================

set -e

echo "🧪 开始测试部署脚本..."

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 测试结果
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 记录测试结果
record_test() {
    local test_name=$1
    local status=$2
    local message=$3
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$status" = "pass" ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo -e "${GREEN}✅ $test_name${NC}"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo -e "${RED}❌ $test_name: $message${NC}"
    fi
}

# 测试：检查脚本文件是否存在
test_script_files() {
    echo -e "\n${YELLOW}[1/5] 测试脚本文件存在性...${NC}"
    
    local scripts=(
        "deploy/1_prepare_environment.sh"
        "deploy/2_upload_code.sh"
        "deploy/3_configure_environment.sh"
        "deploy/4_deploy_services.sh"
        "deploy/5_validate_deployment.sh"
        "deploy/6_setup_monitoring.sh"
        "deploy/deploy_all.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            record_test "文件存在: $script" "pass"
        else
            record_test "文件存在: $script" "fail" "文件不存在"
        fi
    done
}

# 测试：检查脚本语法
test_script_syntax() {
    echo -e "\n${YELLOW}[2/5] 测试脚本语法...${NC}"
    
    local scripts=(
        "deploy/1_prepare_environment.sh"
        "deploy/2_upload_code.sh"
        "deploy/3_configure_environment.sh"
        "deploy/4_deploy_services.sh"
        "deploy/5_validate_deployment.sh"
        "deploy/6_setup_monitoring.sh"
        "deploy/deploy_all.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            if bash -n "$script" 2>/dev/null; then
                record_test "语法检查: $script" "pass"
            else
                record_test "语法检查: $script" "fail" "语法错误"
            fi
        fi
    done
}

# 测试：检查脚本可执行权限
test_script_permissions() {
    echo -e "\n${YELLOW}[3/5] 测试脚本权限...${NC}"
    
    local scripts=(
        "deploy/1_prepare_environment.sh"
        "deploy/2_upload_code.sh"
        "deploy/3_configure_environment.sh"
        "deploy/4_deploy_services.sh"
        "deploy/5_validate_deployment.sh"
        "deploy/6_setup_monitoring.sh"
        "deploy/deploy_all.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            if [ -x "$script" ]; then
                record_test "可执行权限: $script" "pass"
            else
                # 自动添加执行权限
                chmod +x "$script"
                record_test "可执行权限: $script" "pass" "已自动添加"
            fi
        fi
    done
}

# 测试：检查配置文件模板
test_config_templates() {
    echo -e "\n${YELLOW}[4/5] 测试配置文件模板...${NC}"
    
    if [ -f "deploy/upload_config.env.template" ]; then
        record_test "配置模板存在" "pass"
        
        # 检查必需的配置项
        required_keys=(
            "SERVER_HOST"
            "SERVER_USER"
            "SERVER_PATH"
        )
        
        for key in "${required_keys[@]}"; do
            if grep -q "^$key=" "deploy/upload_config.env.template"; then
                record_test "配置项: $key" "pass"
            else
                record_test "配置项: $key" "fail" "缺少配置项"
            fi
        done
    else
        record_test "配置模板存在" "fail" "模板文件不存在"
    fi
}

# 测试：检查文档文件
test_documentation() {
    echo -e "\n${YELLOW}[5/5] 测试文档文件...${NC}"
    
    local docs=(
        "deploy/README.md"
        "deploy/QUICKSTART.md"
    )
    
    for doc in "${docs[@]}"; do
        if [ -f "$doc" ]; then
            record_test "文档存在: $doc" "pass"
        else
            record_test "文档存在: $doc" "fail" "文档不存在"
        fi
    done
}

# 测试：检查脚本依赖的命令
test_dependencies() {
    echo -e "\n${YELLOW}[额外] 检查系统依赖...${NC}"
    
    local commands=(
        "bash"
        "ssh"
        "curl"
    )
    
    for cmd in "${commands[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            record_test "命令可用: $cmd" "pass"
        else
            record_test "命令可用: $cmd" "fail" "命令未安装"
        fi
    done
}

# 生成测试摘要
generate_summary() {
    echo -e "\n${BLUE}======================================"
    echo "测试摘要"
    echo "======================================"${NC}
    echo "总测试数: $TOTAL_TESTS"
    echo "通过: $PASSED_TESTS"
    echo "失败: $FAILED_TESTS"
    
    # 计算成功率
    if [ $TOTAL_TESTS -gt 0 ]; then
        SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
        echo "成功率: $SUCCESS_RATE%"
    fi
    
    echo "======================================"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}✅ 所有测试通过${NC}"
        return 0
    else
        echo -e "${RED}❌ 部分测试失败${NC}"
        return 1
    fi
}

# 主执行流程
main() {
    echo "======================================"
    echo "  部署脚本自动测试"
    echo "======================================"
    echo ""
    
    test_script_files
    test_script_syntax
    test_script_permissions
    test_config_templates
    test_documentation
    test_dependencies
    
    echo ""
    generate_summary
}

main

