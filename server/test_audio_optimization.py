#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频处理优化效果测试脚本
测试优化后的VAD、AGC、音频门控等功能
"""

import numpy as np
import time
import sys
import os

# 设置编码
if sys.platform == "win32":
    os.system("chcp 65001 > nul")

from app.services.audio_gate import is_speech_like
from app.services.live_audio_stream_service import LiveAudioStreamService

def test_audio_gate():
    """测试音频门控算法"""
    print("=" * 50)
    print("测试音频门控算法")
    print("=" * 50)
    
    # 测试1: 随机噪声（应该被过滤）
    print("\n1. 测试随机噪声:")
    noise = (np.random.randn(16000) * 0.1 * 32768).astype(np.int16).tobytes()
    result, details = is_speech_like(noise, 16000)
    print(f"   结果: {'[通过]' if not result else '[失败]'} - {details.get('reason', 'unknown')}")
    print(f"   详细信息: RMS={details.get('rms', 0):.4f}, 人声频带={details.get('r_voice', 0):.3f}")
    
    # 测试2: 单一频率音调（模拟人声）
    print("\n2. 测试人声频率 (800Hz):")
    speech_freq = (np.sin(2 * np.pi * 800 * np.linspace(0, 1, 16000)) * 0.2 * 32768).astype(np.int16).tobytes()
    result, details = is_speech_like(speech_freq, 16000)
    print(f"   结果: {'[需要调整]' if not result else '[检测到人声]'} - {details}")
    
    # 测试3: 复合人声频率
    print("\n3. 测试复合人声频率:")
    t = np.linspace(0, 1, 16000)
    complex_speech = (
        0.3 * np.sin(2 * np.pi * 400 * t) +  # 基频
        0.2 * np.sin(2 * np.pi * 800 * t) +  # 二次谐波
        0.1 * np.sin(2 * np.pi * 1200 * t) + # 三次谐波
        0.05 * np.random.randn(16000)        # 轻微噪声
    )
    complex_speech = (complex_speech * 0.15 * 32768).astype(np.int16).tobytes()
    result, details = is_speech_like(complex_speech, 16000)
    print(f"   结果: {'[检测到人声]' if result else '[需要调整]'} - {details.get('reason', 'unknown')}")
    
    # 测试4: 低频音乐（应该被过滤）
    print("\n4. 测试低频音乐:")
    music = (np.sin(2 * np.pi * 200 * np.linspace(0, 1, 16000)) * 0.3 * 32768).astype(np.int16).tobytes()
    result, details = is_speech_like(music, 16000)
    print(f"   结果: {'[通过]' if not result else '[失败]'} - {details.get('reason', 'unknown')}")

def test_vad_parameters():
    """测试VAD参数优化效果"""
    print("\n" + "=" * 50)
    print("测试VAD参数配置")
    print("=" * 50)
    
    try:
        # 创建LiveAudioStreamService实例来检查参数
        service = LiveAudioStreamService()
        
        print(f"VAD最小静音时长: {service.vad_min_silence_sec}s (优化后: 0.60s)")
        print(f"VAD最小语音时长: {service.vad_min_speech_sec}s (优化后: 0.35s)")
        print(f"VAD延迟时长: {service.vad_hangover_sec}s (优化后: 0.40s)")
        print(f"VAD最小RMS: {service.vad_min_rms} (优化后: 0.015)")
        
        print(f"\nAGC目标RMS: {service.agc_target_rms} (优化后: 0.08)")
        print(f"AGC最大增益: {service.agc_max_gain} (优化后: 6.0)")
        print(f"AGC最小增益: {service.agc_min_gain} (优化后: 0.3)")
        print(f"AGC平滑系数: {service.agc_smooth} (优化后: 0.15)")
        
        print(f"\n背景音乐检测阈值: {service.music_detect_threshold} (优化后: 0.52)")
        print(f"背景音乐释放阈值: {service.music_release_threshold} (优化后: 0.40)")
        print(f"背景音乐RMS增强: {service.music_rms_boost} (优化后: 1.8)")
        
        print("\n✅ VAD参数配置检查完成")
        
    except Exception as e:
        print(f"❌ VAD参数测试失败: {e}")

def test_performance():
    """测试性能"""
    print("\n" + "=" * 50)
    print("性能测试")
    print("=" * 50)
    
    # 测试音频门控算法性能
    test_audio = (np.random.randn(16000) * 0.1 * 32768).astype(np.int16).tobytes()
    
    start_time = time.time()
    for _ in range(100):
        is_speech_like(test_audio, 16000)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 100 * 1000  # 转换为毫秒
    print(f"音频门控算法平均处理时间: {avg_time:.2f}ms")
    print(f"实时处理能力: {'[优秀]' if avg_time < 10 else '[需要优化]' if avg_time < 50 else '[性能不足]'}")

if __name__ == "__main__":
    print("音频处理优化效果测试")
    print("测试时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    
    test_audio_gate()
    test_vad_parameters()
    test_performance()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)