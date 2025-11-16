"""
测试云端服务启动和API
"""
import subprocess
import time
import requests
import sys

def test_cloud_service():
    print("=" * 60)
    print("🧪 测试云端服务")
    print("=" * 60)
    
    # 1. 测试导入
    print("\n1️⃣ 测试模块导入...")
    try:
        from server.cloud.main import app
        print("✅ 模块导入成功")
        print(f"   Routes: {len([r for r in app.routes if hasattr(r, 'path')])}")
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False
    
    # 2. 启动服务
    print("\n2️⃣ 启动云端服务...")
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "server.cloud.main:app", 
             "--host", "127.0.0.1", "--port", "15001", "--log-level", "error"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("✅ 服务进程已启动 (PID: {})".format(proc.pid))
        time.sleep(3)  # 等待服务启动
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False
    
    # 3. 测试API
    print("\n3️⃣ 测试/health端点...")
    try:
        r = requests.get("http://127.0.0.1:15001/health", timeout=5)
        print(f"✅ Status: {r.status_code}")
        print(f"   Response: {r.json()}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        proc.terminate()
        return False
    
    # 4. 测试根路径
    print("\n4️⃣ 测试/根端点...")
    try:
        r = requests.get("http://127.0.0.1:15001/", timeout=5)
        print(f"✅ Status: {r.status_code}")
        print(f"   Service: {r.json().get('service', 'N/A')}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        proc.terminate()
        return False
    
    # 5. 清理
    print("\n5️⃣ 关闭服务...")
    proc.terminate()
    proc.wait(timeout=5)
    print("✅ 服务已关闭")
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_cloud_service()
    sys.exit(0 if success else 1)
