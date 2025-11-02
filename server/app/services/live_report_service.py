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
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional


# Stream URL resolution (StreamCap backend)
from server.modules.streamcap.platforms import get_platform_handler  # type: ignore
from server.modules.streamcap.media import create_builder  # type: ignore

# Douyin web relay (existing service in this repo)
# NOTE: live_report_service.py lives in server/app/services/, so the sibling
# module is server/app/services/douyin_web_relay.py. The previous import used
# an incorrect three-level relative path (…services.*) which resolves to
# server/services/* and crashes with "No module named 'server.services'" when
# FastAPI includes this router. We import from the current package instead.
from .douyin_web_relay import get_douyin_web_relay  # type: ignore

# SenseVoice batch API: transcribe PCM16 mono @ 16k
from server.modules.ast.sensevoice_service import (  # type: ignore
    SenseVoiceConfig,
    SenseVoiceService,
)
from ...utils.async_process import AsyncProcess, create_subprocess_exec

logger = logging.getLogger(__name__)


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
    session_date: str = ""
    session_index: int = 1
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
        self._ffmpeg_proc: Optional[AsyncProcess] = None
        self._comment_queue: Optional[asyncio.Queue] = None
        self._comments: List[Dict[str, Any]] = []
        self._comment_task: Optional[asyncio.Task] = None
        self._relay_client_queue: Optional[asyncio.Queue] = None

        # 🆕 URL 自动刷新机制
        self._url_refresh_task: Optional[asyncio.Task] = None
        self._url_refresh_interval: int = 20 * 60  # 20 分钟刷新一次
        self._health_monitor_task: Optional[asyncio.Task] = None
        self._current_record_url: Optional[str] = None
        self._output_pattern: Optional[str] = None

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
        try:  # Lazy optional imports for style summarisation
            from ...ai.style_profile_builder import StyleProfileBuilder  # type: ignore
        except Exception:  # pragma: no cover
            StyleProfileBuilder = None  # type: ignore
        try:
            from ...ai.style_memory import StyleMemoryManager  # type: ignore
        except Exception:  # pragma: no cover
            StyleMemoryManager = None  # type: ignore
        if "StyleProfileBuilder" in locals() and StyleProfileBuilder:
            try:
                self._style_builder = StyleProfileBuilder()
            except Exception as exc:  # pragma: no cover
                logger.warning("StyleProfileBuilder unavailable: %s", exc)
                self._style_builder = None
        else:
            self._style_builder = None
        if "StyleMemoryManager" in locals() and StyleMemoryManager:
            try:
                self._style_memory = StyleMemoryManager()
            except Exception as exc:  # pragma: no cover
                logger.warning("StyleMemoryManager unavailable: %s", exc)
                self._style_memory = None
        else:
            self._style_memory = None

    # ---------- Public API ----------
    async def start(self, live_url: str, segment_minutes: int = 30) -> LiveReportStatus:
        # 检查是否有活跃的录制会话（正在录制中）
        if self._session is not None and self._ffmpeg_proc is not None:
            raise RuntimeError("Live report session already started")
        
        # 如果有已停止但未生成报告的 session，提示用户
        if self._session is not None and self._ffmpeg_proc is None:
            raise RuntimeError("请先生成报告，然后才能开始新的录制")

        try:
            live_id = _parse_douyin_live_id(live_url)
            handler = get_platform_handler(live_url=live_url)
            if handler is None:
                raise RuntimeError("Unsupported live URL")
            info = await handler.get_stream_info(live_url)
            if isinstance(info, dict):
                is_live = info.get("is_live")
                record_url = info.get("record_url") or info.get("flv_url") or info.get("m3u8_url")
                anchor_raw = info.get("anchor_name", "")
                platform = info.get("platform", "douyin") or "douyin"
            else:
                is_live = getattr(info, "is_live", None)
                record_url = (
                    getattr(info, "record_url", None)
                    or getattr(info, "flv_url", None)
                    or getattr(info, "m3u8_url", None)
                )
                anchor_raw = getattr(info, "anchor_name", "")
                platform = getattr(info, "platform", "douyin") or "douyin"

            if is_live is False:
                raise RuntimeError(f"直播间当前未开播，无法开始录制：{anchor_raw or live_id}")

            if not record_url:
                raise RuntimeError("Failed to resolve record URL (streams unavailable)")

            anchor = _safe_name(anchor_raw)
            day = time.strftime("%Y-%m-%d", time.localtime())
            session_id = f"live_{platform}_{anchor}_{int(time.time())}"
            day_dir = self.records_root / platform / anchor / day
            existing_sessions = [p for p in day_dir.glob("live_*") if p.is_dir()]
            session_index = len(existing_sessions) + 1
            out_dir = day_dir / session_id
            out_dir.mkdir(parents=True, exist_ok=True)

            seg_secs = max(300, int(segment_minutes) * 60)
            pattern = str(out_dir / f"{anchor}_%Y%m%d_%H%M%S_%03d.mp4")

            # 🆕 保存流 URL 和输出模式
            self._current_record_url = record_url
            self._output_pattern = pattern

            self._session = LiveReportStatus(
                session_id=session_id,
                live_url=live_url,
                room_id=live_id,
                anchor_name=anchor,
                platform_key=platform,
                recording_dir=str(out_dir),
                session_date=day,
                session_index=session_index,
                segment_seconds=seg_secs,
            )

            # Start ffmpeg segment recording
            self._ffmpeg_proc = await self._start_ffmpeg(record_url, seg_secs, pattern)
            self._session.recording_pid = self._ffmpeg_proc.pid
            logger.info(f"✅ FFmpeg 启动成功，PID: {self._ffmpeg_proc.pid}")

            # 🆕 启动 URL 自动刷新任务
            self._url_refresh_task = asyncio.create_task(self._auto_refresh_stream_url())
            logger.info(f"🔄 启动 URL 自动刷新任务，间隔: {self._url_refresh_interval // 60} 分钟")

            # 🆕 启动健康监控任务
            self._health_monitor_task = asyncio.create_task(self._monitor_ffmpeg_health())
            logger.info(f"💓 启动 ffmpeg 健康监控任务")

            # Start Douyin relay and consume events into in-memory buffer
            relay = get_douyin_web_relay()
            if live_id:
                logger.info(f"🚀 启动抖音弹幕采集，房间ID: {live_id}")
                await relay.start(live_id)
                logger.info(f"✅ 弹幕 relay 启动成功")
            else:
                logger.warning(f"⚠️ 无法获取房间ID，弹幕采集可能失败")
            
            self._relay_client_queue = await relay.register_client()
            logger.info(f"✅ 注册弹幕客户端成功，队列: {self._relay_client_queue}")
            
            self._comment_task = asyncio.create_task(self._consume_danmu())
            logger.info(f"✅ 启动弹幕消费任务")

            logger.info("=" * 60)
            logger.info("✅ 录制已启动，后台任务运行中:")
            logger.info(f"  📺 URL 刷新: 每 {self._url_refresh_interval // 60} 分钟")
            logger.info(f"  💓 健康检查: 每 30 秒")
            logger.info(f"  💬 弹幕收集: 实时")
            logger.info("=" * 60)

            return self._session
        
        except Exception as e:
            # 清理已创建的session状态，确保下次可以重新启动
            if self._session is not None:
                # 尝试清理已启动的资源
                if self._ffmpeg_proc:
                    try:
                        await self._graceful_stop_ffmpeg(self._ffmpeg_proc)
                    except Exception:
                        pass
                    self._ffmpeg_proc = None
                
                if self._comment_task:
                    self._comment_task.cancel()
                    try:
                        await self._comment_task
                    except asyncio.CancelledError:
                        pass
                    self._comment_task = None
                
                if self._relay_client_queue:
                    try:
                        relay = get_douyin_web_relay()
                        await relay.unregister_client(self._relay_client_queue)
                        await relay.stop()
                    except Exception:
                        pass
                    self._relay_client_queue = None
                
                # 清空session状态
                self._session = None
            
            # 重新抛出原始异常
            raise e

    async def stop(self) -> LiveReportStatus:
        if not self._session:
            # 返回一个默认的停止状态，而不是抛出异常
            return LiveReportStatus(
                session_id="no-session",
                live_url="",
                room_id=None,
                anchor_name="",
                recording_dir=None,
                started_at=_now_ts(),
                stopped_at=_now_ts(),
                segments=[],
                comments_count=0,
                transcript_chars=0,
                metrics={}
            )

        logger.info("🛑 停止录制...")

        # 🆕 停止 URL 刷新任务
        if self._url_refresh_task:
            self._url_refresh_task.cancel()
            try:
                await self._url_refresh_task
            except asyncio.CancelledError:
                pass
            self._url_refresh_task = None
            logger.info("✅ URL 刷新任务已停止")

        # 🆕 停止健康监控任务
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass
            self._health_monitor_task = None
            logger.info("✅ 健康监控任务已停止")

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
        
        # 清理录制相关的资源，但保留 session 数据供生成报告使用
        self._relay_client_queue = None
        self._comment_task = None
        self._ffmpeg_proc = None
        
        # 标记 session 为已停止状态（用于前端判断）
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
        self._update_style_profile(transcript_txt, artifacts_dir)

        # 使用 Gemini 2.5 Flash 进行复盘（超低成本，约 $0.000131/次）
        ai_summary: Dict[str, Any] | None = None
        try:
            logger.info("🔄 开始使用 Gemini 生成复盘报告...")
            from ...ai.gemini_adapter import generate_review_report  # lazy import
            
            # 准备复盘数据
            review_data = {
                "session_id": self._session.session_id,
                "transcript": transcript_txt,
                "comments": self._comments,
                "anchor_name": self._session.anchor_name,
                "metrics": dict(self._agg) if hasattr(self, '_agg') else {}
            }
            
            # 调用 Gemini 生成复盘
            gemini_result = generate_review_report(review_data)
            
            # 转换为旧格式以兼容 HTML 报告模板
            ai_summary = {
                "summary": gemini_result.get("performance_analysis", {}).get("overall_assessment", ""),
                "highlight_points": gemini_result.get("key_highlights", []),
                "risks": gemini_result.get("key_issues", []),
                "suggestions": gemini_result.get("improvement_suggestions", []),
                "top_questions": [],  # Gemini 不返回此字段
                "scripts": [],  # Gemini 不返回此字段
                "overall_score": gemini_result.get("overall_score"),
                "performance_analysis": gemini_result.get("performance_analysis"),
                "trend_charts": gemini_result.get("trend_charts", {}),  # 🆕 保留趋势图数据
                "gemini_metadata": {
                    "model": gemini_result.get("ai_model", "gemini-2.5-flash"),
                    "cost": gemini_result.get("generation_cost", 0),
                    "tokens": gemini_result.get("generation_tokens", 0),
                    "duration": gemini_result.get("generation_duration", 0)
                }
            }
            
            (artifacts_dir / "ai_summary.json").write_text(
                json.dumps(ai_summary, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            
            logger.info(
                f"✅ Gemini 复盘完成 - 评分: {ai_summary.get('overall_score')}/100, "
                f"成本: ${ai_summary['gemini_metadata']['cost']:.6f}, "
                f"耗时: {ai_summary['gemini_metadata']['duration']:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"❌ Gemini 复盘失败: {type(e).__name__}: {str(e)}", exc_info=True)
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

        # 构建结构化的复盘数据
        review_data = {
            "session_id": self._session.session_id,
            "room_id": self._session.room_id,
            "anchor_name": self._session.anchor_name,
            "started_at": self._session.started_at,
            "stopped_at": self._session.stopped_at,
            "duration_seconds": (self._session.stopped_at - self._session.started_at) / 1000 if self._session.stopped_at else 0,
            "metrics": dict(self._agg) if hasattr(self, '_agg') else {},
            "transcript": transcript_txt,
            "comments_count": len(self._comments),
            "ai_summary": ai_summary,
            "transcript_chars": len(transcript_txt),
            "segments_count": len(transcripts),
        }
        
        # 保存 review_data 到 JSON 文件，方便后续查看
        review_data_path = artifacts_dir / "review_data.json"
        review_data_path.write_text(json.dumps(review_data, ensure_ascii=False, indent=2), encoding="utf-8")
        
        # 生成报告完成后，清空 session 允许开始新的录制
        result = {
            "comments": str(comments_path),
            "transcript": str(transcript_path),
            "report": str(report_path),
            "review_data": review_data,
        }
        
        # 清空 session 和相关数据，允许开始新的录制
        self._session = None
        self._comments = []
        self._analysis = []
        self._carry = ""
        self._agg = {
            "follows": 0,
            "entries": 0,
            "peak_viewers": 0,
            "like_total": 0,
            "gifts": {},
        }
        
        # 返回结构化数据，供前端直接展示
        return result

    def status(self) -> Optional[LiveReportStatus]:
        # 实时同步 metrics 到 session，确保前端能获取最新数据
        if self._session and hasattr(self, '_agg'):
            try:
                self._session.metrics = dict(self._agg)
            except Exception:
                pass
        return self._session

    # ---------- Internals ----------
    def _update_style_profile(self, transcript: str, artifacts_dir: Path) -> None:
        """Summarize transcript into long-term style memory repository."""
        if not transcript or not self._session:
            return
        if not self._style_builder or not self._style_memory or not self._style_memory.available():
            return
        try:
            session_date = self._session.session_date or time.strftime("%Y-%m-%d", time.localtime())
            session_index = getattr(self._session, "session_index", 1)
            summary = self._style_builder.build_profile(
                anchor_id=self._session.anchor_name,
                transcript=transcript,
                session_date=session_date,
                session_index=session_index,
            )
            if not summary:
                return
            self._style_memory.ingest_summary(self._session.anchor_name, summary)
            try:
                (artifacts_dir / "style_profile.json").write_text(
                    json.dumps(summary, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception:
                pass
        except Exception as exc:  # pragma: no cover - fail gracefully
            logger.warning("Failed to update style memory: %s", exc)

    async def _start_ffmpeg(self, record_url: str, seg_secs: int, pattern: str) -> AsyncProcess:
        """
        启动 ffmpeg 进程录制直播流
        
        Args:
            record_url: 直播流 URL
            seg_secs: 分段时长(秒)
            pattern: 输出文件名模式
        
        Returns:
            AsyncProcess: ffmpeg 进程对象
        """
        headers = None
        if "douyin" in record_url:
            headers = "referer:https://live.douyin.com"
        
        builder = create_builder(
            "mp4",
            record_url=record_url,
            segment_record=True,
            segment_time=str(seg_secs),
            full_path=pattern,
            headers=headers,
        )
        cmd = builder.build_command()
        
        # 🆕 添加容错参数（在 -i 参数之前插入）
        input_idx = cmd.index("-i") if "-i" in cmd else -1
        if input_idx > 0:
            # 插入容错参数
            reconnect_options = [
                "-reconnect", "1",              # 自动重连
                "-reconnect_streamed", "1",     # 流式重连
                "-reconnect_delay_max", "5",    # 最大重连延迟 5 秒
                "-rw_timeout", "10000000",      # 读写超时 10 秒（10 秒）
            ]
            for i, opt in enumerate(reconnect_options):
                cmd.insert(input_idx + i, opt)
        
        if ("%Y" in pattern or "%H" in pattern or "%M" in pattern or "%S" in pattern) and "-strftime" not in cmd:
            # Insert strftime flag right before the output pattern so rotated files carry wall-clock timestamps.
            output_idx = len(cmd) - 1
            cmd.insert(output_idx, "1")
            cmd.insert(output_idx, "-strftime")
        
        logger.info(f"🎬 启动 ffmpeg 命令: {' '.join(cmd[:15])}...")
        
        proc = await create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        asyncio.create_task(self._watch_segments_tail(pattern))
        return proc

    async def _graceful_stop_ffmpeg(self, proc: AsyncProcess) -> None:
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

    def _extract_record_url(self, info) -> Optional[str]:
        """
        🆕 提取录制 URL（兼容 dict 和对象）
        
        Args:
            info: streamget 返回的流信息
        
        Returns:
            录制 URL 或 None
        """
        if isinstance(info, dict):
            return info.get("record_url") or info.get("flv_url") or info.get("m3u8_url")
        else:
            return (
                getattr(info, "record_url", None)
                or getattr(info, "flv_url", None)
                or getattr(info, "m3u8_url", None)
            )

    async def _auto_refresh_stream_url(self):
        """
        🆕 自动刷新流 URL 的后台任务
        
        工作流程:
        1. 每 20 分钟触发一次
        2. 重新获取流 URL
        3. 无缝切换 ffmpeg 进程
        4. 保存当前分段
        """
        try:
            while self._session and self._ffmpeg_proc:
                # 等待刷新间隔
                await asyncio.sleep(self._url_refresh_interval)
                
                logger.info("🔄 开始刷新直播流 URL...")
                
                try:
                    # 1. 重新获取流地址
                    handler = get_platform_handler(live_url=self._session.live_url)
                    if handler is None:
                        logger.warning("⚠️ 无法获取平台处理器，跳过本次刷新")
                        continue
                    
                    info = await handler.get_stream_info(self._session.live_url)
                    new_record_url = self._extract_record_url(info)
                    
                    if not new_record_url:
                        logger.warning("⚠️ 无法获取新的流地址，保持当前流")
                        continue
                    
                    # 2. 检查直播是否仍在进行
                    is_live = info.get("is_live") if isinstance(info, dict) else getattr(info, "is_live", True)
                    if not is_live:
                        logger.info("📴 检测到直播已结束，停止录制")
                        await self.stop()
                        break
                    
                    # 3. 检查 URL 是否发生变化
                    if new_record_url == self._current_record_url:
                        logger.info("ℹ️ 流地址未变化，无需切换")
                        continue
                    
                    # 4. 切换到新的流 URL
                    logger.info(f"🔄 切换流地址: {new_record_url[:80]}...")
                    
                    # 4.1 优雅停止旧的 ffmpeg 进程
                    old_proc = self._ffmpeg_proc
                    if old_proc:
                        try:
                            await self._graceful_stop_ffmpeg(old_proc)
                            logger.info("✅ 旧 ffmpeg 进程已停止")
                        except Exception as e:
                            logger.warning(f"⚠️ 停止旧进程失败: {e}")
                    
                    # 4.2 启动新的 ffmpeg 进程
                    seg_secs = self._session.segment_seconds
                    pattern = self._output_pattern
                    
                    self._ffmpeg_proc = await self._start_ffmpeg(new_record_url, seg_secs, pattern)
                    self._current_record_url = new_record_url
                    self._session.recording_pid = self._ffmpeg_proc.pid
                    
                    logger.info(f"✅ 流地址刷新成功，新 PID: {self._ffmpeg_proc.pid}")
                    
                except Exception as e:
                    logger.error(f"❌ 刷新流地址失败: {e}")
                    # 继续使用旧的流，等待下次刷新
                    continue
        
        except asyncio.CancelledError:
            logger.info("URL 刷新任务已取消")
        except Exception as e:
            logger.error(f"URL 刷新任务异常: {e}")

    async def _monitor_ffmpeg_health(self):
        """
        🆕 监控 ffmpeg 进程健康状态
        
        检测:
        1. 进程是否异常退出
        2. 输出文件是否在增长
        3. 网络是否断连
        """
        try:
            last_file_size = 0
            no_growth_count = 0
            
            while self._session and self._ffmpeg_proc:
                await asyncio.sleep(30)  # 每 30 秒检查一次
                
                # 1. 检查进程是否存活
                if self._ffmpeg_proc.returncode is not None:
                    logger.error(f"❌ ffmpeg 进程异常退出，返回码: {self._ffmpeg_proc.returncode}")
                    # 尝试重启
                    try:
                        await self._restart_ffmpeg()
                    except Exception as e:
                        logger.error(f"❌ 重启 ffmpeg 失败: {e}")
                        await self.stop()
                        break
                    continue
                
                # 2. 检查文件是否在增长
                try:
                    out_dir = Path(self._session.recording_dir)
                    files = list(out_dir.glob("*.mp4"))
                    if files:
                        latest_file = max(files, key=lambda f: f.stat().st_mtime)
                        current_size = latest_file.stat().st_size
                        
                        if current_size == last_file_size:
                            no_growth_count += 1
                            logger.warning(f"⚠️ 文件大小未增长 ({no_growth_count}/3): {latest_file.name}")
                            
                            if no_growth_count >= 3:
                                logger.error("❌ 文件长时间无增长，可能网络断连，尝试刷新流")
                                try:
                                    await self._restart_ffmpeg()
                                    no_growth_count = 0
                                except Exception as e:
                                    logger.error(f"❌ 重启失败: {e}")
                                    await self.stop()
                                    break
                        else:
                            if no_growth_count > 0:
                                logger.info("✅ 文件正常增长，恢复健康")
                            no_growth_count = 0
                            last_file_size = current_size
                except Exception as e:
                    logger.warning(f"健康检查失败: {e}")
        
        except asyncio.CancelledError:
            logger.info("健康监控任务已取消")
        except Exception as e:
            logger.error(f"健康监控任务异常: {e}")

    async def _restart_ffmpeg(self):
        """🆕 重启 ffmpeg 进程"""
        logger.info("🔄 重启 ffmpeg 进程...")
        
        try:
            # 1. 停止旧进程
            if self._ffmpeg_proc:
                try:
                    await self._graceful_stop_ffmpeg(self._ffmpeg_proc)
                except Exception as e:
                    logger.warning(f"停止旧进程时出错: {e}")
            
            # 2. 重新获取流 URL
            handler = get_platform_handler(live_url=self._session.live_url)
            if handler is None:
                raise RuntimeError("无法获取平台处理器")
            
            info = await handler.get_stream_info(self._session.live_url)
            new_record_url = self._extract_record_url(info)
            
            if not new_record_url:
                raise RuntimeError("无法获取新的流地址")
            
            # 检查直播是否还在进行
            is_live = info.get("is_live") if isinstance(info, dict) else getattr(info, "is_live", True)
            if not is_live:
                logger.info("📴 直播已结束")
                await self.stop()
                return
            
            # 3. 启动新进程
            seg_secs = self._session.segment_seconds
            pattern = self._output_pattern
            
            self._ffmpeg_proc = await self._start_ffmpeg(new_record_url, seg_secs, pattern)
            self._current_record_url = new_record_url
            self._session.recording_pid = self._ffmpeg_proc.pid
            
            logger.info(f"✅ ffmpeg 重启成功，新 PID: {self._ffmpeg_proc.pid}")
        
        except Exception as e:
            logger.error(f"❌ ffmpeg 重启失败: {e}")
            raise

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
                ai = analyze_window(
                    text,
                    comments,
                    self._carry,
                    anchor_id=self._session.anchor_name,
                )
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
            logger.warning("❌ 弹幕队列为空，无法采集弹幕")
            return
        
        logger.info("✅ 开始采集弹幕数据...")
        event_count = 0
        
        try:
            while True:
                ev = await queue.get()
                event_count += 1
                
                if not isinstance(ev, dict):
                    continue
                
                # 每10个事件打印一次日志
                if event_count % 10 == 1:
                    logger.info(f"📊 已接收 {event_count} 个弹幕事件，当前聚合数据: follows={self._agg.get('follows', 0)}, entries={self._agg.get('entries', 0)}, likes={self._agg.get('like_total', 0)}")
                
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
                        logger.debug(f"👤 新增关注: {pl.get('nickname', 'unknown')}")
                    elif et == "member":
                        if pl.get("action") in ("enter", None):
                            self._agg["entries"] = int(self._agg.get("entries", 0)) + 1
                            logger.debug(f"🚪 用户进场: {pl.get('nickname', 'unknown')}")
                    elif et == "room_user_stats":
                        cur = pl.get("current") or pl.get("total_user") or 0
                        try:
                            cur = int(cur)
                        except Exception:
                            cur = 0
                        if cur > int(self._agg.get("peak_viewers", 0)):
                            self._agg["peak_viewers"] = cur
                            logger.debug(f"👥 在线人数更新: {cur}")
                    elif et == "like":
                        inc = pl.get("count")
                        try:
                            inc = int(inc)
                        except Exception:
                            inc = 0
                        self._agg["like_total"] = int(self._agg.get("like_total", 0)) + inc
                        logger.debug(f"❤️ 点赞增加: +{inc}")
                    elif et == "gift":
                        name = (pl.get("gift_name") or "?")
                        cnt = pl.get("count")
                        try:
                            cnt = int(cnt)
                        except Exception:
                            cnt = 1
                        gifts = self._agg.setdefault("gifts", {})
                        gifts[name] = int(gifts.get(name, 0)) + cnt
                        logger.debug(f"🎁 收到礼物: {name} x{cnt}")
                except Exception as e:
                    logger.error(f"处理弹幕事件失败: {e}, event_type={ev.get('type')}")
                    pass
        except asyncio.CancelledError:
            logger.info(f"✅ 弹幕采集结束，共处理 {event_count} 个事件")
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
        proc = await create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
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
