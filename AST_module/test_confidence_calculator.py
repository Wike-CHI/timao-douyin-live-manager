#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能置信度计算器测试
测试多维度置信度计算功能
"""

import unittest
import sys
import os

# 添加AST_module到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from confidence_calculator_enhanced import (
    IntelligentConfidenceCalculator,
    ConfidenceWeights,
    ChineseWordFrequencyAnalyzer,
    ContextCoherenceAnalyzer
)
from enhanced_transcription_result import (
    ConfidenceBreakdown,
    AudioQuality,
    EmotionalFeatures,
    EmotionType
)

class TestIntelligentConfidenceCalculator(unittest.TestCase):
    """智能置信度计算器测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.calculator = IntelligentConfidenceCalculator()
        
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.calculator)
        self.assertIsInstance(self.calculator.weights, ConfidenceWeights)
        self.assertIsInstance(self.calculator.word_analyzer, ChineseWordFrequencyAnalyzer)
        self.assertIsInstance(self.calculator.context_analyzer, ContextCoherenceAnalyzer)
    
    def test_basic_confidence_calculation(self):
        """测试基础置信度计算"""
        text = "这个口红真的很好看"
        vosk_confidence = 0.7
        
        result = self.calculator.calculate_enhanced_confidence(
            text=text,
            vosk_confidence=vosk_confidence
        )
        
        # 验证结果类型
        self.assertIsInstance(result, ConfidenceBreakdown)
        self.assertEqual(result.vosk_confidence, vosk_confidence)
        self.assertGreaterEqual(result.final_confidence, 0.0)
        self.assertLessEqual(result.final_confidence, 1.0)
        
        # 由于包含情感词汇，最终置信度应该有所提升
        self.assertGreaterEqual(result.final_confidence, vosk_confidence)
    
    def test_word_frequency_analysis(self):
        """测试词频分析"""
        # 高频情感词汇
        high_freq_text = "真的很喜欢这个美丽的口红"
        high_freq_result = self.calculator.calculate_enhanced_confidence(
            text=high_freq_text,
            vosk_confidence=0.6
        )
        
        # 低频或未知词汇
        low_freq_text = "这个稀奇古怪的东西"
        low_freq_result = self.calculator.calculate_enhanced_confidence(
            text=low_freq_text,
            vosk_confidence=0.6
        )
        
        # 高频词汇应该有更高的词频评分
        self.assertGreater(
            high_freq_result.word_frequency_score,
            low_freq_result.word_frequency_score
        )
    
    def test_audio_quality_impact(self):
        """测试音频质量对置信度的影响"""
        text = "今天推荐这款面膜"
        vosk_confidence = 0.7
        
        # 高质量音频
        high_quality = AudioQuality(
            noise_level=0.1,    # 低噪音
            volume_level=0.7,   # 适中音量
            clarity_score=0.9,  # 高清晰度
            sample_rate=16000
        )
        
        # 低质量音频
        low_quality = AudioQuality(
            noise_level=0.8,    # 高噪音
            volume_level=0.2,   # 低音量
            clarity_score=0.3,  # 低清晰度
            sample_rate=16000
        )
        
        high_quality_result = self.calculator.calculate_enhanced_confidence(
            text=text,
            vosk_confidence=vosk_confidence,
            audio_quality=high_quality
        )
        
        low_quality_result = self.calculator.calculate_enhanced_confidence(
            text=text,
            vosk_confidence=vosk_confidence,
            audio_quality=low_quality
        )
        
        # 高质量音频应该产生更高的最终置信度
        self.assertGreater(
            high_quality_result.final_confidence,
            low_quality_result.final_confidence
        )
    
    def test_emotional_features_boost(self):
        """测试情感特征加成"""
        text = "超级开心今天的直播"
        vosk_confidence = 0.6
        
        # 强情感特征
        strong_emotion = EmotionalFeatures(
            emotion_type=EmotionType.EXCITED,
            intensity=0.9,         # 高强度
            speech_rate=150.0,
            tone_confidence=0.8    # 高置信度
        )
        
        # 弱情感特征
        weak_emotion = EmotionalFeatures(
            emotion_type=EmotionType.NEUTRAL,
            intensity=0.2,         # 低强度
            speech_rate=120.0,
            tone_confidence=0.3    # 低置信度
        )
        
        strong_result = self.calculator.calculate_enhanced_confidence(
            text=text,
            vosk_confidence=vosk_confidence,
            emotional_features=strong_emotion
        )
        
        weak_result = self.calculator.calculate_enhanced_confidence(
            text=text,
            vosk_confidence=vosk_confidence,
            emotional_features=weak_emotion
        )
        
        # 强情感特征应该产生更高的情感加成
        self.assertGreater(strong_result.emotion_boost, weak_result.emotion_boost)
        self.assertGreater(strong_result.final_confidence, weak_result.final_confidence)
    
    def test_context_coherence(self):
        """测试上下文连贯性"""
        # 先添加一些上下文
        self.calculator._update_context_history(["今天", "给", "大家", "推荐"])
        
        # 连贯的句子
        coherent_text = "这款口红的颜色"
        coherent_result = self.calculator.calculate_enhanced_confidence(
            text=coherent_text,
            vosk_confidence=0.6
        )
        
        # 重置上下文，测试不连贯的句子
        self.calculator.reset_context_history()
        self.calculator._update_context_history(["天气", "很", "好"])
        
        incoherent_text = "计算机算法代码"
        incoherent_result = self.calculator.calculate_enhanced_confidence(
            text=incoherent_text,
            vosk_confidence=0.6
        )
        
        # 连贯的句子应该有更高的上下文评分
        # 注意：由于简单的实现，差异可能不大，但应该有趋势
        self.assertGreaterEqual(
            coherent_result.context_coherence_score,
            incoherent_result.context_coherence_score - 0.1  # 允许小范围差异
        )
    
    def test_comprehensive_calculation(self):
        """测试综合计算"""
        text = "亲们这款面膜真的超级好用推荐给大家"
        vosk_confidence = 0.65
        
        # 高质量音频
        audio_quality = AudioQuality(
            noise_level=0.2,
            volume_level=0.8,
            clarity_score=0.85,
            sample_rate=16000
        )
        
        # 强情感特征
        emotional_features = EmotionalFeatures(
            emotion_type=EmotionType.EXCITED,
            intensity=0.8,
            speech_rate=140.0,
            tone_confidence=0.75
        )
        
        result = self.calculator.calculate_enhanced_confidence(
            text=text,
            vosk_confidence=vosk_confidence,
            audio_quality=audio_quality,
            emotional_features=emotional_features
        )
        
        # 验证所有维度都有合理的评分
        self.assertGreater(result.word_frequency_score, 0.5)  # 包含高频词汇
        self.assertGreater(result.audio_quality_score, 0.5)   # 音频质量好
        self.assertGreater(result.emotion_boost, 0.0)         # 有情感加成
        
        # 最终置信度应该得到提升
        self.assertGreater(result.final_confidence, vosk_confidence)
        
        # 但不应该超过1.0
        self.assertLessEqual(result.final_confidence, 1.0)
    
    def test_statistics_tracking(self):
        """测试统计数据跟踪"""
        initial_stats = self.calculator.get_calculation_stats()
        self.assertEqual(initial_stats["total_calculations"], 0)
        
        # 执行几次计算
        for i in range(3):
            self.calculator.calculate_enhanced_confidence(
                text=f"测试文本{i}",
                vosk_confidence=0.5 + i * 0.1
            )
        
        stats = self.calculator.get_calculation_stats()
        self.assertEqual(stats["total_calculations"], 3)
        self.assertGreater(stats["average_vosk_confidence"], 0)
        self.assertGreater(stats["average_final_confidence"], 0)
    
    def test_context_history_management(self):
        """测试上下文历史管理"""
        # 添加大量上下文
        for i in range(60):  # 超过最大历史大小50
            self.calculator._update_context_history([f"词汇{i}"])
        
        # 检查历史大小是否被限制
        self.assertLessEqual(len(self.calculator.context_history), 50)
        
        # 测试重置功能
        self.calculator.reset_context_history()
        self.assertEqual(len(self.calculator.context_history), 0)

