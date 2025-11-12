#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单稳定的HTTP服务器来托管AST测试页面
"""

import http.server
import socketserver
import os
import sys
import socket
from pathlib import Path

def find_free_port(start_port=8080):
    """查找可用端口"""
    for port in range(start_port, start_port + 20):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', port))
                if result != 0:  # 端口未被使用
                    return port
        except:
            continue
    return None

def main():
    """主函数"""
    # 切换到项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # 查找可用端口
    port = find_free_port(8080)
    if port is None:
        print("❌ 无法找到可用端口 (8080-8099)")
        sys.exit(1)
    
    print(f"📍 使用端口: {port}")
    
    # 自定义处理器
    class SimpleHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
        
        def log_message(self, format, *args):
            print(f"[HTTP] {format % args}")
    
    try:
        # 启动服务器
        with socketserver.TCPServer(("127.0.0.1", port), SimpleHandler) as httpd:
            print("=" * 60)
            print("🌐 AST测试页面Web服务器已启动")
            print(f"📍 服务地址: http://127.0.0.1:{port}")
            print(f"🎯 测试页面: http://127.0.0.1:{port}/AST_test_page.html")
            print("=" * 60)
            print("按 Ctrl+C 停止服务器")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n👋 Web服务器已停止")
    except Exception as e:
        print(f"❌ 服务器错误: {e}")

if __name__ == "__main__":
    main()