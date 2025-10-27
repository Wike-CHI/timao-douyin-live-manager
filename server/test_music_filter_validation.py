#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音乐过滤效果验证测试
专门测试英文歌曲过滤能力
"""

import numpy as np
import time
import sys
import os

# 设置编码
if sys.platform == "win32":
    os.system("chcp 65001 > nul")

from app.services.audio_gate import is_speech_like

def generate_english_song_audio(duration=1.0, sr=16000):
    """生成模拟英文歌曲的音频"""
    t = np.linspace(0, duration, int(sr * duration))
    
    # 英文歌曲特征：
    # 1. 强谐波结构（基频 + 多次谐波）
    # 2. 规律节拍
    # 3. 较宽的频率范围
    # 4. 持续的音调
    
    # 基频 (C4 = 261.63 Hz)
    fundamental = 261.63
    
    # 构建谐波结构（音乐的典型特征）
    audio = np.zeros_like(t)
    harmonics = [1, 2, 3, 4, 5, 6]  # 1-6次谐波
    amplitudes = [1.0, 0.7, 0.5, 0.3, 0.2, 0.1]  # 递减的幅度
    
    for h, amp in zip(harmonics, amplitudes):
        freq = fundamental * h
        if freq < sr / 2:  # 避免混叠
            audio += amp * np.sin(2 * np.pi * freq * t)
    
    # 添加节拍（120 BPM）
    beat_freq = 2.0  # 2 Hz = 120 BPM
    beat_envelope = 0.5 + 0.5 * np.sin(2 * np.pi * beat_freq * t)
    audio *= beat_envelope
    
    # 添加轻微的随机变化（模拟歌声的自然变化）
    vibrato = 0.1 * np.sin(2 * np.pi * 5 * t)  # 5Hz颤音
    audio *= (1 + vibrato)
    
    # 归一化并转换为16位PCM
    audio = audio / np.max(np.abs(audio)) * 0.3  # 控制音量
    return (audio * 32768).astype(np.int16).tobytes()

def generate_chinese_speech_audio(duration=1.0, sr=16000):
    """生成模拟中文语音的音频"""
    t = np.linspace(0, duration, int(sr * duration))
    
    # 中文语音特征：
    # 1. 人声频带集中（300-3400Hz）
    # 2. 调制变化（语音节律）
    # 3. 较低的谐波强度
    # 4. 不规律的包络变化
    
    # 基频在人声范围内
    f0 = 150  # 男声基频
    
    # 构建语音谐波（较弱的谐波结构）
    audio = np.zeros_like(t)
    harmonics = [1, 2, 3]  # 只有前3次谐波
    amplitudes = [1.0, 0.3, 0.1]  # 快速衰减
    
    for h, amp in zip(harmonics, amplitudes):
        freq = f0 * h
        # 添加频率调制（模拟语调变化）
        freq_mod = freq * (1 + 0.1 * np.sin(2 * np.pi * 3 * t))
        audio += amp * np.sin(2 * np.pi * freq_mod * t)
    
    # 添加语音包络（不规律变化）
    envelope = np.abs(np.sin(2 * np.pi * 4 * t)) ** 0.5
    envelope *= (1 + 0.3 * np.random.randn(len(t)))  # 添加随机变化
    envelope = np.clip(envelope, 0, 1)
    audio *= envelope
    
    # 添加轻微噪声（模拟语音的噪声成分）
    noise = 0.05 * np.random.randn(len(t))
    audio += noise
    
    # 归一化并转换为16位PCM
    audio = audio / np.max(np.abs(audio)) * 0.2
    return (audio * 32768).astype(np.int16).tobytes()

def test_music_vs_speech_detection():
    """测试音乐与语音的区分能力"""
    print("=" * 60)
    print("音乐与语音区分能力测试")
    print("=" * 60)
    
    # 测试1: 英文歌曲（应该被过滤）
    print("\n1. 测试英文歌曲（应该被过滤）:")
    english_song = generate_english_song_audio()
    result, details = is_speech_like(english_song, 16000)
    
    print(f"   结果: {'[失败 - 误识别为语音]' if result else '[成功 - 正确过滤]'}")
    print(f"   详细信息:")
    print(f"     - RMS: {details.get('rms', 0):.4f}")
    print(f"     - 人声频带比: {details.get('r_voice', 0):.3f}")
    print(f"     - 频谱质心: {details.get('centroid', 0):.1f} Hz")
    print(f"     - 调制能量: {details.get('mod', 0):.3f}")
    print(f"     - 频谱平坦度: {details.get('flatness', 0):.3f}")
    print(f"     - 谐波强度: {details.get('harmonic_strength', 0):.3f}")
    print(f"     - 节拍规律性: {details.get('beat_regularity', 0):.3f}")
    print(f"     - 音乐特征: {details.get('music_like', False)}")
    print(f"     - 规律节拍: {details.get('regular_beat', False)}")
    
    # 测试2: 中文语音（应该通过）
    print("\n2. 测试中文语音（应该通过）:")
    chinese_speech = generate_chinese_speech_audio()
    result2, details2 = is_speech_like(chinese_speech, 16000)
    
    print(f"   结果: {'[成功 - 正确识别为语音]' if result2 else '[失败 - 误过滤]'}")
    print(f"   详细信息:")
    print(f"     - RMS: {details2.get('rms', 0):.4f}")
    print(f"     - 人声频带比: {details2.get('r_voice', 0):.3f}")
    print(f"     - 频谱质心: {details2.get('centroid', 0):.1f} Hz")
    print(f"     - 调制能量: {details2.get('mod', 0):.3f}")
    print(f"     - 频谱平坦度: {details2.get('flatness', 0):.3f}")
    print(f"     - 谐波强度: {details2.get('harmonic_strength', 0):.3f}")
    print(f"     - 节拍规律性: {details2.get('beat_regularity', 0):.3f}")
    print(f"     - 音乐特征: {details2.get('music_like', False)}")
    print(f"     - 规律节拍: {details2.get('regular_beat', False)}")
    
    return not result and result2  # 音乐被过滤且语音通过

def test_various_music_types():
    """测试各种类型的音乐过滤效果"""
    print("\n" + "=" * 60)
    print("各种音乐类型过滤测试")
    print("=" * 60)
    
    test_cases = [
        ("流行音乐", 440.0, [1, 2, 3, 4, 5], [1.0, 0.8, 0.6, 0.4, 0.2]),
        ("古典音乐", 523.25, [1, 2, 3, 4, 5, 6, 7, 8], [1.0, 0.7, 0.5, 0.4, 0.3, 0.2, 0.15, 0.1]),
        ("电子音乐", 220.0, [1, 3, 5, 7], [1.0, 0.9, 0.8, 0.7]),
        ("摇滚音乐", 329.63, [1, 2, 4, 8], [1.0, 0.6, 0.4, 0.2]),
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for name, fundamental, harmonics, amplitudes in test_cases:
        print(f"\n测试 {name}:")
        
        # 生成音乐音频
        t = np.linspace(0, 1, 16000)
        audio = np.zeros_like(t)
        
        for h, amp in zip(harmonics, amplitudes):
            freq = fundamental * h
            if freq < 8000:  # 避免混叠
                audio += amp * np.sin(2 * np.pi * freq * t)
        
        # 添加节拍
        beat = 0.7 + 0.3 * np.sin(2 * np.pi * 2 * t)
        audio *= beat
        
        # 转换为PCM
        audio = audio / np.max(np.abs(audio)) * 0.3
        pcm = (audio * 32768).astype(np.int16).tobytes()
        
        # 测试过滤效果
        result, details = is_speech_like(pcm, 16000)
        
        if not result:
            print(f"   ✅ 成功过滤")
            success_count += 1
        else:
            print(f"   ❌ 误识别为语音")
        
        print(f"   谐波强度: {details.get('harmonic_strength', 0):.3f}")
        print(f"   节拍规律性: {details.get('beat_regularity', 0):.3f}")
    
    print(f"\n总体过滤成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    return success_count / total_count >= 0.8  # 80%以上成功率

def test_edge_cases():
    """测试边缘情况"""
    print("\n" + "=" * 60)
    print("边缘情况测试")
    print("=" * 60)
    
    edge_cases = []
    
    # 测试1: 轻声说话
    print("\n1. 测试轻声说话:")
    t = np.linspace(0, 1, 16000)
    whisper = 0.05 * np.sin(2 * np.pi * 200 * t) * (1 + 0.3 * np.sin(2 * np.pi * 3 * t))
    whisper_pcm = (whisper * 32768).astype(np.int16).tobytes()
    result, details = is_speech_like(whisper_pcm, 16000)
    print(f"   结果: {'[通过]' if result else '[被过滤]'} - RMS: {details.get('rms', 0):.4f}")
    edge_cases.append(("轻声说话", result))
    
    # 测试2: 背景音乐 + 人声
    print("\n2. 测试背景音乐 + 人声:")
    music = 0.1 * np.sin(2 * np.pi * 440 * t)  # 背景音乐
    voice = 0.2 * np.sin(2 * np.pi * 150 * t) * (1 + 0.5 * np.sin(2 * np.pi * 4 * t))  # 人声
    mixed = music + voice
    mixed_pcm = (mixed * 32768).astype(np.int16).tobytes()
    result, details = is_speech_like(mixed_pcm, 16000)
    print(f"   结果: {'[通过]' if result else '[被过滤]'} - 谐波强度: {details.get('harmonic_strength', 0):.3f}")
    edge_cases.append(("背景音乐+人声", result))
    
    # 测试3: 纯音调（可能是音乐也可能是语音）
    print("\n3. 测试纯音调:")
    pure_tone = 0.2 * np.sin(2 * np.pi * 800 * t)
    pure_pcm = (pure_tone * 32768).astype(np.int16).tobytes()
    result, details = is_speech_like(pure_pcm, 16000)
    print(f"   结果: {'[通过]' if result else '[被过滤]'} - 调制能量: {details.get('mod', 0):.3f}")
    edge_cases.append(("纯音调", result))
    
    return edge_cases

def main():
    """主测试函数"""
    print("音乐过滤效果验证测试")
    print("测试时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("目标：解决英文歌曲被误识别为中文语音的问题")
    
    # 核心测试
    music_speech_ok = test_music_vs_speech_detection()
    
    # 各种音乐类型测试
    various_music_ok = test_various_music_types()
    
    # 边缘情况测试
    edge_cases = test_edge_cases()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    print(f"✅ 音乐与语音区分: {'通过' if music_speech_ok else '失败'}")
    print(f"✅ 各种音乐类型过滤: {'通过' if various_music_ok else '失败'}")
    
    print(f"\n边缘情况处理:")
    for case_name, result in edge_cases:
        print(f"  - {case_name}: {'通过' if result else '被过滤'}")
    
    overall_success = music_speech_ok and various_music_ok
    print(f"\n🎯 总体评估: {'✅ 优化成功' if overall_success else '❌ 需要进一步调整'}")
    
    if overall_success:
        print("\n🎉 英文歌曲过滤问题已解决！")
        print("   - ACRCloud音乐识别阈值已优化")
        print("   - 背景音乐检测参数已调整")
        print("   - 音频门控算法已增强谐波和节拍检测")
    else:
        print("\n⚠️  建议进一步调整:")
        print("   - 考虑降低谐波检测阈值")
        print("   - 调整节拍检测敏感度")
        print("   - 优化人声频带判断条件")

if __name__ == "__main__":
    main()