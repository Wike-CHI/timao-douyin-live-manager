# -*- coding: utf-8 -*-
"""SenseVoice ASR integration for AST module."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, TYPE_CHECKING
import os
from pathlib import Path

import numpy as np

# UMAP/FunASR 会在导入阶段依赖 numba 的 JIT；在 Python 3.11 上会触发已知的
# range lowering bug（i64→i32）。设置以下环境变量可以让 UMAP 走纯 Python 路径，
# 并禁用 numba 的 JIT，从而避免初始化时崩溃。
os.environ.setdefault("UMAP_DONT_USE_NUMBA", "1")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

# Conditional import for FunASR to avoid hard dependency
if TYPE_CHECKING:
    from funasr import AutoModel

try:
    from funasr import AutoModel as AutoModelImpl  # type: ignore
    FUNASR_AVAILABLE = True
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"FunASR 导入失败 (ImportError): {e}")
    AutoModelImpl = object  # type: ignore
    FUNASR_AVAILABLE = False
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"FunASR 导入失败 (非预期错误): {e}")
    import traceback
    logger.debug(f"FunASR 导入详细错误:\n{traceback.format_exc()}")
    AutoModelImpl = object  # type: ignore
    FUNASR_AVAILABLE = False


@dataclass
class SenseVoiceConfig:
    """Configuration for SenseVoice ASR service.

    We hard-lock the backend to SenseVoiceSmall and enable VAD by default.
    Streaming knobs are enabled so we can reuse SenseVoice incremental decoding,
    hotword biasing, and punctuation without hand-written heuristics.
    
    🔧 内存优化：减小chunk_size和look_back参数以降低内存峰值
    """

    # Prefer local checkout if present; otherwise fall back to ModelScope id.
    model_id: str = "iic/SenseVoiceSmall"
    # VAD model: we'll try to auto-detect a local path below and otherwise use
    # the known-good ModelScope id. Keeping this field Optional allows callers
    # to override with an explicit local path, but the service will enforce a
    # default if None.
    vad_model_id: Optional[str] = None
    punc_model_id: Optional[str] = None
    language: str = "zh"
    use_itn: bool = True
    batch_size: int = 1
    disable_update: bool = True
    enable_streaming: bool = True
    chunk_size: int = 1600  # 🔧 从3200降至1600，减少内存峰值
    chunk_shift: int = 400  # 🔧 从800降至400，保持25%重叠率
    encoder_chunk_look_back: int = 2  # 🔧 从4降至2，减少上下文缓存
    decoder_chunk_look_back: int = 1
    hotword_weight: float = 3.0


class SenseVoiceService:
    """Thin wrapper around FunASR AutoModel for SenseVoice transcription."""

    def __init__(self, config: Optional[SenseVoiceConfig] = None):
        self.config = config or SenseVoiceConfig()
        self.logger = logging.getLogger(__name__)
        self._model: Optional[Any] = None  # Type annotation to fix reportOptionalMemberAccess
        self.is_initialized = False
        # Remember which device we loaded the model on (for logging/debug)
        self._device: str = "cpu"
        self._global_hotwords: set[str] = set()
        self._session_hotwords: Dict[str, set[str]] = {}
        # 🔧 性能监控：内存和调用统计
        self._call_count: int = 0
        self._last_memory_check: float = 0.0
        
        # 🔒 并发控制：防止多音频流死锁
        self._model_lock = asyncio.Lock()  # 模型调用互斥锁
        self._max_concurrent = 2  # 最大并发转写数（适配7.4GB内存）
        self._semaphore = asyncio.Semaphore(self._max_concurrent)  # 并发信号量
        self._timeout_seconds = 10.0  # 单次转写超时时间
        self._active_requests: int = 0  # 当前活跃请求数
        self._total_timeouts: int = 0  # 超时计数
        self._total_errors: int = 0  # 错误计数

        # Enforce Small model only. If an external caller passed Medium/Large,
        # normalize it back to Small. Local paths that already point to
        # SenseVoiceSmall are kept untouched.
        try:
            mid = (self.config.model_id or "")
            if re.search(r"SenseVoice(?!Small)(Large|Medium)", mid, re.IGNORECASE):
                self.logger.info("Force model_id to SenseVoiceSmall (was: %s)", mid)
                self.config.model_id = "iic/SenseVoiceSmall"
        except Exception:
            # Best effort; don't fail init due to logging issues
            self.config.model_id = "iic/SenseVoiceSmall"

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

            # Force caches to local project paths to avoid invalid drive letters (e.g., E:\).
            # This also helps in offline environments.
            project_root = Path(__file__).resolve().parents[1]
            cache_root = (project_root / "models" / ".cache").resolve()
            try:
                cache_root.mkdir(parents=True, exist_ok=True)
            except Exception:
                # If we cannot create cache dir, just continue without overriding envs
                pass

            # Override cache related environment variables for modelscope/funasr
            os.environ["MODELSCOPE_CACHE"] = str(cache_root)
            os.environ["MS_CACHE_HOME"] = str(cache_root)
            os.environ.setdefault("FUNASR_HOME", str(cache_root / "funasr"))

            # Choose device: honor override, otherwise prefer CUDA if available
            device_override = os.environ.get("LIVE_FORCE_DEVICE") or os.environ.get("SENSEVOICE_DEVICE")
            device = (device_override or "cpu").strip()
            if device.lower() == "auto":
                device = "cpu"
            if device == "cpu":
                try:
                    import torch  # type: ignore
                    if torch.cuda.is_available():
                        device = "cuda:0"
                except Exception:
                    device = "cpu"
            elif device.startswith("cuda"):
                try:
                    import torch  # type: ignore
                    if not torch.cuda.is_available():
                        self.logger.warning("Requested GPU device %s but CUDA not available, falling back to CPU", device)
                        device = "cpu"
                except Exception:
                    device = "cpu"

            def _resolve_small_model_id() -> str:
                # Prefer local checkout if exists
                project_root = Path(__file__).resolve().parents[1]
                local_dir = project_root / "models" / "models" / "iic" / "SenseVoiceSmall"
                try:
                    if local_dir.exists():
                        return str(local_dir)
                except Exception:
                    pass
                return self.config.model_id

            def _resolve_vad_model_id() -> str:
                # Try local VAD first
                project_root = Path(__file__).resolve().parents[1]
                local_vad = project_root / "models" / "models" / "iic" / "speech_fsmn_vad_zh-cn-16k-common-pytorch"
                try:
                    if self.config.vad_model_id:
                        return self.config.vad_model_id
                    if local_vad.exists():
                        return str(local_vad)
                except Exception:
                    pass
                # Fallback to ModelScope id
                return "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"

            def _resolve_punc_model_id() -> Optional[str]:
                """Prefer a local punctuation model if present; otherwise respect explicit config.
                Avoid forcing network downloads in offline environments.
                """
                try:
                    if self.config.punc_model_id:
                        return self.config.punc_model_id
                    project_root = Path(__file__).resolve().parents[1]
                    local_punc = project_root / "models" / "models" / "iic" / "punc_ct-transformer_zh-cn-common-vocab272727-pytorch"
                    if local_punc.exists():
                        return str(local_punc)
                except Exception:
                    pass
                # No local punc found; return None to skip
                return None

            model_kwargs: Dict[str, Any] = {
                "model": _resolve_small_model_id(),
                "disable_update": self.config.disable_update,
                # 添加hub参数以指定模型下载源
                "hub": "ms",  # ModelScope
                "device": device,
                # Always enable external VAD (local or ModelScope id)
                "vad_model": _resolve_vad_model_id(),
            }
            punc_id = _resolve_punc_model_id()
            if punc_id:
                model_kwargs["punc_model"] = punc_id

            # Strict: VAD is required. If load fails, bubble up the error.
            model = AutoModel(**model_kwargs)
            # persist the selected device for later logging
            self._device = device
            return model

        try:
            self.logger.info("Loading SenseVoice model: %s", self.config.model_id)
            self._model = await loop.run_in_executor(None, _load_model)
            self.is_initialized = True
            # model_kwargs is local to loader; use the tracked device instead
            self.logger.info(
                "✅ SenseVoice model loaded successfully (device=%s)",
                getattr(self, "_device", "unknown"),
            )
            return True
        except Exception as exc:  # pragma: no cover - initialization failures are logged
            self.logger.error("Failed to load SenseVoice model: %s", exc)
            self.is_initialized = False
            return False

    def update_hotwords(self, session_id: Optional[str], terms: Iterable[str]) -> None:
        """Update hotword bias for the decoder."""
        words: set[str] = set()
        for term in terms:
            if not term:
                continue
            try:
                text = str(term).strip()
            except Exception:
                continue
            if not text:
                continue
            if re.search(r"[\u4e00-\u9fa5]", text):
                words.add(text)
        if not words:
            return
        if session_id:
            bucket = self._session_hotwords.setdefault(session_id, set())
            bucket.update(words)
        else:
            self._global_hotwords.update(words)

    async def transcribe_audio(
        self,
        audio_data: bytes,
        *,
        session_id: Optional[str] = None,
        bias_phrases: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """Transcribe a raw PCM chunk (16-bit mono, 16 kHz).
        
        🔒 并发安全：使用信号量限制并发数，使用锁保护模型调用，添加超时防止死锁
        """

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
        
        # 🔒 并发控制：获取信号量，限制同时转写数量
        try:
            async with self._semaphore:
                self._active_requests += 1
                try:
                    # 🔒 添加超时保护，防止死锁
                    result = await asyncio.wait_for(
                        self._transcribe_with_lock(audio_data, session_id, bias_phrases),
                        timeout=self._timeout_seconds
                    )
                    return result
                except asyncio.TimeoutError:
                    self._total_timeouts += 1
                    self.logger.error(
                        f"⏱️ 转写超时 ({self._timeout_seconds}秒)，会话: {session_id}, "
                        f"累计超时: {self._total_timeouts}次"
                    )
                    return {
                        "success": False,
                        "type": "error",
                        "text": "",
                        "confidence": 0.0,
                        "timestamp": time.time(),
                        "words": [],
                        "error": f"转写超时({self._timeout_seconds}秒)",
                    }
                finally:
                    self._active_requests -= 1
        except Exception as exc:
            self._total_errors += 1
            self.logger.error(f"❌ 转写失败: {exc}")
            return self._mock_transcribe(audio_data)
    
    async def _transcribe_with_lock(
        self,
        audio_data: bytes,
        session_id: Optional[str],
        bias_phrases: Optional[Iterable[str]],
    ) -> Dict[str, Any]:
        """使用锁保护的转写实现，防止模型并发调用冲突"""
        
        # 🔧 性能监控：每20次调用检查一次内存（更频繁监控）
        self._call_count += 1
        current_time = time.time()
        
        if self._call_count % 20 == 0 or (current_time - self._last_memory_check > 60):  # 1分钟
            self._last_memory_check = current_time
            try:
                import gc
                import psutil  # pyright: ignore[reportMissingModuleSource]
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                # 更积极的内存管理策略
                if memory_mb > 2000:  # 超过2GB开始垃圾回收
                    gc.collect()
                    
                if memory_mb > 2500:  # 超过2.5GB发出警告
                    self.logger.warning(
                        f"⚠️ SenseVoice内存: {memory_mb:.0f}MB, 活跃请求: {self._active_requests}, "
                        f"调用: {self._call_count}, 超时: {self._total_timeouts}, 错误: {self._total_errors}"
                    )
                    
                    if memory_mb > 3000:  # 超过3GB，记录严重警告
                        self.logger.error(f"❌ SenseVoice内存占用严重: {memory_mb:.0f}MB，建议重启服务")
                elif self._call_count % 100 == 0:  # 每100次正常记录
                    self.logger.debug(
                        f"✅ SenseVoice运行正常: 内存{memory_mb:.0f}MB, 活跃{self._active_requests}, "
                        f"调用{self._call_count}次"
                    )
            except Exception as e:
                self.logger.debug(f"内存监控失败: {e}")

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
                
                # 🔧 快速静音检测：跳过RMS过低的音频，节省CPU
                rms = np.sqrt(np.mean(speech.astype(np.float32) ** 2))
                if rms < 320:  # 约0.01 (320/32768)，极低音量视为静音
                    return {
                        "success": True,
                        "type": "silence",
                        "text": "",
                        "confidence": 0.0,
                        "timestamp": time.time(),
                        "words": [],
                    }

                speech = speech.astype(np.float32) / 32768.0
                audio_sec = float(len(speech)) / 16000.0
                # Check if model is not None before calling generate
                if self._model is not None:
                    gen_kwargs: Dict[str, Any] = {
                        "input": speech,
                        "language": self.config.language,
                        "use_itn": self.config.use_itn,
                        "batch_size": self.config.batch_size,
                    }
                    hotword_payload = self._compose_hotword_payload(session_id, bias_phrases)
                    if hotword_payload:
                        gen_kwargs["hotword"] = hotword_payload
                        gen_kwargs["hotword_weight"] = self.config.hotword_weight
                    if self.config.enable_streaming and session_id:
                        gen_kwargs.update(
                            {
                                "streaming": True,
                                "cache_key": session_id,
                                "chunk_size": self.config.chunk_size,
                                "chunk_shift": self.config.chunk_shift,
                                "decoder_chunk_look_back": self.config.decoder_chunk_look_back,
                                "encoder_chunk_look_back": self.config.encoder_chunk_look_back,
                            }
                        )
                    try:
                        raw_results = self._model.generate(**gen_kwargs)
                    except ValueError as exc:
                        # 捕获 "choose a window size" 等音频处理错误
                        error_msg = str(exc)
                        if "window size" in error_msg or "choose a window size 0" in error_msg:
                            # 音频太短或无有效语音，这是正常情况，返回空结果
                            # 使用DEBUG级别而不是ERROR，因为这不是真正的错误
                            self.logger.debug(f"音频片段太短或无有效语音: {error_msg}")
                            return {
                                "success": True,
                                "type": "silence",
                                "text": "",
                                "confidence": 0.0,
                                "timestamp": time.time(),
                                "words": [],
                            }
                        # 其他 ValueError 继续处理
                        raise
                    except TypeError as exc:
                        self.logger.debug("SenseVoice generate fallback: %s", exc)
                        fallback_kwargs = dict(gen_kwargs)
                        fallback_kwargs.pop("hotword_weight", None)
                        if fallback_kwargs.get("streaming"):
                            fallback_kwargs.pop("streaming", None)
                            fallback_kwargs.pop("cache_key", None)
                            fallback_kwargs.pop("chunk_size", None)
                            fallback_kwargs.pop("chunk_shift", None)
                            fallback_kwargs.pop("decoder_chunk_look_back", None)
                            fallback_kwargs.pop("encoder_chunk_look_back", None)
                        try:
                            raw_results = self._model.generate(**fallback_kwargs)
                        except ValueError as inner_exc:
                            # 同样处理内部的 window size 错误
                            if "window size" in str(inner_exc):
                                self.logger.debug(f"Fallback: 音频片段太短或无有效语音: {inner_exc}")
                                return {
                                    "success": True,
                                    "type": "silence",
                                    "text": "",
                                    "confidence": 0.0,
                                    "timestamp": time.time(),
                                    "words": [],
                                }
                            raise
                        except Exception as inner_exc:
                            self.logger.debug("SenseVoice bare fallback used: %s", inner_exc)
                            try:
                                raw_results = self._model.generate(input=speech)
                            except ValueError as bare_exc:
                                # 最后的 fallback 也捕获 window size 错误
                                if "window size" in str(bare_exc):
                                    self.logger.debug(f"Bare fallback: 音频片段太短或无有效语音: {bare_exc}")
                                    return {
                                        "success": True,
                                        "type": "silence",
                                        "text": "",
                                        "confidence": 0.0,
                                        "timestamp": time.time(),
                                        "words": [],
                                    }
                                raise
                    text = self._extract_text(raw_results)
                    words = self._extract_words(raw_results, text, audio_sec)
                    confidence = self._extract_confidence(raw_results, default=0.9 if text else 0.0)
                    
                    # 🔧 立即释放音频数据和结果，减少内存占用
                    del speech
                    del raw_results
                    
                    return {
                        "success": True,
                        "type": "final",
                        "text": text,
                        "confidence": confidence,
                        "timestamp": time.time(),
                        "words": words,
                    }
                else:
                    return self._mock_transcribe(audio_data)
            except Exception as exc:  # pragma: no cover - handled via logging
                # 如果是window size相关的错误，使用DEBUG级别
                if "window size" in str(exc):
                    self.logger.debug(f"音频片段处理: {exc}")
                    return {
                        "success": True,
                        "type": "silence",
                        "text": "",
                        "confidence": 0.0,
                        "timestamp": time.time(),
                        "words": [],
                    }
                # 其他错误仍然记录为ERROR
                self.logger.error("SenseVoice transcription failed: %s", exc)
                return self._mock_transcribe(audio_data)

        # 🔒 使用锁保护模型调用，防止多音频流并发冲突
        async with self._model_lock:
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
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务运行状态（并发控制、性能统计）"""
        return {
            "initialized": self.is_initialized,
            "device": self._device,
            "call_count": self._call_count,
            "active_requests": self._active_requests,
            "max_concurrent": self._max_concurrent,
            "timeout_seconds": self._timeout_seconds,
            "total_timeouts": self._total_timeouts,
            "total_errors": self._total_errors,
            "config": {
                "chunk_size": self.config.chunk_size,
                "chunk_shift": self.config.chunk_shift,
                "encoder_chunk_look_back": self.config.encoder_chunk_look_back,
                "batch_size": self.config.batch_size,
            }
        }

    def _compose_hotword_payload(
        self,
        session_id: Optional[str],
        bias_phrases: Optional[Iterable[str]],
    ) -> Optional[str]:
        phrases: set[str] = set()
        phrases.update(self._global_hotwords)
        if session_id:
            phrases.update(self._session_hotwords.get(session_id, set()))
        if bias_phrases:
            for term in bias_phrases:
                if not term:
                    continue
                text = str(term).strip()
                if text and re.search(r"[\u4e00-\u9fa5]", text):
                    phrases.add(text)
        if not phrases:
            return None
        ordered = sorted(phrases)
        return " ".join(ordered)

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

    @staticmethod
    def _extract_words(raw_results: Any, text: str, audio_sec: float):
        """Best-effort word/char timestamps.
        - If backend returns timestamps (e.g., CTC alignment), convert to words list.
        - Otherwise approximate by uniformly slicing the audio duration per character.
        """
        try:
            first = raw_results[0] if raw_results else None
            if isinstance(first, dict):
                # Common patterns: first.get('timestamp') or first.get('words')
                if 'words' in first and isinstance(first['words'], list):
                    return first['words']
                ts = first.get('timestamp')
                if isinstance(ts, list) and all(isinstance(p, (list, tuple)) and len(p) == 2 for p in ts):
                    words = []
                    # If text length matches timestamp entries, map char-to-span
                    units = list(text)
                    for i, (s, e) in enumerate(ts[: len(units)]):
                        words.append({"word": units[i], "start": float(s), "end": float(e)})
                    return words
        except Exception:
            pass

        # Fallback: uniform segmentation per character
        text = text or ""
        n = max(1, len(text))
        dur = max(0.001, audio_sec)
        step = dur / n
        t0 = 0.0
        words = []
        for ch in text:
            words.append({"word": ch, "start": t0, "end": t0 + step})
            t0 += step
        return words

    @staticmethod
    def _extract_confidence(raw_results: Any, default: float = 0.0) -> float:
        try:
            first = raw_results[0] if raw_results else None
            if isinstance(first, dict):
                if "confidence" in first and isinstance(first["confidence"], (float, int)):
                    return float(first["confidence"])
                if "score" in first and isinstance(first["score"], (float, int)):
                    return float(first["score"])
                nbest = first.get("nbest")
                if isinstance(nbest, list) and nbest:
                    head = nbest[0]
                    if isinstance(head, dict):
                        if "confidence" in head and isinstance(head["confidence"], (float, int)):
                            return float(head["confidence"])
                        if "score" in head and isinstance(head["score"], (float, int)):
                            return float(head["score"])
        except Exception:
            pass
        return float(default)
