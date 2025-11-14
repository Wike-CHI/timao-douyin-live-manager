#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
压力测试脚本
模拟多场直播同时运行，测试Redis批量入库和性能优化效果
"""

import asyncio
import json
import random
import time
from typing import List, Dict, Any
import aiohttp
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))


class StressTest:
    """压力测试类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: aiohttp.ClientSession = None
        self.results: Dict[str, Any] = {
            "start_time": None,
            "end_time": None,
            "duration_sec": 0,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time_ms": 0,
            "transcriptions_sent": 0,
            "comments_sent": 0,
            "errors": []
        }
    
    async def init(self):
        """初始化测试"""
        self.session = aiohttp.ClientSession()
        print("✅ 测试会话已初始化")
    
    async def cleanup(self):
        """清理测试"""
        if self.session:
            await self.session.close()
        print("✅ 测试会话已关闭")
    
    async def send_transcription(self, session_id: str, text: str) -> bool:
        """模拟发送转写结果"""
        try:
            data = {
                "type": "transcription",
                "text": text,
                "confidence": random.uniform(0.8, 0.98),
                "timestamp": int(time.time() * 1000),
                "is_final": True,
                "session_id": session_id
            }
            
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/api/test/transcription",
                json=data,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                duration_ms = (time.time() - start_time) * 1000
                
                self.results["total_requests"] += 1
                self.results["transcriptions_sent"] += 1
                
                if response.status == 200:
                    self.results["successful_requests"] += 1
                    return True
                else:
                    self.results["failed_requests"] += 1
                    error_text = await response.text()
                    self.results["errors"].append({
                        "type": "transcription",
                        "status": response.status,
                        "error": error_text[:100]
                    })
                    return False
        except Exception as e:
            self.results["total_requests"] += 1
            self.results["failed_requests"] += 1
            self.results["errors"].append({
                "type": "transcription",
                "error": str(e)[:100]
            })
            return False
    
    async def send_comment(self, live_id: str, content: str, user_id: str) -> bool:
        """模拟发送弹幕"""
        try:
            data = {
                "type": "chat",
                "payload": {
                    "user_id": user_id,
                    "nickname": f"用户{user_id}",
                    "content": content
                },
                "timestamp": time.time()
            }
            
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/api/test/comment",
                json=data,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                duration_ms = (time.time() - start_time) * 1000
                
                self.results["total_requests"] += 1
                self.results["comments_sent"] += 1
                
                if response.status == 200:
                    self.results["successful_requests"] += 1
                    return True
                else:
                    self.results["failed_requests"] += 1
                    return False
        except Exception as e:
            self.results["total_requests"] += 1
            self.results["failed_requests"] += 1
            self.results["errors"].append({
                "type": "comment",
                "error": str(e)[:100]
            })
            return False
    
    async def simulate_live_stream(
        self, 
        live_id: str, 
        duration_sec: int = 60,
        transcription_rate: float = 2.0,  # 每秒2条转写
        comment_rate: float = 10.0  # 每秒10条弹幕
    ):
        """模拟一场直播"""
        print(f"🔄 开始模拟直播 {live_id}...")
        
        start_time = time.time()
        tasks = []
        
        # 生成转写和弹幕任务
        transcription_interval = 1.0 / transcription_rate
        comment_interval = 1.0 / comment_rate
        
        # 转写任务
        async def send_transcriptions():
            elapsed = 0
            while elapsed < duration_sec:
                text = random.choice([
                    "大家好，欢迎来到直播间",
                    "今天给大家带来精彩内容",
                    "感谢各位的支持",
                    "这个产品真的很不错",
                    "有什么问题可以问我"
                ])
                await self.send_transcription(live_id, text)
                await asyncio.sleep(transcription_interval)
                elapsed = time.time() - start_time
        
        # 弹幕任务
        async def send_comments():
            elapsed = 0
            comment_templates = [
                "666", "主播牛逼", "支持支持", "点赞", "关注了",
                "这个好", "多少钱", "怎么买", "哈哈哈", "棒棒哒"
            ]
            while elapsed < duration_sec:
                content = random.choice(comment_templates)
                user_id = str(random.randint(10000, 99999))
                await self.send_comment(live_id, content, user_id)
                await asyncio.sleep(comment_interval)
                elapsed = time.time() - start_time
        
        # 并发执行
        await asyncio.gather(
            send_transcriptions(),
            send_comments()
        )
        
        print(f"✅ 直播 {live_id} 模拟完成")
    
    async def check_performance(self) -> Dict[str, Any]:
        """检查性能指标"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/performance/metrics",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"⚠️ 获取性能指标失败: {e}")
        
        return {}
    
    async def run_test(
        self,
        num_streams: int = 10,
        duration_sec: int = 60
    ):
        """运行压力测试"""
        print("=" * 60)
        print(f"  压力测试开始")
        print(f"  模拟直播数: {num_streams}")
        print(f"  测试时长: {duration_sec}秒")
        print("=" * 60)
        print()
        
        self.results["start_time"] = time.time()
        
        # 检查初始性能指标
        print("📊 初始性能指标...")
        initial_metrics = await self.check_performance()
        if initial_metrics:
            print(f"  MySQL连接数: {initial_metrics.get('mysql_active_connections', 'N/A')}")
            print(f"  Redis连接: {'✅' if initial_metrics.get('redis_connected') else '❌'}")
            print(f"  进程内存: {initial_metrics.get('process_memory_mb', 0):.1f}MB")
        print()
        
        # 并发模拟多场直播
        tasks = []
        for i in range(num_streams):
            live_id = f"test_live_{i+1}"
            tasks.append(self.simulate_live_stream(live_id, duration_sec))
        
        print(f"🚀 开始模拟 {num_streams} 场直播...\n")
        await asyncio.gather(*tasks)
        
        self.results["end_time"] = time.time()
        self.results["duration_sec"] = self.results["end_time"] - self.results["start_time"]
        
        # 检查最终性能指标
        print("\n📊 最终性能指标...")
        final_metrics = await self.check_performance()
        if final_metrics:
            print(f"  MySQL连接数: {final_metrics.get('mysql_active_connections', 'N/A')}")
            print(f"  Redis连接: {'✅' if final_metrics.get('redis_connected') else '❌'}")
            print(f"  进程内存: {final_metrics.get('process_memory_mb', 0):.1f}MB")
            print(f"  Redis内存: {final_metrics.get('redis_memory_used_mb', 0):.1f}MB")
        print()
        
        # 输出测试结果
        self.print_results()
        
        return self.results
    
    def print_results(self):
        """打印测试结果"""
        print("=" * 60)
        print("  压力测试结果")
        print("=" * 60)
        print()
        print(f"📈 请求统计:")
        print(f"  总请求数: {self.results['total_requests']}")
        print(f"  成功请求: {self.results['successful_requests']}")
        print(f"  失败请求: {self.results['failed_requests']}")
        success_rate = (self.results['successful_requests'] / max(1, self.results['total_requests'])) * 100
        print(f"  成功率: {success_rate:.2f}%")
        print()
        
        print(f"📊 数据统计:")
        print(f"  转写发送数: {self.results['transcriptions_sent']}")
        print(f"  弹幕发送数: {self.results['comments_sent']}")
        print()
        
        print(f"⏱️  性能统计:")
        print(f"  测试时长: {self.results['duration_sec']:.2f}秒")
        qps = self.results['total_requests'] / max(1, self.results['duration_sec'])
        print(f"  QPS: {qps:.2f}")
        print()
        
        if self.results['errors']:
            print(f"⚠️  错误统计 (显示前5个):")
            for i, error in enumerate(self.results['errors'][:5]):
                print(f"  {i+1}. {error}")
            print()
        
        # 评估结果
        print("=" * 60)
        print("  评估结果")
        print("=" * 60)
        
        if success_rate >= 95:
            print("✅ 优秀！成功率 >= 95%")
        elif success_rate >= 90:
            print("⚠️  良好，成功率 >= 90%")
        else:
            print("❌ 需要优化，成功率 < 90%")
        
        if qps >= 100:
            print("✅ 优秀！QPS >= 100")
        elif qps >= 50:
            print("⚠️  良好，QPS >= 50")
        else:
            print("❌ 需要优化，QPS < 50")
        
        print()


async def main():
    """主函数"""
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='压力测试脚本')
    parser.add_argument('--streams', type=int, default=10, help='模拟直播数（默认10）')
    parser.add_argument('--duration', type=int, default=60, help='测试时长（秒，默认60）')
    parser.add_argument('--url', type=str, default='http://localhost:8000', help='API地址')
    args = parser.parse_args()
    
    # 运行测试
    test = StressTest(base_url=args.url)
    await test.init()
    
    try:
        await test.run_test(
            num_streams=args.streams,
            duration_sec=args.duration
        )
    finally:
        await test.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

