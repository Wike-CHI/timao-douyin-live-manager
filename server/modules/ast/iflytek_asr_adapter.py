#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
科大讯飞实时语音识别适配器

作为SenseVoice的临时替代方案，提供稳定的实时语音识别能力。
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import websockets


@dataclass
class IFlyTekConfig:
    """科大讯飞配置"""
    app_id: str
    api_key: str
    api_secret: str
    # 实时语音识别WebSocket URL
    url: str = "wss://rtasr.xfyun.cn/v1/ws"
    # 音频参数
    sample_rate: int = 16000
    encoding: str = "raw"  # PCM编码
    # 语言设置
    language: str = "zh_cn"  # 中文
    accent: str = "mandarin"  # 普通话
    # 场景
    domain: str = "iat"  # 通用领域
    # VAD相关
    vad_eos: int = 3000  # 静音超时（毫秒）


class IFlyTekASRAdapter:
    """科大讯飞实时语音识别适配器"""
    
    def __init__(self, config: IFlyTekConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._ws: Optional[Any] = None
        self._is_connected = False
        self._result_buffer = []
        self._session_id: Optional[str] = None
        
    def _generate_signature(self) -> str:
        """生成WebSocket连接签名"""
        # 生成RFC1123格式的时间戳
        now = datetime.utcnow()
        date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        # 拼接签名原始字符串
        signature_origin = f"host: rtasr.xfyun.cn\n"
        signature_origin += f"date: {date}\n"
        signature_origin += f"GET /v1/ws HTTP/1.1"
        
        # 使用hmac-sha256加密
        signature_sha = hmac.new(
            self.config.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        
        # Base64编码
        signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')
        
        # 拼接authorization
        authorization_origin = (
            f'api_key="{self.config.api_key}", '
            f'algorithm="hmac-sha256", '
            f'headers="host date request-line", '
            f'signature="{signature_sha_base64}"'
        )
        
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        
        # 构建URL参数
        params = {
            "authorization": authorization,
            "date": date,
            "host": "rtasr.xfyun.cn"
        }
        
        return f"{self.config.url}?{urlencode(params)}"
    
    async def connect(self) -> bool:
        """连接到科大讯飞服务"""
        try:
            url = self._generate_signature()
            self.logger.info("正在连接科大讯飞实时语音识别服务...")
            
            self._ws = await websockets.connect(url)
            self._is_connected = True
            
            # 发送配置参数
            config_data = {
                "common": {
                    "app_id": self.config.app_id
                },
                "business": {
                    "language": self.config.language,
                    "domain": self.config.domain,
                    "accent": self.config.accent,
                    "vad_eos": self.config.vad_eos,
                    "dwa": "wpgs"  # 动态修正
                },
                "data": {
                    "status": 0,  # 0-首帧
                    "format": self.config.encoding,
                    "encoding": "raw",
                    "audio": ""
                }
            }
            
            await self._ws.send(json.dumps(config_data))
            
            # 接收连接确认
            response = await asyncio.wait_for(self._ws.recv(), timeout=5.0)
            result = json.loads(response)
            
            if result.get("code") == 0:
                self.logger.info("✅ 科大讯飞连接成功")
                return True
            else:
                self.logger.error(f"❌ 科大讯飞连接失败: {result}")
                self._is_connected = False
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 连接科大讯飞失败: {e}")
            self._is_connected = False
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None
        self._is_connected = False
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        *,
        session_id: Optional[str] = None,
        is_last: bool = False
    ) -> Dict[str, Any]:
        """
        转写音频
        
        Args:
            audio_data: PCM音频数据（16k, 16bit, 单声道）
            session_id: 会话ID（用于上下文）
            is_last: 是否是最后一帧
            
        Returns:
            转写结果字典
        """
        if not self._is_connected:
            # 自动重连
            success = await self.connect()
            if not success:
                return {
                    "success": False,
                    "type": "error",
                    "text": "",
                    "confidence": 0.0,
                    "timestamp": time.time(),
                    "error": "未连接到科大讯飞服务"
                }
        
        try:
            # Base64编码音频数据
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # 构建数据帧
            data_frame = {
                "data": {
                    "status": 2 if is_last else 1,  # 1-中间帧, 2-最后一帧
                    "format": self.config.encoding,
                    "encoding": "raw",
                    "audio": audio_base64
                }
            }
            
            # 发送音频数据
            await self._ws.send(json.dumps(data_frame))
            
            # 接收识别结果（非阻塞）
            try:
                response = await asyncio.wait_for(self._ws.recv(), timeout=0.5)
                result = json.loads(response)
                
                if result.get("code") == 0:
                    # 解析识别结果
                    data = result.get("data", {})
                    result_text = data.get("result", {}).get("ws", [])
                    
                    # 提取文本
                    text_parts = []
                    for ws_item in result_text:
                        for cw_item in ws_item.get("cw", []):
                            text_parts.append(cw_item.get("w", ""))
                    
                    text = "".join(text_parts).strip()
                    
                    # 判断是否是最终结果
                    is_final = data.get("result", {}).get("pgs", "") == "rpl"
                    
                    return {
                        "success": True,
                        "type": "final" if is_final or is_last else "partial",
                        "text": text,
                        "confidence": 0.9,  # 科大讯飞不返回置信度，使用默认值
                        "timestamp": time.time(),
                        "words": []  # 科大讯飞不返回词级别时间戳
                    }
                else:
                    self.logger.error(f"科大讯飞识别错误: {result}")
                    return {
                        "success": False,
                        "type": "error",
                        "text": "",
                        "confidence": 0.0,
                        "timestamp": time.time(),
                        "error": result.get("message", "未知错误")
                    }
                    
            except asyncio.TimeoutError:
                # 没有收到结果，返回空
                return {
                    "success": True,
                    "type": "silence",
                    "text": "",
                    "confidence": 0.0,
                    "timestamp": time.time(),
                    "words": []
                }
                
        except Exception as e:
            self.logger.error(f"科大讯飞转写失败: {e}")
            # 尝试重连
            self._is_connected = False
            return {
                "success": False,
                "type": "error",
                "text": "",
                "confidence": 0.0,
                "timestamp": time.time(),
                "error": str(e)
            }


class IFlyTekASRService:
    """
    科大讯飞ASR服务（兼容SenseVoice接口）
    
    作为SenseVoice的临时替代方案，提供相同的接口
    """
    
    def __init__(self, config: Optional[IFlyTekConfig] = None):
        import os
        
        # 从环境变量读取配置
        if config is None:
            config = IFlyTekConfig(
                app_id=os.getenv("IFLYTEK_APP_ID", ""),
                api_key=os.getenv("IFLYTEK_API_KEY", ""),
                api_secret=os.getenv("IFLYTEK_API_SECRET", "")
            )
        
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._adapter: Optional[IFlyTekASRAdapter] = None
        self.is_initialized = False
        
        # 会话管理（支持多会话）
        self._session_adapters: Dict[str, IFlyTekASRAdapter] = {}
    
    async def initialize(self) -> bool:
        """初始化服务"""
        # 验证配置
        if not self.config.app_id or not self.config.api_key or not self.config.api_secret:
            self.logger.error("❌ 科大讯飞配置缺失，请设置环境变量：")
            self.logger.error("   IFLYTEK_APP_ID")
            self.logger.error("   IFLYTEK_API_KEY")
            self.logger.error("   IFLYTEK_API_SECRET")
            return False
        
        # 创建一个测试适配器验证配置
        test_adapter = IFlyTekASRAdapter(self.config)
        success = await test_adapter.connect()
        
        if success:
            await test_adapter.disconnect()
            self.is_initialized = True
            self.logger.info("✅ 科大讯飞ASR服务初始化成功")
            return True
        else:
            self.logger.error("❌ 科大讯飞ASR服务初始化失败")
            return False
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        *,
        session_id: Optional[str] = None,
        bias_phrases: Optional[Any] = None,  # 科大讯飞不支持，忽略
    ) -> Dict[str, Any]:
        """
        转写音频（兼容SenseVoice接口）
        
        Args:
            audio_data: PCM音频数据
            session_id: 会话ID
            bias_phrases: 热词（科大讯飞不支持，忽略）
        """
        if not self.is_initialized:
            return {
                "success": False,
                "type": "error",
                "text": "",
                "confidence": 0.0,
                "timestamp": time.time(),
                "error": "服务未初始化"
            }
        
        # 获取或创建会话适配器
        session_key = session_id or "default"
        
        if session_key not in self._session_adapters:
            adapter = IFlyTekASRAdapter(self.config)
            await adapter.connect()
            self._session_adapters[session_key] = adapter
        
        adapter = self._session_adapters[session_key]
        
        # 转写音频
        return await adapter.transcribe_audio(audio_data, session_id=session_id)
    
    async def cleanup(self):
        """清理资源"""
        # 关闭所有会话
        for adapter in self._session_adapters.values():
            await adapter.disconnect()
        
        self._session_adapters.clear()
        self.is_initialized = False
        self.logger.info("科大讯飞ASR服务已清理")
    
    def get_model_info(self) -> Dict[str, Any]:
        """返回模型信息（兼容SenseVoice接口）"""
        return {
            "backend": "iflytek",
            "model_id": "rtasr",
            "initialized": self.is_initialized,
        }

