#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频增强功能测试
测试音频处理和增强功能的效果（不依赖VOSK库）

功能:
1. 加载和分析真实音频文件
2. 测试音频增强算法
3. 生成音频质量分析报告
4. 导出增强前后的音频文件进行对比

依赖:
pip install numpy scipy pydub matplotlib
"""

import sys
import os
import json
import time
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from pydub import AudioSegment
    import scipy.signal
    import scipy.stats
    print("✅ 所有依赖导入成功")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请安装所需依赖: pip install numpy scipy pydub")
    print("注意: 您可能还需要安装ffmpeg来处理音频文件")
    sys.exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioEnhancementTester:
    """音频增强测试器"""
    
    def __init__(self, sample_rate: int = 16000):
        """
        初始化测试器
        
        Args:
            sample_rate: 采样率
        """
        self.sample_rate = sample_rate
        self.logger = logging.getLogger(__name__)
        
        # 初始化音频增强器参数
        self._initialize_enhancer()
        
        # 测试结果
        self.test_results = {
            "original": {
                "rms_level": 0.0,
                "peak_level": 0.0,
                "dynamic_range": 0.0,
                "noise_floor": 0.0,
                "snr_estimate": 0.0
            },
            "enhanced": {
                "rms_level": 0.0,
                "peak_level": 0.0,
                "dynamic_range": 0.0,
                "noise_floor": 0.0,
                "snr_estimate": 0.0
            }
        }
    
    def _initialize_enhancer(self):
        """初始化音频增强器参数"""
        # 降噪滤波器参数
        self.noise_gate_threshold = 0.01
        self.noise_reduction_factor = 0.3
        
        # 麦克风增强参数
        self.auto_gain_target = 0.7
        self.compressor_ratio = 3.0
        self.compressor_threshold = 0.5
        
        # 高通滤波器 - 去除低频噪声
        self.highpass_cutoff = 80  # Hz
        nyquist = self.sample_rate / 2
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
        
        self.logger.info("音频增强器参数初始化完成")
    
    def load_and_convert_audio(self, audio_path: str) -> np.ndarray:
        """
        加载并转换音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            音频数据数组
        """
        logger.info(f"正在加载音频文件: {audio_path}")
        
        try:
            # 加载音频文件
            audio = AudioSegment.from_file(audio_path)
            
            # 转换为单声道，指定采样率
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(self.sample_rate)
            audio = audio.set_sample_width(2)  # 16-bit
            
            # 转换为numpy数组
            audio_array = np.array(audio.get_array_of_samples(), dtype=np.float32)
            audio_array = audio_array / 32768.0  # 归一化到[-1, 1]
            
            logger.info(f"✅ 音频加载完成: {len(audio_array)} 采样点, {len(audio_array)/self.sample_rate:.2f}秒")
            return audio_array
            
        except Exception as e:
            logger.error(f"❌ 音频加载失败: {e}")
            raise
    
    def analyze_audio_quality(self, audio: np.ndarray, label: str = "") -> Dict:
        """
        分析音频质量
        
        Args:
            audio: 音频数据
            label: 标签
            
        Returns:
            质量分析结果
        """
        logger.info(f"分析音频质量: {label}")
        
        # RMS电平
        rms_level = np.sqrt(np.mean(audio ** 2))
        
        # 峰值电平
        peak_level = np.max(np.abs(audio))
        
        # 动态范围
        dynamic_range = peak_level - rms_level
        
        # 估算噪声底噪（最小的10%样本的RMS）
        sorted_abs = np.sort(np.abs(audio))
        noise_floor = np.sqrt(np.mean(sorted_abs[:len(sorted_abs)//10] ** 2))
        
        # 估算信噪比
        signal_power = rms_level ** 2
        noise_power = noise_floor ** 2
        snr_estimate = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else float('inf')
        
        result = {
            "rms_level": rms_level,
            "peak_level": peak_level,
            "dynamic_range": dynamic_range,
            "noise_floor": noise_floor,
            "snr_estimate": snr_estimate
        }
        
        logger.info(f"  RMS电平: {rms_level:.4f}")
        logger.info(f"  峰值电平: {peak_level:.4f}")
        logger.info(f"  动态范围: {dynamic_range:.4f}")
        logger.info(f"  噪声底噪: {noise_floor:.4f}")
        logger.info(f"  估算SNR: {snr_estimate:.2f} dB")
        
        return result
    
    def enhance_audio(self, audio: np.ndarray) -> np.ndarray:
        """
        音频增强处理
        
        Args:
            audio: 原始音频数据
            
        Returns:
            增强后的音频数据
        """
        logger.info("开始音频增强处理...")
        
        try:
            # 1. 高通滤波 - 去除低频噪声
            logger.info("  1. 高通滤波")
            audio_filtered = scipy.signal.sosfilt(self.highpass_sos, audio)
            
            # 2. 自适应降噪
            logger.info("  2. 自适应降噪")
            # 确保audio_filtered是正确的numpy数组
            if isinstance(audio_filtered, tuple):
                audio_filtered = audio_filtered[0] if len(audio_filtered) > 0 else np.array([])
            audio_filtered = np.asarray(audio_filtered, dtype=np.float32)
            audio_denoised = self._adaptive_noise_gate(audio_filtered)
            
            # 3. 人声增强 - 带通滤波突出人声频段
            logger.info("  3. 人声频段增强")
            # 确保audio_denoised是正确的numpy数组
            if isinstance(audio_denoised, tuple):
                audio_denoised = audio_denoised[0] if len(audio_denoised) > 0 else np.array([])
            audio_denoised = np.asarray(audio_denoised, dtype=np.float32)
            audio_voice_enhanced = scipy.signal.sosfilt(self.voice_sos, audio_denoised)
            
            # 4. 自动增益控制
            logger.info("  4. 自动增益控制")
            # 确保audio_voice_enhanced是正确的numpy数组
            if isinstance(audio_voice_enhanced, tuple):
                audio_voice_enhanced = audio_voice_enhanced[0] if len(audio_voice_enhanced) > 0 else np.array([])
            audio_voice_enhanced = np.asarray(audio_voice_enhanced, dtype=np.float32)
            audio_gained = self._auto_gain_control(audio_voice_enhanced)
            
            # 5. 动态压缩
            logger.info("  5. 动态压缩")
            audio_compressed = self._dynamic_compressor(audio_gained)
            
            logger.info("✅ 音频增强处理完成")
            return audio_compressed
            
        except Exception as e:
            logger.error(f"❌ 音频增强失败: {e}")
            return audio  # 失败时返回原始数据
    
    def _adaptive_noise_gate(self, audio: np.ndarray) -> np.ndarray:
        """自适应噪声门"""
        # 计算短时能量
        frame_length = int(0.025 * self.sample_rate)  # 25ms
        hop_length = int(0.01 * self.sample_rate)     # 10ms
        
        energy = []
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i:i+frame_length]
            frame_energy = float(np.mean(frame ** 2))
            energy.append(frame_energy)
        
        if not energy:
            return audio
            
        # 动态阈值 - 基于能量分布的百分位数
        threshold = float(np.percentile(energy, 30)) * 2
        threshold = max(float(threshold), float(self.noise_gate_threshold))
        
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
        # 计算RMS电平
        rms = np.sqrt(np.mean(audio ** 2))
        
        if rms < 1e-6:  # 避免除零
            return audio
        
        # 计算所需增益
        target_rms = self.auto_gain_target * 0.1
        gain = target_rms / rms
        
        # 限制增益范围
        gain = np.clip(gain, 0.1, 10.0)
        
        return audio * gain
    
    def _dynamic_compressor(self, audio: np.ndarray) -> np.ndarray:
        """动态压缩器"""
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
    
    def save_audio(self, audio: np.ndarray, filepath: str):
        """保存音频文件"""
        try:
            # 转换回int16格式
            audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
            
            # 创建AudioSegment
            audio_segment = AudioSegment(
                audio_int16.tobytes(),
                frame_rate=self.sample_rate,
                sample_width=2,
                channels=1
            )
            
            # 导出为WAV文件
            audio_segment.export(filepath, format="wav")
            logger.info(f"✅ 音频已保存: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ 音频保存失败: {e}")
    
    def test_audio_file(self, audio_path: str) -> Dict:
        """
        测试音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            测试结果
        """
        logger.info(f"开始测试音频文件: {audio_path}")
        
        if not Path(audio_path).exists():
            logger.error(f"音频文件不存在: {audio_path}")
            return {}
        
        # 加载音频
        try:
            original_audio = self.load_and_convert_audio(audio_path)
        except Exception as e:
            logger.error(f"音频加载失败: {e}")
            return {}
        
        # 分析原始音频
        logger.info("\n" + "="*50)
        logger.info("🔍 分析原始音频")
        logger.info("="*50)
        
        self.test_results["original"] = self.analyze_audio_quality(original_audio, "原始音频")
        
        # 增强音频
        logger.info("\n" + "="*50)
        logger.info("🚀 音频增强处理")
        logger.info("="*50)
        
        enhanced_audio = self.enhance_audio(original_audio)
        
        # 分析增强后音频
        logger.info("\n" + "="*50)
        logger.info("📊 分析增强后音频")
        logger.info("="*50)
        
        self.test_results["enhanced"] = self.analyze_audio_quality(enhanced_audio, "增强音频")
        
        # 保存音频文件
        output_dir = Path(audio_path).parent / "enhanced_audio_output"
        output_dir.mkdir(exist_ok=True)
        
        original_output = output_dir / f"{Path(audio_path).stem}_original.wav"
        enhanced_output = output_dir / f"{Path(audio_path).stem}_enhanced.wav"
        
        self.save_audio(original_audio, str(original_output))
        self.save_audio(enhanced_audio, str(enhanced_output))
        
        return self.test_results
    
    def generate_report(self) -> str:
        """生成测试报告"""
        report = []
        report.append("🎙️ 音频增强功能测试报告")
        report.append("=" * 60)
        
        # 测试参数信息
        report.append("\n⚙️ 测试参数:")
        report.append(f"  采样率: {self.sample_rate}Hz")
        report.append(f"  高通滤波截止频率: {self.highpass_cutoff}Hz")
        report.append(f"  人声频段: {self.voice_lowcut}-{self.voice_highcut}Hz")
        report.append(f"  噪声门阈值: {self.noise_gate_threshold}")
        report.append(f"  降噪因子: {self.noise_reduction_factor}")
        report.append(f"  自动增益目标: {self.auto_gain_target}")
        
        # 原始音频分析
        orig = self.test_results["original"]
        report.append("\n🔍 原始音频分析:")
        report.append(f"  RMS电平: {orig.get('rms_level', 0):.4f}")
        report.append(f"  峰值电平: {orig.get('peak_level', 0):.4f}")
        report.append(f"  动态范围: {orig.get('dynamic_range', 0):.4f}")
        report.append(f"  噪声底噪: {orig.get('noise_floor', 0):.4f}")
        report.append(f"  估算SNR: {orig.get('snr_estimate', 0):.2f} dB")
        
        # 增强后音频分析
        enh = self.test_results["enhanced"]
        report.append("\n🚀 增强后音频分析:")
        report.append(f"  RMS电平: {enh.get('rms_level', 0):.4f}")
        report.append(f"  峰值电平: {enh.get('peak_level', 0):.4f}")
        report.append(f"  动态范围: {enh.get('dynamic_range', 0):.4f}")
        report.append(f"  噪声底噪: {enh.get('noise_floor', 0):.4f}")
        report.append(f"  估算SNR: {enh.get('snr_estimate', 0):.2f} dB")
        
        # 改进分析
        report.append("\n📊 增强效果分析:")
        
        # RMS电平变化
        rms_change = enh.get('rms_level', 0) - orig.get('rms_level', 0)
        rms_percent = (rms_change / orig.get('rms_level', 1)) * 100 if orig.get('rms_level', 0) > 0 else 0
        report.append(f"  RMS电平变化: {rms_change:+.4f} ({rms_percent:+.1f}%)")
        
        # 峰值电平变化
        peak_change = enh.get('peak_level', 0) - orig.get('peak_level', 0)
        peak_percent = (peak_change / orig.get('peak_level', 1)) * 100 if orig.get('peak_level', 0) > 0 else 0
        report.append(f"  峰值电平变化: {peak_change:+.4f} ({peak_percent:+.1f}%)")
        
        # 动态范围变化
        dr_change = enh.get('dynamic_range', 0) - orig.get('dynamic_range', 0)
        report.append(f"  动态范围变化: {dr_change:+.4f}")
        
        # 噪声底噪变化
        noise_change = enh.get('noise_floor', 0) - orig.get('noise_floor', 0)
        noise_percent = (noise_change / orig.get('noise_floor', 1)) * 100 if orig.get('noise_floor', 0) > 0 else 0
        report.append(f"  噪声底噪变化: {noise_change:+.4f} ({noise_percent:+.1f}%)")
        
        # SNR改进
        snr_improvement = enh.get('snr_estimate', 0) - orig.get('snr_estimate', 0)
        report.append(f"  SNR改进: {snr_improvement:+.2f} dB")
        
        # 总体评估
        report.append("\n✨ 总体评估:")
        if snr_improvement > 0:
            report.append("  ✅ SNR有所改善")
        else:
            report.append("  ⚠️ SNR未见明显改善")
        
        if noise_percent < -10:
            report.append("  ✅ 噪声显著降低")
        elif noise_percent < 0:
            report.append("  ✅ 噪声有所降低")
        else:
            report.append("  ⚠️ 噪声未见明显降低")
        
        if abs(rms_percent) > 5:
            report.append("  ✅ 音频电平得到调整")
        else:
            report.append("  ℹ️ 音频电平变化较小")
        
        report.append("\n" + "=" * 60)
        return "\n".join(report)
    
    def save_report(self, filepath: str):
        """保存测试报告到文件"""
        report = self.generate_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"📄 测试报告已保存: {filepath}")


def main():
    """主函数"""
    print("🎙️ 音频增强功能真实测试")
    print("=" * 50)
    
    # 查找测试音频文件
    test_audio_path = Path(__file__).parent / "tests" / "录音 (12).m4a"
    
    if not test_audio_path.exists():
        print(f"❌ 找不到测试音频文件: {test_audio_path}")
        print("请确保tests文件夹中有音频文件")
        return
    
    print(f"📁 测试音频文件: {test_audio_path}")
    
    # 创建测试器
    try:
        tester = AudioEnhancementTester()
        
        # 执行测试
        results = tester.test_audio_file(str(test_audio_path))
        
        if results:
            # 显示报告
            report = tester.generate_report()
            print("\n" + report)
            
            # 保存报告
            report_path = Path(__file__).parent / "audio_enhancement_test_report.txt"
            tester.save_report(str(report_path))
            
            print(f"\n✅ 测试完成！")
            print(f"📄 报告已保存至: {report_path}")
            print(f"🎵 音频文件已保存至: {Path(test_audio_path).parent / 'enhanced_audio_output'}")
        else:
            print("❌ 测试失败")
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print("❌ 测试失败，请检查错误日志")


if __name__ == "__main__":
    main()