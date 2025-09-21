#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频增强功能演示脚本
展示如何使用音频增强模块提升语音识别效果
"""

import sys
import os
import time
import json
import logging
import numpy as np
from pathlib import Path
from pydub import AudioSegment

# 添加项目路径
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import vosk
    from audio_enhancer import AudioEnhancer, EnhancedKaldiRecognizer
    logger.info("✅ 成功导入所需模块")
except ImportError as e:
    logger.error(f"❌ 导入模块失败: {e}")
    sys.exit(1)

def load_test_audio(audio_path: str) -> tuple:
    """加载并转换测试音频"""
    logger.info("🔄 加载测试音频...")
    
    try:
        # 加载音频
        audio = AudioSegment.from_file(audio_path)
        logger.info(f"   原始音频: {audio.frame_rate}Hz, {audio.channels}声道, {len(audio)/1000:.2f}秒")
        
        # 转换为单声道16kHz
        if audio.channels > 1:
            audio = audio.set_channels(1)
        if audio.frame_rate != 16000:
            audio = audio.set_frame_rate(16000)
        audio = audio.set_sample_width(2)  # 16-bit
        
        # 转换为numpy数组
        samples = np.array(audio.get_array_of_samples())
        logger.info(f"   转换后音频: {len(samples)} 采样点")
        
        return samples, audio.frame_rate
    except Exception as e:
        logger.error(f"❌ 音频加载失败: {e}")
        return None, None

def compare_recognizers(audio_data: np.ndarray, sample_rate: int):
    """比较标准识别器和增强版识别器"""
    logger.info("🔍 开始比较测试...")
    
    # 初始化模型
    logger.info("   加载VOSK模型...")
    model = vosk.Model(model_name="vosk-model-small-cn-0.22")
    
    # 测试1: 标准识别器
    logger.info("   测试标准识别器...")
    standard_recognizer = vosk.KaldiRecognizer(model, sample_rate)
    standard_recognizer.SetWords(True)
    
    start_time = time.time()
    results = []
    
    # 分块处理音频
    chunk_size = 4000  # 4000 bytes ≈ 0.25秒 (16kHz, 16-bit)
    chunk_samples = chunk_size // 2
    
    total_samples = len(audio_data)
    processed_samples = 0
    
    while processed_samples < total_samples:
        chunk_end = min(processed_samples + chunk_samples, total_samples)
        chunk = audio_data[processed_samples:chunk_end]
        chunk_bytes = chunk.tobytes()
        
        if standard_recognizer.AcceptWaveform(chunk_bytes):
            result = json.loads(standard_recognizer.Result())
            if result.get('text', '').strip():
                results.append(result)
        
        processed_samples = chunk_end
    
    # 获取最终结果
    final_result = json.loads(standard_recognizer.FinalResult())
    if final_result.get('text', '').strip():
        results.append(final_result)
    
    standard_time = time.time() - start_time
    
    # 合并结果
    standard_text = ' '.join([r.get('text', '') for r in results if r.get('text', '').strip()])
    standard_words = sum([len(r.get('result', [])) for r in results])
    
    logger.info(f"   标准识别器结果: {standard_text[:100]}{'...' if len(standard_text) > 100 else ''}")
    logger.info(f"   识别词数: {standard_words}")
    logger.info(f"   处理时间: {standard_time:.2f}秒")
    
    # 测试2: 增强版识别器
    logger.info("   测试增强版识别器...")
    base_recognizer = vosk.KaldiRecognizer(model, sample_rate)
    base_recognizer.SetWords(True)
    
    enhanced_recognizer = EnhancedKaldiRecognizer(
        base_recognizer,
        enable_audio_enhancement=True,
        noise_reduction_strength=0.5,
        gain_target=0.7
    )
    enhanced_recognizer.EnableAudioEnhancement(True)
    
    start_time = time.time()
    results = []
    
    processed_samples = 0
    while processed_samples < total_samples:
        chunk_end = min(processed_samples + chunk_samples, total_samples)
        chunk = audio_data[processed_samples:chunk_end]
        chunk_bytes = chunk.tobytes()
        
        if enhanced_recognizer.AcceptWaveform(chunk_bytes):
            result = json.loads(enhanced_recognizer.Result())
            if result.get('text', '').strip():
                results.append(result)
        
        processed_samples = chunk_end
    
    # 获取最终结果
    final_result = json.loads(enhanced_recognizer.FinalResult())
    if final_result.get('text', '').strip():
        results.append(final_result)
    
    enhanced_time = time.time() - start_time
    
    # 合并结果
    enhanced_text = ' '.join([r.get('text', '') for r in results if r.get('text', '').strip()])
    enhanced_words = sum([len(r.get('result', [])) for r in results])
    
    logger.info(f"   增强版识别器结果: {enhanced_text[:100]}{'...' if len(enhanced_text) > 100 else ''}")
    logger.info(f"   识别词数: {enhanced_words}")
    logger.info(f"   处理时间: {enhanced_time:.2f}秒")
    
    # 获取增强统计信息
    enhancement_stats = enhanced_recognizer.GetEnhancementStats()
    logger.info(f"   增强处理块数: {enhancement_stats.get('processed_chunks', 0)}")
    logger.info(f"   平均增强时间: {enhancement_stats.get('average_enhancement_time', 0)*1000:.2f}毫秒")
    
    # 输出比较结果
    logger.info("📊 测试结果比较:")
    logger.info(f"   文本相似度: {calculate_similarity(standard_text, enhanced_text):.1f}%")
    logger.info(f"   词数差异: {enhanced_words - standard_words}")
    logger.info(f"   时间差异: {enhanced_time - standard_time:+.2f}秒")

def calculate_similarity(text1: str, text2: str) -> float:
    """计算文本相似度"""
    if not text1 and not text2:
        return 100.0
    if not text1 or not text2:
        return 0.0
        
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 and not words2:
        return 100.0
        
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return (intersection / union * 100) if union > 0 else 0.0

def demo_audio_enhancer():
    """演示音频增强器的独立使用"""
    logger.info("🔊 演示音频增强器独立使用...")
    
    # 创建增强器
    enhancer = AudioEnhancer(sample_rate=16000)
    
    # 设置参数
    enhancer.set_noise_reduction(0.6)
    enhancer.set_gain_target(0.8)
    
    logger.info("   音频增强器已配置:")
    logger.info("   - 降噪强度: 0.6")
    logger.info("   - 增益目标: 0.8")
    logger.info("   - 采样率: 16000Hz")
    
    # 生成测试音频数据(模拟)
    test_duration = 1.0  # 1秒
    sample_rate = 16000
    samples = int(test_duration * sample_rate)
    
    # 生成带噪声的正弦波信号
    t = np.linspace(0, test_duration, samples, False)
    signal = np.sin(2 * np.pi * 440 * t)  # 440Hz正弦波
    
    # 添加噪声
    noise = np.random.normal(0, 0.1, samples)
    noisy_signal = signal + noise
    
    # 归一化并转换为int16
    noisy_signal = np.clip(noisy_signal * 32767, -32768, 32767).astype(np.int16)
    audio_bytes = noisy_signal.tobytes()
    
    logger.info(f"   生成测试音频: {len(audio_bytes)} 字节")
    
    # 应用增强
    start_time = time.time()
    enhanced_bytes = enhancer.enhance_audio(audio_bytes)
    enhance_time = time.time() - start_time
    
    logger.info(f"   增强后音频: {len(enhanced_bytes)} 字节")
    logger.info(f"   处理时间: {enhance_time*1000:.2f}毫秒")
    logger.info("✅ 音频增强演示完成")

def main():
    """主函数"""
    logger.info("🎙️ 音频增强功能演示开始")
    logger.info("=" * 50)
    
    # 演示音频增强器独立使用
    demo_audio_enhancer()
    
    # 查找测试音频文件
    test_audio_path = project_path / "tests" / "录音 (12).m4a"
    
    if not test_audio_path.exists():
        logger.warning(f"⚠️  找不到测试音频文件: {test_audio_path}")
        logger.info("请确保tests目录中有录音文件")
        return
    
    logger.info(f"📁 使用测试音频: {test_audio_path}")
    
    # 加载音频
    audio_data, sample_rate = load_test_audio(str(test_audio_path))
    if audio_data is None:
        return
    
    # 比较识别器
    compare_recognizers(audio_data, sample_rate)
    
    logger.info("=" * 50)
    logger.info("🎉 音频增强功能演示完成!")

if __name__ == "__main__":
    main()