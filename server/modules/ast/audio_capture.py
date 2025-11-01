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
    """音频配置 - 优化参数以提高人声检测和背景音乐抑制"""
    sample_rate: int = 16000  # SenseVoice 推荐采样率
    channels: int = 1         # 单声道
    chunk_size: int = 1024    # 每次读取的帧数
    format: int = pyaudio.paInt16  # 16位深度
    input_device_index: Optional[int] = None
    # 降噪与电平控制 - 优化参数
    enable_denoise: bool = True
    denoise_backend: str = "spectral"   # 使用频谱门限降噪，更好抑制背景音乐
    denoise_level: str = "high"         # 提高降噪等级
    enable_agc: bool = True             # 自动增益（自动控制响度）
    target_rms: float = 0.08            # 提高目标RMS，增强人声

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
    """音频预处理器
    - 将输入音频统一到目标采样率与单声道。
    - 明确区分输入采样率/通道，避免因为默认 44.1k 假设导致的错误重采样。
    """
    
    def __init__(
        self,
        target_sample_rate: int = 16000,
        source_sample_rate: int = 16000,
        source_channels: int = 1,
        enable_denoise: bool = True,
        denoise_backend: str = "auto",
        denoise_level: str = "moderate",
        enable_agc: bool = True,
        target_rms: float = 0.05,
    ):
        self.target_sample_rate = target_sample_rate
        self.source_sample_rate = source_sample_rate
        self.source_channels = max(1, int(source_channels))
        self.logger = logging.getLogger(__name__)
        # 降噪/AGC 配置
        self.enable_denoise = enable_denoise
        self.enable_agc = enable_agc
        self._target_rms = float(max(1e-4, min(0.9, target_rms)))
        self._denoise_backend = denoise_backend
        self._denoise_level = denoise_level
        # 内部状态：用于频谱门限与 AGC 的平滑
        self._noise_mag_est: Optional[np.ndarray] = None
        self._prev_gain: float = 1.0
        self._agc_smooth: float = 0.9  # 0.9 越平滑、响应越慢
        # 探测可用的降噪库
        self._use_rnnoise = False
        self._use_webrtc = False
        if self.enable_denoise and denoise_backend in ("auto", "rnnoise"):
            try:
                import rnnoise  # type: ignore
                self._rnnoise = rnnoise.RNNoise()
                self._use_rnnoise = True
                if self._denoise_backend == "auto":
                    self._denoise_backend = "rnnoise"
                self.logger.info("降噪后端: RNNoise")
            except Exception:
                pass
        if self.enable_denoise and not self._use_rnnoise and denoise_backend in ("auto", "webrtc"):
            try:
                import webrtc_audio_processing as ap  # type: ignore
                # 初始化轻量 NS；AEC 需要回放路由支持，这里不启用
                self._ap = ap.AudioProcessing(ns_level=self._webrtc_ns_level(denoise_level), enable_ns=True)
                self._use_webrtc = True
                if self._denoise_backend == "auto":
                    self._denoise_backend = "webrtc"
                self.logger.info("降噪后端: WebRTC-NS")
            except Exception:
                pass
        if self.enable_denoise and not (self._use_rnnoise or self._use_webrtc):
            # 回退到频谱门限
            if self._denoise_backend == "off":
                self.enable_denoise = False
            else:
                if self._denoise_backend == "auto":
                    self._denoise_backend = "spectral"
                self.logger.info("降噪后端: Spectral-gate")

    @staticmethod
    def _webrtc_ns_level(level: str) -> int:
        # 将字符串等级映射到 webrtc 音频处理库的设定（0~3）
        lv = (level or "moderate").lower()
        return {"low": 1, "moderate": 2, "high": 3}.get(lv, 2)
    
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
    
    def convert_to_16khz_mono(self, audio_data: bytes) -> bytes:
        """将输入音频转换为目标采样率的单声道。
        使用初始化时提供的 source_sample_rate/source_channels 作为真实输入格式。
        """
        try:
            # 转换为numpy数组
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # 如果是多通道，按通道均值转单声道
            if self.source_channels > 1:
                total_frames = len(audio_array) // self.source_channels
                if total_frames > 0:
                    multi = audio_array[: total_frames * self.source_channels].reshape(
                        -1, self.source_channels
                    )
                    mono = np.mean(multi, axis=1).astype(np.int16)
                else:
                    mono = audio_array
            else:
                mono = audio_array
            
            # 重采样到16kHz
            if self.source_sample_rate != self.target_sample_rate:
                # 简单的重采样 (线性插值)
                resample_ratio = self.target_sample_rate / float(self.source_sample_rate)
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
        """应用降噪，自动选择后端。
        - RNNoise（若可用）：质量高，延迟低，但依赖 48k 帧；本实现做近似处理。
        - WebRTC-NS（若可用）：稳健、轻量。
        - 频谱门限：零依赖的基础方案。
        - 简单门限（gate）：最基础的保底方案。
        """
        if not self.enable_denoise:
            return audio_data

        try:
            if self._use_rnnoise and self._denoise_backend == "rnnoise":
                return self._denoise_with_rnnoise(audio_data)
            if self._use_webrtc and self._denoise_backend == "webrtc":
                return self._denoise_with_webrtc(audio_data)
            if self._denoise_backend == "spectral":
                return self._denoise_with_spectral_gate(audio_data)
            # 回退到简单门限
            return self._denoise_with_gate(audio_data)
        except Exception as e:
            self.logger.error(f"噪声降低失败: {e}")
            return audio_data

    def _denoise_with_gate(self, audio_data: bytes) -> bytes:
        audio = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        if audio.size == 0:
            return audio_data
        thr_ratio = {"low": 0.2, "moderate": 0.1, "high": 0.05}.get(self._denoise_level, 0.1)
        thr = max(50.0, float(np.max(np.abs(audio))) * thr_ratio)
        mask = np.abs(audio) > thr
        den = (audio * mask).astype(np.int16)
        return den.tobytes()

    def _denoise_with_webrtc(self, audio_data: bytes) -> bytes:
        # webrtc 期望 float32 [-1,1]，但该 Python 封装支持 16k 单声道处理
        import webrtc_audio_processing as ap  # type: ignore
        proc: ap.AudioProcessing = self._ap  # type: ignore[attr-defined]
        # 将短整型转 [-1,1]
        x = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        # WebRTC 库以帧为单位处理，采用 10ms 步长
        sr = self.target_sample_rate
        frame = int(sr * 0.01)
        out = np.empty_like(x)
        for i in range(0, len(x), frame):
            seg = x[i : i + frame]
            if len(seg) < frame:
                seg = np.pad(seg, (0, frame - len(seg)))
            y = proc.process_stream(seg.reshape(-1, 1), sr)
            out[i : i + frame] = y[: len(seg), 0]
        out = np.clip(out, -1.0, 1.0)
        return (out * 32767.0).astype(np.int16).tobytes()

    def _denoise_with_rnnoise(self, audio_data: bytes) -> bytes:
        # RNNoise 以 48k、每帧 480 样本为最佳；此处采用简单重采样近似。
        import rnnoise  # type: ignore
        x16 = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        if x16.size == 0:
            return audio_data
        # 上采样至 48k（线性插值），分帧处理，再下采样回 16k
        up_ratio = 48000.0 / float(self.target_sample_rate)
        up_len = int(len(x16) * up_ratio)
        x48 = np.interp(
            np.linspace(0, len(x16) - 1, up_len),
            np.arange(len(x16)),
            x16,
        )
        den48 = np.empty_like(x48)
        frame = 480
        st = self._rnnoise  # type: ignore[attr-defined]
        for i in range(0, len(x48), frame):
            seg = x48[i : i + frame]
            if len(seg) < frame:
                seg = np.pad(seg, (0, frame - len(seg)))
            y = st.process_frame(seg)
            den48[i : i + frame] = y[: len(seg)]
        # 下采样回原采样率
        down_len = len(x16)
        den16 = np.interp(
            np.linspace(0, len(den48) - 1, down_len),
            np.arange(len(den48)),
            den48,
        )
        den16 = np.clip(den16, -32767.0, 32767.0).astype(np.int16)
        return den16.tobytes()

    def _denoise_with_spectral_gate(self, audio_data: bytes) -> bytes:
        # 简化的单帧频谱门限，适合实时处理；为减少计算，仅做单帧 FFT。
        x = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        if x.size == 0:
            return audio_data
        # 汉宁窗，避免频谱泄露
        win = np.hanning(len(x)).astype(np.float32)
        xw = x * win
        X = np.fft.rfft(xw)
        mag = np.abs(X)
        # 初始化/更新噪声谱估计（滑动最小值法的近似）
        if self._noise_mag_est is None or self._noise_mag_est.shape != mag.shape:
            self._noise_mag_est = mag.copy()
        else:
            # 平滑更新：对较小的谱分量靠近
            self._noise_mag_est = np.minimum(
                self._noise_mag_est * 0.98 + mag * 0.02,
                mag,
            )
        # 门限：k 倍噪声谱
        k = {"low": 1.2, "moderate": 1.5, "high": 2.0}.get(self._denoise_level, 1.5)
        thr = self._noise_mag_est * k
        gain = np.clip((mag - thr) / (mag + 1e-6), 0.0, 1.0)
        # 轻微保留：避免完全静音造成金属音
        gain = 0.1 + 0.9 * gain
        Y = X * gain
        y = np.fft.irfft(Y)
        # 反窗并裁剪
        y = y / (win.mean() + 1e-6)
        y = np.clip(y, -32767.0, 32767.0).astype(np.int16)
        return y.tobytes()
    
    def normalize_audio(self, audio_data: bytes) -> bytes:
        """自动增益控制（AGC）：将片段 RMS 拉向目标值，避免时大时小。
        使用平滑的增益，降低听感突变。
        """
        if not self.enable_agc:
            return audio_data
        try:
            x = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
            if x.size == 0:
                return audio_data
            rms = float(np.sqrt(np.mean((x / 32768.0) ** 2)) + 1e-8)
            desired = self._target_rms
            gain = desired / rms
            # 限制瞬时增益范围，避免爆音
            gain = float(np.clip(gain, 0.5, 8.0))
            # 平滑
            self._prev_gain = self._agc_smooth * self._prev_gain + (1 - self._agc_smooth) * gain
            y = x * self._prev_gain
            y = np.clip(y, -32767.0, 32767.0).astype(np.int16)
            return y.tobytes()
        except Exception as e:
            self.logger.error(f"音频标准化失败: {e}")
            return audio_data
    
    def process_audio_chunk(self, audio_data: bytes) -> bytes:
        """处理音频块 - 完整的预处理流水线"""
        if not self.validate_audio_format(audio_data):
            return b''
        
        # 1. 格式转换（基于真实输入采样率/通道）
        processed = self.convert_to_16khz_mono(audio_data)
        
        # 2. 噪声降低
        processed = self.apply_noise_reduction(processed)
        
        # 3. 自动增益（响度）
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
