# -*- coding: utf-8 -*-
"""
Sherpa-ONNX backend for AST module.

This provides a minimal offline recognizer wrapper that can consume small
PCM16 mono 16k chunks and return text. It attempts to locate a downloaded
model under `models/` or downloads it via ModelScope when missing.

It is designed to be best-effort: if dependencies are missing or the model
layout is unexpected, initialization will fail gracefully so the caller can
fallback to other backends.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import os

import numpy as np


def _try_import_sherpa():
    try:
        import sherpa_onnx as s  # type: ignore
        return s
    except Exception:
        try:
            import k2_sherpa_onnx as s  # type: ignore
            return s
        except Exception:
            return None


def _try_models_snapshot(model_id: str, cache_dir: Path) -> Optional[Path]:
    try:
        from modelscope.hub.snapshot_download import snapshot_download  # type: ignore
    except Exception:
        return None
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        local_dir = snapshot_download(model_id=model_id, cache_dir=str(cache_dir))
        return Path(local_dir)
    except Exception:
        return None


@dataclass
class SherpaConfig:
    model_id: str = "xiaowangge/sherpa-onnx-sense-voice-small"
    local_dir: Optional[str] = None
    provider: str = "cpu"  # or 'cuda'
    num_threads: int = 2
    sample_rate: int = 16000
    language: str = "zh"


class SherpaOnnxService:
    def __init__(self, config: Optional[SherpaConfig] = None):
        self.config = config or SherpaConfig()
        self.logger = logging.getLogger(__name__)
        self._recognizer = None
        self.is_initialized = False

    def _find_files(self, root: Path) -> Tuple[Optional[Path], Optional[Tuple[Path, Path, Path]]]:
        """Return (paraformer_model, (enc, dec, join)) if found."""
        para = None
        transducer = None
        # tokens
        tokens = None
        for p in root.rglob("tokens*.txt"):
            tokens = p
            break
        if not tokens:
            for p in root.rglob("*.txt"):
                if "token" in p.name:
                    tokens = p
                    break
        if not tokens:
            return None, None

        # paraformer: model.onnx
        for p in root.rglob("model.onnx"):
            para = p
            break
        # transducer: encoder/decoder/joiner
        enc = root / "encoder.onnx"
        dec = root / "decoder.onnx"
        join = root / "joiner.onnx"
        if not (enc.exists() and dec.exists() and join.exists()):
            enc = next(iter(root.rglob("*encoder*.onnx")), None)
            dec = next(iter(root.rglob("*decoder*.onnx")), None)
            join = next(iter(root.rglob("*joiner*.onnx")), None)
        if enc and dec and join:
            transducer = (enc, dec, join, tokens)

        # Store tokens path for later
        self._tokens = tokens
        return para, (transducer[0], transducer[1], transducer[2]) if transducer else (None)

    async def initialize(self) -> bool:
        if self.is_initialized:
            return True
        sherpa = _try_import_sherpa()
        if sherpa is None:
            self.logger.error("sherpa-onnx not installed: pip install k2-sherpa-onnx")
            return False

        # Resolve model directory
        local_dir: Optional[Path] = None
        if self.config.local_dir:
            p = Path(self.config.local_dir)
            local_dir = p if p.exists() else None
        if local_dir is None:
            # try under project models/
            project_root = Path(__file__).resolve().parents[1]
            guess = project_root / "models" / "third_party" / "sherpa" / self.config.model_id.replace("/", "_")
            if (guess).exists():
                local_dir = guess
        if local_dir is None:
            # try modelscope snapshot
            project_root = Path(__file__).resolve().parents[1]
            cache_root = project_root / "models" / ".cache" / "modelscope"
            dl = _try_models_snapshot(self.config.model_id, cache_root)
            if dl is not None:
                local_dir = dl

        if local_dir is None:
            self.logger.error("Sherpa model not found and cannot be downloaded: %s", self.config.model_id)
            return False

        para, transducer = self._find_files(local_dir)
        if not getattr(self, "_tokens", None):
            self.logger.error("No tokens file found under %s", local_dir)
            return False

        cfg = None
        try:
            if para is not None:
                cfg = sherpa.OfflineRecognizerConfig(
                    tokens=str(self._tokens),
                    paraformer=sherpa.OfflineParaformerModelConfig(
                        model=str(para), provider=self.config.provider, num_threads=self.config.num_threads
                    ),
                    sample_rate=self.config.sample_rate,
                )
            elif transducer is not None:
                enc, dec, join = transducer
                cfg = sherpa.OfflineRecognizerConfig(
                    tokens=str(self._tokens),
                    transducer=sherpa.OfflineTransducerModelConfig(
                        encoder=str(enc), decoder=str(dec), joiner=str(join),
                        provider=self.config.provider, num_threads=self.config.num_threads
                    ),
                    sample_rate=self.config.sample_rate,
                )
            else:
                self.logger.error("Unsupported sherpa model layout under %s", local_dir)
                return False

            self._recognizer = sherpa.OfflineRecognizer(cfg)
            self.is_initialized = True
            self.logger.info("✅ Sherpa-ONNX model ready: %s", local_dir)
            return True
        except Exception as e:
            self.logger.error("Failed to init sherpa-onnx: %s", e)
            return False

    async def transcribe_audio(self, audio_data: bytes) -> Dict[str, Any]:
        if not self.is_initialized or self._recognizer is None:
            return {
                "success": False,
                "type": "error",
                "text": "",
                "confidence": 0.0,
                "timestamp": 0.0,
                "words": [],
                "error": "sherpa-onnx not initialized",
            }

        if not audio_data:
            return {"success": True, "type": "silence", "text": "", "confidence": 0.0, "timestamp": 0.0, "words": []}

        loop = asyncio.get_event_loop()

        def _infer() -> Dict[str, Any]:
            try:
                speech = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                stream = self._recognizer.create_stream()
                stream.accept_waveform(self.config.sample_rate, speech)
                self._recognizer.decode_stream(stream)
                res = stream.result.text or ""
                return {
                    "success": True,
                    "type": "final",
                    "text": res,
                    "confidence": 0.9 if res else 0.0,
                    "timestamp": 0.0,
                    "words": [],
                }
            except Exception as e:
                self.logger.error("sherpa-onnx inference failed: %s", e)
                return {
                    "success": False,
                    "type": "error",
                    "text": "",
                    "confidence": 0.0,
                    "timestamp": 0.0,
                    "words": [],
                    "error": str(e),
                }

        return await loop.run_in_executor(None, _infer)

    async def cleanup(self):
        self._recognizer = None
        self.is_initialized = False

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "backend": "sherpa-onnx",
            "model_id": self.config.model_id,
            "initialized": self.is_initialized,
        }

