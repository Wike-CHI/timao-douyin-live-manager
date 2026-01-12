#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地模式修复验证脚本
测试纯本地模式下的各项功能
"""

import sys
import os
from pathlib import Path
import requests
import time

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class LocalModeTest:
    """本地模式测试"""
    
    def __init__(self):
        self.backend_port = 11111
        self.backend_url = f"http://127.0.0.1:{self.backend_port}"
        self.results = []
        
    def log(self, message: str, status: str = "INFO"):
        """记录日志"""
        icon = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️"
        }.get(status, "ℹ️")
        
        print(f"{icon} {message}")
        self.results.append((status, message))
    
    def test_backend_connection(self) -> bool:
        """测试后端连接"""
        self.log("测试后端连接...")
        
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                self.log("后端服务连接成功", "SUCCESS")
                return True
            else:
                self.log(f"后端服务返回异常状态: {response.status_code}", "ERROR")
                return False
        except requests.exceptions.ConnectionError:
            self.log("无法连接到后端服务，请确保服务已启动", "ERROR")
            return False
        except Exception as e:
            self.log(f"连接测试失败: {e}", "ERROR")
            return False
    
    def test_no_redis(self) -> bool:
        """测试Redis未启用"""
        self.log("检查Redis配置...")
        
        # 检查环境变量
        enable_redis = os.getenv("ENABLE_REDIS", "false").lower()
        
        if enable_redis == "false":
            self.log("Redis已禁用（纯本地模式）", "SUCCESS")
            return True
        else:
            self.log(f"Redis未禁用: ENABLE_REDIS={enable_redis}", "WARNING")
            return False
    
    def test_no_database(self) -> bool:
        """测试数据库未启用"""
        self.log("检查数据库配置...")
        
        # 检查环境变量
        enable_database = os.getenv("ENABLE_DATABASE", "false").lower()
        
        if enable_database == "false":
            self.log("数据库已禁用（纯本地模式）", "SUCCESS")
            return True
        else:
            self.log(f"数据库未禁用: ENABLE_DATABASE={enable_database}", "WARNING")
            return False
    
    def test_bootstrap_status(self) -> bool:
        """测试启动状态接口"""
        self.log("测试启动状态接口...")
        
        try:
            response = requests.get(f"{self.backend_url}/api/bootstrap/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log(f"启动状态: {data}", "SUCCESS")
                return True
            else:
                self.log(f"启动状态接口返回异常: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"启动状态测试失败: {e}", "ERROR")
            return False
    
    def test_port_config(self) -> bool:
        """测试端口配置工具"""
        self.log("测试端口配置工具...")
        
        try:
            from scripts.构建与启动.port_config import PortConfig
            
            config = PortConfig()
            backend_port = config.get_port("backend")
            
            if backend_port == self.backend_port:
                self.log(f"端口配置正确: {backend_port}", "SUCCESS")
                return True
            else:
                self.log(f"端口配置不匹配: 期望{self.backend_port}, 实际{backend_port}", "WARNING")
                return False
        except Exception as e:
            self.log(f"端口配置测试失败: {e}", "ERROR")
            return False
    
    def test_syntax_errors(self) -> bool:
        """测试语法错误修复"""
        self.log("检查语法错误修复...")
        
        try:
            # 尝试导入修复后的脚本
            from scripts.构建与启动.service_launcher import ServiceManager
            
            self.log("service_launcher.py 语法正确", "SUCCESS")
            return True
        except SyntaxError as e:
            self.log(f"语法错误: {e}", "ERROR")
            return False
        except Exception as e:
            self.log(f"导入失败: {e}", "WARNING")
            return True  # 其他错误不算语法错误
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("🧪 本地模式修复验证测试")
        print("=" * 60)
        print()
        
        tests = [
            ("语法错误修复", self.test_syntax_errors),
            ("端口配置", self.test_port_config),
            ("Redis配置", self.test_no_redis),
            ("数据库配置", self.test_no_database),
            ("后端连接", self.test_backend_connection),
            ("启动状态接口", self.test_bootstrap_status),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            print(f"\n📋 测试: {name}")
            print("-" * 40)
            
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"测试异常: {e}", "ERROR")
                failed += 1
        
        print("\n" + "=" * 60)
        print(f"📊 测试结果: {passed} 通过, {failed} 失败")
        print("=" * 60)
        
        return failed == 0


def main():
    """主函数"""
    tester = LocalModeTest()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

