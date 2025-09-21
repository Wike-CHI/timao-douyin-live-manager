#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
长音频实时处理测试脚本
用于测试30分钟演讲音频的处理性能
"""

import sys
import os
import time
import json
import logging
import numpy as np
from pathlib import Path
from pydub import AudioSegment
from typing import Tuple, Union

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

def process_audio_with_timing(audio_data: np.ndarray, sample_rate: int, use_enhancement: bool = False) -> Tuple[str, int, float]:
    """处理音频并计时"""
    logger.info(f"🚀 开始处理音频 (增强: {'开启' if use_enhancement else '关闭'})")
    
    # 初始化模型
    logger.info("   加载VOSK模型...")
    model = vosk.Model(model_name="vosk-model-small-cn-0.22")
    
    # 创建识别器
    base_recognizer = vosk.KaldiRecognizer(model, sample_rate)
    base_recognizer.SetWords(True)
    
    # 类型注解帮助静态分析工具理解
    recognizer: Union[vosk.KaldiRecognizer, EnhancedKaldiRecognizer]
    
    if use_enhancement:
        recognizer = EnhancedKaldiRecognizer(
            base_recognizer,
            enable_audio_enhancement=True,
            noise_reduction_strength=0.5,
            gain_target=0.7
        )
        # 类型安全检查
        if isinstance(recognizer, EnhancedKaldiRecognizer):
            recognizer.EnableAudioEnhancement(True)
        logger.info("   已启用音频增强功能")
    else:
        recognizer = base_recognizer
        logger.info("   使用标准识别器")
    
    start_time = time.time()
    results = []
    
    # 分块处理音频（模拟实时流）
    chunk_size = 4000  # 4000 bytes ≈ 0.25秒 (16kHz, 16-bit)
    chunk_samples = chunk_size // 2
    
    total_samples = len(audio_data)
    processed_samples = 0
    
    # 进度跟踪
    last_progress = 0
    logger.info("   开始处理音频数据...")
    
    while processed_samples < total_samples:
        chunk_end = min(processed_samples + chunk_samples, total_samples)
        chunk = audio_data[processed_samples:chunk_end]
        chunk_bytes = chunk.tobytes()
        
        if recognizer.AcceptWaveform(chunk_bytes):
            result = json.loads(recognizer.Result())
            if result.get('text', '').strip():
                results.append(result)
        
        processed_samples = chunk_end
        
        # 显示进度
        progress = int((processed_samples / total_samples) * 100)
        if progress >= last_progress + 10:  # 每10%显示一次进度
            elapsed = time.time() - start_time
            logger.info(f"   处理进度: {progress}% (已用时: {elapsed:.1f}秒)")
            last_progress = progress
    
    # 获取最终结果
    final_result = json.loads(recognizer.FinalResult())
    if final_result.get('text', '').strip():
        results.append(final_result)
    
    total_time = time.time() - start_time
    
    # 合并结果
    full_text = ' '.join([r.get('text', '') for r in results if r.get('text', '').strip()])
    word_count = sum([len(r.get('result', [])) for r in results])
    
    logger.info(f"   识别完成!")
    logger.info(f"   识别文本: {full_text[:100]}{'...' if len(full_text) > 100 else ''}")
    logger.info(f"   识别词数: {word_count}")
    logger.info(f"   处理时间: {total_time:.2f}秒")
    
    # 如果使用增强，显示增强统计
    if use_enhancement and isinstance(recognizer, EnhancedKaldiRecognizer):
        enhancement_stats = recognizer.GetEnhancementStats()
        logger.info(f"   增强处理块数: {enhancement_stats.get('processed_chunks', 0)}")
        logger.info(f"   平均增强时间: {enhancement_stats.get('average_enhancement_time', 0)*1000:.2f}毫秒")
    
    return full_text, word_count, total_time

def main():
    """主函数"""
    logger.info("🎙️ 长音频实时处理测试")
    logger.info("=" * 50)
    
    # 指定测试音频文件路径 (修改为用户指定的文件)
    test_audio_path = project_path / "tests" / "27994754259-1-30280.mp4"
    
    if not test_audio_path.exists():
        logger.error(f"❌ 找不到测试音频文件: {test_audio_path}")
        return
    
    logger.info(f"📁 使用测试音频: {test_audio_path}")
    
    # 检查文件大小（预估时长）
    file_size_mb = test_audio_path.stat().st_size / (1024 * 1024)
    logger.info(f"   文件大小: {file_size_mb:.1f} MB")
    
    # 加载音频
    audio_data, sample_rate = load_test_audio(str(test_audio_path))
    if audio_data is None:
        return
    
    # 估算音频时长
    estimated_duration = len(audio_data) / sample_rate
    logger.info(f"   估算时长: {estimated_duration/60:.1f} 分钟")
    
    # 测试1: 标准处理
    logger.info("\n" + "=" * 50)
    standard_text, standard_words, standard_time = process_audio_with_timing(
        audio_data, sample_rate, use_enhancement=False
    )
    
    # 测试2: 增强处理
    logger.info("\n" + "=" * 50)
    enhanced_text, enhanced_words, enhanced_time = process_audio_with_timing(
        audio_data, sample_rate, use_enhancement=True
    )
    
    # 输出比较结果
    logger.info("\n" + "=" * 50)
    logger.info("📊 性能比较结果:")
    logger.info(f"   音频时长: {estimated_duration/60:.1f} 分钟")
    logger.info(f"   标准处理: {standard_time:.1f}秒 ({standard_time/estimated_duration*1000:.1f}倍速)")
    logger.info(f"   增强处理: {enhanced_time:.1f}秒 ({enhanced_time/estimated_duration*1000:.1f}倍速)")
    logger.info(f"   处理差异: {enhanced_time - standard_time:+.1f}秒")
    logger.info(f"   词数对比: 标准={standard_words}, 增强={enhanced_words}")
    
    # 保存结果
    results_dir = project_path / "test_results"
    results_dir.mkdir(exist_ok=True)
    
    # 保存文本结果
    with open(results_dir / "standard_transcription.txt", "w", encoding="utf-8") as f:
        f.write(standard_text)
    
    with open(results_dir / "enhanced_transcription.txt", "w", encoding="utf-8") as f:
        f.write(enhanced_text)
    
    logger.info(f"\n📝 结果已保存到: {results_dir}")
    logger.info("🎉 长音频处理测试完成!")

if __name__ == "__main__":
    main()