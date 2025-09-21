#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VOSK增强语音识别演示
集成了降噪和麦克风增强功能的VOSK语音识别示例

主要功能:
1. 使用增强版KaldiRecognizer进行语音识别
2. 实时降噪和麦克风增强
3. 自适应音频参数调节
4. 性能监测和统计

依赖安装:
pip install vosk numpy scipy pyaudio
"""

import json
import sys
import os
import time
import logging
from pathlib import Path
from typing import Optional

# 添加VOSK模块到路径
vosk_path = Path(__file__).parent / "vosk-api" / "python"
sys.path.insert(0, str(vosk_path))

try:
    import vosk
    from vosk import Model
    # 尝试导入增强版识别器，如果不存在则使用基础版本
    EnhancedKaldiRecognizer = getattr(vosk, 'EnhancedKaldiRecognizer', None)
    if EnhancedKaldiRecognizer is not None:
        ENHANCED_RECOGNIZER_AVAILABLE = True
    else:
        from vosk import KaldiRecognizer as EnhancedKaldiRecognizer
        ENHANCED_RECOGNIZER_AVAILABLE = False
        
    import pyaudio
    import numpy as np
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所需依赖: pip install vosk numpy scipy pyaudio")
    sys.exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoskEnhancedDemo:
    """VOSK增强语音识别演示类"""
    
    def __init__(self, model_path: Optional[str] = None, model_name: Optional[str] = None):
        """
        初始化演示程序
        
        Args:
            model_path: 模型文件路径
            model_name: 模型名称 (如果model_path为None)
        """
        self.sample_rate = 16000
        self.chunk_size = 4000
        self.audio = None
        self.stream = None
        
        # 设置日志级别
        vosk.SetLogLevel(-1)  # 减少VOSK日志输出
        
        # 初始化模型
        logger.info("正在加载VOSK模型...")
        try:
            if model_path:
                self.model = Model(model_path=model_path)
            else:
                # 尝试自动下载中文模型
                self.model = Model(model_name=model_name or "vosk-model-small-cn-0.22")
            logger.info("模型加载成功")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
        
        # 初始化增强版识别器
        logger.info("正在初始化增强版识别器...")
        if ENHANCED_RECOGNIZER_AVAILABLE and EnhancedKaldiRecognizer is not None:
            # 使用增强版识别器
            self.recognizer = EnhancedKaldiRecognizer(self.model, self.sample_rate)
            # 动态设置增强参数（如果支持）
            if hasattr(self.recognizer, 'enable_audio_enhancement'):
                getattr(self.recognizer, 'enable_audio_enhancement', lambda x: None)(True)
            if hasattr(self.recognizer, 'noise_reduction_strength'):
                getattr(self.recognizer, 'noise_reduction_strength', lambda x: None)(0.6)
            if hasattr(self.recognizer, 'gain_target'):
                getattr(self.recognizer, 'gain_target', lambda x: None)(0.8)
        else:
            # 使用基础识别器
            if EnhancedKaldiRecognizer is not None:
                self.recognizer = EnhancedKaldiRecognizer(self.model, self.sample_rate)
            else:
                # 如果连基础识别器都不可用，则抛出错误
                raise ImportError("无法导入VOSK识别器")
            logger.warning("使用基础识别器，音频增强功能不可用")
        
        # 配置识别器参数
        self.recognizer.SetWords(True)
        self.recognizer.SetPartialWords(True)
        self.recognizer.SetMaxAlternatives(3)
        
        logger.info("增强版识别器初始化完成")
        
        # 统计信息
        self.recognition_stats = {
            "total_chunks": 0,
            "recognition_time": 0.0,
            "successful_recognitions": 0,
            "empty_results": 0
        }
    
    def initialize_audio(self):
        """初始化音频录制"""
        try:
            self.audio = pyaudio.PyAudio()
            
            # 检查可用的音频设备
            logger.info("可用音频设备:")
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if int(info.get('maxInputChannels', 0)) > 0:
                    logger.info(f"  设备 {i}: {info['name']} (输入通道: {info['maxInputChannels']})")
            
            # 创建音频流
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info(f"音频流已初始化 (采样率: {self.sample_rate}Hz, 块大小: {self.chunk_size})")
            
        except Exception as e:
            logger.error(f"音频初始化失败: {e}")
            raise
    
    def run_interactive_demo(self):
        """运行交互式演示"""
        print("\n" + "="*60)
        print("🎤 VOSK增强语音识别演示")
        print("="*60)
        print("功能特性:")
        print("✅ 实时降噪处理")
        print("✅ 麦克风增强")
        print("✅ 自适应音频参数")
        print("✅ 性能监测统计")
        print("="*60)
        print("\n命令说明:")
        print("  回车键 - 开始/停止识别")
        print("  's' - 显示统计信息")
        print("  'n 0.5' - 设置降噪强度(0.0-1.0)")
        print("  'g 0.8' - 设置增益目标(0.0-1.0)")
        print("  'e' - 切换音频增强开关")
        print("  'r' - 重置统计信息")
        print("  'q' - 退出程序")
        print("="*60)
        
        try:
            self.initialize_audio()
            
            while True:
                command = input("\n请输入命令 (回车开始识别): ").strip().lower()
                
                if command == 'q':
                    break
                elif command == 's':
                    self._show_statistics()
                elif command.startswith('n '):
                    if ENHANCED_RECOGNIZER_AVAILABLE and hasattr(self.recognizer, 'SetNoiseReduction'):
                        try:
                            strength = float(command.split()[1])
                            getattr(self.recognizer, 'SetNoiseReduction')(strength)
                            print(f"✅ 降噪强度已设置为: {strength:.2f}")
                        except (ValueError, IndexError):
                            print("❌ 无效的降噪强度值。使用格式: n 0.5")
                    else:
                        print("❌ 音频增强功能不可用")
                elif command.startswith('g '):
                    if ENHANCED_RECOGNIZER_AVAILABLE and hasattr(self.recognizer, 'SetGainTarget'):
                        try:
                            target = float(command.split()[1])
                            getattr(self.recognizer, 'SetGainTarget')(target)
                            print(f"✅ 增益目标已设置为: {target:.2f}")
                        except (ValueError, IndexError):
                            print("❌ 无效的增益目标值。使用格式: g 0.8")
                    else:
                        print("❌ 音频增强功能不可用")
                elif command == 'e':
                    if ENHANCED_RECOGNIZER_AVAILABLE and hasattr(self.recognizer, 'GetEnhancementStats') and hasattr(self.recognizer, 'EnableAudioEnhancement'):
                        # 切换音频增强
                        stats = getattr(self.recognizer, 'GetEnhancementStats')()
                        current_state = stats.get("enhancement_enabled", False)
                        getattr(self.recognizer, 'EnableAudioEnhancement')(not current_state)
                        status = "禁用" if current_state else "启用"
                        print(f"✅ 音频增强已{status}")
                    else:
                        print("❌ 音频增强功能不可用")
                elif command == 'r':
                    if ENHANCED_RECOGNIZER_AVAILABLE and hasattr(self.recognizer, 'ResetEnhancementStats'):
                        getattr(self.recognizer, 'ResetEnhancementStats')()
                    self.recognition_stats = {
                        "total_chunks": 0,
                        "recognition_time": 0.0,
                        "successful_recognitions": 0,
                        "empty_results": 0
                    }
                    print("✅ 统计信息已重置")
                elif command == '' or command == 'start':
                    self._run_recognition_session()
                else:
                    print("❌ 未知命令。请查看帮助信息。")
                    
        except KeyboardInterrupt:
            print("\n\n👋 程序被用户中断")
        except Exception as e:
            logger.error(f"演示运行错误: {e}")
        finally:
            self._cleanup()
    
    def _run_recognition_session(self):
        """运行一次识别会话"""
        print("\n🎤 开始语音识别... (按Ctrl+C停止)")
        print("-" * 50)
        
        try:
            start_time = time.time()
            
            while True:
                # 读取音频数据
                if self.stream:
                    try:
                        data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    except Exception as e:
                        logger.warning(f"音频读取错误: {e}")
                        continue
                else:
                    logger.error("音频流未初始化")
                    break
                
                # 更新统计
                self.recognition_stats["total_chunks"] += 1
                
                # 语音识别
                recognition_start = time.time()
                
                if self.recognizer.AcceptWaveform(data):
                    # 完整识别结果
                    result = json.loads(self.recognizer.Result())
                    recognition_time = time.time() - recognition_start
                    self.recognition_stats["recognition_time"] += recognition_time
                    
                    if result.get("text", "").strip():
                        self.recognition_stats["successful_recognitions"] += 1
                        print(f"✅ 识别结果: {result['text']}")
                        
                        # 显示置信度信息
                        if "result" in result and result["result"]:
                            confidences = [word.get("conf", 0) for word in result["result"]]
                            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                            print(f"   置信度: {avg_confidence:.2f} | 处理时间: {recognition_time*1000:.1f}ms")
                    else:
                        self.recognition_stats["empty_results"] += 1
                else:
                    # 部分识别结果
                    partial = json.loads(self.recognizer.PartialResult())
                    if partial.get("partial", "").strip():
                        print(f"🔄 部分结果: {partial['partial']}", end="\\r")
                
                # 每5秒显示一次简单统计
                if time.time() - start_time > 5:
                    self._show_realtime_stats()
                    start_time = time.time()
                    
        except KeyboardInterrupt:
            print("\\n\\n⏹️ 识别会话已停止")
            # 获取最终结果
            final_result = json.loads(self.recognizer.FinalResult())
            if final_result.get("text", "").strip():
                print(f"🎯 最终结果: {final_result['text']}")
        except Exception as e:
            logger.error(f"识别会话错误: {e}")
    
    def _show_realtime_stats(self):
        """显示实时统计信息"""
        if ENHANCED_RECOGNIZER_AVAILABLE and hasattr(self.recognizer, 'GetEnhancementStats'):
            enhancement_stats = getattr(self.recognizer, 'GetEnhancementStats')()
        else:
            enhancement_stats = {}
        
        print(f"\n📊 实时统计:")
        print(f"   处理块数: {self.recognition_stats['total_chunks']}")
        print(f"   成功识别: {self.recognition_stats['successful_recognitions']}")
        print(f"   音频增强: {'启用' if enhancement_stats.get('enhancement_enabled', False) else '禁用'}")
        if enhancement_stats.get('processed_chunks', 0) > 0:
            avg_enhancement_time = enhancement_stats.get('average_enhancement_time', 0)
            print(f"   平均增强时间: {avg_enhancement_time*1000:.1f}ms")
    
    def _show_statistics(self):
        """显示详细统计信息"""
        if ENHANCED_RECOGNIZER_AVAILABLE and hasattr(self.recognizer, 'GetEnhancementStats'):
            enhancement_stats = getattr(self.recognizer, 'GetEnhancementStats')()
        else:
            enhancement_stats = {}
        
        print("\n" + "="*50)
        print("📊 详细统计信息")
        print("="*50)
        
        # 识别统计
        print("🎤 语音识别统计:")
        print(f"   总处理块数: {self.recognition_stats['total_chunks']}")
        print(f"   成功识别次数: {self.recognition_stats['successful_recognitions']}")
        print(f"   空结果次数: {self.recognition_stats['empty_results']}")
        
        if self.recognition_stats['total_chunks'] > 0:
            success_rate = (self.recognition_stats['successful_recognitions'] / 
                          self.recognition_stats['total_chunks'] * 100)
            print(f"   识别成功率: {success_rate:.1f}%")
        
        if self.recognition_stats['successful_recognitions'] > 0:
            avg_time = (self.recognition_stats['recognition_time'] / 
                       self.recognition_stats['successful_recognitions'])
            print(f"   平均识别时间: {avg_time*1000:.1f}ms")
        
        # 音频增强统计
        print("\n🔧 音频增强统计:")
        print(f"   增强功能状态: {'启用' if enhancement_stats.get('enhancement_enabled', False) else '禁用'}")
        print(f"   增强处理块数: {enhancement_stats.get('processed_chunks', 0)}")
        
        if enhancement_stats.get('processed_chunks', 0) > 0:
            avg_enhancement_time = enhancement_stats.get('average_enhancement_time', 0)
            total_enhancement_time = enhancement_stats.get('enhancement_time', 0)
            print(f"   总增强时间: {total_enhancement_time*1000:.1f}ms")
            print(f"   平均增强时间: {avg_enhancement_time*1000:.1f}ms")
            
            # 计算性能影响
            if self.recognition_stats['recognition_time'] > 0:
                enhancement_overhead = (total_enhancement_time / 
                                      self.recognition_stats['recognition_time'] * 100)
                print(f"   性能开销: {enhancement_overhead:.1f}%")
        
        print("="*50)
    
    def _cleanup(self):
        """清理资源"""
        logger.info("正在清理资源...")
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if self.audio:
            self.audio.terminate()
        
        logger.info("资源清理完成")


def main():
    """主函数"""
    print("🚀 正在启动VOSK增强语音识别演示...")
    
    # 检查模型路径
    model_path = None
    possible_paths = [
        "vosk-model-small-cn-0.22",
        "models/vosk-model-small-cn-0.22",
        Path.home() / ".cache/vosk/vosk-model-small-cn-0.22"
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            model_path = str(path)
            break
    
    try:
        demo = VoskEnhancedDemo(model_path=model_path)
        demo.run_interactive_demo()
    except Exception as e:
        logger.error(f"演示启动失败: {e}")
        print("\\n❌ 程序启动失败。请检查:")
        print("1. VOSK模型是否正确安装")
        print("2. 音频设备是否可用")
        print("3. 所需依赖包是否已安装")
        sys.exit(1)


if __name__ == "__main__":
    main()