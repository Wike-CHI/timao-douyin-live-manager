# -*- coding: utf-8 -*-
"""
音频预处理增强器
为情感博主语音识别场景优化的音频预处理组件

主要功能:
1. 自适应降噪处理
2. 音量归一化
3. 静音段检测
4. 音频质量实时监测
"""

import numpy as np
import time
import logging
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass
import scipy.signal
import scipy.stats
from enhanced_transcription_result import AudioQuality

# 音频处理常量
SAMPLE_RATE = 16000
FRAME_SIZE = 1024
HOP_SIZE = 512
FREQ_BINS = 512

@dataclass
class AudioProcessingConfig:
    """音频处理配置"""
    sample_rate: int = SAMPLE_RATE
    frame_size: int = FRAME_SIZE
    hop_size: int = HOP_SIZE
    noise_reduction_strength: float = 0.5  # 降噪强度 (0.0-1.0)
    volume_target: float = 0.7            # 目标音量 (0.0-1.0)
    silence_threshold: float = 0.01       # 静音阈值
    quality_window_size: int = 10         # 质量评估窗口大小

class SpectralGateDenoiser:
    """频谱门降噪器"""
    
    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.noise_profile = None
        self.logger = logging.getLogger(__name__)
        
    def estimate_noise_profile(self, audio_data: np.ndarray, 
                              noise_duration: float = 0.5) -> np.ndarray:
        """估计噪音频谱特征
        
        Args:
            audio_data: 音频数据
            noise_duration: 用于估计噪音的时长(秒)
            
        Returns:
            噪音频谱特征
        """
        try:
            # 取开头部分作为噪音样本 (假设开头是静音或背景噪音)
            noise_samples = int(noise_duration * self.sample_rate)
            noise_segment = audio_data[:min(noise_samples, len(audio_data))]
            
            # 计算噪音的功率谱密度
            f, psd = scipy.signal.welch(noise_segment, self.sample_rate, 
                                       nperseg=1024, noverlap=512)
            
            # 平滑噪音特征
            self.noise_profile = scipy.signal.savgol_filter(psd, 11, 3)
            
            return self.noise_profile
            
        except Exception as e:
            self.logger.error(f"噪音特征估计失败: {e}")
            return np.ones(FREQ_BINS) * 0.001  # 返回默认噪音特征

    def reduce_noise(self, audio_data: np.ndarray, 
                    strength: float = 0.5) -> np.ndarray:
        """应用频谱门降噪
        
        Args:
            audio_data: 输入音频数据
            strength: 降噪强度 (0.0-1.0)
            
        Returns:
            降噪后的音频数据
        """
        try:
            if self.noise_profile is None:
                self.estimate_noise_profile(audio_data)
            
            # 计算短时傅里叶变换
            f, t, stft = scipy.signal.stft(audio_data, self.sample_rate,
                                          nperseg=1024, noverlap=512)
            
            # 计算幅度谱
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # 频谱门阈值
            if self.noise_profile is not None:
                noise_floor = np.mean(self.noise_profile) * (1 + strength)
            else:
                noise_floor = 0.01  # 默认阈值
            
            # 应用频谱门
            gate_mask = magnitude > noise_floor
            magnitude_filtered = magnitude * gate_mask
            
            # 平滑处理避免失真
            magnitude_filtered = scipy.signal.savgol_filter(
                magnitude_filtered, 5, 2, axis=0
            )
            
            # 重构复数频谱
            stft_filtered = magnitude_filtered * np.exp(1j * phase)
            
            # 逆变换回时域
            _, audio_denoised = scipy.signal.istft(stft_filtered, self.sample_rate)
            
            return audio_denoised.astype(np.float32)
            
        except Exception as e:
            self.logger.error(f"降噪处理失败: {e}")
            return audio_data  # 降噪失败时返回原始数据

