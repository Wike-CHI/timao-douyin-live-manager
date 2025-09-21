# -*- coding: utf-8 -*-
"""
简单的VOSK测试脚本
"""

import sys
from pathlib import Path

# 添加VOSK模块路径
vosk_path = Path(__file__).parent / "vosk-api" / "python"
sys.path.insert(0, str(vosk_path))

def test_vosk():
    try:
        import vosk
        print("VOSK模块导入成功")
        print(f"AudioEnhancer可用: {hasattr(vosk, 'AudioEnhancer')}")
        print(f"EnhancedKaldiRecognizer可用: {hasattr(vosk, 'EnhancedKaldiRecognizer')}")
        
        if hasattr(vosk, 'AudioEnhancer'):
            AudioEnhancerClass = getattr(vosk, 'AudioEnhancer', None)
            if AudioEnhancerClass is not None:
                enhancer = AudioEnhancerClass()
                print(f"AudioEnhancer实例创建成功: {enhancer.enabled}")
            else:
                print("AudioEnhancer类不存在")
            
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    test_vosk()