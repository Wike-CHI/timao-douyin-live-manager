#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自适应阈值控制器
为情感博主语音识别场景优化的动态阈值调整组件

主要功能:
1. 基于音频质量的阈值调整
2. 基于情感强度的阈值调整
3. 基于历史表现的阈值学习
4. 多维度阈值融合算法
5. 实时阈值优化策略
"""

import time
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque, defaultdict
import math
from enhanced_transcription_result import (
    AudioQuality,
    EmotionalFeatures,
    ConfidenceBreakdown,
    EmotionType
)

# 阈值控制常量
DEFAULT_CONFIDENCE_THRESHOLD = 0.6    # 默认置信度阈值
MIN_THRESHOLD = 0.3                   # 最小阈值
MAX_THRESHOLD = 0.9                   # 最大阈值
HISTORY_WINDOW_SIZE = 100             # 历史窗口大小
ADAPTATION_RATE = 0.1                 # 适应速率
PERFORMANCE_SMOOTHING = 0.8           # 性能平滑系数

@dataclass
class ThresholdConfig:
    """阈值配置"""
    base_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    audio_quality_weight: float = 0.3      # 音频质量权重
    emotion_intensity_weight: float = 0.2   # 情感强度权重
    historical_weight: float = 0.3          # 历史表现权重
    real_time_weight: float = 0.2          # 实时调整权重
    
    # 调整参数
    quality_sensitivity: float = 0.5       # 音质敏感度
    emotion_sensitivity: float = 0.4       # 情感敏感度
    adaptation_speed: float = 0.1          # 适应速度
    
    def __post_init__(self):
        """权重归一化"""
        total_weight = (self.audio_quality_weight + self.emotion_intensity_weight + 
                       self.historical_weight + self.real_time_weight)
        if total_weight != 1.0:
            factor = 1.0 / total_weight
            self.audio_quality_weight *= factor
            self.emotion_intensity_weight *= factor
            self.historical_weight *= factor
            self.real_time_weight *= factor

@dataclass
class ThresholdState:
    """阈值状态"""
    current_threshold: float
    audio_quality_factor: float
    emotion_intensity_factor: float
    historical_performance_factor: float
    real_time_adjustment: float
    last_update_time: float
    confidence_level: float              # 阈值置信度

@dataclass
class PerformanceMetrics:
    """性能指标"""
    accuracy: float                      # 准确率
    precision: float                    # 精确率
    recall: float                       # 召回率
    f1_score: float                     # F1分数
    false_positive_rate: float          # 误报率
    false_negative_rate: float          # 漏报率
    sample_count: int                   # 样本数量

class AudioQualityThresholdAdapter:
    """音频质量阈值适配器"""
    
    def __init__(self, sensitivity: float = 0.5):
        self.sensitivity = sensitivity
        self.logger = logging.getLogger(__name__)
        
        # 音频质量与阈值调整的映射关系
        self.quality_threshold_mapping = {
            # (noise_level, volume_level, clarity_score) -> threshold_adjustment
            "high_quality": {
                "conditions": {"noise_level": (0.0, 0.2), "volume_level": (0.6, 1.0), "clarity_score": (0.8, 1.0)},
                "adjustment": -0.1  # 高质量时降低阈值，更容易接受
            },
            "good_quality": {
                "conditions": {"noise_level": (0.0, 0.3), "volume_level": (0.5, 1.0), "clarity_score": (0.6, 1.0)},
                "adjustment": -0.05
            },
            "medium_quality": {
                "conditions": {"noise_level": (0.2, 0.5), "volume_level": (0.3, 0.8), "clarity_score": (0.4, 0.8)},
                "adjustment": 0.0   # 中等质量时保持默认阈值
            },
            "poor_quality": {
                "conditions": {"noise_level": (0.4, 0.8), "volume_level": (0.1, 0.6), "clarity_score": (0.2, 0.6)},
                "adjustment": 0.1   # 差质量时提高阈值，更严格
            },
            "very_poor_quality": {
                "conditions": {"noise_level": (0.6, 1.0), "volume_level": (0.0, 0.4), "clarity_score": (0.0, 0.4)},
                "adjustment": 0.2   # 很差质量时大幅提高阈值
            }
        }
    
    def calculate_quality_adjustment(self, audio_quality: AudioQuality) -> float:
        """计算基于音频质量的阈值调整
        
        Args:
            audio_quality: 音频质量数据
            
        Returns:
            阈值调整值 (-0.3 到 +0.3)
        """
        try:
            if not audio_quality:
                return 0.0
            
            # 匹配质量级别
            matched_adjustments = []
            
            for quality_level, mapping in self.quality_threshold_mapping.items():
                conditions = mapping["conditions"]
                adjustment = mapping["adjustment"]
                
                # 检查是否满足条件
                matches = 0
                total_conditions = len(conditions)
                
                for metric, (min_val, max_val) in conditions.items():
                    value = getattr(audio_quality, metric, 0.5)
                    if min_val <= value <= max_val:
                        matches += 1
                
                # 计算匹配度
                match_ratio = matches / total_conditions
                if match_ratio > 0.5:  # 超过一半条件匹配
                    weighted_adjustment = adjustment * match_ratio
                    matched_adjustments.append(weighted_adjustment)
            
            # 如果有多个匹配，取加权平均
            if matched_adjustments:
                final_adjustment = np.mean(matched_adjustments)
            else:
                # 基于整体质量评分的线性调整
                quality_score = self._calculate_overall_quality_score(audio_quality)
                final_adjustment = (0.7 - quality_score) * 0.3  # 质量越低，阈值调整越大
            
            # 应用敏感度因子
            final_adjustment *= self.sensitivity
            
            return max(-0.3, min(0.3, float(final_adjustment)))
            
        except Exception as e:
            self.logger.error(f"音频质量阈值调整计算失败: {e}")
            return 0.0
    
    def _calculate_overall_quality_score(self, audio_quality: AudioQuality) -> float:
        """计算整体质量评分"""
        # 加权计算整体质量
        noise_score = 1.0 - audio_quality.noise_level      # 噪音越低越好
        volume_score = min(audio_quality.volume_level * 2, 1.0)  # 音量适中最好
        clarity_score = audio_quality.clarity_score        # 清晰度越高越好
        
        overall_score = (noise_score * 0.4 + volume_score * 0.3 + clarity_score * 0.3)
        return max(0.0, min(1.0, overall_score))

class EmotionIntensityThresholdAdapter:
    """情感强度阈值适配器"""
    
    def __init__(self, sensitivity: float = 0.4):
        self.sensitivity = sensitivity
        self.logger = logging.getLogger(__name__)
        
        # 情感类型与阈值调整的映射
        self.emotion_threshold_mapping = {
            EmotionType.EXCITED: {
                "base_adjustment": -0.1,     # 兴奋时容忍度更高
                "intensity_factor": 1.2      # 强度影响因子
            },
            EmotionType.JOYFUL: {
                "base_adjustment": -0.05,    # 愉悦时略微降低阈值
                "intensity_factor": 1.0
            },
            EmotionType.CALM: {
                "base_adjustment": 0.05,     # 平静时稍微提高阈值
                "intensity_factor": 0.8
            },
            EmotionType.FRUSTRATED: {
                "base_adjustment": 0.1,      # 沮丧时提高阈值
                "intensity_factor": 1.1
            },
            EmotionType.ANXIOUS: {
                "base_adjustment": 0.08,     # 焦虑时提高阈值
                "intensity_factor": 1.3
            },
            EmotionType.NEUTRAL: {
                "base_adjustment": 0.0,      # 中性时保持默认
                "intensity_factor": 1.0
            }
        }
    
    def calculate_emotion_adjustment(self, emotional_features: EmotionalFeatures) -> float:
        """计算基于情感强度的阈值调整
        
        Args:
            emotional_features: 情感特征数据
            
        Returns:
            阈值调整值 (-0.2 到 +0.2)
        """
        try:
            if not emotional_features:
                return 0.0
            
            emotion_type = emotional_features.emotion_type
            intensity = emotional_features.intensity
            tone_confidence = emotional_features.tone_confidence
            
            # 获取情感类型的基础调整
            emotion_config = self.emotion_threshold_mapping.get(emotion_type, 
                                                              self.emotion_threshold_mapping[EmotionType.NEUTRAL])
            
            base_adjustment = emotion_config["base_adjustment"]
            intensity_factor = emotion_config["intensity_factor"]
            
            # 基于强度和置信度计算最终调整
            intensity_adjustment = (intensity - 0.5) * intensity_factor * 0.2  # 强度影响
            confidence_adjustment = (tone_confidence - 0.5) * 0.1  # 置信度影响
            
            final_adjustment = base_adjustment + intensity_adjustment + confidence_adjustment
            
            # 应用敏感度因子
            final_adjustment *= self.sensitivity
            
            return max(-0.2, min(0.2, final_adjustment))
            
        except Exception as e:
            self.logger.error(f"情感强度阈值调整计算失败: {e}")
            return 0.0

class HistoricalPerformanceAnalyzer:
    """历史表现分析器"""
    
    def __init__(self, window_size: int = HISTORY_WINDOW_SIZE):
        self.window_size = window_size
        self.performance_history = deque(maxlen=window_size)
        self.threshold_history = deque(maxlen=window_size)
        self.logger = logging.getLogger(__name__)
        
        # 性能目标
        self.target_metrics = {
            "accuracy": 0.8,        # 目标准确率80%
            "precision": 0.75,      # 目标精确率75%
            "recall": 0.8,          # 目标召回率80%
            "f1_score": 0.77        # 目标F1分数77%
        }
    
    def add_performance_sample(self, metrics: PerformanceMetrics, threshold_used: float):
        """添加性能样本
        
        Args:
            metrics: 性能指标
            threshold_used: 使用的阈值
        """
        self.performance_history.append(metrics)
        self.threshold_history.append(threshold_used)
    
    def calculate_historical_adjustment(self) -> float:
        """计算基于历史表现的阈值调整
        
        Returns:
            阈值调整值 (-0.2 到 +0.2)
        """
        try:
            if len(self.performance_history) < 10:  # 需要足够的历史数据
                return 0.0
            
            # 计算近期性能趋势
            recent_performance = self._calculate_recent_performance()
            performance_gap = self._calculate_performance_gap(recent_performance)
            
            # 分析阈值与性能的关系
            threshold_performance_correlation = self._analyze_threshold_performance_correlation()
            
            # 计算调整建议
            adjustment = self._calculate_adjustment_from_analysis(
                performance_gap, threshold_performance_correlation
            )
            
            return max(-0.2, min(0.2, adjustment))
            
        except Exception as e:
            self.logger.error(f"历史表现阈值调整计算失败: {e}")
            return 0.0
    
    def _calculate_recent_performance(self) -> PerformanceMetrics:
        """计算近期平均性能"""
        if not self.performance_history:
            return PerformanceMetrics(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0)
        
        recent_count = min(20, len(self.performance_history))  # 最近20个样本
        recent_samples = list(self.performance_history)[-recent_count:]
        
        avg_accuracy = np.mean([m.accuracy for m in recent_samples])
        avg_precision = np.mean([m.precision for m in recent_samples])
        avg_recall = np.mean([m.recall for m in recent_samples])
        avg_f1 = np.mean([m.f1_score for m in recent_samples])
        avg_fpr = np.mean([m.false_positive_rate for m in recent_samples])
        avg_fnr = np.mean([m.false_negative_rate for m in recent_samples])
        total_samples = sum([m.sample_count for m in recent_samples])
        
        return PerformanceMetrics(
            accuracy=float(avg_accuracy),
            precision=float(avg_precision),
            recall=float(avg_recall),
            f1_score=float(avg_f1),
            false_positive_rate=float(avg_fpr),
            false_negative_rate=float(avg_fnr),
            sample_count=total_samples
        )
    
    def _calculate_performance_gap(self, current_performance: PerformanceMetrics) -> Dict[str, float]:
        """计算性能差距"""
        gaps = {}
        gaps["accuracy_gap"] = self.target_metrics["accuracy"] - current_performance.accuracy
        gaps["precision_gap"] = self.target_metrics["precision"] - current_performance.precision
        gaps["recall_gap"] = self.target_metrics["recall"] - current_performance.recall
        gaps["f1_gap"] = self.target_metrics["f1_score"] - current_performance.f1_score
        return gaps
    
    def _analyze_threshold_performance_correlation(self) -> Dict[str, float]:
        """分析阈值与性能的相关性"""
        if len(self.performance_history) < 10:
            return {"accuracy_corr": 0.0, "precision_corr": 0.0, "recall_corr": 0.0}
        
        thresholds = list(self.threshold_history)
        accuracies = [m.accuracy for m in self.performance_history]
        precisions = [m.precision for m in self.performance_history]
        recalls = [m.recall for m in self.performance_history]
        
        # 计算相关系数
        accuracy_corr = np.corrcoef(thresholds, accuracies)[0, 1] if len(thresholds) > 1 else 0.0
        precision_corr = np.corrcoef(thresholds, precisions)[0, 1] if len(thresholds) > 1 else 0.0
        recall_corr = np.corrcoef(thresholds, recalls)[0, 1] if len(thresholds) > 1 else 0.0
        
        return {
            "accuracy_corr": accuracy_corr if not np.isnan(accuracy_corr) else 0.0,
            "precision_corr": precision_corr if not np.isnan(precision_corr) else 0.0,
            "recall_corr": recall_corr if not np.isnan(recall_corr) else 0.0
        }
    
    def _calculate_adjustment_from_analysis(self, performance_gap: Dict[str, float], 
                                          correlations: Dict[str, float]) -> float:
        """基于分析结果计算调整值"""
        # 权重配置
        gap_weights = {"accuracy_gap": 0.4, "precision_gap": 0.2, "recall_gap": 0.3, "f1_gap": 0.1}
        
        # 计算加权性能差距
        weighted_gap = sum(gap_weights[key] * gap for key, gap in performance_gap.items())
        
        # 基于相关性确定调整方向
        avg_correlation = np.mean(list(correlations.values()))
        
        if weighted_gap > 0:  # 性能不足
            if avg_correlation > 0:  # 阈值与性能正相关，降低阈值
                adjustment = -weighted_gap * 0.5
            else:  # 阈值与性能负相关，提高阈值
                adjustment = weighted_gap * 0.5
        else:  # 性能超预期
            adjustment = -weighted_gap * 0.2  # 小幅调整
        
        return adjustment

class AdaptiveThresholdController:
    """自适应阈值控制器
    
    整合音频质量、情感强度和历史表现的动态阈值调整
    """
    
    def __init__(self, config: Optional[ThresholdConfig] = None):
        self.config = config or ThresholdConfig()
        
        # 初始化各个适配器
        self.audio_adapter = AudioQualityThresholdAdapter(self.config.quality_sensitivity)
        self.emotion_adapter = EmotionIntensityThresholdAdapter(self.config.emotion_sensitivity)
        self.historical_analyzer = HistoricalPerformanceAnalyzer()
        
        # 当前状态
        self.current_state = ThresholdState(
            current_threshold=self.config.base_threshold,
            audio_quality_factor=0.0,
            emotion_intensity_factor=0.0,
            historical_performance_factor=0.0,
            real_time_adjustment=0.0,
            last_update_time=time.time(),
            confidence_level=0.8
        )
        
        # 统计数据
        self.adjustment_stats = {
            "total_adjustments": 0,
            "audio_quality_adjustments": 0,
            "emotion_adjustments": 0,
            "historical_adjustments": 0,
            "average_threshold": self.config.base_threshold,
            "threshold_variance": 0.0
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("自适应阈值控制器已初始化")
    
    def calculate_adaptive_threshold(self,
                                   audio_quality: Optional[AudioQuality] = None,
                                   emotional_features: Optional[EmotionalFeatures] = None,
                                   confidence_breakdown: Optional[ConfidenceBreakdown] = None) -> float:
        """计算自适应阈值
        
        Args:
            audio_quality: 音频质量数据
            emotional_features: 情感特征数据
            confidence_breakdown: 置信度分解数据
            
        Returns:
            调整后的阈值
        """
        try:
            # 1. 计算各维度调整
            audio_adjustment = 0.0
            if audio_quality:
                audio_adjustment = self.audio_adapter.calculate_quality_adjustment(audio_quality)
                self.current_state.audio_quality_factor = audio_adjustment
            
            emotion_adjustment = 0.0
            if emotional_features:
                emotion_adjustment = self.emotion_adapter.calculate_emotion_adjustment(emotional_features)
                self.current_state.emotion_intensity_factor = emotion_adjustment
            
            historical_adjustment = self.historical_analyzer.calculate_historical_adjustment()
            self.current_state.historical_performance_factor = historical_adjustment
            
            # 2. 实时微调（基于最近的置信度分解）
            real_time_adjustment = 0.0
            if confidence_breakdown:
                real_time_adjustment = self._calculate_real_time_adjustment(confidence_breakdown)
                self.current_state.real_time_adjustment = real_time_adjustment
            
            # 3. 加权融合
            total_adjustment = (
                audio_adjustment * self.config.audio_quality_weight +
                emotion_adjustment * self.config.emotion_intensity_weight +
                historical_adjustment * self.config.historical_weight +
                real_time_adjustment * self.config.real_time_weight
            )
            
            # 4. 应用适应速度限制
            max_adjustment = self.config.adaptation_speed
            total_adjustment = max(-max_adjustment, min(max_adjustment, total_adjustment))
            
            # 5. 计算最终阈值
            new_threshold = self.config.base_threshold + total_adjustment
            new_threshold = max(MIN_THRESHOLD, min(MAX_THRESHOLD, new_threshold))
            
            # 6. 更新状态
            old_threshold = self.current_state.current_threshold
            self.current_state.current_threshold = new_threshold
            self.current_state.last_update_time = time.time()
            
            # 7. 计算调整置信度
            self.current_state.confidence_level = self._calculate_adjustment_confidence(
                audio_quality, emotional_features, confidence_breakdown
            )
            
            # 8. 更新统计数据
            self._update_adjustment_stats(old_threshold, new_threshold, total_adjustment)
            
            return new_threshold
            
        except Exception as e:
            self.logger.error(f"自适应阈值计算失败: {e}")
            return self.config.base_threshold
    
    def _calculate_real_time_adjustment(self, confidence_breakdown: ConfidenceBreakdown) -> float:
        """计算实时微调"""
        try:
            # 基于各维度置信度的质量评估
            vosk_quality = confidence_breakdown.vosk_confidence
            word_freq_quality = confidence_breakdown.word_frequency_score
            context_quality = confidence_breakdown.context_coherence_score
            audio_quality = confidence_breakdown.audio_quality_score
            
            # 计算整体质量分数
            overall_quality = (vosk_quality * 0.4 + word_freq_quality * 0.25 + 
                             context_quality * 0.2 + audio_quality * 0.15)
            
            # 基于质量分数计算调整
            if overall_quality > 0.8:
                adjustment = -0.05  # 高质量时降低阈值
            elif overall_quality < 0.4:
                adjustment = 0.05   # 低质量时提高阈值
            else:
                adjustment = (0.6 - overall_quality) * 0.1  # 线性调整
            
            return max(-0.1, min(0.1, adjustment))
            
        except Exception as e:
            self.logger.error(f"实时调整计算失败: {e}")
            return 0.0
    
    def _calculate_adjustment_confidence(self, 
                                       audio_quality: Optional[AudioQuality],
                                       emotional_features: Optional[EmotionalFeatures],
                                       confidence_breakdown: Optional[ConfidenceBreakdown]) -> float:
        """计算调整置信度"""
        confidence_factors = []
        
        # 音频质量置信度
        if audio_quality:
            audio_conf = (audio_quality.clarity_score + (1 - audio_quality.noise_level)) / 2
            confidence_factors.append(audio_conf)
        
        # 情感特征置信度
        if emotional_features:
            emotion_conf = emotional_features.tone_confidence
            confidence_factors.append(emotion_conf)
        
        # 置信度分解质量
        if confidence_breakdown:
            breakdown_conf = confidence_breakdown.final_confidence
            confidence_factors.append(breakdown_conf)
        
        # 历史表现置信度
        if len(self.historical_analyzer.performance_history) > 5:
            recent_perf = self.historical_analyzer._calculate_recent_performance()
            hist_conf = (recent_perf.accuracy + recent_perf.f1_score) / 2
            confidence_factors.append(hist_conf)
        
        if confidence_factors:
            return float(np.mean(confidence_factors))
        else:
            return 0.5  # 默认中等置信度
    
    def _update_adjustment_stats(self, old_threshold: float, new_threshold: float, adjustment: float):
        """更新调整统计数据"""
        self.adjustment_stats["total_adjustments"] += 1
        
        # 统计调整类型
        if abs(self.current_state.audio_quality_factor) > 0.01:
            self.adjustment_stats["audio_quality_adjustments"] += 1
        if abs(self.current_state.emotion_intensity_factor) > 0.01:
            self.adjustment_stats["emotion_adjustments"] += 1
        if abs(self.current_state.historical_performance_factor) > 0.01:
            self.adjustment_stats["historical_adjustments"] += 1
        
        # 更新平均阈值
        count = self.adjustment_stats["total_adjustments"]
        prev_avg = self.adjustment_stats["average_threshold"]
        self.adjustment_stats["average_threshold"] = (
            (prev_avg * (count - 1) + new_threshold) / count
        )
        
        # 计算阈值方差
        if count > 1:
            threshold_diff = new_threshold - self.adjustment_stats["average_threshold"]
            prev_var = self.adjustment_stats["threshold_variance"]
            self.adjustment_stats["threshold_variance"] = (
                (prev_var * (count - 2) + threshold_diff ** 2) / (count - 1)
            )
    
    def add_performance_feedback(self, metrics: PerformanceMetrics):
        """添加性能反馈
        
        Args:
            metrics: 性能指标
        """
        self.historical_analyzer.add_performance_sample(
            metrics, self.current_state.current_threshold
        )
    
    def get_threshold_state(self) -> ThresholdState:
        """获取当前阈值状态"""
        return self.current_state
    
    def get_adjustment_stats(self) -> Dict[str, Any]:
        """获取调整统计信息"""
        stats = self.adjustment_stats.copy()
        
        # 添加额外指标
        if stats["total_adjustments"] > 0:
            stats["audio_adjustment_ratio"] = stats["audio_quality_adjustments"] / stats["total_adjustments"]
            stats["emotion_adjustment_ratio"] = stats["emotion_adjustments"] / stats["total_adjustments"]
            stats["historical_adjustment_ratio"] = stats["historical_adjustments"] / stats["total_adjustments"]
        else:
            stats["audio_adjustment_ratio"] = 0.0
            stats["emotion_adjustment_ratio"] = 0.0
            stats["historical_adjustment_ratio"] = 0.0
        
        stats["current_threshold"] = self.current_state.current_threshold
        stats["threshold_confidence"] = self.current_state.confidence_level
        
        return stats
    
    def reset_controller(self):
        """重置控制器状态"""
        self.current_state = ThresholdState(
            current_threshold=self.config.base_threshold,
            audio_quality_factor=0.0,
            emotion_intensity_factor=0.0,
            historical_performance_factor=0.0,
            real_time_adjustment=0.0,
            last_update_time=time.time(),
            confidence_level=0.8
        )
        
        self.adjustment_stats = {
            "total_adjustments": 0,
            "audio_quality_adjustments": 0,
            "emotion_adjustments": 0,
            "historical_adjustments": 0,
            "average_threshold": self.config.base_threshold,
            "threshold_variance": 0.0
        }
        
        self.historical_analyzer.performance_history.clear()
        self.historical_analyzer.threshold_history.clear()
        
        self.logger.info("自适应阈值控制器已重置")

# 导出主要类
__all__ = [
    'AdaptiveThresholdController',
    'ThresholdConfig',
    'ThresholdState',
    'PerformanceMetrics',
    'AudioQualityThresholdAdapter',
    'EmotionIntensityThresholdAdapter',
    'HistoricalPerformanceAnalyzer'
]