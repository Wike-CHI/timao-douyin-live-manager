#!/usr/bin/env python3
"""
专门测试英文歌曲过滤效果的脚本
"""

import numpy as np
import sys
import os
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.audio_gate import is_speech_like

def generate_english_song_audio(duration=2.0, sr=16000):
    """生成模拟英文歌曲的音频信号"""
    t = np.linspace(0, duration, int(sr * duration))
    
    # 英文歌曲特征：
    # 1. 多个谐波频率（和声结构）
    # 2. 规律的节拍模式
    # 3. 较宽的频率范围
    # 4. 持续的音调变化
    
    # 主旋律（基频）
    fundamental = 220  # A3
    melody = np.sin(2 * np.pi * fundamental * t)
    
    # 添加谐波（音乐的典型特征）
    harmonics = (
        0.8 * np.sin(2 * np.pi * fundamental * 2 * t) +  # 2次谐波
        0.6 * np.sin(2 * np.pi * fundamental * 3 * t) +  # 3次谐波
        0.4 * np.sin(2 * np.pi * fundamental * 4 * t) +  # 4次谐波
        0.3 * np.sin(2 * np.pi * fundamental * 5 * t)    # 5次谐波
    )
    
    # 添加和弦（C大调）
    chord_c = np.sin(2 * np.pi * 261.63 * t)  # C4
    chord_e = np.sin(2 * np.pi * 329.63 * t)  # E4
    chord_g = np.sin(2 * np.pi * 392.00 * t)  # G4
    
    # 节拍模式（4/4拍）
    beat_freq = 2.0  # 每秒2拍
    beat_pattern = 0.5 * (1 + np.sin(2 * np.pi * beat_freq * t))
    
    # 组合所有元素
    music_signal = (
        melody * 0.4 +
        harmonics * 0.3 +
        (chord_c + chord_e + chord_g) * 0.2 * beat_pattern +
        np.random.normal(0, 0.05, len(t))  # 轻微噪声
    )
    
    # 添加音量包络（模拟歌声起伏）
    envelope = 0.5 * (1 + np.sin(2 * np.pi * 0.5 * t))
    music_signal *= envelope
    
    # 归一化并转换为PCM16
    music_signal = music_signal / np.max(np.abs(music_signal)) * 0.7
    return (music_signal * 32767).astype(np.int16).tobytes()

