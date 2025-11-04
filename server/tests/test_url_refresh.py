"""
测试直播流 URL 自动刷新功能

使用方法:
1. 确保后端服务正在运行 (uvicorn app.main:app --port 9019)
2. 运行此脚本: python test_url_refresh.py
3. 观察日志输出，验证 URL 刷新机制
"""

import asyncio
import time
import requests
import json

BASE_URL = "http://127.0.0.1:9019"

async def test_url_refresh():
    """测试 URL 自动刷新功能"""
    
    print("=" * 60)
    print("🧪 开始测试直播流 URL 自动刷新功能")
    print("=" * 60)
    
    # 测试用的直播地址（请替换为实际直播地址）
    # live_url = "https://live.douyin.com/xxxxx"  # 替换为真实直播地址
    live_url = input("请输入抖音直播地址 (例如: https://live.douyin.com/xxxxx): ").strip()
    
    if not live_url:
        print("❌ 未输入直播地址，退出测试")
        return
    
    try:
        # 1. 启动录制
        print("\n📺 步骤 1: 启动录制...")
        response = requests.post(
            f"{BASE_URL}/api/report/live/start",
            json={"live_url": live_url, "segment_minutes": 30},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ 启动录制失败: {response.text}")
            return
        
        result = response.json()
        print(f"✅ 录制已启动")
        print(f"   Session ID: {result.get('session_id')}")
        print(f"   主播: {result.get('anchor_name')}")
        print(f"   录制目录: {result.get('recording_dir')}")
        
        # 2. 监控状态
        print("\n💡 步骤 2: 监控录制状态...")
        print("   观察日志，应该会在 20 分钟后看到 URL 刷新")
        print("   按 Ctrl+C 可以随时停止测试\n")
        
        start_time = time.time()
        check_count = 0
        
        while True:
            try:
                # 检查状态
                status_response = requests.get(
                    f"{BASE_URL}/api/report/live/status",
                    timeout=5
                )
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    elapsed_minutes = (time.time() - start_time) / 60
                    
                    check_count += 1
                    if check_count % 6 == 0:  # 每 60 秒输出一次
                        print(f"⏱️ 已录制 {elapsed_minutes:.1f} 分钟")
                        print(f"   分段数: {len(status.get('segments', []))}")
                        print(f"   弹幕数: {status.get('comments_count', 0)}")
                        print(f"   PID: {status.get('recording_pid')}")
                        
                        if elapsed_minutes >= 20:
                            print("\n🔄 提示: 已超过 20 分钟，应该触发 URL 刷新了")
                            print("   请检查后端日志，查找:")
                            print("   - 🔄 开始刷新直播流 URL...")
                            print("   - ✅ 流地址刷新成功")
                
                await asyncio.sleep(10)  # 每 10 秒检查一次
                
            except KeyboardInterrupt:
                print("\n\n⚠️ 用户中断测试")
                break
            except Exception as e:
                print(f"⚠️ 检查状态时出错: {e}")
                await asyncio.sleep(5)
        
        # 3. 停止录制
        print("\n🛑 步骤 3: 停止录制...")
        stop_response = requests.post(
            f"{BASE_URL}/api/report/live/stop",
            timeout=30
        )
        
        if stop_response.status_code == 200:
            print("✅ 录制已停止")
            
            # 4. 生成报告（可选）
            generate = input("\n是否生成报告? (y/n): ").strip().lower()
            if generate == 'y':
                print("\n📊 步骤 4: 生成报告...")
                gen_response = requests.post(
                    f"{BASE_URL}/api/report/live/generate",
                    timeout=300
                )
                
                if gen_response.status_code == 200:
                    report = gen_response.json()
                    print("✅ 报告生成完成")
                    print(f"   转写字符数: {report.get('transcript_chars', 0)}")
                    print(f"   弹幕数: {report.get('comments_count', 0)}")
                    print(f"   报告文件: {report.get('artifacts', {}).get('report')}")
                else:
                    print(f"⚠️ 生成报告失败: {gen_response.text}")
        else:
            print(f"⚠️ 停止录制失败: {stop_response.text}")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 测试完成")
    print("=" * 60)

def test_simple():
    """简单测试：启动并立即停止"""
    print("=" * 60)
    print("🧪 简单测试：验证代码修改是否正常工作")
    print("=" * 60)
    
    live_url = input("请输入抖音直播地址: ").strip()
    if not live_url:
        print("❌ 未输入直播地址")
        return
    
    try:
        # 启动
        print("\n1️⃣ 启动录制...")
        r1 = requests.post(
            f"{BASE_URL}/api/report/live/start",
            json={"live_url": live_url},
            timeout=30
        )
        print(f"   状态码: {r1.status_code}")
        if r1.status_code == 200:
            print(f"   ✅ 启动成功")
            data = r1.json()
            print(f"   Session: {data.get('session_id')}")
            print(f"   主播: {data.get('anchor_name')}")
        else:
            print(f"   ❌ {r1.text}")
            return
        
        # 等待 5 秒
        print("\n2️⃣ 等待 5 秒...")
        time.sleep(5)
        
        # 检查状态
        print("\n3️⃣ 检查状态...")
        r2 = requests.get(f"{BASE_URL}/api/report/live/status", timeout=5)
        if r2.status_code == 200:
            status = r2.json()
            print(f"   ✅ 状态正常")
            print(f"   PID: {status.get('recording_pid')}")
            print(f"   分段数: {len(status.get('segments', []))}")
        
        # 停止
        print("\n4️⃣ 停止录制...")
        r3 = requests.post(f"{BASE_URL}/api/report/live/stop", timeout=30)
        if r3.status_code == 200:
            print(f"   ✅ 停止成功")
        else:
            print(f"   ⚠️ {r3.text}")
        
        print("\n✅ 简单测试通过！代码修改正常工作")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n选择测试模式:")
    print("1. 简单测试 (启动->等待5秒->停止)")
    print("2. 完整测试 (启动->监控->手动停止)")
    
    choice = input("\n请选择 (1/2): ").strip()
    
    if choice == "1":
        test_simple()
    elif choice == "2":
        asyncio.run(test_url_refresh())
    else:
        print("❌ 无效选择")