class VolumeNormalizer:
    """音量归一化器"""
    
    def __init__(self):
        self.target_rms = 0.1  # 目标RMS值
        self.logger = logging.getLogger(__name__)
        
    def normalize_volume(self, audio_data: np.ndarray, 
                        target_level: float = 0.7) -> Tuple[np.ndarray, float]:
        """音量归一化
        
        Args:
            audio_data: 输入音频数据
            target_level: 目标音量级别 (0.0-1.0)
            
        Returns:
            (归一化后的音频, 增益系数)
        """
        try:
            # 计算RMS (Root Mean Square)
            rms = np.sqrt(np.mean(audio_data ** 2))
            
            if rms < 1e-6:  # 避免除零错误
                return audio_data, 1.0
            
            # 计算目标RMS
            target_rms = target_level * 0.15  # 调整到合适的RMS范围
            
            # 计算增益
            gain = target_rms / rms
            
            # 限制增益范围，避免过度放大
            gain = np.clip(gain, 0.1, 10.0)
            
            # 应用增益
            normalized_audio = audio_data * gain
            
            # 限制幅度范围，避免削峰
            normalized_audio = np.clip(normalized_audio, -1.0, 1.0)
            
            return normalized_audio.astype(np.float32), gain
            
        except Exception as e:
            self.logger.error(f"音量归一化失败: {e}")
            return audio_data, 1.0

class SilenceDetector:
    """静音检测器"""
    
    def __init__(self, threshold: float = 0.01, min_duration: float = 0.1):
        self.threshold = threshold
        self.min_duration = min_duration
        self.logger = logging.getLogger(__name__)
        
    def detect_silence_segments(self, audio_data: np.ndarray, 
                               sample_rate: int) -> List[Tuple[float, float]]:
        """检测静音段
        
        Args:
            audio_data: 音频数据
            sample_rate: 采样率
            
        Returns:
            静音段列表 [(开始时间, 结束时间), ...]
        """
        try:
            # 计算短时能量
            frame_length = int(0.025 * sample_rate)  # 25ms帧
            hop_length = int(0.01 * sample_rate)     # 10ms步长
            
            energy = []
            for i in range(0, len(audio_data) - frame_length, hop_length):
                frame = audio_data[i:i+frame_length]
                frame_energy = np.sum(frame ** 2) / len(frame)
                energy.append(frame_energy)
            
            energy = np.array(energy)
            
            # 检测低于阈值的帧
            silence_frames = energy < self.threshold
            
            # 找到连续的静音段
            silence_segments = []
            in_silence = False
            start_frame = 0
            
            for i, is_silent in enumerate(silence_frames):
                if is_silent and not in_silence:
                    # 静音开始
                    start_frame = i
                    in_silence = True
                elif not is_silent and in_silence:
                    # 静音结束
                    duration = (i - start_frame) * hop_length / sample_rate
                    if duration >= self.min_duration:
                        start_time = start_frame * hop_length / sample_rate
                        end_time = i * hop_length / sample_rate
                        silence_segments.append((start_time, end_time))
                    in_silence = False
            
            return silence_segments
            
        except Exception as e:
            self.logger.error(f"静音检测失败: {e}")
            return []

