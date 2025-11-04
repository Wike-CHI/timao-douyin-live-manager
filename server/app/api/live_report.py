# -*- coding: utf-8 -*-
"""
Live Report API
Start/stop a live recording session (Douyin), and after finishing, run
SenseVoice transcription per 30-min segment and compose a recap report.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any, Union, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db_session
from ..services.live_report_service import get_live_report_service
from server.utils.service_logger import log_service_start, log_service_stop, log_generation_start, log_generation_complete, log_generation_error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/report/live", tags=["live-report"])


class StartReq(BaseModel):
    live_url: str = Field(..., description="Douyin live URL, e.g., https://live.douyin.com/xxxx")
    segment_minutes: int = Field(30, ge=5, le=120, description="Segment length in minutes (default 30)")


class BaseResp(BaseModel):
    success: bool = True
    message: str = "ok"
    data: Optional[Union[dict, list]] = None


@router.post("/start")
async def start_live_report(req: StartReq) -> BaseResp:
    try:
        svc = get_live_report_service()
        log_service_start("直播录制服务", live_url=req.live_url, segment_minutes=req.segment_minutes)
        status = await svc.start(req.live_url, req.segment_minutes)
        log_service_start("直播录制服务", session_id=status.session_id, recording_pid=status.recording_pid, status="已启动")
        return BaseResp(data={
            "session_id": status.session_id,
            "recording_pid": status.recording_pid,
            "recording_dir": status.recording_dir,
            "segment_seconds": status.segment_seconds,
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        from server.utils.service_logger import log_service_error
        log_service_error("直播录制服务", str(e), live_url=req.live_url)
        logger.error(f"Live report start failed: {type(e).__name__}: {str(e)}", exc_info=True)
        
        # 提供更具体的错误信息
        error_msg = str(e)
        if "already started" in error_msg.lower():
            raise HTTPException(status_code=409, detail="直播录制服务已在运行中")
        elif "unsupported live url" in error_msg.lower():
            raise HTTPException(status_code=400, detail=f"不支持的直播平台或地址: {error_msg}")
        elif "未开播" in error_msg or "not live" in error_msg.lower():
            raise HTTPException(status_code=400, detail=f"直播间未开播: {error_msg}")
        elif "failed to resolve" in error_msg.lower():
            raise HTTPException(status_code=400, detail=f"无法解析直播流地址: {error_msg}")
        elif "ffmpeg" in error_msg.lower():
            raise HTTPException(status_code=500, detail=f"录制服务启动失败: {error_msg}")
        else:
            raise HTTPException(status_code=400, detail=f"启动直播录制服务失败: {error_msg}")


@router.post("/stop")
async def stop_live_report() -> BaseResp:
    try:
        svc = get_live_report_service()
        status = await svc.stop()
        log_service_stop("直播录制服务", session_id=status.session_id, segments=status.segments, comments_count=status.comments_count)
        return BaseResp(data={
            "session_id": status.session_id,
            "stopped_at": status.stopped_at,
            "segments": status.segments,
            "comments_count": status.comments_count,
            "status": status.status,
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Live report stop failed: {type(e).__name__}: {str(e)}", exc_info=True)
        
        # 提供更具体的错误信息
        error_msg = str(e)
        if "no active session" in error_msg.lower() or "not started" in error_msg.lower():
            # 没有活跃会话时返回成功响应，而不是404错误
            return BaseResp(success=True, message="没有正在运行的录制会话", data=None)
        else:
            raise HTTPException(status_code=400, detail=f"停止直播录制服务失败: {error_msg}")


@router.post("/pause")
async def pause_live_report() -> BaseResp:
    """暂停录制(保留会话状态,可以继续)"""
    try:
        svc = get_live_report_service()
        status = await svc.pause()
        return BaseResp(data={
            "session_id": status.session_id,
            "status": status.status,
            "paused_at": status.paused_at,
            "pause_count": status.pause_count,
            "segments": status.segments,
            "comments_count": status.comments_count,
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Live report pause failed: {type(e).__name__}: {str(e)}", exc_info=True)
        
        error_msg = str(e)
        if "no active session" in error_msg.lower():
            raise HTTPException(status_code=404, detail="没有正在运行的录制会话")
        elif "cannot pause" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=f"暂停录制失败: {error_msg}")


@router.post("/resume")
async def resume_live_report() -> BaseResp:
    """继续录制(从暂停状态恢复)"""
    try:
        svc = get_live_report_service()
        status = await svc.resume()
        return BaseResp(data={
            "session_id": status.session_id,
            "status": status.status,
            "resumed_at": status.resumed_at,
            "recording_pid": status.recording_pid,
            "segments": status.segments,
            "comments_count": status.comments_count,
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Live report resume failed: {type(e).__name__}: {str(e)}", exc_info=True)
        
        error_msg = str(e)
        if "no session" in error_msg.lower():
            raise HTTPException(status_code=404, detail="没有可以恢复的会话")
        elif "cannot resume" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg)
        elif "未开播" in error_msg or "not live" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=f"恢复录制失败: {error_msg}")


@router.get("/resumable")
async def get_resumable_session() -> BaseResp:
    """检查是否有可恢复的会话(应用启动时调用)"""
    try:
        svc = get_live_report_service()
        session = await svc.get_resumable_session()
        if session:
            return BaseResp(data={
                "session_id": session.session_id,
                "live_url": session.live_url,
                "room_id": session.room_id,
                "anchor_name": session.anchor_name,
                "status": session.status,
                "started_at": session.started_at,
                "paused_at": session.paused_at,
                "segments": session.segments,
                "comments_count": session.comments_count,
            })
        else:
            return BaseResp(success=True, message="没有可恢复的会话", data=None)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Get resumable session failed: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"获取可恢复会话失败: {str(e)}")


@router.get("/status")
async def live_report_status() -> dict:
    from dataclasses import asdict
    svc = get_live_report_service()
    s = svc.status()
    return {"active": s is not None, "status": asdict(s) if s else None}


@router.post("/generate")
async def generate_live_report() -> BaseResp:
    """
    生成直播复盘报告（仅保存到本地，不保存到数据库）
    报告保存在 server/records/ 目录下
    """
    try:
        svc = get_live_report_service()
        import time
        start_time = time.time()
        log_generation_start("直播报告", "当前会话")
        artifacts = await svc.generate_report()
        duration = time.time() - start_time
        log_generation_complete("直播报告", "当前会话", duration=duration)
        
        # 桌面端仅保存到本地，不保存到数据库
        report_path = artifacts.get("report")
        if report_path:
            logger.info(f"✅ 复盘报告已保存到本地: {report_path}")
        else:
            logger.info("✅ 复盘报告已生成（本地保存）")
        
        return BaseResp(data=artifacts)
    except Exception as e:
        log_generation_error("直播报告", "当前会话", str(e))
        logger.error(f"Live report generate failed: {type(e).__name__}: {str(e)}", exc_info=True)
        
        # 提供更具体的错误信息
        error_msg = str(e)
        if "no active session" in error_msg.lower() or "not started" in error_msg.lower():
            raise HTTPException(status_code=404, detail="没有正在运行的录制会话，无法生成报告")
        else:
            raise HTTPException(status_code=400, detail=f"生成直播报告失败: {error_msg}")


async def _save_report_to_database(artifacts: Dict[str, Any], db: Session):
    """
    将生成的报告保存到数据库（已废弃，桌面端仅保存到本地）
    
    注意：此函数已不再使用，桌面端的复盘报告仅保存在本地文件系统中。
    如需恢复数据库保存功能，请取消注释 generate_live_report 中的相关调用。
    """
    from ..models.live import LiveSession
    from ..models.live_review import LiveReviewReport
    from ..models.user import User
    
    review_data = artifacts.get("review_data")
    if not review_data:
        logger.warning("⚠️ artifacts 中没有 review_data，跳过数据库保存")
        return
    
    session_id_str = review_data.get("session_id")
    room_id = review_data.get("room_id")
    
    # 1. 查找或创建 LiveSession
    # 注意：旧的 live_report_service 使用字符串 session_id，但数据库需要整数 ID
    # 我们需要创建或查找一个 LiveSession 记录
    
    # 尝试通过 room_id 和时间范围查找现有会话
    from datetime import datetime, timedelta
    
    # 获取第一个用户（或创建默认用户）
    user = db.query(User).first()
    if not user:
        logger.warning("⚠️ 数据库中没有用户，无法关联会话")
        return
    
    # 查找最近的相同房间号的会话
    recent_session = db.query(LiveSession).filter(
        LiveSession.room_id == room_id,
        LiveSession.user_id == user.id
    ).order_by(LiveSession.start_time.desc()).first()
    
    # 如果没有找到，或者找到的会话太旧，创建新会话
    started_at_ms = review_data.get("started_at", 0)
    stopped_at_ms = review_data.get("stopped_at", 0)
    duration_seconds = review_data.get("duration_seconds", 0)
    
    if not recent_session or (datetime.now() - recent_session.start_time).total_seconds() > 7200:
        # 创建新会话
        logger.info(f"📊 [保存报告] 步骤4: 创建新 LiveSession，room_id={room_id}")
        session = LiveSession(
            user_id=user.id,
            room_id=room_id or "unknown",
            platform="douyin",
            title=review_data.get("anchor_name") or room_id,
            start_time=datetime.fromtimestamp(started_at_ms / 1000) if started_at_ms else datetime.now(),
            end_time=datetime.fromtimestamp(stopped_at_ms / 1000) if stopped_at_ms else datetime.now(),
            duration=int(duration_seconds),
            status="ended",
            comment_count=review_data.get("comments_count", 0),
            transcribe_enabled=True,
            transcribe_char_count=review_data.get("transcript_chars", 0),
            transcript_file=artifacts.get("transcript"),
            comment_file=artifacts.get("comments"),
            report_file=artifacts.get("report")
        )
        
        # 填充 metrics 数据
        metrics = review_data.get("metrics", {})
        session.total_viewers = metrics.get("entries", 0)
        session.peak_viewers = metrics.get("peak_viewers", 0)
        session.new_followers = metrics.get("follows", 0)
        session.like_count = metrics.get("like_total", 0)
        
        db.add(session)
        db.flush()
        logger.info(f"✅ 创建新的 LiveSession: id={session.id}, room_id={room_id}")
    else:
        session = recent_session
        logger.info(f"✅ 使用现有 LiveSession: id={session.id}, room_id={room_id}")
    
    # 2. 创建或更新 LiveReviewReport
    logger.info(f"📊 [保存报告] 步骤5: 查找或创建 LiveReviewReport，session_id={session.id}")
    existing_report = db.query(LiveReviewReport).filter(
        LiveReviewReport.session_id == session.id
    ).first()
    
    ai_summary = review_data.get("ai_summary", {})
    gemini_metadata = ai_summary.get("gemini_metadata", {})
    
    logger.info(f"📊 [保存报告] ai_summary keys: {list(ai_summary.keys()) if ai_summary else 'None'}")
    logger.info(f"📊 [保存报告] gemini_metadata: {gemini_metadata}")
    
    if existing_report:
        # 更新现有报告
        existing_report.overall_score = ai_summary.get("overall_score")
        existing_report.performance_analysis = ai_summary.get("performance_analysis")
        existing_report.key_highlights = ai_summary.get("highlight_points", [])
        existing_report.key_issues = ai_summary.get("risks", [])
        existing_report.improvement_suggestions = ai_summary.get("suggestions", [])
        existing_report.trend_charts = ai_summary.get("trend_charts", {})
        existing_report.status = "completed"
        existing_report.ai_model = gemini_metadata.get("model", "gemini-2.5-flash")
        existing_report.generation_cost = gemini_metadata.get("cost", 0)
        existing_report.generation_tokens = gemini_metadata.get("tokens", 0)
        existing_report.generation_duration = gemini_metadata.get("duration", 0)
        logger.info(f"✅ 更新 LiveReviewReport: id={existing_report.id}")
    else:
        # 创建新报告
        report = LiveReviewReport(
            session_id=session.id,
            overall_score=ai_summary.get("overall_score"),
            performance_analysis=ai_summary.get("performance_analysis"),
            key_highlights=ai_summary.get("highlight_points", []),
            key_issues=ai_summary.get("risks", []),
            improvement_suggestions=ai_summary.get("suggestions", []),
            trend_charts=ai_summary.get("trend_charts", {}),
            full_report_text=ai_summary.get("summary", ""),
            status="completed",
            ai_model=gemini_metadata.get("model", "gemini-2.5-flash"),
            generation_cost=gemini_metadata.get("cost", 0),
            generation_tokens=gemini_metadata.get("tokens", 0),
            generation_duration=gemini_metadata.get("duration", 0)
        )
        db.add(report)
        db.flush()
        logger.info(f"✅ 创建新的 LiveReviewReport: id={report.id}")
    
    logger.info(f"📊 [保存报告] 步骤6: 提交数据库事务...")
    db.commit()
    logger.info(f"✅ [保存报告] 数据库事务提交成功！report_id={report.id if 'report' in locals() else existing_report.id}")


@router.get("/review/{report_path:path}")
async def get_review_data(report_path: str) -> BaseResp:
    """
    从历史报告的 HTML 路径加载对应的 review_data.json
    report_path: 例如 "D:/project/.../artifacts/report.html"
    返回: review_data 结构化数据
    """
    try:
        import json
        from pathlib import Path
        
        # 将 report.html 路径转为 review_data.json 路径
        report_file = Path(report_path)
        if not report_file.exists() or report_file.name != "report.html":
            raise HTTPException(status_code=404, detail=f"报告文件不存在: {report_path}")
        
        # artifacts/ 目录下应该有 review_data.json
        review_data_file = report_file.parent / "review_data.json"
        if not review_data_file.exists():
            raise HTTPException(status_code=404, detail=f"复盘数据文件不存在，可能是旧版本报告")
        
        # 读取 JSON 文件
        review_data = json.loads(review_data_file.read_text(encoding="utf-8"))
        return BaseResp(data={"review_data": review_data})
        
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Load review data failed: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"加载复盘数据失败: {str(e)}")


@router.get("/history")
async def list_local_reports(limit: int = 20) -> BaseResp:
    """
    扫描本地 records 目录，返回最近的复盘报告列表
    
    - **limit**: 返回数量（默认 20）
    
    返回：
    - 基于本地文件系统的报告列表（按生成时间倒序）
    """
    try:
        import json
        from pathlib import Path
        from datetime import datetime
        
        svc = get_live_report_service()
        records_root = svc.records_root
        
        logger.info(f"📂 扫描本地报告目录: {records_root}")
        
        # 查找所有 review_data.json 文件
        reports = []
        for review_file in records_root.rglob("review_data.json"):
            try:
                # 读取 review_data.json
                review_data = json.loads(review_file.read_text(encoding="utf-8"))
                
                # 获取 artifacts 目录和 report.html 路径
                artifacts_dir = review_file.parent
                report_html = artifacts_dir / "report.html"
                
                # 提取关键信息
                session_id = review_data.get("session_id", "unknown")
                room_id = review_data.get("room_id")
                anchor_name = review_data.get("anchor_name", "未知主播")
                started_at = review_data.get("started_at", 0)
                stopped_at = review_data.get("stopped_at", 0)
                duration_seconds = review_data.get("duration_seconds", 0)
                
                # 获取文件修改时间作为生成时间
                generated_at = datetime.fromtimestamp(review_file.stat().st_mtime)
                
                # AI 模型信息
                ai_summary = review_data.get("ai_summary", {})
                gemini_metadata = ai_summary.get("gemini_metadata", {})
                ai_model = gemini_metadata.get("model", "unknown")
                overall_score = ai_summary.get("overall_score")
                
                reports.append({
                    "session_id": session_id,
                    "room_id": room_id,
                    "title": anchor_name,
                    "anchor_name": anchor_name,
                    "started_at": datetime.fromtimestamp(started_at / 1000).isoformat() if started_at else None,
                    "stopped_at": datetime.fromtimestamp(stopped_at / 1000).isoformat() if stopped_at else None,
                    "duration_seconds": duration_seconds,
                    "generated_at": generated_at.isoformat(),
                    "report_path": str(report_html),
                    "review_data_path": str(review_file),
                    "ai_model": ai_model,
                    "overall_score": overall_score,
                    "status": "completed"
                })
                
            except Exception as e:
                logger.warning(f"⚠️ 读取报告文件失败: {review_file}, 错误: {e}")
                continue
        
        # 按生成时间倒序排序
        reports.sort(key=lambda x: x["generated_at"], reverse=True)
        
        # 限制返回数量
        reports = reports[:limit]
        
        logger.info(f"✅ 找到 {len(reports)} 个本地报告")
        
        return BaseResp(data=reports)
        
    except Exception as e:
        logger.error(f"扫描本地报告失败: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"扫描本地报告失败: {str(e)}")


@router.delete("/history/{session_id}")
async def delete_local_report(session_id: str) -> BaseResp:
    """
    删除本地报告（包括整个会话目录）
    
    - **session_id**: 会话 ID，例如 live_抖音_主播名_1234567890
    
    返回：
    - 删除结果
    """
    try:
        import shutil
        from pathlib import Path
        
        svc = get_live_report_service()
        records_root = svc.records_root
        
        logger.info(f"🗑️ 尝试删除报告: {session_id}")
        
        # 查找会话目录（可能在不同的平台/主播/日期下）
        session_dirs = list(records_root.rglob(session_id))
        
        if not session_dirs:
            logger.warning(f"⚠️ 未找到会话目录: {session_id}")
            raise HTTPException(status_code=404, detail=f"报告不存在: {session_id}")
        
        # 删除所有匹配的目录（通常只有一个）
        deleted_count = 0
        for session_dir in session_dirs:
            if session_dir.is_dir():
                try:
                    shutil.rmtree(session_dir)
                    logger.info(f"✅ 已删除目录: {session_dir}")
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"❌ 删除目录失败: {session_dir}, 错误: {e}")
        
        if deleted_count == 0:
            raise HTTPException(status_code=500, detail="删除报告失败")
        
        logger.info(f"✅ 成功删除 {deleted_count} 个报告目录")
        
        return BaseResp(
            success=True,
            message=f"成功删除报告 {session_id}",
            data={"deleted_count": deleted_count}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除报告失败: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除报告失败: {str(e)}")

