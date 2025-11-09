#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
讯飞语音识别服务
WebSocket 实时语音转写
"""

import asyncio
import base64
import hashlib
import hmac
import json
import time
from datetime import datetime
from typing import Optional
from urllib.parse import quote, urlencode

import websockets
from loguru import logger


class XfyunASR:
    """讯飞语音识别（实时转写）"""
    
    def __init__(self, app_id: str, api_key: str, api_secret: str):
        """
        初始化
        
        Args:
            app_id: 讯飞APPID
            api_key: APIKey
            api_secret: APISecret
        """
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.ws_url = "wss://office-api-ast-dx.iflyaisol.com/ast/communicate/v1"
        
    def _generate_signature(self, params: dict) -> str:
        """
        生成签名
        
        Args:
            params: 请求参数字典（不含signature）
            
        Returns:
            签名字符串
        """
        # 1. 参数按key升序排序
        sorted_params = sorted(params.items())
        
        # 2. URL编码并拼接
        base_string = "&".join([
            f"{quote(k)}={quote(str(v))}" 
            for k, v in sorted_params
        ])
        
        # 3. HMAC-SHA1加密
        signature_bytes = hmac.new(
            self.api_secret.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        # 4. Base64编码
        signature = base64.b64encode(signature_bytes).decode('utf-8')
        
        return signature
    
    def _build_ws_url(self, uuid: str = "default_user") -> str:
        """
        构建WebSocket连接URL
        
        Args:
            uuid: 用户标识
            
        Returns:
            完整的WebSocket URL
        """
        # 当前UTC时间（ISO 8601格式）
        utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+0000")
        
        # 请求参数
        params = {
            "appId": self.app_id,
            "accessKeyId": self.api_key,
            "uuid": uuid,
            "utc": utc,
            "audio_encode": "pcm_s16le",  # PCM 16k16bit
            "lang": "autodialect",  # 中英+202种方言自动识别
            "samplerate": "16000",  # 采样率16k
        }
        
        # 生成签名
        signature = self._generate_signature(params)
        params["signature"] = signature
        
        # 构建完整URL
        url = f"{self.ws_url}?{urlencode(params, quote_via=quote)}"
        
        return url
    
    async def transcribe_audio_file(self, audio_path: str, uuid: str = "default_user") -> str:
        """
        转写音频文件
        
        Args:
            audio_path: 音频文件路径（PCM格式，16k采样率）
            uuid: 用户标识
            
        Returns:
            转写文本结果
        """
        # 读取音频文件
        with open(audio_path, "rb") as f:
            audio_data = f.read()
        
        # 调用实时转写
        result = await self.transcribe_audio(audio_data, uuid)
        return result
    
    async def transcribe_audio(self, audio_data: bytes, uuid: str = "default_user") -> str:
        """
        实时转写音频数据
        
        Args:
            audio_data: 音频二进制数据（PCM格式，16k采样率）
            uuid: 用户标识
            
        Returns:
            转写文本结果
        """
        url = self._build_ws_url(uuid)
        
        try:
            async with websockets.connect(url) as ws:
                logger.info(f"WebSocket连接成功: {uuid}")
                
                # 接收握手响应
                response = await ws.recv()
                result = json.loads(response)
                
                # 检查握手响应（msg_type=action, data.action=started）
                if result.get("msg_type") == "action" and result.get("data", {}).get("action") == "started":
                    logger.info("握手成功，开始发送音频")
                else:
                    logger.error(f"握手失败: {result}")
                    return ""
                
                # 发送音频数据（每40ms发送1280字节）
                chunk_size = 1280  # 16k采样率，16bit，单声道，40ms = 1280字节
                total_chunks = len(audio_data) // chunk_size + (1 if len(audio_data) % chunk_size else 0)
                
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i + chunk_size]
                    await ws.send(chunk)
                    await asyncio.sleep(0.04)  # 40ms间隔
                    
                    if (i // chunk_size) % 25 == 0:  # 每秒日志一次
                        logger.debug(f"发送进度: {i // chunk_size + 1}/{total_chunks}")
                
                # 发送结束标识
                session_id = f"session_{int(time.time())}"
                end_frame = json.dumps({"end": True, "sessionId": session_id})
                await ws.send(end_frame)
                logger.info("音频发送完成，等待最终结果")
                
                # 接收转写结果
                transcription_result = []
                
                while True:
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=10.0)
                        result = json.loads(response)
                        
                        # 解析转写结果
                        if result.get("msg_type") == "result" and result.get("res_type") == "asr":
                            data = result.get("data", {})
                            cn = data.get("cn", {})
                            st = cn.get("st", {})
                            rt_list = st.get("rt", [])
                            
                            for rt in rt_list:
                                for word_seg in rt.get("ws", []):
                                    for cw in word_seg.get("cw", []):
                                        word = cw.get("w", "")
                                        if word:
                                            transcription_result.append(word)
                            
                            # 检查是否为最后一帧
                            if data.get("ls", False):
                                logger.info("收到最后一帧结果")
                                break
                        
                        # 检查错误
                        elif result.get("msg_type") == "result" and result.get("res_type") == "frc":
                            logger.error(f"转写异常: {result.get('data', {}).get('desc')}")
                            break
                            
                    except asyncio.TimeoutError:
                        logger.warning("接收结果超时")
                        break
                
                # 返回完整转写文本
                full_text = "".join(transcription_result)
                logger.info(f"转写完成，文本长度: {len(full_text)}")
                return full_text
                
        except Exception as e:
            logger.error(f"转写失败: {e}", exc_info=True)
            return ""


# 使用示例
async def main():
    """测试示例"""
    import os
    
    # 从环境变量读取配置
    app_id = os.getenv("XFYUN_APPID", "3f3b2c39")
    api_key = os.getenv("XFYUN_API_KEY", "4cb3fb678a09e3072fb8889d840ef6a2")
    api_secret = os.getenv("XFYUN_API_SECRET", "MTg2ZTFlZjJlYWYyYzVjZWJhMmIyYzUz")
    
    # 初始化
    asr = XfyunASR(app_id, api_key, api_secret)
    
    # 测试音频（需要是PCM格式，16k采样率，16bit，单声道）
    # audio_path = "test.pcm"
    # result = await asr.transcribe_audio_file(audio_path)
    # print(f"转写结果: {result}")


if __name__ == "__main__":
    asyncio.run(main())

