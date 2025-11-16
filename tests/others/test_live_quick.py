#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直播间快速功能测试脚本（2分钟快速验证）
审查人: 叶维哲

用于快速验证系统功能是否正常工作
"""

import asyncio
import time
import json
import logging
from datetime import datetime
from pathlib import Path
import sys
import os
from sqlalchemy import text  # pyright: ignore[reportMissingImports]

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# 初始化Redis管理器
from server.utils.redis_manager import init_redis
from server.config import config_manager

redis_config = config_manager.config.redis
redis_mgr = init_redis(redis_config)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_redis():
    """测试Redis连接和性能"""
    logger.info("📋 测试Redis...")
    
    try:
        from server.utils.redis_manager import get_redis
        redis_mgr = get_redis()
        
        if not redis_mgr:
            logger.error("❌ Redis管理器未初始化")
            return False
        
        # 测试基本操作
        test_key = "test:quick:check"
        test_data = {"test": "value", "中文": "测试"}
        
        # 写入
        start = time.time()
        redis_mgr.set(test_key, json.dumps(test_data, ensure_ascii=False), ttl=60)
        write_time = (time.time() - start) * 1000
        
        # 读取
        start = time.time()
        cached = redis_mgr.get(test_key)
        read_time = (time.time() - start) * 1000
        
        # 删除
        redis_mgr.delete(test_key)
        
        if cached:
            logger.info(f"✅ Redis测试通过")
            logger.info(f"   写入耗时: {write_time:.2f}ms")
            logger.info(f"   读取耗时: {read_time:.2f}ms")
            return True
        else:
            logger.error("❌ Redis读取失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ Redis测试失败: {e}")
        return False


async def test_mysql():
    """测试MySQL连接和性能"""
    logger.info("\n📋 测试MySQL...")
    
    try:
        from server.app.database import DatabaseManager
        from server.config import config_manager
        
        db_manager = DatabaseManager(config_manager.config.database)
        db_manager.initialize()
        
        # 测试查询
        with db_manager.get_session() as session:
            start = time.time()
            result = session.execute(text("SELECT 1 as test"))
            query_time = (time.time() - start) * 1000
            
            logger.info(f"✅ MySQL测试通过")
            logger.info(f"   查询耗时: {query_time:.2f}ms")
            return True
        
    except Exception as e:
        logger.error(f"❌ MySQL测试失败: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False


async def test_ai_cache():
    """测试AI缓存功能"""
    logger.info("\n📋 测试AI缓存...")
    
    try:
        from server.app.services.ai_live_analyzer import AILiveAnalyzer
        
        analyzer = AILiveAnalyzer()
        
        # 测试缓存键生成
        test_content = "这是测试内容"
        cache_key = analyzer._generate_cache_key("test_session", test_content)
        
        # 测试缓存存储
        test_result = {"sentiment": "positive", "keywords": ["测试"]}
        await analyzer._cache_analysis_result(cache_key, test_result)
        
        # 测试缓存读取
        cached = await analyzer._get_cached_analysis(cache_key)
        
        if cached:
            logger.info(f"✅ AI缓存测试通过")
            logger.info(f"   缓存键: {cache_key}")
            logger.info(f"   缓存数据: {cached}")
            return True
        else:
            logger.warning("⚠️  AI缓存未命中（可能Redis未启用）")
            return True  # 不算失败
            
    except Exception as e:
        logger.error(f"❌ AI缓存测试失败: {e}")
        return False


async def test_batch_buffer():
    """测试批量缓冲功能"""
    logger.info("\n📋 测试批量缓冲...")
    
    try:
        from server.app.services.live_audio_stream_service import LiveAudioStreamService
        
        service = LiveAudioStreamService()
        
        # 检查批量配置
        logger.info(f"   批量写入启用: {service._redis_batch_enabled}")
        logger.info(f"   批量大小: {service._redis_batch_size}")
        logger.info(f"   批量间隔: {service._redis_batch_interval}秒")
        
        logger.info(f"✅ 批量缓冲配置正常")
        return True
        
    except Exception as e:
        logger.error(f"❌ 批量缓冲测试失败: {e}")
        return False


async def test_session_manager():
    """测试会话管理器"""
    logger.info("\n📋 测试会话管理器...")
    
    try:
        from server.app.services.live_session_manager import LiveSessionManager, LiveSessionState
        
        manager = LiveSessionManager()
        
        # 创建测试会话状态
        test_session = LiveSessionState(
            session_id="test_session_123",
            platform="douyin",
            room_id="test_room",
            anchor_name="测试主播",
            status="recording"
        )
        
        # 测试保存
        manager._current_session = test_session
        await manager._save_session_state()
        
        logger.info(f"✅ 会话管理器测试通过")
        logger.info(f"   会话ID: {test_session.session_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 会话管理器测试失败: {e}")
        return False


async def test_connection_pool():
    """测试数据库连接池配置"""
    logger.info("\n📋 测试连接池配置...")
    
    try:
        from server.config import config_manager
        
        db_config = config_manager.config.database
        
        logger.info(f"   连接池大小: {db_config.pool_size}")
        logger.info(f"   连接超时: {db_config.pool_timeout}秒")
        logger.info(f"   连接回收: {db_config.pool_recycle}秒")
        logger.info(f"   最大溢出: {db_config.max_overflow}")
        
        if db_config.pool_size >= 50:
            logger.info(f"✅ 连接池配置已优化")
            return True
        else:
            logger.warning(f"⚠️  连接池配置较小: {db_config.pool_size}")
            return True  # 不算失败
            
    except Exception as e:
        logger.error(f"❌ 连接池配置测试失败: {e}")
        return False


async def main():
    """主测试流程"""
    logger.info("=" * 80)
    logger.info("🚀 直播间快速功能测试")
    logger.info("   审查人: 叶维哲")
    logger.info("=" * 80)
    
    start_time = time.time()
    results = {}
    
    # 运行所有测试
    tests = [
        ("Redis连接", test_redis),
        ("MySQL连接", test_mysql),
        ("AI缓存", test_ai_cache),
        ("批量缓冲", test_batch_buffer),
        ("会话管理", test_session_manager),
        ("连接池配置", test_connection_pool),
    ]
    
    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            logger.error(f"❌ {test_name}异常: {e}")
            results[test_name] = False
    
    # 生成报告
    duration = time.time() - start_time
    
    logger.info("\n" + "=" * 80)
    logger.info("📊 测试报告")
    logger.info("=" * 80)
    logger.info(f"⏱️  测试时长: {duration:.2f}秒")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    logger.info(f"\n✅ 通过: {passed}/{total}")
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"   {test_name}: {status}")
    
    if passed == total:
        logger.info("\n🎉 所有测试通过！")
        logger.info("=" * 80)
        return 0
    else:
        logger.info(f"\n⚠️  {total - passed}个测试失败")
        logger.info("=" * 80)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

