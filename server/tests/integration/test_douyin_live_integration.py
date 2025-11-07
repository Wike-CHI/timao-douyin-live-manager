# -*- coding: utf-8 -*-
"""
抖音直播间集成测试

测试目标直播间: https://live.douyin.com/191495446158
房间ID: 7569996511182932786
主播ID: 58994334334

测试时长: 5分钟
测试内容:
1. 直播监控启动/停止
2. 音频转写功能
3. AI实时分析
4. 直播报告生成
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any
import httpx


# 测试配置
TEST_DURATION_SECONDS = 300  # 5分钟
# 从环境变量读取后端端口,默认9030
BASE_URL = f"http://localhost:{os.getenv('BACKEND_PORT', '9030')}"
LIVE_ROOM_URL = "https://live.douyin.com/191495446158"
ROOM_ID = "7569996511182932786"
ANCHOR_ID = "58994334334"


class DouyinLiveIntegrationTest:
    """抖音直播间集成测试类"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
        self.session_id = None
        self.test_start_time = None
        self.test_results = {
            "监控启动": False,
            "音频转写": False,
            "AI分析": False,
            "直播报告": False,
            "监控停止": False,
        }
        self.errors = []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    async def test_1_start_douyin_monitoring(self) -> bool:
        """测试1: 启动抖音直播监控"""
        await self.log("=" * 60)
        await self.log("测试 1/5: 启动抖音直播监控")
        await self.log(f"直播间链接: {LIVE_ROOM_URL}")
        await self.log(f"房间ID: {ROOM_ID}")
        
        try:
            response = await self.client.post(
                "/api/douyin/start",
                json={
                    "live_url": LIVE_ROOM_URL,
                    "room_id": ROOM_ID,
                    "save_comments": True
                }
            )
            
            await self.log(f"响应状态: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                await self.log(f"响应数据: {data}")
                
                if data.get("success"):
                    await self.log("✅ 直播监控启动成功")
                    self.test_results["监控启动"] = True
                    return True
                else:
                    await self.log(f"❌ 监控启动失败: {data.get('message')}", "ERROR")
            else:
                await self.log(f"❌ HTTP错误: {response.status_code}", "ERROR")
                
        except Exception as e:
            await self.log(f"❌ 异常: {str(e)}", "ERROR")
            self.errors.append(f"监控启动异常: {str(e)}")
        
        return False
    
    async def test_2_start_audio_transcription(self) -> bool:
        """测试2: 启动音频转写"""
        await self.log("=" * 60)
        await self.log("测试 2/5: 启动音频转写")
        
        try:
            # 等待监控稳定
            await asyncio.sleep(5)
            
            response = await self.client.post(
                "/api/live/audio/start",
                json={
                    "room_id": ROOM_ID,
                    "language": "zh",
                    "enable_translation": False,
                    "save_to_db": True
                }
            )
            
            await self.log(f"响应状态: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    await self.log("✅ 音频转写启动成功")
                    self.test_results["音频转写"] = True
                    return True
                else:
                    await self.log(f"⚠️ 转写启动响应: {data.get('message')}", "WARN")
                    # 可能已经在运行，检查状态
                    return await self.check_audio_status()
            else:
                await self.log(f"❌ HTTP错误: {response.status_code}", "ERROR")
                
        except Exception as e:
            await self.log(f"❌ 异常: {str(e)}", "ERROR")
            self.errors.append(f"音频转写异常: {str(e)}")
        
        return False
    
    async def check_audio_status(self) -> bool:
        """检查音频转写状态"""
        try:
            response = await self.client.get("/api/live/audio/status")
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data", {}).get("is_running"):
                    await self.log("✅ 音频转写正在运行")
                    self.test_results["音频转写"] = True
                    return True
        except Exception as e:
            await self.log(f"⚠️ 状态检查异常: {str(e)}", "WARN")
        return False
    
    async def test_3_start_ai_analysis(self) -> bool:
        """测试3: 启动AI实时分析"""
        await self.log("=" * 60)
        await self.log("测试 3/5: 启动AI实时分析")
        
        try:
            # 等待一些转写内容
            await asyncio.sleep(10)
            
            response = await self.client.post(
                "/api/ai/live/start",
                json={
                    "room_id": ROOM_ID,
                    "analysis_interval": 30,  # 每30秒分析一次
                    "enable_sentiment": True,
                    "enable_topics": True
                }
            )
            
            await self.log(f"响应状态: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    await self.log("✅ AI分析启动成功")
                    self.test_results["AI分析"] = True
                    return True
                else:
                    await self.log(f"⚠️ AI分析响应: {data.get('message')}", "WARN")
                    return await self.check_ai_status()
            else:
                await self.log(f"❌ HTTP错误: {response.status_code}", "ERROR")
                
        except Exception as e:
            await self.log(f"❌ 异常: {str(e)}", "ERROR")
            self.errors.append(f"AI分析异常: {str(e)}")
        
        return False
    
    async def check_ai_status(self) -> bool:
        """检查AI分析状态"""
        try:
            response = await self.client.get("/api/ai/live/status")
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data", {}).get("is_running"):
                    await self.log("✅ AI分析正在运行")
                    self.test_results["AI分析"] = True
                    return True
        except Exception as e:
            await self.log(f"⚠️ 状态检查异常: {str(e)}", "WARN")
        return False
    
    async def test_4_monitor_and_collect_data(self):
        """测试4: 监控并收集数据（持续到5分钟）"""
        await self.log("=" * 60)
        await self.log("测试 4/5: 监控并收集数据")
        
        remaining_time = TEST_DURATION_SECONDS - (time.time() - self.test_start_time)
        await self.log(f"剩余测试时间: {int(remaining_time)}秒")
        
        # 每30秒检查一次状态
        check_interval = 30
        checks = int(remaining_time / check_interval)
        
        for i in range(checks):
            await asyncio.sleep(check_interval)
            elapsed = time.time() - self.test_start_time
            remaining = TEST_DURATION_SECONDS - elapsed
            
            await self.log(f"[进度 {i+1}/{checks}] 已运行: {int(elapsed)}秒, 剩余: {int(remaining)}秒")
            
            # 检查各个服务状态
            await self.check_all_status()
            
            if remaining <= check_interval:
                break
    
    async def check_all_status(self):
        """检查所有服务状态"""
        try:
            # 检查抖音监控
            response = await self.client.get("/api/douyin/status")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    status = data.get("data", {})
                    await self.log(f"  📊 抖音监控: {status.get('status', 'unknown')}")
            
            # 检查音频转写
            response = await self.client.get("/api/live/audio/status")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    status = data.get("data", {})
                    is_running = status.get("is_running", False)
                    segments_count = status.get("segments_count", 0)
                    await self.log(f"  🎤 音频转写: {'运行中' if is_running else '已停止'}, 片段数: {segments_count}")
            
            # 检查AI分析
            response = await self.client.get("/api/ai/live/status")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    status = data.get("data", {})
                    is_running = status.get("is_running", False)
                    analysis_count = status.get("analysis_count", 0)
                    await self.log(f"  🤖 AI分析: {'运行中' if is_running else '已停止'}, 分析次数: {analysis_count}")
                    
        except Exception as e:
            await self.log(f"  ⚠️ 状态检查异常: {str(e)}", "WARN")
    
    async def test_5_generate_report_and_stop(self) -> bool:
        """测试5: 生成报告并停止监控"""
        await self.log("=" * 60)
        await self.log("测试 5/5: 生成报告并停止监控")
        
        # 停止AI分析
        try:
            response = await self.client.post("/api/ai/live/stop")
            if response.status_code == 200:
                await self.log("  ✅ AI分析已停止")
        except Exception as e:
            await self.log(f"  ⚠️ 停止AI分析异常: {str(e)}", "WARN")
        
        # 停止音频转写
        try:
            response = await self.client.post("/api/live/audio/stop")
            if response.status_code == 200:
                await self.log("  ✅ 音频转写已停止")
        except Exception as e:
            await self.log(f"  ⚠️ 停止音频转写异常: {str(e)}", "WARN")
        
        # 生成直播报告
        try:
            await self.log("  📝 生成直播报告...")
            response = await self.client.post(
                "/api/live/report/start",
                json={
                    "room_id": ROOM_ID,
                    "generate_type": "auto"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    await self.log("  ✅ 直播报告生成成功")
                    self.test_results["直播报告"] = True
                else:
                    await self.log(f"  ⚠️ 报告生成响应: {data.get('message')}", "WARN")
            
            # 等待报告生成
            await asyncio.sleep(5)
            
        except Exception as e:
            await self.log(f"  ⚠️ 报告生成异常: {str(e)}", "WARN")
            self.errors.append(f"报告生成异常: {str(e)}")
        
        # 停止抖音监控
        try:
            response = await self.client.post("/api/douyin/stop")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    await self.log("  ✅ 直播监控已停止")
                    self.test_results["监控停止"] = True
                    return True
            
        except Exception as e:
            await self.log(f"  ❌ 停止监控异常: {str(e)}", "ERROR")
            self.errors.append(f"停止监控异常: {str(e)}")
        
        return False
    
    async def print_summary(self):
        """打印测试总结"""
        await self.log("=" * 60)
        await self.log("测试总结")
        await self.log("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        await self.log(f"\n📊 测试结果: {passed_tests}/{total_tests} 通过")
        await self.log("")
        
        for test_name, result in self.test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            await self.log(f"  {status} - {test_name}")
        
        if self.errors:
            await self.log(f"\n❌ 错误列表 ({len(self.errors)} 个):")
            for i, error in enumerate(self.errors, 1):
                await self.log(f"  {i}. {error}")
        
        test_duration = time.time() - self.test_start_time
        await self.log(f"\n⏱️  总测试时长: {int(test_duration)}秒 ({int(test_duration/60)}分{int(test_duration%60)}秒)")
        await self.log("=" * 60)
        
        return passed_tests == total_tests


@pytest.mark.asyncio
async def test_douyin_live_integration():
    """
    抖音直播间完整集成测试
    
    测试流程:
    1. 启动抖音直播监控
    2. 启动音频转写
    3. 启动AI实时分析
    4. 持续监控5分钟
    5. 生成报告并停止所有服务
    """
    
    async with DouyinLiveIntegrationTest() as test:
        test.test_start_time = time.time()
        
        # 打印测试信息
        await test.log("=" * 60)
        await test.log("抖音直播间集成测试")
        await test.log("=" * 60)
        await test.log(f"测试直播间: {LIVE_ROOM_URL}")
        await test.log(f"房间ID: {ROOM_ID}")
        await test.log(f"主播ID: {ANCHOR_ID}")
        await test.log(f"测试时长: {TEST_DURATION_SECONDS}秒 (5分钟)")
        await test.log(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        await test.log("")
        
        # 执行测试
        await test.test_1_start_douyin_monitoring()
        await test.test_2_start_audio_transcription()
        await test.test_3_start_ai_analysis()
        await test.test_4_monitor_and_collect_data()
        await test.test_5_generate_report_and_stop()
        
        # 打印总结
        all_passed = await test.print_summary()
        
        # 断言所有测试通过
        assert all_passed, f"部分测试失败，详情请查看日志"


# 独立运行脚本
async def main():
    """独立运行测试"""
    print("\n" + "=" * 60)
    print("抖音直播间集成测试 - 独立运行模式")
    print("=" * 60)
    print(f"目标直播间: {LIVE_ROOM_URL}")
    print(f"测试时长: {TEST_DURATION_SECONDS}秒 (5分钟)")
    print(f"后端服务: {BASE_URL}")
    print("=" * 60 + "\n")
    
    # 检查后端服务
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=5.0) as client:
            response = await client.get("/api/douyin/health")
            if response.status_code == 200:
                print("✅ 后端服务正常")
            else:
                print(f"⚠️  后端服务响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接到后端服务: {str(e)}")
        print(f"   请确保后端服务运行在 {BASE_URL}")
        return
    
    print("")
    
    # 运行测试
    await test_douyin_live_integration()


if __name__ == "__main__":
    asyncio.run(main())

