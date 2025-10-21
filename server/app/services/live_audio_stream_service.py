"""
Live Audio Stream Transcription Service

Replaces microphone capture with network capture:
- Resolve Douyin live URL via StreamCap platform handler
- Use ffmpeg to demux/transcode audio to PCM16 16k mono (pipe)
- Feed chunks into SenseVoice, apply cleaner/guard/assembler
- Expose callbacks for transcripts and input level
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import signal
import sys
import time
import shutil
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Deque, Dict, List, Optional


# Workspace root on sys.path so we can import StreamCap and AST_module
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# StreamCap platform handler (resolve real stream URL from live URL)
from StreamCap.app.core.platforms.platform_handlers import (  # type: ignore
    get_platform_handler,
)

# SenseVoice (batch API)
from AST_module.sensevoice_service import (  # type: ignore
    SenseVoiceConfig,
    SenseVoiceService,
)

# ACRCloud (optional music recognition)
try:
    from AST_module.acrcloud_client import (  # type: ignore
        ACRMusicMatch,
        load_acr_client_from_env,
    )
except Exception:  # pragma: no cover - optional依赖
    ACRMusicMatch = None  # type: ignore
    load_acr_client_from_env = None  # type: ignore

# Postprocessing & light DSP helpers
from AST_module.postprocess import (  # type: ignore
    ChineseCleaner,
    HallucinationGuard,
    SentenceAssembler,
    pcm16_rms,
)
try:
    from server.nlp.hotwords import HotwordReplacer  # type: ignore
except Exception:
    HotwordReplacer = None  # type: ignore
try:
    from server.nlp.phonetic_corrector import PhoneticCorrector  # type: ignore
except Exception:
    PhoneticCorrector = None  # type: ignore
try:
    from .online_diarizer import OnlineDiarizer  # type: ignore
except Exception:
    OnlineDiarizer = None  # type: ignore
try:
    from server.utils.jsonl_writer import JSONLWriter  # type: ignore
except Exception:
    JSONLWriter = None  # type: ignore
# Removed optional audio gate / diarizer dependencies to simplify pipeline

try:  # Optional dependency: 本地环境已包含 numpy
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - numpy 非必需
    np = None  # type: ignore


def _now() -> float:
    return time.time()


def _parse_live_id(live_url_or_id: str) -> Optional[str]:
    s = (live_url_or_id or "").strip()
    m = re.search(r"live\.douyin\.com/([A-Za-z0-9_\-]+)", s)
    if m:
        return m.group(1)
    # Already an ID
    if re.fullmatch(r"[A-Za-z0-9_\-]+", s):
        return s
    return None


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(
    name: str,
    default: float,
    *,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    if (min_value is not None) and (value < min_value):
        value = min_value
    if (max_value is not None) and (value > max_value):
        value = max_value
    return value


def _env_int(
    name: str,
    default: int,
    *,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    if (min_value is not None) and (value < min_value):
        value = min_value
    if (max_value is not None) and (value > max_value):
        value = max_value
    return value


@dataclass
class LiveAudioStatus:
    is_running: bool = False
    live_url: Optional[str] = None
    live_id: Optional[str] = None
    session_id: Optional[str] = None
    started_at: float = field(default_factory=_now)
    ffmpeg_pid: Optional[int] = None
    total_audio_chunks: int = 0
    successful_transcriptions: int = 0
    failed_transcriptions: int = 0
    average_confidence: float = 0.0
    music_guard_active: bool = False
    music_guard_score: float = 0.0
    music_last_title: Optional[str] = None
    music_last_score: float = 0.0
    music_last_detected_at: float = 0.0


class LiveAudioStreamService:
    """Single-session live audio stream transcriber."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._status = LiveAudioStatus()
        self._ffmpeg: Optional[asyncio.subprocess.Process] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._stop_evt = asyncio.Event()

        # ASR & postprocess
        self._sv: Optional[SenseVoiceService] = None
        self._cleaner = ChineseCleaner()
        # 保守的防幻觉参数（回到 Small+VAD 统一策略的默认）
        self._guard = HallucinationGuard(min_rms=0.018, min_len=2, low_conf=0.50)
        # 分句器恢复更稳的默认：等待更久、静音次数更高，避免碎句
        self._assembler = SentenceAssembler(max_wait=3.5, max_chars=60, silence_flush=2)

        # Hotword replacer (optional)
        self._hotword: Optional[Any] = None
        try:
            if HotwordReplacer is not None:
                self._hotword = HotwordReplacer()
        except Exception:
            self._hotword = None

        # Phonetic correction (optional, depends on pypinyin & knowledge base)
        self._corrector: Optional[Any] = None
        self._context_terms: Deque[str] = deque(maxlen=96)
        try:
            if PhoneticCorrector is not None:
                self._corrector = PhoneticCorrector()
        except Exception:
            self._corrector = None

        # Automatic gain control (SenseVoice gain assistant)
        self.agc_enabled = bool(int(os.getenv("LIVE_AUDIO_AGC", "1")))
        self.agc_target_rms = float(os.getenv("LIVE_AUDIO_AGC_TARGET", "0.06"))
        self.agc_max_gain = float(os.getenv("LIVE_AUDIO_AGC_MAX_GAIN", "5.0"))
        self.agc_min_gain = float(os.getenv("LIVE_AUDIO_AGC_MIN_GAIN", "0.4"))
        self.agc_smooth = float(os.getenv("LIVE_AUDIO_AGC_SMOOTH", "0.2"))
        self._agc_gain = 1.0

        # Speaker diarization (host vs guest)
        self._diarizer = None
        self._last_speaker_label: str = "unknown"
        self._last_speaker_debug: Dict[str, float] = {}
        self._diarizer_warmup_sec: Optional[float] = None
        self._init_diarizer()

        # Callbacks
        self._tr_callbacks: Dict[str, Callable[[Dict[str, Any]], Awaitable[None] | None]] = {}
        self._level_callbacks: Dict[str, Callable[[float, float], Awaitable[None] | None]] = {}

        # Config
        # Output mode: hard-lock to 'vad' per product requirement
        self.mode: str = "vad"
        # Model size: 'small'|'medium'|'large'
        self._model_size: str = "small"
        # Streaming/VAD parameters are applied via profile presets (default -> stable)
        self.chunk_seconds: float = 0.8
        self.vad_min_silence_sec: float = 0.80
        self.vad_min_speech_sec: float = 0.50
        self.vad_hangover_sec: float = 0.30
        self.vad_min_rms: float = 0.018
        self.vad_force_flush_sec: float = 6.0
        self.vad_force_flush_overlap_sec: float = 0.25
        # Track partial text already emitted via delta
        self._partial_text: str = ""
        # VAD runtime state
        self._vad_in_speech: bool = False
        self._vad_silence_acc: float = 0.0
        self._vad_speech_acc: float = 0.0
        self._vad_buf: bytearray = bytearray()
        # Duplicate suppression (final sentence level)
        self._last_sent_norms: List[str] = []  # keep recent normalized sentences
        # Soft constraints
        self.min_sentence_chars: int = 8  # 默认稳定配置，可通过 profile 覆盖
        # Stability gating for non-punctuation finals
        self._stable_prev_norm: str = ""
        self._stable_hits: int = 0
        # Preload state (simple busy flags per size)
        self._preload_busy: set[str] = set()

        # Profile name（fast|stable），用于一键切换参数
        self.profile: str = "fast"
        default_profile = os.environ.get("LIVE_AUDIO_PROFILE", self.profile)
        try:
            self.apply_profile(default_profile)
        except Exception:
            # 确保至少回退到快速档，保障低延迟体验
            self.apply_profile("fast")
        # Allow environment overrides so ops can tune latency vs stability quickly
        self._apply_env_overrides()

        # Advanced filters removed (simplified pipeline)
        # Persistence (transcriptions)
        # 默认开启字幕持久化，保存到 records/live_logs/<live_id>/<YYYY-MM-DD>/
        self.persist_enabled: bool = True
        self.persist_root: Optional[str] = None
        self._persist_tr: Optional[Any] = None

        # 背景音乐检测与自适应阈值
        self.music_detection_enabled: bool = bool(int(os.getenv("LIVE_VAD_MUSIC_DETECT", "1")))
        if np is None:
            self.music_detection_enabled = False
        self.music_detect_alpha: float = 0.25
        self.music_detect_threshold: float = 0.58
        self.music_release_threshold: float = 0.45
        self.music_release_frames: int = 4
        self.music_rms_boost: float = 1.6
        self.music_min_speech_boost: float = 1.3
        self.music_min_silence_scale: float = 1.1
        self._music_ema: float = 0.0
        self._music_flag: bool = False
        self._music_release_counter: int = 0
        self._music_last_notice: float = 0.0
        # ACRCloud 背景音乐识别（可选）
        self._acr_client: Optional[Any] = None
        self._acr_enabled: bool = False
        self._acr_buffer: bytearray = bytearray()
        self._acr_bytes_per_sec: int = 16000 * 2  # PCM16 mono
        self._acr_segment_sec: float = _env_float("LIVE_ACR_SEGMENT_SEC", 10.0, min_value=4.0, max_value=15.0)
        self._acr_target_bytes: int = int(self._acr_bytes_per_sec * self._acr_segment_sec)
        self._acr_cooldown_sec: float = _env_float("LIVE_ACR_COOLDOWN_SEC", 25.0, min_value=5.0, max_value=120.0)
        self._acr_match_hold_sec: float = _env_float("LIVE_ACR_MATCH_HOLD_SEC", 6.0, min_value=1.0, max_value=60.0)
        self._acr_last_attempt: float = 0.0
        self._acr_active_until: float = 0.0
        self._acr_pending_task: Optional[asyncio.Task] = None
        self._acr_last_match: Optional[Any] = None
        self._acr_last_title: Optional[str] = None
        self._acr_last_score: float = 0.0
        if load_acr_client_from_env is not None:
            client, reason = load_acr_client_from_env(logger=self.logger)
            if client is not None:
                self._acr_client = client
                self._acr_enabled = True
                self.logger.info(
                    "ACRCloud 背景音乐识别启用，片段 %.1fs，冷却 %.1fs",
                    self._acr_segment_sec,
                    self._acr_cooldown_sec,
                )
            elif reason:
                self.logger.info("ACRCloud 背景音乐识别未启用：%s", reason)
        else:
            self.logger.debug("ACRCloud 模块不可用，跳过背景音乐识别。")
        # Text noise filter to suppress fillers such as “嗯嗯” or long laughter
        self.noise_filter_enabled: bool = bool(int(os.getenv("LIVE_TEXT_NOISE_FILTER", "1")))
        self.noise_filter_min_chars: int = _env_int("LIVE_TEXT_NOISE_MIN_CHARS", 3, min_value=1, max_value=12)
        self.noise_filter_repeat_chars: int = _env_int("LIVE_TEXT_NOISE_REPEAT", 3, min_value=2, max_value=10)

    # ---------- Public API ----------
    async def start(self, live_url_or_id: str, session_id: Optional[str] = None) -> LiveAudioStatus:
        if self._status.is_running:
            raise RuntimeError("live audio service already running")

        live_id = _parse_live_id(live_url_or_id)
        if not live_id:
            raise RuntimeError("invalid Douyin live URL or ID")

        # Resolve stream using StreamCap handler
        handler = get_platform_handler(live_url=f"https://live.douyin.com/{live_id}")
        if handler is None:
            raise RuntimeError("unsupported live URL")
        info = await handler.get_stream_info(f"https://live.douyin.com/{live_id}")
        # StreamCap returns a StreamData object (attrs) but defensive fallback supports dict
        if isinstance(info, dict):
            is_live = info.get("is_live")
            record_url = info.get("record_url") or info.get("flv_url") or info.get("m3u8_url")
            anchor_name = info.get("anchor_name")
            resolved_live_url = info.get("live_url")
        else:
            is_live = getattr(info, "is_live", None)
            record_url = (
                getattr(info, "record_url", None)
                or getattr(info, "flv_url", None)
                or getattr(info, "m3u8_url", None)
            )
            anchor_name = getattr(info, "anchor_name", None)
            resolved_live_url = getattr(info, "live_url", None)

        if is_live is False:
            raise RuntimeError(
                f"直播间未开播，无法拉流（{anchor_name or live_id}）。请确认直播已开始后再试。"
            )

        if not record_url:
            raise RuntimeError("failed to resolve record URL (streams unavailable)")

        # Init SenseVoice on demand
        await self._ensure_sv()
        if self._sv is None:
            raise RuntimeError("SenseVoice initialize failed")

        self._status = LiveAudioStatus(
            is_running=True,
            live_url=str(resolved_live_url or f"https://live.douyin.com/{live_id}"),
            live_id=live_id,
            session_id=session_id or f"live_{int(time.time())}",
            started_at=_now(),
        )
        self._agc_gain = 1.0
        self._init_diarizer()
        if self._sv is not None:
            seed_terms: List[str] = []
            if anchor_name:
                seed_terms.append(str(anchor_name))
            seed_terms.append(live_id)
            try:
                self._sv.update_hotwords(self._status.session_id, seed_terms)  # type: ignore[attr-defined]
            except Exception:
                pass
        self._music_ema = 0.0
        self._music_flag = False
        self._music_release_counter = 0
        self._status.music_guard_active = False
        self._status.music_guard_score = 0.0
        self._status.music_last_title = None
        self._status.music_last_score = 0.0
        self._status.music_last_detected_at = 0.0
        if self._acr_enabled:
            self._acr_buffer.clear()
            self._acr_last_attempt = 0.0
            self._acr_active_until = 0.0
            self._acr_last_match = None
            self._acr_last_title = None
            self._acr_last_score = 0.0
            if self._acr_pending_task and not self._acr_pending_task.done():
                self._acr_pending_task.cancel()
            self._acr_pending_task = None
        # reset streaming state
        self._partial_text = ""
        self._vad_in_speech = False
        self._vad_silence_acc = 0.0
        self._vad_speech_acc = 0.0
        self._vad_buf = bytearray()
        # Prepare persistence writer
        if self.persist_enabled and JSONLWriter is not None:
            try:
                root = Path(self.persist_root or (PROJECT_ROOT / "records" / "live_logs")).resolve()
                day = time.strftime("%Y-%m-%d", time.localtime())
                out_dir = root / (self._status.live_id or "unknown") / day
                self._persist_tr = JSONLWriter(out_dir / f"transcripts_{self._status.session_id}.jsonl")
                self._persist_tr.open()
            except Exception:
                self._persist_tr = None

        # Start ffmpeg to pipe raw PCM s16le 16k mono to stdout
        headers = []
        if "douyin" in record_url:
            # Add compatible headers for Douyin CDN, especially HLS
            ua = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/127 Safari/537.36"
            )
            headers.extend(["-headers", f"referer:https://live.douyin.com"])
            headers.extend(["-headers", f"user-agent:{ua}"])
            if ".m3u8" in (record_url or ""):
                headers.extend(["-headers", "accept:application/vnd.apple.mpegurl"])
        # Resolve ffmpeg binary: env FFMPEG_BIN > PATH > local tools/ffmpeg/*/bin
        ffmpeg_bin = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg") or str(
            (PROJECT_ROOT / "tools" / "ffmpeg" / ("win64" if os.name == "nt" else ("mac" if sys.platform == "darwin" else "linux")) / "bin" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")).resolve()
        )
        cmd = [
            ffmpeg_bin,
            "-loglevel",
            "warning",
            *headers,
            "-i",
            record_url,
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "s16le",
            "pipe:1",
        ]
        self._ffmpeg = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._status.ffmpeg_pid = self._ffmpeg.pid
        self._stop_evt.clear()
        self._reader_task = asyncio.create_task(self._read_loop())
        return self._status

    async def stop(self) -> LiveAudioStatus:
        # Stop loops
        self._stop_evt.set()
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None

        # Stop ffmpeg gracefully
        if self._ffmpeg:
            try:
                if os.name != "nt":
                    self._ffmpeg.send_signal(signal.SIGINT)
                else:
                    if self._ffmpeg.stdin:
                        self._ffmpeg.stdin.write(b"q")
                        await self._ffmpeg.stdin.drain()
                try:
                    await asyncio.wait_for(self._ffmpeg.wait(), timeout=8)
                except asyncio.TimeoutError:
                    self._ffmpeg.kill()
            except ProcessLookupError:
                pass
            self._ffmpeg = None

        self._status.is_running = False
        self._status.music_guard_active = False
        self._status.music_guard_score = 0.0
        self._status.music_last_title = None
        self._status.music_last_score = 0.0
        self._status.music_last_detected_at = 0.0
        if self._acr_pending_task and not (self._acr_pending_task.done()):
            self._acr_pending_task.cancel()
        self._acr_pending_task = None
        self._acr_buffer.clear()
        self._acr_active_until = 0.0
        self._acr_last_match = None
        self._acr_last_title = None
        self._acr_last_score = 0.0
        # Close persistence writer
        try:
            if self._persist_tr is not None:
                self._persist_tr.close()
        except Exception:
            pass
        self._persist_tr = None
        return self._status

    def status(self) -> LiveAudioStatus:
        return self._status

    # ---------- Profiles ----------
    def apply_profile(self, profile: str) -> None:
        """Apply a preset for latency vs. stability.
        - 'fast': lower end-to-end latency with robust filters
        - 'stable': more conservative VAD/assembler for highest accuracy
        Caller may still override specific params afterwards via API.
        """
        p = (profile or "").strip().lower()
        if p not in {"fast", "stable"}:
            p = "fast"
        self.profile = p
        if p == "fast":
            # Streaming granularity
            self.chunk_seconds = 0.4
            # VAD
            self.vad_min_rms = 0.012
            self.vad_min_speech_sec = 0.30
            self.vad_min_silence_sec = 0.45
            self.vad_hangover_sec = 0.18
            self.vad_force_flush_sec = 4.5
            self.vad_force_flush_overlap_sec = 0.25
            # Guard
            self._guard = HallucinationGuard(min_rms=0.014, min_len=2, low_conf=0.55)
            # Assembler
            self._assembler = SentenceAssembler(max_wait=1.8, max_chars=60, silence_flush=1)
            self.min_sentence_chars = 5
        else:  # stable
            self.chunk_seconds = 0.8
            self.vad_min_rms = 0.018
            self.vad_min_speech_sec = 0.50
            self.vad_min_silence_sec = 0.80
            self.vad_hangover_sec = 0.30
            self.vad_force_flush_sec = 6.0
            self.vad_force_flush_overlap_sec = 0.30
            self._guard = HallucinationGuard(min_rms=0.018, min_len=2, low_conf=0.50)
            self._assembler = SentenceAssembler(max_wait=3.5, max_chars=60, silence_flush=2)
            self.min_sentence_chars = 8
        # Clear transient states so the new profile takes effect smoothly
        self._partial_text = ""
        self._stable_prev_norm = ""
        self._stable_hits = 0
        self._last_sent_norms.clear()
        self._apply_env_overrides()

    def _apply_env_overrides(self) -> None:
        """Override key VAD knobs via environment variables for fast tuning."""
        self.chunk_seconds = _env_float("LIVE_VAD_CHUNK_SEC", self.chunk_seconds, min_value=0.2, max_value=2.0)
        self.vad_min_rms = _env_float("LIVE_VAD_MIN_RMS", self.vad_min_rms, min_value=0.001, max_value=0.2)
        self.vad_min_speech_sec = _env_float(
            "LIVE_VAD_MIN_SPEECH_SEC", self.vad_min_speech_sec, min_value=0.2, max_value=2.5
        )
        self.vad_min_silence_sec = _env_float(
            "LIVE_VAD_MIN_SILENCE_SEC", self.vad_min_silence_sec, min_value=0.2, max_value=2.5
        )
        self.vad_hangover_sec = _env_float("LIVE_VAD_HANGOVER_SEC", self.vad_hangover_sec, min_value=0.1, max_value=1.5)
        self.vad_force_flush_sec = _env_float(
            "LIVE_VAD_FORCE_FLUSH_SEC", self.vad_force_flush_sec, min_value=2.0, max_value=15.0
        )
        self.vad_force_flush_overlap_sec = _env_float(
            "LIVE_VAD_FORCE_FLUSH_OVERLAP",
            self.vad_force_flush_overlap_sec,
            min_value=0.0,
            max_value=1.5,
        )
        # min sentence chars is quite sensitive; keep parity with assembler defaults
        self.min_sentence_chars = _env_int(
            "LIVE_VAD_MIN_SENTENCE_CHARS", self.min_sentence_chars, min_value=0, max_value=128
        )

    # WebSocket/consumer hooks
    def add_transcription_callback(self, name: str, cb: Callable[[Dict[str, Any]], Awaitable[None] | None]) -> None:
        self._tr_callbacks[name] = cb

    def remove_transcription_callback(self, name: str) -> None:
        self._tr_callbacks.pop(name, None)

    def add_level_callback(self, name: str, cb: Callable[[float, float], Awaitable[None] | None]) -> None:
        self._level_callbacks[name] = cb

    def remove_level_callback(self, name: str) -> None:
        self._level_callbacks.pop(name, None)

    # ---------- Internals ----------
    async def _ensure_sv(self) -> None:
        """Ensure a single Small+VAD SenseVoice instance is loaded.
        Prefer a local checkout under models/models/iic/* if available to avoid network.
        """
        def _resolve_small_model_id() -> str:
            root = Path(__file__).resolve().parents[3]
            local_dir = root / "models" / "models" / "iic" / "SenseVoiceSmall"
            try:
                if local_dir.exists():
                    return str(local_dir)
            except Exception:
                pass
            return "iic/SenseVoiceSmall"

        def _resolve_vad_model_id() -> str:
            root = Path(__file__).resolve().parents[3]
            local_vad = root / "models" / "models" / "iic" / "speech_fsmn_vad_zh-cn-16k-common-pytorch"
            try:
                if local_vad.exists():
                    return str(local_vad)
            except Exception:
                pass
            return "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"

        desired_mid = _resolve_small_model_id()
        # If already loaded with desired id, keep it
        if self._sv is not None:
            try:
                cur = (self._sv.get_model_info() or {}).get("model_id")  # type: ignore
            except Exception:
                cur = None
            if cur and str(cur) == desired_mid:
                return
            try:
                await self._sv.cleanup()  # type: ignore
            except Exception:
                pass
            self._sv = None

        cfg = SenseVoiceConfig(model_id=desired_mid, vad_model_id=_resolve_vad_model_id())
        sv = SenseVoiceService(cfg)
        ok = await sv.initialize()
        if ok:
            self._sv = sv
            self._model_size = "small"
            return
        # Failed to init
        self._sv = None

    async def _read_loop(self) -> None:
        assert self._ffmpeg and self._ffmpeg.stdout
        # chunk bytes for s16le @ 16k mono
        chunk_bytes = int(self.chunk_seconds * 16000 * 2)
        buf = bytearray()
        try:
            while not self._stop_evt.is_set():
                data = await self._ffmpeg.stdout.read(chunk_bytes)
                if not data:
                    await asyncio.sleep(0.01)
                    continue
                buf.extend(data)
                while len(buf) >= chunk_bytes:
                    frame = bytes(buf[:chunk_bytes])
                    del buf[:chunk_bytes]
                    if self.mode == "vad":
                        await self._handle_audio_chunk_vad(frame)
                    else:
                        await self._handle_audio_chunk(frame)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            await self._emit({
                "type": "error",
                "data": {"message": f"audio read error: {e}"},
            })

    async def _handle_audio_chunk(self, pcm16: bytes) -> None:
        # Level feedback with automatic gain control
        raw_rms = pcm16_rms(pcm16)
        pcm16 = self._apply_gain_control(pcm16, raw_rms)
        lvl = pcm16_rms(pcm16)
        await self._emit_level(lvl, _now())
        self._update_speaker_state(pcm16, self.chunk_seconds)

        # Blank/silent chunks are frequent; still pass through guard/assembler
        if not self._sv:
            return

        self._status.total_audio_chunks += 1
        session_key = self._status.session_id or self._status.live_id or "live_default"
        bias_terms = self._collect_bias_terms()
        try:
            res = await self._sv.transcribe_audio(
                pcm16,
                session_id=session_key,
                bias_phrases=bias_terms,
            )
        except Exception as e:
            self._status.failed_transcriptions += 1
            await self._emit({
                "type": "error",
                "data": {"message": str(e)},
            })
            return

        text_raw = (res or {}).get("text") or ""
        ok = bool((res or {}).get("success")) and bool(text_raw)
        conf = float((res or {}).get("confidence") or 0.0)
        if not ok:
            # Silence tick: may force a sentence
            maybe = self._assembler.mark_silence()
            if maybe:
                # finalize current buffered sentence
                if self.noise_filter_enabled and self._should_skip_text(maybe, conf):
                    self._partial_text = ""
                    return
                self._partial_text = ""
                self._update_context_terms(maybe)
                await self._emit_delta("final", maybe, conf)
            return

        clean = self._cleaner.clean(text_raw)
        clean = self._apply_corrections(clean)
        # Hotword replace
        if self._hotword is not None and clean:
            try:
                clean = self._hotword.apply(clean)
            except Exception:
                pass
        # Anti-hallucination
        if self._guard.should_drop(clean, conf, lvl):
            return

        is_final, buf_or_sent = self._assembler.feed(clean)
        # Time-based forced flush to avoid long waiting without punctuation
        if not is_final:
            tick_out = self._assembler.tick()
            if tick_out:
                is_final, buf_or_sent = True, tick_out
        if self.mode == "sentence":
            # Only emit when sentence completes (with stability gating)
            if is_final:
                # too short? treat as partial preview
                if self.min_sentence_chars and len(buf_or_sent) < self.min_sentence_chars:
                    new_buf = buf_or_sent
                    delta = self._compute_delta(self._partial_text, new_buf)
                    self._partial_text = new_buf
                    if delta:
                        await self._emit_delta("append", delta, conf)
                else:
                    ended_by_punc = bool(buf_or_sent and buf_or_sent[-1] in "。！？；")
                    if not ended_by_punc:
                        n = self._normalize_text(buf_or_sent)
                        if n == self._stable_prev_norm:
                            self._stable_hits += 1
                        else:
                            self._stable_prev_norm = n
                            self._stable_hits = 1
                        if self._stable_hits < 2:
                            # hold for one more confirmation
                            new_buf = buf_or_sent
                            delta = self._compute_delta(self._partial_text, new_buf)
                            self._partial_text = new_buf
                            if delta:
                                await self._emit_delta("append", delta, conf)
                            return
                    # finalize
                    self._stable_prev_norm = ""
                    self._stable_hits = 0
                    self._partial_text = ""
                    if self.noise_filter_enabled and self._should_skip_text(buf_or_sent, conf):
                        return
                    if not self._is_duplicate_sentence(buf_or_sent):
                        self._update_context_terms(buf_or_sent)
                        await self._emit_delta("final", buf_or_sent, conf)
        else:
            # delta mode (default)
            if is_final:
                # Optional: enforce minimum sentence length (skip too short finals)
                if self.min_sentence_chars and len(buf_or_sent) < self.min_sentence_chars:
                    # treat as partial append instead
                    new_buf = buf_or_sent
                    delta = self._compute_delta(self._partial_text, new_buf)
                    self._partial_text = new_buf
                    if delta:
                        await self._emit_delta("append", delta, conf)
                else:
                    self._partial_text = ""
                    if self.noise_filter_enabled and self._should_skip_text(buf_or_sent, conf):
                        return
                    # duplicate suppression at sentence level
                    if not self._is_duplicate_sentence(buf_or_sent):
                        self._update_context_terms(buf_or_sent)
                        await self._emit_delta("final", buf_or_sent, conf)
            else:
                new_buf = buf_or_sent
                delta = self._compute_delta(self._partial_text, new_buf)
                self._partial_text = new_buf
                if delta:
                    await self._emit_delta("append", delta, conf)
        self._status.successful_transcriptions += 1
        # update rolling average
        s = self._status
        s.average_confidence = (
            (s.average_confidence * (s.successful_transcriptions - 1) + conf)
            / max(1, s.successful_transcriptions)
        )

        # full message for compatibility（sentence/delta 都发）
        await self._emit({
            "type": "transcription",
            "data": {
                "text": buf_or_sent,
                "confidence": conf,
                "timestamp": _now(),
                "is_final": is_final if self.mode != "sentence" else is_final,
                "room_id": self._status.live_id,
                "session_id": self._status.session_id,
                "words": res.get("words", []),
                "speaker": self._last_speaker_label,
                "speaker_debug": self._last_speaker_debug,
            },
        })
        # Persist also in non-VAD path when a final is emitted
        if is_final:
            try:
                if self._persist_tr is not None:
                    self._persist_tr.write({
                        "type": "transcription",
                        "text": buf_or_sent,
                        "confidence": conf,
                        "timestamp": _now(),
                        "is_final": True,
                        "room_id": self._status.live_id,
                        "session_id": self._status.session_id,
                        "words": res.get("words", []),
                        "speaker": self._last_speaker_label,
                        "speaker_debug": self._last_speaker_debug,
                    })
            except Exception:
                pass

    async def _emit(self, msg: Dict[str, Any]) -> None:
        # Fan out to callbacks; tolerate failures
        for _, cb in list(self._tr_callbacks.items()):
            try:
                r = cb(msg)
                if asyncio.iscoroutine(r):
                    await r
            except Exception:
                pass

    async def _emit_level(self, rms: float, ts: float) -> None:
        for _, cb in list(self._level_callbacks.items()):
            try:
                r = cb(rms, ts)
                if asyncio.iscoroutine(r):
                    await r
            except Exception:
                pass

    async def _emit_delta(self, op: str, text: str, confidence: float) -> None:
        await self._emit({
            "type": "transcription_delta",
            "data": {
                "op": op,
                "text": text,
                "timestamp": _now(),
                "confidence": confidence,
                "speaker": self._last_speaker_label,
                "speaker_debug": self._last_speaker_debug,
            },
        })

    def _acr_ingest_chunk(self, pcm16: bytes) -> None:
        if not self._acr_enabled or self._acr_client is None or not pcm16:
            return
        # 仅在背景音乐检测触发时累积，避免频繁打 API
        if self._music_flag:
            self._acr_buffer.extend(pcm16)
            max_bytes = self._acr_target_bytes * 2
            if len(self._acr_buffer) > max_bytes:
                # 保留最新窗口数据，丢掉旧的
                del self._acr_buffer[:-self._acr_target_bytes]
            ready = len(self._acr_buffer) >= self._acr_target_bytes
            cooldown_ready = (_now() - self._acr_last_attempt) >= self._acr_cooldown_sec
            pending = self._acr_pending_task and not self._acr_pending_task.done()
            if ready and cooldown_ready and not pending:
                payload = bytes(self._acr_buffer)
                self._acr_buffer.clear()
                self._acr_pending_task = asyncio.create_task(self._acr_identify(payload))
        else:
            if self._acr_buffer:
                self._acr_buffer.clear()

    async def _acr_identify(self, pcm_payload: bytes) -> None:
        self._acr_last_attempt = _now()
        try:
            client = self._acr_client
            if client is None or not pcm_payload:
                return
            loop = asyncio.get_running_loop()
            match = await loop.run_in_executor(None, client.identify, pcm_payload)
            if not match:
                return
            now = _now()
            # 持续认为背景音乐有效一段时间，配合 VAD 调整阈值
            self._acr_active_until = max(self._acr_active_until, now + self._acr_match_hold_sec)
            self._acr_last_match = match
            self._acr_last_title = match.title or match.artist or "unknown"
            self._acr_last_score = match.score
            self._status.music_last_title = self._acr_last_title
            self._status.music_last_score = match.score
            self._status.music_last_detected_at = now
            self._status.music_guard_active = True
            self._status.music_guard_score = max(self._status.music_guard_score, match.score)
            self._music_flag = True
            self.logger.info(
                "ACRCloud 检测到背景音乐: %s | %s (score=%.2f)",
                match.title or "未知曲目",
                match.artist or "",
                match.score,
            )
        except Exception as exc:  # pragma: no cover - 防御性
            self.logger.warning("ACRCloud 识别任务异常: %s", exc)
        finally:
            self._acr_pending_task = None

    def _init_diarizer(self) -> None:
        if OnlineDiarizer is None:
            print("[说话人分离] OnlineDiarizer 类未导入，说话人分离功能不可用")
            self._diarizer = None
            self._last_speaker_label = "unknown"
            self._last_speaker_debug = {}
            return
        
        enroll_sec = _env_float("LIVE_DIARIZER_ENROLL_SEC", 4.0, min_value=1.0, max_value=20.0)
        max_speakers = _env_int("LIVE_DIARIZER_MAX_SPEAKERS", 2, min_value=1, max_value=4)
        smooth = _env_float("LIVE_DIARIZER_SMOOTH", 0.2, min_value=0.05, max_value=0.6)
        
        print(f"[说话人分离] 初始化参数: 注册时长={enroll_sec}s, 最大说话人数={max_speakers}, 平滑系数={smooth}")
        
        try:
            self._diarizer = OnlineDiarizer(
                sr=16000,
                max_speakers=max_speakers,
                enroll_sec=enroll_sec,
                smooth=smooth,
            )
            print(f"[说话人分离] OnlineDiarizer 初始化成功: {type(self._diarizer)}")
        except Exception as e:
            print(f"[说话人分离] OnlineDiarizer 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            self._diarizer = None
            
        warmup_default = max(0.0, enroll_sec * 0.75)
        warmup_env = os.getenv("LIVE_DIARIZER_WARMUP_SEC")
        if warmup_env is not None:
            self._diarizer_warmup_sec = _env_float(
                "LIVE_DIARIZER_WARMUP_SEC",
                warmup_default,
                min_value=0.0,
                max_value=20.0,
            )
        else:
            self._diarizer_warmup_sec = warmup_default
            
        print(f"[说话人分离] 预热时间设置为: {self._diarizer_warmup_sec}s")
        
        self._last_speaker_label = "unknown"
        self._last_speaker_debug = {}
        
        if self._diarizer is not None:
            print("[说话人分离] 说话人分离器已成功启用")
        else:
            print("[说话人分离] 说话人分离器启用失败，将使用默认标签")

    def _apply_gain_control(self, pcm16: bytes, rms: float) -> bytes:
        if not self.agc_enabled or np is None or not pcm16:
            return pcm16
        if rms <= 1e-5:
            return pcm16
        desired_gain = self.agc_target_rms / max(rms, 1e-5)
        desired_gain = min(self.agc_max_gain, max(self.agc_min_gain, desired_gain))
        self._agc_gain = (1.0 - self.agc_smooth) * self._agc_gain + self.agc_smooth * desired_gain
        try:
            arr = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32)
            arr *= self._agc_gain
            np.clip(arr, -32768, 32767, out=arr)
            return arr.astype(np.int16).tobytes()
        except Exception:
            return pcm16

    def _update_speaker_state(self, pcm16: bytes, frame_sec: float) -> None:
        if self._diarizer is None or not pcm16:
            return
        try:
            label, dbg = self._diarizer.feed(pcm16, frame_sec or self.chunk_seconds or 0.8)
            observed_sec = 0.0
            state = getattr(self._diarizer, "state", None)
            if state is not None:
                observed_sec = float(getattr(state, "enrolled_sec", 0.0))
            ready = observed_sec >= max(0.0, self._diarizer_warmup_sec or 0.0)
            
            # 详细日志记录
            print(f"[说话人分离] 音频长度: {len(pcm16)}字节, 时长: {frame_sec:.3f}s")
            print(f"[说话人分离] 观察时长: {observed_sec:.3f}s, 预热阈值: {self._diarizer_warmup_sec:.3f}s, 就绪: {ready}")
            print(f"[说话人分离] 原始标签: {label}, 调试信息: {dbg}")
            
            if not ready:
                self._last_speaker_label = "unknown"
                print(f"[说话人分离] 预热中，设置标签为: unknown")
            else:
                self._last_speaker_label = label or "unknown"
                print(f"[说话人分离] 已就绪，设置标签为: {self._last_speaker_label}")
            
            dbg_payload: Dict[str, float] = {}
            if isinstance(dbg, dict):
                dbg_payload.update({k: float(v) for k, v in dbg.items()})
            dbg_payload["observed_sec"] = float(observed_sec)
            dbg_payload["warmup_remaining"] = float(max(0.0, (self._diarizer_warmup_sec or 0.0) - observed_sec))
            self._last_speaker_debug = dbg_payload
            
            print(f"[说话人分离] 最终调试信息: {self._last_speaker_debug}")
        except Exception as e:
            print(f"[说话人分离] 处理音频时发生错误: {e}")
            import traceback
            traceback.print_exc()

    def _should_skip_text(self, text: str, confidence: float) -> bool:
        """Heuristic noise filter to drop filler-only or heavily repeated subtitles."""
        if not text:
            return True
        normalized = re.sub(r"\s+", "", text)
        if not normalized:
            return True
        if self._acr_enabled and self._acr_active_until > _now():
            if confidence < 0.6 or not re.search(r"[\u4e00-\u9fff]", normalized):
                return True
        # Strip punctuation so we can evaluate repeated characters
        simple = re.sub(r"[，。,、！？!?~～…\-]", "", normalized)
        if not simple:
            return True
        filler_chars = set("嗯啊哦呀呃欸嘿呵哈哼唔额呢嘛哎噢唉哇咦呜")
        if len(simple) <= self.noise_filter_min_chars and all(ch in filler_chars for ch in simple):
            return True
        if self.noise_filter_repeat_chars and len(simple) >= self.noise_filter_repeat_chars:
            unique_chars = {ch for ch in simple if ch.strip()}
            if len(unique_chars) == 1:
                return True
        if re.fullmatch(r"(.)\1{2,}", simple):
            return True
        if re.fullmatch(r"[hH啊Aa哦Oo嗯Mm呀Yy呃Ee噢Oo欸Ee嘿Hh呵Hh哈Ha哼Hh唔Ww～~！!？?,.，。、…]*", normalized):
            return True
        # Keep low-confidence results; they may still deserve manual review downstream.
        return False

    def _apply_corrections(self, text: str) -> str:
        if not text or self._corrector is None:
            return text
        try:
            return self._corrector.correct(text, context_terms=list(self._context_terms))
        except Exception:
            return text

    def _update_context_terms(self, sentence: str) -> None:
        if not sentence:
            return
        terms = self._extract_candidate_terms(sentence)
        if not terms:
            return
        for term in terms:
            self._context_terms.append(term)
        if self._sv is not None:
            try:
                session_key = self._status.session_id or self._status.live_id
                self._sv.update_hotwords(session_key, terms)  # type: ignore[attr-defined]
            except Exception:
                pass
        if self._corrector is not None:
            try:
                self._corrector.extend_context(terms)
            except Exception:
                pass

    def _collect_bias_terms(self) -> List[str]:
        if not self._context_terms:
            return []
        seen: set[str] = set()
        result: List[str] = []
        for term in reversed(self._context_terms):
            if term in seen:
                continue
            seen.add(term)
            result.append(term)
            if len(result) >= 24:
                break
        result.reverse()
        return result

    @staticmethod
    def _extract_candidate_terms(text: str) -> List[str]:
        if not text:
            return []
        return re.findall(r"[\u4e00-\u9fa5]{2,4}", text)

    def _compute_delta(self, prev: str, curr: str) -> str:
        """Compute incremental delta between previous and current partial text.
        - If curr starts with prev, return the tail.
        - Else trim the longest suffix of prev that matches a prefix of curr.
        This reduces duplicate appends when the model repeats context.
        """
        if not curr:
            return ""
        if not prev:
            return curr
        if curr.startswith(prev):
            return curr[len(prev):]
        max_olap = min(len(prev), len(curr), 64)
        for k in range(max_olap, 0, -1):
            if prev[-k:] == curr[:k]:
                return curr[k:]
        return curr

    def _estimate_music_score(self, pcm16: bytes) -> float:
        if not self.music_detection_enabled or np is None or not pcm16:
            return 0.0
        try:
            arr = np.frombuffer(pcm16, dtype=np.int16)
        except ValueError:  # pragma: no cover - defensive
            return 0.0
        if arr.size == 0:
            return 0.0
        arr = arr.astype(np.float32)
        arr /= 32768.0
        if not np.any(arr):
            return 0.0
        spec = np.abs(np.fft.rfft(arr))
        spec_sum = float(spec.sum()) + 1e-6
        low_idx = max(1, int(spec.size * 0.08))
        mid_idx = max(low_idx + 1, int(spec.size * 0.45))
        low = float(spec[:low_idx].sum())
        mid = float(spec[low_idx:mid_idx].sum())
        high = float(spec[mid_idx:].sum())
        band_energy_ratio = (low + high) / (mid + 1e-6)
        sign = np.sign(arr)
        zcr = float(np.mean((sign[:-1] * sign[1:]) < 0.0))
        spectral_flatness = float(
            np.exp(np.mean(np.log(spec + 1e-6))) / (np.mean(spec) + 1e-6)
        )
        band_component = min(1.5, band_energy_ratio * 0.6)
        zcr_component = min(1.0, zcr * 1.2)
        tonal_component = 1.0 - max(0.0, min(1.0, spectral_flatness))
        score = 0.5 * band_component + 0.3 * zcr_component + 0.2 * tonal_component
        if score < 0.0:
            score = 0.0
        if score > 1.0:
            score = 1.0
        return float(score)

    def _update_music_flag(self) -> None:
        if not self.music_detection_enabled:
            if self._music_flag:
                self._music_flag = False
                self._music_release_counter = 0
            return
        if self._music_flag:
            if self._music_ema < self.music_release_threshold:
                self._music_release_counter += 1
            else:
                self._music_release_counter = 0
            if self._music_release_counter >= self.music_release_frames:
                self._music_flag = False
                self._music_release_counter = 0
                if _now() - self._music_last_notice >= 5.0:
                    print(f"[背景音乐监测] 背景音乐降至安全阈值，恢复默认 VAD。score={self._music_ema:.2f}")
                    self._music_last_notice = _now()
        else:
            if self._music_ema >= self.music_detect_threshold:
                self._music_flag = True
                self._music_release_counter = 0
                if _now() - self._music_last_notice >= 1.5:
                    print(f"[背景音乐监测] 检测到持续背景音乐，自动提高 VAD 门限。score={self._music_ema:.2f}")
                    self._music_last_notice = _now()

    # ------------- VAD mode -------------
    async def _handle_audio_chunk_vad(self, pcm16: bytes) -> None:
        # Simple energy-based VAD with hangover using RMS
        raw_rms = pcm16_rms(pcm16)
        pcm16 = self._apply_gain_control(pcm16, raw_rms)
        lvl = pcm16_rms(pcm16)
        await self._emit_level(lvl, _now())
        self._update_speaker_state(pcm16, self.chunk_seconds)
        frame_sec = self.chunk_seconds
        if self.music_detection_enabled:
            music_score = self._estimate_music_score(pcm16)
            alpha = self.music_detect_alpha
            self._music_ema = (1 - alpha) * self._music_ema + alpha * music_score
            self._update_music_flag()
            self._status.music_guard_score = float(round(self._music_ema, 4))
            self._status.music_guard_active = self._music_flag
        else:
            # 缓慢衰减，避免长时间保持高值
            self._music_ema *= 0.9
            if self._music_ema < 0.01:
                self._music_ema = 0.0
            if self._status.music_guard_active or self._status.music_guard_score:
                self._status.music_guard_active = False
                self._status.music_guard_score = 0.0
        self._acr_ingest_chunk(pcm16)

        effective_rms = self.vad_min_rms
        effective_min_speech_sec = self.vad_min_speech_sec
        effective_min_silence_sec = self.vad_min_silence_sec
        if self.music_detection_enabled and self._music_flag:
            effective_rms *= self.music_rms_boost
            effective_min_speech_sec *= self.music_min_speech_boost
            effective_min_silence_sec *= self.music_min_silence_scale

        # 固定门限：仅使用简洁的 RMS+挂起逻辑（回退到 Small+VAD 统一策略）
        speaking = lvl >= effective_rms
        if speaking:
            self._vad_speech_acc += frame_sec
            self._vad_silence_acc = 0.0
            # enter speech once min_speech satisfied
            if not self._vad_in_speech and self._vad_speech_acc >= effective_min_speech_sec:
                self._vad_in_speech = True
                print(f"[延迟监控] VAD检测到语音开始，累计语音时长: {self._vad_speech_acc:.3f}s")
            # accumulate audio if speaking or already in speech
            self._vad_buf.extend(pcm16)
        else:
            self._vad_silence_acc += frame_sec
            # still keep audio during hangover while in speech
            if self._vad_in_speech and self._vad_silence_acc <= self.vad_hangover_sec:
                self._vad_buf.extend(pcm16)

        # finalize when in_speech and silence >= min_silence
        if self._vad_in_speech:
            if self._vad_silence_acc >= effective_min_silence_sec:
                print(f"[延迟监控] VAD检测到语音结束，静音时长: {self._vad_silence_acc:.3f}s，缓冲区大小: {len(self._vad_buf)}字节")
                await self._finalize_vad_segment(force=False)
            elif (
                self.vad_force_flush_sec > 0.0
                and self._vad_speech_acc >= self.vad_force_flush_sec
            ):
                print(f"[延迟监控] VAD长语音超时强制输出，累计语音时长: {self._vad_speech_acc:.3f}s，缓冲区大小: {len(self._vad_buf)}字节")
                await self._finalize_vad_segment(force=True)

    async def _finalize_vad_segment(self, *, force: bool = False) -> None:
        # 延迟监控：记录VAD段处理开始时间
        vad_start_time = _now()
        seg = bytes(self._vad_buf)
        if force:
            overlap_bytes = int(self.vad_force_flush_overlap_sec * 16000 * 2)
            if overlap_bytes > 0 and overlap_bytes < len(seg):
                keep_tail = seg[-overlap_bytes:]
                seg = seg[:-overlap_bytes]
                self._vad_buf = bytearray(keep_tail)
            else:
                self._vad_buf = bytearray()
            self._vad_in_speech = True
            self._vad_silence_acc = 0.0
            self._vad_speech_acc = len(self._vad_buf) / 32000.0
        else:
            self._vad_buf.clear()
            self._vad_in_speech = False
            self._vad_silence_acc = 0.0
            self._vad_speech_acc = 0.0
        if not seg:
            return
        # 不进行人声检测/音乐过滤与音量归一化（按你的要求精简为 Small+VAD 统一模式）
        self._status.total_audio_chunks += 1
        seg_duration = len(seg) / 32000.0
        self._update_speaker_state(seg, seg_duration)
        session_key = self._status.session_id or self._status.live_id or "live_default"
        bias_terms = self._collect_bias_terms()
        try:
            # 延迟监控：记录转录开始时间
            transcribe_start = _now()
            res = await self._sv.transcribe_audio(
                seg,
                session_id=session_key,
                bias_phrases=bias_terms,
            ) if self._sv else None
            # 延迟监控：计算转录耗时
            transcribe_duration = _now() - transcribe_start
            suffix = "（强制分段）" if force else ""
            print(f"[延迟监控] VAD段转录耗时: {transcribe_duration:.3f}s, 音频长度: {len(seg)/32000:.3f}s{suffix}")
        except Exception as e:
            self._status.failed_transcriptions += 1
            await self._emit({
                "type": "error",
                "data": {"message": str(e)},
            })
            return
        raw_text = ""
        if isinstance(res, dict):
            raw_text = str(res.get("text") or "").strip()
            if not raw_text:
                raw_text = str(res.get("text_postprocessed") or "").strip()
            if not raw_text:
                segs = res.get("segments")
                if isinstance(segs, list):
                    parts: List[str] = []
                    for seg_dict in segs:
                        if isinstance(seg_dict, dict):
                            t = str(seg_dict.get("text") or "").strip()
                            if t:
                                parts.append(t)
                    raw_text = " ".join(parts).strip()
        conf = float((res or {}).get("confidence") or 0.0)
        clean = self._cleaner.clean(raw_text) if raw_text else ""
        if not clean:
            clean = raw_text
        clean = (clean or "").strip()
        if not clean:
            return

        reason = "force_flush" if force else "vad_silence"
        effective_min_chars = 0 if force else self.min_sentence_chars

        # Secondary segmentation inside VAD segment: split by punctuation and length
        pending_short: str = ""
        for sent in self._split_sentences(clean):
            if not sent:
                continue
            candidate = f"{pending_short}{sent}" if pending_short else sent
            candidate = candidate.strip()
            if effective_min_chars and len(candidate) < effective_min_chars:
                pending_short = candidate
                continue
            pending_short = ""
            if not self._is_duplicate_sentence(candidate):
                await self._emit_delta("final", candidate, conf)
        if pending_short:
            candidate = pending_short.strip()
            if candidate and not self._is_duplicate_sentence(candidate):
                await self._emit_delta("final", candidate, conf)
        self._status.successful_transcriptions += 1
        s = self._status
        s.average_confidence = (
            (s.average_confidence * (s.successful_transcriptions - 1) + conf)
            / max(1, s.successful_transcriptions)
        )
        # Optionally emit the whole segment as one transcription record for compatibility
        await self._emit({
            "type": "transcription",
            "data": {
                "text": clean,
                "confidence": conf,
                "timestamp": _now(),
                "is_final": True,
                "room_id": self._status.live_id,
                "session_id": self._status.session_id,
                "words": res.get("words", []),
                "reason": reason,
                "speaker": self._last_speaker_label,
                "speaker_debug": self._last_speaker_debug,
            },
        })
        # Persist final transcription (VAD)
        try:
            if self._persist_tr is not None:
                self._persist_tr.write({
                    "type": "transcription",
                    "text": clean,
                    "confidence": conf,
                    "timestamp": _now(),
                    "is_final": True,
                    "room_id": self._status.live_id,
                    "session_id": self._status.session_id,
                    "words": res.get("words", []),
                    "reason": reason,
                    "speaker": self._last_speaker_label,
                    "speaker_debug": self._last_speaker_debug,
                })
        except Exception:
            pass

    def _is_duplicate_sentence(self, text: str) -> bool:
        n = self._normalize_text(text)
        if not n:
            return True
        for old in self._last_sent_norms[-2:]:
            # equal or containment both directions
            if n == old or n in old or old in n:
                return True
        # push
        self._last_sent_norms.append(n)
        if len(self._last_sent_norms) > 8:
            del self._last_sent_norms[: len(self._last_sent_norms) - 8]
        return False

    @staticmethod
    def _normalize_text(s: str) -> str:
        # remove spaces and unify punctuation to reduce duplicate variation
        if not s:
            return ""
        t = s.strip()
        t = (
            t.replace(",", "，").replace(";", "；").replace(":", "：")
            .replace("?", "？").replace("!", "！").replace(".", "。")
        )
        # remove spaces
        t = re.sub(r"\s+", "", t)
        # collapse duplicated puncts
        t = re.sub(r"([，。！？；：,…])\1+", r"\1", t)
        return t

    def _split_sentences(self, text: str) -> List[str]:
        """Split a large paragraph into sentences by punctuation and max_chars.
        Keep punctuation with the sentence; then trim whitespace.
        """
        out: List[str] = []
        buf = ""
        for ch in text:
            buf += ch
            if ch in "。！？；" or len(buf) >= getattr(self._assembler, "max_chars", 60):
                s = buf.strip()
                if s:
                    out.append(s)
                buf = ""
        if buf.strip():
            out.append(buf.strip())
        return out

    # --------- Model selection helpers ---------
    @staticmethod
    def _candidate_model_ids(size: str) -> List[str]:
        # Hard-locked: only Small is supported locally
        return ["iic/SenseVoiceSmall"]

    def set_model_size(self, size: str) -> None:
        # No-op: keep small
        self._model_size = "small"

    def get_model_size(self) -> str:
        return self._model_size

    async def preload_model(self, size: str) -> None:
        # Only preload small; ignore others
        try:
            self._preload_busy.add("small")
            tmp = SenseVoiceService(SenseVoiceConfig(model_id="iic/SenseVoiceSmall"))
            ok = await tmp.initialize()
            if ok:
                await tmp.cleanup()
        finally:
            self._preload_busy.discard("small")

    def get_preload_busy(self) -> List[str]:
        return list(sorted(self._preload_busy))

    def get_model_cache_status(self) -> Dict[str, Dict[str, Any]]:
        """Return cache presence for Small only under models/.cache."""
        root = Path(__file__).resolve().parents[3] / "models" / ".cache" / "models" / "iic"
        def stat_dir(d: Path) -> Dict[str, Any]:
            if not d.exists():
                return {"cached": False, "path": str(d), "bytes": 0}
            total = 0
            for p in d.rglob("*"):
                try:
                    if p.is_file():
                        total += p.stat().st_size
                except Exception:
                    pass
            return {"cached": True, "path": str(d), "bytes": total}
        return {"small": stat_dir(root / "SenseVoiceSmall")}

    # Advanced config
    # Advanced filters removed; keep no-op for backward compatibility
    def update_advanced(
        self,
        *,
        music_filter: Optional[bool] = None,
        diarization: Optional[bool] = None,
        max_speakers: Optional[int] = None,
        agc: Optional[bool] = None,
    ) -> Dict[str, Any]:
        if agc is not None:
            self.agc_enabled = bool(agc)
        if diarization is not None:
            if diarization:
                self._init_diarizer()
            else:
                self._diarizer = None
                self._last_speaker_label = "unknown"
                self._last_speaker_debug = {}
        if max_speakers is not None and self._diarizer is not None:
            try:
                self._diarizer.max_speakers = max(1, int(max_speakers))
            except Exception:
                pass
        return {
            "agc_enabled": self.agc_enabled,
            "agc_gain": round(self._agc_gain, 3),
            "diarizer_active": self._diarizer is not None,
            "max_speakers": getattr(self._diarizer, "max_speakers", 0) if self._diarizer else 0,
            "last_speaker": self._last_speaker_label,
        }

    # Persistence toggle (API-compatible with live_audio /advanced handler)
    def update_persist(self, *, enable: Optional[bool] = None, root: Optional[str] = None) -> Dict[str, Any]:
        if enable is not None:
            self.persist_enabled = bool(enable)
        if root is not None:
            self.persist_root = str(root)
        return {"persist_enabled": self.persist_enabled, "persist_root": self.persist_root or "records/live_logs"}

    # Hotwords update from API
    def update_hotwords(self, replace: Dict[str, List[str]]) -> None:
        try:
            if self._hotword is None and HotwordReplacer is not None:
                self._hotword = HotwordReplacer()
            if self._hotword is not None:
                self._hotword.set_rules(replace)  # type: ignore
        except Exception:
            pass


# Singleton accessor
_live_audio_service: Optional[LiveAudioStreamService] = None


def get_live_audio_service() -> LiveAudioStreamService:
    global _live_audio_service
    if _live_audio_service is None:
        _live_audio_service = LiveAudioStreamService()
    return _live_audio_service
