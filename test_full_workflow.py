#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整功能测试脚本 - 绕过API认证直接测试服务
测试内容：语音转写 + 弹幕拉取 + AI工作流
测试时长：5分钟
直播间：https://live.douyin.com/40452701152
"""

import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime
import logging

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'test_workflow_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 测试配置
LIVE_URL = "https://live.douyin.com/40452701152"
TEST_DURATION = 300  # 5分钟
SESSION_ID = f"test_{int(time.time())}"


class WorkflowTester:
    """完整工作流测试器"""
    
    def __init__(self):
        self.audio_service = None
        self.douyin_service = None
        self.ai_analyzer = None
        self.stats = {
            "audio_transcripts": [],
            "douyin_messages": [],
            "ai_analyses": [],
            "errors": []
        }
        
    async def setup_services(self):
        """初始化所有服务"""
        logger.info("=" * 80)
        logger.info("开始初始化服务...")
        logger.info("=" * 80)
        
        try:
            # 1. 获取音频转写服务（会自动初始化数据库）
            logger.info("🎤 获取音频转写服务...")
            from server.app.services.live_audio_stream_service import get_live_audio_service
            self.audio_service = get_live_audio_service()
            logger.info("✅ 音频转写服务已加载")
            
            # 2. 获取抖音服务
            logger.info("📱 获取抖音服务...")
            from server.app.services.douyin_web_relay import get_douyin_web_relay
            self.douyin_service = get_douyin_web_relay()
            logger.info("✅ 抖音服务已加载")
            
            # 3. 获取AI分析服务
            logger.info("🤖 获取AI分析服务...")
            from server.app.services.ai_live_analyzer import get_ai_live_analyzer
            self.ai_analyzer = get_ai_live_analyzer()
            logger.info("✅ AI分析服务已加载")
            
            logger.info("=" * 80)
            logger.info("✅ 所有服务初始化完成")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ 服务初始化失败: {e}", exc_info=True)
            self.stats["errors"].append(f"服务初始化失败: {str(e)}")
            raise
    
    async def start_audio_transcription(self):
        """启动音频转写"""
        logger.info("\n" + "=" * 80)
        logger.info("🎤 启动音频转写服务...")
        logger.info("=" * 80)
        
        try:
            # 注册转写回调
            def on_transcript(transcript_data):
                text = transcript_data.get("text", "")
                if text.strip():
                    logger.info(f"📝 [音频转写] {text}")
                    self.stats["audio_transcripts"].append({
                        "time": datetime.now().isoformat(),
                        "text": text,
                        "confidence": transcript_data.get("confidence", 0)
                    })
            
            self.audio_service.add_transcript_callback("test", on_transcript)
            
            # 启动服务
            status = await self.audio_service.start(LIVE_URL, SESSION_ID)
            
            if status.is_running:
                logger.info(f"✅ 音频转写服务启动成功")
                logger.info(f"   - Session ID: {status.session_id}")
                logger.info(f"   - Live ID: {status.live_id}")
                logger.info(f"   - FFmpeg PID: {status.ffmpeg_pid}")
                return True
            else:
                logger.error(f"❌ 音频转写服务启动失败")
                self.stats["errors"].append("音频转写服务启动失败")
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
            # 注册事件队列
            event_queue = await self.douyin_service.register_client()
            
            # 启动监控
            result = await self.douyin_service.start_monitoring(LIVE_URL)
            
            if result.get("success"):
                logger.info(f"✅ 抖音监控启动成功")
                logger.info(f"   - Room ID: {result.get('room_id')}")
                logger.info(f"   - Live ID: {result.get('live_id')}")
                
                # 启动事件处理任务
                asyncio.create_task(self._process_douyin_events(event_queue))
                return True
            else:
                logger.error(f"❌ 抖音监控启动失败: {result.get('message')}")
                self.stats["errors"].append(f"抖音监控启动失败: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 抖音监控启动异常: {e}", exc_info=True)
            self.stats["errors"].append(f"抖音监控启动异常: {str(e)}")
            return False
    
    async def _process_douyin_events(self, event_queue):
        """处理抖音事件"""
        try:
            while True:
                event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                
                event_type = event.get("type", "unknown")
                
                if event_type == "chat":
                    user = event.get("user", "匿名")
                    content = event.get("content", "")
                    logger.info(f"💬 [弹幕] {user}: {content}")
                    self.stats["douyin_messages"].append({
                        "time": datetime.now().isoformat(),
                        "type": "chat",
                        "user": user,
                        "content": content
                    })
                    
                elif event_type == "gift":
                    user = event.get("user", "匿名")
                    gift_name = event.get("gift_name", "")
                    count = event.get("count", 1)
                    logger.info(f"🎁 [礼物] {user} 送出 {gift_name} x{count}")
                    self.stats["douyin_messages"].append({
                        "time": datetime.now().isoformat(),
                        "type": "gift",
                        "user": user,
                        "gift": gift_name,
                        "count": count
                    })
                    
                elif event_type == "like":
                    count = event.get("count", 1)
                    logger.info(f"❤️ [点赞] +{count}")
                    
                elif event_type == "member":
                    user = event.get("user", "匿名")
                    logger.info(f"👋 [进入] {user} 来了")
                    
        except asyncio.TimeoutError:
            pass
        except asyncio.CancelledError:
            logger.info("抖音事件处理任务已取消")
        except Exception as e:
            logger.error(f"❌ 处理抖音事件时出错: {e}", exc_info=True)
            self.stats["errors"].append(f"处理抖音事件出错: {str(e)}")
    
    async def start_ai_analysis(self):
        """启动AI分析"""
        logger.info("\n" + "=" * 80)
        logger.info("🤖 启动AI分析服务...")
        logger.info("=" * 80)
        
        try:
            # 启动AI分析（60秒窗口）
            result = await self.ai_analyzer.start(window_sec=60, session_id=SESSION_ID)
            
            if result.get("success"):
                logger.info(f"✅ AI分析服务启动成功")
                logger.info(f"   - 分析窗口: 60秒")
                
                # 注册AI事件队列
                ai_queue = await self.ai_analyzer.register_client()
                asyncio.create_task(self._process_ai_events(ai_queue))
                return True
            else:
                logger.error(f"❌ AI分析服务启动失败: {result.get('message')}")
                self.stats["errors"].append(f"AI分析启动失败: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ AI分析启动异常: {e}", exc_info=True)
            self.stats["errors"].append(f"AI分析启动异常: {str(e)}")
            return False
    
    async def _process_ai_events(self, ai_queue):
        """处理AI分析事件"""
        try:
            while True:
                event = await asyncio.wait_for(ai_queue.get(), timeout=1.0)
                
                event_type = event.get("type", "unknown")
                
                if event_type == "analysis":
                    logger.info("🤖 [AI分析] 收到新的分析结果")
                    data = event.get("data", {})
                    
                    # 记录关键信息
                    if "vibe" in data:
                        logger.info(f"   - 氛围: {data['vibe']}")
                    if "style_profile" in data:
                        logger.info(f"   - 风格: {data['style_profile']}")
                    
                    self.stats["ai_analyses"].append({
                        "time": datetime.now().isoformat(),
                        "data": data
                    })
                    
                elif event_type == "error":
                    error_msg = event.get("message", "未知错误")
                    logger.error(f"❌ [AI错误] {error_msg}")
                    self.stats["errors"].append(f"AI分析错误: {error_msg}")
                    
        except asyncio.TimeoutError:
            pass
        except asyncio.CancelledError:
            logger.info("AI事件处理任务已取消")
        except Exception as e:
            logger.error(f"❌ 处理AI事件时出错: {e}", exc_info=True)
            self.stats["errors"].append(f"处理AI事件出错: {str(e)}")
    
    async def run_test(self):
        """运行完整测试"""
        logger.info("\n" + "=" * 80)
        logger.info("🚀 开始完整工作流测试")
        logger.info(f"📍 直播间: {LIVE_URL}")
        logger.info(f"⏱️  测试时长: {TEST_DURATION}秒 (5分钟)")
        logger.info(f"🆔 会话ID: {SESSION_ID}")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        try:
            # 初始化服务
            await self.setup_services()
            
            # 依次启动各项服务
            audio_ok = await self.start_audio_transcription()
            await asyncio.sleep(2)  # 等待音频服务稳定
            
            douyin_ok = await self.start_douyin_monitoring()
            await asyncio.sleep(2)  # 等待抖音服务稳定
            
            ai_ok = await self.start_ai_analysis()
            await asyncio.sleep(2)  # 等待AI服务稳定
            
            if not (audio_ok and douyin_ok and ai_ok):
                logger.error("❌ 部分服务启动失败，但继续测试...")
            
            # 运行测试
            logger.info("\n" + "=" * 80)
            logger.info(f"⏳ 测试运行中... (将持续 {TEST_DURATION} 秒)")
            logger.info("=" * 80)
            
            # 每30秒输出一次统计
            for i in range(TEST_DURATION // 30):
                await asyncio.sleep(30)
                elapsed = time.time() - start_time
                logger.info(f"\n📊 [{int(elapsed)}秒] 中间统计:")
                logger.info(f"   - 音频转写: {len(self.stats['audio_transcripts'])} 条")
                logger.info(f"   - 弹幕消息: {len(self.stats['douyin_messages'])} 条")
                logger.info(f"   - AI分析: {len(self.stats['ai_analyses'])} 次")
                logger.info(f"   - 错误: {len(self.stats['errors'])} 个")
            
            # 等待剩余时间
            remaining = TEST_DURATION - (time.time() - start_time)
            if remaining > 0:
                await asyncio.sleep(remaining)
            
        except KeyboardInterrupt:
            logger.info("\n⚠️ 测试被用户中断")
        except Exception as e:
            logger.error(f"\n❌ 测试过程中发生错误: {e}", exc_info=True)
            self.stats["errors"].append(f"测试执行错误: {str(e)}")
        finally:
            await self.cleanup_services()
            await self.print_final_report(start_time)
    
    async def cleanup_services(self):
        """清理所有服务"""
        logger.info("\n" + "=" * 80)
        logger.info("🧹 清理服务...")
        logger.info("=" * 80)
        
        try:
            # 停止音频转写
            if self.audio_service:
                try:
                    await self.audio_service.stop()
                    logger.info("✅ 音频转写服务已停止")
                except Exception as e:
                    logger.error(f"❌ 停止音频转写失败: {e}")
            
            # 停止抖音监控
            if self.douyin_service:
                try:
                    await self.douyin_service.stop_monitoring()
                    logger.info("✅ 抖音监控已停止")
                except Exception as e:
                    logger.error(f"❌ 停止抖音监控失败: {e}")
            
            # 停止AI分析
            if self.ai_analyzer:
                try:
                    await self.ai_analyzer.stop()
                    logger.info("✅ AI分析服务已停止")
                except Exception as e:
                    logger.error(f"❌ 停止AI分析失败: {e}")
                    
        except Exception as e:
            logger.error(f"❌ 清理服务时发生错误: {e}", exc_info=True)
    
    async def print_final_report(self, start_time):
        """打印最终测试报告"""
        elapsed = time.time() - start_time
        
        logger.info("\n" + "=" * 80)
        logger.info("📋 测试报告")
        logger.info("=" * 80)
        logger.info(f"⏱️  总测试时间: {elapsed:.1f}秒")
        logger.info(f"🎤 音频转写: {len(self.stats['audio_transcripts'])} 条")
        logger.info(f"💬 弹幕消息: {len(self.stats['douyin_messages'])} 条")
        logger.info(f"🤖 AI分析: {len(self.stats['ai_analyses'])} 次")
        logger.info(f"❌ 错误数量: {len(self.stats['errors'])} 个")
        logger.info("=" * 80)
        
        # 详细统计
        if self.stats["audio_transcripts"]:
            logger.info("\n📝 音频转写样例 (最近5条):")
            for item in self.stats["audio_transcripts"][-5:]:
                logger.info(f"   [{item['time']}] {item['text']} (置信度: {item['confidence']:.2f})")
        
        if self.stats["douyin_messages"]:
            logger.info("\n💬 弹幕消息样例 (最近5条):")
            for item in self.stats["douyin_messages"][-5:]:
                if item['type'] == 'chat':
                    logger.info(f"   [{item['time']}] {item['user']}: {item['content']}")
                elif item['type'] == 'gift':
                    logger.info(f"   [{item['time']}] {item['user']} -> {item['gift']} x{item['count']}")
        
        if self.stats["ai_analyses"]:
            logger.info(f"\n🤖 AI分析次数: {len(self.stats['ai_analyses'])}")
        
        if self.stats["errors"]:
            logger.info("\n❌ 错误列表:")
            for error in self.stats["errors"]:
                logger.info(f"   - {error}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ 测试完成！")
        logger.info("=" * 80)


async def main():
    """主函数"""
    tester = WorkflowTester()
    await tester.run_test()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n测试被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        sys.exit(1)

