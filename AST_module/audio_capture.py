# -*- coding: utf-8 -*-
"""
音频采集和处理组件
负责麦克风音频采集、格式转换和预处理
"""

import asyncio
import pyaudio
import numpy as np
import wave
import io
import logging
from typing import Optional, AsyncGenerator, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class AudioConfig:
    """音频配置"""
    sample_rate: int = 16000  # SenseVoice 推荐采样率
    channels: int = 1         # 单声道
    chunk_size: int = 1024    # 每次读取的帧数
    format: int = pyaudio.paInt16  # 16位深度
    input_device_index: Optional[int] = None

class AudioCapture:
    """音频采集器"""
    
    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.audio: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        self.is_recording = False
        self.logger = logging.getLogger(__name__)
    
    def initialize(self) -> bool:
        """初始化音频系统"""
        try:
            self.audio = pyaudio.PyAudio()
            
            # 检查可用的音频设备
            self._list_audio_devices()
            
            return True
        except Exception as e:
            self.logger.error(f"音频系统初始化失败: {e}")
            return False
    
    def _list_audio_devices(self):
        """列出可用的音频设备"""
        if self.audio is None:
            return
        
        self.logger.info("可用音频设备:")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            max_input_channels = info.get('maxInputChannels')
            if isinstance(max_input_channels, int) and max_input_channels > 0:
                self.logger.info(f"  {i}: {info['name']} (输入通道: {max_input_channels})")

    def list_audio_devices(self):
        """获取可用音频设备列表"""
        if self.audio is None:
            return []
        
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            max_input_channels = info.get('maxInputChannels')
            if isinstance(max_input_channels, int) and max_input_channels > 0:
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'maxInputChannels': max_input_channels
                })
        
        return devices
    
    async def start_recording(self) -> bool:
        """开始录音"""
        try:
            if self.is_recording:
                return True
            
            if self.audio is None:
                return False
            
            # 打开音频流
            self.stream = self.audio.open(
                format=self.config.format,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                input_device_index=self.config.input_device_index,
                frames_per_buffer=self.config.chunk_size
            )
            
            self.is_recording = True
            self.logger.info("✅ 音频录制已开始")
            return True
            
        except Exception as e:
            self.logger.error(f"开始录音失败: {e}")
            return False
    
    async def stop_recording(self):
        """停止录音"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        self.is_recording = False
        self.logger.info("音频录制已停止")
    
    async def get_audio_stream(self) -> AsyncGenerator[bytes, None]:
        """获取音频流"""
        if not self.is_recording or not self.stream:
            raise RuntimeError("音频录制未开始")
        
        try:
            while self.is_recording:
                # 读取音频数据
                data = self.stream.read(self.config.chunk_size, exception_on_overflow=False)
                yield data
                
                # 让出控制权
                await asyncio.sleep(0.001)
                
        except Exception as e:
            self.logger.error(f"音频流读取失败: {e}")
            raise
    
    def cleanup(self):
        """清理资源"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if self.audio:
            self.audio.terminate()
        
        self.logger.info("音频系统已清理")

