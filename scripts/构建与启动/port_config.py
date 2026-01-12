#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态端口配置管理
支持自动检测、端口冲突解决、配置持久化
"""

import os
import json
import socket
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple

logger = logging.getLogger(__name__)


class PortConfig:
    """端口配置管理器"""
    
    def __init__(self, config_file: str = "config/ports.json"):
        self.project_root = Path(__file__).parent.parent.parent
        self.config_file = self.project_root / config_file
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """加载端口配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载端口配置失败: {e}，使用默认配置")
        
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "ports": {
                "backend": {"default": 11111},
                "frontend": {"default": 10065},
                "websocket": {"default": 11112}
            },
            "environment": "development"
        }
    
    def save_config(self) -> bool:
        """保存配置"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"保存端口配置失败: {e}")
            return False
    
    def get_port(self, service: str) -> int:
        """
        获取服务端口
        
        优先级：环境变量 > 配置文件 > 默认值
        """
        # 1. 环境变量
        env_var = f"{service.upper()}_PORT"
        env_port = os.getenv(env_var)
        if env_port:
            try:
                return int(env_port)
            except ValueError:
                logger.warning(f"环境变量 {env_var} 值无效: {env_port}")
        
        # 2. 配置文件
        env = self.config.get("environment", "development")
        service_config = self.config.get("ports", {}).get(service, {})
        
        if env in service_config:
            return service_config[env]
        
        # 3. 默认值
        return service_config.get("default", 8000)
    
    def set_port(self, service: str, port: int, persist: bool = True) -> bool:
        """设置服务端口"""
        env = self.config.get("environment", "development")
        
        if "ports" not in self.config:
            self.config["ports"] = {}
        
        if service not in self.config["ports"]:
            self.config["ports"][service] = {}
        
        self.config["ports"][service][env] = port
        
        if persist:
            return self.save_config()
        
        return True
    
    def is_port_available(self, port: int, host: str = "127.0.0.1") -> bool:
        """检查端口是否可用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                return True
        except OSError:
            return False
    
    def find_available_port(self, start_port: int, max_attempts: int = 100) -> Optional[int]:
        """查找可用端口"""
        for port in range(start_port, start_port + max_attempts):
            if self.is_port_available(port):
                return port
        return None
    
    def check_and_resolve_conflicts(self) -> Dict[str, int]:
        """
        检查端口冲突并自动解决
        
        Returns:
            更新后的端口配置字典
        """
        resolved_ports = {}
        
        for service in ["backend", "frontend", "websocket"]:
            port = self.get_port(service)
            
            if not self.is_port_available(port):
                logger.warning(f"⚠️  端口 {port} ({service}) 已被占用，尝试查找替代端口...")
                new_port = self.find_available_port(port + 1)
                
                if new_port:
                    logger.info(f"✅ 为 {service} 分配新端口: {new_port}")
                    self.set_port(service, new_port, persist=False)
                    resolved_ports[service] = new_port
                else:
                    logger.error(f"❌ 无法为 {service} 找到可用端口")
                    resolved_ports[service] = port
            else:
                logger.info(f"✅ 端口 {port} ({service}) 可用")
                resolved_ports[service] = port
        
        return resolved_ports
    
    def get_all_ports(self) -> Dict[str, int]:
        """获取所有服务端口"""
        return {
            "backend": self.get_port("backend"),
            "frontend": self.get_port("frontend"),
            "websocket": self.get_port("websocket")
        }
    
    def export_env_file(self, output_path: Optional[Path] = None) -> bool:
        """导出为 .env 文件"""
        if output_path is None:
            output_path = self.project_root / ".env"
        
        try:
            ports = self.get_all_ports()
            
            env_content = [
                "# 动态端口配置（自动生成）",
                f"BACKEND_PORT={ports['backend']}",
                f"FRONTEND_PORT={ports['frontend']}",
                f"WEBSOCKET_PORT={ports['websocket']}",
                "",
                "# 纯本地模式配置",
                "ENABLE_REDIS=false",
                "ENABLE_DATABASE=false",
                ""
            ]
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(env_content))
            
            logger.info(f"✅ 端口配置已导出到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False


def main():
    """命令行工具"""
    import argparse
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="端口配置管理工具")
    parser.add_argument("--check", action="store_true", help="检查端口冲突")
    parser.add_argument("--resolve", action="store_true", help="解决端口冲突")
    parser.add_argument("--export", action="store_true", help="导出 .env 文件")
    parser.add_argument("--list", action="store_true", help="列出所有端口")
    parser.add_argument("--set", nargs=2, metavar=("SERVICE", "PORT"), help="设置端口")
    
    args = parser.parse_args()
    
    config = PortConfig()
    
    if args.check:
        print("🔍 检查端口配置...")
        ports = config.get_all_ports()
        for service, port in ports.items():
            available = config.is_port_available(port)
            status = "✅ 可用" if available else "❌ 被占用"
            print(f"  {service}: {port} - {status}")
    
    elif args.resolve:
        print("🔧 解决端口冲突...")
        resolved = config.check_and_resolve_conflicts()
        print("\n📋 解决结果:")
        for service, port in resolved.items():
            print(f"  {service}: {port}")
        config.save_config()
    
    elif args.export:
        print("📤 导出端口配置...")
        if config.export_env_file():
            print("✅ 配置已导出到 .env 文件")
        else:
            print("❌ 导出失败")
    
    elif args.list:
        print("📋 当前端口配置:")
        ports = config.get_all_ports()
        for service, port in ports.items():
            print(f"  {service}: {port}")
    
    elif args.set:
        service, port = args.set
        try:
            port = int(port)
            if config.set_port(service, port):
                print(f"✅ 已设置 {service} 端口为 {port}")
            else:
                print(f"❌ 设置失败")
        except ValueError:
            print(f"❌ 端口必须是数字")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

