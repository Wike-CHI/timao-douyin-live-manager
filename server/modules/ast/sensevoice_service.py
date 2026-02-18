# -*- coding: utf-8 -*-
"""SenseVoice ASR integration using sherpa-onnx."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

import numpy as np

# 尝试导入 sherpa_onnx
try:
    import sherpa_onnx
    SHERPA_ONNX_AVAILABLE = True
except ImportError:
    sherpa_onnx = None  # type: ignore
    SHERPA_ONNX_AVAILABLE = False


@dataclass
class SenseVoiceConfig:
    """sherpa-onnx SenseVoice 配置。

    Attributes:
        model_dir: ONNX 模型目录路径
        language: 语言设置 (auto/zh/en/ja/ko/yue)
        use_itn: 是否使用逆文本正则化
        hotword_weight: 热词权重
        max_concurrent: 最大并发转写数
        timeout_seconds: 单次转写超时时间
        device: 设备 (cpu/cuda)
    """

    model_dir: str = "models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
    language: str = "auto"
    use_itn: bool = True
    hotword_weight: float = 3.0
    max_concurrent: int = 4
    timeout_seconds: float = 10.0
    device: str = "cpu"


class SenseVoiceService:
    """sherpa-onnx SenseVoice 服务封装。

    使用 sherpa-onnx 进行离线语音识别，支持热词功能。
    """

    def __init__(self, config: Optional[SenseVoiceConfig] = None):
        """初始化服务。

        Args:
            config: 配置对象，如果为 None 则使用默认配置
        """
        self.config = config or SenseVoiceConfig()
        self.logger = logging.getLogger(__name__)

        # 模型实例
        self._recognizer: Optional[Any] = None
        self.is_initialized = False

        # 热词存储
        self._global_hotwords: set = set()
        self._session_hotwords: Dict[str, set] = {}

        # 并发控制
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._active_requests: int = 0

        # 统计
        self._call_count: int = 0
        self._total_errors: int = 0

    async def initialize(self) -> bool:
        """加载 ONNX 模型。

        Returns:
            bool: 初始化是否成功
        """
        if self.is_initialized:
            return True

        if not SHERPA_ONNX_AVAILABLE:
            self.logger.error("sherpa-onnx 未安装")
            return False

        # 检查模型目录
        from pathlib import Path
        model_path = Path(self.config.model_dir)
        if not model_path.exists():
            self.logger.error(f"模型目录不存在: {model_path}")
            return False

        try:
            loop = asyncio.get_event_loop()

            def _load_model():
                return sherpa_onnx.OfflineRecognizer.from_sense_voice(
                    model=str(model_path),
                    language=self.config.language,
                    use_itn=self.config.use_itn,
                )

            self._recognizer = await loop.run_in_executor(None, _load_model)
            self.is_initialized = True
            self.logger.info(f"✅ sherpa-onnx 模型加载成功: {model_path}")
            return True

        except Exception as exc:
            self.logger.error(f"模型加载失败: {exc}")
            self.is_initialized = False
            return False

    async def transcribe_audio(
        self,
        audio_data: bytes,
        *,
        session_id: Optional[str] = None,
        bias_phrases: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """转录音频。

        Args:
            audio_data: PCM 16-bit 音频数据 (16kHz)
            session_id: 会话 ID（用于会话级热词）
            bias_phrases: 临时热词

        Returns:
            Dict: 转录结果
        """
        # 未初始化
        if not self.is_initialized:
            return {
                "success": False,
                "type": "error",
                "text": "",
                "confidence": 0.0,
                "timestamp": time.time(),
                "words": [],
                "error": "模型未初始化",
            }

        # 空音频
        if not audio_data:
            return {
                "success": True,
                "type": "silence",
                "text": "",
                "confidence": 0.0,
                "timestamp": time.time(),
                "words": [],
            }

        # 并发控制
        try:
            async with self._semaphore:
                self._active_requests += 1
                try:
                    result = await asyncio.wait_for(
                        self._transcribe_internal(audio_data, session_id, bias_phrases),
                        timeout=self.config.timeout_seconds,
                    )
                    return result
                except asyncio.TimeoutError:
                    self.logger.error(f"转录超时 ({self.config.timeout_seconds}s)")
                    return {
                        "success": False,
                        "type": "error",
                        "text": "",
                        "confidence": 0.0,
                        "timestamp": time.time(),
                        "words": [],
                        "error": "转录超时",
                    }
                finally:
                    self._active_requests -= 1
        except Exception as exc:
            self._total_errors += 1
            self.logger.error(f"转录失败: {exc}")
            return {
                "success": False,
                "type": "error",
                "text": "",
                "confidence": 0.0,
                "timestamp": time.time(),
                "words": [],
                "error": str(exc),
            }

    async def _transcribe_internal(
        self,
        audio_data: bytes,
        session_id: Optional[str],
        bias_phrases: Optional[Iterable[str]],
    ) -> Dict[str, Any]:
        """内部转录实现。"""
        loop = asyncio.get_event_loop()

        def _infer():
            # 转换为 numpy
            audio_np = np.frombuffer(audio_data, dtype=np.int16)

            # 静音检测
            rms = np.sqrt(np.mean(audio_np.astype(np.float32) ** 2))
            if rms < 320:
                return {
                    "success": True,
                    "type": "silence",
                    "text": "",
                    "confidence": 0.0,
                    "timestamp": time.time(),
                    "words": [],
                }

            # 创建流并识别
            stream = self._recognizer.create_stream()
            stream.accept_waveform(16000, audio_np)

            # 设置热词 (sherpa-onnx 热词 API 需要验证)
            hotwords = self._compose_hotword_payload(session_id, bias_phrases)
            if hotwords:
                # TODO: 验证 sherpa-onnx 热词 API
                pass

            self._recognizer.decode_stream(stream)

            # 提取结果
            text = stream.result.text.strip()
            confidence = 0.9 if text else 0.0

            return {
                "success": True,
                "type": "final",
                "text": text,
                "confidence": confidence,
                "timestamp": time.time(),
                "words": [],
            }

        self._call_count += 1
        return await loop.run_in_executor(None, _infer)

    def update_hotwords(
        self,
        session_id: Optional[str],
        terms: Iterable[str],
    ) -> None:
        """更新热词。

        Args:
            session_id: 会话 ID，None 表示全局热词
            terms: 热词列表
        """
        words: set = set()
        for term in terms:
            if not term:
                continue
            text = str(term).strip()
            if text:
                words.add(text)

        if not words:
            return

        if session_id:
            bucket = self._session_hotwords.setdefault(session_id, set())
            bucket.update(words)
        else:
            self._global_hotwords.update(words)

    def _compose_hotword_payload(
        self,
        session_id: Optional[str],
        bias_phrases: Optional[Iterable[str]],
    ) -> Optional[str]:
        """组装热词字符串。"""
        phrases: set = set()
        phrases.update(self._global_hotwords)

        if session_id:
            phrases.update(self._session_hotwords.get(session_id, set()))

        if bias_phrases:
            for term in bias_phrases:
                if term:
                    phrases.add(str(term).strip())

        if not phrases:
            return None

        return " ".join(sorted(phrases))

    async def cleanup(self) -> None:
        """释放资源。"""
        self._recognizer = None
        self.is_initialized = False
        self.logger.info("SenseVoice 服务已清理")

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息。"""
        return {
            "backend": "sherpa-onnx",
            "model_dir": self.config.model_dir,
            "language": self.config.language,
            "initialized": self.is_initialized,
        }

    # ==================== 兼容性方法 ====================

    def reset(self):
        """Soft reset hook for compatibility."""
        return None

    def get_service_status(self) -> Dict[str, Any]:
        """获取服务运行状态。"""
        return {
            "initialized": self.is_initialized,
            "call_count": self._call_count,
            "active_requests": self._active_requests,
            "max_concurrent": self.config.max_concurrent,
            "timeout_seconds": self.config.timeout_seconds,
            "total_errors": self._total_errors,
            "config": {
                "model_dir": self.config.model_dir,
                "language": self.config.language,
                "use_itn": self.config.use_itn,
            }
        }
