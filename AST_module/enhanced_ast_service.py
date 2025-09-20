#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版AST语音转录服务
整合所有增强组件的统一语音识别服务

主要功能:
1. 完全向后兼容的API接口
2. 集成音频预处理、智能置信度计算、情感分析、文本后处理
3. 自适应阈值控制和性能优化
4. 针对情感博主场景的专门优化
5. 实时性能监控和统计
"""

import time
import json
import logging
import asyncio
from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import asdict
import numpy as np

# 导入所有增强组件
from enhanced_transcription_result import (
    EnhancedTranscriptionResult,
    AudioQuality,
    EmotionalFeatures,
    ConfidenceBreakdown,
    ProcessingType,
    EmotionType,
    create_enhanced_result
)
from audio_preprocessor_enhanced import (
    AudioPreprocessorEnhanced,
    AudioProcessingConfig
)
from confidence_calculator_enhanced import (
    IntelligentConfidenceCalculator,
    ConfidenceWeights
)
from emotional_analyzer_enhanced import (
    EmotionalAnalyzerEnhanced
)
from text_postprocessor_enhanced import (
    LiveStreamTextPostProcessor,
    PostProcessingResult
)
from adaptive_threshold_controller import (
    AdaptiveThresholdController,
    ThresholdConfig,
    PerformanceMetrics
)

# 服务常量
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHUNK_SIZE = 1024
MIN_AUDIO_LENGTH = 0.1  # 最小音频长度（秒）
MAX_PROCESSING_TIME = 5.0  # 最大处理时间（秒）

class EnhancedASTServiceConfig:
    """增强版AST服务配置"""
    
    def __init__(self):
        # 音频预处理配置
        self.audio_config = AudioProcessingConfig(
            sample_rate=DEFAULT_SAMPLE_RATE,
            frame_size=1024,
            noise_reduction_strength=0.8,
            silence_threshold=0.01,
            volume_target=0.7
        )
        
        # 置信度计算配置
        self.confidence_config = ConfidenceWeights(
            vosk_weight=0.4,
            word_frequency_weight=0.25,
            context_coherence_weight=0.2,
            audio_quality_weight=0.15
        )
        
        # 阈值控制配置
        self.threshold_config = ThresholdConfig(
            base_threshold=0.6,
            audio_quality_weight=0.3,
            emotion_intensity_weight=0.2,
            historical_weight=0.3,
            real_time_weight=0.2
        )
        
        # 服务级别配置
        self.enable_audio_preprocessing = True
        self.enable_confidence_enhancement = True
        self.enable_emotion_analysis = True
        self.enable_text_postprocessing = True
        self.enable_adaptive_threshold = True
        
        # 性能配置
        self.max_concurrent_requests = 10
        self.enable_caching = True
        self.cache_size = 1000
        self.enable_metrics = True

class EnhancedASTService:
    """增强版AST语音转录服务
    
    完全兼容原有AST服务接口，同时提供针对情感博主场景的增强功能
    """
    
    def __init__(self, config: Optional[EnhancedASTServiceConfig] = None):
        self.config = config or EnhancedASTServiceConfig()
        
        # 初始化所有增强组件
        self._initialize_components()
        
        # 服务状态
        self.is_running = False
        self.session_count = 0
        
        # 性能统计
        self.service_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_processing_time": 0.0,
            "average_confidence": 0.0,
            "enhancement_usage": {
                "audio_preprocessing": 0,
                "confidence_enhancement": 0,
                "emotion_analysis": 0,
                "text_postprocessing": 0,
                "adaptive_threshold": 0
            }
        }
        
        # 缓存
        self.result_cache = {} if self.config.enable_caching else None
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("增强版AST服务已初始化")
    
    def _initialize_components(self):
        """初始化所有增强组件"""
        try:
            # 音频预处理器
            if self.config.enable_audio_preprocessing:
                self.audio_preprocessor = AudioPreprocessorEnhanced(self.config.audio_config)
                self.logger.info("音频预处理器已初始化")
            
            # 智能置信度计算器
            if self.config.enable_confidence_enhancement:
                self.confidence_calculator = IntelligentConfidenceCalculator(self.config.confidence_config)
                self.logger.info("智能置信度计算器已初始化")
            
            # 情感分析器
            if self.config.enable_emotion_analysis:
                self.emotion_analyzer = EmotionalAnalyzerEnhanced(self.config.audio_config.sample_rate)
                self.logger.info("情感分析器已初始化")
            
            # 文本后处理器
            if self.config.enable_text_postprocessing:
                self.text_postprocessor = LiveStreamTextPostProcessor()
                self.logger.info("文本后处理器已初始化")
            
            # 自适应阈值控制器
            if self.config.enable_adaptive_threshold:
                self.threshold_controller = AdaptiveThresholdController(self.config.threshold_config)
                self.logger.info("自适应阈值控制器已初始化")
            
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            raise
    
    async def transcribe_audio(self, 
                             audio_data: bytes,
                             session_id: str = "",
                             room_id: str = "",
                             enable_enhancements: bool = True,
                             processing_types: Optional[List[ProcessingType]] = None) -> EnhancedTranscriptionResult:
        """转录音频数据
        
        Args:
            audio_data: 音频字节数据
            session_id: 会话ID
            room_id: 房间ID
            enable_enhancements: 是否启用增强功能
            processing_types: 指定的处理类型
            
        Returns:
            增强版转录结果
        """
        start_time = time.time()
        request_id = f"{session_id}_{int(start_time * 1000)}"
        
        try:
            self.service_stats["total_requests"] += 1
            
            # 1. 输入验证
            if not audio_data or len(audio_data) < 100:
                raise ValueError("音频数据无效或过短")
            
            # 2. 检查缓存
            if self.result_cache and enable_enhancements:
                cache_key = self._generate_cache_key(audio_data, processing_types)
                if cache_key in self.result_cache:
                    self.logger.debug(f"缓存命中: {request_id}")
                    return self.result_cache[cache_key]
            
            # 3. 音频预处理
            processed_audio = audio_data
            audio_quality = None
            
            if enable_enhancements and self.config.enable_audio_preprocessing:
                processed_audio, audio_quality = await self._process_audio(audio_data)
                self.service_stats["enhancement_usage"]["audio_preprocessing"] += 1
            
            # 4. 基础语音识别（模拟VOSK调用）
            vosk_result = await self._call_vosk_recognition(processed_audio)
            
            # 5. 情感分析
            emotional_features = None
            if enable_enhancements and self.config.enable_emotion_analysis:
                emotional_features = await self._analyze_emotion(
                    vosk_result["text"], 
                    self._bytes_to_audio_array(processed_audio),
                    vosk_result["duration"],
                    audio_quality
                )
                self.service_stats["enhancement_usage"]["emotion_analysis"] += 1
            
            # 6. 智能置信度计算
            confidence_breakdown = None
            final_confidence = vosk_result["confidence"]
            
            if enable_enhancements and self.config.enable_confidence_enhancement:
                confidence_breakdown = await self._calculate_enhanced_confidence(
                    vosk_result["text"],
                    vosk_result["confidence"],
                    vosk_result.get("words", []),
                    audio_quality,
                    emotional_features
                )
                final_confidence = confidence_breakdown.final_confidence
                self.service_stats["enhancement_usage"]["confidence_enhancement"] += 1
            
            # 7. 自适应阈值检查
            adaptive_threshold = None
            if enable_enhancements and self.config.enable_adaptive_threshold:
                adaptive_threshold = await self._get_adaptive_threshold(
                    audio_quality, emotional_features, confidence_breakdown
                )
                self.service_stats["enhancement_usage"]["adaptive_threshold"] += 1
            
            # 8. 文本后处理
            processed_text = vosk_result["text"]
            applied_corrections = []
            processing_confidence = 1.0
            applied_processing_types = []
            
            if enable_enhancements and self.config.enable_text_postprocessing:
                post_result = await self._process_text(
                    vosk_result["text"],
                    emotional_features.emotion_type if emotional_features else None,
                    processing_types
                )
                processed_text = post_result.processed_text
                applied_corrections = post_result.applied_corrections
                processing_confidence = post_result.processing_confidence
                applied_processing_types = post_result.processing_types
                self.service_stats["enhancement_usage"]["text_postprocessing"] += 1
            
            # 9. 构建增强版结果
            result = create_enhanced_result(
                text=processed_text,
                confidence=final_confidence,
                audio_quality=audio_quality,
                emotional_features=emotional_features,
                confidence_breakdown=confidence_breakdown,
                timestamp=start_time,
                duration=vosk_result["duration"],
                is_final=True,
                words=vosk_result.get("words"),
                room_id=room_id,
                session_id=session_id
            )
            
            # 设置增强字段
            result.post_processing_applied = applied_processing_types
            result.adaptive_threshold_used = adaptive_threshold
            result.original_text = vosk_result["text"] if processed_text != vosk_result["text"] else None
            result.processing_time_ms = (time.time() - start_time) * 1000
            
            # 10. 缓存结果
            if self.result_cache and enable_enhancements:
                self._cache_result(cache_key, result)
            
            # 11. 更新统计
            self._update_service_stats(True, time.time() - start_time, final_confidence)
            
            self.logger.debug(f"转录完成: {request_id}, 耗时: {result.processing_time_ms:.1f}ms")
            
            return result
            
        except Exception as e:
            self.logger.error(f"转录失败: {request_id}, 错误: {e}")
            self._update_service_stats(False, time.time() - start_time, 0.0)
            
            # 返回基础结果
            return EnhancedTranscriptionResult(
                text="",
                confidence=0.0,
                timestamp=start_time,
                duration=0.0,
                is_final=True,
                room_id=room_id,
                session_id=session_id,
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _process_audio(self, audio_data: bytes) -> Tuple[bytes, AudioQuality]:
        """音频预处理"""
        try:
            return self.audio_preprocessor.process_audio_chunk(audio_data)
        except Exception as e:
            self.logger.error(f"音频预处理失败: {e}")
            # 返回原始音频和默认质量
            default_quality = AudioQuality(0.5, 0.5, 0.5, DEFAULT_SAMPLE_RATE)
            return audio_data, default_quality
    
    async def _call_vosk_recognition(self, audio_data: bytes) -> Dict[str, Any]:
        """调用VOSK语音识别（模拟实现）"""
        try:
            # 这里应该集成真实的VOSK识别
            # 目前返回模拟结果用于框架验证
            
            # 估算音频时长
            audio_array = self._bytes_to_audio_array(audio_data)
            duration = len(audio_array) / DEFAULT_SAMPLE_RATE
            
            # 模拟识别结果
            return {
                "text": "这款口红的颜色真的很好看",  # 模拟识别文本
                "confidence": 0.75,  # 模拟VOSK置信度
                "duration": duration,
                "words": [
                    {"word": "这款", "start": 0.0, "end": 0.5, "conf": 0.8},
                    {"word": "口红", "start": 0.5, "end": 1.0, "conf": 0.9},
                    {"word": "的", "start": 1.0, "end": 1.2, "conf": 0.7},
                    {"word": "颜色", "start": 1.2, "end": 1.8, "conf": 0.8},
                    {"word": "真的", "start": 1.8, "end": 2.2, "conf": 0.9},
                    {"word": "很", "start": 2.2, "end": 2.4, "conf": 0.6},
                    {"word": "好看", "start": 2.4, "end": 3.0, "conf": 0.8}
                ]
            }
            
        except Exception as e:
            self.logger.error(f"VOSK识别失败: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "duration": 0.0,
                "words": []
            }
    
    async def _analyze_emotion(self, text: str, audio_array: Optional[np.ndarray], 
                             duration: float, audio_quality: Optional[AudioQuality]) -> EmotionalFeatures:
        """情感分析"""
        try:
            return self.emotion_analyzer.analyze_comprehensive_emotion(
                text=text,
                audio_data=audio_array,
                duration=duration,
                audio_quality=audio_quality
            )
        except Exception as e:
            self.logger.error(f"情感分析失败: {e}")
            # 返回默认情感特征
            return EmotionalFeatures(
                emotion_type=EmotionType.NEUTRAL,
                intensity=0.5,
                speech_rate=150.0,
                tone_confidence=0.5
            )
    
    async def _calculate_enhanced_confidence(self, text: str, vosk_confidence: float,
                                           words: List[Dict[str, Any]], audio_quality: Optional[AudioQuality],
                                           emotional_features: Optional[EmotionalFeatures]) -> ConfidenceBreakdown:
        """计算增强置信度"""
        try:
            return self.confidence_calculator.calculate_enhanced_confidence(
                text=text,
                vosk_confidence=vosk_confidence,
                words=None,  # 转换格式留待后续优化
                audio_quality=audio_quality,
                emotional_features=emotional_features
            )
        except Exception as e:
            self.logger.error(f"置信度计算失败: {e}")
            # 返回基础置信度分解
            return ConfidenceBreakdown(
                vosk_confidence=vosk_confidence,
                word_frequency_score=0.5,
                context_coherence_score=0.5,
                audio_quality_score=0.5,
                emotion_boost=0.0,
                final_confidence=vosk_confidence
            )
    
    async def _get_adaptive_threshold(self, audio_quality: Optional[AudioQuality],
                                    emotional_features: Optional[EmotionalFeatures],
                                    confidence_breakdown: Optional[ConfidenceBreakdown]) -> float:
        """获取自适应阈值"""
        try:
            return self.threshold_controller.calculate_adaptive_threshold(
                audio_quality=audio_quality,
                emotional_features=emotional_features,
                confidence_breakdown=confidence_breakdown
            )
        except Exception as e:
            self.logger.error(f"阈值计算失败: {e}")
            return self.config.threshold_config.base_threshold
    
    async def _process_text(self, text: str, emotion_type: Optional[EmotionType],
                          processing_types: Optional[List[ProcessingType]]) -> PostProcessingResult:
        """文本后处理"""
        try:
            return self.text_postprocessor.process_text(
                text=text,
                emotion_type=emotion_type,
                processing_types=processing_types
            )
        except Exception as e:
            self.logger.error(f"文本后处理失败: {e}")
            # 返回未处理的结果
            from text_postprocessor_enhanced import PostProcessingResult
            return PostProcessingResult(
                original_text=text,
                processed_text=text,
                applied_corrections=[],
                processing_confidence=1.0,
                processing_types=[]
            )
    
    def _bytes_to_audio_array(self, audio_data: bytes) -> np.ndarray:
        """将字节数据转换为音频数组"""
        try:
            return np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        except Exception as e:
            self.logger.error(f"音频数据转换失败: {e}")
            return np.array([])
    
    def _generate_cache_key(self, audio_data: bytes, processing_types: Optional[List[ProcessingType]]) -> str:
        """生成缓存键"""
        import hashlib
        audio_hash = hashlib.md5(audio_data).hexdigest()[:16]
        types_str = ",".join([t.value for t in processing_types]) if processing_types else "default"
        return f"{audio_hash}_{types_str}"
    
    def _cache_result(self, cache_key: str, result: EnhancedTranscriptionResult):
        """缓存结果"""
        if len(self.result_cache) >= self.config.cache_size:
            # 移除最旧的缓存项
            oldest_key = next(iter(self.result_cache))
            del self.result_cache[oldest_key]
        
        self.result_cache[cache_key] = result
    
    def _update_service_stats(self, success: bool, processing_time: float, confidence: float):
        """更新服务统计"""
        if success:
            self.service_stats["successful_requests"] += 1
        else:
            self.service_stats["failed_requests"] += 1
        
        # 更新平均处理时间
        total_requests = self.service_stats["total_requests"]
        prev_avg_time = self.service_stats["average_processing_time"]
        self.service_stats["average_processing_time"] = (
            (prev_avg_time * (total_requests - 1) + processing_time) / total_requests
        )
        
        # 更新平均置信度
        if success:
            prev_avg_conf = self.service_stats["average_confidence"]
            success_count = self.service_stats["successful_requests"]
            self.service_stats["average_confidence"] = (
                (prev_avg_conf * (success_count - 1) + confidence) / success_count
            )
    
    # 兼容性接口方法
    def transcribe(self, audio_data: bytes, **kwargs) -> Dict[str, Any]:
        """同步转录接口（向后兼容）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.transcribe_audio(audio_data, **kwargs))
            return result.to_legacy_format()
        except Exception as e:
            self.logger.error(f"同步转录失败: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "timestamp": time.time(),
                "duration": 0.0,
                "is_final": True,
                "words": [],
                "room_id": kwargs.get("room_id", ""),
                "session_id": kwargs.get("session_id", "")
            }
    
    def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        stats = self.service_stats.copy()
        
        # 添加组件统计
        if hasattr(self, 'audio_preprocessor'):
            stats["audio_preprocessor_stats"] = self.audio_preprocessor.get_processing_stats()
        
        if hasattr(self, 'confidence_calculator'):
            stats["confidence_calculator_stats"] = self.confidence_calculator.get_calculation_stats()
        
        if hasattr(self, 'emotion_analyzer'):
            stats["emotion_analyzer_stats"] = self.emotion_analyzer.get_analysis_stats()
        
        if hasattr(self, 'text_postprocessor'):
            stats["text_postprocessor_stats"] = self.text_postprocessor.get_processing_stats()
        
        if hasattr(self, 'threshold_controller'):
            stats["threshold_controller_stats"] = self.threshold_controller.get_adjustment_stats()
        
        return stats
    
    def reset_service_stats(self):
        """重置服务统计"""
        self.service_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_processing_time": 0.0,
            "average_confidence": 0.0,
            "enhancement_usage": {
                "audio_preprocessing": 0,
                "confidence_enhancement": 0,
                "emotion_analysis": 0,
                "text_postprocessing": 0,
                "adaptive_threshold": 0
            }
        }
        
        # 重置组件统计
        if hasattr(self, 'audio_preprocessor'):
            self.audio_preprocessor.reset_stats()
        
        if hasattr(self, 'confidence_calculator'):
            self.confidence_calculator.reset_statistics()
        
        if hasattr(self, 'emotion_analyzer'):
            self.emotion_analyzer.reset_stats()
        
        if hasattr(self, 'text_postprocessor'):
            self.text_postprocessor.reset_stats()
        
        if hasattr(self, 'threshold_controller'):
            self.threshold_controller.reset_controller()
        
        self.logger.info("服务统计已重置")

# 导出主要类
__all__ = [
    'EnhancedASTService',
    'EnhancedASTServiceConfig'
]