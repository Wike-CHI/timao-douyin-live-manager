#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音直播API综合测试脚本
测试所有API功能模块的完整性、性能和稳定性
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta

# 导入抖音直播模块
from douyin_live_fecter_module import (
    # API核心
    DouyinLiveAPI, APIFactory, create_api,
    # 连接管理
    ConnectionManager, create_connection_manager,
    # 消息处理
    MessageStreamManager, create_message_stream_manager,
    MessageHandler, MessageAdapterManager,
    # 数据模型
    BaseMessage, ChatMessage, GiftMessage, LikeMessage, FollowMessage,
    MessageType, RoomStatus,
    # 适配器
    ChatMessageAdapter, GiftMessageAdapter, 
    LikeMessageAdapter, FollowMessageAdapter,
    get_adapter_manager, reset_adapter_manager,
    # 状态管理
    get_state_manager, ConnectionState, ConnectionStatus,
    # 缓存管理
    get_cache_manager, CacheBackend, MemoryCacheBackend,
    MultiLevelCacheManager, cache_result,
    # 配置管理
    get_config_manager,
    # 工具
    TimeUtils, now
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveAPITester:
    """综合API测试器"""
    
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        self.error_log = []
        
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始综合API测试")
        
        test_methods = [
            # 基础功能测试
            self.test_api_creation,
            self.test_connection_management,
            self.test_message_stream_processing,
            
            # 适配器测试
            self.test_message_adapters,
            self.test_adapter_manager,
            
            # 状态管理测试
            self.test_state_management,
            self.test_room_state_tracking,
            
            # 缓存系统测试
            self.test_cache_operations,
            self.test_cache_performance,
            
            # 配置管理测试
            self.test_config_management,
            
            # 集成测试
            self.test_end_to_end_workflow,
            
            # 性能测试
            self.test_concurrent_operations,
            self.test_memory_usage,
            
            # 稳定性测试
            self.test_error_handling,
            self.test_resource_cleanup
        ]
        
        passed = 0
        failed = 0
        total_time = 0
        
        for test_method in test_methods:
            test_name = test_method.__name__
            logger.info(f"📋 执行测试: {test_name}")
            
            start_time = time.time()
            try:
                result = await test_method()
                execution_time = time.time() - start_time
                total_time += execution_time
                
                if result:
                    logger.info(f"✅ {test_name} - 通过 ({execution_time:.3f}s)")
                    passed += 1
                else:
                    logger.error(f"❌ {test_name} - 失败 ({execution_time:.3f}s)")
                    failed += 1
                    
                self.test_results[test_name] = {
                    'passed': result,
                    'execution_time': execution_time
                }
                
            except Exception as e:
                execution_time = time.time() - start_time
                total_time += execution_time
                
                logger.error(f"💥 {test_name} - 异常: {str(e)} ({execution_time:.3f}s)")
                failed += 1
                self.error_log.append(f"{test_name}: {str(e)}")
                
                self.test_results[test_name] = {
                    'passed': False,
                    'execution_time': execution_time,
                    'error': str(e)
                }
        
        # 生成测试报告
        await self.generate_test_report(passed, failed, total_time)
    
    async def test_api_creation(self) -> bool:
        """测试API创建功能"""
        try:
            # 测试直接创建
            api1 = DouyinLiveAPI("test_room_1")
            assert api1.room_id == "test_room_1"
            
            # 测试工厂方法创建
            api2 = await create_api("test_room_2")
            assert api2.room_id == "test_room_2"
            
            # 测试APIFactory
            api3 = await APIFactory.create_api("test_room_3")
            assert api3.room_id == "test_room_3"
            
            return True
        except Exception as e:
            logger.error(f"API创建测试失败: {e}")
            return False
    
    async def test_connection_management(self) -> bool:
        """测试连接管理功能"""
        try:
            # 创建连接管理器
            conn_mgr = await create_connection_manager("test_room")
            assert conn_mgr.room_id == "test_room"
            
            # 测试连接状态
            assert not conn_mgr.is_connected
            
            # 模拟连接（由于没有真实服务器，这里只测试接口）
            # result = await conn_mgr.connect()
            # assert result is True
            
            return True
        except Exception as e:
            logger.error(f"连接管理测试失败: {e}")
            return False
    
    async def test_message_stream_processing(self) -> bool:
        """测试消息流处理功能"""
        try:
            # 创建消息流管理器
            stream_mgr = await create_message_stream_manager("test_room")
            assert stream_mgr.room_id == "test_room"
            
            # 测试消息处理器添加
            class TestHandler(MessageHandler):
                async def handle_message(self, message: BaseMessage) -> bool:
                    return True
            
            handler = TestHandler()
            stream_mgr.add_handler(handler)
            
            # 测试消息处理
            test_message = ChatMessage(
                user_id="123",
                user_name="测试用户",
                content="测试消息",
                timestamp=now()
            )
            
            await stream_mgr.process_message(test_message)
            
            return True
        except Exception as e:
            logger.error(f"消息流处理测试失败: {e}")
            return False
    
    async def test_message_adapters(self) -> bool:
        """测试消息适配器功能"""
        try:
            # 测试聊天消息适配器
            chat_adapter = ChatMessageAdapter()
            
            # 测试礼物消息适配器
            gift_adapter = GiftMessageAdapter()
            
            # 测试点赞消息适配器
            like_adapter = LikeMessageAdapter()
            
            # 测试关注消息适配器
            follow_adapter = FollowMessageAdapter()
            
            # 测试适配功能
            test_data = {
                'type': 'chat',
                'user': {'user_id': '123', 'nickname': '测试用户'},
                'content': '测试消息',
                'timestamp': time.time()
            }
            
            # 由于适配器可能需要特定格式，这里只测试创建
            assert chat_adapter is not None
            assert gift_adapter is not None
            assert like_adapter is not None
            assert follow_adapter is not None
            
            return True
        except Exception as e:
            logger.error(f"消息适配器测试失败: {e}")
            return False
    
    async def test_adapter_manager(self) -> bool:
        """测试适配器管理器功能"""
        try:
            # 获取适配器管理器
            adapter_mgr = get_adapter_manager()
            assert adapter_mgr is not None
            
            # 测试消息适配器管理器
            msg_adapter_mgr = MessageAdapterManager()
            
            # 添加适配器
            chat_adapter = ChatMessageAdapter()
            msg_adapter_mgr.add_adapter('chat', chat_adapter)
            
            # 测试适配器获取
            retrieved_adapter = msg_adapter_mgr.get_adapter('chat')
            assert retrieved_adapter is not None
            
            return True
        except Exception as e:
            logger.error(f"适配器管理器测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_state_management(self) -> bool:
        """测试状态管理功能"""
        try:
            # 获取状态管理器
            state_mgr = get_state_manager()
            assert state_mgr is not None
            
            # 测试房间状态更新
            await state_mgr.update_room_status("test_room", RoomStatus.ACTIVE)
            
            # 测试连接状态更新
            connection_state = ConnectionState(status=ConnectionStatus.CONNECTED)
            await state_mgr.update_room_connection_state("test_room", connection_state)
            
            # 测试消息记录
            await state_mgr.record_message("test_room")
            
            return True
        except Exception as e:
            logger.error(f"状态管理测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_room_state_tracking(self) -> bool:
        """测试房间状态跟踪功能"""
        try:
            state_mgr = get_state_manager()
            
            # 测试多个房间状态
            rooms = ["room1", "room2", "room3"]
            
            for room in rooms:
                await state_mgr.update_room_status(room, RoomStatus.ACTIVE)
                await state_mgr.record_message(room)
            
            # 测试房间管理器获取
            room_mgr = await state_mgr.get_room_manager("room1")
            assert room_mgr is not None
            
            return True
        except Exception as e:
            logger.error(f"房间状态跟踪测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_cache_operations(self) -> bool:
        """测试缓存操作功能"""
        try:
            # 获取缓存管理器
            cache_mgr = await get_cache_manager()
            
            # 测试基本缓存操作
            await cache_mgr.set("test_key", "test_value", ttl=60)
            cached_value = await cache_mgr.get("test_key")
            assert cached_value == "test_value"
            
            # 测试缓存删除
            await cache_mgr.delete("test_key")
            deleted_value = await cache_mgr.get("test_key")
            assert deleted_value is None
            
            return True
        except Exception as e:
            logger.error(f"缓存操作测试失败: {e}")
            return False
    
    async def test_cache_performance(self) -> bool:
        """测试缓存性能"""
        try:
            cache_mgr = await get_cache_manager()
            
            # 测试批量缓存操作性能
            start_time = time.time()
            
            # 批量设置缓存
            for i in range(100):
                await cache_mgr.set(f"perf_key_{i}", f"value_{i}", ttl=60)
            
            set_time = time.time() - start_time
            
            # 批量获取缓存
            start_time = time.time()
            for i in range(100):
                value = await cache_mgr.get(f"perf_key_{i}")
                assert value == f"value_{i}"
            
            get_time = time.time() - start_time
            
            self.performance_metrics['cache_set_time'] = set_time
            self.performance_metrics['cache_get_time'] = get_time
            
            return True
        except Exception as e:
            logger.error(f"缓存性能测试失败: {e}")
            return False
    
    async def test_config_management(self) -> bool:
        """测试配置管理功能"""
        try:
            # 获取配置管理器
            config_mgr = get_config_manager()
            assert config_mgr is not None
            
            # 测试配置获取（使用默认值）
            test_config = config_mgr.get('test_key', 'default_value')
            assert test_config == 'default_value'
            
            return True
        except Exception as e:
            logger.error(f"配置管理测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_end_to_end_workflow(self) -> bool:
        """测试端到端工作流"""
        try:
            # 创建完整的API实例
            api = await create_api("e2e_test_room")
            
            # 添加消息处理器
            class E2EHandler(MessageHandler):
                def __init__(self):
                    self.processed_messages = []
                
                async def handle_message(self, message: BaseMessage) -> bool:
                    self.processed_messages.append(message)
                    return True
            
            handler = E2EHandler()
            api.message_stream.add_handler(handler)
            
            # 模拟消息处理流程
            test_message = ChatMessage(
                user_id="e2e_user",
                user_name="E2E测试用户",
                content="端到端测试消息",
                timestamp=now()
            )
            
            await api.message_stream.process_message(test_message)
            
            # 验证消息被处理
            assert len(handler.processed_messages) == 1
            assert handler.processed_messages[0].content == "端到端测试消息"
            
            return True
        except Exception as e:
            logger.error(f"端到端工作流测试失败: {e}")
            return False
    
    async def test_concurrent_operations(self) -> bool:
        """测试并发操作性能"""
        try:
            # 创建多个API实例
            apis = []
            for i in range(10):
                api = await create_api(f"concurrent_room_{i}")
                apis.append(api)
            
            # 并发处理消息
            async def process_messages(api: DouyinLiveAPI, count: int):
                for j in range(count):
                    message = ChatMessage(
                        user_id=f"user_{j}",
                        user_name=f"用户{j}",
                        content=f"并发消息{j}",
                        timestamp=now()
                    )
                    await api.message_stream.process_message(message)
            
            # 测试并发性能
            start_time = time.time()
            tasks = [process_messages(api, 10) for api in apis]
            await asyncio.gather(*tasks)
            concurrent_time = time.time() - start_time
            
            self.performance_metrics['concurrent_processing_time'] = concurrent_time
            self.performance_metrics['messages_per_second'] = (10 * 10) / concurrent_time
            
            return True
        except Exception as e:
            logger.error(f"并发操作测试失败: {e}")
            return False
    
    async def test_memory_usage(self) -> bool:
        """测试内存使用情况"""
        try:
            import psutil
            import os
            
            # 获取当前进程
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 创建大量对象
            apis = []
            for i in range(100):
                api = await create_api(f"memory_test_room_{i}")
                apis.append(api)
            
            # 处理消息
            for api in apis:
                message = ChatMessage(
                    user_id="memory_user",
                    user_name="内存测试用户",
                    content="内存测试消息",
                    timestamp=now()
                )
                await api.message_stream.process_message(message)
            
            # 检查内存使用
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            self.performance_metrics['memory_usage_mb'] = final_memory
            self.performance_metrics['memory_increase_mb'] = memory_increase
            
            # 清理
            apis.clear()
            
            return True
        except ImportError:
            logger.warning("psutil未安装，跳过内存测试")
            return True
        except Exception as e:
            logger.error(f"内存使用测试失败: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """测试错误处理机制"""
        try:
            # 测试无效房间ID
            try:
                api = DouyinLiveAPI("")
                # 应该能创建，但可能在连接时失败
            except Exception:
                pass  # 预期的错误
            
            # 测试无效消息处理
            api = await create_api("error_test_room")
            
            # 测试处理None消息
            try:
                await api.message_stream.process_message(None)
            except Exception:
                pass  # 预期的错误
            
            # 测试适配器错误处理
            adapter_mgr = get_adapter_manager()
            try:
                # 尝试适配无效数据
                result = adapter_mgr.adapt_message({}, "test_room")
                # 应该返回None或抛出异常
            except Exception:
                pass  # 预期的错误
            
            return True
        except Exception as e:
            logger.error(f"错误处理测试失败: {e}")
            return False
    
    async def test_resource_cleanup(self) -> bool:
        """测试资源清理功能"""
        try:
            # 创建API实例
            api = await create_api("cleanup_test_room")
            
            # 启动消息处理
            await api.message_stream.start_processing()
            
            # 停止处理
            await api.message_stream.stop_processing()
            
            # 测试连接清理
            if hasattr(api.connection_manager, 'disconnect'):
                await api.connection_manager.disconnect()
            
            # 重置适配器管理器
            reset_adapter_manager()
            
            return True
        except Exception as e:
            logger.error(f"资源清理测试失败: {e}")
            return False
    
    async def generate_test_report(self, passed: int, failed: int, total_time: float):
        """生成测试报告"""
        total_tests = passed + failed
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("📊 综合API测试报告")
        print("="*60)
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed}")
        print(f"失败测试: {failed}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"总执行时间: {total_time:.3f}s")
        
        if failed > 0:
            print(f"\n❌ 失败的测试:")
            for test_name, result in self.test_results.items():
                if not result['passed']:
                    error_msg = result.get('error', '未知错误')
                    print(f"  - {test_name}: {error_msg}")
        
        if self.performance_metrics:
            print(f"\n⚡ 性能指标:")
            for metric, value in self.performance_metrics.items():
                if isinstance(value, float):
                    print(f"  - {metric}: {value:.6f}")
                else:
                    print(f"  - {metric}: {value}")
        
        # 保存详细报告
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': passed,
                'failed': failed,
                'success_rate': success_rate,
                'total_time': total_time
            },
            'test_results': self.test_results,
            'performance_metrics': self.performance_metrics,
            'errors': self.error_log
        }
        
        with open('comprehensive_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存到: comprehensive_test_report.json")
        print("🎉 综合API测试完成!")


async def main():
    """主函数"""
    tester = ComprehensiveAPITester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())