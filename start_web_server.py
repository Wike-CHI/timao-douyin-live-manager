#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的HTTP服务器来托管AST测试页面
"""

import http.server
import socketserver
import os
import logging
import socket
from pathlib import Path

def find_free_port(start_port=8080, max_attempts=10):
    """查找可用端口"""
    for i in range(max_attempts):
        port = start_port + i
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise OSError("无法找到可用端口")

def start_web_server(port=None):
    """启动简单的Web服务器"""
    
    # 如果没有指定端口，自动查找可用端口
    if port is None:
        try:
            port = find_free_port(8080)
            logging.info(f"自动选择可用端口: {port}")
        except OSError as e:
            logging.error(f"无法找到可用端口: {e}")
            return
    
    # 切换到项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建HTTP处理器
    class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            # 添加CORS头 - 限制为本地开发环境
            self.send_header('Access-Control-Allow-Origin', 'http://127.0.0.1:30013')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
        
        def log_message(self, format, *args):
            # 自定义日志格式
            logging.info(f"HTTP: {format % args}")
    
    try:
        with socketserver.TCPServer(("127.0.0.1", port), CustomHTTPRequestHandler) as httpd:
            logging.info("=" * 60)
            logging.info("🌐 AST测试页面Web服务器已启动")
            logging.info(f"📍 服务地址: http://127.0.0.1:{port}")
            logging.info(f"🎯 测试页面: http://127.0.0.1:{port}/AST_test_page.html")
            logging.info("=" * 60)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        logging.info("👋 Web服务器已停止")
    except Exception as e:
        logging.error(f"❌ Web服务器启动失败: {e}")

if __name__ == "__main__":
    start_web_server()  # 不传递端口，让函数自动查找