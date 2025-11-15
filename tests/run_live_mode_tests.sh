#!/bin/bash

##############################################################################
# 直播控制台双模式功能测试运行脚本
#
# 测试文档：docs/产品使用手册/直播控制台双模式设计文档.md
# 审查人：叶维哲
# 创建日期：2025-11-15
##############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 打印标题
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  直播控制台双模式功能测试套件                           ║${NC}"
    echo -e "${BLUE}║  Reviewer: 叶维哲                                        ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# 打印分隔线
print_divider() {
    echo -e "${BLUE}─────────────────────────────────────────────────────────────${NC}"
}

# 打印成功信息
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# 打印错误信息
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 打印警告信息
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 打印信息
print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# 检查Python环境
check_python() {
    print_info "检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3未安装"
        exit 1
    fi
    
    python_version=$(python3 --version)
    print_success "Python环境正常: $python_version"
}

# 检查依赖
check_dependencies() {
    print_info "检查测试依赖..."
    
    if ! python3 -c "import pytest" 2>/dev/null; then
        print_warning "pytest未安装，正在安装..."
        pip install pytest pytest-cov pytest-html pytest-timeout
    fi
    
    print_success "依赖检查完成"
}

# 检查后端服务
check_backend() {
    print_info "检查后端服务状态..."
    
    if curl -s http://localhost:8090/api/health > /dev/null 2>&1; then
        print_success "后端服务运行正常"
        return 0
    else
        print_warning "后端服务未运行，部分API测试将被跳过"
        return 1
    fi
}

# 运行测试
run_tests() {
    local test_file=$1
    local test_name=$2
    
    print_divider
    echo -e "${BLUE}运行测试: $test_name${NC}"
    print_divider
    
    if [ -f "$test_file" ]; then
        pytest "$test_file" -v --tb=short --color=yes || {
            print_error "$test_name 测试失败"
            return 1
        }
        print_success "$test_name 测试通过"
    else
        print_error "测试文件不存在: $test_file"
        return 1
    fi
    
    echo ""
}

# 运行所有测试
run_all_tests() {
    local failed=0
    
    # 1. 高价值用户检测测试
    run_tests "tests/test_high_value_detection.py" "高价值用户检测" || ((failed++))
    
    # 2. 冷场检测测试
    run_tests "tests/test_silence_detection.py" "冷场检测" || ((failed++))
    
    # 3. 智能话术生成测试
    run_tests "tests/test_script_generation.py" "智能话术生成" || ((failed++))
    
    # 4. 信息轮播测试
    run_tests "tests/test_carousel.py" "信息轮播" || ((failed++))
    
    return $failed
}

# 生成测试报告
generate_report() {
    print_divider
    print_info "生成测试报告..."
    
    # 创建报告目录
    mkdir -p tests/reports
    
    # 生成HTML报告
    pytest tests/test_high_value_detection.py \
           tests/test_silence_detection.py \
           tests/test_script_generation.py \
           tests/test_carousel.py \
           --html=tests/reports/live_mode_test_report_$(date +%Y%m%d_%H%M%S).html \
           --self-contained-html \
           -v > /dev/null 2>&1 || true
    
    if [ -f tests/reports/live_mode_test_report_*.html ]; then
        print_success "测试报告已生成: tests/reports/"
    fi
}

# 显示使用帮助
show_help() {
    cat << EOF
使用方法: $0 [选项]

选项:
    all             运行所有测试（默认）
    high-value      只运行高价值用户检测测试
    silence         只运行冷场检测测试
    script          只运行话术生成测试
    carousel        只运行信息轮播测试
    report          运行测试并生成报告
    quick           快速测试（跳过性能测试）
    help            显示此帮助信息

示例:
    $0                  # 运行所有测试
    $0 high-value       # 只运行高价值用户检测测试
    $0 report           # 运行测试并生成报告
    $0 quick            # 快速测试

EOF
}

# 主函数
main() {
    print_header
    
    # 检查环境
    check_python
    check_dependencies
    check_backend
    
    echo ""
    print_divider
    
    # 解析参数
    case "${1:-all}" in
        all)
            print_info "运行所有测试..."
            echo ""
            run_all_tests
            failed=$?
            ;;
        high-value)
            run_tests "tests/test_high_value_detection.py" "高价值用户检测"
            failed=$?
            ;;
        silence)
            run_tests "tests/test_silence_detection.py" "冷场检测"
            failed=$?
            ;;
        script)
            run_tests "tests/test_script_generation.py" "智能话术生成"
            failed=$?
            ;;
        carousel)
            run_tests "tests/test_carousel.py" "信息轮播"
            failed=$?
            ;;
        report)
            print_info "运行测试并生成报告..."
            echo ""
            run_all_tests
            failed=$?
            generate_report
            ;;
        quick)
            print_info "快速测试（跳过性能测试）..."
            echo ""
            pytest tests/test_high_value_detection.py \
                   tests/test_silence_detection.py \
                   tests/test_script_generation.py \
                   tests/test_carousel.py \
                   -v -m "not performance" --tb=short
            failed=$?
            ;;
        help)
            show_help
            exit 0
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
    
    # 显示结果
    print_divider
    echo ""
    
    if [ $failed -eq 0 ]; then
        print_success "所有测试通过！🎉"
        echo ""
        exit 0
    else
        print_error "有 $failed 个测试失败"
        echo ""
        exit 1
    fi
}

# 运行主函数
main "$@"

