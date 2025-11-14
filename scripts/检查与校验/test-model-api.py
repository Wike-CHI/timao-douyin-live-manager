#!/usr/bin/env python3
"""
模型状态 API 自动测试脚本
审查人：叶维哲
"""

import sys
import json
import requests
from typing import Dict, Any

# 颜色定义
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'


class ModelAPITester:
    """模型 API 测试器"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:11111"):
        self.base_url = base_url
        self.tests_passed = 0
        self.tests_total = 0
    
    def print_header(self, text: str):
        """打印标题"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
        print(f"{Colors.BLUE}{text}{Colors.NC}")
        print(f"{Colors.BLUE}{'='*60}{Colors.NC}\n")
    
    def print_section(self, text: str):
        """打印章节"""
        print(f"\n{Colors.BLUE}=== {text} ==={Colors.NC}\n")
    
    def test_endpoint(self, name: str, endpoint: str, expected_keys: list[str]) -> bool:
        """测试 API 端点"""
        self.tests_total += 1
        try:
            url = f"{self.base_url}{endpoint}"
            print(f"{Colors.YELLOW}[{self.tests_total}] 测试: {name}{Colors.NC}")
            print(f"   URL: {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                print(f"{Colors.RED}   ❌ HTTP 状态码错误: {response.status_code}{Colors.NC}")
                return False
            
            data = response.json()
            
            # 检查必需的键
            missing_keys = [key for key in expected_keys if key not in data]
            if missing_keys:
                print(f"{Colors.RED}   ❌ 缺少字段: {', '.join(missing_keys)}{Colors.NC}")
                return False
            
            print(f"{Colors.GREEN}   ✅ 通过{Colors.NC}")
            print(f"   响应字段: {', '.join(data.keys())}")
            self.tests_passed += 1
            return True
            
        except requests.exceptions.ConnectionError:
            print(f"{Colors.RED}   ❌ 连接失败: 无法连接到服务器{Colors.NC}")
            return False
        except requests.exceptions.Timeout:
            print(f"{Colors.RED}   ❌ 超时: 服务器响应超时{Colors.NC}")
            return False
        except json.JSONDecodeError:
            print(f"{Colors.RED}   ❌ JSON 解析失败{Colors.NC}")
            return False
        except Exception as e:
            print(f"{Colors.RED}   ❌ 异常: {str(e)}{Colors.NC}")
            return False
    
    def test_model_status_details(self) -> bool:
        """测试模型状态详细信息"""
        self.tests_total += 1
        try:
            url = f"{self.base_url}/api/model/status"
            print(f"{Colors.YELLOW}[{self.tests_total}] 测试: 模型状态详细验证{Colors.NC}")
            
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"{Colors.RED}   ❌ HTTP 错误{Colors.NC}")
                return False
            
            data = response.json()
            
            # 验证模型信息
            if not data.get("sensevoice", {}).get("exists"):
                print(f"{Colors.YELLOW}   ⚠️  SenseVoice 模型文件不存在{Colors.NC}")
            else:
                size_mb = data["sensevoice"].get("size_mb", 0)
                print(f"{Colors.GREEN}   ✅ SenseVoice 存在 ({size_mb:.1f} MB){Colors.NC}")
            
            if not data.get("vad", {}).get("exists"):
                print(f"{Colors.YELLOW}   ⚠️  VAD 模型文件不存在{Colors.NC}")
            else:
                size_mb = data["vad"].get("size_mb", 0)
                print(f"{Colors.GREEN}   ✅ VAD 存在 ({size_mb:.1f} MB){Colors.NC}")
            
            # 验证配置
            vad_config = data.get("vad_config", {})
            if vad_config.get("chunk_sec"):
                print(f"{Colors.GREEN}   ✅ VAD 参数已配置{Colors.NC}")
            else:
                print(f"{Colors.YELLOW}   ⚠️  VAD 参数未配置{Colors.NC}")
            
            pytorch_config = data.get("pytorch_config", {})
            if pytorch_config.get("omp_threads"):
                print(f"{Colors.GREEN}   ✅ PyTorch 优化已配置{Colors.NC}")
            else:
                print(f"{Colors.YELLOW}   ⚠️  PyTorch 优化未配置{Colors.NC}")
            
            # 验证系统资源
            system = data.get("system", {})
            available_mem = system.get("available_memory_gb", 0)
            if available_mem >= 3.0:
                print(f"{Colors.GREEN}   ✅ 内存充足 ({available_mem:.2f} GB){Colors.NC}")
            else:
                print(f"{Colors.YELLOW}   ⚠️  内存紧张 ({available_mem:.2f} GB){Colors.NC}")
            
            # 显示警告
            warnings = data.get("warnings", [])
            if warnings:
                print(f"{Colors.YELLOW}   警告信息 ({len(warnings)} 条):{Colors.NC}")
                for warning in warnings:
                    print(f"      • {warning}")
            
            # 显示建议
            recommendations = data.get("recommendations", [])
            if recommendations:
                print(f"{Colors.BLUE}   建议 ({len(recommendations)} 条):{Colors.NC}")
                for rec in recommendations:
                    print(f"      • {rec}")
            
            self.tests_passed += 1
            return True
            
        except Exception as e:
            print(f"{Colors.RED}   ❌ 异常: {str(e)}{Colors.NC}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        self.print_header("模型状态 API 自动测试")
        
        # 1. 基础连接测试
        self.print_section("1. API 端点连接测试")
        
        # 测试健康检查端点
        self.test_endpoint(
            "健康检查端点",
            "/api/model/health",
            ["status", "timestamp", "checks"]
        )
        
        # 测试配置查询端点
        self.test_endpoint(
            "配置查询端点",
            "/api/model/config",
            ["status", "timestamp", "config"]
        )
        
        # 测试完整状态端点
        self.test_endpoint(
            "完整状态端点",
            "/api/model/status",
            ["status", "timestamp", "sensevoice", "vad", "system"]
        )
        
        # 2. 详细内容验证
        self.print_section("2. 模型状态详细验证")
        self.test_model_status_details()
        
        # 3. 显示总结
        self.print_summary()
    
    def print_summary(self):
        """打印测试总结"""
        self.print_header("测试总结")
        
        print(f"{Colors.BLUE}测试结果: {Colors.GREEN}{self.tests_passed}{Colors.NC}/{Colors.BLUE}{self.tests_total}{Colors.NC} 项通过\n")
        
        if self.tests_passed == self.tests_total:
            print(f"{Colors.GREEN}✅ 所有测试通过！API 运行正常。{Colors.NC}\n")
            print(f"{Colors.BLUE}可用的 API 端点:{Colors.NC}")
            print(f"  • {Colors.YELLOW}GET /api/model/status{Colors.NC}  - 完整的模型状态")
            print(f"  • {Colors.YELLOW}GET /api/model/health{Colors.NC}  - 简单健康检查")
            print(f"  • {Colors.YELLOW}GET /api/model/config{Colors.NC}  - 环境变量配置")
            print(f"\n{Colors.BLUE}使用示例:{Colors.NC}")
            print(f"  curl http://127.0.0.1:11111/api/model/status | python3 -m json.tool")
            return 0
        elif self.tests_passed > 0:
            print(f"{Colors.YELLOW}⚠️  部分测试通过。{Colors.NC}\n")
            print(f"{Colors.YELLOW}建议操作:{Colors.NC}")
            print(f"  1. 检查后端服务是否运行: pm2 list")
            print(f"  2. 查看后端日志: pm2 logs timao-backend")
            print(f"  3. 检查端口是否被占用: netstat -tulnp | grep 11111")
            return 1
        else:
            print(f"{Colors.RED}❌ 所有测试失败。{Colors.NC}\n")
            print(f"{Colors.RED}故障排除步骤:{Colors.NC}")
            print(f"  1. 确认后端服务已启动: pm2 list")
            print(f"  2. 确认端口正确: 11111")
            print(f"  3. 检查防火墙设置")
            print(f"  4. 查看详细日志: pm2 logs timao-backend --err")
            return 2


def main():
    """主函数"""
    tester = ModelAPITester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

