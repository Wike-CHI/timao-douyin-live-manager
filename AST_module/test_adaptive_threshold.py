#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自适应阈值控制器测试
测试动态阈值调整功能
"""

import unittest
import sys
import os

# 添加AST_module到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adaptive_threshold_controller import (
    AdaptiveThresholdController,
    ThresholdConfig,
    PerformanceMetrics,
    AudioQualityThresholdAdapter,
    EmotionIntensityThresholdAdapter,
    HistoricalPerformanceAnalyzer
)
from enhanced_transcription_result import (
    AudioQuality,
    EmotionalFeatures,
    ConfidenceBreakdown,
    EmotionType
)

class TestAdaptiveThresholdController(unittest.TestCase):
    """自适应阈值控制器测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.config = ThresholdConfig(
            base_threshold=0.6,
            audio_quality_weight=0.3,
            emotion_intensity_weight=0.2,
            historical_weight=0.3,
            real_time_weight=0.2
        )
        self.controller = AdaptiveThresholdController(self.config)
        
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.controller)
        self.assertEqual(self.controller.current_state.current_threshold, 0.6)
        self.assertIsInstance(self.controller.audio_adapter, AudioQualityThresholdAdapter)
        self.assertIsInstance(self.controller.emotion_adapter, EmotionIntensityThresholdAdapter)
        self.assertIsInstance(self.controller.historical_analyzer, HistoricalPerformanceAnalyzer)
    
    def test_audio_quality_adjustment(self):
        """测试音频质量调整"""
        # 高质量音频
        high_quality = AudioQuality(
            noise_level=0.1,    # 低噪音
            volume_level=0.8,   # 适中音量
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
        
        high_quality_threshold = self.controller.calculate_adaptive_threshold(
            audio_quality=high_quality
        )
        
        low_quality_threshold = self.controller.calculate_adaptive_threshold(
            audio_quality=low_quality
        )
        
        # 高质量音频的阈值应该更低（更容易接受）
        self.assertLess(high_quality_threshold, low_quality_threshold)
        
        # 阈值应该在合理范围内
        self.assertGreaterEqual(high_quality_threshold, 0.3)
        self.assertLessEqual(high_quality_threshold, 0.9)
        self.assertGreaterEqual(low_quality_threshold, 0.3)
        self.assertLessEqual(low_quality_threshold, 0.9)
    
    def test_emotion_intensity_adjustment(self):
        """测试情感强度调整"""
        # 强兴奋情感
        excited_emotion = EmotionalFeatures(
            emotion_type=EmotionType.EXCITED,
            intensity=0.9,
            speech_rate=200.0,
            tone_confidence=0.8
        )
        
        # 平静情感
        calm_emotion = EmotionalFeatures(
            emotion_type=EmotionType.CALM,
            intensity=0.3,
            speech_rate=120.0,
            tone_confidence=0.7
        )
        
        excited_threshold = self.controller.calculate_adaptive_threshold(
            emotional_features=excited_emotion
        )
        
        calm_threshold = self.controller.calculate_adaptive_threshold(
            emotional_features=calm_emotion
        )
        
        # 兴奋情感的阈值应该更低（更容易接受）
        self.assertLess(excited_threshold, calm_threshold)
    
    def test_confidence_breakdown_adjustment(self):
        """测试置信度分解调整"""
        # 高质量置信度分解
        high_confidence = ConfidenceBreakdown(
            vosk_confidence=0.8,
            word_frequency_score=0.9,
            context_coherence_score=0.8,
            audio_quality_score=0.9,
            emotion_boost=0.1,
            final_confidence=0.85
        )
        
        # 低质量置信度分解
        low_confidence = ConfidenceBreakdown(
            vosk_confidence=0.4,
            word_frequency_score=0.3,
            context_coherence_score=0.4,
            audio_quality_score=0.3,
            emotion_boost=0.0,
            final_confidence=0.35
        )
        
        high_conf_threshold = self.controller.calculate_adaptive_threshold(
            confidence_breakdown=high_confidence
        )
        
        low_conf_threshold = self.controller.calculate_adaptive_threshold(
            confidence_breakdown=low_confidence
        )
        
        # 高置信度时阈值应该更低
        self.assertLess(high_conf_threshold, low_conf_threshold)
    
    def test_comprehensive_adjustment(self):
        """测试综合调整"""
        # 优质场景：高质量音频 + 兴奋情感 + 高置信度
        audio_quality = AudioQuality(
            noise_level=0.1,
            volume_level=0.8,
            clarity_score=0.9,
            sample_rate=16000
        )
        
        emotional_features = EmotionalFeatures(
            emotion_type=EmotionType.EXCITED,
            intensity=0.8,
            speech_rate=180.0,
            tone_confidence=0.8
        )
        
        confidence_breakdown = ConfidenceBreakdown(
            vosk_confidence=0.8,
            word_frequency_score=0.9,
            context_coherence_score=0.8,
            audio_quality_score=0.9,
            emotion_boost=0.1,
            final_confidence=0.85
        )
        
        optimal_threshold = self.controller.calculate_adaptive_threshold(
            audio_quality=audio_quality,
            emotional_features=emotional_features,
            confidence_breakdown=confidence_breakdown
        )
        
        # 优质场景下阈值应该明显低于基础阈值
        self.assertLess(optimal_threshold, self.config.base_threshold)
        
        # 验证状态更新
        state = self.controller.get_threshold_state()
        self.assertEqual(state.current_threshold, optimal_threshold)
        self.assertGreater(state.confidence_level, 0.5)
    
    def test_historical_performance_learning(self):
        """测试历史表现学习"""
        # 添加一些历史性能数据
        for i in range(15):
            # 模拟逐渐改善的性能
            accuracy = 0.6 + i * 0.02  # 从60%改善到88%
            precision = 0.55 + i * 0.02
            recall = 0.65 + i * 0.02
            f1 = (precision + recall) / 2
            
            metrics = PerformanceMetrics(
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                false_positive_rate=0.1,
                false_negative_rate=0.1,
                sample_count=100
            )
            
            self.controller.add_performance_feedback(metrics)
        
        # 计算带历史学习的阈值
        learned_threshold = self.controller.calculate_adaptive_threshold()
        
        # 由于性能在改善，阈值应该有所调整
        self.assertNotEqual(learned_threshold, self.config.base_threshold)
        
        # 验证历史分析器有数据
        self.assertGreater(len(self.controller.historical_analyzer.performance_history), 10)
    
    def test_threshold_bounds(self):
        """测试阈值边界限制"""
        # 极端情况：所有因素都建议大幅降低阈值
        extreme_low_audio = AudioQuality(
            noise_level=0.0,    # 无噪音
            volume_level=1.0,   # 完美音量
            clarity_score=1.0,  # 完美清晰度
            sample_rate=16000
        )
        
        extreme_threshold = self.controller.calculate_adaptive_threshold(
            audio_quality=extreme_low_audio
        )
        
        # 即使在极端情况下，阈值也不应该超出边界
        self.assertGreaterEqual(extreme_threshold, 0.3)  # 最小阈值
        self.assertLessEqual(extreme_threshold, 0.9)     # 最大阈值
    
    def test_statistics_tracking(self):
        """测试统计数据跟踪"""
        initial_stats = self.controller.get_adjustment_stats()
        self.assertEqual(initial_stats["total_adjustments"], 0)
        
        # 执行几次调整
        for i in range(5):
            audio_quality = AudioQuality(
                noise_level=0.2 + i * 0.1,
                volume_level=0.7 - i * 0.1,
                clarity_score=0.8 - i * 0.1,
                sample_rate=16000
            )
            
            self.controller.calculate_adaptive_threshold(audio_quality=audio_quality)
        
        final_stats = self.controller.get_adjustment_stats()
        self.assertEqual(final_stats["total_adjustments"], 5)
        self.assertGreater(final_stats["audio_adjustment_ratio"], 0)

class TestAudioQualityThresholdAdapter(unittest.TestCase):
    """音频质量阈值适配器测试"""
    
    def setUp(self):
        self.adapter = AudioQualityThresholdAdapter(sensitivity=0.5)
    
    def test_high_quality_adjustment(self):
        """测试高质量音频调整"""
        high_quality = AudioQuality(
            noise_level=0.1,
            volume_level=0.8,
            clarity_score=0.9,
            sample_rate=16000
        )
        
        adjustment = self.adapter.calculate_quality_adjustment(high_quality)
        
        # 高质量应该降低阈值
        self.assertLess(adjustment, 0)
        self.assertGreaterEqual(adjustment, -0.3)
    
    def test_poor_quality_adjustment(self):
        """测试低质量音频调整"""
        poor_quality = AudioQuality(
            noise_level=0.8,
            volume_level=0.2,
            clarity_score=0.3,
            sample_rate=16000
        )
        
        adjustment = self.adapter.calculate_quality_adjustment(poor_quality)
        
        # 低质量应该提高阈值
        self.assertGreater(adjustment, 0)
        self.assertLessEqual(adjustment, 0.3)

class TestEmotionIntensityThresholdAdapter(unittest.TestCase):
    """情感强度阈值适配器测试"""
    
    def setUp(self):
        self.adapter = EmotionIntensityThresholdAdapter(sensitivity=0.4)
    
    def test_excited_emotion_adjustment(self):
        """测试兴奋情感调整"""
        excited_features = EmotionalFeatures(
            emotion_type=EmotionType.EXCITED,
            intensity=0.9,
            speech_rate=200.0,
            tone_confidence=0.8
        )
        
        adjustment = self.adapter.calculate_emotion_adjustment(excited_features)
        
        # 兴奋情感应该降低阈值
        self.assertLess(adjustment, 0)
    
    def test_calm_emotion_adjustment(self):
        """测试平静情感调整"""
        calm_features = EmotionalFeatures(
            emotion_type=EmotionType.CALM,
            intensity=0.3,
            speech_rate=120.0,
            tone_confidence=0.6
        )
        
        adjustment = self.adapter.calculate_emotion_adjustment(calm_features)
        
        # 平静情感应该提高阈值
        self.assertGreater(adjustment, 0)

class TestHistoricalPerformanceAnalyzer(unittest.TestCase):
    """历史表现分析器测试"""
    
    def setUp(self):
        self.analyzer = HistoricalPerformanceAnalyzer(window_size=50)
    
    def test_performance_sample_addition(self):
        """测试性能样本添加"""
        metrics = PerformanceMetrics(
            accuracy=0.8,
            precision=0.75,
            recall=0.8,
            f1_score=0.77,
            false_positive_rate=0.1,
            false_negative_rate=0.1,
            sample_count=100
        )
        
        self.analyzer.add_performance_sample(metrics, 0.6)
        
        self.assertEqual(len(self.analyzer.performance_history), 1)
        self.assertEqual(len(self.analyzer.threshold_history), 1)
    
    def test_historical_adjustment_with_insufficient_data(self):
        """测试数据不足时的历史调整"""
        # 只添加少量数据
        for i in range(5):
            metrics = PerformanceMetrics(0.7, 0.7, 0.7, 0.7, 0.1, 0.1, 100)
            self.analyzer.add_performance_sample(metrics, 0.6)
        
        adjustment = self.analyzer.calculate_historical_adjustment()
        
        # 数据不足时应该返回0
        self.assertEqual(adjustment, 0.0)
    
    def test_historical_adjustment_with_sufficient_data(self):
        """测试数据充足时的历史调整"""
        # 添加足够的数据
        for i in range(15):
            # 模拟性能低于目标的情况
            metrics = PerformanceMetrics(0.6, 0.6, 0.6, 0.6, 0.2, 0.2, 100)
            self.analyzer.add_performance_sample(metrics, 0.6)
        
        adjustment = self.analyzer.calculate_historical_adjustment()
        
        # 应该有调整建议
        self.assertNotEqual(adjustment, 0.0)
        self.assertGreaterEqual(adjustment, -0.2)
        self.assertLessEqual(adjustment, 0.2)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)