# -*- coding: utf-8 -*-
"""
增强版语音转录结果数据结构
为情感博主语音识别优化而设计的扩展数据模型
"""

import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

class EmotionType(Enum):
    """情感类型枚举"""
    EXCITED = "excited"        # 兴奋
    CALM = "calm"             # 平静
    FRUSTRATED = "frustrated"  # 沮丧
    JOYFUL = "joyful"         # 愉悦
    ANXIOUS = "anxious"       # 焦虑
    NEUTRAL = "neutral"       # 中性
    UNKNOWN = "unknown"       # 未知

class ProcessingType(Enum):
    """后处理类型枚举"""
    EMOTION_CORRECTION = "emotion_correction"      # 情感表达纠错
    PRODUCT_STANDARDIZATION = "product_std"        # 产品名称标准化
    SLANG_NORMALIZATION = "slang_norm"            # 网络用语规范化
    CONFIDENCE_BOOST = "confidence_boost"          # 置信度提升
    NOISE_FILTERING = "noise_filtering"           # 噪音过滤

@dataclass
class AudioQuality:
    """音频质量评估数据"""
    noise_level: float              # 噪音水平 (0.0-1.0)
    volume_level: float             # 音量水平 (0.0-1.0)  
    clarity_score: float            # 清晰度评分 (0.0-1.0)
    sample_rate: int               # 采样率 (Hz)
    snr_db: Optional[float] = None # 信噪比 (dB)
    
    def __post_init__(self):
        """数据验证"""
        self.noise_level = max(0.0, min(1.0, self.noise_level))
        self.volume_level = max(0.0, min(1.0, self.volume_level))
        self.clarity_score = max(0.0, min(1.0, self.clarity_score))

@dataclass
class EmotionalFeatures:
    """情感特征数据"""
    emotion_type: EmotionType       # 情感类型
    intensity: float               # 情感强度 (0.0-1.0)
    speech_rate: float             # 语速 (words per minute)
    tone_confidence: float         # 语调识别置信度 (0.0-1.0)
    pause_pattern: Optional[List[float]] = None  # 停顿模式 (秒)
    voice_stress: Optional[float] = None         # 语音压力指标 (0.0-1.0)
    
    def __post_init__(self):
        """数据验证"""
        self.intensity = max(0.0, min(1.0, self.intensity))
        self.tone_confidence = max(0.0, min(1.0, self.tone_confidence))
        if self.voice_stress is not None:
            self.voice_stress = max(0.0, min(1.0, self.voice_stress))

@dataclass
class ConfidenceBreakdown:
    """置信度分解数据"""
    vosk_confidence: float          # VOSK原始置信度
    word_frequency_score: float     # 词频权重评分
    context_coherence_score: float  # 上下文连贯性评分
    audio_quality_score: float      # 音频质量评分
    emotion_boost: float           # 情感特征加成
    final_confidence: float        # 最终置信度
    
    def __post_init__(self):
        """数据验证和归一化"""
        self.vosk_confidence = max(0.0, min(1.0, self.vosk_confidence))
        self.word_frequency_score = max(0.0, min(1.0, self.word_frequency_score))
        self.context_coherence_score = max(0.0, min(1.0, self.context_coherence_score))
        self.audio_quality_score = max(0.0, min(1.0, self.audio_quality_score))
        self.emotion_boost = max(0.0, min(0.15, self.emotion_boost))  # 最大15%加成
        self.final_confidence = max(0.0, min(1.0, self.final_confidence))

@dataclass
class WordAnalysis:
    """单词级分析数据"""
    word: str                      # 单词文本
    confidence: float              # 单词置信度
    start_time: float             # 开始时间 (秒)
    end_time: float               # 结束时间 (秒)
    is_emotional_keyword: bool = False      # 是否为情感关键词
    is_product_mention: bool = False        # 是否为产品提及
    is_slang: bool = False                 # 是否为网络用语
    correction_applied: Optional[str] = None # 应用的纠错 (原词->纠正词)

