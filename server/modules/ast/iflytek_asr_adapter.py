#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
讯飞实时语音转写大模型适配器

作为SenseVoice的替代方案，使用讯飞办公产品API提供稳定的实时语音识别能力。
审查人：叶维哲
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlencode

import websockets


@dataclass
class IFlyTekConfig:
    """讯飞语音转写配置"""
    app_id: str
    api_key: str
    api_secret: str
    # 实时语音转写大模型WebSocket URL
    url: str = "wss://office-api-ast-dx.iflyaisol.com/ast/communicate/v1"
    # 音频参数
    sample_rate: int = 16000
    audio_encode: str = "pcm_s16le"  # PCM S16LE格式
    # 语言设置
    lang: str = "autodialect"  # 中英+202种方言自动识别
    # 说话人分离
    role_type: int = 0  # 0-关闭, 2-开启实时角色分离


class IFlyTekASRAdapter:
    """讯飞实时语音转写适配器"""
    
    def __init__(self, config: IFlyTekConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._ws: Optional[Any] = None
        self._is_connected = False
        self._result_buffer: List[str] = []
        self._session_id: Optional[str] = None
        
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """生成签名（讯飞办公产品签名规则）"""
        # 1. 参数排序
        sorted_keys = sorted(params.keys())
        
        # 2. URL编码并拼接
        base_string_parts = []
        for key in sorted_keys:
            value = str(params[key])
            encoded_key = quote(key, safe='')
            encoded_value = quote(value, safe='')
            base_string_parts.append(f"{encoded_key}={encoded_value}")
        
        base_string = "&".join(base_string_parts)
        
        # 3. HMAC-SHA1签名
        signature_bytes = hmac.new(
            self.config.api_secret.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        # 4. Base64编码
        signature = base64.b64encode(signature_bytes).decode('utf-8')
        
        return signature
    
    def _build_url(self) -> str:
        """构建WebSocket URL"""
        import uuid
        
        # 本地时间（北京时间 UTC+8）
        local_time = datetime.now()
        utc_str = local_time.strftime("%Y-%m-%dT%H:%M:%S+0800")
        
        # 请求参数
        params = {
            "appId": self.config.app_id,
            "accessKeyId": self.config.api_key,
            "uuid": str(uuid.uuid4()),
            "utc": utc_str,
            "audio_encode": self.config.audio_encode,
            "lang": self.config.lang,
            "samplerate": str(self.config.sample_rate),
        }
        
        # 生成签名
        signature = self._generate_signature(params)
        params["signature"] = signature
        
        # URL编码参数（按字母顺序排列，与签名生成顺序一致）
        query_parts = []
        for key in sorted(params.keys()):
            value = params[key]
            # URL编码键和值
            encoded_key = quote(str(key), safe='')
            encoded_value = quote(str(value), safe='')
            query_parts.append(f"{encoded_key}={encoded_value}")
        
        query_string = "&".join(query_parts)
        
        return f"{self.config.url}?{query_string}"
    
    async def connect(self) -> bool:
        """连接到讯飞服务"""
        try:
            url = self._build_url()
            self.logger.info("正在连接讯飞实时语音转写服务...")
            self.logger.debug(f"连接URL: {url[:100]}...")  # 只显示前100个字符
            
            self._ws = await websockets.connect(url, ping_interval=None)
            
            # 接收握手响应
            response = await asyncio.wait_for(self._ws.recv(), timeout=5.0)
            result = json.loads(response)
            
            # 检查握手响应（msg_type=action, data.action=started）
            if result.get("msg_type") == "action" and result.get("data", {}).get("action") == "started":
                self.logger.info("✅ 讯飞连接成功")
                self._is_connected = True
                self._result_buffer.clear()
                return True
            else:
                self.logger.error(f"❌ 讯飞握手失败: {result}")
                self._is_connected = False
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 连接讯飞失败: {e}")
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
            转写结果字典（兼容SenseVoice格式）
        """
        if not self._is_connected:
            # 自动重连
            success = await self.connect()
            if not success:
                return {
                    "success": False,
                    "text": "",
                    "confidence": 0.0,
                    "words": []
                }
        
        try:
            # 分块发送音频数据（每40ms发送1280字节）
            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                if not chunk:
                    break
                
                # 直接发送二进制数据
                await self._ws.send(chunk)
                await asyncio.sleep(0.04)  # 40ms
            
            # 如果是最后一帧，发送结束标识
            if is_last:
                await self._ws.send(b'{"end": true}')
            
            # 接收所有可用结果
            transcription_result: List[str] = []
            response_count = 0  # 计数器
            try:
                # 给足够的时间接收结果（最多等待10秒）
                max_wait_time = 10.0
                start_wait = time.time()
                consecutive_timeouts = 0
                
                while time.time() - start_wait < max_wait_time:
                    try:
                        response = await asyncio.wait_for(self._ws.recv(), timeout=0.5)
                        consecutive_timeouts = 0  # 重置超时计数
                        
                        if isinstance(response, str):
                            result = json.loads(response)
                            msg_type = result.get('msg_type')
                            self.logger.debug(f"收到响应: {msg_type}")
                            
                            # 检查错误
                            if result.get("msg_type") == "error":
                                error_data = result.get("data", {})
                                self.logger.error(f"讯飞识别错误: {error_data}")
                                return {
                                    "success": False,
                                    "text": "",
                                    "confidence": 0.0,
                                    "words": []
                                }
                            
                            # 检查结束信号
                            if result.get("msg_type") == "action":
                                action = result.get("data", {}).get("action")
                                if action == "finished":
                                    self.logger.info("收到结束信号，停止接收")
                                    break
                            
                            # 解析识别结果
                            if result.get("msg_type") == "result":
                                response_count += 1
                                res_type = result.get("res_type", "")
                                data = result.get("data", {})
                                
                                # 正确的结构是: data.cn.st.rt[]
                                cn = data.get("cn", {})
                                st = cn.get("st", {})
                                rt_list = st.get("rt", [])
                                
                                # 提取文本
                                words_in_response = 0
                                for rt in rt_list:
                                    for word_seg in rt.get("ws", []):
                                        for cw in word_seg.get("cw", []):
                                            word = cw.get("w", "")
                                            if word:
                                                transcription_result.append(word)
                                                words_in_response += 1
                                
                                self.logger.info(f"响应#{response_count}: 提取了{words_in_response}个字")
                    except asyncio.TimeoutError:
                        consecutive_timeouts += 1
                        # 如果连续超时3次，认为没有更多结果了
                        if consecutive_timeouts >= 3:
                            self.logger.info("连续超时，结束接收")
                            break
            except Exception as inner_e:
                self.logger.warning(f"接收结果时出错: {inner_e}")
            
            # 拼接结果
            text = "".join(transcription_result)
            
            return {
                "success": True,
                "text": text,
                "confidence": 0.85,  # 讯飞大模型默认置信度
                "words": []
            }
                
        except Exception as e:
            self.logger.error(f"讯飞转写失败: {e}")
            # 标记需要重连
            self._is_connected = False
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "words": []
            }


class IFlyTekASRService:
    """
    科大讯飞ASR服务（兼容SenseVoice接口）
    
    作为SenseVoice的临时替代方案，提供相同的接口
    """
    
    def __init__(self, config: Optional[IFlyTekConfig] = None):
        import os
        
        # 从环境变量读取配置（使用新的XFYUN前缀）
        if config is None:
            config = IFlyTekConfig(
                app_id=os.getenv("XFYUN_APPID", ""),
                api_key=os.getenv("XFYUN_API_KEY", ""),
                api_secret=os.getenv("XFYUN_API_SECRET", "")
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
            self.logger.error("❌ 讯飞配置缺失，请设置环境变量：")
            self.logger.error("   XFYUN_APPID")
            self.logger.error("   XFYUN_API_KEY")
            self.logger.error("   XFYUN_API_SECRET")
            return False
        
        # 创建一个测试适配器验证配置
        test_adapter = IFlyTekASRAdapter(self.config)
        success = await test_adapter.connect()
        
        if success:
            await test_adapter.disconnect()
            self.is_initialized = True
            self.logger.info("✅ 讯飞ASR服务初始化成功")
            return True
        else:
            self.logger.error("❌ 讯飞ASR服务初始化失败")
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
                "text": "",
                "confidence": 0.0,
                "words": []
            }
        
        # 获取或创建会话适配器
        session_key = session_id or "default"
        
        if session_key not in self._session_adapters:
            adapter = IFlyTekASRAdapter(self.config)
            await adapter.connect()
            self._session_adapters[session_key] = adapter
        
        adapter = self._session_adapters[session_key]
        
        # 转写音频（默认非最后一帧）
        result = await adapter.transcribe_audio(
            audio_data,
            session_id=session_id,
            is_last=False
        )
        return result
    
    async def transcribe_file(
        self,
        audio_file_path: str,
        *,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        转写音频文件（兼容SenseVoice接口）
        
        自动将音频转换为PCM格式后转写。
        
        Args:
            audio_file_path: 音频文件路径（支持MP4/MP3/WAV等格式）
            session_id: 会话ID
        
        Returns:
            兼容SenseVoice格式的结果
        """
        from pathlib import Path
        
        if not self.is_initialized:
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "words": [],
                "error": "服务未初始化"
            }
        
        audio_path = Path(audio_file_path)
        if not audio_path.exists():
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "words": [],
                "error": f"文件不存在: {audio_file_path}"
            }
        
        try:
            # 转换为PCM格式
            from server.app.utils.audio_converter import AudioConverter
            pcm_file_path = AudioConverter.convert_to_pcm(str(audio_path))
            
            # 读取PCM文件内容
            pcm_data = Path(pcm_file_path).read_bytes()
            self.logger.info(f"PCM文件大小: {len(pcm_data)} 字节")
            
            # 创建独立的适配器用于文件转写
            adapter = IFlyTekASRAdapter(self.config)
            success = await adapter.connect()
            
            if not success:
                return {
                    "success": False,
                    "text": "",
                    "confidence": 0.0,
                    "words": [],
                    "error": "连接讯飞服务失败"
                }
            
            try:
                # 转写（标记为最后一帧）
                result = await adapter.transcribe_audio(
                    pcm_data,
                    session_id=session_id,
                    is_last=True
                )
                return result
            finally:
                await adapter.disconnect()
                # 清理临时PCM文件
                try:
                    Path(pcm_file_path).unlink(missing_ok=True)
                except Exception:
                    pass
                
        except Exception as e:
            self.logger.error(f"转写文件失败: {e}")
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "words": [],
                "error": str(e)
            }
    
    async def close_session(self, session_id: Optional[str] = None):
        """关闭会话"""
        session_key = session_id or "default"
        
        if session_key in self._session_adapters:
            adapter = self._session_adapters[session_key]
            await adapter.disconnect()
            del self._session_adapters[session_key]
            self.logger.info(f"已关闭会话: {session_key}")
    
    async def cleanup(self):
        """清理资源"""
        # 关闭所有会话
        for adapter in self._session_adapters.values():
            await adapter.disconnect()
        
        self._session_adapters.clear()
        self.is_initialized = False
        self.logger.info("讯飞ASR服务已清理")
    
    def get_model_info(self) -> Dict[str, Any]:
        """返回模型信息（兼容SenseVoice接口）"""
        return {
            "backend": "xunfei",
            "model_id": "ast_v1",
            "model_name": "Xunfei RealTime ASR (Large Model)",
            "provider": "iFlytek",
            "initialized": self.is_initialized,
        }

