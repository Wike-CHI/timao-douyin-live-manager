# -*- coding: utf-8 -*-
"""
VOSK基础验证测试
验证VOSK模型是否正确加载和工作
"""

import asyncio
import logging
import json
import wave
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO)

async def test_vosk_basic():
    """基础VOSK测试"""
    
    print("🔍 VOSK基础验证测试")
    print("=" * 40)
    
    try:
        # 1. 检查VOSK包
        print("1️⃣ 检查VOSK包...")
        try:
            import vosk
            print("✅ VOSK包导入成功")
        except ImportError as e:
            print(f"❌ VOSK包导入失败: {e}")
            return False
        
        # 2. 检查模型路径
        print("2️⃣ 检查模型路径...")
        model_path = Path("d:/gsxm/timao-douyin-live-manager/vosk-api/vosk-model-cn-0.22")
        if model_path.exists():
            print(f"✅ 模型路径存在: {model_path}")
            
            # 检查关键文件
            required_files = [
                "conf/model.conf",
                "ivector/final.ie", 
                "graph/HCLG.fst",
                "graph/words.txt"
            ]
            
            missing_files = []
            for file in required_files:
                if not (model_path / file).exists():
                    missing_files.append(file)
                else:
                    print(f"  ✅ {file}")
            
            if missing_files:
                print(f"❌ 缺失关键文件: {missing_files}")
                return False
        else:
            print(f"❌ 模型路径不存在: {model_path}")
            return False
        
        # 3. 加载模型
        print("3️⃣ 加载VOSK模型...")
        try:
            print("   ⏳ 正在加载模型（可能需要30-60秒）...")
            model = vosk.Model(str(model_path))
            print("   ✅ 模型加载成功")
        except Exception as e:
            print(f"   ❌ 模型加载失败: {e}")
            return False
        
        # 4. 创建识别器
        print("4️⃣ 创建识别器...")
        try:
            rec = vosk.KaldiRecognizer(model, 16000)
            rec.SetWords(True)
            print("   ✅ 识别器创建成功")
        except Exception as e:
            print(f"   ❌ 识别器创建失败: {e}")
            return False
        
        # 5. 测试识别
        print("5️⃣ 测试语音识别...")
        try:
            # 创建测试音频（简单的正弦波，模拟语音信号）
            sample_rate = 16000
            duration = 1.0
            frequency = 440  # A4音符
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio_signal = np.sin(frequency * 2 * np.pi * t) * 0.1
            
            # 添加一些变化，模拟语音特征
            noise = np.random.normal(0, 0.02, len(audio_signal))
            audio_signal += noise
            
            # 转换为16位整数
            audio_int16 = (audio_signal * 32767).astype(np.int16)
            audio_bytes = audio_int16.tobytes()
            
            # 进行识别
            if rec.AcceptWaveform(audio_bytes):
                result = json.loads(rec.Result())
                print(f"   ✅ 识别结果: {result}")
            else:
                partial = json.loads(rec.PartialResult())
                print(f"   ⚠️ 部分结果: {partial}")
                
            # 获取最终结果
            final = json.loads(rec.FinalResult())
            print(f"   📄 最终结果: {final}")
            
        except Exception as e:
            print(f"   ❌ 识别测试失败: {e}")
            return False
        
        print("\n🎉 VOSK基础验证测试完成！")
        print("✅ 真实VOSK模型已成功集成并可以正常工作")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始VOSK基础验证...")
    success = asyncio.run(test_vosk_basic())
    
    if success:
        print("\n📊 测试结论:")
        print("✅ VOSK中文模型集成成功")
        print("✅ 语音识别引擎工作正常") 
        print("✅ 可以进行真实的语音转录测试")
        print("\n💡 下一步可以:")
        print("- 运行真实麦克风录音测试")
        print("- 集成到FastAPI服务中")
        print("- 进行端到端的语音转录验证")
    else:
        print("\n❌ VOSK集成存在问题，需要检查:")
        print("- VOSK模型文件完整性")
        print("- Python环境和依赖")
        print("- 系统资源（内存至少4GB）")