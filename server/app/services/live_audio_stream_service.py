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
import os
import re
import signal
import sys
import time
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional


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
    from server.utils.jsonl_writer import JSONLWriter  # type: ignore
except Exception:
    JSONLWriter = None  # type: ignore
# Removed optional audio gate / diarizer dependencies to simplify pipeline


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


class LiveAudioStreamService:
    """Single-session live audio stream transcriber."""

    def __init__(self) -> None:
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
        self.profile: str = "stable"
        default_profile = os.environ.get("LIVE_AUDIO_PROFILE", self.profile)
        try:
            self.apply_profile(default_profile)
        except Exception:
            # Ensure at least stable defaults when profile application fails
            self.apply_profile("stable")

        # Advanced filters removed (simplified pipeline)
        # Persistence (transcriptions)
        # 默认开启字幕持久化，保存到 records/live_logs/<live_id>/<YYYY-MM-DD>/
        self.persist_enabled: bool = True
        self.persist_root: Optional[str] = None
        self._persist_tr: Optional[Any] = None

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
            headers = ["-headers", "referer:https://live.douyin.com"]
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
            self.chunk_seconds = 0.5
            # VAD
            self.vad_min_rms = 0.015
            self.vad_min_speech_sec = 0.35
            self.vad_min_silence_sec = 0.55
            self.vad_hangover_sec = 0.22
            # Guard
            self._guard = HallucinationGuard(min_rms=0.016, min_len=2, low_conf=0.55)
            # Assembler
            self._assembler = SentenceAssembler(max_wait=2.2, max_chars=60, silence_flush=1)
            self.min_sentence_chars = 6
        else:  # stable
            self.chunk_seconds = 0.8
            self.vad_min_rms = 0.018
            self.vad_min_speech_sec = 0.50
            self.vad_min_silence_sec = 0.80
            self.vad_hangover_sec = 0.30
            self._guard = HallucinationGuard(min_rms=0.018, min_len=2, low_conf=0.50)
            self._assembler = SentenceAssembler(max_wait=3.5, max_chars=60, silence_flush=2)
            self.min_sentence_chars = 8
        # Clear transient states so the new profile takes effect smoothly
        self._partial_text = ""
        self._stable_prev_norm = ""
        self._stable_hits = 0
        self._last_sent_norms.clear()

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
        # Level feedback
        lvl = pcm16_rms(pcm16)
        await self._emit_level(lvl, _now())

        # Blank/silent chunks are frequent; still pass through guard/assembler
        if not self._sv:
            return

        self._status.total_audio_chunks += 1
        try:
            res = await self._sv.transcribe_audio(pcm16)
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
                self._partial_text = ""
                await self._emit_delta("final", maybe, conf)
            return

        clean = self._cleaner.clean(text_raw)
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
                    if not self._is_duplicate_sentence(buf_or_sent):
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
                    # duplicate suppression at sentence level
                    if not self._is_duplicate_sentence(buf_or_sent):
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
            },
        })

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

    # ------------- VAD mode -------------
    async def _handle_audio_chunk_vad(self, pcm16: bytes) -> None:
        # Simple energy-based VAD with hangover using RMS
        lvl = pcm16_rms(pcm16)
        await self._emit_level(lvl, _now())
        frame_sec = self.chunk_seconds
        # 固定门限：仅使用简洁的 RMS+挂起逻辑（回退到 Small+VAD 统一策略）
        speaking = lvl >= self.vad_min_rms
        if speaking:
            self._vad_speech_acc += frame_sec
            self._vad_silence_acc = 0.0
            # enter speech once min_speech satisfied
            if not self._vad_in_speech and self._vad_speech_acc >= self.vad_min_speech_sec:
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
        if self._vad_in_speech and self._vad_silence_acc >= self.vad_min_silence_sec:
            print(f"[延迟监控] VAD检测到语音结束，静音时长: {self._vad_silence_acc:.3f}s，缓冲区大小: {len(self._vad_buf)}字节")
            await self._finalize_vad_segment()

    async def _finalize_vad_segment(self) -> None:
        # 延迟监控：记录VAD段处理开始时间
        vad_start_time = _now()
        seg = bytes(self._vad_buf)
        self._vad_buf.clear()
        self._vad_in_speech = False
        self._vad_silence_acc = 0.0
        self._vad_speech_acc = 0.0
        if not seg:
            return
        # 不进行人声检测/音乐过滤与音量归一化（按你的要求精简为 Small+VAD 统一模式）
        self._status.total_audio_chunks += 1
        try:
            # 延迟监控：记录转录开始时间
            transcribe_start = _now()
            res = await self._sv.transcribe_audio(seg) if self._sv else None
            # 延迟监控：计算转录耗时
            transcribe_duration = _now() - transcribe_start
            print(f"[延迟监控] VAD段转录耗时: {transcribe_duration:.3f}s, 音频长度: {len(seg)/32000:.3f}s")
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
                    for seg in segs:
                        if isinstance(seg, dict):
                            t = str(seg.get("text") or "").strip()
                            if t:
                                parts.append(t)
                    raw_text = " ".join(parts).strip()
        conf = float((res or {}).get("confidence") or 0.0)
        # 不进行说话人分离
        speaker = None
        clean = self._cleaner.clean(raw_text) if raw_text else ""
        if not clean:
            clean = raw_text
        clean = (clean or "").strip()
        if not clean:
            return
        # Secondary segmentation inside VAD segment: split by punctuation and length
        pending_short: str = ""
        for sent in self._split_sentences(clean):
            if not sent:
                continue
            candidate = f"{pending_short}{sent}" if pending_short else sent
            candidate = candidate.strip()
            if self.min_sentence_chars and len(candidate) < self.min_sentence_chars:
                pending_short = candidate
                continue
            pending_short = ""
            if not self._is_duplicate_sentence(candidate):
                await self._emit_delta("final", candidate, conf)
        if pending_short:
            candidate = pending_short.strip()
            if candidate:
                if not self._is_duplicate_sentence(candidate):
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
    def update_advanced(self, *, music_filter: Optional[bool] = None, diarization: Optional[bool] = None, max_speakers: Optional[int] = None) -> Dict[str, Any]:
        return {}

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
