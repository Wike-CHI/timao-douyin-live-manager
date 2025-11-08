#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端口配置验证脚本

功能:
1. 检查前后端.env文件是否存在
2. 验证必需的端口配置
3. 检查端口是否被占用
4. 生成配置报告

审查人: 叶维哲
"""

import os
import socket
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def check_port_available(port: int, service: str) -> bool:
    """检查端口是否可用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    
    if result == 0:
        print_error(f"{service} 端口 {port} 已被占用")
        return False
    else:
        print_success(f"{service} 端口 {port} 可用")
        return True

def check_env_file(env_path: str, required_vars: List[str], service_name: str) -> Tuple[bool, Dict[str, str]]:
    """检查.env文件是否存在且包含必需变量"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}📋 检查 {service_name} 配置{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # 检查文件是否存在
    if not Path(env_path).exists():
        print_error(f"配置文件不存在: {env_path}")
        print_warning(f"请创建 {env_path} 文件")
        return False, {}
    
    print_success(f"配置文件存在: {env_path}")
    
    # 加载配置
    try:
        # 手动解析.env文件,避免依赖dotenv
        config = {}
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        
        # 检查必需变量
        missing = [var for var in required_vars if var not in config or not config[var]]
        
        if missing:
            print_error(f"缺少必需配置: {', '.join(missing)}")
            return False, config
        else:
            print_success("所有必需配置都已设置")
            
            # 显示配置值
            for var in required_vars:
                print_info(f"  {var} = {config[var]}")
            
            return True, config
    
    except Exception as e:
        print_error(f"读取配置文件失败: {e}")
        return False, {}

def main():
    """主函数"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🔍 提猫直播助手 - 端口配置验证{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    
    # 配置路径
    backend_env = project_root / "server" / ".env"
    frontend_env = project_root / "electron" / "renderer" / ".env"
    
    # 验证结果
    all_valid = True
    
    # 1. 检查后端配置
    backend_required = ['BACKEND_PORT']
    backend_valid, backend_config = check_env_file(
        str(backend_env),
        backend_required,
        "后端服务"
    )
    all_valid = all_valid and backend_valid
    
    # 2. 检查前端配置
    frontend_required = ['VITE_PORT', 'VITE_FASTAPI_URL']
    frontend_valid, frontend_config = check_env_file(
        str(frontend_env),
        frontend_required,
        "前端开发服务器"
    )
    all_valid = all_valid and frontend_valid
    
    # 3. 检查端口占用
    if backend_valid and frontend_valid:
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🔌 检查端口占用情况{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        backend_port = int(backend_config.get('BACKEND_PORT', '11111'))
        frontend_port = int(frontend_config.get('VITE_PORT', '10050'))
        
        backend_port_ok = check_port_available(backend_port, "后端服务")
        frontend_port_ok = check_port_available(frontend_port, "前端开发服务器")
        
        all_valid = all_valid and backend_port_ok and frontend_port_ok
    
    # 4. 生成总结报告
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}📊 配置验证结果{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    if all_valid:
        print_success("所有配置验证通过！")
        print_info("后端服务端口: " + backend_config.get('BACKEND_PORT', 'N/A'))
        print_info("前端开发端口: " + frontend_config.get('VITE_PORT', 'N/A'))
        print()
        print_info("🚀 可以启动服务:")
        print_info("  后端: cd server && python app/main.py")
        print_info(f"  前端: cd electron/renderer && npm run dev")
        return 0
    else:
        print_error("配置验证失败，请检查上述错误")
        print()
        print_info("📖 参考文档: docs/PORT_CONFIGURATION.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())

