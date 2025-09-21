#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频增强模块 - 提供降噪和麦克风增强功能
"""

import numpy as np
import logging
from typing import Union

# 音频预处理相关导入
try:
    import scipy.signal
    import scipy.stats
    scipy = scipy  # 为了满足类型检查器
    AUDIO_ENHANCEMENT_AVAILABLE = True
except ImportError:
    scipy = None
    AUDIO_ENHANCEMENT_AVAILABLE = False
    logging.warning("Audio enhancement dependencies not available. Install scipy for enhanced audio processing.")

class AudioEnhancer:
    """音频增强器 - 提供降噪和麦克风增强功能"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.logger = logging.getLogger(__name__)
        
        if not AUDIO_ENHANCEMENT_AVAILABLE:
            self.logger.warning("音频增强功能不可用，需要安装scipy库")
            self.enabled = False
        else:
            self.enabled = True
            self._initialize_enhancer()
    
    def _initialize_enhancer(self):
        """初始化音频增强器"""
        if not self.enabled:
            return
            
        # 降噪滤波器参数
        self.noise_gate_threshold = 0.01  # 噪声门阈值
        self.noise_reduction_factor = 0.3  # 降噪因子
        
        # 麦克风增强参数
        self.auto_gain_target = 0.7  # 自动增益目标电平
        self.compressor_ratio = 3.0   # 压缩比
        self.compressor_threshold = 0.5  # 压缩阈值
        
        # 高通滤波器 - 去除低频噪声
        self.highpass_cutoff = 80  # Hz
        nyquist = self.sample_rate / 2
        if AUDIO_ENHANCEMENT_AVAILABLE and scipy is not None:
            self.highpass_sos = scipy.signal.butter(
                4, self.highpass_cutoff / nyquist, btype='high', output='sos'
            )
            
            # 带通滤波器 - 突出人声频段 (300-3400 Hz)
            self.voice_lowcut = 300
            self.voice_highcut = 3400
            self.voice_sos = scipy.signal.butter(
                2, [self.voice_lowcut / nyquist, self.voice_highcut / nyquist], 
                btype='band', output='sos'
            )
        
        self.logger.info("音频增强器初始化完成")
    
    def enhance_audio(self, audio_data: bytes) -> bytes:
        """增强音频数据
        
        Args:
            audio_data: 原始音频字节数据 (int16格式)
            
        Returns:
            增强后的音频字节数据
        """
        if not self.enabled:
            return audio_data
            
        try:
            # 转换为float数组
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
            audio_array = audio_array / 32768.0  # 归一化到[-1, 1]
            
            # 1. 高通滤波 - 去除低频噪声
            if AUDIO_ENHANCEMENT_AVAILABLE and scipy is not None:
                audio_filtered = scipy.signal.sosfilt(self.highpass_sos, audio_array)
            else:
                audio_filtered = audio_array
            
            # 2. 自适应降噪
            # 确保audio是正确的numpy数组
            if isinstance(audio_filtered, tuple):
                audio_filtered = audio_filtered[0] if len(audio_filtered) > 0 else np.array([])
            audio_filtered = np.asarray(audio_filtered, dtype=np.float32)
            
            audio_denoised = self._adaptive_noise_gate(audio_filtered)
            
            # 3. 人声增强 - 带通滤波突出人声频段
            if AUDIO_ENHANCEMENT_AVAILABLE and scipy is not None:
                audio_voice_enhanced = scipy.signal.sosfilt(self.voice_sos, audio_denoised)
            else:
                audio_voice_enhanced = audio_denoised
            
            # 4. 自动增益控制
            # 确保audio_voice_enhanced是正确的numpy数组
            if isinstance(audio_voice_enhanced, tuple):
                audio_voice_enhanced = audio_voice_enhanced[0] if len(audio_voice_enhanced) > 0 else np.array([])
            audio_voice_enhanced = np.asarray(audio_voice_enhanced, dtype=np.float32)
            
            audio_gained = self._auto_gain_control(audio_voice_enhanced)
            
            # 5. 动态压缩
            audio_compressed = self._dynamic_compressor(audio_gained)
            
            # 转换回int16格式
            audio_enhanced = np.clip(audio_compressed * 32767, -32768, 32767).astype(np.int16)
            
            return audio_enhanced.tobytes()
            
        except Exception as e:
            self.logger.error(f"音频增强失败: {e}")
            return audio_data  # 失败时返回原始数据
    
    def _adaptive_noise_gate(self, audio: np.ndarray) -> np.ndarray:
        """自适应噪声门"""
        # 确保scipy可用
        if scipy is None:
            return audio
            
        # 计算短时能量
        frame_length = int(0.025 * self.sample_rate)  # 25ms
        hop_length = int(0.01 * self.sample_rate)     # 10ms
        
        energy = []
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i:i+frame_length]
            frame_energy = np.mean(frame ** 2)
            energy.append(frame_energy)
        
        if not energy:
            return audio
            
        # 动态阈值 - 基于能量分布的百分位数
        threshold = np.percentile(energy, 30) * 2  # 使用30%分位数的2倍作为阈值
        threshold = max(float(threshold), self.noise_gate_threshold)  # 确保不低于最小阈值
        
        # 应用噪声门
        output = audio.copy()
        frame_idx = 0
        for i in range(0, len(audio) - frame_length, hop_length):
            if frame_idx < len(energy):
                if energy[frame_idx] < threshold:
                    # 在低能量段应用降噪
                    output[i:i+frame_length] *= (1 - self.noise_reduction_factor)
                frame_idx += 1
        
        return output
    
    def _auto_gain_control(self, audio: np.ndarray) -> np.ndarray:
        """自动增益控制"""
        # 计算RMS电平并确保类型兼容性
        rms = float(np.sqrt(np.mean(audio ** 2)))
        
        if rms < 1e-6:  # 避免除零
            return audio
        
        # 计算所需增益
        target_rms = float(self.auto_gain_target * 0.1)  # 调整到合适的RMS范围
        gain = target_rms / rms
        
        # 限制增益范围
        gain = float(np.clip(gain, 0.1, 10.0))
        
        return audio * gain
    
    def _dynamic_compressor(self, audio: np.ndarray) -> np.ndarray:
        """动态压缩器"""
        # 简化的压缩器实现
        threshold = self.compressor_threshold
        ratio = self.compressor_ratio
        
        # 计算瞬时幅度
        amplitude = np.abs(audio)
        
        # 应用压缩
        compressed_amplitude = np.where(
            amplitude > threshold,
            threshold + (amplitude - threshold) / ratio,
            amplitude
        )
        
        # 保持原始符号
        compressed_audio = np.sign(audio) * compressed_amplitude
        
        return compressed_audio
    
    def set_noise_reduction(self, strength: float):
        """设置降噪强度
        
        Args:
            strength: 降噪强度 (0.0-1.0)
        """
        self.noise_reduction_factor = np.clip(strength, 0.0, 1.0)
        self.logger.info(f"降噪强度已设置为: {self.noise_reduction_factor:.2f}")
    
    def set_gain_target(self, target: float):
        """设置自动增益目标
        
        Args:
            target: 目标电平 (0.0-1.0)
        """
        self.auto_gain_target = np.clip(target, 0.1, 1.0)
        self.logger.info(f"自动增益目标已设置为: {self.auto_gain_target:.2f}")

