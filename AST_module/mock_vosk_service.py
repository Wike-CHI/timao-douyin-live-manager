# -*- coding: utf-8 -*-
"""
VOSK模拟服务 - 当VOSK不可用时的降级方案
提供与VoskServiceV2相同的接口，但使用模拟数据
"""

import asyncio
import logging
import json
import time
import random
from typing import Optional, Dict, Any, AsyncGenerator
from pathlib import Path

class MockVoskService:
    """VOSK模拟服务 - 用于开发和测试"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化模拟VOSK服务
        
        Args:
            model_path: 模型路径 (在模拟模式下被忽略)
        """
        self.model_path = model_path or "./vosk-model-cn-0.22"
        self.is_initialized = False
        self.logger = logging.getLogger(__name__)
        
        # 模拟的中文词汇库
        self.sample_words = [
            "欢迎", "大家", "来到", "直播间", "今天", "给", "大家", "推荐", 
            "这个", "产品", "非常", "好用", "价格", "实惠", "质量", "很好",
            "有", "什么", "问题", "可以", "问", "我", "现在", "下单",
            "还有", "优惠", "活动", "谢谢", "支持", "关注", "点赞"
        ]
        
        # 模拟转录计数器
        self.transcription_count = 0
    
    async def initialize(self) -> bool:
        """
        初始化模拟服务
        
        Returns:
            bool: 总是返回True (模拟成功)
        """
        self.logger.info("🤖 使用VOSK模拟服务 (开发模式)")
        await asyncio.sleep(0.5)  # 模拟加载时间
        self.is_initialized = True
        return True
    
    async def transcribe_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """
        模拟音频转录
        
        Args:
            audio_data: 音频字节数据 (被忽略)
            
        Returns:
            Dict: 模拟的转录结果
        """
        if not self.is_initialized:
            return {
                "success": False,
                "error": "模拟服务未初始化",
                "text": "",
                "timestamp": time.time()
            }
        
        # 模拟处理延迟
        await asyncio.sleep(0.1 + random.uniform(0, 0.2))
        
        # 生成模拟转录文本
        self.transcription_count += 1
        
        # 根据音频数据长度决定是否生成文本
        if len(audio_data) < 1000:  # 太短的音频不转录
            return {
                "success": True,
                "type": "partial",
                "text": "",
                "confidence": 0.0,
                "words": [],
                "timestamp": time.time()
            }
        
        # 生成随机中文句子
        num_words = random.randint(2, 6)
        words = random.sample(self.sample_words, min(num_words, len(self.sample_words)))
        text = " ".join(words)
        
        # 模拟置信度
        confidence = random.uniform(0.3, 0.95)
        
        # 模拟词级别信息
        mock_words = []
        start_time = 0.0
        for i, word in enumerate(words):
            mock_words.append({
                "word": word,
                "start": start_time,
                "end": start_time + len(word) * 0.1,
                "conf": confidence + random.uniform(-0.1, 0.1)
            })
            start_time += len(word) * 0.1 + 0.05
        
        return {
            "success": True,
            "type": "final",
            "text": text,
            "confidence": confidence,
            "words": mock_words,
            "timestamp": time.time(),
            "_mock": True,  # 标识这是模拟数据
            "_count": self.transcription_count
        }
    
    async def transcribe_stream(self, audio_stream: AsyncGenerator[bytes, None]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        模拟流式转录
        
        Args:
            audio_stream: 音频流
            
        Yields:
            Dict: 模拟转录结果
        """
        chunk_count = 0
        
        async for audio_chunk in audio_stream:
            chunk_count += 1
            
            # 每3个音频块生成一次转录结果
            if chunk_count % 3 == 0:
                result = await self.transcribe_audio(audio_chunk)
                if result.get("text"):
                    yield result
            
            # 模拟部分结果
            elif chunk_count % 2 == 0:
                yield {
                    "success": True,
                    "type": "partial",
                    "text": random.choice(self.sample_words) + "...",
                    "confidence": 0.5,
                    "timestamp": time.time(),
                    "_mock": True
                }
    
    async def cleanup(self):
        """清理模拟服务"""
        self.is_initialized = False
        self.logger.info("🤖 VOSK模拟服务已清理")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模拟模型信息
        
        Returns:
            Dict: 模型信息
        """
        return {
            "model_path": self.model_path,
            "sample_rate": 16000,
            "is_initialized": self.is_initialized,
            "model_type": "mock-vosk-cn",
            "deployment_mode": "mock_service",
            "transcription_count": self.transcription_count,
            "status": "🤖 模拟模式 - 仅用于开发和测试"
        }

def create_vosk_service(model_path: Optional[str] = None):
    """
    创建VOSK服务实例 - 自动选择真实或模拟服务
    
    Args:
        model_path: 模型路径
        
    Returns:
        VOSK服务实例
    """
    # 首先尝试导入真实的VOSK
    try:
        from .vosk_service_v2 import VoskServiceV2
        
        # 检查模型文件是否存在
        if model_path and Path(model_path).exists():
            return VoskServiceV2(model_path)
        elif model_path is None:
            # 尝试默认路径
            default_path = Path(__file__).parent.parent / "vosk-api" / "vosk-model-cn-0.22"
            if default_path.exists():
                return VoskServiceV2(str(default_path))
        
        # 如果模型不存在，降级到模拟服务
        logging.warning("VOSK模型文件不存在，使用模拟服务")
        return MockVoskService(model_path)
        
    except ImportError as e:
        logging.warning(f"VOSK模块导入失败: {e}，使用模拟服务")
        return MockVoskService(model_path)

if __name__ == "__main__":
    # 测试模拟服务
    async def test_mock_vosk():
        service = MockVoskService()
        
        print("🧪 测试VOSK模拟服务")
        
        # 初始化
        if await service.initialize():
            print("✅ 模拟服务初始化成功")
            
            # 测试转录
            test_audio = b'\x00' * 8000  # 模拟音频数据
            for i in range(3):
                result = await service.transcribe_audio(test_audio)
                print(f"📝 模拟转录 {i+1}: {result['text']} (置信度: {result['confidence']:.2f})")
            
            # 获取模型信息
            info = service.get_model_info()
            print(f"📊 模型信息: {info['status']}")
            
            # 清理
            await service.cleanup()
        else:
            print("❌ 模拟服务初始化失败")
    
    asyncio.run(test_mock_vosk())