def generate_chinese_speech_audio(duration=2.0, sr=16000):
    """生成模拟中文语音的音频信号"""
    t = np.linspace(0, duration, int(sr * duration))
    
    # 中文语音特征：
    # 1. 主要能量在300-3400Hz人声频带
    # 2. 不规律的调制模式（语音节律）
    # 3. 较少的谐波结构
    # 4. 频谱质心在人声范围内
    
    # 基础语音频率（模拟中文声调）
    base_freq = 150  # 男声基频
    
    # 声调变化（中文特有的声调模式）
    tone_pattern = np.concatenate([
        np.linspace(1.0, 1.2, len(t)//4),    # 第一声（平）
        np.linspace(1.2, 0.8, len(t)//4),    # 第二声（升）
        np.linspace(0.8, 0.6, len(t)//4),    # 第三声（降升）
        np.linspace(0.6, 1.0, len(t)//4)     # 第四声（降）
    ])
    
    # 生成语音信号
    speech_signal = np.sin(2 * np.pi * base_freq * tone_pattern * t)
    
    # 添加共振峰（人声的典型特征）
    formant1 = 0.3 * np.sin(2 * np.pi * 800 * t)   # 第一共振峰
    formant2 = 0.2 * np.sin(2 * np.pi * 1200 * t)  # 第二共振峰
    formant3 = 0.1 * np.sin(2 * np.pi * 2400 * t)  # 第三共振峰
    
    # 语音调制（不规律的包络）
    modulation = np.random.uniform(0.3, 1.0, len(t))
    
    # 组合语音信号
    speech_signal = (
        speech_signal * 0.6 +
        formant1 + formant2 + formant3 +
        np.random.normal(0, 0.02, len(t))  # 轻微噪声
    ) * modulation
    
    # 归一化并转换为PCM16
    speech_signal = speech_signal / np.max(np.abs(speech_signal)) * 0.5
    return (speech_signal * 32767).astype(np.int16).tobytes()

def test_english_music_filtering():
    """测试英文歌曲过滤效果"""
    print("=" * 60)
    print("英文歌曲过滤效果专项测试")
    print("=" * 60)
    
    # 测试1: 英文歌曲（应该被过滤）
    print("\n1. 测试英文歌曲（应该被过滤）:")
    english_music = generate_english_song_audio()
    keep, debug = is_speech_like(english_music)
    
    result_text = "✅ 成功过滤" if not keep else "❌ 误识别为语音"
    print(f"   结果: {result_text}")
    print(f"   详细信息:")
    print(f"     - RMS: {debug['rms']:.4f}")
    print(f"     - 人声频带比: {debug['r_voice']:.3f}")
    print(f"     - 频谱质心: {debug['centroid']:.1f} Hz")
    print(f"     - 调制能量: {debug['mod']:.3f}")
    print(f"     - 频谱平坦度: {debug['flatness']:.3f}")
    print(f"     - 谐波强度: {debug['harmonic_strength']:.3f}")
    print(f"     - 节拍规律性: {debug['beat_regularity']:.3f}")
    print(f"     - 基础语音条件: {debug['basic_speech_criteria']}")
    print(f"     - 强音乐特征: {debug['strong_music_features']}")
    
    # 测试2: 中文语音（应该通过）
    print("\n2. 测试中文语音（应该通过）:")
    chinese_speech = generate_chinese_speech_audio()
    keep2, debug2 = is_speech_like(chinese_speech)
    
    result_text2 = "✅ 成功通过" if keep2 else "❌ 误过滤"
    print(f"   结果: {result_text2}")
    print(f"   详细信息:")
    print(f"     - RMS: {debug2['rms']:.4f}")
    print(f"     - 人声频带比: {debug2['r_voice']:.3f}")
    print(f"     - 频谱质心: {debug2['centroid']:.1f} Hz")
    print(f"     - 调制能量: {debug2['mod']:.3f}")
    print(f"     - 频谱平坦度: {debug2['flatness']:.3f}")
    print(f"     - 谐波强度: {debug2['harmonic_strength']:.3f}")
    print(f"     - 节拍规律性: {debug2['beat_regularity']:.3f}")
    print(f"     - 基础语音条件: {debug2['basic_speech_criteria']}")
    print(f"     - 强音乐特征: {debug2['strong_music_features']}")
    
    # 测试结果总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    music_filtered = not keep
    speech_passed = keep2
    
    print(f"英文歌曲过滤: {'✅ 成功' if music_filtered else '❌ 失败'}")
    print(f"中文语音通过: {'✅ 成功' if speech_passed else '❌ 失败'}")
    
    if music_filtered and speech_passed:
        print("\n🎯 总体评估: ✅ 优秀 - 能够正确区分英文歌曲和中文语音")
    elif music_filtered or speech_passed:
        print("\n🎯 总体评估: ⚠️  部分成功 - 需要进一步调整")
    else:
        print("\n🎯 总体评估: ❌ 需要优化 - 无法正确区分音乐和语音")
    
    # 参数建议
    print("\n📊 参数分析:")
    if not music_filtered:
        print("   - 英文歌曲未被过滤，建议:")
        if debug['harmonic_strength'] <= 0.8:
            print("     * 降低谐波检测阈值 (当前: 0.8)")
        if debug['beat_regularity'] <= 0.7:
            print("     * 降低节拍检测阈值 (当前: 0.7)")
        if debug['basic_speech_criteria']:
            print("     * 收紧基础语音条件")
    
    if not speech_passed:
        print("   - 中文语音被误过滤，建议:")
        if not debug2['basic_speech_criteria']:
            print("     * 放宽基础语音条件")
        if debug2['strong_music_features']:
            print("     * 提高音乐特征检测阈值")

if __name__ == "__main__":
    test_english_music_filtering()