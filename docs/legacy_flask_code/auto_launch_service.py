#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动启动语音转录服务脚本
此脚本将自动启动Flask服务器并在浏览器中打开服务页面
"""

import os
import sys
import subprocess
import webbrowser
import time
import threading
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def start_flask_server():
    """启动Flask服务器"""
    ast_module_dir = os.path.join(os.path.dirname(__file__), 'AST_module')
    server_script = os.path.join(ast_module_dir, 'test_server.py')
    
    if not os.path.exists(server_script):
        logger.error(f"服务器脚本不存在: {server_script}")
        return None
    
    try:
        logger.info("正在启动Flask服务器...")
        # 启动Flask服务器
        process = subprocess.Popen([sys.executable, server_script], 
                                 cwd=ast_module_dir,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        
        return process
            
    except Exception as e:
        logger.error(f"启动Flask服务器时发生错误: {e}")
        return None

def open_browser():
    """在浏览器中打开服务页面"""
    try:
        # 等待服务器启动
        time.sleep(3)
        logger.info("正在打开浏览器...")
        webbrowser.open('http://127.0.0.1:5000')
        logger.info("浏览器已打开")
        return True
    except Exception as e:
        logger.error(f"打开浏览器时发生错误: {e}")
        return False

def monitor_server(process):
    """监控服务器进程"""
    if process is None:
        return
    
    try:
        # 读取服务器输出
        while True:
            output = process.stdout.readline()
            if output:
                print(output.decode('utf-8').strip())
            
            # 检查进程是否仍在运行
            if process.poll() is not None:
                break
                
    except Exception as e:
        logger.error(f"监控服务器时发生错误: {e}")

def main():
    """主函数"""
    logger.info("开始自动启动语音转录服务")
    
    # 启动Flask服务器
    server_process = start_flask_server()
    
    if server_process is None:
        logger.error("无法启动Flask服务器")
        return False
    
    logger.info("Flask服务器已启动")
    
    # 在单独的线程中监控服务器
    monitor_thread = threading.Thread(target=monitor_server, args=(server_process,))
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # 打开浏览器
    open_browser()
    
    print("\n" + "="*50)
    print("语音转录服务已启动")
    print("请在浏览器中使用服务")
    print("按 Ctrl+C 停止服务")
    print("="*50)
    
    try:
        # 等待服务器进程结束
        server_process.wait()
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        if server_process:
            server_process.terminate()
            server_process.wait()
        print("服务已停止")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)