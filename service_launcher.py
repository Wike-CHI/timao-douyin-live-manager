#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提猫直播助手 - 统一服务启动器
"""

import os
import sys
import time
import signal
import logging
import subprocess
import threading
import socket
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.services: Dict[str, subprocess.Popen] = {}
        self.running = False
        self.base_dir = Path(__file__).parent
        self.health_check_thread = None
        
        # 配置日志
        self.setup_logging()
        
    def setup_logging(self):
        """配置日志系统"""
        log_dir = self.base_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 创建自定义的StreamHandler，支持UTF-8编码
        class UTF8StreamHandler(logging.StreamHandler):
            def __init__(self, stream=None):
                super().__init__(stream)
                if hasattr(self.stream, 'reconfigure'):
                    try:
                        self.stream.reconfigure(encoding='utf-8')
                    except:
                        pass
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "service_manager.log", encoding='utf-8'),
                UTF8StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("ServiceManager")
        
    def find_free_port(self, start_port: int, max_attempts: int = 100) -> Optional[int]:
        """查找可用端口"""
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                continue
        return None
    
    def is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return False
        except OSError:
            return True
    
    def start_service(self, name: str, cmd: List[str], cwd: Optional[str] = None, 
                     expected_port: Optional[int] = None) -> bool:
        """启动单个服务"""
        try:
            # 检查端口冲突
            if expected_port and self.is_port_in_use(expected_port):
                self.logger.warning(f"端口 {expected_port} 已被占用，尝试查找替代端口...")
                new_port = self.find_free_port(expected_port + 1)
                if new_port:
                    self.logger.info(f"为服务 {name} 分配新端口: {new_port}")
                    # 更新命令中的端口参数
                    cmd = [arg.replace(str(expected_port), str(new_port)) if str(expected_port) in arg else arg for arg in cmd]
                else:
                    self.logger.error(f"无法为服务 {name} 找到可用端口")
                    return False
            
            # 启动进程
            process = subprocess.Popen(
                cmd,
                cwd=cwd or self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            self.services[name] = process
            self.logger.info(f"[OK] 服务 {name} 已启动 (PID: {process.pid})")
            
            # 启动输出监控线程
            self.start_output_monitor(name, process)
            
            return True
            
        except Exception as e:
            self.logger.error(f"[ERROR] 启动服务 {name} 失败: {e}")
            return False
    
    def start_output_monitor(self, name: str, process: subprocess.Popen):
        """启动输出监控线程"""
        def monitor_stdout():
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    self.logger.info(f"[{name}] {line.strip()}")
        
        def monitor_stderr():
            for line in iter(process.stderr.readline, ''):
                if line.strip():
                    self.logger.error(f"[{name}] {line.strip()}")
        
        threading.Thread(target=monitor_stdout, daemon=True).start()
        threading.Thread(target=monitor_stderr, daemon=True).start()
    
    def start_all_services(self):
        """启动所有服务"""
        self.running = True
        self.logger.info("[START] 开始启动所有后端服务...")
        
        # 1. 启动主FastAPI服务
        fastapi_success = self.start_service(
            "fastapi_main",
            [sys.executable, "-m", "uvicorn", "server.app.main:app", 
             "--host", "127.0.0.1", "--port", "9019", "--log-level", "info"],
            cwd=self.base_dir,
            expected_port=9019
        )
        
        if fastapi_success:
            # 等待FastAPI服务启动
            self.logger.info("等待FastAPI服务启动...")
            time.sleep(5)
        
        # 2. 启动StreamCap服务
        streamcap_path = self.base_dir / "StreamCap" / "main.py"
        if streamcap_path.exists():
            streamcap_success = self.start_service(
                "streamcap",
                [sys.executable, str(streamcap_path), "--web", "--port", "6006"],
                cwd=self.base_dir / "StreamCap",
                expected_port=6006
            )
            
            if streamcap_success:
                self.logger.info("等待StreamCap服务启动...")
                time.sleep(3)
        else:
            self.logger.warning("StreamCap服务未找到，跳过启动")
        
        # 3. 启动健康检查
        self.start_health_monitor()
        
        self.logger.info("[OK] 所有服务启动完成")
        
    def start_health_monitor(self):
        """启动健康检查监控"""
        def health_monitor():
            while self.running:
                try:
                    self.health_check()
                    time.sleep(30)  # 每30秒检查一次
                except Exception as e:
                    self.logger.error(f"健康检查异常: {e}")
                    time.sleep(10)
        
        self.health_check_thread = threading.Thread(target=health_monitor, daemon=True)
        self.health_check_thread.start()
        
    def health_check(self):
        """健康检查"""
        services_to_check = [
            ("FastAPI主服务", "http://127.0.0.1:9019/health"),
            ("StreamCap服务", "http://127.0.0.1:6006/health"),
        ]
        
        for name, url in services_to_check:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.logger.debug(f"[OK] {name} 健康检查通过")
                else:
                    self.logger.warning(f"[WARN] {name} 健康检查异常: {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"[ERROR] {name} 健康检查失败: {e}")
                # 尝试重启服务
                self.restart_service_by_url(name, url)
    
    def restart_service_by_url(self, service_name: str, url: str):
        """根据URL重启对应服务"""
        if "9019" in url and "fastapi_main" in self.services:
            self.logger.info(f"尝试重启 {service_name}...")
            self.restart_service("fastapi_main")
        elif "6006" in url and "streamcap" in self.services:
            self.logger.info(f"尝试重启 {service_name}...")
            self.restart_service("streamcap")
    
    def restart_service(self, name: str):
        """重启指定服务"""
        if name in self.services:
            self.logger.info(f"正在重启服务: {name}")
            self.stop_service(name)
            time.sleep(2)
            
            # 根据服务名重新启动
            if name == "fastapi_main":
                self.start_service(
                    "fastapi_main",
                    [sys.executable, "-m", "uvicorn", "server.app.main:app", 
                     "--host", "127.0.0.1", "--port", "9019", "--log-level", "info"],
                    cwd=self.base_dir,
                    expected_port=9019
                )
            elif name == "streamcap":
                streamcap_path = self.base_dir / "StreamCap" / "main.py"
                if streamcap_path.exists():
                    self.start_service(
                        "streamcap",
                        [sys.executable, str(streamcap_path), "--web", "--port", "6006"],
                        cwd=self.base_dir / "StreamCap",
                        expected_port=6006
                    )
    
    def stop_service(self, name: str):
        """停止指定服务"""
        if name in self.services:
            process = self.services[name]
            try:
                if os.name == 'nt':
                    # Windows系统
                    process.terminate()
                else:
                    # Unix系统
                    process.terminate()
                
                process.wait(timeout=10)
                self.logger.info(f"[OK] 服务 {name} 已停止")
            except subprocess.TimeoutExpired:
                process.kill()
                self.logger.warning(f"[WARN] 强制终止服务 {name}")
            except Exception as e:
                self.logger.error(f"[ERROR] 停止服务 {name} 失败: {e}")
            finally:
                del self.services[name]
    
    def stop_all_services(self):
        """停止所有服务"""
        self.running = False
        self.logger.info("正在停止所有服务...")
        
        # 停止健康检查线程
        if self.health_check_thread and self.health_check_thread.is_alive():
            self.health_check_thread.join(timeout=5)
        
        # 停止所有服务
        for name in list(self.services.keys()):
            self.stop_service(name)
        
        self.logger.info("[OK] 所有服务已停止")
    
    def get_service_status(self) -> Dict[str, Dict]:
        """获取服务状态"""
        status = {}
        for name, process in self.services.items():
            status[name] = {
                "pid": process.pid,
                "running": process.poll() is None,
                "returncode": process.returncode
            }
        return status

def signal_handler(signum, frame):
    """信号处理器"""
    logging.info("收到停止信号，正在关闭服务...")
    if 'service_manager' in globals():
        service_manager.stop_all_services()
    sys.exit(0)

def main():
    """主函数"""
    global service_manager
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动服务管理器
    service_manager = ServiceManager()
    
    try:
        service_manager.start_all_services()
        
        # 保持运行
        while service_manager.running:
            time.sleep(1)
            
            # 检查服务进程状态
            for name, process in list(service_manager.services.items()):
                if process.poll() is not None:
                    service_manager.logger.error(f"服务 {name} 意外退出 (返回码: {process.returncode})")
                    # 自动重启
                    service_manager.restart_service(name)
            
    except KeyboardInterrupt:
        service_manager.logger.info("用户中断，正在关闭服务...")
    except Exception as e:
        service_manager.logger.error(f"服务管理器异常: {e}")
    finally:
        service_manager.stop_all_services()

if __name__ == "__main__":
    main()