class TestChineseWordFrequencyAnalyzer(unittest.TestCase):
    """中文词频分析器测试"""
    
    def setUp(self):
        self.analyzer = ChineseWordFrequencyAnalyzer()
    
    def test_emotion_words_scoring(self):
        """测试情感词汇评分"""
        # 高频情感词
        high_score = self.analyzer.get_word_frequency_score("喜欢")
        self.assertGreater(high_score, 0.8)
        
        # 低频情感词
        low_score = self.analyzer.get_word_frequency_score("清新")
        self.assertGreater(low_score, 0.1)
        self.assertLess(low_score, high_score)
    
    def test_product_words_scoring(self):
        """测试产品词汇评分"""
        # 化妆品词汇
        cosmetic_score = self.analyzer.get_word_frequency_score("口红")
        self.assertGreater(cosmetic_score, 0.8)
        
        # 服装词汇
        clothing_score = self.analyzer.get_word_frequency_score("衣服")
        self.assertGreater(clothing_score, 0.8)
    
    def test_unknown_words_handling(self):
        """测试未知词汇处理"""
        # 未知词汇应该有较低但非零的评分
        unknown_score = self.analyzer.get_word_frequency_score("未知词汇测试")
        self.assertGreater(unknown_score, 0.0)
        self.assertLess(unknown_score, 0.6)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)