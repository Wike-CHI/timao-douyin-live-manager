#!/usr/bin/env python3
"""
SenseVoice + VAD 模型配置自动测试脚本
审查人：叶维哲
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# 颜色定义
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


class ModelConfigTester:
    """模型配置测试器"""
    
    def __init__(self):
        self.project_root = Path("/www/wwwroot/wwwroot/timao-douyin-live-manager")
        self.tests_passed = 0
        self.tests_total = 0
        self.test_results: List[Tuple[str, bool, str]] = []
    
    def print_header(self, text: str):
        """打印标题"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
        print(f"{Colors.BLUE}{text}{Colors.NC}")
        print(f"{Colors.BLUE}{'='*60}{Colors.NC}\n")
    
    def print_section(self, text: str):
        """打印章节"""
        print(f"\n{Colors.BLUE}=== {text} ==={Colors.NC}\n")
    
    def run_test(self, test_name: str, test_func, expected_desc: str) -> bool:
        """运行单个测试"""
        self.tests_total += 1
        try:
            result = test_func()
            if result:
                print(f"{Colors.GREEN}✅ [{self.tests_total}] {test_name}: 通过{Colors.NC}")
                print(f"   {expected_desc}")
                self.tests_passed += 1
                self.test_results.append((test_name, True, expected_desc))
                return True
            else:
                print(f"{Colors.RED}❌ [{self.tests_total}] {test_name}: 失败{Colors.NC}")
                print(f"   {expected_desc}")
                self.test_results.append((test_name, False, expected_desc))
                return False
        except Exception as e:
            print(f"{Colors.RED}❌ [{self.tests_total}] {test_name}: 异常{Colors.NC}")
            print(f"   错误: {str(e)}")
            self.test_results.append((test_name, False, str(e)))
            return False
    
    def test_model_files_exist(self) -> bool:
        """测试模型文件是否存在"""
        sensevoice_path = self.project_root / "server/models/models/iic/SenseVoiceSmall/model.pt"
        return sensevoice_path.exists()
    
    def test_vad_files_exist(self) -> bool:
        """测试 VAD 文件是否存在"""
        vad_path = self.project_root / "server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/model.pt"
        return vad_path.exists()
    
    def test_ecosystem_config_exists(self) -> bool:
        """测试 ecosystem.config.js 是否存在"""
        config_path = self.project_root / "ecosystem.config.js"
        return config_path.exists()
    
    def test_ecosystem_has_model_env(self) -> bool:
        """测试 ecosystem.config.js 是否包含模型环境变量"""
        config_path = self.project_root / "ecosystem.config.js"
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return 'SENSEVOICE_MODEL_PATH' in content and 'VAD_MODEL_PATH' in content
    
    def test_ecosystem_has_vad_params(self) -> bool:
        """测试 ecosystem.config.js 是否包含 VAD 参数"""
        config_path = self.project_root / "ecosystem.config.js"
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return 'LIVE_VAD_CHUNK_SEC' in content and 'LIVE_VAD_MIN_SILENCE_SEC' in content
    
    def test_ecosystem_has_pytorch_config(self) -> bool:
        """测试 ecosystem.config.js 是否包含 PyTorch 配置"""
        config_path = self.project_root / "ecosystem.config.js"
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return 'OMP_NUM_THREADS' in content and 'MKL_NUM_THREADS' in content
    
    def test_ecosystem_memory_limit(self) -> bool:
        """测试 ecosystem.config.js 内存限制是否合理"""
        config_path = self.project_root / "ecosystem.config.js"
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 检查是否设置为 3G 或更高
        return "max_memory_restart: '3G'" in content or "max_memory_restart: '4G'" in content
    
    def test_pm2_process_running(self) -> bool:
        """测试 PM2 进程是否运行"""
        try:
            result = subprocess.run(['pm2', 'jlist'], capture_output=True, text=True)
            if result.returncode == 0:
                processes = json.loads(result.stdout)
                for proc in processes:
                    if proc.get('name') == 'timao-backend':
                        return proc.get('pm2_env', {}).get('status') == 'online'
            return False
        except Exception:
            return False
    
    def test_pm2_env_vars_loaded(self) -> bool:
        """测试 PM2 环境变量是否加载"""
        try:
            result = subprocess.run(['pm2', 'env', '0'], capture_output=True, text=True)
            if result.returncode == 0:
                return 'SENSEVOICE_MODEL_PATH' in result.stdout or 'VAD_MODEL_PATH' in result.stdout
            return False
        except Exception:
            return False
    
    def test_verify_script_exists(self) -> bool:
        """测试验证脚本是否存在"""
        script_path = self.project_root / "scripts/部署与运维/verify-model-config.sh"
        return script_path.exists() and os.access(script_path, os.X_OK)
    
    def test_documentation_exists(self) -> bool:
        """测试文档是否存在"""
        doc_path = self.project_root / "docs/SenseVoice模型配置指南.md"
        return doc_path.exists()
    
    def test_pm2_guide_updated(self) -> bool:
        """测试 PM2 使用指南是否更新"""
        guide_path = self.project_root / "docs/PM2使用指南.md"
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return 'SenseVoice + VAD 模型配置' in content
    
    def run_all_tests(self):
        """运行所有测试"""
        self.print_header("SenseVoice + VAD 模型配置自动测试")
        
        # 1. 模型文件测试
        self.print_section("1. 模型文件检查")
        self.run_test(
            "SenseVoice 模型文件",
            self.test_model_files_exist,
            "model.pt 文件应存在（~2.3GB）"
        )
        self.run_test(
            "VAD 模型文件",
            self.test_vad_files_exist,
            "model.pt 文件应存在（~140MB）"
        )
        
        # 2. 配置文件测试
        self.print_section("2. 配置文件检查")
        self.run_test(
            "ecosystem.config.js 存在",
            self.test_ecosystem_config_exists,
            "配置文件应存在"
        )
        self.run_test(
            "模型环境变量配置",
            self.test_ecosystem_has_model_env,
            "应包含 SENSEVOICE_MODEL_PATH 和 VAD_MODEL_PATH"
        )
        self.run_test(
            "VAD 参数配置",
            self.test_ecosystem_has_vad_params,
            "应包含 LIVE_VAD_CHUNK_SEC 等参数"
        )
        self.run_test(
            "PyTorch 配置",
            self.test_ecosystem_has_pytorch_config,
            "应包含 OMP_NUM_THREADS 和 MKL_NUM_THREADS"
        )
        self.run_test(
            "内存限制配置",
            self.test_ecosystem_memory_limit,
            "应设置为 3G 或更高"
        )
        
        # 3. PM2 运行状态测试
        self.print_section("3. PM2 运行状态检查")
        self.run_test(
            "PM2 进程运行",
            self.test_pm2_process_running,
            "timao-backend 应处于 online 状态"
        )
        self.run_test(
            "环境变量已加载",
            self.test_pm2_env_vars_loaded,
            "PM2 应加载模型环境变量"
        )
        
        # 4. 工具和文档测试
        self.print_section("4. 工具和文档检查")
        self.run_test(
            "验证脚本存在",
            self.test_verify_script_exists,
            "verify-model-config.sh 应存在且可执行"
        )
        self.run_test(
            "配置指南存在",
            self.test_documentation_exists,
            "SenseVoice模型配置指南.md 应存在"
        )
        self.run_test(
            "PM2 使用指南已更新",
            self.test_pm2_guide_updated,
            "应包含模型配置章节"
        )
        
        # 显示总结
        self.print_summary()
    
    def print_summary(self):
        """打印测试总结"""
        self.print_header("测试总结")
        
        print(f"{Colors.BLUE}测试结果: {Colors.GREEN}{self.tests_passed}{Colors.NC}/{Colors.BLUE}{self.tests_total}{Colors.NC} 项通过\n")
        
        # 显示失败的测试
        failed_tests = [r for r in self.test_results if not r[1]]
        if failed_tests:
            print(f"{Colors.RED}失败的测试:{Colors.NC}")
            for name, _, desc in failed_tests:
                print(f"  ❌ {name}")
                print(f"     {desc}")
            print()
        
        # 给出建议
        if self.tests_passed == self.tests_total:
            print(f"{Colors.GREEN}✅ 所有测试通过！模型配置完成。{Colors.NC}\n")
            print(f"{Colors.BLUE}下一步操作:{Colors.NC}")
            print(f"  1. 运行验证脚本: {Colors.YELLOW}./scripts/部署与运维/verify-model-config.sh{Colors.NC}")
            print(f"  2. 查看服务日志: {Colors.YELLOW}pm2 logs timao-backend{Colors.NC}")
            print(f"  3. 测试 API: {Colors.YELLOW}curl http://127.0.0.1:11111/health{Colors.NC}")
            return 0
        elif self.tests_passed > self.tests_total * 0.7:
            print(f"{Colors.YELLOW}⚠️  大部分测试通过，但仍有问题需要修复。{Colors.NC}\n")
            print(f"{Colors.YELLOW}建议操作:{Colors.NC}")
            print(f"  1. 检查失败的测试项")
            print(f"  2. 重新加载 PM2 配置: {Colors.YELLOW}pm2 delete timao-backend && pm2 start ecosystem.config.js{Colors.NC}")
            print(f"  3. 查看详细日志: {Colors.YELLOW}pm2 logs timao-backend --err{Colors.NC}")
            return 1
        else:
            print(f"{Colors.RED}❌ 多项测试失败，需要重新配置。{Colors.NC}\n")
            print(f"{Colors.RED}故障排除步骤:{Colors.NC}")
            print(f"  1. 确认模型文件已下载")
            print(f"  2. 检查 ecosystem.config.js 配置")
            print(f"  3. 重新启动服务: {Colors.YELLOW}pm2 restart timao-backend --update-env{Colors.NC}")
            print(f"  4. 查看文档: {Colors.YELLOW}docs/SenseVoice模型配置指南.md{Colors.NC}")
            return 2


def main():
    """主函数"""
    tester = ModelConfigTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

