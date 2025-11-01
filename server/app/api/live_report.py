# -*- coding: utf-8 -*-
"""
Live Report API
Start/stop a live recording session (Douyin), and after finishing, run
SenseVoice transcription per 30-min segment and compose a recap report.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.live_report_service import get_live_report_service


router = APIRouter(prefix="/api/report/live", tags=["live-report"])


class StartReq(BaseModel):
    live_url: str = Field(..., description="Douyin live URL, e.g., https://live.douyin.com/xxxx")
    segment_minutes: int = Field(30, ge=5, le=120, description="Segment length in minutes (default 30)")


class BaseResp(BaseModel):
    success: bool = True
    message: str = "ok"
    data: Optional[dict] = None


@router.post("/start")
async def start_live_report(req: StartReq) -> BaseResp:
    try:
        svc = get_live_report_service()
        status = await svc.start(req.live_url, req.segment_minutes)
        return BaseResp(data={
            "session_id": status.session_id,
            "recording_pid": status.recording_pid,
            "recording_dir": status.recording_dir,
            "segment_seconds": status.segment_seconds,
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
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
        return BaseResp(data={
            "session_id": status.session_id,
            "stopped_at": status.stopped_at,
            "segments": status.segments,
            "comments_count": status.comments_count,
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


@router.get("/status")
async def live_report_status() -> dict:
    svc = get_live_report_service()
    s = svc.status()
    return {"active": s is not None, "status": s.__dict__ if s else None}


@router.post("/generate")
async def generate_live_report() -> BaseResp:
    try:
        svc = get_live_report_service()
        artifacts = await svc.generate_report()
        return BaseResp(data=artifacts)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Live report generate failed: {type(e).__name__}: {str(e)}", exc_info=True)
        
        # 提供更具体的错误信息
        error_msg = str(e)
        if "no active session" in error_msg.lower() or "not started" in error_msg.lower():
            raise HTTPException(status_code=404, detail="没有正在运行的录制会话，无法生成报告")
        else:
            raise HTTPException(status_code=400, detail=f"生成直播报告失败: {error_msg}")


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

