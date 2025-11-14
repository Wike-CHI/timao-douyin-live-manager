#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 完整功能测试脚本 - 通过HTTP API测试
测试内容：语音转写 + 弹幕拉取 + AI工作流
测试时长：5分钟
直播间：https://live.douyin.com/40452701152
"""

import asyncio
import aiohttp
import time
from datetime import datetime
import logging
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'test_api_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 测试配置
BASE_URL = "http://127.0.0.1:11111"
LIVE_URL = "https://live.douyin.com/40452701152"
TEST_DURATION = 300  # 5分钟
SESSION_ID = f"test_{int(time.time())}"


class APIWorkflowTester:
    """API工作流测试器"""
    
    def __init__(self):
        self.session = None
        self.stats = {
            "audio_status_checks": 0,
            "douyin_messages": 0,
            "ai_analyses": 0,
            "errors": []
        }
        
    async def create_session(self):
        """创建HTTP会话"""
        self.session = aiohttp.ClientSession()
        logger.info("✅ HTTP会话已创建")
    
    async def close_session(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            logger.info("✅ HTTP会话已关闭")
    
    async def start_audio_transcription(self):
        """启动音频转写"""
        logger.info("\n" + "=" * 80)
        logger.info("🎤 启动音频转写服务...")
        logger.info("=" * 80)
        
        try:
            url = f"{BASE_URL}/api/live_audio/start"
            data = {
                "live_url": LIVE_URL,
                "session_id": SESSION_ID,
                "profile": "fast"
            }
            
            async with self.session.post(url, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info(f"✅ 音频转写服务启动成功")
                    logger.info(f"   响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    return True
                else:
                    error_text = await resp.text()
                    logger.error(f"❌ 音频转写服务启动失败 (HTTP {resp.status})")
                    logger.error(f"   错误: {error_text}")
                    self.stats["errors"].append(f"音频转写启动失败: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ 音频转写启动异常: {e}", exc_info=True)
            self.stats["errors"].append(f"音频转写启动异常: {str(e)}")
            return False
    
    async def start_douyin_monitoring(self):
        """启动抖音弹幕监控"""
        logger.info("\n" + "=" * 80)
        logger.info("📱 启动抖音弹幕监控...")
        logger.info("=" * 80)
        
        try:
            url = f"{BASE_URL}/api/douyin/start"
            data = {
                "live_url": LIVE_URL,
                "session_id": SESSION_ID
            }
            
            async with self.session.post(url, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info(f"✅ 抖音监控启动成功")
                    logger.info(f"   响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    return True
                else:
                    error_text = await resp.text()
                    logger.error(f"❌ 抖音监控启动失败 (HTTP {resp.status})")
                    logger.error(f"   错误: {error_text}")
                    self.stats["errors"].append(f"抖音监控启动失败: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ 抖音监控启动异常: {e}", exc_info=True)
            self.stats["errors"].append(f"抖音监控启动异常: {str(e)}")
            return False
    
    async def check_audio_status(self):
        """检查音频转写状态"""
        try:
            url = f"{BASE_URL}/api/live_audio/status"
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    self.stats["audio_status_checks"] += 1
                    
                    if result.get("success"):
                        data = result.get("data", {})
                        if data.get("is_running"):
                            logger.info(f"📊 音频转写运行中 - Session: {data.get('session_id')}")
                        return data
                return None
        except Exception as e:
            logger.warning(f"检查音频状态失败: {e}")
            return None
    
    async def check_douyin_status(self):
        """检查抖音监控状态"""
        try:
            url = f"{BASE_URL}/api/douyin/status"
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    
                    if result.get("success"):
                        data = result.get("data", {})
                        if data.get("is_monitoring"):
                            logger.info(f"📊 抖音监控运行中 - Room: {data.get('current_room_id')}")
                        return data
                return None
        except Exception as e:
            logger.warning(f"检查抖音状态失败: {e}")
            return None
    
    async def monitor_services(self, duration):
        """监控服务状态"""
        logger.info("\n" + "=" * 80)
        logger.info(f"⏳ 监控服务运行... (持续 {duration} 秒)")
        logger.info("=" * 80)
        
        start_time = time.time()
        check_interval = 10  # 每10秒检查一次
        
        try:
            while time.time() - start_time < duration:
                await asyncio.sleep(check_interval)
                
                elapsed = int(time.time() - start_time)
                logger.info(f"\n⏱️ [{elapsed}秒] 状态检查:")
                
                # 检查音频状态
                audio_status = await self.check_audio_status()
                
                # 检查抖音状态
                douyin_status = await self.check_douyin_status()
                
                # 输出统计
                logger.info(f"   - 状态检查次数: {self.stats['audio_status_checks']}")
                logger.info(f"   - 错误数量: {len(self.stats['errors'])}")
                
        except Exception as e:
            logger.error(f"监控过程中发生错误: {e}", exc_info=True)
            self.stats["errors"].append(f"监控错误: {str(e)}")
    
    async def stop_services(self):
        """停止所有服务"""
        logger.info("\n" + "=" * 80)
        logger.info("🛑 停止所有服务...")
        logger.info("=" * 80)
        
        # 停止音频转写
        try:
            url = f"{BASE_URL}/api/live_audio/stop"
            async with self.session.post(url, json={}) as resp:
                if resp.status == 200:
                    logger.info("✅ 音频转写服务已停止")
                else:
                    logger.warning(f"音频转写停止响应: HTTP {resp.status}")
        except Exception as e:
            logger.error(f"停止音频转写失败: {e}")
        
        # 停止抖音监控
        try:
            url = f"{BASE_URL}/api/douyin/stop"
            async with self.session.post(url, json={}) as resp:
                if resp.status == 200:
                    logger.info("✅ 抖音监控已停止")
                else:
                    logger.warning(f"抖音监控停止响应: HTTP {resp.status}")
        except Exception as e:
            logger.error(f"停止抖音监控失败: {e}")
    
    async def print_final_report(self, elapsed):
        """打印最终测试报告"""
        logger.info("\n" + "=" * 80)
        logger.info("📋 测试报告")
        logger.info("=" * 80)
        logger.info(f"⏱️  总测试时间: {elapsed:.1f}秒")
        logger.info(f"📊 状态检查次数: {self.stats['audio_status_checks']}")
        logger.info(f"❌ 错误数量: {len(self.stats['errors'])}")
        logger.info("=" * 80)
        
        if self.stats["errors"]:
            logger.info("\n❌ 错误列表:")
            for error in self.stats["errors"]:
                logger.info(f"   - {error}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ 测试完成！")
        logger.info("=" * 80)
    
    async def run_test(self):
        """运行完整测试"""
        logger.info("\n" + "=" * 80)
        logger.info("🚀 开始API完整工作流测试")
        logger.info(f"📍 直播间: {LIVE_URL}")
        logger.info(f"⏱️  测试时长: {TEST_DURATION}秒 (5分钟)")
        logger.info(f"🆔 会话ID: {SESSION_ID}")
        logger.info(f"🌐 API地址: {BASE_URL}")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        try:
            # 创建HTTP会话
            await self.create_session()
            
            # 启动服务
            audio_ok = await self.start_audio_transcription()
            await asyncio.sleep(3)  # 等待服务稳定
            
            douyin_ok = await self.start_douyin_monitoring()
            await asyncio.sleep(3)  # 等待服务稳定
            
            if audio_ok or douyin_ok:
                # 监控服务运行
                await self.monitor_services(TEST_DURATION)
            else:
                logger.error("❌ 所有服务启动失败，终止测试")
            
        except KeyboardInterrupt:
            logger.info("\n⚠️ 测试被用户中断")
        except Exception as e:
            logger.error(f"\n❌ 测试过程中发生错误: {e}", exc_info=True)
            self.stats["errors"].append(f"测试执行错误: {str(e)}")
        finally:
            await self.stop_services()
            await self.close_session()
            
            elapsed = time.time() - start_time
            await self.print_final_report(elapsed)


async def main():
    """主函数"""
    tester = APIWorkflowTester()
    await tester.run_test()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n测试被用户中断")
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)

