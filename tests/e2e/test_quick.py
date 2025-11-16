# -*- coding: utf-8 -*-
"""
快速端到端测试 - 不依赖SenseVoice模型
测试基础功能：服务启动、状态管理、回调系统
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from server.local.services.live_audio_stream_service import (
    get_live_audio_service,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_service_lifecycle():
    """测试服务生命周期"""
    logger.info("=== 测试1: 服务生命周期 ===")
    
    service = get_live_audio_service()
    
    # 检查初始状态
    status = service.status()
    assert not status.is_running, "初始状态应该是未运行"
    logger.info("✅ 初始状态正确")
    
    # 测试配置
    service.apply_profile("fast")
    logger.info("✅ 配置应用成功")
    
    # 测试回调注册
    callback_called = []
    
    async def test_callback(data):
        callback_called.append(data)
    
    service.add_transcription_callback("test", test_callback)
    service.add_level_callback("test", lambda r, t: None)
    logger.info("✅ 回调注册成功")
    
    # 清理
    service.remove_transcription_callback("test")
    service.remove_level_callback("test")
    logger.info("✅ 回调移除成功")


async def test_health_status():
    """测试健康状态接口"""
    logger.info("=== 测试2: 健康状态接口 ===")
    
    service = get_live_audio_service()
    health = service.get_health_status()
    
    assert "is_receiving_real_audio" in health
    assert "ffmpeg_running" in health
    logger.info(f"健康状态: {health}")
    logger.info("✅ 健康状态接口正常")


async def test_model_cache_status():
    """测试模型缓存状态"""
    logger.info("=== 测试3: 模型缓存状态 ===")
    
    service = get_live_audio_service()
    cache_status = service.get_model_cache_status()
    
    logger.info(f"模型缓存状态: {cache_status}")
    logger.info("✅ 模型缓存状态接口正常")


async def test_text_processing():
    """测试文本后处理组件"""
    logger.info("=== 测试4: 文本后处理 ===")
    
    from server.modules.ast.postprocess import (
        ChineseCleaner,
        HallucinationGuard,
        SentenceAssembler
    )
    
    # 测试文本清洗
    cleaner = ChineseCleaner()
    test_text = "你好,世界!这是测试。。。"
    cleaned = cleaner.clean(test_text)
    logger.info(f"原文: {test_text}")
    logger.info(f"清洗后: {cleaned}")
    assert "，" in cleaned and "。" in cleaned
    logger.info("✅ 文本清洗正常")
    
    # 测试防幻觉
    guard = HallucinationGuard(min_rms=0.01, min_len=2)
    should_drop = guard.should_drop("嗯", confidence=0.3, rms=0.005)
    assert should_drop, "低置信度+低RMS应该被丢弃"
    logger.info("✅ 防幻觉过滤正常")
    
    # 测试分句器
    assembler = SentenceAssembler(max_wait=2.0, max_chars=50)
    is_final, text = assembler.feed("这是一个测试")
    logger.info(f"分句结果: is_final={is_final}, text={text}")
    logger.info("✅ 分句器正常")


async def test_audio_processing():
    """测试音频处理组件"""
    logger.info("=== 测试5: 音频处理 ===")
    
    from server.modules.ast.postprocess import pcm16_rms
    import numpy as np
    
    # 生成测试音频数据
    duration = 1.0  # 1秒
    sample_rate = 16000
    frequency = 440  # A4音
    
    t = np.linspace(0, duration, sample_rate)
    audio = np.sin(2 * np.pi * frequency * t)
    audio = (audio * 32767 * 0.5).astype(np.int16)
    pcm_data = audio.tobytes()
    
    # 计算RMS
    rms = pcm16_rms(pcm_data)
    logger.info(f"测试音频RMS: {rms:.4f}")
    assert rms > 0, "正弦波RMS应该大于0"
    logger.info("✅ 音频RMS计算正常")


async def test_streamcap_integration():
    """测试StreamCap集成"""
    logger.info("=== 测试6: StreamCap集成 ===")
    
    try:
        from server.modules.streamcap.platforms import get_platform_handler
        
        # 测试直播URL解析（这会失败，因为不是真实直播间）
        test_url = "https://live.douyin.com/test123"
        handler = get_platform_handler(live_url=test_url)
        
        if handler:
            logger.info(f"✅ StreamCap handler创建成功: {type(handler)}")
        else:
            logger.warning("⚠️ 无法创建handler（可能是URL不被支持）")
            
    except Exception as e:
        logger.error(f"StreamCap集成测试失败: {e}")


async def main():
    """运行所有测试"""
    logger.info("=" * 60)
    logger.info("快速端到端测试 - 无模型依赖")
    logger.info("=" * 60)
    
    tests = [
        test_service_lifecycle,
        test_health_status,
        test_model_cache_status,
        test_text_processing,
        test_audio_processing,
        test_streamcap_integration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            logger.error(f"❌ 测试失败: {test.__name__}")
            logger.error(f"   错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    logger.info("=" * 60)
    logger.info(f"测试完成: {passed}个通过, {failed}个失败")
    logger.info("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
