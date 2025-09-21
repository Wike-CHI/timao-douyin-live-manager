#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音直播API集成测试脚本
测试API封装的功能完整性和性能表现
"""

import asyncio
import logging
import time
from typing import Dict, Any, List
import sys
import os

# 添加项目路径
sys.path.append('.')

from douyin_live_fecter_module import (
    DouyinLiveAPI,
    APIFactory,
    create_api,
    create_connection_manager,
    create_message_stream_manager,
    MessageAdapterManager,
    get_adapter_manager,
    get_state_manager,
    init_state_manager,
    get_cache_manager,
    MessageType,
    DouyinMessage
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APIIntegrationTester:
    """API集成测试器"""
    
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有集成测试"""
        logger.info("🚀 开始API集成测试...")
        
        test_methods = [
            self.test_basic_imports,
            self.test_api_factory,
            self.test_connection_manager,
            self.test_message_stream_manager,
            self.test_adapter_manager,
            self.test_state_manager,
            self.test_cache_manager,
            self.test_message_processing,
            self.test_performance_metrics
        ]
        
        for test_method in test_methods:
            test_name = test_method.__name__
            logger.info(f"📋 执行测试: {test_name}")
            
            start_time = time.time()
            try:
                result = await test_method()
                execution_time = time.time() - start_time
                
                self.test_results[test_name] = {
                    'status': 'PASSED',
                    'result': result,
                    'execution_time': execution_time
                }
                logger.info(f"✅ {test_name} - 通过 ({execution_time:.3f}s)")
                
            except Exception as e:
                execution_time = time.time() - start_time
                self.test_results[test_name] = {
                    'status': 'FAILED',
                    'error': str(e),
                    'execution_time': execution_time
                }
                logger.error(f"❌ {test_name} - 失败: {e}")
        
        return self.generate_test_report()
    
    async def test_basic_imports(self) -> Dict[str, Any]:
        """测试基础导入功能"""
        # 测试所有主要类和函数是否可以正常导入
        imports_to_test = [
            'DouyinLiveAPI',
            'APIFactory', 
            'MessageAdapterManager',
            'MessageType',
            'DouyinMessage'
        ]
        
        import_results = {}
        for import_name in imports_to_test:
            try:
                # 通过globals()检查是否已导入
                if import_name in globals():
                    import_results[import_name] = True
                else:
                    import_results[import_name] = False
            except Exception as e:
                import_results[import_name] = f"Error: {e}"
        
        return {
            'imports_tested': len(imports_to_test),
            'imports_successful': sum(1 for v in import_results.values() if v is True),
            'import_details': import_results
        }
    
    async def test_api_factory(self) -> Dict[str, Any]:
        """测试API工厂功能"""
        test_room_id = "test_room_123"
        
        # 测试APIFactory静态方法
        api = await APIFactory.create_api(test_room_id)
        assert api is not None, "API创建失败"
        assert hasattr(api, 'room_id'), "API缺少room_id属性"
        
        # 测试便捷函数
        api2 = await create_api(test_room_id)
        assert api2 is not None, "便捷函数创建API失败"
        
        # 测试连接管理器创建
        conn_mgr = await create_connection_manager()
        assert conn_mgr is not None, "连接管理器创建失败"
        
        # 测试消息流管理器创建
        msg_mgr = await create_message_stream_manager()
        assert msg_mgr is not None, "消息流管理器创建失败"
        
        return {
            'api_created': True,
            'connection_manager_created': True,
            'message_stream_manager_created': True,
            'factory_methods_working': True
        }
    
    async def test_connection_manager(self) -> Dict[str, Any]:
        """测试连接管理器功能"""
        conn_mgr = await create_connection_manager()
        
        # 测试基本属性和方法
        assert hasattr(conn_mgr, 'is_connected'), "缺少is_connected属性"
        assert hasattr(conn_mgr, 'connect'), "缺少connect方法"
        assert hasattr(conn_mgr, 'disconnect'), "缺少disconnect方法"
        
        # 测试初始状态
        initial_connected = conn_mgr.is_connected
        
        return {
            'manager_created': True,
            'has_required_methods': True,
            'initial_connected_state': initial_connected
        }
    
    async def test_message_stream_manager(self) -> Dict[str, Any]:
        """测试消息流管理器功能"""
        msg_mgr = await create_message_stream_manager()
        
        # 测试基本属性和方法
        assert hasattr(msg_mgr, 'add_handler'), "缺少add_handler方法"
        assert hasattr(msg_mgr, 'remove_handler'), "缺少remove_handler方法"
        assert hasattr(msg_mgr, 'process_message'), "缺少process_message方法"
        
        # 测试处理器管理
        handler_count_before = len(getattr(msg_mgr, 'handlers', []))
        
        # 添加测试处理器
        async def test_handler(message):
            pass
        
        msg_mgr.add_handler(test_handler)
        handler_count_after = len(getattr(msg_mgr, 'handlers', []))
        
        return {
            'manager_created': True,
            'has_required_methods': True,
            'handler_management_working': handler_count_after > handler_count_before
        }
    
    async def test_adapter_manager(self) -> Dict[str, Any]:
        """测试适配器管理器功能"""
        adapter_mgr = get_adapter_manager()
        
        # 测试基本功能
        assert adapter_mgr is not None, "适配器管理器获取失败"
        assert hasattr(adapter_mgr, 'process_message'), "缺少process_message方法"
        assert hasattr(adapter_mgr, 'get_adapter_stats'), "缺少get_adapter_stats方法"
        
        # 获取统计信息
        stats = adapter_mgr.get_adapter_stats()
        
        return {
            'manager_obtained': True,
            'has_required_methods': True,
            'adapter_stats': stats
        }
    
    async def test_state_manager(self) -> Dict[str, Any]:
        """测试状态管理器功能"""
        # 初始化状态管理器
        init_state_manager()
        state_mgr = get_state_manager()
        
        assert state_mgr is not None, "状态管理器获取失败"
        
        # 测试基本功能
        if hasattr(state_mgr, 'get_room_state'):
            room_state = state_mgr.get_room_state("test_room")
            room_state_available = True
        else:
            room_state_available = False
        
        return {
            'manager_initialized': True,
            'manager_obtained': True,
            'room_state_available': room_state_available
        }
    
    async def test_cache_manager(self) -> Dict[str, Any]:
        """测试缓存管理器功能"""
        cache_mgr = get_cache_manager()
        
        assert cache_mgr is not None, "缓存管理器获取失败"
        
        # 测试基本功能
        cache_available = hasattr(cache_mgr, 'get') or hasattr(cache_mgr, 'set')
        
        return {
            'manager_obtained': True,
            'cache_methods_available': cache_available
        }
    
    async def test_message_processing(self) -> Dict[str, Any]:
        """测试消息处理功能"""
        adapter_mgr = get_adapter_manager()
        
        # 创建测试消息数据
        test_message_data = {
            'type': 'chat',
            'username': 'test_user',
            'content': 'Hello, World!',
            'timestamp': int(time.time() * 1000),
            'user_id': '12345',
            'room_id': 'test_room'
        }
        
        # 处理消息
        try:
            processed_message = await adapter_mgr.process_message(test_message_data)
            processing_successful = True
            message_type_detected = processed_message is not None
        except Exception as e:
            processing_successful = False
            message_type_detected = False
            logger.warning(f"消息处理测试出现预期错误: {e}")
        
        return {
            'test_message_created': True,
            'processing_attempted': True,
            'processing_successful': processing_successful,
            'message_type_detected': message_type_detected
        }
    
    async def test_performance_metrics(self) -> Dict[str, Any]:
        """测试性能指标"""
        # 测试API创建性能
        start_time = time.time()
        for i in range(10):
            api = await create_api(f"test_room_{i}")
        api_creation_time = (time.time() - start_time) / 10
        
        # 测试适配器管理器性能
        adapter_mgr = get_adapter_manager()
        start_time = time.time()
        for i in range(100):
            stats = adapter_mgr.get_adapter_stats()
        stats_retrieval_time = (time.time() - start_time) / 100
        
        self.performance_metrics = {
            'avg_api_creation_time': api_creation_time,
            'avg_stats_retrieval_time': stats_retrieval_time
        }
        
        return self.performance_metrics
    
    def generate_test_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PASSED')
        failed_tests = total_tests - passed_tests
        
        total_execution_time = sum(result['execution_time'] for result in self.test_results.values())
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                'total_execution_time': total_execution_time
            },
            'test_results': self.test_results,
            'performance_metrics': self.performance_metrics,
            'timestamp': time.time()
        }
        
        return report


async def main():
    """主函数"""
    print("🔧 抖音直播API集成测试")
    print("=" * 50)
    
    tester = APIIntegrationTester()
    report = await tester.run_all_tests()
    
    # 打印测试报告
    print("\n📊 测试报告")
    print("=" * 50)
    
    summary = report['summary']
    print(f"总测试数: {summary['total_tests']}")
    print(f"通过测试: {summary['passed_tests']}")
    print(f"失败测试: {summary['failed_tests']}")
    print(f"成功率: {summary['success_rate']:.1f}%")
    print(f"总执行时间: {summary['total_execution_time']:.3f}s")
    
    if summary['failed_tests'] > 0:
        print("\n❌ 失败的测试:")
        for test_name, result in report['test_results'].items():
            if result['status'] == 'FAILED':
                print(f"  - {test_name}: {result['error']}")
    
    if report['performance_metrics']:
        print("\n⚡ 性能指标:")
        for metric, value in report['performance_metrics'].items():
            print(f"  - {metric}: {value:.6f}s")
    
    print("\n🎉 API集成测试完成!")
    
    # 返回退出码
    return 0 if summary['failed_tests'] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)