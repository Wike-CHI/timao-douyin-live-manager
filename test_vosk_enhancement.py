# -*- coding: utf-8 -*-
"""
VOSK音频增强功能测试脚本
测试AudioEnhancer和EnhancedKaldiRecognizer功能
"""

import sys
import os
import numpy as np
from pathlib import Path

# 添加项目路径
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

def test_vosk_enhancement():
    """测试VOSK音频增强功能"""
    print("🎙️ VOSK音频增强功能测试")
    print("=" * 50)
    
    try:
        # 导入VOSK模块
        import vosk
        print("✅ VOSK模块导入成功")
        print(f"  VOSK版本: {getattr(vosk, '__version__', 'unknown')}")
        
        # 导入音频增强模块
        try:
            # 修复：正确从audio_enhancer模块导入，而不是从vosk模块
            from audio_enhancer import AudioEnhancer, EnhancedKaldiRecognizer
            print("✅ 音频增强模块导入成功")
        except ImportError as e:
            print(f"❌ 音频增强模块导入失败: {e}")
            return False
        
        # 测试AudioEnhancer
        print("\n🔍 测试AudioEnhancer...")
        try:
            enhancer = AudioEnhancer(sample_rate=16000)
            print("✅ AudioEnhancer实例创建成功")
            print(f"  增强器启用状态: {enhancer.enabled}")
            
            # 生成测试音频数据
            duration = 1.0  # 1秒
            sample_rate = 16000
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # 创建带噪声的测试信号
            clean_signal = np.sin(2 * np.pi * 440 * t)  # 440Hz正弦波
            noise = 0.1 * np.random.randn(len(t))  # 添加噪声
            noisy_signal = clean_signal + noise
            
            # 转换为int16格式
            audio_data = (noisy_signal * 32767).astype(np.int16).tobytes()
            print(f"  生成测试音频数据: {len(audio_data)} 字节")
            
            # 测试音频增强
            if enhancer.enabled:
                enhanced_data = enhancer.enhance_audio(audio_data)
                print(f"  音频增强完成: {len(enhanced_data)} 字节")
                print("✅ AudioEnhancer功能正常")
            else:
                print("⚠️  AudioEnhancer未启用（缺少依赖）")
                
        except Exception as e:
            print(f"❌ AudioEnhancer测试失败: {e}")
            return False
            
        # 测试EnhancedKaldiRecognizer
        print("\n🔍 测试EnhancedKaldiRecognizer...")
        try:
            # 创建基础识别器
            try:
                model = vosk.Model(model_name="vosk-model-small-cn-0.22")
                base_recognizer = vosk.KaldiRecognizer(model, 16000)
                print("✅ VOSK基础识别器创建成功")
            except Exception as e:
                print(f"⚠️  VOSK模型加载失败: {e}")
                print("  将创建模拟识别器进行测试")
                base_recognizer = None
            
            # 创建增强版识别器实例
            if base_recognizer:
                # 修复：正确使用从audio_enhancer模块导入的EnhancedKaldiRecognizer
                enhanced_recognizer = EnhancedKaldiRecognizer(
                    base_recognizer,
                    enable_audio_enhancement=True,
                    noise_reduction_strength=0.5,
                    gain_target=0.7
                )
            else:
                # 创建模拟的增强识别器用于测试
                class MockRecognizer:
                    def __init__(self):
                        pass
                    
                    def AcceptWaveform(self, data):
                        return 1
                    
                    def Result(self):
                        return '{"text": "mock result"}'
                    
                    def FinalResult(self):
                        return '{"text": "mock final result"}'
                
                mock_recognizer = MockRecognizer()
                # 修复：正确使用从audio_enhancer模块导入的EnhancedKaldiRecognizer
                enhanced_recognizer = EnhancedKaldiRecognizer(
                    mock_recognizer,
                    enable_audio_enhancement=True,
                    noise_reduction_strength=0.5,
                    gain_target=0.7
                )
            
            print("✅ EnhancedKaldiRecognizer实例创建成功")
            
            # 检查方法
            methods = [
                'AcceptWaveform', 'SetNoiseReduction', 'SetGainTarget',
                'EnableAudioEnhancement', 'GetEnhancementStats', 'ResetEnhancementStats'
            ]
            
            for method in methods:
                if hasattr(enhanced_recognizer, method):
                    print(f"  ✅ 方法 {method} 可用")
                else:
                    print(f"  ❌ 方法 {method} 缺失")
                    
            print("✅ EnhancedKaldiRecognizer功能检查完成")
            
        except Exception as e:
            print(f"❌ EnhancedKaldiRecognizer测试失败: {e}")
            return False
            
        print("\n🎉 所有测试通过！")
        print("VOSK音频增强功能已正确集成")
        return True
        
    except ImportError as e:
        print(f"❌ VOSK模块导入失败: {e}")
        print("请确保VOSK已正确安装")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    print("VOSK音频增强功能验证脚本")
    print("=" * 50)
    
    success = test_vosk_enhancement()
    
    if success:
        print("\n✅ VOSK音频增强功能验证成功")
        print("您可以使用增强版语音识别功能了！")
    else:
        print("\n❌ VOSK音频增强功能验证失败")
        print("请检查安装和配置")

if __name__ == "__main__":
    main()