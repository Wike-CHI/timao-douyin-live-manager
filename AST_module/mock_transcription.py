"""Fallback transcription generator used when SenseVoice cannot start."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import AsyncGenerator

from .ast_service import TranscriptionResult

logger = logging.getLogger(__name__)


@dataclass
class MockTranscriptionGenerator:
    chunk_duration: float = 1.0

    async def stream(self) -> AsyncGenerator[TranscriptionResult, None]:
        phrases = [
            "模拟转录数据，SenseVoice 未初始化成功。",
            "请检查依赖安装、麦克风权限或模型下载。",
            "此数据仅用于占位，不代表真实语音。",
        ]
        while True:
            ts = time.time()
            for text in phrases:
                yield TranscriptionResult(
                    text=text,
                    confidence=0.0,
                    timestamp=ts,
                    duration=self.chunk_duration,
                    is_final=True,
                )
                await asyncio.sleep(self.chunk_duration)
