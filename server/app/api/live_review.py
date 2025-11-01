# -*- coding: utf-8 -*-
"""
直播复盘 API

提供直播结束后的复盘分析功能，包括：
- 结束直播会话
- 生成复盘报告（Gemini）
- 查询复盘报告
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db_session
from ..services.live_review_service import get_live_review_service
from ..models.live_review import LiveReviewReport
from ..models.live import LiveSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/live/review", tags=["直播复盘"])


class EndSessionRequest(BaseModel):
    """结束直播请求"""
    session_id: int = Field(..., description="直播会话ID")
    generate_review: bool = Field(True, description="是否自动生成复盘报告")


class GenerateReviewRequest(BaseModel):
    """生成复盘报告请求"""
    session_id: int = Field(..., description="直播会话ID")
    force_regenerate: bool = Field(False, description="是否强制重新生成（覆盖已有报告）")


@router.post("/end_session")
async def end_session(
    req: EndSessionRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """结束直播并触发复盘分析
    
    - **session_id**: 直播会话 ID
    - **generate_review**: 是否自动生成复盘报告（默认 True）
    
    返回：
    - 直播会话基本信息
    - 复盘报告生成状态
    """
    session = db.query(LiveSession).filter(LiveSession.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="直播会话不存在")
    
    # 更新会话状态
    if session.status == "live":
        session.status = "ended"
        session.end_time = datetime.utcnow()
        session.calculate_duration()
        db.commit()
        logger.info(f"✅ 直播会话已结束: session_id={session.id}, duration={session.duration}s")
    
    # 如果需要生成复盘，加入后台任务
    if req.generate_review:
        review_service = get_live_review_service()
        background_tasks.add_task(review_service.generate_review, req.session_id, db)
        message = "直播已结束，复盘报告生成中（预计 30-60 秒）..."
    else:
        message = "直播已结束"
    
    return {
        "success": True,
        "message": message,
        "data": {
            "session_id": session.id,
            "room_id": session.room_id,
            "duration": session.duration,
            "total_viewers": session.total_viewers,
            "peak_viewers": session.peak_viewers,
            "comment_count": session.comment_count,
            "gift_value": float(session.gift_value) if session.gift_value else 0
        }
    }


@router.post("/generate")
async def generate_review(
    req: GenerateReviewRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """手动触发复盘报告生成
    
    用于：
    - 补生成之前遗漏的报告
    - 重新生成已有报告（设置 force_regenerate=true）
    
    - **session_id**: 直播会话 ID
    - **force_regenerate**: 是否强制重新生成（默认 False）
    
    返回：
    - 任务状态
    """
    session = db.query(LiveSession).filter(LiveSession.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="直播会话不存在")
    
    if session.status != "ended":
        raise HTTPException(status_code=400, detail=f"直播尚未结束，当前状态: {session.status}")
    
    # 检查是否已有报告
    existing_report = db.query(LiveReviewReport).filter(
        LiveReviewReport.session_id == req.session_id
    ).first()
    
    if existing_report and not req.force_regenerate:
        raise HTTPException(
            status_code=400, 
            detail="复盘报告已存在，如需重新生成请设置 force_regenerate=true"
        )
    
    # 异步生成报告
    review_service = get_live_review_service()
    background_tasks.add_task(review_service.generate_review, req.session_id, db)
    
    return {
        "success": True,
        "message": "复盘报告生成中，预计 30-60 秒后完成",
        "data": {
            "session_id": req.session_id,
            "estimated_time": "30-60秒"
        }
    }


@router.get("/{session_id}")
async def get_review(
    session_id: int,
    db: Session = Depends(get_db_session)
):
    """获取直播复盘报告
    
    - **session_id**: 直播会话 ID
    
    返回：
    - 完整的复盘报告（包含评分、分析、建议等）
    """
    report = db.query(LiveReviewReport).filter(
        LiveReviewReport.session_id == session_id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="复盘报告不存在，可能还未生成")
    
    return {
        "success": True,
        "data": {
            "id": report.id,
            "session_id": report.session_id,
            "status": report.status,
            "overall_score": report.overall_score,
            "performance_analysis": report.performance_analysis,
            "key_highlights": report.key_highlights,
            "key_issues": report.key_issues,
            "improvement_suggestions": report.improvement_suggestions,
            "full_report_markdown": report.full_report_text,
            "generated_at": report.generated_at.isoformat() if report.generated_at else None,
            "ai_model": report.ai_model,
            "generation_cost": float(report.generation_cost) if report.generation_cost else 0,
            "generation_tokens": report.generation_tokens,
            "generation_duration": report.generation_duration,
            "error_message": report.error_message
        }
    }


@router.get("/list/recent")
async def list_recent_reviews(
    limit: int = 10,
    db: Session = Depends(get_db_session)
):
    """获取最近的复盘报告列表
    
    - **limit**: 返回数量（默认 10）
    
    返回：
    - 复盘报告列表（按生成时间倒序）
    """
    reports = db.query(LiveReviewReport).order_by(
        LiveReviewReport.generated_at.desc()
    ).limit(limit).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "session_id": r.session_id,
                "overall_score": r.overall_score,
                "status": r.status,
                "generated_at": r.generated_at.isoformat() if r.generated_at else None,
                "ai_model": r.ai_model
            }
            for r in reports
        ]
    }


@router.delete("/{report_id}")
async def delete_review(
    report_id: int,
    db: Session = Depends(get_db_session)
):
    """删除复盘报告
    
    - **report_id**: 报告 ID
    
    返回：
    - 删除结果
    """
    report = db.query(LiveReviewReport).filter(LiveReviewReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    db.delete(report)
    db.commit()
    
    return {
        "success": True,
        "message": "报告已删除"
    }


@router.get("/session/{session_id}/exists")
async def check_review_exists(
    session_id: int,
    db: Session = Depends(get_db_session)
):
    """检查指定会话是否已有复盘报告
    
    - **session_id**: 直播会话 ID
    
    返回：
    - exists: 是否存在
    - report_id: 报告 ID（如果存在）
    """
    report = db.query(LiveReviewReport).filter(
        LiveReviewReport.session_id == session_id
    ).first()
    
    return {
        "success": True,
        "data": {
            "exists": report is not None,
            "report_id": report.id if report else None,
            "status": report.status if report else None
        }
    }
