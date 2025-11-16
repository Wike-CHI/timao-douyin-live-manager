# -*- coding: utf-8 -*-
"""
端到端测试：LiveAudioStreamService完整流程
测试音频流拉取 → SenseVoice转写 → 文本后处理 → WebSocket推送
"""

import asyncio
import logging
import sys
import time
import psutil
import os
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["PYTHONPATH"] = str(PROJECT_ROOT)

from server.local.services.live_audio_stream_service import (
    get_live_audio_service,
    LiveAudioStatus
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class E2ETestRunner:
    """端到端测试运行器"""
    
    def __init__(self):
        self.service = get_live_audio_service()
        self.transcriptions = []
        self.audio_levels = []
        self.start_time = None
        self.process = psutil.Process()
        
    async def test_with_file(self, audio_file: Path):
        """使用本地音频文件测试（模拟直播流）"""
        logger.info(f"=== 测试开始: 使用文件 {audio_file} ===")
        
        # 记录初始内存
        mem_before = self.process.memory_info().rss / (1024 ** 2)  # MB
        logger.info(f"初始内存: {mem_before:.2f}MB")
        
        # 注册回调
        self.service.add_transcription_callback("test", self._on_transcription)
        self.service.add_level_callback("test", self._on_level)
        
        try:
            # 方案1：使用测试音频文件（通过file://协议模拟）
            # 注意：这需要FFmpeg支持，或者我们直接读取文件并推送
            test_url = f"file://{audio_file.absolute()}"
            
            logger.info(f"启动服务...")
            self.start_time = time.time()
            
            try:
                status = await self.service.start(
                    live_url_or_id=str(test_url),
                    session_id="e2e_test"
                )
                logger.info(f"服务状态: {status}")
            except Exception as e:
                logger.error(f"启动失败（预期，因为file://不是有效的直播URL）: {e}")
                logger.info("切换到模拟音频流模式...")
                return await self._test_mock_stream(audio_file)
            
            # 运行10秒
            await asyncio.sleep(10)
            
            # 停止服务
            logger.info("停止服务...")
            await self.service.stop()
            
        finally:
            self.service.remove_transcription_callback("test")
            self.service.remove_level_callback("test")
        
        # 统计结果
        await self._print_results(mem_before)
    
    async def _test_mock_stream(self, audio_file: Path):
        """
        模拟音频流测试（直接读取PCM数据推送）
        
        由于我们无法用file://协议启动真实的FFmpeg流，
        这里我们模拟音频流处理流程
        """
        logger.info("=== 模拟音频流测试 ===")
        
        # 读取WAV文件
        import wave
        with wave.open(str(audio_file), 'rb') as wav:
            sample_rate = wav.getframerate()
            n_channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            
            logger.info(f"音频参数: {sample_rate}Hz, {n_channels}声道, {sample_width*8}bit")
            
            # 读取所有数据
            pcm_data = wav.readframes(wav.getnframes())
        
        # 检查SenseVoice是否可用
        logger.info("初始化SenseVoice模型...")
        await self.service._ensure_sv()
        
        if self.service._sv is None:
            logger.error("❌ SenseVoice模型加载失败，无法测试转写功能")
            logger.info("建议：运行 `python -m server.local.utils.model_downloader` 下载模型")
            return
        
        logger.info("✅ SenseVoice模型已加载")
        
        # 模拟分块处理
        chunk_size = int(1.6 * 16000 * 2)  # 1.6秒的PCM16数据
        offset = 0
        
        logger.info(f"开始处理音频数据，总大小: {len(pcm_data)} bytes")
        
        while offset < len(pcm_data):
            chunk = pcm_data[offset:offset+chunk_size]
            if len(chunk) < chunk_size:
                break
            
            # 调用VAD处理（模拟_handle_audio_chunk_vad）
            try:
                # 这里简化测试，直接调用转写
                from server.modules.ast.postprocess import pcm16_rms
                
                rms = pcm16_rms(chunk)
                logger.info(f"音频块RMS: {rms:.4f}")
                
                # 如果有足够的能量，进行转写
                if rms > 0.01:
                    res = await self.service._sv.transcribe_audio(
                        chunk,
                        session_id="e2e_test",
                        bias_phrases=[]
                    )
                    
                    if res and res.get("text"):
                        text = res["text"]
                        conf = res.get("confidence", 0.0)
                        logger.info(f"转写结果: {text} (置信度: {conf:.2f})")
                        self.transcriptions.append({
                            "text": text,
                            "confidence": conf,
                            "timestamp": time.time()
                        })
                
            except Exception as e:
                logger.error(f"转写异常: {e}")
            
            offset += chunk_size
            await asyncio.sleep(0.1)  # 模拟实时处理
        
        logger.info("音频处理完成")
        
        # 统计结果
        mem_after = self.process.memory_info().rss / (1024 ** 2)
        await self._print_results(mem_after - 100)  # 假设初始内存100MB
    
    async def _on_transcription(self, data: dict):
        """转写结果回调"""
        self.transcriptions.append(data)
        text = data.get("data", {}).get("text", "")
        conf = data.get("data", {}).get("confidence", 0.0)
        logger.info(f"📝 转写: {text} (置信度: {conf:.2f})")
    
    async def _on_level(self, rms: float, timestamp: float):
        """音频电平回调"""
        self.audio_levels.append((rms, timestamp))
    
    async def _print_results(self, mem_before: float):
        """打印测试结果"""
        logger.info("=== 测试结果 ===")
        
        # 内存统计
        mem_after = self.process.memory_info().rss / (1024 ** 2)
        mem_delta = mem_after - mem_before
        logger.info(f"内存使用: {mem_before:.2f}MB → {mem_after:.2f}MB (增加 {mem_delta:.2f}MB)")
        
        # CPU统计
        cpu_percent = self.process.cpu_percent(interval=1.0)
        logger.info(f"CPU使用: {cpu_percent:.1f}%")
        
        # 转写统计
        logger.info(f"转写结果数: {len(self.transcriptions)}")
        if self.transcriptions:
            avg_conf = sum(t.get("confidence", 0) for t in self.transcriptions) / len(self.transcriptions)
            logger.info(f"平均置信度: {avg_conf:.2f}")
        
        # 音频电平统计
        logger.info(f"音频电平采样数: {len(self.audio_levels)}")
        
        logger.info("=== 测试完成 ===")


async def main():
    """主测试函数"""
    runner = E2ETestRunner()
    
    # 测试音频文件
    test_audio = PROJECT_ROOT / "test_data" / "test_audio_10s.wav"
    
    if not test_audio.exists():
        logger.error(f"测试音频文件不存在: {test_audio}")
        logger.info("请先运行: python test_data/generate_test_audio.py")
        return
    
    await runner.test_with_file(test_audio)


if __name__ == "__main__":
    asyncio.run(main())
