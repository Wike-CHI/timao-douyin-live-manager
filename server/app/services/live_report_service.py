"""
Live Report Service
Integrates StreamCap's recording backend (streamget + ffmpeg), collects Douyin
danmu, runs offline SenseVoice transcription on 30-minute segments, and composes
final transcript and a recap report artifact.

Notes:
- This service is backend-only; no StreamCap/Flet UI is used.
- Requires ffmpeg installed and available on PATH.
- For stream URL resolution we reuse StreamCap platform handlers.
- For transcription we reuse AST_module.sensevoice_service to run batch
  inference from 16k mono PCM (decoded from recorded segments).
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import signal
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# Workspace root on sys.path so we can import StreamCap modules
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Stream URL resolution (StreamCap backend)
from StreamCap.app.core.platforms.platform_handlers import (  # type: ignore
    get_platform_handler,
)

# Douyin web relay (existing service in this repo)
# NOTE: live_report_service.py lives in server/app/services/, so the sibling
# module is server/app/services/douyin_web_relay.py. The previous import used
# an incorrect three-level relative path (…services.*) which resolves to
# server/services/* and crashes with "No module named 'server.services'" when
# FastAPI includes this router. We import from the current package instead.
from .douyin_web_relay import get_douyin_web_relay  # type: ignore

# SenseVoice batch API: transcribe PCM16 mono @ 16k
from AST_module.sensevoice_service import (  # type: ignore
    SenseVoiceConfig,
    SenseVoiceService,
)


def _now_ts() -> int:
    return int(time.time() * 1000)


def _safe_name(s: str) -> str:
    s = re.sub(r"[\\/:*?\"<>|]", "_", s)
    s = re.sub(r"\s+", "_", s).strip("._")
    return s or "unknown"


def _parse_douyin_live_id(live_url: str) -> Optional[str]:
    # Expect https://live.douyin.com/<id>
    m = re.search(r"live\.douyin\.com/([A-Za-z0-9_\-]+)", live_url)
    return m.group(1) if m else None


@dataclass
class LiveReportStatus:
    session_id: str
    live_url: str
    room_id: Optional[str] = None
    anchor_name: Optional[str] = None
    platform_key: str = "douyin"
    started_at: int = field(default_factory=_now_ts)
    stopped_at: Optional[int] = None
    recording_pid: Optional[int] = None
    recording_dir: Optional[str] = None
    segment_seconds: int = 1800
    segments: List[Dict[str, Any]] = field(default_factory=list)  # {seq, path, start_ts, end_ts}
    comments_count: int = 0
    transcript_chars: int = 0
    report_path: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


class LiveReportService:
    def __init__(self, records_root: Optional[str] = None) -> None:
        self.records_root = Path(records_root or os.getenv("RECORDS_ROOT", "records")).resolve()
        self.records_root.mkdir(parents=True, exist_ok=True)
        self._session: Optional[LiveReportStatus] = None
        self._ffmpeg_proc: Optional[asyncio.subprocess.Process] = None
        self._comment_queue: Optional[asyncio.Queue] = None
        self._comments: List[Dict[str, Any]] = []
        self._comment_task: Optional[asyncio.Task] = None
        self._relay_client_queue: Optional[asyncio.Queue] = None

        # Shared ASR (lazy)
        self._sv: Optional[SenseVoiceService] = None
        # Rolling analysis state
        self._analysis: List[Dict[str, Any]] = []  # per-window results
        self._carry: str = ""
        # Aggregates for report
        self._agg: Dict[str, Any] = {
            "follows": 0,
            "entries": 0,
            "peak_viewers": 0,
            "like_total": 0,
            "gifts": {},  # name -> count
        }

    # ---------- Public API ----------
    async def start(self, live_url: str, segment_minutes: int = 30) -> LiveReportStatus:
        if self._session is not None:
            raise RuntimeError("Live report session already started")

        live_id = _parse_douyin_live_id(live_url)
        handler = get_platform_handler(live_url=live_url)
        if handler is None:
            raise RuntimeError("Unsupported live URL")
        info = await handler.get_stream_info(live_url)
        record_url = getattr(info, "flv_url", None) or getattr(info, "record_url", None)
        if not record_url:
            raise RuntimeError("Failed to resolve record URL")

        anchor = _safe_name(getattr(info, "anchor_name", ""))
        platform = getattr(info, "platform", "douyin") or "douyin"
        day = time.strftime("%Y-%m-%d", time.localtime())
        session_id = f"live_{platform}_{anchor}_{int(time.time())}"
        out_dir = self.records_root / platform / anchor / day / session_id
        out_dir.mkdir(parents=True, exist_ok=True)

        seg_secs = max(300, int(segment_minutes) * 60)
        pattern = str(out_dir / f"{anchor}_%Y%m%d_%H%M%S_%03d.mp4")

        self._session = LiveReportStatus(
            session_id=session_id,
            live_url=live_url,
            room_id=live_id,
            anchor_name=anchor,
            platform_key=platform,
            recording_dir=str(out_dir),
            segment_seconds=seg_secs,
        )

        # Start ffmpeg segment recording
        self._ffmpeg_proc = await self._start_ffmpeg(record_url, seg_secs, pattern)
        self._session.recording_pid = self._ffmpeg_proc.pid

        # Start Douyin relay and consume events into in-memory buffer
        relay = get_douyin_web_relay()
        if live_id:
            await relay.start(live_id)
        self._relay_client_queue = await relay.register_client()
        self._comment_task = asyncio.create_task(self._consume_danmu())

        return self._session

    async def stop(self) -> LiveReportStatus:
        if not self._session:
            raise RuntimeError("No active session")

        # Stop ffmpeg
        if self._ffmpeg_proc:
            await self._graceful_stop_ffmpeg(self._ffmpeg_proc)
            self._ffmpeg_proc = None

        # Stop relay and consumer
        try:
            relay = get_douyin_web_relay()
            if self._relay_client_queue:
                await relay.unregister_client(self._relay_client_queue)
            await relay.stop()
        except Exception:
            pass
        if self._comment_task:
            self._comment_task.cancel()
            try:
                await self._comment_task
            except asyncio.CancelledError:
                pass

        self._session.stopped_at = _now_ts()
        self._session.comments_count = len(self._comments)
        try:
            self._session.metrics = dict(self._agg)
        except Exception:
            pass

        # Capture existing segments (best effort)
        await self._scan_segments()
        return self._session

    async def generate_report(self) -> Dict[str, Any]:
        """Offline pipeline after stop(): transcribe segments, integrate comments, compose HTML.

        Returns a dict with artifact paths.
        """
        if not self._session:
            raise RuntimeError("No active session")

        out_dir = Path(self._session.recording_dir)
        artifacts_dir = out_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Persist danmu
        comments_path = artifacts_dir / "comments.jsonl"
        with comments_path.open("w", encoding="utf-8") as f:
            for ev in self._comments:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")

        # Transcribe each segment with SenseVoice
        transcripts: List[Dict[str, Any]] = []
        await self._scan_segments()
        sv = await self._get_sv()
        for seg in sorted(self._session.segments, key=lambda x: x.get("seq", 0)):
            seg_path = Path(seg["path"])  # mp4
            pcm_path = seg_path.with_suffix(".pcm")
            await self._extract_pcm(seg_path, pcm_path)
            pcm_bytes = pcm_path.read_bytes()
            res = await sv.transcribe_audio(pcm_bytes)
            text = res.get("text", "") or ""
            transcripts.append({
                "seq": seg.get("seq"),
                "path": str(seg_path),
                "text": text,
            })
        transcript_txt = "\n\n".join(
            [f"[Segment {t['seq']}]\n{t['text']}" for t in transcripts]
        )
        self._session.transcript_chars = len(transcript_txt)
        transcript_path = artifacts_dir / "transcript.txt"
        transcript_path.write_text(transcript_txt, encoding="utf-8")

        # Prefer rolling windows merged summary; fallback to one-shot if env provides
        ai_summary: Dict[str, Any] | None = None
        try:
            windows_dir = artifacts_dir / "windows"
            if windows_dir.exists() and self._analysis:
                merged = {
                    "summary": "\n\n".join([str(w.get("ai", {}).get("summary", "")) for w in self._analysis if isinstance(w, dict)]).strip(),
                    "highlight_points": [],
                    "risks": [],
                    "suggestions": [],
                    "top_questions": [],
                    "scripts": [],
                }
                for w in self._analysis:
                    aiw = w.get("ai") or {}
                    for k in ("highlight_points", "risks", "suggestions", "top_questions", "scripts"):
                        v = aiw.get(k)
                        if isinstance(v, list):
                            merged[k].extend(v)
                ai_summary = merged
                (artifacts_dir / "ai_summary.json").write_text(
                    json.dumps(ai_summary, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            elif os.getenv("OPENAI_BASE_URL") and os.getenv("OPENAI_API_KEY"):
                from ...ai.qwen_openai_compatible import analyze_live_session  # lazy import
                ai_summary = analyze_live_session(transcript_txt, self._comments)
                (artifacts_dir / "ai_summary.json").write_text(
                    json.dumps(ai_summary, ensure_ascii=False, indent=2), encoding="utf-8"
                )
        except Exception as e:
            ai_summary = {"error": str(e)}
            (artifacts_dir / "ai_summary.error.txt").write_text(str(e), encoding="utf-8")

        # Compose recap HTML (with or without AI summary)
        try:
            self._session.metrics = dict(self._agg)
        except Exception:
            pass
        report_html = self._render_html_report(
            session=self._session,
            transcript=transcript_txt,
            comments=self._comments,
            ai=ai_summary,
        )
        report_path = artifacts_dir / "report.html"
        report_path.write_text(report_html, encoding="utf-8")
        self._session.report_path = str(report_path)

        return {
            "comments": str(comments_path),
            "transcript": str(transcript_path),
            "report": str(report_path),
        }

    def status(self) -> Optional[LiveReportStatus]:
        return self._session

    # ---------- Internals ----------
    async def _start_ffmpeg(self, record_url: str, seg_secs: int, pattern: str) -> asyncio.subprocess.Process:
        headers = []
        if "douyin" in record_url:
            headers = ["-headers", "referer:https://live.douyin.com"]
        cmd = [
            "ffmpeg",
            "-y",
            *headers,
            "-i",
            record_url,
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            "-f",
            "segment",
            "-segment_time",
            str(seg_secs),
            "-reset_timestamps",
            "1",
            pattern,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        asyncio.create_task(self._watch_segments_tail(pattern))
        return proc

    async def _graceful_stop_ffmpeg(self, proc: asyncio.subprocess.Process) -> None:
        try:
            if os.name == "nt":
                if proc.stdin:
                    proc.stdin.write(b"q")
                    await proc.stdin.drain()
            else:
                proc.send_signal(signal.SIGINT)
            try:
                await asyncio.wait_for(proc.wait(), timeout=10)
            except asyncio.TimeoutError:
                proc.kill()
        except ProcessLookupError:
            pass

    async def _watch_segments_tail(self, pattern: str) -> None:
        # After ffmpeg starts, periodically rescan output dir for new files
        out_dir = Path(pattern).parent
        seen: set[str] = set()
        try:
            while self._ffmpeg_proc is not None:
                for p in sorted(out_dir.glob("*.mp4")):
                    if str(p) in seen:
                        continue
                    # basic stability check
                    size1 = p.stat().st_size
                    await asyncio.sleep(1.0)
                    size2 = p.stat().st_size
                    if size2 >= size1:
                        await self._add_segment(p)
                        seen.add(str(p))
                await asyncio.sleep(2.0)
        except asyncio.CancelledError:
            pass

    async def _scan_segments(self) -> None:
        if not self._session:
            return
        out_dir = Path(self._session.recording_dir)
        files = sorted(out_dir.glob("*.mp4"))
        for p in files:
            # add if not present
            if not any(seg.get("path") == str(p) for seg in self._session.segments):
                await self._add_segment(p)

    async def _add_segment(self, p: Path) -> None:
        if not self._session:
            return
        seq = self._infer_seq(p)
        start_ts = self._infer_start_ts(p)
        end_ts = int(start_ts + 1000 * self._session.segment_seconds) if start_ts else None
        seg_meta = {
            "seq": seq,
            "path": str(p),
            "start_ts": start_ts,
            "end_ts": end_ts,
        }
        self._session.segments.append(seg_meta)
        # Fire-and-forget: process and analyze as soon as segment appears
        try:
            asyncio.create_task(self._process_and_analyze_segment(seg_meta))
        except Exception:
            pass

    def _infer_seq(self, p: Path) -> int:
        m = re.search(r"_(\d{3})\.mp4$", p.name)
        return int(m.group(1)) if m else len(self._session.segments) + 1

    def _infer_start_ts(self, p: Path) -> Optional[int]:
        # Pattern in filename: _YYYYmmdd_HHMMSS_###.mp4
        m = re.search(r"_(\d{8})_(\d{6})_\d{3}\.mp4$", p.name)
        if not m:
            return None
        date_str, time_str = m.group(1), m.group(2)
        try:
            t = time.strptime(date_str + time_str, "%Y%m%d%H%M%S")
            return int(time.mktime(t) * 1000)
        except Exception:
            return None

    def _slice_comments(self, start_ts: Optional[int], end_ts: Optional[int]) -> List[Dict[str, Any]]:
        if start_ts is None or end_ts is None:
            return list(self._comments)
        return [ev for ev in self._comments if isinstance(ev, dict) and start_ts <= int(ev.get("ts", 0)) <= end_ts]

    async def _process_and_analyze_segment(self, seg_meta: Dict[str, Any]) -> None:
        try:
            # Transcribe current segment
            seg_path = Path(seg_meta.get("path", ""))
            if not seg_path.exists():
                return
            pcm_path = seg_path.with_suffix(".pcm")
            await self._extract_pcm(seg_path, pcm_path)
            sv = await self._get_sv()
            res = await sv.transcribe_audio(pcm_path.read_bytes())
            text = (res or {}).get("text", "") or ""

            comments = self._slice_comments(seg_meta.get("start_ts"), seg_meta.get("end_ts"))

            # Qwen window analysis with carry-over
            try:
                from ...ai.qwen_openai_compatible import analyze_window  # type: ignore
                ai = analyze_window(text, comments, self._carry)
                self._carry = str(ai.get("carry") or "")[:200]
            except Exception:
                ai = {"error": "ai_unavailable"}

            # Persist window artifact
            try:
                artifacts = Path(self._session.recording_dir) / "artifacts" / "windows"
                artifacts.mkdir(parents=True, exist_ok=True)
                payload = {
                    "seq": seg_meta.get("seq"),
                    "start_ts": seg_meta.get("start_ts"),
                    "end_ts": seg_meta.get("end_ts"),
                    "transcript": text,
                    "ai": ai,
                }
                (artifacts / f"seg_{int(seg_meta.get('seq', 0)):03d}.json").write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                self._analysis.append(payload)
            except Exception:
                pass
        except Exception:
            # tolerate any processing failure, do not crash recorder
            pass

    async def _consume_danmu(self) -> None:
        queue = self._relay_client_queue
        if queue is None:
            return
        try:
            while True:
                ev = await queue.get()
                if not isinstance(ev, dict):
                    continue
                # annotate minimal fields
                ev.setdefault("ts", int(time.time() * 1000))
                ev.setdefault("source", "douyin")
                self._comments.append(ev)
                # aggregates
                try:
                    et = ev.get("type")
                    pl = ev.get("payload") or {}
                    if et == "follow":
                        self._agg["follows"] = int(self._agg.get("follows", 0)) + 1
                    elif et == "member":
                        if pl.get("action") in ("enter", None):
                            self._agg["entries"] = int(self._agg.get("entries", 0)) + 1
                    elif et == "room_user_stats":
                        cur = pl.get("current") or pl.get("total_user") or 0
                        try:
                            cur = int(cur)
                        except Exception:
                            cur = 0
                        if cur > int(self._agg.get("peak_viewers", 0)):
                            self._agg["peak_viewers"] = cur
                    elif et == "like":
                        inc = pl.get("count")
                        try:
                            inc = int(inc)
                        except Exception:
                            inc = 0
                        self._agg["like_total"] = int(self._agg.get("like_total", 0)) + inc
                    elif et == "gift":
                        name = (pl.get("gift_name") or "?")
                        cnt = pl.get("count")
                        try:
                            cnt = int(cnt)
                        except Exception:
                            cnt = 1
                        gifts = self._agg.setdefault("gifts", {})
                        gifts[name] = int(gifts.get(name, 0)) + cnt
                except Exception:
                    pass
        except asyncio.CancelledError:
            pass

    async def _get_sv(self) -> SenseVoiceService:
        if self._sv is None:
            self._sv = SenseVoiceService(SenseVoiceConfig())
            ok = await self._sv.initialize()
            if not ok:
                raise RuntimeError("SenseVoiceService initialize failed")
        return self._sv

    async def _extract_pcm(self, in_mp4: Path, out_pcm: Path) -> None:
        # ffmpeg -i input.mp4 -vn -ac 1 -ar 16000 -f s16le output.pcm
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(in_mp4),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "s16le",
            str(out_pcm),
        ]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg extract pcm failed: {proc.returncode}")

    def _render_html_report(self, session: LiveReportStatus, transcript: str, comments: List[Dict[str, Any]], ai: Optional[Dict[str, Any]] = None) -> str:
        # Minimal themed report (inspired by docs/protype/*_multi_theme.html)
        # Keep inline CSS small; frontend can take over later.
        css = """
        body{font-family:Segoe UI,Helvetica,Arial,sans-serif;background:#f8f5ff;color:#36384c;margin:0}
        .shell{max-width:1080px;margin:40px auto;background:#fff;border-radius:20px;box-shadow:0 18px 32px rgba(167,139,250,.18);padding:28px}
        h1{font-size:24px;margin:0 0 12px}.meta{color:#6b6b8a;font-size:14px;margin-bottom:18px}
        .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
        .card{background:#fff;border-radius:16px;box-shadow:0 12px 24px rgba(0,0,0,.06);padding:18px}
        .card h2{font-size:18px;margin:0 0 10px}.mono{white-space:pre-wrap;font-family:ui-monospace,Consolas,monospace;font-size:14px;line-height:1.5}
        .badge{display:inline-block;background:#efe8ff;color:#6b46c1;border-radius:999px;padding:4px 10px;font-size:12px;font-weight:600}
        ul{margin:0;padding-left:18px}
        table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #f0ebff;padding:8px 6px;text-align:left;font-size:14px}
        """
        meta = f"平台: {session.platform_key} · 主播: {session.anchor_name or '-'} · 片段: {len(session.segments)} · 弹幕: {len(comments)}"
        # Simple heuristics: top users & word-like counts (client can enhance later)
        top_users: Dict[str, int] = {}
        for ev in comments:
            u = (ev.get("user") or ev.get("payload", {}).get("user")) or "?"
            top_users[u] = top_users.get(u, 0) + 1
        top_sorted = sorted(top_users.items(), key=lambda x: x[1], reverse=True)[:10]
        rows = "".join([f"<tr><td>{u}</td><td>{c}</td></tr>" for u, c in top_sorted])

        # AI summary blocks
        ai_block = ""
        if ai and isinstance(ai, dict):
            def _ul(key: str) -> str:
                items = ai.get(key) or []
                if isinstance(items, list):
                    lis = "".join([f"<li>{str(x)}</li>" for x in items])
                    return f"<ul>{lis}</ul>" if lis else "<div class=mono>(暂无)</div>"
                return f"<div class=mono>{str(items)[:4000]}</div>"
            scripts = ai.get("scripts") or []
            script_lis = "".join([f"<li><b>{(s.get('type') or 'script')}</b> — {s.get('text') or ''}</li>" for s in scripts if isinstance(s, dict)])
            ai_block = (
                "<div class=card>"
                "<h2>AI 总结</h2>"
                f"<h3>亮点</h3>{_ul('highlight_points')}"
                f"<h3>风险</h3>{_ul('risks')}"
                f"<h3>改进建议</h3>{_ul('suggestions')}"
                f"<h3>高频问题</h3>{_ul('top_questions')}"
                f"<h3>可用话术</h3><ul>{script_lis or '<li>(暂无)</li>'}</ul>"
                "</div>"
            )

        # Metrics
        m = session.metrics or {}
        gifts = m.get("gifts") or {}
        gift_rows = "".join([f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in sorted(gifts.items(), key=lambda x: x[1], reverse=True)])
        metrics_html = (
            "<div class=card>"
            "<h2>直播数据</h2>"
            f"<div class=badge>新增关注: {int(m.get('follows',0))}</div> "
            f"<div class=badge>进场人数: {int(m.get('entries',0))}</div> "
            f"<div class=badge>最高在线: {int(m.get('peak_viewers',0))}</div> "
            f"<div class=badge>新增点赞: {int(m.get('like_total',0))}</div>"
            + ("<h3>礼物统计</h3><table><thead><tr><th>礼物</th><th>数量</th></tr></thead><tbody>" + (gift_rows or "<tr><td colspan=2>(暂无)</td></tr>") + "</tbody></table>")
            + "</div>"
        )

        html = f"""
        <!doctype html><html lang=zh-CN><meta charset=utf-8><title>直播复盘报告 · {session.anchor_name or ''}</title>
        <style>{css}</style>
        <body><div class=shell>
          <h1>直播复盘报告</h1>
          <div class=meta>{meta}</div>
          <div class=grid>
            <div class=card>
              <h2>话术要点（自动草稿） <span class=badge>Beta</span></h2>
              <div class=mono>{self._extract_key_points(transcript)}</div>
            </div>
            {metrics_html}
            <div class=card>
              <h2>互动概览</h2>
              <table><thead><tr><th>用户</th><th>消息数</th></tr></thead><tbody>{rows or '<tr><td>—</td><td>—</td></tr>'}</tbody></table>
            </div>
            {ai_block}
            <div class=card style="grid-column:1/-1">
              <h2>整场口播转写</h2>
              <div class=mono>{transcript}</div>
            </div>
          </div>
        </div></body></html>
        """
        return html

    def _extract_key_points(self, transcript: str, limit: int = 8) -> str:
        # Very rough heuristics: take first N non-empty lines or split by '。'
        if not transcript:
            return "(暂无转写)"
        sents = re.split(r"[。！？!?]\s*", transcript)
        picks = [s.strip() for s in sents if s.strip()][:limit]
        return "\n- ".join([picks[0]] + picks[1:]) if picks else transcript[:300]


# Singleton for app
_live_report_service: Optional[LiveReportService] = None


def get_live_report_service() -> LiveReportService:
    global _live_report_service
    if _live_report_service is None:
        _live_report_service = LiveReportService()
    return _live_report_service
