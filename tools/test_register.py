"""
测试用户注册功能
"""
import requests
import json
import sys
import random
import string

BASE_URL = "http://127.0.0.1:9019"

def generate_random_user():
    """生成随机测试用户数据"""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return {
        "username": f"test_{suffix}",
        "email": f"test_{suffix}@example.com",
        "password": "Test@123456",
        "phone": f"138{random.randint(10000000, 99999999)}",
        "nickname": f"测试用户_{suffix}"
    }

def test_register():
    """测试用户注册"""
    print("\n🧪 测试用户注册功能")
    print("=" * 60)
    
    # 生成测试用户数据
    user_data = generate_random_user()
    print(f"\n📝 生成测试用户数据:")
    print(f"   用户名: {user_data['username']}")
    print(f"   邮箱: {user_data['email']}")
    print(f"   昵称: {user_data['nickname']}")
    
    # 发送注册请求
    print(f"\n🚀 发送注册请求到: {BASE_URL}/api/auth/register")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=user_data,
            timeout=10
        )
        
        print(f"\n📊 响应状态码: {response.status_code}")
        print(f"📄 响应内容:")
        
        if response.status_code == 201:
            result = response.json()
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print("\n✅ 注册成功！")
            return True
        else:
            print(response.text)
            print(f"\n❌ 注册失败 (状态码: {response.status_code})")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器，请确保应用正在运行")
        print(f"   服务地址: {BASE_URL}")
        return False
    except requests.exceptions.Timeout:
        print("\n❌ 请求超时")
        return False
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_duplicate_register():
    """测试重复注册"""
    print("\n\n🧪 测试重复注册（预期失败）")
    print("=" * 60)
    
    # 使用固定用户名测试重复注册
    user_data = {
        "username": "duplicate_test",
        "email": "duplicate@example.com",
        "password": "Test@123456",
        "phone": "13800138000",
        "nickname": "重复测试"
    }
    
    print(f"\n📝 第一次注册...")
    response1 = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    print(f"状态码: {response1.status_code}")
    
    if response1.status_code == 201:
        print("✅ 第一次注册成功")
    else:
        print(f"已存在或其他错误: {response1.text}")
    
    print(f"\n📝 第二次注册（使用相同数据）...")
    response2 = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    print(f"状态码: {response2.status_code}")
    
    if response2.status_code == 400:
        error_data = response2.json()
        print(f"✅ 正确拒绝重复注册: {error_data.get('detail')}")
        return True
    else:
        print(f"❌ 未正确处理重复注册")
        return False

def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("🎯 用户注册功能测试")
    print("=" * 60)
    
    # 测试1: 正常注册
    success1 = test_register()
    
    # 测试2: 重复注册
    success2 = test_duplicate_register()
    
    # 总结
    print("\n\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"正常注册测试: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"重复注册测试: {'✅ 通过' if success2 else '❌ 失败'}")
    print("=" * 60)
    
    if success1 and success2:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n⚠️ 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
