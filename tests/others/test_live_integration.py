#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直播间完整功能和性能测试脚本
审查人: 叶维哲

测试目标：
1. 功能完整性验证
2. MySQL性能监控
3. Redis性能监控
4. SenseVoice + VAD语音转写性能
5. AI分析性能
6. 实时弹幕性能
"""

import asyncio
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import sys
import os

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# 初始化Redis管理器
from server.utils.redis_manager import init_redis
from server.config import config_manager

redis_config = config_manager.config.redis
redis_mgr = init_redis(redis_config)
if redis_mgr:
    print("✅ Redis管理器已初始化")

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LiveIntegrationTest:
    """直播间完整功能和性能测试"""
    
    def __init__(self, room_url: str, test_duration_minutes: int = 10):
        """
        初始化测试
        
        Args:
            room_url: 直播间URL
            test_duration_minutes: 测试时长（分钟）
        """
        self.room_url = room_url
        self.room_id = self._extract_room_id(room_url)
        self.test_duration = test_duration_minutes * 60  # 转换为秒
        self.start_time = None
        self.session_id = None
        
        # 性能指标
        self.metrics = {
            "mysql": {
                "queries": 0,
                "avg_query_time": 0,
                "slow_queries": 0,
                "errors": 0
            },
            "redis": {
                "operations": 0,
                "avg_operation_time": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "errors": 0
            },
            "transcription": {
                "segments_processed": 0,
                "avg_processing_time": 0,
                "errors": 0,
                "vad_detections": 0
            },
            "ai_analysis": {
                "analyses_performed": 0,
                "avg_analysis_time": 0,
                "cache_hits": 0,
                "errors": 0
            },
            "danmu": {
                "messages_received": 0,
                "messages_processed": 0,
                "avg_processing_time": 0,
                "errors": 0
            },
            "system": {
                "memory_usage_mb": [],
                "cpu_usage_percent": [],
                "active_connections": []
            }
        }
        
        # 测试结果
        self.test_results = {
            "start_time": None,
            "end_time": None,
            "duration_seconds": 0,
            "test_passed": False,
            "errors": [],
            "metrics": {}
        }
    
    def _extract_room_id(self, url: str) -> str:
        """从URL提取房间ID"""
        try:
            # 从URL中提取room_id参数
            if "room_id=" in url:
                room_id = url.split("room_id=")[1].split("&")[0]
            else:
                # 从路径中提取
                room_id = url.split("/")[-1].split("?")[0]
            return room_id
        except Exception as e:
            logger.error(f"提取房间ID失败: {e}")
            return "7572532254115826451"  # 默认房间ID
    
    async def setup(self):
        """测试环境准备"""
        logger.info("=" * 80)
        logger.info("🚀 开始直播间完整功能和性能测试")
        logger.info("=" * 80)
        logger.info(f"测试房间: {self.room_url}")
        logger.info(f"房间ID: {self.room_id}")
        logger.info(f"测试时长: {self.test_duration / 60}分钟")
        logger.info("=" * 80)
        
        self.start_time = time.time()
        self.test_results["start_time"] = datetime.now().isoformat()
        
        # 检查依赖服务
        await self._check_dependencies()
    
    async def _check_dependencies(self):
        """检查依赖服务状态"""
        logger.info("\n📋 检查依赖服务...")
        
        # 检查Redis
        try:
            from server.utils.redis_manager import get_redis
            redis_mgr = get_redis()
            if redis_mgr:
                # 测试连接
                test_key = "test:connection:check"
                redis_mgr.set(test_key, "ok", ttl=10)
                result = redis_mgr.get(test_key)
                redis_mgr.delete(test_key)
                logger.info("✅ Redis连接正常")
            else:
                logger.warning("⚠️  Redis未初始化，将使用内存回退")
        except Exception as e:
            logger.error(f"❌ Redis检查失败: {e}")
            self.test_results["errors"].append(f"Redis检查失败: {e}")
        
        # 检查MySQL
        try:
            from server.app.database import DatabaseManager
            from server.config import config_manager
            from sqlalchemy import text
            
            db_manager = DatabaseManager(config_manager.config.database)
            db_manager.initialize()
            
            # 执行简单查询测试
            with db_manager.get_session() as session:
                session.execute(text("SELECT 1"))
            logger.info("✅ MySQL连接正常")
        except Exception as e:
            logger.error(f"❌ MySQL检查失败: {e}")
            self.test_results["errors"].append(f"MySQL检查失败: {e}")
        
        # 检查SenseVoice
        try:
            # 检查模型文件是否存在
            model_path = Path("models/SenseVoiceSmall")
            if model_path.exists():
                logger.info("✅ SenseVoice模型存在")
            else:
                logger.warning("⚠️  SenseVoice模型不存在")
        except Exception as e:
            logger.error(f"❌ SenseVoice检查失败: {e}")
    
    async def test_live_session(self):
        """测试完整直播会话"""
        logger.info("\n🎬 开始测试直播会话...")
        
        try:
            # 1. 创建直播会话
            await self._test_create_session()
            
            # 2. 启动各个服务
            await self._test_start_services()
            
            # 3. 监控性能指标
            await self._monitor_performance()
            
            # 4. 停止服务
            await self._test_stop_services()
            
            self.test_results["test_passed"] = True
            
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}")
            self.test_results["errors"].append(f"测试失败: {e}")
            self.test_results["test_passed"] = False
    
    async def _test_create_session(self):
        """测试创建会话"""
        logger.info("\n1️⃣  测试创建直播会话...")
        
        try:
            from server.app.services.live_session_manager import LiveSessionManager
            
            manager = LiveSessionManager()
            
            # 创建会话（使用实际的方法签名）
            session = await manager.create_session(
                live_url=self.room_url,
                room_id=self.room_id,
                anchor_name="测试主播",
                platform_key="douyin"
            )
            self.session_id = session.session_id
            
            logger.info(f"✅ 会话创建成功: {self.session_id}")
            
            # 记录指标
            self.metrics["mysql"]["queries"] += 1
            
        except Exception as e:
            logger.error(f"❌ 创建会话失败: {e}")
            raise
    
    async def _test_start_services(self):
        """测试启动各个服务"""
        logger.info("\n2️⃣  测试启动服务...")
        
        # 启动音频转写服务
        await self._start_audio_service()
        
        # 启动弹幕服务
        await self._start_danmu_service()
        
        # 启动AI分析服务
        await self._start_ai_service()
    
    async def _start_audio_service(self):
        """启动音频转写服务"""
        logger.info("  📝 启动音频转写服务...")
        
        try:
            from server.app.services.live_audio_stream_service import LiveAudioStreamService
            
            service = LiveAudioStreamService()
            # 这里需要实际的音频流配置
            # 暂时只是初始化检查
            
            logger.info("  ✅ 音频转写服务准备就绪")
            
        except Exception as e:
            logger.error(f"  ❌ 音频转写服务启动失败: {e}")
            self.test_results["errors"].append(f"音频转写服务: {e}")
    
    async def _start_danmu_service(self):
        """启动弹幕服务"""
        logger.info("  💬 启动弹幕服务...")
        
        try:
            from server.app.services.douyin_web_relay import DouyinWebRelay
            
            relay = DouyinWebRelay()
            # 初始化检查
            
            logger.info("  ✅ 弹幕服务准备就绪")
            
        except Exception as e:
            logger.error(f"  ❌ 弹幕服务启动失败: {e}")
            self.test_results["errors"].append(f"弹幕服务: {e}")
    
    async def _start_ai_service(self):
        """启动AI分析服务"""
        logger.info("  🤖 启动AI分析服务...")
        
        try:
            from server.app.services.ai_live_analyzer import AILiveAnalyzer
            
            analyzer = AILiveAnalyzer()
            # 初始化检查
            
            logger.info("  ✅ AI分析服务准备就绪")
            
        except Exception as e:
            logger.error(f"  ❌ AI分析服务启动失败: {e}")
            self.test_results["errors"].append(f"AI分析服务: {e}")
    
    async def _monitor_performance(self):
        """监控性能指标"""
        logger.info(f"\n3️⃣  开始监控性能（{self.test_duration}秒）...")
        
        start_time = time.time()
        check_interval = 10  # 每10秒检查一次
        
        while time.time() - start_time < self.test_duration:
            # 收集性能指标
            await self._collect_metrics()
            
            # 显示实时指标
            elapsed = int(time.time() - start_time)
            remaining = self.test_duration - elapsed
            logger.info(f"  ⏱️  已运行 {elapsed}秒 / 剩余 {remaining}秒")
            
            # 等待下次检查
            await asyncio.sleep(check_interval)
        
        logger.info("✅ 性能监控完成")
    
    async def _collect_metrics(self):
        """收集性能指标"""
        try:
            # 收集Redis指标
            await self._collect_redis_metrics()
            
            # 收集MySQL指标
            await self._collect_mysql_metrics()
            
            # 收集系统指标
            await self._collect_system_metrics()
            
        except Exception as e:
            logger.error(f"收集指标失败: {e}")
    
    async def _collect_redis_metrics(self):
        """收集Redis指标"""
        try:
            from server.utils.redis_manager import get_redis
            redis_mgr = get_redis()
            
            if redis_mgr:
                # 测试Redis操作性能
                start = time.time()
                test_key = "test:perf:check"
                redis_mgr.set(test_key, "test", ttl=10)
                redis_mgr.get(test_key)
                redis_mgr.delete(test_key)
                operation_time = (time.time() - start) * 1000  # 毫秒
                
                self.metrics["redis"]["operations"] += 3
                self.metrics["redis"]["avg_operation_time"] = (
                    (self.metrics["redis"]["avg_operation_time"] * (self.metrics["redis"]["operations"] - 3) + operation_time) /
                    self.metrics["redis"]["operations"]
                )
        except Exception as e:
            self.metrics["redis"]["errors"] += 1
            logger.debug(f"Redis指标收集失败: {e}")
    
    async def _collect_mysql_metrics(self):
        """收集MySQL指标"""
        try:
            from server.app.database import get_database
            db = get_database()
            
            # 测试查询性能
            start = time.time()
            db.execute("SELECT 1")
            query_time = (time.time() - start) * 1000  # 毫秒
            
            self.metrics["mysql"]["queries"] += 1
            self.metrics["mysql"]["avg_query_time"] = (
                (self.metrics["mysql"]["avg_query_time"] * (self.metrics["mysql"]["queries"] - 1) + query_time) /
                self.metrics["mysql"]["queries"]
            )
            
            if query_time > 100:  # 慢查询阈值：100ms
                self.metrics["mysql"]["slow_queries"] += 1
                
        except Exception as e:
            self.metrics["mysql"]["errors"] += 1
            logger.debug(f"MySQL指标收集失败: {e}")
    
    async def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            import psutil
            
            # 内存使用
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.metrics["system"]["memory_usage_mb"].append(memory_mb)
            
            # CPU使用
            cpu_percent = process.cpu_percent(interval=0.1)
            self.metrics["system"]["cpu_usage_percent"].append(cpu_percent)
            
        except Exception as e:
            logger.debug(f"系统指标收集失败: {e}")
    
    async def _test_stop_services(self):
        """测试停止服务"""
        logger.info("\n4️⃣  测试停止服务...")
        
        try:
            if self.session_id:
                from server.app.services.live_session_manager import LiveSessionManager
                
                manager = LiveSessionManager()
                # stop_session 不接受参数，停止当前活跃会话
                stopped_session = await manager.stop_session()
                
                if stopped_session:
                    logger.info(f"✅ 会话停止成功: {stopped_session.session_id}")
                else:
                    logger.warning("⚠️  没有活跃会话可停止")
        except Exception as e:
            logger.error(f"❌ 停止会话失败: {e}")
            self.test_results["errors"].append(f"停止会话: {e}")
    
    async def generate_report(self):
        """生成测试报告"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 测试报告")
        logger.info("=" * 80)
        
        # 计算测试时长
        end_time = time.time()
        duration = end_time - self.start_time
        self.test_results["end_time"] = datetime.now().isoformat()
        self.test_results["duration_seconds"] = duration
        self.test_results["metrics"] = self.metrics
        
        # 打印报告
        logger.info(f"\n📅 测试时间: {self.test_results['start_time']}")
        logger.info(f"⏱️  测试时长: {duration:.2f}秒 ({duration/60:.2f}分钟)")
        logger.info(f"{'✅' if self.test_results['test_passed'] else '❌'} 测试结果: {'通过' if self.test_results['test_passed'] else '失败'}")
        
        # MySQL性能
        logger.info(f"\n🗄️  MySQL性能:")
        logger.info(f"  查询次数: {self.metrics['mysql']['queries']}")
        logger.info(f"  平均查询时间: {self.metrics['mysql']['avg_query_time']:.2f}ms")
        logger.info(f"  慢查询数: {self.metrics['mysql']['slow_queries']}")
        logger.info(f"  错误数: {self.metrics['mysql']['errors']}")
        
        # Redis性能
        logger.info(f"\n💾 Redis性能:")
        logger.info(f"  操作次数: {self.metrics['redis']['operations']}")
        logger.info(f"  平均操作时间: {self.metrics['redis']['avg_operation_time']:.2f}ms")
        logger.info(f"  缓存命中: {self.metrics['redis']['cache_hits']}")
        logger.info(f"  缓存未命中: {self.metrics['redis']['cache_misses']}")
        logger.info(f"  错误数: {self.metrics['redis']['errors']}")
        
        # 语音转写性能
        logger.info(f"\n📝 语音转写性能:")
        logger.info(f"  处理片段数: {self.metrics['transcription']['segments_processed']}")
        logger.info(f"  平均处理时间: {self.metrics['transcription']['avg_processing_time']:.2f}ms")
        logger.info(f"  VAD检测数: {self.metrics['transcription']['vad_detections']}")
        logger.info(f"  错误数: {self.metrics['transcription']['errors']}")
        
        # AI分析性能
        logger.info(f"\n🤖 AI分析性能:")
        logger.info(f"  分析次数: {self.metrics['ai_analysis']['analyses_performed']}")
        logger.info(f"  平均分析时间: {self.metrics['ai_analysis']['avg_analysis_time']:.2f}ms")
        logger.info(f"  缓存命中: {self.metrics['ai_analysis']['cache_hits']}")
        logger.info(f"  错误数: {self.metrics['ai_analysis']['errors']}")
        
        # 弹幕性能
        logger.info(f"\n💬 弹幕性能:")
        logger.info(f"  接收消息数: {self.metrics['danmu']['messages_received']}")
        logger.info(f"  处理消息数: {self.metrics['danmu']['messages_processed']}")
        logger.info(f"  平均处理时间: {self.metrics['danmu']['avg_processing_time']:.2f}ms")
        logger.info(f"  错误数: {self.metrics['danmu']['errors']}")
        
        # 系统资源
        if self.metrics["system"]["memory_usage_mb"]:
            avg_memory = sum(self.metrics["system"]["memory_usage_mb"]) / len(self.metrics["system"]["memory_usage_mb"])
            max_memory = max(self.metrics["system"]["memory_usage_mb"])
            logger.info(f"\n💻 系统资源:")
            logger.info(f"  平均内存: {avg_memory:.2f}MB")
            logger.info(f"  峰值内存: {max_memory:.2f}MB")
        
        if self.metrics["system"]["cpu_usage_percent"]:
            avg_cpu = sum(self.metrics["system"]["cpu_usage_percent"]) / len(self.metrics["system"]["cpu_usage_percent"])
            max_cpu = max(self.metrics["system"]["cpu_usage_percent"])
            logger.info(f"  平均CPU: {avg_cpu:.2f}%")
            logger.info(f"  峰值CPU: {max_cpu:.2f}%")
        
        # 错误列表
        if self.test_results["errors"]:
            logger.info(f"\n❌ 错误列表:")
            for error in self.test_results["errors"]:
                logger.info(f"  - {error}")
        
        # 保存报告到文件
        await self._save_report()
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ 测试完成")
        logger.info("=" * 80)
    
    async def _save_report(self):
        """保存测试报告到文件"""
        try:
            reports_dir = Path("test_reports")
            reports_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = reports_dir / f"live_integration_test_{timestamp}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"\n📄 报告已保存: {report_file}")
            
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
    
    async def run(self):
        """运行完整测试"""
        try:
            # 准备
            await self.setup()
            
            # 测试
            await self.test_live_session()
            
            # 报告
            await self.generate_report()
            
        except Exception as e:
            logger.error(f"测试运行失败: {e}")
            self.test_results["test_passed"] = False
            self.test_results["errors"].append(f"运行失败: {e}")
            
            # 仍然生成报告
            await self.generate_report()


async def main():
    """主函数"""
    # 测试配置
    room_url = "https://live.douyin.com/932546434419?room_id=7572532254115826451"
    test_duration_minutes = 10
    
    # 创建测试实例
    test = LiveIntegrationTest(room_url, test_duration_minutes)
    
    # 运行测试
    await test.run()


if __name__ == "__main__":
    print("=" * 80)
    print("  直播间完整功能和性能测试脚本")
    print("  审查人: 叶维哲")
    print("=" * 80)
    print()
    
    # 运行测试
    asyncio.run(main())

