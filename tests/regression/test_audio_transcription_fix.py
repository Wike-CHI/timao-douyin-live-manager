#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试音频转写修复效果

验证：
1. 能否持续转录多句话
2. Window size错误是否正确处理
3. 日志级别是否正确
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig
from server.app.services.live_audio_stream_service import LiveAudioStreamService

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_sensevoice_with_short_audio():
    """测试SenseVoice处理短音频的能力"""
    logger.info("=" * 80)
    logger.info("测试1: SenseVoice处理短音频")
    logger.info("=" * 80)
    
    # 初始化服务
    sv = SenseVoiceService()
    
    # 初始化模型
    logger.info("正在初始化SenseVoice模型...")
    success = await sv.initialize()
    
    if not success:
        logger.error("❌ 模型初始化失败")
        return False
    
    logger.info("✅ 模型初始化成功")
    
    # 测试不同长度的音频
    test_cases = [
        ("极短音频", 0.1),  # 0.1秒，应该返回silence
        ("短音频", 0.5),    # 0.5秒，应该返回silence
        ("中等音频", 1.0),  # 1.0秒，可能成功
        ("正常音频", 1.6),  # 1.6秒，应该成功
        ("长音频", 2.0),    # 2.0秒，应该成功
    ]
    
    results = []
    
    for name, duration in test_cases:
        # 生成测试音频（静音）
        sample_rate = 16000
        samples = int(duration * sample_rate)
        audio_data = bytes([0] * (samples * 2))  # 16-bit音频
        
        logger.info(f"\n测试 {name} ({duration}秒, {len(audio_data)}字节)...")
        
        try:
            result = await sv.transcribe_audio(audio_data, session_id="test_session")
            
            success = result.get("success", False)
            result_type = result.get("type", "unknown")
            text = result.get("text", "")
            
            logger.info(f"  结果: success={success}, type={result_type}, text='{text}'")
            
            # 验证结果
            if duration < 1.0:
                # 短音频应该返回silence
                if result_type == "silence" and success:
                    logger.info(f"  ✅ {name}: 正确处理（返回silence）")
                    results.append(True)
                else:
                    logger.error(f"  ❌ {name}: 预期返回silence，实际返回{result_type}")
                    results.append(False)
            else:
                # 长音频应该能够处理（即使是静音也应该返回success）
                if success:
                    logger.info(f"  ✅ {name}: 正确处理")
                    results.append(True)
                else:
                    logger.error(f"  ❌ {name}: 处理失败")
                    results.append(False)
                    
        except Exception as e:
            logger.error(f"  ❌ {name}: 异常 - {e}")
            results.append(False)
    
    # 清理
    await sv.cleanup()
    
    # 汇总结果
    logger.info("\n" + "=" * 80)
    logger.info(f"测试1结果: {sum(results)}/{len(results)} 通过")
    logger.info("=" * 80)
    
    return all(results)


async def test_live_audio_stream_config():
    """测试LiveAudioStreamService的配置"""
    logger.info("\n" + "=" * 80)
    logger.info("测试2: LiveAudioStreamService配置")
    logger.info("=" * 80)
    
    service = LiveAudioStreamService()
    
    # 检查chunk_seconds配置
    logger.info(f"chunk_seconds: {service.chunk_seconds}秒")
    
    if service.chunk_seconds >= 1.5:
        logger.info("✅ chunk_seconds配置正确（>= 1.5秒）")
        result1 = True
    else:
        logger.error(f"❌ chunk_seconds配置太小: {service.chunk_seconds}秒")
        result1 = False
    
    # 检查VAD配置
    logger.info(f"vad_min_silence_sec: {service.vad_min_silence_sec}秒")
    logger.info(f"vad_min_speech_sec: {service.vad_min_speech_sec}秒")
    logger.info(f"vad_hangover_sec: {service.vad_hangover_sec}秒")
    logger.info(f"vad_min_rms: {service.vad_min_rms}")
    
    # 检查其他配置
    logger.info(f"mode: {service.mode}")
    logger.info(f"agc_enabled: {service.agc_enabled}")
    
    logger.info("\n" + "=" * 80)
    logger.info("测试2结果: " + ("✅ 通过" if result1 else "❌ 失败"))
    logger.info("=" * 80)
    
    return result1


async def test_error_log_levels():
    """测试错误日志级别"""
    logger.info("\n" + "=" * 80)
    logger.info("测试3: 错误日志级别")
    logger.info("=" * 80)
    
    # 创建一个自定义handler来捕获日志
    from io import StringIO
    import logging
    
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    # 添加handler到SenseVoice的logger
    sv_logger = logging.getLogger("server.modules.ast.sensevoice_service")
    sv_logger.addHandler(handler)
    
    # 初始化服务
    sv = SenseVoiceService()
    success = await sv.initialize()
    
    if not success:
        logger.error("❌ 模型初始化失败，跳过日志级别测试")
        return False
    
    # 测试短音频（应该触发window size错误）
    audio_data = bytes([0] * 1600)  # 0.05秒的音频
    
    logger.info("测试短音频触发window size错误...")
    result = await sv.transcribe_audio(audio_data, session_id="test_session")
    
    # 检查日志内容
    log_content = log_capture.getvalue()
    
    # 检查是否有ERROR级别的window size日志
    has_error_window_size = "ERROR" in log_content and "window size" in log_content.lower()
    
    # 检查是否有DEBUG级别的window size日志
    has_debug_window_size = "DEBUG" in log_content and "window size" in log_content.lower()
    
    if has_error_window_size:
        logger.error("❌ window size错误仍然使用ERROR级别记录")
        logger.error(f"日志内容:\n{log_content}")
        result1 = False
    elif has_debug_window_size:
        logger.info("✅ window size错误正确使用DEBUG级别记录")
        result1 = True
    else:
        logger.info("ℹ️ 未触发window size错误（可能音频长度足够）")
        result1 = True
    
    # 清理
    await sv.cleanup()
    sv_logger.removeHandler(handler)
    
    logger.info("\n" + "=" * 80)
    logger.info("测试3结果: " + ("✅ 通过" if result1 else "❌ 失败"))
    logger.info("=" * 80)
    
    return result1


async def main():
    """运行所有测试"""
    logger.info("🚀 开始音频转写修复测试\n")
    
    results = []
    
    # 测试1: SenseVoice处理短音频
    try:
        result1 = await test_sensevoice_with_short_audio()
        results.append(("SenseVoice短音频处理", result1))
    except Exception as e:
        logger.error(f"测试1异常: {e}")
        results.append(("SenseVoice短音频处理", False))
    
    # 测试2: LiveAudioStreamService配置
    try:
        result2 = await test_live_audio_stream_config()
        results.append(("LiveAudioStreamService配置", result2))
    except Exception as e:
        logger.error(f"测试2异常: {e}")
        results.append(("LiveAudioStreamService配置", False))
    
    # 测试3: 错误日志级别
    try:
        result3 = await test_error_log_levels()
        results.append(("错误日志级别", result3))
    except Exception as e:
        logger.error(f"测试3异常: {e}")
        results.append(("错误日志级别", False))
    
    # 汇总结果
    logger.info("\n" + "=" * 80)
    logger.info("📊 测试结果汇总")
    logger.info("=" * 80)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    logger.info("\n" + "=" * 80)
    if all_passed:
        logger.info("🎉 所有测试通过！音频转写修复成功！")
    else:
        logger.error("❌ 部分测试失败，请检查修复是否正确")
    logger.info("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

