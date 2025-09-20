#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情感语调分析器
为情感博主语音识别场景优化的情感和语调分析组件

主要功能:
1. 语调情感识别
2. 语速分析和检测  
3. 停顿模式分析
4. 语音压力指标计算
5. 情感强度评估
"""

import re
import math
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict
import scipy.signal
from enhanced_transcription_result import (
    EmotionalFeatures,
    EmotionType,
    AudioQuality
)

# 情感分析常量
DEFAULT_SPEECH_RATE = 150.0  # 默认语速 (词/分钟)
PAUSE_THRESHOLD = 0.3       # 停顿检测阈值 (秒)
STRESS_THRESHOLD = 0.6      # 语音压力阈值
EMOTION_CONFIDENCE_THRESHOLD = 0.4  # 情感识别置信度阈值

@dataclass
class SpeechFeatures:
    """语音特征数据"""
    fundamental_frequency: float    # 基频 (Hz)
    pitch_variance: float          # 音调变化度
    energy_variance: float         # 能量变化度
    spectral_centroid: float       # 频谱重心
    zero_crossing_rate: float      # 过零率
    mfcc_features: Optional[List[float]] = None  # MFCC特征

@dataclass 
class EmotionPatterns:
    """情感模式数据"""
    text_emotion_indicators: Dict[EmotionType, List[str]]
    prosody_emotion_mapping: Dict[str, EmotionType]
    intensity_thresholds: Dict[EmotionType, Tuple[float, float]]

class ProsodyAnalyzer:
    """韵律分析器 - 分析语音的韵律特征"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.logger = logging.getLogger(__name__)
        
        # 情感韵律特征阈值
        self.prosody_thresholds = {
            EmotionType.EXCITED: {
                "pitch_mean_min": 180,    # 基频均值下限 (Hz)
                "pitch_variance_min": 50,  # 音调变化度下限
                "energy_variance_min": 0.3 # 能量变化度下限
            },
            EmotionType.CALM: {
                "pitch_mean_max": 150,    # 基频均值上限
                "pitch_variance_max": 20,  # 音调变化度上限  
                "energy_variance_max": 0.1 # 能量变化度上限
            },
            EmotionType.JOYFUL: {
                "pitch_mean_min": 160,
                "pitch_variance_min": 30,
                "energy_variance_min": 0.2
            },
            EmotionType.FRUSTRATED: {
                "pitch_mean_min": 170,
                "pitch_variance_min": 40,
                "energy_variance_min": 0.4
            }
        }
    
    def extract_prosody_features(self, audio_data: np.ndarray) -> SpeechFeatures:
        """提取韵律特征
        
        Args:
            audio_data: 音频数据 (归一化到[-1,1])
            
        Returns:
            语音特征数据
        """
        try:
            # 1. 基频提取
            fundamental_freq = self._extract_fundamental_frequency(audio_data)
            
            # 2. 音调变化度
            pitch_variance = self._calculate_pitch_variance(audio_data)
            
            # 3. 能量变化度  
            energy_variance = self._calculate_energy_variance(audio_data)
            
            # 4. 频谱重心
            spectral_centroid = self._calculate_spectral_centroid(audio_data)
            
            # 5. 过零率
            zero_crossing_rate = self._calculate_zero_crossing_rate(audio_data)
            
            # 6. MFCC特征 (简化版)
            mfcc_features = self._extract_mfcc_features(audio_data)
            
            return SpeechFeatures(
                fundamental_frequency=fundamental_freq,
                pitch_variance=pitch_variance,
                energy_variance=energy_variance,
                spectral_centroid=spectral_centroid,
                zero_crossing_rate=zero_crossing_rate,
                mfcc_features=mfcc_features
            )
            
        except Exception as e:
            self.logger.error(f"韵律特征提取失败: {e}")
            # 返回默认特征
            return SpeechFeatures(
                fundamental_frequency=150.0,
                pitch_variance=20.0,
                energy_variance=0.2,
                spectral_centroid=1000.0,
                zero_crossing_rate=0.1
            )
    
    def _extract_fundamental_frequency(self, audio_data: np.ndarray) -> float:
        """提取基频 (F0)"""
        try:
            # 使用自相关法估计基频
            # 预处理：低通滤波
            nyquist = self.sample_rate / 2
            low_cutoff = 50 / nyquist   # 50Hz低通
            high_cutoff = 400 / nyquist # 400Hz高通
            
            sos = scipy.signal.butter(4, [low_cutoff, high_cutoff], 
                                     btype='band', output='sos')
            filtered_audio = scipy.signal.sosfilt(sos, audio_data)
            
            # 自相关计算
            correlation = np.correlate(filtered_audio, filtered_audio, mode='full')
            correlation = correlation[correlation.size // 2:]
            
            # 寻找第一个峰值 (排除0延迟)
            min_period = int(self.sample_rate / 400)  # 最高400Hz
            max_period = int(self.sample_rate / 50)   # 最低50Hz
            
            if max_period < len(correlation):
                peak_idx = np.argmax(correlation[min_period:max_period]) + min_period
                fundamental_freq = self.sample_rate / peak_idx
            else:
                fundamental_freq = 150.0  # 默认基频
                
            return max(50.0, min(400.0, float(fundamental_freq)))
            
        except Exception:
            return 150.0  # 默认女性说话基频
    
    def _calculate_pitch_variance(self, audio_data: np.ndarray) -> float:
        """计算音调变化度"""
        try:
            # 分帧计算基频
            frame_length = int(0.025 * self.sample_rate)  # 25ms帧
            hop_length = int(0.01 * self.sample_rate)     # 10ms步长
            
            pitch_values = []
            for i in range(0, len(audio_data) - frame_length, hop_length):
                frame = audio_data[i:i+frame_length]
                if np.sum(frame**2) > 0.001:  # 只分析有能量的帧
                    pitch = self._extract_fundamental_frequency(frame)
                    pitch_values.append(pitch)
            
            if len(pitch_values) < 2:
                return 20.0
            
            # 计算标准差作为变化度
            pitch_variance = np.std(pitch_values)
            return min(float(pitch_variance), 100.0)  # 限制最大值
            
        except Exception:
            return 20.0
    
    def _calculate_energy_variance(self, audio_data: np.ndarray) -> float:
        """计算能量变化度"""
        try:
            # 分帧计算能量
            frame_length = int(0.025 * self.sample_rate)
            hop_length = int(0.01 * self.sample_rate)
            
            energy_values = []
            for i in range(0, len(audio_data) - frame_length, hop_length):
                frame = audio_data[i:i+frame_length]
                energy = np.sum(frame**2) / len(frame)
                energy_values.append(energy)
            
            if len(energy_values) < 2:
                return 0.1
            
            # 计算相对变化度
            energy_variance = np.std(energy_values) / (np.mean(energy_values) + 1e-8)
            return min(float(energy_variance), 1.0)
            
        except Exception:
            return 0.1
    
    def _calculate_spectral_centroid(self, audio_data: np.ndarray) -> float:
        """计算频谱重心"""
        try:
            # 计算功率谱
            freqs, psd = scipy.signal.welch(audio_data, self.sample_rate, nperseg=1024)
            
            # 计算频谱重心
            centroid = np.sum(freqs * psd) / (np.sum(psd) + 1e-8)
            return min(centroid, self.sample_rate / 2)
            
        except Exception:
            return 1000.0  # 默认值
    
    def _calculate_zero_crossing_rate(self, audio_data: np.ndarray) -> float:
        """计算过零率"""
        try:
            # 计算符号变化
            sign_changes = np.diff(np.sign(audio_data))
            zero_crossings = np.sum(np.abs(sign_changes)) / 2
            zcr = zero_crossings / len(audio_data)
            return min(zcr, 1.0)
            
        except Exception:
            return 0.1
    
    def _extract_mfcc_features(self, audio_data: np.ndarray, 
                              n_mfcc: int = 13) -> List[float]:
        """提取MFCC特征 (简化版)"""
        try:
            # 简化的MFCC实现
            # 1. 预加重
            pre_emphasized = np.append(audio_data[0], 
                                     audio_data[1:] - 0.97 * audio_data[:-1])
            
            # 2. 加窗和FFT
            windowed = pre_emphasized * np.hanning(len(pre_emphasized))
            fft = np.fft.rfft(windowed)
            magnitude = np.abs(fft)
            
            # 3. 梅尔滤波器组 (简化版)
            mel_filters = self._create_mel_filterbank(len(magnitude))
            mel_spectrum = np.dot(mel_filters, magnitude)
            
            # 4. 对数和DCT
            log_mel = np.log(mel_spectrum + 1e-8)
            mfcc = scipy.fft.dct(log_mel, type=2, norm='ortho')[:n_mfcc]
            
            return mfcc.tolist()
            
        except Exception:
            # 返回默认MFCC特征
            return [1.0] + [0.0] * 12
    
    def _create_mel_filterbank(self, n_fft: int, n_filters: int = 26) -> np.ndarray:
        """创建梅尔滤波器组"""
        # 简化的梅尔滤波器实现
        mel_filters = np.zeros((n_filters, n_fft))
        
        # 梅尔频率范围
        mel_min = 0
        mel_max = 2595 * np.log10(1 + (self.sample_rate / 2) / 700)
        mel_points = np.linspace(mel_min, mel_max, n_filters + 2)
        
        # 转换回Hz
        hz_points = 700 * (np.power(10, mel_points / 2595) - 1)
        bin_points = np.floor((n_fft + 1) * hz_points / self.sample_rate).astype(int)
        
        for i in range(1, n_filters + 1):
            left = bin_points[i - 1]
            center = bin_points[i]
            right = bin_points[i + 1]
            
            for j in range(left, center):
                if center > left:
                    mel_filters[i - 1, j] = (j - left) / (center - left)
            
            for j in range(center, right):
                if right > center:
                    mel_filters[i - 1, j] = (right - j) / (right - center)
        
        return mel_filters

class TextEmotionAnalyzer:
    """文本情感分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 情感关键词词典
        self.emotion_keywords = {
            EmotionType.EXCITED: {
                "强烈词汇": ["太棒了", "超级", "激动", "兴奋", "哇", "绝了", "yyds", "爱了"],
                "语气词": ["呀", "啊", "哎呀", "天哪", "我的天"],
                "强调词": ["真的", "超", "特别", "非常", "巨", "贼"]
            },
            EmotionType.JOYFUL: {
                "积极词汇": ["开心", "高兴", "快乐", "愉快", "美好", "幸福", "甜蜜"],
                "喜爱词汇": ["喜欢", "爱", "钟爱", "迷恋", "心动", "满意"],
                "赞美词汇": ["好", "棒", "赞", "优秀", "完美", "惊艳", "美"]
            },
            EmotionType.CALM: {
                "平静词汇": ["平静", "安静", "淡定", "从容", "稳重", "温和"],
                "舒缓词汇": ["舒服", "放松", "轻松", "自在", "惬意", "宁静"],
                "理性词汇": ["理性", "客观", "冷静", "思考", "分析", "判断"]
            },
            EmotionType.FRUSTRATED: {
                "负面词汇": ["烦", "累", "难受", "不爽", "郁闷", "无语"],
                "困难词汇": ["困难", "麻烦", "复杂", "头疼", "棘手"],
                "否定词汇": ["不", "没", "不是", "不对", "不行", "不好"]
            },
            EmotionType.ANXIOUS: {
                "担心词汇": ["担心", "焦虑", "紧张", "不安", "忧虑", "害怕"],
                "犹豫词汇": ["犹豫", "纠结", "矛盾", "迷茫", "困惑"],
                "急迫词汇": ["急", "赶紧", "快", "马上", "立刻", "迫切"]
            }
        }
        
        # 情感强度修饰词
        self.intensity_modifiers = {
            "高强度": ["超级", "特别", "非常", "极其", "相当", "巨", "贼", "太"],
            "中强度": ["比较", "还", "挺", "蛮", "很", "真的"],
            "低强度": ["稍微", "略", "有点", "一点", "些许"]
        }
    
    def analyze_text_emotion(self, text: str) -> Tuple[EmotionType, float, Dict[str, Any]]:
        """分析文本情感
        
        Args:
            text: 输入文本
            
        Returns:
            (情感类型, 强度, 分析详情)
        """
        try:
            # 1. 情感关键词匹配
            emotion_scores = self._calculate_emotion_scores(text)
            
            # 2. 强度修饰词分析
            intensity_factor = self._analyze_intensity_modifiers(text)
            
            # 3. 确定主要情感
            if not emotion_scores:
                return EmotionType.NEUTRAL, 0.3, {"keywords": [], "modifiers": []}
            
            # 找到得分最高的情感
            primary_emotion = max(emotion_scores.keys(), key=lambda k: emotion_scores[k])
            base_intensity = emotion_scores[primary_emotion]
            
            # 4. 应用强度修饰
            final_intensity = min(base_intensity * intensity_factor, 1.0)
            
            # 5. 构建分析详情
            analysis_details = {
                "emotion_scores": emotion_scores,
                "intensity_factor": intensity_factor,
                "keywords_found": self._extract_found_keywords(text, primary_emotion),
                "modifiers_found": self._extract_found_modifiers(text)
            }
            
            return primary_emotion, final_intensity, analysis_details
            
        except Exception as e:
            self.logger.error(f"文本情感分析失败: {e}")
            return EmotionType.NEUTRAL, 0.3, {"error": str(e)}
    
    def _calculate_emotion_scores(self, text: str) -> Dict[EmotionType, float]:
        """计算各情感类型得分"""
        emotion_scores = {}
        
        for emotion_type, keyword_groups in self.emotion_keywords.items():
            total_score = 0.0
            total_keywords = 0
            
            for group_name, keywords in keyword_groups.items():
                group_score = 0.0
                for keyword in keywords:
                    if keyword in text:
                        # 根据关键词组别设置权重
                        if "强烈" in group_name or "积极" in group_name:
                            weight = 1.5
                        elif "语气" in group_name:
                            weight = 1.2
                        else:
                            weight = 1.0
                        
                        # 考虑关键词长度
                        length_bonus = len(keyword) / 4.0
                        
                        group_score += weight * (1.0 + length_bonus)
                        total_keywords += 1
                
                total_score += group_score
            
            if total_keywords > 0:
                # 归一化得分
                normalized_score = min(total_score / (total_keywords + 1), 1.0)
                emotion_scores[emotion_type] = normalized_score
        
        return emotion_scores
    
    def _analyze_intensity_modifiers(self, text: str) -> float:
        """分析强度修饰词"""
        intensity_factor = 1.0
        
        # 检查不同强度的修饰词
        for intensity_level, modifiers in self.intensity_modifiers.items():
            for modifier in modifiers:
                if modifier in text:
                    if "高强度" in intensity_level:
                        intensity_factor *= 1.5
                    elif "中强度" in intensity_level:
                        intensity_factor *= 1.2
                    else:  # 低强度
                        intensity_factor *= 0.8
                    break  # 每个强度级别只计算一次
        
        return min(intensity_factor, 2.0)  # 限制最大放大倍数
    
    def _extract_found_keywords(self, text: str, emotion_type: EmotionType) -> List[str]:
        """提取文本中找到的情感关键词"""
        found_keywords = []
        
        if emotion_type in self.emotion_keywords:
            for group_name, keywords in self.emotion_keywords[emotion_type].items():
                for keyword in keywords:
                    if keyword in text:
                        found_keywords.append(keyword)
        
        return found_keywords
    
    def _extract_found_modifiers(self, text: str) -> List[str]:
        """提取文本中找到的强度修饰词"""
        found_modifiers = []
        
        for intensity_level, modifiers in self.intensity_modifiers.items():
            for modifier in modifiers:
                if modifier in text:
                    found_modifiers.append(modifier)
        
        return found_modifiers

class SpeechRateAnalyzer:
    """语速分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 语速评估标准 (词/分钟)
        self.speech_rate_ranges = {
            "very_slow": (60, 100),
            "slow": (100, 140),
            "normal": (140, 180),
            "fast": (180, 220),
            "very_fast": (220, 300)
        }
        
        # 情感与语速的关联
        self.emotion_speech_rate_mapping = {
            EmotionType.EXCITED: (180, 250),    # 兴奋时语速较快
            EmotionType.JOYFUL: (150, 200),     # 愉快时语速适中偏快
            EmotionType.CALM: (120, 160),       # 平静时语速较慢
            EmotionType.FRUSTRATED: (100, 140), # 沮丧时语速较慢
            EmotionType.ANXIOUS: (160, 220),    # 焦虑时语速不稳定
            EmotionType.NEUTRAL: (140, 180)     # 中性时语速正常
        }
    
    def calculate_speech_rate(self, text: str, duration: float, 
                            word_count: Optional[int] = None) -> float:
        """计算语速
        
        Args:
            text: 识别文本
            duration: 音频时长(秒)
            word_count: 词汇数量(可选)
            
        Returns:
            语速 (词/分钟)
        """
        try:
            if duration <= 0:
                return DEFAULT_SPEECH_RATE
            
            # 估算词汇数量
            if word_count is None:
                # 简单的中文词汇计数
                # 移除标点符号
                clean_text = re.sub(r'[^\u4e00-\u9fa5\w\s]', '', text)
                
                # 中文按字算，英文按词算
                chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', clean_text))
                english_words = len(re.findall(r'\b[a-zA-Z]+\b', clean_text))
                
                # 中文字转词(平均每个词2个字)
                estimated_words = chinese_chars / 2 + english_words
            else:
                estimated_words = word_count
            
            # 计算语速
            speech_rate = (estimated_words / duration) * 60  # 转换为每分钟
            
            # 限制合理范围
            return max(30.0, min(speech_rate, 400.0))
            
        except Exception as e:
            self.logger.error(f"语速计算失败: {e}")
            return DEFAULT_SPEECH_RATE
    
    def analyze_speech_rate_pattern(self, speech_rate: float) -> Dict[str, Any]:
        """分析语速模式"""
        # 确定语速类别
        rate_category = "normal"
        for category, (min_rate, max_rate) in self.speech_rate_ranges.items():
            if min_rate <= speech_rate < max_rate:
                rate_category = category
                break
        
        # 分析可能的情感状态
        possible_emotions = []
        for emotion, (min_rate, max_rate) in self.emotion_speech_rate_mapping.items():
            if min_rate <= speech_rate <= max_rate:
                # 计算匹配度
                center = (min_rate + max_rate) / 2
                distance = abs(speech_rate - center)
                range_width = max_rate - min_rate
                match_score = 1.0 - (distance / range_width)
                
                possible_emotions.append({
                    "emotion": emotion,
                    "match_score": max(0.0, match_score)
                })
        
        # 按匹配度排序
        possible_emotions.sort(key=lambda x: x["match_score"], reverse=True)
        
        return {
            "rate_category": rate_category,
            "speech_rate": speech_rate,
            "possible_emotions": possible_emotions[:3],  # 返回前3个可能的情感
            "is_abnormal": rate_category in ["very_slow", "very_fast"]
        }

class PausePatternAnalyzer:
    """停顿模式分析器"""
    
    def __init__(self, pause_threshold: float = PAUSE_THRESHOLD):
        self.pause_threshold = pause_threshold
        self.logger = logging.getLogger(__name__)
    
    def detect_pause_patterns(self, audio_data: np.ndarray, 
                            sample_rate: int) -> List[float]:
        """检测停顿模式
        
        Args:
            audio_data: 音频数据
            sample_rate: 采样率
            
        Returns:
            停顿时长列表(秒)
        """
        try:
            # 计算短时能量
            frame_length = int(0.025 * sample_rate)  # 25ms帧
            hop_length = int(0.01 * sample_rate)     # 10ms步长
            
            energy_values = []
            for i in range(0, len(audio_data) - frame_length, hop_length):
                frame = audio_data[i:i+frame_length]
                energy = np.sum(frame ** 2) / len(frame)
                energy_values.append(energy)
            
            # 检测低能量区域(停顿)
            energy_threshold = np.mean(energy_values) * 0.1  # 能量阈值
            silence_frames = np.array(energy_values) < energy_threshold
            
            # 找到连续的静音段
            pause_durations = []
            in_pause = False
            pause_start = 0
            
            for i, is_silent in enumerate(silence_frames):
                if is_silent and not in_pause:
                    # 停顿开始
                    pause_start = i
                    in_pause = True
                elif not is_silent and in_pause:
                    # 停顿结束
                    pause_length = (i - pause_start) * hop_length / sample_rate
                    if pause_length >= self.pause_threshold:
                        pause_durations.append(pause_length)
                    in_pause = False
            
            return pause_durations
            
        except Exception as e:
            self.logger.error(f"停顿模式检测失败: {e}")
            return []
    
    def analyze_pause_characteristics(self, pause_durations: List[float]) -> Dict[str, Any]:
        """分析停顿特征"""
        if not pause_durations:
            return {
                "pause_count": 0,
                "average_pause_duration": 0.0,
                "pause_variance": 0.0,
                "pause_pattern": "no_pauses",
                "emotional_indicator": "neutral"
            }
        
        pause_count = len(pause_durations)
        avg_duration = np.mean(pause_durations)
        pause_variance = np.var(pause_durations)
        
        # 分析停顿模式
        if avg_duration > 1.0:
            if pause_variance > 0.5:
                pause_pattern = "irregular_long"  # 不规则长停顿
                emotional_indicator = "anxious_or_thinking"
            else:
                pause_pattern = "regular_long"    # 规则长停顿
                emotional_indicator = "calm_or_deliberate"
        elif avg_duration > 0.5:
            pause_pattern = "normal"             # 正常停顿
            emotional_indicator = "neutral"
        else:
            if pause_count > 10:
                pause_pattern = "frequent_short"   # 频繁短停顿
                emotional_indicator = "excited_or_nervous"
            else:
                pause_pattern = "minimal"          # 最少停顿
                emotional_indicator = "fluent_or_excited"
        
        return {
            "pause_count": pause_count,
            "average_pause_duration": avg_duration,
            "pause_variance": pause_variance,
            "pause_pattern": pause_pattern,
            "emotional_indicator": emotional_indicator
        }

class EmotionalAnalyzerEnhanced:
    """增强版情感分析器
    
    整合音频韵律分析、文本情感分析、语速分析和停顿模式分析
    """
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        
        # 初始化各个分析器
        self.prosody_analyzer = ProsodyAnalyzer(sample_rate)
        self.text_analyzer = TextEmotionAnalyzer()
        self.speech_rate_analyzer = SpeechRateAnalyzer()
        self.pause_analyzer = PausePatternAnalyzer()
        
        # 统计数据
        self.analysis_stats = {
            "total_analyses": 0,
            "emotion_distribution": defaultdict(int),
            "average_intensity": 0.0,
            "average_speech_rate": 0.0
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("增强版情感分析器已初始化")
    
    def analyze_comprehensive_emotion(self, 
                                    text: str,
                                    audio_data: Optional[np.ndarray] = None,
                                    duration: float = 1.0,
                                    audio_quality: Optional[AudioQuality] = None) -> EmotionalFeatures:
        """综合情感分析
        
        Args:
            text: 识别文本
            audio_data: 音频数据(可选)
            duration: 音频时长
            audio_quality: 音频质量数据
            
        Returns:
            情感特征结果
        """
        try:
            # 1. 文本情感分析
            text_emotion, text_intensity, text_details = self.text_analyzer.analyze_text_emotion(text)
            
            # 2. 语速分析
            speech_rate = self.speech_rate_analyzer.calculate_speech_rate(text, duration)
            speech_rate_analysis = self.speech_rate_analyzer.analyze_speech_rate_pattern(speech_rate)
            
            # 3. 音频韵律分析(如果有音频数据)
            prosody_confidence = 0.5  # 默认置信度
            pause_patterns = []
            voice_stress = None
            
            if audio_data is not None and len(audio_data) > 0:
                # 韵律特征提取
                prosody_features = self.prosody_analyzer.extract_prosody_features(audio_data)
                prosody_confidence = self._calculate_prosody_confidence(prosody_features, audio_quality)
                
                # 停顿模式分析
                pause_durations = self.pause_analyzer.detect_pause_patterns(audio_data, self.sample_rate)
                pause_analysis = self.pause_analyzer.analyze_pause_characteristics(pause_durations)
                pause_patterns = pause_durations
                
                # 语音压力指标
                voice_stress = self._calculate_voice_stress(prosody_features, pause_analysis)
            
            # 4. 多模态融合决策
            final_emotion, final_intensity, tone_confidence = self._fuse_multimodal_analysis(
                text_emotion, text_intensity, speech_rate_analysis, 
                prosody_confidence, audio_quality
            )
            
            # 5. 更新统计数据
            self._update_analysis_stats(final_emotion, final_intensity, speech_rate)
            
            # 6. 构建情感特征结果
            emotional_features = EmotionalFeatures(
                emotion_type=final_emotion,
                intensity=final_intensity,
                speech_rate=speech_rate,
                tone_confidence=tone_confidence,
                pause_pattern=pause_patterns,
                voice_stress=voice_stress
            )
            
            return emotional_features
            
        except Exception as e:
            self.logger.error(f"综合情感分析失败: {e}")
            # 返回默认结果
            return EmotionalFeatures(
                emotion_type=EmotionType.NEUTRAL,
                intensity=0.3,
                speech_rate=DEFAULT_SPEECH_RATE,
                tone_confidence=0.3
            )
    
    def _calculate_prosody_confidence(self, prosody_features: SpeechFeatures, 
                                    audio_quality: Optional[AudioQuality]) -> float:
        """计算韵律置信度"""
        base_confidence = 0.5
        
        # 基于基频的置信度
        if 80 <= prosody_features.fundamental_frequency <= 300:
            base_confidence += 0.2
        
        # 基于音质的置信度
        if audio_quality:
            if audio_quality.clarity_score > 0.7:
                base_confidence += 0.2
            if audio_quality.noise_level < 0.3:
                base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _calculate_voice_stress(self, prosody_features: SpeechFeatures, 
                              pause_analysis: Dict[str, Any]) -> float:
        """计算语音压力指标"""
        stress_indicators = 0.0
        
        # 音调变化度指标
        if prosody_features.pitch_variance > 40:
            stress_indicators += 0.3
        
        # 能量变化度指标
        if prosody_features.energy_variance > 0.4:
            stress_indicators += 0.3
        
        # 停顿模式指标
        if pause_analysis.get("pause_pattern") == "irregular_long":
            stress_indicators += 0.2
        elif pause_analysis.get("pause_pattern") == "frequent_short":
            stress_indicators += 0.2
        
        return min(stress_indicators, 1.0)
    
    def _fuse_multimodal_analysis(self, text_emotion: EmotionType, text_intensity: float,
                                speech_rate_analysis: Dict[str, Any], prosody_confidence: float,
                                audio_quality: Optional[AudioQuality]) -> Tuple[EmotionType, float, float]:
        """融合多模态分析结果"""
        # 权重计算
        text_weight = 0.6  # 文本情感权重
        prosody_weight = 0.4 * prosody_confidence  # 韵律情感权重
        
        # 基于文本的情感和强度
        final_emotion = text_emotion
        final_intensity = text_intensity * text_weight
        
        # 基于语速的情感调整
        if speech_rate_analysis["possible_emotions"]:
            top_emotion = speech_rate_analysis["possible_emotions"][0]
            if top_emotion["match_score"] > 0.7:
                # 语速与文本情感一致时，增强置信度
                if top_emotion["emotion"] == text_emotion:
                    final_intensity += 0.1
        
        # 综合置信度
        tone_confidence = (text_weight + prosody_weight) / (text_weight + 0.4)
        
        # 音质影响
        if audio_quality and audio_quality.clarity_score < 0.5:
            tone_confidence *= 0.8  # 音质差时降低置信度
        
        return final_emotion, min(final_intensity, 1.0), min(tone_confidence, 1.0)
    
    def _update_analysis_stats(self, emotion: EmotionType, intensity: float, speech_rate: float):
        """更新分析统计数据"""
        self.analysis_stats["total_analyses"] += 1
        self.analysis_stats["emotion_distribution"][emotion] += 1
        
        # 更新平均值
        count = self.analysis_stats["total_analyses"]
        prev_avg_intensity = self.analysis_stats["average_intensity"]
        prev_avg_rate = self.analysis_stats["average_speech_rate"]
        
        self.analysis_stats["average_intensity"] = (
            (prev_avg_intensity * (count - 1) + intensity) / count
        )
        self.analysis_stats["average_speech_rate"] = (
            (prev_avg_rate * (count - 1) + speech_rate) / count
        )
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """获取分析统计信息"""
        stats = dict(self.analysis_stats)
        stats["emotion_distribution"] = dict(stats["emotion_distribution"])
        return stats
    
    def reset_stats(self):
        """重置统计数据"""
        self.analysis_stats = {
            "total_analyses": 0,
            "emotion_distribution": defaultdict(int),
            "average_intensity": 0.0,
            "average_speech_rate": 0.0
        }
        self.logger.info("情感分析统计数据已重置")

# 导出主要类
__all__ = [
    'EmotionalAnalyzerEnhanced',
    'ProsodyAnalyzer',
    'TextEmotionAnalyzer',
    'SpeechRateAnalyzer',
    'PausePatternAnalyzer',
    'SpeechFeatures',
    'EmotionPatterns'
]