class EnhancedKaldiRecognizer:
    """增强版Kaldi识别器包装器 - 集成音频降噪和麦克风增强功能"""
    
    def __init__(self, recognizer, enable_audio_enhancement: bool = True, 
                 noise_reduction_strength: float = 0.5,
                 gain_target: float = 0.7):
        """
        初始化增强版识别器包装器
        
        Args:
            recognizer: 原始的KaldiRecognizer实例
            enable_audio_enhancement: 是否启用音频增强
            noise_reduction_strength: 降噪强度 (0.0-1.0)
            gain_target: 自动增益目标 (0.0-1.0)
        """
        self.recognizer = recognizer
        self.logger = logging.getLogger(__name__)
        
        # 初始化音频增强器
        if enable_audio_enhancement:
            self.audio_enhancer = AudioEnhancer()
            self.audio_enhancer.set_noise_reduction(noise_reduction_strength)
            self.audio_enhancer.set_gain_target(gain_target)
            self.enhancement_enabled = self.audio_enhancer.enabled
        else:
            self.audio_enhancer = None
            self.enhancement_enabled = False
        
        # 统计信息
        self.enhancement_stats = {
            "processed_chunks": 0,
            "enhancement_time": 0.0,
            "enhancement_enabled": self.enhancement_enabled
        }
        
        if self.enhancement_enabled:
            self.logger.info("增强版Kaldi识别器已启用音频增强功能")
        else:
            self.logger.info("增强版Kaldi识别器已初始化（音频增强功能未启用）")
    
    def AcceptWaveform(self, data: Union[bytes, memoryview]) -> int:
        """接受音频数据（带音频增强）
        
        Args:
            data: 音频数据
            
        Returns:
            识别结果状态
        """
        # 如果启用了音频增强，先处理音频
        if self.enhancement_enabled and self.audio_enhancer:
            import time
            start_time = time.time()
            
            # 转换为bytes如果是memoryview
            if isinstance(data, memoryview):
                data = data.tobytes()
            
            # 应用音频增强
            enhanced_data = self.audio_enhancer.enhance_audio(data)
            
            # 更新统计信息
            self.enhancement_stats["processed_chunks"] += 1
            self.enhancement_stats["enhancement_time"] += (time.time() - start_time)
            
            # 使用增强后的数据
            data = enhanced_data
        
        # 调用原始识别器方法
        return self.recognizer.AcceptWaveform(data)
    
    def SetNoiseReduction(self, strength: float):
        """设置降噪强度
        
        Args:
            strength: 降噪强度 (0.0-1.0)
        """
        if self.audio_enhancer:
            self.audio_enhancer.set_noise_reduction(strength)
        else:
            self.logger.warning("音频增强器未启用，无法设置降噪强度")
    
    def SetGainTarget(self, target: float):
        """设置自动增益目标
        
        Args:
            target: 目标电平 (0.0-1.0)
        """
        if self.audio_enhancer:
            self.audio_enhancer.set_gain_target(target)
        else:
            self.logger.warning("音频增强器未启用，无法设置增益目标")
    
    def EnableAudioEnhancement(self, enable: bool = True):
        """启用或禁用音频增强
        
        Args:
            enable: 是否启用
        """
        if self.audio_enhancer and self.audio_enhancer.enabled:
            self.enhancement_enabled = enable
            status = "启用" if enable else "禁用"
            self.logger.info(f"音频增强功能已{status}")
        else:
            self.logger.warning("音频增强器不可用")
    
    def GetEnhancementStats(self) -> dict:
        """获取音频增强统计信息
        
        Returns:
            统计信息字典
        """
        stats = self.enhancement_stats.copy()
        
        if stats["processed_chunks"] > 0:
            stats["average_enhancement_time"] = (
                stats["enhancement_time"] / stats["processed_chunks"]
            )
        else:
            stats["average_enhancement_time"] = 0.0
        
        return stats
    
    def ResetEnhancementStats(self):
        """重置音频增强统计信息"""
        self.enhancement_stats["processed_chunks"] = 0
        self.enhancement_stats["enhancement_time"] = 0.0
        self.logger.info("音频增强统计信息已重置")
    
    # 代理所有其他方法到原始识别器
    def __getattr__(self, name):
        # 如果这个类没有该属性，则从原始识别器获取
        return getattr(self.recognizer, name)