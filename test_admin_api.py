# -*- coding: utf-8 -*-
"""测试管理员API"""
import requests
import json

BASE_URL = "http://127.0.0.1:9030"

# 1. 登录获取token
print("1. 登录...")
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={
        "username_or_email": "tc1102Admin",
        "password": "xjystimao1115"
    }
)
print(f"登录状态码: {login_response.status_code}")
if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"Token获取成功: {token[:50]}...")
else:
    print(f"登录失败: {login_response.text}")
    exit(1)

# 2. 测试获取用户列表
print("\n2. 获取用户列表...")
headers = {"Authorization": f"Bearer {token}"}

# 测试基本请求
response = requests.get(
    f"{BASE_URL}/api/admin/users?page=1&size=10",
    headers=headers
)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"返回数据结构: {list(data.keys())}")
    print(f"用户总数: {data.get('total', 0)}")
    print(f"用户列表长度: {len(data.get('data', []))}")
    if data.get('data'):
        print(f"第一个用户: {json.dumps(data['data'][0], indent=2, ensure_ascii=False)}")
else:
    print(f"请求失败: {response.text}")

# 3. 测试带筛选的请求
print("\n3. 测试带筛选的请求...")
response = requests.get(
    f"{BASE_URL}/api/admin/users?page=1&size=10&is_active=true",
    headers=headers
)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"激活用户数: {data.get('total', 0)}")
else:
    print(f"请求失败: {response.text}")

# 4. 测试支付列表
print("\n4. 测试支付列表...")
response = requests.get(
    f"{BASE_URL}/api/admin/payments?page=1&size=10",
    headers=headers
)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"支付记录总数: {data.get('total', 0)}")
else:
    print(f"请求失败: {response.text}")

print("\n测试完成!")
