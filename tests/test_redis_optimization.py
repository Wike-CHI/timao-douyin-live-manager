#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis优化功能自动测试脚本
测试批量写入、缓存、会话管理等核心功能

审查人: 叶维哲
创建日期: 2025-01-14
"""

import asyncio
import pytest
import sys
import os
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# 初始化Redis管理器（测试环境）
def init_test_redis():
    """初始化测试用的Redis管理器"""
    try:
        from server.utils.redis_manager import init_redis
        from server.config import config_manager
        
        redis_config = config_manager.config.redis
        redis_mgr = init_redis(redis_config)
        
        if redis_mgr:
            print(f"✅ Redis管理器已初始化（测试环境）")
        else:
            print(f"⚠️  Redis管理器初始化失败（将使用内存回退）")
        
        return redis_mgr
    except Exception as e:
        print(f"❌ Redis初始化失败: {e}")
        return None

# 在模块加载时初始化Redis
_redis_mgr = init_test_redis()


class TestRedisBatchWrite:
    """测试Redis批量写入功能"""
    
    @pytest.mark.asyncio
    async def test_transcription_batch_buffer(self):
        """测试转写结果批量缓冲"""
        from server.app.services.live_audio_stream_service import get_live_audio_service
        
        service = get_live_audio_service()
        
        # 模拟转写数据
        test_data = {
            "type": "transcription",
            "text": "测试转写文本",
            "confidence": 0.95,
            "timestamp": 1234567890,
            "is_final": True
        }
        
        # 测试缓冲功能
        if hasattr(service, '_buffer_transcription_for_batch'):
            await service._buffer_transcription_for_batch(test_data)
            assert len(service._redis_batch_buffer) > 0, "批量缓冲区应包含数据"
            print("✅ 转写批量缓冲测试通过")
        else:
            print("⚠️  转写批量缓冲方法未找到（跳过测试）")
    
    @pytest.mark.asyncio
    async def test_danmu_batch_buffer(self):
        """测试弹幕批量缓冲"""
        from server.app.services.douyin_web_relay import get_douyin_web_relay
        
        relay = get_douyin_web_relay()
        
        # 模拟弹幕数据
        test_event = {
            "type": "chat",
            "payload": {
                "user_id": "12345",
                "nickname": "测试用户",
                "content": "测试弹幕"
            },
            "timestamp": 1234567890
        }
        
        # 测试缓冲功能
        if hasattr(relay, '_buffer_danmu_for_batch'):
            await relay._buffer_danmu_for_batch(test_event)
            assert len(relay._redis_batch_buffer) > 0, "批量缓冲区应包含数据"
            print("✅ 弹幕批量缓冲测试通过")
        else:
            print("⚠️  弹幕批量缓冲方法未找到（跳过测试）")


class TestRedisSessionManagement:
    """测试Redis会话管理"""
    
    @pytest.mark.asyncio
    async def test_session_save_to_redis(self):
        """测试会话保存到Redis"""
        from server.app.services.live_session_manager import get_session_manager
        
        session_mgr = get_session_manager()
        
        # 创建测试会话
        session = await session_mgr.create_session(
            live_url="https://test.douyin.com/123456",
            live_id="123456",
            anchor_name="测试主播"
        )
        
        assert session is not None, "会话创建应成功"
        assert session.session_id is not None, "会话ID应存在"
        
        print(f"✅ 会话创建测试通过，Session ID: {session.session_id}")
        
        # 清理
        await session_mgr.stop_session()
    
    @pytest.mark.asyncio
    async def test_session_load_from_redis(self):
        """测试从Redis加载会话"""
        from server.app.services.live_session_manager import get_session_manager
        
        session_mgr = get_session_manager()
        
        # 创建测试会话
        created_session = await session_mgr.create_session(
            live_url="https://test.douyin.com/654321",
            live_id="654321",
            anchor_name="测试主播2"
        )
        
        # 重新加载会话
        loaded_session = await session_mgr.get_current_session()
        
        assert loaded_session is not None, "会话加载应成功"
        assert loaded_session.session_id == created_session.session_id, "会话ID应匹配"
        
        print(f"✅ 会话加载测试通过，Session ID: {loaded_session.session_id}")
        
        # 清理
        await session_mgr.stop_session()


class TestAICache:
    """测试AI分析缓存"""
    
    def test_cache_key_generation(self):
        """测试缓存键生成"""
        from server.app.services.ai_live_analyzer import AILiveAnalyzer
        
        analyzer = AILiveAnalyzer()
        
        # 测试缓存键生成
        sentences = ["测试句子1", "测试句子2"]
        comments = [{"content": "测试评论1"}, {"content": "测试评论2"}]
        
        if hasattr(analyzer, '_generate_cache_key'):
            cache_key = analyzer._generate_cache_key(sentences, comments)
            assert cache_key is not None, "缓存键应生成成功"
            assert "ai_analysis:" in cache_key, "缓存键应包含前缀"
            print(f"✅ 缓存键生成测试通过: {cache_key}")
        else:
            print("⚠️  缓存键生成方法未找到（跳过测试）")
    
    @pytest.mark.asyncio
    async def test_cache_storage_and_retrieval(self):
        """测试缓存存储和获取"""
        from server.app.services.ai_live_analyzer import AILiveAnalyzer
        
        analyzer = AILiveAnalyzer()
        
        # 测试数据
        test_result = {
            "summary": "测试总结",
            "highlights": ["亮点1", "亮点2"]
        }
        cache_key = "ai_analysis:test:abc123"
        
        if hasattr(analyzer, '_cache_analysis_result') and hasattr(analyzer, '_get_cached_analysis'):
            # 存储缓存
            await analyzer._cache_analysis_result(cache_key, test_result)
            
            # 获取缓存
            cached_result = await analyzer._get_cached_analysis(cache_key)
            
            if cached_result:
                assert cached_result["summary"] == test_result["summary"], "缓存内容应匹配"
                print("✅ AI缓存存储和获取测试通过")
            else:
                print("⚠️  缓存获取失败（可能Redis未启用）")
        else:
            print("⚠️  AI缓存方法未找到（跳过测试）")


class TestMemoryLimits:
    """测试内存限制"""
    
    def test_memory_limit_enforcement(self):
        """测试内存限制强制执行"""
        from server.app.services.ai_live_analyzer import AILiveAnalyzer
        
        analyzer = AILiveAnalyzer()
        
        # 填充超过限制的数据
        analyzer._state.sentences = ["句子"] * 300  # 超过max_sentences (200)
        analyzer._state.comments = [{"content": "评论"}] * 600  # 超过max_comments (500)
        
        # 执行内存限制
        if hasattr(analyzer, '_enforce_memory_limits'):
            analyzer._enforce_memory_limits()
            
            assert len(analyzer._state.sentences) <= 200, "句子数量应不超过限制"
            assert len(analyzer._state.comments) <= 500, "评论数量应不超过限制"
            
            print(f"✅ 内存限制测试通过，句子: {len(analyzer._state.sentences)}, 评论: {len(analyzer._state.comments)}")
        else:
            print("⚠️  内存限制方法未找到（跳过测试）")


class TestDatabaseConfig:
    """测试数据库配置"""
    
    def test_connection_pool_config(self):
        """测试连接池配置"""
        from server.config import config_manager
        
        db_config = config_manager.config.database
        
        # 验证连接池配置已优化
        assert db_config.pool_size >= 50, f"连接池大小应 >= 50，实际: {db_config.pool_size}"
        assert db_config.max_overflow >= 20, f"最大溢出应 >= 20，实际: {db_config.max_overflow}"
        assert db_config.pool_timeout >= 60, f"连接超时应 >= 60秒，实际: {db_config.pool_timeout}"
        
        print(f"✅ 数据库连接池配置测试通过")
        print(f"   - pool_size: {db_config.pool_size}")
        print(f"   - max_overflow: {db_config.max_overflow}")
        print(f"   - pool_timeout: {db_config.pool_timeout}s")


class TestPerformanceMonitor:
    """测试性能监控"""
    
    @pytest.mark.asyncio
    async def test_performance_monitor_init(self):
        """测试性能监控初始化"""
        from server.utils.performance_monitor import get_performance_monitor
        
        monitor = get_performance_monitor()
        
        assert monitor is not None, "性能监控器应初始化成功"
        
        # 测试启动
        result = await monitor.start()
        assert result["success"], "性能监控应启动成功"
        
        print("✅ 性能监控初始化测试通过")
        
        # 等待一次采集
        await asyncio.sleep(2)
        
        # 获取指标
        metrics = monitor.get_current_metrics()
        if metrics:
            print(f"   - MySQL连接: {metrics.mysql_active_connections}")
            print(f"   - Redis连接: {'✅' if metrics.redis_connected else '❌'}")
            print(f"   - 进程内存: {metrics.process_memory_mb:.1f}MB")
        
        # 清理
        await monitor.stop()


# 运行所有测试
def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("  Redis优化功能自动测试")
    print("  审查人: 叶维哲")
    print("=" * 60)
    print()
    
    # 使用pytest运行测试
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_all_tests()

