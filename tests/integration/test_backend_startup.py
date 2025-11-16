#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端服务启动测试脚本
测试 FastAPI 服务是否正常启动并监听端口

审查人: 叶维哲
"""

import os
import sys
import time
import socket
import subprocess
import requests
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

class BackendStartupTest:
    """后端启动测试类"""
    
    def __init__(self):
        self.backend_port = int(os.getenv("BACKEND_PORT", "8080"))
        self.test_results = {
            "port_available": False,
            "service_started": False,
            "health_check_passed": False,
            "cors_enabled": False
        }
    
    def is_port_available(self, port: int) -> bool:
        """检查端口是否可用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return True
        except OSError:
            return False
    
    def is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex(('127.0.0.1', port))
                return result == 0
        except Exception:
            return False
    
    def test_port_availability(self) -> bool:
        """测试端口可用性"""
        print("\n" + "="*60)
        print("测试 1: 检查端口可用性")
        print("="*60)
        
        if self.is_port_available(self.backend_port):
            print_success(f"端口 {self.backend_port} 可用")
            self.test_results["port_available"] = True
            return True
        else:
            print_warning(f"端口 {self.backend_port} 已被占用")
            # 检查是否是 FastAPI 服务占用
            if self.is_port_in_use(self.backend_port):
                print_info("端口被占用，但可能是 FastAPI 服务")
                self.test_results["port_available"] = True
                return True
            return False
    
    def start_service(self) -> bool:
        """启动服务（如果未运行）"""
        print("\n" + "="*60)
        print("测试 2: 启动服务")
        print("="*60)
        
        # 检查服务是否已运行
        if self.is_port_in_use(self.backend_port):
            print_info("服务已经在运行")
            self.test_results["service_started"] = True
            return True
        
        print_info("服务未运行，尝试启动...")
        try:
            # 这里不实际启动服务，只是提示
            print_warning("请手动运行: npm run dev")
            print_info("或运行: python scripts/构建与启动/service_launcher.py")
            return False
        except Exception as e:
            print_error(f"启动服务失败: {e}")
            return False
    
    def test_health_check(self, max_retries: int = 5, retry_delay: int = 2) -> bool:
        """测试健康检查端点"""
        print("\n" + "="*60)
        print("测试 3: 健康检查")
        print("="*60)
        
        url = f"http://127.0.0.1:{self.backend_port}/health"
        
        for attempt in range(1, max_retries + 1):
            print_info(f"尝试连接 ({attempt}/{max_retries}): {url}")
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print_success("健康检查通过")
                    print_info(f"响应数据: {response.json()}")
                    self.test_results["health_check_passed"] = True
                    return True
                else:
                    print_warning(f"健康检查返回异常状态码: {response.status_code}")
            except requests.exceptions.ConnectionError as e:
                print_warning(f"连接失败: {e}")
                if attempt < max_retries:
                    print_info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
            except requests.exceptions.Timeout:
                print_warning("连接超时")
                if attempt < max_retries:
                    print_info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
            except Exception as e:
                print_error(f"请求失败: {e}")
                break
        
        print_error("健康检查失败")
        return False
    
    def test_cors(self) -> bool:
        """测试 CORS 配置"""
        print("\n" + "="*60)
        print("测试 4: CORS 配置")
        print("="*60)
        
        url = f"http://127.0.0.1:{self.backend_port}/api/cors-test"
        
        try:
            response = requests.get(
                url,
                headers={"Origin": "http://localhost:3000"},
                timeout=10
            )
            
            if response.status_code == 200:
                print_success("CORS 端点可访问")
                
                # 检查 CORS 响应头
                cors_headers = {
                    "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                    "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                    "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
                }
                
                print_info("CORS 响应头:")
                for header, value in cors_headers.items():
                    if value:
                        print(f"  {header}: {value}")
                
                if cors_headers["Access-Control-Allow-Origin"] == "*":
                    print_success("CORS 已正确配置（允许所有来源）")
                    self.test_results["cors_enabled"] = True
                    return True
                else:
                    print_warning("CORS 配置可能不完整")
                    return False
            else:
                print_error(f"CORS 测试端点返回异常状态码: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"CORS 测试失败: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print(f"\n{'='*60}")
        print("🧪 开始后端服务启动测试")
        print(f"{'='*60}")
        print_info(f"测试端口: {self.backend_port}")
        
        # 运行测试
        self.test_port_availability()
        self.start_service()
        health_ok = self.test_health_check()
        cors_ok = self.test_cors()
        
        # 输出测试结果
        print(f"\n{'='*60}")
        print("📊 测试结果汇总")
        print(f"{'='*60}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        for test_name, result in self.test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
        
        print(f"\n总计: {passed_tests}/{total_tests} 测试通过")
        
        if passed_tests == total_tests:
            print_success("\n所有测试通过！后端服务运行正常。")
            return True
        else:
            print_error("\n部分测试失败，请检查服务状态。")
            print_info("\n建议操作:")
            print("1. 检查日志: logs/service_manager.log")
            print("2. 手动启动: python -m uvicorn server.app.main:app --host 127.0.0.1 --port 8080")
            print("3. 运行诊断: node scripts/诊断与排障/check-backend-port.js")
            print("4. 查看排查指南: docs/问题排查/后端端口连接问题排查指南.md")
            return False

def main():
    """主函数"""
    # 加载环境变量
    try:
        from dotenv import load_dotenv
        project_root = Path(__file__).parent.parent.parent
        load_dotenv(project_root / ".env")
        load_dotenv(project_root / "server" / ".env")
    except ImportError:
        print_warning("python-dotenv 未安装，使用默认端口配置")
    
    # 运行测试
    tester = BackendStartupTest()
    success = tester.run_all_tests()
    
    # 返回退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

