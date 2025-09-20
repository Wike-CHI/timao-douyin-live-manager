# -*- coding: utf-8 -*-
"""
VOSK语音识别服务 - 独立服务版本
使用Docker容器或独立进程运行VOSK服务
"""

import asyncio
import aiohttp
import logging
import json
import base64
import subprocess
import os
import time
from typing import Optional, Dict, Any, AsyncGenerator
from pathlib import Path
from dataclasses import dataclass

@dataclass
class VoskConfig:
    """VOSK配置"""
    model_path: str
    server_host: str = "localhost"
    server_port: int = 2700
    sample_rate: int = 16000
    confidence_threshold: float = 0.7

class VoskServerManager:
    """VOSK服务管理器"""
    
    def __init__(self, config: VoskConfig):
        self.config = config
        self.process = None
        self.is_running = False
        self.logger = logging.getLogger(__name__)
    
    async def start_server(self) -> bool:
        """启动VOSK服务器"""
        try:
            # 检查模型文件是否存在
            if not Path(self.config.model_path).exists():
                self.logger.error(f"VOSK模型不存在: {self.config.model_path}")
                return False
            
            # 启动VOSK WebSocket服务器
            cmd = [
                "python", "-m", "vosk.transcriber.cli",
                "--interface", self.config.server_host,
                "--port", str(self.config.server_port),
                "--model", self.config.model_path
            ]
            
            self.logger.info(f"启动VOSK服务: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path(__file__).parent.parent.parent / "vosk-api" / "python"
            )
            
            # 等待服务启动
            await asyncio.sleep(3)
            
            # 检查服务是否启动成功
            if await self._check_server_health():
                self.is_running = True
                self.logger.info("✅ VOSK服务启动成功")
                return True
            else:
                self.logger.error("❌ VOSK服务启动失败")
                return False
                
        except Exception as e:
            self.logger.error(f"启动VOSK服务失败: {e}")
            return False
    
    async def stop_server(self):
        """停止VOSK服务器"""
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(
                    asyncio.create_task(self._wait_for_process()),
                    timeout=10
                )
            except asyncio.TimeoutError:
                self.process.kill()
            
            self.process = None
            self.is_running = False
            self.logger.info("VOSK服务已停止")
    
    async def _wait_for_process(self):
        """等待进程结束"""
        while self.process and self.process.poll() is None:
            await asyncio.sleep(0.1)
    
    async def _check_server_health(self) -> bool:
        """检查服务器健康状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{self.config.server_host}:{self.config.server_port}/health") as response:
                    return response.status == 200
        except:
            return False

class VoskServiceV2:
    """VOSK语音识别服务 - 服务版本"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化VOSK服务
        
        Args:
            model_path: 模型路径，默认使用项目中的中文模型
        """
        self.model_path = model_path or self._get_default_model_path()
        
        # 服务配置
        self.config = VoskConfig(
            model_path=self.model_path,
            server_host="localhost",
            server_port=2700
        )
        
        self.server_manager = VoskServerManager(self.config)
        self.session = None
        self.websocket = None
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
        初始化VOSK服务
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 启动VOSK服务器
            if not await self.server_manager.start_server():
                return False
            
            # 创建HTTP会话
            self.session = aiohttp.ClientSession()
            
            # 测试连接
            if await self._test_connection():
                self.is_initialized = True
                self.logger.info("✅ VOSK服务初始化成功")
                return True
            else:
                self.logger.error("❌ VOSK服务连接测试失败")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ VOSK服务初始化失败: {e}")
            return False
    
    async def _test_connection(self) -> bool:
        """测试连接"""
        try:
            # 发送测试音频
            test_audio = b'\x00' * 8000  # 0.5秒的静音
            result = await self.transcribe_audio(test_audio)
            return result.get("success", False)
        except:
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
            # 通过HTTP API发送音频数据
            url = f"http://{self.config.server_host}:{self.config.server_port}/transcribe"
            
            # 编码音频数据
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            data = {
                "audio": audio_b64,
                "sample_rate": self.config.sample_rate,
                "content_type": "audio/wav"
            }
            
            # 棄查session是否已初始化
            if self.session is None:
                raise RuntimeError("HTTP会话未初始化")
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "type": "final",
                        "text": result.get("text", ""),
                        "confidence": result.get("confidence", 0.0),
                        "words": result.get("words", []),
                        "timestamp": time.time()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "text": "",
                        "timestamp": time.time()
                    }
                    
        except Exception as e:
            self.logger.error(f"音频转录失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "timestamp": time.time()
            }
    
    async def transcribe_stream(self, audio_stream: AsyncGenerator[bytes, None]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式转录音频
        
        Args:
            audio_stream: 音频流
            
        Yields:
            Dict: 转录结果
        """
        try:
            # 连接到WebSocket
            ws_url = f"ws://{self.config.server_host}:{self.config.server_port}/ws"
            
            # 棄查session是否已初始化
            if self.session is None:
                raise RuntimeError("HTTP会话未初始化")
            
            async with self.session.ws_connect(ws_url) as ws:
                # 发送配置
                config_msg = {
                    "config": {
                        "sample_rate": self.config.sample_rate,
                        "words": True
                    }
                }
                await ws.send_str(json.dumps(config_msg))
                
                # 处理音频流
                async for audio_chunk in audio_stream:
                    # 发送音频数据
                    await ws.send_bytes(audio_chunk)
                    
                    # 接收转录结果
                    try:
                        msg = await asyncio.wait_for(ws.receive(), timeout=0.1)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            result = json.loads(msg.data)
                            if result.get("text"):
                                yield {
                                    "success": True,
                                    "type": "partial" if result.get("partial") else "final",
                                    "text": result.get("text", ""),
                                    "confidence": result.get("confidence", 0.0),
                                    "timestamp": time.time()
                                }
                    except asyncio.TimeoutError:
                        continue
                
                # 发送结束信号
                await ws.send_str('{"eof": 1}')
                
                # 获取最终结果
                final_msg = await ws.receive()
                if final_msg.type == aiohttp.WSMsgType.TEXT:
                    final_result = json.loads(final_msg.data)
                    yield {
                        "success": True,
                        "type": "final",
                        "text": final_result.get("text", ""),
                        "confidence": final_result.get("confidence", 0.0),
                        "timestamp": time.time()
                    }
                    
        except Exception as e:
            self.logger.error(f"流式转录失败: {e}")
            yield {
                "success": False,
                "error": str(e),
                "text": "",
                "timestamp": time.time()
            }
    
    async def cleanup(self):
        """清理资源"""
        if self.session:
            await self.session.close()
        
        if self.server_manager:
            await self.server_manager.stop_server()
        
        self.is_initialized = False
        self.logger.info("VOSK服务已清理")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict: 模型信息
        """
        return {
            "model_path": self.model_path,
            "server_host": self.config.server_host,
            "server_port": self.config.server_port,
            "sample_rate": self.config.sample_rate,
            "is_initialized": self.is_initialized,
            "model_type": "vosk-model-cn-0.22",
            "deployment_mode": "standalone_server"
        }

# 全局服务实例
vosk_service_v2: Optional[VoskServiceV2] = None

def get_vosk_service() -> VoskServiceV2:
    """获取VOSK服务实例"""
    global vosk_service_v2
    if vosk_service_v2 is None:
        vosk_service_v2 = VoskServiceV2()
    return vosk_service_v2

async def cleanup_vosk_service():
    """清理VOSK服务"""
    global vosk_service_v2
    if vosk_service_v2:
        await vosk_service_v2.cleanup()
        vosk_service_v2 = None

if __name__ == "__main__":
    # 测试代码
    async def test_vosk():
        service = VoskServiceV2()
        
        # 初始化服务
        if await service.initialize():
            print("✅ VOSK服务初始化成功")
            
            # 测试音频转录
            test_audio = b'\x00' * 16000  # 1秒静音
            result = await service.transcribe_audio(test_audio)
            print(f"转录结果: {result}")
            
            # 清理
            await service.cleanup()
        else:
            print("❌ VOSK服务初始化失败")
    
    asyncio.run(test_vosk())