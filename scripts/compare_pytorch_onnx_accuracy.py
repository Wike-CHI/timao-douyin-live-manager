#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比PyTorch和ONNX版本的准确率和性能

使用方法:
    python scripts/compare_pytorch_onnx_accuracy.py [测试音频文件]
"""
import os
import sys
import time
from pathlib import Path

# 🔧 强制使用CPU，避免CUDA库加载问题
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import numpy as np


async def compare_backends(audio_file: Path = None):
    """对比PyTorch和ONNX后端的性能和准确率"""
    print("=" * 60)
    print("🔬 PyTorch vs ONNX 对比测试")
    print("=" * 60)
    
    # 生成测试音频（1秒，16kHz，单声道）
    if audio_file and audio_file.exists():
        print(f"\n📁 使用音频文件: {audio_file}")
        import soundfile as sf
        audio, sr = sf.read(str(audio_file))
        if sr != 16000:
            print(f"⚠️  音频采样率为{sr}Hz，将重采样到16kHz")
            from scipy import signal
            audio = signal.resample(audio, int(len(audio) * 16000 / sr))
        # 转换为PCM16格式
        audio_pcm16 = (audio * 32768).astype(np.int16).tobytes()
    else:
        print("\n🔊 生成测试音频 (1秒静音)")
        audio_pcm16 = np.zeros(16000, dtype=np.int16).tobytes()
    
    print(f"   音频长度: {len(audio_pcm16) / 2 / 16000:.2f}秒")
    
    results = {}
    
    # 测试PyTorch后端
    print("\n" + "=" * 60)
    print("测试 PyTorch 后端")
    print("=" * 60)
    
    try:
        from server.modules.ast.sensevoice_service import (
            SenseVoiceService,
            SenseVoiceConfig,
        )
        
        pytorch_service = SenseVoiceService(SenseVoiceConfig())
        print("🔧 初始化PyTorch模型...")
        
        init_start = time.time()
        pytorch_ok = await pytorch_service.initialize()
        init_time = time.time() - init_start
        
        if pytorch_ok:
            print(f"✅ 初始化成功 ({init_time:.2f}秒)")
            
            # 性能测试
            print("\n⚡ 性能测试 (10次推理)...")
            times = []
            texts = []
            
            for i in range(10):
                start = time.time()
                result = await pytorch_service.transcribe_audio(audio_pcm16)
                elapsed = time.time() - start
                times.append(elapsed)
                texts.append(result.get('text', ''))
                
                if i == 0:
                    print(f"\n   首次推理结果:")
                    print(f"   - 文本: {result.get('text', '(空)')}")
                    print(f"   - 置信度: {result.get('confidence', 0):.2f}")
                    print(f"   - 时间: {elapsed*1000:.2f}ms")
            
            avg_time = np.mean(times) * 1000
            std_time = np.std(times) * 1000
            
            print(f"\n   平均推理时间: {avg_time:.2f}ms (±{std_time:.2f}ms)")
            print(f"   最快: {min(times)*1000:.2f}ms")
            print(f"   最慢: {max(times)*1000:.2f}ms")
            
            results['pytorch'] = {
                'init_time': init_time,
                'avg_inference_time': avg_time,
                'std_inference_time': std_time,
                'min_inference_time': min(times) * 1000,
                'max_inference_time': max(times) * 1000,
                'sample_text': texts[0],
            }
            
            await pytorch_service.cleanup()
        else:
            print("❌ 初始化失败")
            results['pytorch'] = None
            
    except Exception as e:
        print(f"❌ PyTorch测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['pytorch'] = None
    
    # 测试ONNX后端
    print("\n" + "=" * 60)
    print("测试 ONNX 后端")
    print("=" * 60)
    
    try:
        from server.modules.ast.sensevoice_onnx_service import (
            SenseVoiceONNXService,
            SenseVoiceONNXConfig,
        )
        
        onnx_service = SenseVoiceONNXService(SenseVoiceONNXConfig())
        print("🔧 初始化ONNX模型...")
        
        init_start = time.time()
        onnx_ok = await onnx_service.initialize()
        init_time = time.time() - init_start
        
        if onnx_ok:
            print(f"✅ 初始化成功 ({init_time:.2f}秒)")
            
            # 性能测试
            print("\n⚡ 性能测试 (10次推理)...")
            times = []
            texts = []
            
            for i in range(10):
                start = time.time()
                result = await onnx_service.transcribe_audio(audio_pcm16)
                elapsed = time.time() - start
                times.append(elapsed)
                texts.append(result.get('text', ''))
                
                if i == 0:
                    print(f"\n   首次推理结果:")
                    print(f"   - 文本: {result.get('text', '(空)')}")
                    print(f"   - 置信度: {result.get('confidence', 0):.2f}")
                    print(f"   - 时间: {elapsed*1000:.2f}ms")
            
            avg_time = np.mean(times) * 1000
            std_time = np.std(times) * 1000
            
            print(f"\n   平均推理时间: {avg_time:.2f}ms (±{std_time:.2f}ms)")
            print(f"   最快: {min(times)*1000:.2f}ms")
            print(f"   最慢: {max(times)*1000:.2f}ms")
            
            results['onnx'] = {
                'init_time': init_time,
                'avg_inference_time': avg_time,
                'std_inference_time': std_time,
                'min_inference_time': min(times) * 1000,
                'max_inference_time': max(times) * 1000,
                'sample_text': texts[0],
            }
            
            await onnx_service.cleanup()
        else:
            print("❌ 初始化失败")
            results['onnx'] = None
            
    except Exception as e:
        print(f"❌ ONNX测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['onnx'] = None
    
    # 对比结果
    print("\n" + "=" * 60)
    print("📊 对比结果")
    print("=" * 60)
    
    if results['pytorch'] and results['onnx']:
        pt = results['pytorch']
        ox = results['onnx']
        
        print("\n初始化时间:")
        print(f"  PyTorch: {pt['init_time']:.2f}秒")
        print(f"  ONNX:    {ox['init_time']:.2f}秒")
        speedup = pt['init_time'] / ox['init_time']
        print(f"  加速比: {speedup:.2f}x {'✅' if speedup > 1 else '⚠️'}")
        
        print("\n平均推理时间:")
        print(f"  PyTorch: {pt['avg_inference_time']:.2f}ms")
        print(f"  ONNX:    {ox['avg_inference_time']:.2f}ms")
        speedup = pt['avg_inference_time'] / ox['avg_inference_time']
        print(f"  加速比: {speedup:.2f}x {'✅' if speedup > 1 else '⚠️'}")
        
        print("\n文本准确性:")
        print(f"  PyTorch: {pt['sample_text']}")
        print(f"  ONNX:    {ox['sample_text']}")
        if pt['sample_text'] == ox['sample_text']:
            print("  结果: ✅ 完全一致")
        else:
            print("  结果: ⚠️  有差异（需要进一步验证）")
        
        print("\n总结:")
        if speedup > 1.1:
            print("  ✅ ONNX版本更快")
        elif speedup > 0.9:
            print("  ✅ 两者性能相当")
        else:
            print("  ⚠️  PyTorch版本更快")
        
    elif results['pytorch'] and not results['onnx']:
        print("\n⚠️  ONNX后端测试失败")
        print("   请检查:")
        print("   1. ONNX模型是否已导出")
        print("   2. 运行: python scripts/export_models_to_onnx.py")
        
    elif not results['pytorch'] and results['onnx']:
        print("\n⚠️  PyTorch后端测试失败")
        print("   ONNX后端工作正常")
        
    else:
        print("\n❌ 两个后端都测试失败")
        print("   请检查依赖和模型文件")
    
    print("\n" + "=" * 60)
    
    return results


def main():
    """主函数"""
    # 检查命令行参数
    audio_file = None
    if len(sys.argv) > 1:
        audio_file = Path(sys.argv[1])
        if not audio_file.exists():
            print(f"❌ 音频文件不存在: {audio_file}")
            return 1
    
    # 运行对比测试
    asyncio.run(compare_backends(audio_file))
    return 0


if __name__ == "__main__":
    sys.exit(main())

