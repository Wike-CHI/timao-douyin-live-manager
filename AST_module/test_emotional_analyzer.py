#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情感分析器测试
测试情感语调分析功能
"""

import unittest
import numpy as np
import sys
import os

# 添加AST_module到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from emotional_analyzer_enhanced import (
    EmotionalAnalyzerEnhanced,
    TextEmotionAnalyzer,
    SpeechRateAnalyzer,
    PausePatternAnalyzer,
    ProsodyAnalyzer
)
from enhanced_transcription_result import (
    EmotionalFeatures,
    EmotionType,
    AudioQuality
)

class TestEmotionalAnalyzerEnhanced(unittest.TestCase):
    """情感分析器测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.analyzer = EmotionalAnalyzerEnhanced()
        
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.analyzer)
        self.assertIsInstance(self.analyzer.text_analyzer, TextEmotionAnalyzer)
        self.assertIsInstance(self.analyzer.speech_rate_analyzer, SpeechRateAnalyzer)
        self.assertIsInstance(self.analyzer.pause_analyzer, PausePatternAnalyzer)
        self.assertIsInstance(self.analyzer.prosody_analyzer, ProsodyAnalyzer)
    
    def test_text_only_emotion_analysis(self):
        """测试纯文本情感分析"""
        # 兴奋情感
        excited_text = "哇太棒了这款口红超级好看我爱了"
        excited_result = self.analyzer.analyze_comprehensive_emotion(
            text=excited_text,
            duration=2.0
        )
        
        self.assertIsInstance(excited_result, EmotionalFeatures)
        self.assertEqual(excited_result.emotion_type, EmotionType.EXCITED)
        self.assertGreater(excited_result.intensity, 0.5)
        
        # 平静情感
        calm_text = "这个产品还可以比较稳定"
        calm_result = self.analyzer.analyze_comprehensive_emotion(
            text=calm_text,
            duration=2.0
        )
        
        # 平静文本的情感强度应该较低
        self.assertLess(calm_result.intensity, excited_result.intensity)
    
    def test_speech_rate_analysis(self):
        """测试语速分析"""
        # 快语速文本（更多词汇）
        fast_text = "今天给大家推荐这款超级好用的面膜真的特别棒"
        fast_result = self.analyzer.analyze_comprehensive_emotion(
            text=fast_text,
            duration=2.0  # 短时间内说很多话
        )
        
        # 慢语速文本（相同词汇，更长时间）
        slow_result = self.analyzer.analyze_comprehensive_emotion(
            text=fast_text,
            duration=8.0  # 长时间说相同的话
        )
        
        # 快语速应该明显高于慢语速
        self.assertGreater(fast_result.speech_rate, slow_result.speech_rate)
        self.assertGreater(fast_result.speech_rate, 200)  # 快语速应该>200词/分钟
        self.assertLess(slow_result.speech_rate, 120)     # 慢语速应该<120词/分钟
    
    def test_audio_enhanced_analysis(self):
        """测试音频增强分析"""
        text = "这个面膜真的很好用"
        duration = 3.0
        
        # 生成测试音频数据
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # 高质量音频（清晰的正弦波）
        high_quality_audio = np.sin(2 * np.pi * 200 * t) * 0.5  # 200Hz基频
        high_quality = AudioQuality(
            noise_level=0.1,
            volume_level=0.7,
            clarity_score=0.9,
            sample_rate=sample_rate
        )
        
        # 低质量音频（带噪声）
        noise = np.random.normal(0, 0.3, len(t))
        low_quality_audio = np.sin(2 * np.pi * 150 * t) * 0.3 + noise
        low_quality = AudioQuality(
            noise_level=0.8,
            volume_level=0.3,
            clarity_score=0.2,
            sample_rate=sample_rate
        )
        
        high_quality_result = self.analyzer.analyze_comprehensive_emotion(
            text=text,
            audio_data=high_quality_audio,
            duration=duration,
            audio_quality=high_quality
        )
        
        low_quality_result = self.analyzer.analyze_comprehensive_emotion(
            text=text,
            audio_data=low_quality_audio,
            duration=duration,
            audio_quality=low_quality
        )
        
        # 高质量音频应该有更高的语调置信度
        self.assertGreaterEqual(
            high_quality_result.tone_confidence,
            low_quality_result.tone_confidence
        )
    
    def test_comprehensive_emotion_detection(self):
        """测试综合情感检测"""
        # 强烈兴奋的文本
        excited_text = "天哪这款口红的颜色绝了太美了我超级爱"
        
        # 生成模拟兴奋语音（高基频，快语速）
        duration = 2.0
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # 模拟兴奋的语音特征：高基频 + 音调变化
        base_freq = 220  # 较高的基频
        freq_variation = 50 * np.sin(2 * np.pi * 3 * t)  # 音调变化
        excited_audio = np.sin(2 * np.pi * (base_freq + freq_variation) * t) * 0.6
        
        audio_quality = AudioQuality(
            noise_level=0.2,
            volume_level=0.8,
            clarity_score=0.8,
            sample_rate=sample_rate
        )
        
        result = self.analyzer.analyze_comprehensive_emotion(
            text=excited_text,
            audio_data=excited_audio,
            duration=duration,
            audio_quality=audio_quality
        )
        
        # 验证检测结果
        self.assertEqual(result.emotion_type, EmotionType.EXCITED)
        self.assertGreater(result.intensity, 0.6)  # 强烈的情感强度
        self.assertGreater(result.speech_rate, 180)  # 较快的语速
        self.assertGreater(result.tone_confidence, 0.5)  # 合理的置信度