@dataclass
class EnhancedTranscriptionResult:
    """增强版语音转录结果
    
    完全兼容原有TranscriptionResult接口，同时提供情感博主场景的增强功能
    """
    # 基础字段 (与原TranscriptionResult完全兼容)
    text: str                      # 转录文本
    confidence: float              # 最终置信度 (0.0-1.0)
    timestamp: float               # 时间戳
    duration: float                # 音频时长 (秒)
    is_final: bool                # 是否为最终结果
    words: Optional[List[Dict[str, Any]]] = None    # 词级别信息 (兼容格式)
    room_id: str = ""             # 房间ID
    session_id: str = ""          # 会话ID
    
    # 增强字段 (新增功能)
    audio_quality: Optional[AudioQuality] = None           # 音频质量评估
    emotional_features: Optional[EmotionalFeatures] = None  # 情感特征分析
    confidence_breakdown: Optional[ConfidenceBreakdown] = None  # 置信度分解
    post_processing_applied: List[ProcessingType] = field(default_factory=list)  # 应用的后处理
    adaptive_threshold_used: Optional[float] = None        # 使用的自适应阈值
    enhanced_words: Optional[List[WordAnalysis]] = None    # 增强的词级分析
    original_text: Optional[str] = None                    # 原始识别文本 (纠错前)
    processing_time_ms: Optional[float] = None             # 处理耗时 (毫秒)
    
    def __post_init__(self):
        """后初始化处理"""
        # 验证基础字段
        self.confidence = max(0.0, min(1.0, self.confidence))
        if self.words is None:
            self.words = []
        
        # 设置默认时间戳
        if self.timestamp <= 0:
            self.timestamp = time.time()
    
    def to_legacy_format(self) -> Dict[str, Any]:
        """转换为原始TranscriptionResult格式，确保向后兼容"""
        return {
            "text": self.text,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "duration": self.duration,
            "is_final": self.is_final,
            "words": self.words,
            "room_id": self.room_id,
            "session_id": self.session_id
        }
    
    def get_emotion_summary(self) -> str:
        """获取情感分析摘要"""
        if not self.emotional_features:
            return "未分析"
        
        emotion_name = self.emotional_features.emotion_type.value
        intensity = self.emotional_features.intensity
        return f"{emotion_name}({intensity:.1f})"
    
    def get_confidence_summary(self) -> str:
        """获取置信度分析摘要"""
        if not self.confidence_breakdown:
            return f"总体:{self.confidence:.2f}"
        
        breakdown = self.confidence_breakdown
        return (f"总体:{breakdown.final_confidence:.2f} "
               f"(VOSK:{breakdown.vosk_confidence:.2f} "
               f"词频:{breakdown.word_frequency_score:.2f} "
               f"情感加成:{breakdown.emotion_boost:.2f})")
    
    def get_processing_summary(self) -> str:
        """获取处理过程摘要"""
        if not self.post_processing_applied:
            return "无后处理"
        
        process_names = [p.value for p in self.post_processing_applied]
        return f"处理: {', '.join(process_names)}"
    
    def has_enhancement(self) -> bool:
        """检查是否应用了增强功能"""
        return bool(
            self.audio_quality or 
            self.emotional_features or 
            self.confidence_breakdown or 
            self.post_processing_applied or
            self.enhanced_words
        )

# 类型别名，确保兼容性
TranscriptionResult = EnhancedTranscriptionResult

def create_basic_result(text: str, confidence: float, timestamp: Optional[float] = None, 
                       duration: float = 1.0, is_final: bool = True,
                       room_id: str = "", session_id: str = "") -> EnhancedTranscriptionResult:
    """创建基础转录结果的便捷函数"""
    return EnhancedTranscriptionResult(
        text=text,
        confidence=confidence,
        timestamp=timestamp or time.time(),
        duration=duration,
        is_final=is_final,
        room_id=room_id,
        session_id=session_id
    )

def create_enhanced_result(text: str, confidence: float, 
                          audio_quality: Optional[AudioQuality] = None,
                          emotional_features: Optional[EmotionalFeatures] = None,
                          confidence_breakdown: Optional[ConfidenceBreakdown] = None,
                          **kwargs) -> EnhancedTranscriptionResult:
    """创建增强转录结果的便捷函数"""
    result = create_basic_result(text, confidence, **kwargs)
    result.audio_quality = audio_quality
    result.emotional_features = emotional_features
    result.confidence_breakdown = confidence_breakdown
    return result

# 导出所有公共类和函数
__all__ = [
    'EnhancedTranscriptionResult',
    'TranscriptionResult',  # 兼容性别名
    'AudioQuality',
    'EmotionalFeatures',
    'ConfidenceBreakdown',
    'WordAnalysis',
    'EmotionType',
    'ProcessingType',
    'create_basic_result',
    'create_enhanced_result'
]