# -*- coding: utf-8 -*-
"""
测试音频生成器
生成测试用的PCM音频数据
"""

import numpy as np
import wave
from pathlib import Path


def generate_test_audio(
    output_path: Path,
    duration: float = 10.0,
    sample_rate: int = 16000,
    frequency: int = 440  # A4音符
):
    """
    生成测试音频文件（正弦波）
    
    Args:
        output_path: 输出WAV文件路径
        duration: 音频时长（秒）
        sample_rate: 采样率
        frequency: 正弦波频率
    """
    # 生成正弦波
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * frequency * t)
    
    # 归一化到int16范围
    audio = (audio * 32767).astype(np.int16)
    
    # 保存为WAV
    with wave.open(str(output_path), 'wb') as wav_file:
        wav_file.setnchannels(1)  # 单声道
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())
    
    print(f"✅ 生成测试音频: {output_path} ({duration}s)")


def generate_silence(
    output_path: Path,
    duration: float = 5.0,
    sample_rate: int = 16000
):
    """生成静音音频"""
    samples = int(sample_rate * duration)
    audio = np.zeros(samples, dtype=np.int16)
    
    with wave.open(str(output_path), 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())
    
    print(f"✅ 生成静音音频: {output_path} ({duration}s)")


if __name__ == "__main__":
    test_data_dir = Path(__file__).parent
    
    # 生成测试音频
    generate_test_audio(test_data_dir / "test_audio_10s.wav", duration=10.0)
    generate_silence(test_data_dir / "silence_5s.wav", duration=5.0)
    
    print("✅ 测试音频生成完成")
