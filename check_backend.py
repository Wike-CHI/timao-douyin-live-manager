#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的后端服务检查脚本
"""

import requests
import time

def check_backend_service():
    """检查后端服务"""
    print("🔍 检查后端服务...")
    
    for i in range(10):
        try:
            response = requests.get("http://localhost:10090", timeout=5)
            print(f"✅ 后端服务已启动，状态码: {response.status_code}")
            return True
        except:
            print(f"⏳ 等待后端服务启动... ({i+1}/10)")
            time.sleep(2)
    
    print("❌ 后端服务未启动")
    return False

if __name__ == "__main__":
    check_backend_service()