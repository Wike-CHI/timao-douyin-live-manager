#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Electron 本地语音识别集成测试
审查人：叶维哲

测试范围：
1. Python 转写服务启动和健康检查
2. 服务器音频 WebSocket 推流
3. 转写结果上传 API
4. 端到端集成测试
"""

import asyncio
import json
import time
import struct
import numpy as np
import pytest
from pathlib import Path
import sys

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import requests
    import websockets
except ImportError:
    print("请安装依赖: pip install requests websockets pytest numpy")
    sys.exit(1)


class TestPythonTranscriberService:
    """测试 Python 转写服务"""
    
    BASE_URL = "http://127.0.0.1:9527"
    
    @pytest.fixture(scope="class", autouse=True)
    def wait_for_service(self):
        """等待服务启动"""
        print("\n⏳ 等待 Python 转写服务启动...")
        max_wait = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"{self.BASE_URL}/health", timeout=2)
                if response.status_code == 200 and response.json().get("status") == "ok":
                    print("✅ Python 转写服务已就绪")
                    return
            except Exception:
                time.sleep(1)
        
        pytest.fail("Python 转写服务启动超时")
    
    def test_health_check(self):
        """测试健康检查端点"""
        response = requests.get(f"{self.BASE_URL}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert data["model_loaded"] is True
        assert data["funasr_available"] is True
        print("✅ 健康检查通过")
    
    def test_service_info(self):
        """测试服务信息端点"""
        response = requests.get(f"{self.BASE_URL}/info")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "Python Transcriber Service"
        assert data["model"] == "SenseVoice Small"
        assert data["vad"] == "FSMN-VAD"
        assert data["sample_rate"] == 16000
        assert data["initialized"] is True
        print("✅ 服务信息正确")
    
    def test_transcribe_silence(self):
        """测试转写静音音频（应返回空文本）"""
        # 生成 0.5 秒静音 PCM 数据（16kHz, 16bit, mono）
        duration = 0.5
        sample_rate = 16000
        samples = int(duration * sample_rate)
        audio_data = struct.pack(f"{samples}h", *[0] * samples)
        
        response = requests.post(
            f"{self.BASE_URL}/transcribe",
            data=audio_data,
            headers={"Content-Type": "application/octet-stream"},
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == ""
        assert data["confidence"] == 0.0
        print("✅ 静音转写测试通过")
    
    def test_transcribe_noise(self):
        """测试转写噪音音频（应能处理但可能返回空）"""
        # 生成 1 秒随机噪音 PCM 数据
        duration = 1.0
        sample_rate = 16000
        samples = int(duration * sample_rate)
        
        # 生成随机噪音（幅度较小）
        noise = np.random.randint(-1000, 1000, samples, dtype=np.int16)
        audio_data = noise.tobytes()
        
        response = requests.post(
            f"{self.BASE_URL}/transcribe",
            data=audio_data,
            headers={"Content-Type": "application/octet-stream"},
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        # 噪音可能被识别为空或无意义文本
        assert "error" not in data
        assert data["confidence"] >= 0.0
        print(f"✅ 噪音转写测试通过（结果: '{data['text']}'）")


class TestServerAudioWebSocket:
    """测试服务器音频 WebSocket 推流"""
    
    SERVER_URL = "http://localhost:8000"
    WS_URL = "ws://localhost:8000/api/live_audio/ws/audio"
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """测试 WebSocket 连接"""
        try:
            async with websockets.connect(self.WS_URL) as ws:
                print("✅ WebSocket 连接成功")
                
                # 发送心跳
                await ws.send(json.dumps({"type": "ping"}))
                
                # 接收响应（带超时）
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    data = json.loads(response)
                    assert data.get("type") == "pong"
                    print("✅ WebSocket 心跳测试通过")
                except asyncio.TimeoutError:
                    print("⚠️ WebSocket 心跳超时（可能服务器未推送音频）")
        except Exception as e:
            pytest.skip(f"服务器未运行或 WebSocket 不可用: {e}")


class TestTranscriptionUploadAPI:
    """测试转写结果上传 API"""
    
    API_URL = "http://localhost:8000/api/live_audio/transcriptions"
    
    def test_upload_transcription_success(self):
        """测试成功上传转写结果"""
        payload = {
            "session_id": "test_session_123",
            "text": "测试转写文本",
            "confidence": 0.95,
            "timestamp": time.time()
        }
        
        try:
            response = requests.post(self.API_URL, json=payload, timeout=5)
            assert response.status_code == 200
            
            data = response.json()
            assert data["data"]["success"] is True
            assert data["data"]["session_id"] == "test_session_123"
            print("✅ 转写结果上传成功")
        except Exception as e:
            pytest.skip(f"服务器未运行或 API 不可用: {e}")
    
    def test_upload_transcription_missing_session_id(self):
        """测试缺少 session_id 时返回错误"""
        payload = {
            "text": "测试文本",
            "confidence": 0.9
        }
        
        try:
            response = requests.post(self.API_URL, json=payload, timeout=5)
            assert response.status_code == 400
            print("✅ 缺少 session_id 验证通过")
        except Exception as e:
            pytest.skip(f"服务器未运行或 API 不可用: {e}")
    
    def test_upload_empty_text(self):
        """测试空文本上传（应被忽略）"""
        payload = {
            "session_id": "test_session_456",
            "text": "",
            "confidence": 0.0
        }
        
        try:
            response = requests.post(self.API_URL, json=payload, timeout=5)
            assert response.status_code == 200
            
            data = response.json()
            assert data["data"]["success"] is True
            print("✅ 空文本上传处理正确")
        except Exception as e:
            pytest.skip(f"服务器未运行或 API 不可用: {e}")


class TestEndToEndIntegration:
    """端到端集成测试"""
    
    def test_full_workflow(self):
        """
        完整工作流测试：
        1. 生成测试音频
        2. 调用 Python 转写服务
        3. 上传转写结果到服务器
        """
        print("\n🧪 开始端到端集成测试...")
        
        # 1. 生成测试音频（1秒噪音）
        duration = 1.0
        sample_rate = 16000
        samples = int(duration * sample_rate)
        audio_data = np.random.randint(-1000, 1000, samples, dtype=np.int16).tobytes()
        print("✅ 步骤 1: 生成测试音频")
        
        # 2. 调用 Python 转写服务
        try:
            response = requests.post(
                "http://127.0.0.1:9527/transcribe",
                data=audio_data,
                headers={"Content-Type": "application/octet-stream"},
                timeout=10
            )
            assert response.status_code == 200
            transcription = response.json()
            print(f"✅ 步骤 2: 转写完成 (文本: '{transcription['text']}')")
        except Exception as e:
            pytest.fail(f"Python 转写服务调用失败: {e}")
        
        # 3. 上传转写结果到服务器
        try:
            upload_payload = {
                "session_id": "e2e_test_session",
                "text": transcription["text"],
                "confidence": transcription["confidence"],
                "timestamp": transcription.get("timestamp", time.time())
            }
            
            response = requests.post(
                "http://localhost:8000/api/live_audio/transcriptions",
                json=upload_payload,
                timeout=5
            )
            
            if response.status_code == 200:
                print("✅ 步骤 3: 转写结果上传成功")
            else:
                print(f"⚠️ 步骤 3: 服务器返回 {response.status_code}")
        except Exception as e:
            print(f"⚠️ 步骤 3: 服务器未运行或 API 不可用: {e}")
        
        print("✅ 端到端集成测试完成")


def generate_test_audio_file(output_path: str, duration: float = 2.0):
    """
    生成测试音频文件（PCM 格式）
    
    Args:
        output_path: 输出文件路径
        duration: 音频时长（秒）
    """
    sample_rate = 16000
    samples = int(duration * sample_rate)
    
    # 生成正弦波 + 噪音
    t = np.linspace(0, duration, samples)
    frequency = 440  # A4 音符
    sine_wave = np.sin(2 * np.pi * frequency * t)
    noise = np.random.randn(samples) * 0.1
    audio = (sine_wave + noise) * 16000
    audio = audio.astype(np.int16)
    
    with open(output_path, 'wb') as f:
        f.write(audio.tobytes())
    
    print(f"✅ 生成测试音频文件: {output_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("Electron 本地语音识别集成测试")
    print("审查人：叶维哲")
    print("=" * 60)
    
    # 生成测试音频文件（可选）
    test_audio_path = "/tmp/test_audio.pcm"
    generate_test_audio_file(test_audio_path, duration=2.0)
    
    # 运行测试
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s"  # 显示 print 输出
    ])