class AudioProcessor:
    """音频预处理器"""
    
    def __init__(self, target_sample_rate: int = 16000):
        self.target_sample_rate = target_sample_rate
        self.logger = logging.getLogger(__name__)
    
    def validate_audio_format(self, audio_data: bytes) -> bool:
        """验证音频格式"""
        try:
            # 检查数据长度
            if len(audio_data) == 0:
                return False
            
            # 检查是否为有效的音频数据
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # 检查是否有音频信号 (非全零)
            return not np.all(audio_array == 0)
            
        except Exception as e:
            self.logger.error(f"音频格式验证失败: {e}")
            return False
    
    def convert_to_16khz_mono(self, audio_data: bytes, original_rate: int = 44100) -> bytes:
        """转换为16kHz单声道格式"""
        try:
            # 转换为numpy数组
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # 如果是立体声，转换为单声道
            if len(audio_array) % 2 == 0:
                # 假设是立体声
                stereo = audio_array.reshape(-1, 2)
                mono = np.mean(stereo, axis=1).astype(np.int16)
            else:
                mono = audio_array
            
            # 重采样到16kHz
            if original_rate != self.target_sample_rate:
                # 简单的重采样 (线性插值)
                resample_ratio = self.target_sample_rate / original_rate
                new_length = int(len(mono) * resample_ratio)
                resampled = np.interp(
                    np.linspace(0, len(mono) - 1, new_length),
                    np.arange(len(mono)),
                    mono
                ).astype(np.int16)
            else:
                resampled = mono
            
            return resampled.tobytes()
            
        except Exception as e:
            self.logger.error(f"音频格式转换失败: {e}")
            return audio_data
    
    def apply_noise_reduction(self, audio_data: bytes) -> bytes:
        """应用噪声降低"""
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # 简单的噪声门限制
            threshold = np.max(np.abs(audio_array)) * 0.1
            mask = np.abs(audio_array) > threshold
            
            # 应用掩码
            processed = audio_array * mask
            
            return processed.astype(np.int16).tobytes()
            
        except Exception as e:
            self.logger.error(f"噪声降低失败: {e}")
            return audio_data
    
    def normalize_audio(self, audio_data: bytes) -> bytes:
        """音频标准化"""
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # 标准化到[-32767, 32767]范围
            max_val = np.max(np.abs(audio_array))
            if max_val > 0:
                normalized = (audio_array / max_val * 32767).astype(np.int16)
            else:
                normalized = audio_array
            
            return normalized.tobytes()
            
        except Exception as e:
            self.logger.error(f"音频标准化失败: {e}")
            return audio_data
    
    def process_audio_chunk(self, audio_data: bytes) -> bytes:
        """处理音频块 - 完整的预处理流水线"""
        if not self.validate_audio_format(audio_data):
            return b''
        
        # 1. 格式转换
        processed = self.convert_to_16khz_mono(audio_data)
        
        # 2. 噪声降低
        processed = self.apply_noise_reduction(processed)
        
        # 3. 标准化
        processed = self.normalize_audio(processed)
        
        return processed
    
    def save_audio_to_file(self, audio_data: bytes, filepath: str):
        """保存音频到文件 (用于调试)"""
        try:
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(1)  # 单声道
                wf.setsampwidth(2)  # 16位 = 2字节
                wf.setframerate(self.target_sample_rate)
                wf.writeframes(audio_data)
            
            self.logger.info(f"音频已保存到: {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存音频文件失败: {e}")

class AudioBuffer:
    """音频缓冲区"""
    
    def __init__(self, max_duration: float = 10.0, sample_rate: int = 16000):
        self.max_duration = max_duration
        self.sample_rate = sample_rate
        self.max_size = int(max_duration * sample_rate * 2)  # 2字节每样本
        self.buffer = bytearray()
        self.lock = asyncio.Lock()
    
    async def append(self, audio_data: bytes):
        """添加音频数据"""
        async with self.lock:
            self.buffer.extend(audio_data)
            
            # 如果超过最大长度，移除旧数据
            if len(self.buffer) > self.max_size:
                excess = len(self.buffer) - self.max_size
                self.buffer = self.buffer[excess:]
    
    async def get_recent(self, duration: float) -> bytes:
        """获取最近的音频数据"""
        async with self.lock:
            size = int(duration * self.sample_rate * 2)
            if len(self.buffer) >= size:
                return bytes(self.buffer[-size:])
            else:
                return bytes(self.buffer)
    
    async def clear(self):
        """清空缓冲区"""
        async with self.lock:
            self.buffer.clear()

if __name__ == "__main__":
    # 测试代码
    async def test_audio():
        # 初始化音频采集
        capture = AudioCapture()
        if not capture.initialize():
            print("❌ 音频系统初始化失败")
            return
        
        processor = AudioProcessor()
        
        try:
            # 开始录音
            if await capture.start_recording():
                print("✅ 开始录音测试 (5秒)")
                
                # 录制5秒
                chunks = []
                async for chunk in capture.get_audio_stream():
                    processed_chunk = processor.process_audio_chunk(chunk)
                    if processed_chunk:
                        chunks.append(processed_chunk)
                    
                    if len(chunks) >= 50:  # 约5秒
                        break
                
                # 保存测试文件
                if chunks:
                    all_audio = b''.join(chunks)
                    processor.save_audio_to_file(all_audio, "test_audio.wav")
                    print(f"✅ 录制完成，共 {len(all_audio)} 字节")
                
            await capture.stop_recording()
            
        finally:
            capture.cleanup()
    
    import asyncio
    asyncio.run(test_audio())
