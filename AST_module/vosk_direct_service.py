# -*- coding: utf-8 -*-
"""
VOSK直接集成服务
直接使用VOSK Python API，不依赖独立服务进程
"""

import json
import asyncio
import logging
import time
from typing import Optional, Dict, Any
from pathlib import Path

class VoskDirectService:
    """VOSK直接集成服务"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化VOSK直接服务
        
        Args:
            model_path: 模型路径
        """
        self.model_path = model_path or self._get_default_model_path()
        self.model = None
        self.recognizer = None
        self.sample_rate = 16000
        self.is_initialized = False
        
        # 日志配置
        self.logger = logging.getLogger(__name__)
        
    def _get_default_model_path(self) -> str:
        """获取默认的中文模型路径"""
        current_dir = Path(__file__).parent.parent
        model_path = current_dir / "vosk-api" / "vosk-model-cn-0.22"
        return str(model_path)
    
    async def initialize(self) -> bool:
        """
        初始化VOSK模型
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 检查模型路径
            if not Path(self.model_path).exists():
                self.logger.error(f"VOSK模型路径不存在: {self.model_path}")
                return False
            
            self.logger.info(f"正在加载VOSK模型: {self.model_path}")
            
            # 导入VOSK
            try:
                import vosk
                self.logger.info("VOSK Python包导入成功")
            except ImportError as e:
                self.logger.error(f"VOSK Python包导入失败: {e}")
                return False
            
            # 在线程池中加载模型（避免阻塞）
            loop = asyncio.get_event_loop()
            
            def load_model():
                model = vosk.Model(self.model_path)
                recognizer = vosk.KaldiRecognizer(model, self.sample_rate)
                recognizer.SetWords(True)  # 启用单词级别的时间戳
                return model, recognizer
            
            self.model, self.recognizer = await loop.run_in_executor(None, load_model)
            
            self.is_initialized = True
            self.logger.info("✅ VOSK模型加载成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ VOSK模型加载失败: {e}")
            return False
    
    async def transcribe_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """
        转录音频数据
        
        Args:
            audio_data: 音频字节数据 (16kHz, 16bit, 单声道)
            
        Returns:
            Dict: 转录结果
        """
        if not self.is_initialized:
            return {
                "success": False,
                "error": "VOSK服务未初始化",
                "text": "",
                "timestamp": time.time()
            }
        
        try:
            # 在线程池中处理音频（避免阻塞）
            loop = asyncio.get_event_loop()
            
            def process_audio():
                # 处理音频数据
                if self.recognizer.AcceptWaveform(audio_data):
                    # 完整识别结果
                    result = json.loads(self.recognizer.Result())
                    return {
                        "success": True,
                        "type": "final",
                        "text": result.get("text", ""),
                        "confidence": self._calculate_confidence(result),
                        "words": result.get("result", []),
                        "timestamp": time.time()
                    }
                else:
                    # 部分识别结果
                    partial = json.loads(self.recognizer.PartialResult())
                    return {
                        "success": True,
                        "type": "partial",
                        "text": partial.get("partial", ""),
                        "confidence": 0.5,  # 部分结果置信度较低
                        "words": [],
                        "timestamp": time.time()
                    }
            
            result = await loop.run_in_executor(None, process_audio)
            return result
                
        except Exception as e:
            self.logger.error(f"音频转录失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "timestamp": time.time()
            }
    
    async def transcribe_final(self) -> Dict[str, Any]:
        """
        获取最终转录结果
        
        Returns:
            Dict: 最终转录结果
        """
        if not self.is_initialized:
            return {
                "success": False,
                "error": "VOSK服务未初始化",
                "text": "",
                "timestamp": time.time()
            }
        
        try:
            loop = asyncio.get_event_loop()
            
            def get_final():
                result = json.loads(self.recognizer.FinalResult())
                return {
                    "success": True,
                    "type": "final",
                    "text": result.get("text", ""),
                    "confidence": self._calculate_confidence(result),
                    "words": result.get("result", []),
                    "timestamp": time.time()
                }
            
            return await loop.run_in_executor(None, get_final)
            
        except Exception as e:
            self.logger.error(f"获取最终结果失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "timestamp": time.time()
            }
    
    def reset(self):
        """重置识别器状态"""
        if self.recognizer:
            self.recognizer.Reset()
    
    def _calculate_confidence(self, result: Dict) -> float:
        """
        计算识别置信度
        
        Args:
            result: VOSK识别结果
            
        Returns:
            float: 置信度 (0-1)
        """
        if not result.get("result"):
            return 0.0
            
        words = result["result"]
        if not words:
            return 0.0
            
        # 计算平均置信度
        confidences = [word.get("conf", 0.0) for word in words]
        return sum(confidences) / len(confidences)
    
    async def cleanup(self):
        """清理资源"""
        self.is_initialized = False
        self.model = None
        self.recognizer = None
        self.logger.info("VOSK直接服务已清理")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict: 模型信息
        """
        return {
            "model_path": self.model_path,
            "sample_rate": self.sample_rate,
            "is_initialized": self.is_initialized,
            "model_type": "vosk-model-cn-0.22",
            "deployment_mode": "direct_integration",
            "status": "✅ 真实VOSK模型" if self.is_initialized else "⚠️ 未初始化"
        }

if __name__ == "__main__":
    # 测试代码
    async def test_vosk_direct():
        service = VoskDirectService()
        
        print("🧪 测试VOSK直接集成服务")
        
        # 初始化
        if await service.initialize():
            print("✅ VOSK直接服务初始化成功")
            
            # 创建测试音频数据 (1秒静音)
            import numpy as np
            sample_rate = 16000
            duration = 1  # 1秒
            
            # 生成简单的正弦波测试音频
            t = np.linspace(0, duration, sample_rate * duration, False)
            frequency = 440  # A4音符
            audio_signal = np.sin(frequency * 2 * np.pi * t) * 0.1
            
            # 转换为16位整数
            audio_int16 = (audio_signal * 32767).astype(np.int16)
            test_audio = audio_int16.tobytes()
            
            # 测试转录
            result = await service.transcribe_audio(test_audio)
            print(f"📝 转录结果: {result}")
            
            # 获取模型信息
            info = service.get_model_info()
            print(f"📊 模型信息: {info}")
            
            # 清理
            await service.cleanup()
        else:
            print("❌ VOSK直接服务初始化失败")
    
    asyncio.run(test_vosk_direct())