class AudioQualityMonitor:
    """音频质量监测器"""
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.quality_history = []
        self.logger = logging.getLogger(__name__)
        
    def assess_quality(self, audio_data: np.ndarray, 
                      sample_rate: int) -> AudioQuality:
        """评估音频质量
        
        Args:
            audio_data: 音频数据
            sample_rate: 采样率
            
        Returns:
            音频质量评估结果
        """
        try:
            # 1. 计算噪音水平 (基于高频能量)
            noise_level = self._calculate_noise_level(audio_data, sample_rate)
            
            # 2. 计算音量水平 (RMS)
            rms = np.sqrt(np.mean(audio_data ** 2))
            volume_level = min(rms * 10, 1.0)  # 归一化到0-1
            
            # 3. 计算清晰度评分 (基于谱平坦度)
            clarity_score = self._calculate_spectral_clarity(audio_data, sample_rate)
            
            # 4. 计算信噪比
            snr_db = self._calculate_snr(audio_data)
            
            quality = AudioQuality(
                noise_level=noise_level,
                volume_level=volume_level,
                clarity_score=clarity_score,
                sample_rate=sample_rate,
                snr_db=snr_db
            )
            
            # 更新历史记录
            self.quality_history.append(quality)
            if len(self.quality_history) > self.window_size:
                self.quality_history.pop(0)
            
            return quality
            
        except Exception as e:
            self.logger.error(f"音频质量评估失败: {e}")
            return AudioQuality(0.5, 0.5, 0.5, sample_rate)
    
    def _calculate_noise_level(self, audio_data: np.ndarray, 
                              sample_rate: int) -> float:
        """计算噪音水平"""
        try:
            # 使用高频部分估计噪音
            nyquist = sample_rate / 2
            high_freq_cutoff = 0.8 * nyquist
            
            # 高通滤波器
            sos = scipy.signal.butter(4, high_freq_cutoff / nyquist, 
                                     btype='high', output='sos')
            high_freq_signal = scipy.signal.sosfilt(sos, audio_data)
            
            # 计算高频部分的能量作为噪音指标
            noise_energy = np.mean(np.power(high_freq_signal, 2))
            noise_level = min(np.sqrt(noise_energy) * 5, 1.0)
            
            return noise_level
            
        except Exception:
            return 0.5  # 默认中等噪音水平
    
    def _calculate_spectral_clarity(self, audio_data: np.ndarray, 
                                   sample_rate: int) -> float:
        """计算频谱清晰度"""
        try:
            # 计算功率谱密度
            f, psd = scipy.signal.welch(audio_data, sample_rate, nperseg=1024)
            
            # 计算谱平坦度 (Spectral Flatness)
            geometric_mean = scipy.stats.gmean(psd + 1e-10)
            arithmetic_mean = np.mean(psd)
            
            spectral_flatness = geometric_mean / (arithmetic_mean + 1e-10)
            
            # 转换为清晰度分数 (谱平坦度越低，清晰度越高)
            clarity_score = 1.0 - spectral_flatness
            
            return np.clip(clarity_score, 0.0, 1.0)
            
        except Exception:
            return 0.5  # 默认中等清晰度
    
    def _calculate_snr(self, audio_data: np.ndarray) -> float:
        """计算信噪比"""
        try:
            # 简单的SNR估计：基于信号幅度分布
            sorted_samples = np.sort(np.abs(audio_data))
            
            # 假设前10%为噪音，后10%为信号
            noise_level = np.mean(sorted_samples[:len(sorted_samples)//10])
            signal_level = np.mean(sorted_samples[-len(sorted_samples)//10:])
            
            if noise_level < 1e-6:
                return 40.0  # 很高的SNR
            
            snr_linear = signal_level / noise_level
            snr_db = 20 * np.log10(snr_linear + 1e-10)
            
            return np.clip(snr_db, -10.0, 40.0)
            
        except Exception:
            return 15.0  # 默认合理的SNR

    def get_average_quality(self) -> Optional[AudioQuality]:
        """获取平均音频质量"""
        if not self.quality_history:
            return None
        
        avg_noise = np.mean([q.noise_level for q in self.quality_history])
        avg_volume = np.mean([q.volume_level for q in self.quality_history])  
        avg_clarity = np.mean([q.clarity_score for q in self.quality_history])
        avg_snr = np.mean([q.snr_db for q in self.quality_history if q.snr_db])
        
        return AudioQuality(
            noise_level=float(avg_noise),
            volume_level=float(avg_volume),
            clarity_score=float(avg_clarity),
            sample_rate=self.quality_history[0].sample_rate,
            snr_db=float(avg_snr)
        )

class AudioPreprocessorEnhanced:
    """增强版音频预处理器
    
    整合降噪、归一化、静音检测和质量监测功能
    """
    
    def __init__(self, config: Optional[AudioProcessingConfig] = None):
        self.config = config or AudioProcessingConfig()
        
        # 初始化组件
        self.noise_reducer = SpectralGateDenoiser(self.config.sample_rate)
        self.volume_normalizer = VolumeNormalizer()
        self.silence_detector = SilenceDetector(self.config.silence_threshold)
        self.quality_monitor = AudioQualityMonitor(self.config.quality_window_size)
        
        # 统计信息
        self.processing_stats = {
            "total_chunks_processed": 0,
            "total_processing_time": 0.0,
            "average_noise_reduction": 0.0,
            "average_volume_gain": 0.0
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("增强版音频预处理器已初始化")
    
    def process_audio_chunk(self, audio_data: bytes) -> Tuple[bytes, AudioQuality]:
        """处理音频块并返回质量指标
        
        Args:
            audio_data: 原始音频字节数据
            
        Returns:
            (处理后的音频字节数据, 音频质量评估)
        """
        start_time = time.time()
        
        try:
            # 1. 转换为numpy数组
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # 2. 音频质量评估 (在处理前)
            quality = self.quality_monitor.assess_quality(audio_array, self.config.sample_rate)
            
            # 3. 根据质量决定处理策略
            processed_audio = audio_array
            
            # 3.1 自适应降噪
            if quality.noise_level > 0.3:  # 噪音较高时启用降噪
                noise_strength = min(quality.noise_level * self.config.noise_reduction_strength, 0.8)
                processed_audio = self.noise_reducer.reduce_noise(processed_audio, noise_strength)
            
            # 3.2 音量归一化
            if quality.volume_level < 0.3 or quality.volume_level > 0.9:  # 音量异常时归一化
                processed_audio, gain = self.volume_normalizer.normalize_volume(
                    processed_audio, self.config.volume_target
                )
                self.processing_stats["average_volume_gain"] = (
                    self.processing_stats["average_volume_gain"] * 0.9 + gain * 0.1
                )
            
            # 4. 转换回字节格式
            processed_int16 = (processed_audio * 32767).astype(np.int16)
            processed_bytes = processed_int16.tobytes()
            
            # 5. 更新统计信息
            processing_time = time.time() - start_time
            self.processing_stats["total_chunks_processed"] += 1
            self.processing_stats["total_processing_time"] += processing_time
            
            return processed_bytes, quality
            
        except Exception as e:
            self.logger.error(f"音频处理失败: {e}")
            # 处理失败时返回原始数据和默认质量评估
            default_quality = AudioQuality(0.5, 0.5, 0.5, self.config.sample_rate)
            return audio_data, default_quality
    
    def adaptive_noise_reduction(self, audio_data: bytes, noise_level: float) -> bytes:
        """自适应降噪处理
        
        Args:
            audio_data: 音频数据
            noise_level: 噪音水平 (0.0-1.0)
            
        Returns:
            降噪后的音频数据
        """
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # 根据噪音水平调整降噪强度
            strength = min(noise_level * 1.5, 0.9)
            denoised_audio = self.noise_reducer.reduce_noise(audio_array, strength)
            
            # 转换回字节格式
            denoised_int16 = (denoised_audio * 32767).astype(np.int16)
            return denoised_int16.tobytes()
            
        except Exception as e:
            self.logger.error(f"自适应降噪失败: {e}")
            return audio_data
    
    def normalize_volume(self, audio_data: bytes) -> bytes:
        """音量归一化
        
        Args:
            audio_data: 音频数据
            
        Returns:
            归一化后的音频数据
        """
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            normalized_audio, _ = self.volume_normalizer.normalize_volume(
                audio_array, self.config.volume_target
            )
            
            # 转换回字节格式
            normalized_int16 = (normalized_audio * 32767).astype(np.int16)
            return normalized_int16.tobytes()
            
        except Exception as e:
            self.logger.error(f"音量归一化失败: {e}")
            return audio_data
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        stats = self.processing_stats.copy()
        
        # 计算平均处理时间
        if stats["total_chunks_processed"] > 0:
            stats["average_processing_time"] = (
                stats["total_processing_time"] / stats["total_chunks_processed"]
            )
        else:
            stats["average_processing_time"] = 0.0
        
        # 添加质量监测统计
        avg_quality = self.quality_monitor.get_average_quality()
        if avg_quality:
            stats["average_quality"] = {
                "noise_level": avg_quality.noise_level,
                "volume_level": avg_quality.volume_level,
                "clarity_score": avg_quality.clarity_score,
                "snr_db": avg_quality.snr_db
            }
        
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        self.processing_stats = {
            "total_chunks_processed": 0,
            "total_processing_time": 0.0,
            "average_noise_reduction": 0.0,
            "average_volume_gain": 0.0
        }
        self.quality_monitor.quality_history.clear()
        self.logger.info("处理统计信息已重置")

# 为向后兼容创建别名
AudioProcessorConfig = AudioProcessingConfig

# 导出主要类
__all__ = [
    'AudioPreprocessorEnhanced',
    'AudioProcessingConfig',
    'AudioProcessorConfig',  # 别名
    'AudioQuality',
    'SpectralGateDenoiser',
    'VolumeNormalizer', 
    'SilenceDetector',
    'AudioQualityMonitor'
]