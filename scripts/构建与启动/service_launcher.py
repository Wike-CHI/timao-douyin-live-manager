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

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    # 加载项目根目录和 server 目录的 .env 文件
    project_root = Path(__file__).parent.parent.parent
    load_dotenv(project_root / ".env")
    load_dotenv(project_root / "server" / ".env")
except ImportError:
    print("⚠️ python-dotenv 未安装，将使用默认端口配置")
    print("提示：运行 pip install python-dotenv 来支持 .env 文件")

class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.services: Dict[str, subprocess.Popen] = {}
        self.running = False
        # 修正：从 scripts/构建与启动/ -> scripts -> 项目根目录
        self.base_dir = Path(__file__).parent.parent.parent
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
            
            # 启动进程（Windows 需要设置编码）
            process = subprocess.Popen(
                cmd,
                cwd=cwd or self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',  # 明确指定 UTF-8 编码
                errors='replace',  # 遇到无法解码的字符时替换
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
            try:
                for line in iter(process.stdout.readline, ''):
                    if line.strip():
                        # 尝试解码UTF-8，失败则忽略特殊字符
                        try:
                            self.logger.info(f"[{name}] {line.strip()}")
                        except UnicodeEncodeError:
                            self.logger.info(f"[{name}] {line.encode('utf-8', errors='replace').decode('utf-8').strip()}")
            except Exception as e:
                self.logger.error(f"[{name}] 输出监控异常: {e}")
        
        def monitor_stderr():
            try:
                for line in iter(process.stderr.readline, ''):
                    if line.strip():
                        # 错误输出更重要，必须显示
                        try:
                            self.logger.error(f"[{name}] 错误: {line.strip()}")
                        except UnicodeEncodeError:
                            self.logger.error(f"[{name}] 错误: {line.encode('utf-8', errors='replace').decode('utf-8').strip()}")
            except Exception as e:
                self.logger.error(f"[{name}] 错误监控异常: {e}")
        
        threading.Thread(target=monitor_stdout, daemon=True).start()
        threading.Thread(target=monitor_stderr, daemon=True).start()
    
    def start_all_services(self):
        """启动所有服务"""
        self.running = True
        self.logger.info("[START] 开始启动所有后端服务...")
        
        # 1. 启动主FastAPI服务
        # 🔧 硬编码端口 11111（演示测试）
        backend_port = "11111"
        fastapi_success = self.start_service(
            "fastapi_main",
            [sys.executable, "-m", "uvicorn", "server.app.main:app", 
             "--host", "127.0.0.1", "--port", backend_port, "--log-level", "info"],
            cwd=self.base_dir,
            expected_port=int(backend_port)
        )
        
        if fastapi_success:
            # 等待FastAPI服务启动（增加等待时间，确保数据库连接完成）
            self.logger.info("等待FastAPI服务启动...")
            time.sleep(10)  # 从5秒增加到10秒
        
        # 2. 启动StreamCap服务（已迁移到 server/modules/streamcap，不再需要独立启动）
        # StreamCap 功能已集成到主服务中，无需单独启动
        self.logger.info("StreamCap 功能已集成到主服务，跳过独立启动")
        
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
        # 🔧 硬编码端口 11111（演示测试）
        backend_port = "11111"
        services_to_check = [
            ("FastAPI主服务", f"http://127.0.0.1:{backend_port}/health"),
            # StreamCap 功能已集成到主服务中，无需单独检查
        ]
        
        for name, url in services_to_check:
            try:
                response = requests.get(url, timeout=10)  # 增加超时时间到10秒
                if response.status_code == 200:
                    self.logger.info(f"[OK] {name} 健康检查通过")
                else:
                    self.logger.warning(f"[WARN] {name} 健康检查异常: {response.status_code}")
            except requests.exceptions.ConnectionError as e:
                self.logger.error(f"[ERROR] {name} 连接失败（端口: {backend_port}）: {e}")
                self.logger.error(f"       请检查：1) 端口是否正确 2) 服务是否启动成功 3) 防火墙是否阻止")
                # 尝试重启服务
                self.restart_service_by_url(name, url)
            except requests.exceptions.Timeout as e:
                self.logger.error(f"[ERROR] {name} 连接超时: {e}")
                self.logger.error(f"       服务可能启动缓慢，建议检查日志")
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"[ERROR] {name} 健康检查失败: {e}")
                # 尝试重启服务
                self.restart_service_by_url(name, url)
    
    def restart_service_by_url(self, service_name: str, url: str):
        """根据URL重启对应服务"""
        # 🔧 硬编码端口 11111（演示测试）
        backend_port = "11111"
        if backend_port in url and "fastapi_main" in self.services:
            self.logger.info(f"尝试重启 {service_name}...")
            self.restart_service("fastapi_main")
        # StreamCap 功能已集成到主服务中，无需单独处理
    
    def restart_service(self, name: str):
        """重启指定服务"""
        if name in self.services:
            self.logger.info(f"正在重启服务: {name}")
            self.stop_service(name)
            time.sleep(2)
            
            # 根据服务名重新启动
            if name == "fastapi_main":
                # 🔧 硬编码端口 11111（演示测试）
                backend_port = "11111"
                self.start_service(
                    "fastapi_main",
                    [sys.executable, "-m", "uvicorn", "server.app.main:app", 
                     "--host", "127.0.0.1", "--port", backend_port, "--log-level", "info"],
                    cwd=self.base_dir,
                    expected_port=int(backend_port)
                )
            elif name == "streamcap":
                # StreamCap 功能已集成到主服务中，无需单独启动
                self.logger.info("StreamCap 功能已集成到主服务，无需单独启动")
    
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