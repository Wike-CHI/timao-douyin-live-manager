# -*- coding: utf-8 -*-
"""
VOSK语音识别服务
基于本地VOSK模型的中文语音识别
"""

import json
import asyncio
import logging
import os
import sys
from typing import Optional, Dict, Any
from pathlib import Path

# 添加VOSK路径到系统路径
VOSK_PATH = Path(__file__).parent.parent.parent / "vosk-api" / "python"
sys.path.insert(0, str(VOSK_PATH))

try:
    from vosk import Model, KaldiRecognizer
except ImportError as e:
    logging.error(f"VOSK导入失败: {e}")
    raise

class VoskService:
    """VOSK语音识别服务"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化VOSK服务
        
        Args:
            model_path: 模型路径，默认使用项目中的中文模型
        """
        self.model_path = model_path or self._get_default_model_path()
        self.model = None
        self.recognizer = None
        self.sample_rate = 16000  # VOSK推荐的采样率
        self.is_initialized = False
        
        # 日志配置
        self.logger = logging.getLogger(__name__)
        
    def _get_default_model_path(self) -> str:
        """获取默认的中文模型路径"""
        current_dir = Path(__file__).parent.parent.parent
        model_path = current_dir / "vosk-api" / "vosk-model-cn-0.22"
        
        if not model_path.exists():
            raise FileNotFoundError(f"VOSK中文模型未找到: {model_path}")
            
        return str(model_path)
    
    async def initialize(self) -> bool:
        """
        异步初始化VOSK模型
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info(f"正在加载VOSK模型: {self.model_path}")
            
            # 在线程池中加载模型 (避免阻塞)
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, lambda: Model(self.model_path)
            )
            
            # 创建识别器
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)  # 启用单词级别的时间戳
            
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
            raise RuntimeError("VOSK服务未初始化，请先调用initialize()")
        
        try:
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
                    "timestamp": self._get_current_timestamp()
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
                    "timestamp": self._get_current_timestamp()
                }
                
        except Exception as e:
            self.logger.error(f"音频转录失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "timestamp": self._get_current_timestamp()
            }
    
    async def transcribe_final(self) -> Dict[str, Any]:
        """
        获取最终转录结果
        
        Returns:
            Dict: 最终转录结果
        """
        if not self.is_initialized:
            raise RuntimeError("VOSK服务未初始化")
        
        try:
            result = json.loads(self.recognizer.FinalResult())
            return {
                "success": True,
                "type": "final",
                "text": result.get("text", ""),
                "confidence": self._calculate_confidence(result),
                "words": result.get("result", []),
                "timestamp": self._get_current_timestamp()
            }
        except Exception as e:
            self.logger.error(f"获取最终结果失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "timestamp": self._get_current_timestamp()
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
    
    def _get_current_timestamp(self) -> float:
        """获取当前时间戳"""
        import time
        return time.time()
    
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
            "language": "zh-CN"
        }

class AudioProcessor:
    """音频处理器"""
    
    @staticmethod
    def validate_audio_format(audio_data: bytes, expected_rate: int = 16000) -> bool:
        """
        验证音频格式
        
        Args:
            audio_data: 音频数据
            expected_rate: 期望的采样率
            
        Returns:
            bool: 格式是否正确
        """
        # 简单的长度检查
        if len(audio_data) == 0:
            return False
            
        # TODO: 添加更详细的音频格式验证
        return True
    
    @staticmethod
    def convert_to_16khz_mono(audio_data: bytes) -> bytes:
        """
        转换音频到16kHz单声道格式
        
        Args:
            audio_data: 原始音频数据
            
        Returns:
            bytes: 转换后的音频数据
        """
        # TODO: 实现音频格式转换
        # 这里可以使用ffmpeg或其他音频处理库
        return audio_data

# 全局VOSK服务实例
vosk_service: Optional[VoskService] = None

async def get_vosk_service() -> VoskService:
    """
    获取全局VOSK服务实例
    
    Returns:
        VoskService: VOSK服务实例
    """
    global vosk_service
    
    if vosk_service is None:
        vosk_service = VoskService()
        await vosk_service.initialize()
    
    return vosk_service

async def cleanup_vosk_service():
    """清理VOSK服务"""
    global vosk_service
    if vosk_service:
        vosk_service = None

if __name__ == "__main__":
    # 测试代码
    async def test_vosk():
        service = VoskService()
        success = await service.initialize()
        print(f"VOSK初始化: {'成功' if success else '失败'}")
        print(f"模型信息: {service.get_model_info()}")
    
    asyncio.run(test_vosk())