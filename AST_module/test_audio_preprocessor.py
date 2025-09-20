#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频预处理增强器测试
测试SpectralGateDenoiser、VolumeNormalizer、AudioQualityMonitor等组件功能
"""

import unittest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# 添加AST_module到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audio_preprocessor_enhanced import (
    AudioPreprocessorEnhanced, 
    AudioProcessingConfig,
    AudioQuality
)

class TestAudioPreprocessorEnhanced(unittest.TestCase):
    """音频预处理增强器测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.config = AudioProcessingConfig(
            sample_rate=16000,
            frame_size=1024,
            noise_reduction_strength=0.8,
            silence_threshold=0.01,
            volume_target=0.7
        )
        self.processor = AudioPreprocessorEnhanced(self.config)
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.processor)
        self.assertEqual(self.processor.config.sample_rate, 16000)
        self.assertEqual(self.processor.config.frame_size, 1024)
    
    def test_audio_quality_assessment(self):
        """测试音频质量评估"""
        # 生成测试音频数据（正弦波）
        duration = 1.0  # 1秒
        sample_rate = 16000
        frequency = 440  # A音符
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32) * 0.5
        
        # 评估音频质量
        quality = self.processor.quality_monitor.assess_quality(audio_data, sample_rate)
        
        # 验证质量评估结果
        self.assertIsInstance(quality, AudioQuality)
        self.assertGreaterEqual(quality.snr_db or 0, 0)
        self.assertGreaterEqual(quality.volume_level, 0)
        self.assertLessEqual(quality.volume_level, 1.0)
        self.assertGreaterEqual(quality.clarity_score, 0)
        self.assertLessEqual(quality.clarity_score, 1.0)
    
    def test_process_audio_chunk_clean(self):
        """测试处理干净音频"""
        # 生成干净的测试音频（16位PCM格式）
        duration = 0.5  # 0.5秒
        sample_rate = 16000
        frequency = 880  # 高一点的频率
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_float = np.sin(2 * np.pi * frequency * t) * 0.3  # 较小的音量
        audio_int16 = (audio_float * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()
        
        # 处理音频
        processed_bytes, quality = self.processor.process_audio_chunk(audio_bytes)
        
        # 验证结果
        self.assertIsInstance(processed_bytes, bytes)
        self.assertIsInstance(quality, AudioQuality)
        self.assertGreater(len(processed_bytes), 0)
        self.assertLessEqual(quality.noise_level, 0.5)  # 干净音频的噪声应该较低
    
    def test_process_audio_chunk_noisy(self):
        """测试处理含噪声音频"""
        # 生成含噪声的测试音频
        duration = 0.5
        sample_rate = 16000
        frequency = 440
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # 信号 + 噪声
        signal = np.sin(2 * np.pi * frequency * t) * 0.5
        noise = np.random.normal(0, 0.2, len(t))  # 添加高斯噪声
        audio_float = signal + noise
        
        # 转换为16位PCM
        audio_int16 = np.clip(audio_float * 32767, -32767, 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()
        
        # 处理音频
        processed_bytes, quality = self.processor.process_audio_chunk(audio_bytes)
        
        # 验证结果
        self.assertIsInstance(processed_bytes, bytes)
        self.assertIsInstance(quality, AudioQuality)
        self.assertGreater(quality.noise_level, 0.1)  # 含噪声音频的噪声水平应该更高
    
    def test_silence_detection(self):
        """测试静音检测"""
        # 生成静音音频
        duration = 0.5
        sample_rate = 16000
        audio_float = np.zeros(int(sample_rate * duration), dtype=np.float32)
        audio_int16 = (audio_float * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()
        
        # 处理音频
        processed_bytes, quality = self.processor.process_audio_chunk(audio_bytes)
        
        # 验证静音检测
        self.assertLessEqual(quality.volume_level, 0.02)  # 静音的音量应该很低
    
    def test_volume_normalization(self):
        """测试音量归一化"""
        # 生成低音量音频
        duration = 0.5
        sample_rate = 16000
        frequency = 440
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_float = np.sin(2 * np.pi * frequency * t) * 0.1  # 很低的音量
        audio_int16 = (audio_float * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()
        
        # 处理音频（应该进行归一化）
        processed_bytes, quality = self.processor.process_audio_chunk(audio_bytes)
        
        # 验证归一化效果
        processed_array = np.frombuffer(processed_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        processed_rms = np.sqrt(np.mean(processed_array ** 2))
        
        # 归一化后的RMS应该接近目标值
        self.assertGreater(processed_rms, 0.2)  # 应该被放大了
    
    def test_config_validation(self):
        """测试配置验证"""
        # 测试有效配置
        valid_config = AudioProcessingConfig(
            sample_rate=16000,
            frame_size=1024,
            noise_reduction_strength=0.5,
            silence_threshold=0.01,
            volume_target=0.7
        )
        processor = AudioPreprocessorEnhanced(valid_config)
        self.assertIsNotNone(processor)
        
        # 测试边界值
        boundary_config = AudioProcessingConfig(
            sample_rate=8000,  # 最低支持采样率
            frame_size=512,    # 最小块大小
            noise_reduction_strength=1.0,  # 最大降噪强度
            silence_threshold=0.0,         # 最低静音阈值
            volume_target=1.0       # 最大归一化目标
        )
        processor = AudioPreprocessorEnhanced(boundary_config)
        self.assertIsNotNone(processor)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)