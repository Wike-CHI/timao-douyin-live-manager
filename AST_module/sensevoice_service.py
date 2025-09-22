# -*- coding: utf-8 -*-
"""SenseVoice ASR integration for AST module."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, TYPE_CHECKING

import numpy as np

# Conditional import for FunASR to avoid hard dependency
if TYPE_CHECKING:
    from funasr import AutoModel

try:
    from funasr import AutoModel as AutoModelImpl  # type: ignore
    FUNASR_AVAILABLE = True
except ImportError:
    AutoModelImpl = object  # type: ignore
    FUNASR_AVAILABLE = False


@dataclass
class SenseVoiceConfig:
    """Configuration for SenseVoice ASR service."""

    model_id: str = "iic/SenseVoiceSmall"
    vad_model_id: Optional[str] = "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
    punc_model_id: Optional[str] = None
    language: str = "zh"
    use_itn: bool = True
    batch_size: int = 1
    disable_update: bool = True


class SenseVoiceService:
    """Thin wrapper around FunASR AutoModel for SenseVoice transcription."""

    def __init__(self, config: Optional[SenseVoiceConfig] = None):
        self.config = config or SenseVoiceConfig()
        self.logger = logging.getLogger(__name__)
        self._model: Optional[Any] = None  # Type annotation to fix reportOptionalMemberAccess
        self.is_initialized = False

    async def initialize(self) -> bool:
        """Load SenseVoice model asynchronously."""

        if self.is_initialized:
            return True

        # 检查是否缺少依赖包
        missing_deps = []
        required_packages = {
            'editdistance': 'editdistance',
            'hydra': 'hydra-core',
            'jaconv': 'jaconv',
            'jamo': 'jamo',
            'jieba': 'jieba',
            'librosa': 'librosa',
            'oss2': 'oss2',
            'sentencepiece': 'sentencepiece',
            'soundfile': 'soundfile',
            'tensorboardX': 'tensorboardX',
            'umap': 'umap-learn'
        }
        
        for module_name, package_name in required_packages.items():
            try:
                __import__(module_name)
            except ImportError:
                missing_deps.append(package_name)
        
        # 特殊处理 pytorch_wpe，因为它可能有不同的导入方式
        pytorch_wpe_available = False
        try:
            __import__('pytorch_wpe')
            pytorch_wpe_available = True
        except ImportError:
            pass
        
        if not pytorch_wpe_available:
            missing_deps.append('pytorch-wpe')

        if missing_deps:
            self.logger.error(
                "SenseVoice 启动失败，缺少依赖包: %s",
                ", ".join(missing_deps),
            )
            return False

        if not FUNASR_AVAILABLE:
            self.logger.error(
                "FunASR 未安装，请先执行 pip install funasr 等依赖。"
            )
            return False

        loop = asyncio.get_event_loop()

        def _load_model():
            from funasr import AutoModel  # Local import so FunASR is optional until used

            model_kwargs: Dict[str, Any] = {
                "model": self.config.model_id,
                "disable_update": self.config.disable_update,
                # 添加hub参数以指定模型下载源
                "hub": "ms"  # ModelScope
            }
            if self.config.vad_model_id:
                model_kwargs["vad_model"] = self.config.vad_model_id
            if self.config.punc_model_id:
                model_kwargs["punc_model"] = self.config.punc_model_id

            return AutoModel(**model_kwargs)

        try:
            self.logger.info("Loading SenseVoice model: %s", self.config.model_id)
            self._model = await loop.run_in_executor(None, _load_model)
            self.is_initialized = True
            self.logger.info("✅ SenseVoice model loaded successfully")
            return True
        except Exception as exc:  # pragma: no cover - initialization failures are logged
            self.logger.error("Failed to load SenseVoice model: %s", exc)
            self.is_initialized = False
            return False

    async def transcribe_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """Transcribe a raw PCM chunk (16-bit mono, 16 kHz)."""

        # 如果模型未初始化或缺少依赖包，使用模拟转录
        if not self.is_initialized or not FUNASR_AVAILABLE:
            return self._mock_transcribe(audio_data)

        if not audio_data:
            return {
                "success": True,
                "type": "silence",
                "text": "",
                "confidence": 0.0,
                "timestamp": time.time(),
                "words": [],
            }

        loop = asyncio.get_event_loop()

        def _infer() -> Dict[str, Any]:
            try:
                speech = np.frombuffer(audio_data, dtype=np.int16)
                if speech.size == 0:
                    return {
                        "success": True,
                        "type": "silence",
                        "text": "",
                        "confidence": 0.0,
                        "timestamp": time.time(),
                        "words": [],
                    }

                speech = speech.astype(np.float32) / 32768.0
                # Check if model is not None before calling generate
                if self._model is not None:
                    raw_results = self._model.generate(
                        input=speech,
                        language=self.config.language,
                        use_itn=self.config.use_itn,
                        batch_size=self.config.batch_size,
                    )

                    text = self._extract_text(raw_results)
                    confidence = 0.9 if text else 0.0
                    return {
                        "success": True,
                        "type": "final",
                        "text": text,
                        "confidence": confidence,
                        "timestamp": time.time(),
                        "words": [],
                    }
                else:
                    return self._mock_transcribe(audio_data)
            except Exception as exc:  # pragma: no cover - handled via logging
                self.logger.error("SenseVoice transcription failed: %s", exc)
                return self._mock_transcribe(audio_data)

        return await loop.run_in_executor(None, _infer)

    def _mock_transcribe(self, audio_data: bytes) -> Dict[str, Any]:
        """模拟转录功能"""
        # 简单的模拟，根据音频数据长度生成一些文本
        return {
            "success": False,
            "type": "error",
            "text": "",
            "confidence": 0.0,
            "timestamp": time.time(),
            "words": [],
            "error": "SenseVoice 未就绪，无法生成实时转录",
        }

    async def cleanup(self):
        """Release model resources if necessary."""
        self._model = None
        self.is_initialized = False

    def reset(self):
        """Soft reset hook for compatibility with SenseVoice direct service."""
        # SenseVoice AutoModel does not expose explicit reset; noop for parity.
        return None

    def get_model_info(self) -> Dict[str, Any]:
        """Return metadata about the loaded model."""
        return {
            "backend": "sensevoice",
            "model_id": self.config.model_id,
            "vad_model_id": self.config.vad_model_id,
            "punc_model_id": self.config.punc_model_id,
            "initialized": self.is_initialized,
        }

    @staticmethod
    def _extract_text(raw_results: Any) -> str:
        if not raw_results:
            return ""

        first = raw_results[0]
        text = first.get("text", "") if isinstance(first, dict) else ""
        # Remove special tokens such as <|zh|>
        clean = re.sub(r"<\|[^|>]+\|>", "", text)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()