class TestTextEmotionAnalyzer(unittest.TestCase):
    """文本情感分析器测试"""
    
    def setUp(self):
        self.analyzer = TextEmotionAnalyzer()
    
    def test_excited_emotion_detection(self):
        """测试兴奋情感检测"""
        excited_texts = [
            "哇太棒了这个真的超级好",
            "我的天啊绝了yyds",
            "激动死了太开心了"
        ]
        
        for text in excited_texts:
            emotion, intensity, details = self.analyzer.analyze_text_emotion(text)
            self.assertEqual(emotion, EmotionType.EXCITED)
            self.assertGreater(intensity, 0.5)
    
    def test_joyful_emotion_detection(self):
        """测试愉悦情感检测"""
        joyful_texts = [
            "很喜欢这个颜色真的很美",
            "开心满意这次购买体验",
            "爱了爱了完美的选择"
        ]
        
        for text in joyful_texts:
            emotion, intensity, details = self.analyzer.analyze_text_emotion(text)
            self.assertIn(emotion, [EmotionType.JOYFUL, EmotionType.EXCITED])
            self.assertGreater(intensity, 0.4)
    
    def test_calm_emotion_detection(self):
        """测试平静情感检测"""
        calm_texts = [
            "这个产品还不错比较稳定",
            "从容考虑一下这个选择",
            "理性分析这个方案"
        ]
        
        for text in calm_texts:
            emotion, intensity, details = self.analyzer.analyze_text_emotion(text)
            # 平静情感可能被识别为中性或平静
            self.assertIn(emotion, [EmotionType.CALM, EmotionType.NEUTRAL])
    
    def test_intensity_modifiers(self):
        """测试强度修饰词"""
        base_text = "好看"
        
        # 高强度修饰
        high_intensity_text = "超级好看"
        high_emotion, high_intensity, _ = self.analyzer.analyze_text_emotion(high_intensity_text)
        
        # 低强度修饰
        low_intensity_text = "有点好看"
        low_emotion, low_intensity, _ = self.analyzer.analyze_text_emotion(low_intensity_text)
        
        # 高强度修饰应该产生更高的强度值
        self.assertGreater(high_intensity, low_intensity)

