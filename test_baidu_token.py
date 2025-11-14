#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试百度access_token获取"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载.env文件
from dotenv import load_dotenv
env_path = project_root / "server" / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# 测试获取access_token
import requests

app_id = os.getenv("BAIDU_ASR_APP_ID")
api_key = os.getenv("BAIDU_ASR_API_KEY")
secret_key = os.getenv("BAIDU_ASR_SECRET_KEY")

print("=" * 80)
print("测试百度access_token获取")
print("=" * 80)
print(f"API Key: {api_key}")
print(f"Secret Key: {secret_key[:10]}...")

url = "https://aip.baidubce.com/oauth/2.0/token"
params = {
    "grant_type": "client_credentials",
    "client_id": api_key,
    "client_secret": secret_key
}

try:
    print("\n发送请求...")
    response = requests.get(url, params=params, timeout=10)
    print(f"HTTP Status: {response.status_code}")
    
    result = response.json()
    print(f"响应: {result}")
    
    if "access_token" in result:
        print(f"\n✅ 成功获取access_token:")
        print(f"   Token: {result['access_token'][:20]}...")
        print(f"   有效期: {result.get('expires_in')}秒")
    else:
        print(f"\n❌ 获取失败:")
        print(f"   错误: {result.get('error_description', '未知错误')}")
        
except Exception as e:
    print(f"\n❌ 请求异常: {e}")

print("=" * 80)

