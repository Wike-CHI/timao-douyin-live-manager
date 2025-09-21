#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实音频文件转录测试
测试VOSK音频增强功能的实际效果

功能:
1. 处理真实的音频文件 (支持多种格式)
2. 测试音频增强功能的效果
3. 对比增强前后的转录效果
4. 生成详细的测试报告

依赖:
pip install vosk numpy scipy pydub
"""

import sys
import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 添加VOSK模块到路径
vosk_path = Path(__file__).parent / "vosk-api" / "python"
sys.path.insert(0, str(vosk_path))

try:
    import vosk
    from vosk import Model, KaldiRecognizer
    
    # 尝试导入增强版识别器
    EnhancedKaldiRecognizer = getattr(vosk, 'EnhancedKaldiRecognizer', None)
    ENHANCED_RECOGNIZER_AVAILABLE = EnhancedKaldiRecognizer is not None
    
    # 导入音频处理库
    from pydub import AudioSegment
    from pydub.utils import which
    import numpy as np
    
    print("✅ 所有依赖导入成功")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请安装所需依赖: pip install vosk numpy scipy pydub")
    print("注意: 您可能还需要安装ffmpeg来处理音频文件")
    sys.exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioTranscriptionTester:
    """音频转录测试器"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化测试器
        
        Args:
            model_path: VOSK模型路径
        """
        self.sample_rate = 16000
        self.chunk_size = 4000
        
        # 设置VOSK日志级别
        try:
            vosk.SetLogLevel(-1)
        except:
            pass
        
        # 初始化模型
        self.model = self._load_model(model_path)
        
        # 初始化识别器
        self.standard_recognizer = None
        self.enhanced_recognizer = None
        self._initialize_recognizers()
        
        # 测试结果
        self.test_results = {
            "standard": {
                "transcription": "",
                "confidence": 0.0,
                "processing_time": 0.0,
                "word_count": 0
            },
            "enhanced": {
                "transcription": "",
                "confidence": 0.0,
                "processing_time": 0.0,
                "word_count": 0
            }
        }
    
    def _load_model(self, model_path: Optional[str]) -> Optional[object]:
        """加载VOSK模型"""
        logger.info("正在加载VOSK模型...")
        
        try:
            if model_path and Path(model_path).exists():
                model = Model(model_path=model_path)
                logger.info(f"✅ 模型加载成功: {model_path}")
                return model
            else:
                # 尝试使用默认模型
                logger.info("尝试使用默认中文模型...")
                model = Model(model_name="vosk-model-small-cn-0.22")
                logger.info("✅ 默认模型加载成功")
                return model
                
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            logger.info("请确保已正确安装VOSK模型")
            return None
    
    def _initialize_recognizers(self):
        """初始化识别器"""
        if not self.model:
            logger.error("无法初始化识别器：模型加载失败")
            return
        
        try:
            # 初始化标准识别器
            self.standard_recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.standard_recognizer.SetWords(True)
            logger.info("✅ 标准识别器初始化成功")
            
            # 尝试初始化增强版识别器
            if ENHANCED_RECOGNIZER_AVAILABLE and EnhancedKaldiRecognizer is not None:
                self.enhanced_recognizer = EnhancedKaldiRecognizer(self.model, self.sample_rate)
                self.enhanced_recognizer.SetWords(True)
                logger.info("✅ 增强版识别器初始化成功")
            else:
                logger.warning("⚠️ 增强版识别器不可用，将只测试标准识别器")
                
        except Exception as e:
            logger.error(f"❌ 识别器初始化失败: {e}")
    
    def convert_audio_to_wav(self, audio_path: str) -> str:
        """
        将音频文件转换为WAV格式
        
        Args:
            audio_path: 输入音频文件路径
            
        Returns:
            转换后的WAV文件路径
        """
        logger.info(f"正在转换音频文件: {audio_path}")
        
        try:
            # 加载音频文件
            audio = AudioSegment.from_file(audio_path)
            
            # 转换为单声道，16kHz采样率
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(self.sample_rate)
            audio = audio.set_sample_width(2)  # 16-bit
            
            # 导出为WAV格式
            output_path = Path(audio_path).parent / f"{Path(audio_path).stem}_converted.wav"
            audio.export(str(output_path), format="wav")
            
            logger.info(f"✅ 音频转换完成: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ 音频转换失败: {e}")
            raise
    
    def transcribe_audio(self, wav_path: str, use_enhanced: bool = False) -> Dict:
        """
        转录音频文件
        
        Args:
            wav_path: WAV音频文件路径
            use_enhanced: 是否使用增强版识别器
            
        Returns:
            转录结果字典
        """
        recognizer = self.enhanced_recognizer if use_enhanced else self.standard_recognizer
        
        if not recognizer:
            logger.error("识别器未初始化")
            return {"transcription": "", "confidence": 0.0, "processing_time": 0.0}
        
        logger.info(f"开始转录音频 ({'增强版' if use_enhanced else '标准版'}识别器)")
        
        start_time = time.time()
        results = []
        
        try:
            with open(wav_path, 'rb') as audio_file:
                # 跳过WAV文件头
                audio_file.seek(44)
                
                while True:
                    data = audio_file.read(self.chunk_size)
                    if len(data) == 0:
                        break
                    
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        if result.get('text', '').strip():
                            results.append(result)
                
                # 获取最终结果
                final_result = json.loads(recognizer.FinalResult())
                if final_result.get('text', '').strip():
                    results.append(final_result)
        
        except Exception as e:
            logger.error(f"转录过程中发生错误: {e}")
            return {"transcription": "", "confidence": 0.0, "processing_time": 0.0}
        
        processing_time = time.time() - start_time
        
        # 合并转录结果
        full_transcription = []
        total_confidence = 0.0
        word_count = 0
        
        for result in results:
            text = result.get('text', '').strip()
            if text:
                full_transcription.append(text)
                
                # 计算平均置信度
                if 'result' in result and result['result']:
                    confidences = [word.get('conf', 0.0) for word in result['result']]
                    if confidences:
                        total_confidence += sum(confidences)
                        word_count += len(confidences)
        
        final_transcription = ' '.join(full_transcription)
        avg_confidence = total_confidence / word_count if word_count > 0 else 0.0
        
        logger.info(f"✅ 转录完成 ({processing_time:.2f}秒)")
        logger.info(f"转录结果: {final_transcription[:100]}{'...' if len(final_transcription) > 100 else ''}")
        
        return {
            "transcription": final_transcription,
            "confidence": avg_confidence,
            "processing_time": processing_time,
            "word_count": word_count
        }
    
    def test_audio_file(self, audio_path: str) -> Dict:
        """
        测试音频文件转录
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            测试结果
        """
        logger.info(f"开始测试音频文件: {audio_path}")
        
        if not Path(audio_path).exists():
            logger.error(f"音频文件不存在: {audio_path}")
            return {}
        
        # 转换音频格式
        try:
            wav_path = self.convert_audio_to_wav(audio_path)
        except Exception as e:
            logger.error(f"音频转换失败: {e}")
            return {}
        
        # 测试标准识别器
        logger.info("\n" + "="*50)
        logger.info("🔍 测试标准识别器")
        logger.info("="*50)
        
        self.test_results["standard"] = self.transcribe_audio(wav_path, use_enhanced=False)
        
        # 测试增强版识别器
        if self.enhanced_recognizer:
            logger.info("\n" + "="*50)
            logger.info("🚀 测试增强版识别器")
            logger.info("="*50)
            
            self.test_results["enhanced"] = self.transcribe_audio(wav_path, use_enhanced=True)
        
        # 清理临时文件
        try:
            Path(wav_path).unlink()
        except:
            pass
        
        return self.test_results
    
    def generate_report(self) -> str:
        """生成测试报告"""
        report = []
        report.append("🎙️ VOSK音频转录测试报告")
        report.append("=" * 60)
        
        # 测试环境信息
        report.append("\n📋 测试环境:")
        report.append(f"  VOSK版本: {'已安装' if self.model else '未安装'}")
        report.append(f"  增强功能: {'可用' if ENHANCED_RECOGNIZER_AVAILABLE else '不可用'}")
        report.append(f"  采样率: {self.sample_rate}Hz")
        report.append(f"  块大小: {self.chunk_size} bytes")
        
        # 标准识别器结果
        std_result = self.test_results["standard"]
        report.append("\n🔍 标准识别器结果:")
        report.append(f"  转录文本: {std_result.get('transcription', 'N/A')}")
        report.append(f"  平均置信度: {std_result.get('confidence', 0):.3f}")
        report.append(f"  处理时间: {std_result.get('processing_time', 0):.2f}秒")
        report.append(f"  识别词数: {std_result.get('word_count', 0)}")
        
        # 增强版识别器结果
        if self.enhanced_recognizer:
            enh_result = self.test_results["enhanced"]
            report.append("\n🚀 增强版识别器结果:")
            report.append(f"  转录文本: {enh_result.get('transcription', 'N/A')}")
            report.append(f"  平均置信度: {enh_result.get('confidence', 0):.3f}")
            report.append(f"  处理时间: {enh_result.get('processing_time', 0):.2f}秒")
            report.append(f"  识别词数: {enh_result.get('word_count', 0)}")
            
            # 性能对比
            report.append("\n📊 性能对比:")
            
            # 置信度改进
            conf_improvement = enh_result.get('confidence', 0) - std_result.get('confidence', 0)
            report.append(f"  置信度改进: {conf_improvement:+.3f}")
            
            # 处理时间对比
            time_diff = enh_result.get('processing_time', 0) - std_result.get('processing_time', 0)
            report.append(f"  时间差异: {time_diff:+.2f}秒")
            
            # 词数对比
            word_diff = enh_result.get('word_count', 0) - std_result.get('word_count', 0)
            report.append(f"  识别词数差异: {word_diff:+d}")
            
            # 文本相似度(简单对比)
            std_text = std_result.get('transcription', '')
            enh_text = enh_result.get('transcription', '')
            if std_text and enh_text:
                similarity = len(set(std_text.split()) & set(enh_text.split())) / max(len(std_text.split()), len(enh_text.split())) * 100
                report.append(f"  文本相似度: {similarity:.1f}%")
        
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
    print("🎙️ VOSK音频转录真实测试")
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
        tester = AudioTranscriptionTester()
        
        # 执行测试
        results = tester.test_audio_file(str(test_audio_path))
        
        if results:
            # 显示报告
            report = tester.generate_report()
            print("\n" + report)
            
            # 保存报告
            report_path = Path(__file__).parent / "audio_transcription_test_report.txt"
            tester.save_report(str(report_path))
            
            print(f"\n✅ 测试完成！报告已保存至: {report_path}")
        else:
            print("❌ 测试失败")
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print("❌ 测试失败，请检查错误日志")


if __name__ == "__main__":
    main()