class TestSpeechRateAnalyzer(unittest.TestCase):
    """语速分析器测试"""
    
    def setUp(self):
        self.analyzer = SpeechRateAnalyzer()
    
    def test_speech_rate_calculation(self):
        """测试语速计算"""
        # 中等长度文本
        text = "今天给大家推荐这款面膜"
        
        # 不同时长的语速计算
        fast_rate = self.analyzer.calculate_speech_rate(text, duration=2.0)
        normal_rate = self.analyzer.calculate_speech_rate(text, duration=4.0)
        slow_rate = self.analyzer.calculate_speech_rate(text, duration=8.0)
        
        # 验证语速关系
        self.assertGreater(fast_rate, normal_rate)
        self.assertGreater(normal_rate, slow_rate)
        
        # 验证合理范围
        self.assertGreater(fast_rate, 100)
        self.assertLess(slow_rate, 200)
    
    def test_speech_rate_pattern_analysis(self):
        """测试语速模式分析"""
        # 非常快的语速
        very_fast_analysis = self.analyzer.analyze_speech_rate_pattern(250)
        self.assertEqual(very_fast_analysis["rate_category"], "very_fast")
        
        # 正常语速
        normal_analysis = self.analyzer.analyze_speech_rate_pattern(160)
        self.assertEqual(normal_analysis["rate_category"], "normal")
        
        # 很慢的语速
        very_slow_analysis = self.analyzer.analyze_speech_rate_pattern(80)
        self.assertEqual(very_slow_analysis["rate_category"], "very_slow")
    
    def test_emotion_speech_rate_mapping(self):
        """测试情感与语速的映射关系"""
        # 兴奋情感范围内的语速
        excited_analysis = self.analyzer.analyze_speech_rate_pattern(200)
        possible_emotions = [e["emotion"] for e in excited_analysis["possible_emotions"]]
        self.assertIn(EmotionType.EXCITED, possible_emotions)

class TestPausePatternAnalyzer(unittest.TestCase):
    """停顿模式分析器测试"""
    
    def setUp(self):
        self.analyzer = PausePatternAnalyzer()
    
    def test_pause_detection(self):
        """测试停顿检测"""
        sample_rate = 16000
        duration = 4.0
        
        # 创建带停顿的音频：前1秒有声音，中间2秒静音，最后1秒有声音
        t1 = np.linspace(0, 1, sample_rate)
        t2 = np.linspace(0, 2, 2 * sample_rate)  # 2秒静音
        t3 = np.linspace(0, 1, sample_rate)
        
        audio_part1 = np.sin(2 * np.pi * 200 * t1) * 0.5
        silence_part = np.zeros(len(t2))  # 静音段
        audio_part2 = np.sin(2 * np.pi * 200 * t3) * 0.5
        
        audio_with_pause = np.concatenate([audio_part1, silence_part, audio_part2])
        
        # 检测停顿
        pause_durations = self.analyzer.detect_pause_patterns(audio_with_pause, sample_rate)
        
        # 应该检测到一个约2秒的停顿
        self.assertGreater(len(pause_durations), 0)
        self.assertGreater(pause_durations[0], 1.5)  # 停顿时长应该接近2秒
    
    def test_pause_characteristics_analysis(self):
        """测试停顿特征分析"""
        # 频繁短停顿
        frequent_short_pauses = [0.4, 0.5, 0.3, 0.6, 0.4]
        analysis1 = self.analyzer.analyze_pause_characteristics(frequent_short_pauses)
        self.assertEqual(analysis1["pause_pattern"], "frequent_short")
        
        # 不规则长停顿
        irregular_long_pauses = [1.2, 0.8, 2.1, 1.5]
        analysis2 = self.analyzer.analyze_pause_characteristics(irregular_long_pauses)
        self.assertEqual(analysis2["pause_pattern"], "irregular_long")
        
        # 无停顿
        no_pauses = []
        analysis3 = self.analyzer.analyze_pause_characteristics(no_pauses)
        self.assertEqual(analysis3["pause_pattern"], "no_pauses")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)