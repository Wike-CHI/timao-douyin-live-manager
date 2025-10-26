"""
AI 使用量监控 API
提供使用统计、成本分析、报告导出等功能
"""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from ...utils.ai_usage_monitor import get_usage_monitor, ModelPricing

router = APIRouter(prefix="/api/ai_usage", tags=["AI使用监控"])


@router.get("/stats/current")
async def get_current_stats():
    """获取当前实时统计"""
    monitor = get_usage_monitor()
    hourly = monitor.get_hourly_summary(hours_ago=0)
    daily = monitor.get_daily_summary(days_ago=0)
    
    return {
        "current_hour": {
            "calls": hourly.total_calls,
            "tokens": hourly.total_tokens,
            "cost": hourly.total_cost,
            "success_rate": (
                round(hourly.successful_calls / hourly.total_calls * 100, 2)
                if hourly.total_calls > 0 else 0
            )
        },
        "today": {
            "calls": daily.total_calls,
            "tokens": daily.total_tokens,
            "cost": daily.total_cost,
            "by_model": daily.by_model,
            "by_function": daily.by_function
        }
    }


@router.get("/stats/hourly")
async def get_hourly_stats(
    hours_ago: int = Query(0, ge=0, le=72, description="小时偏移（0=当前小时）")
):
    """获取指定小时的统计"""
    monitor = get_usage_monitor()
    summary = monitor.get_hourly_summary(hours_ago=hours_ago)
    
    return {
        "period": "hourly",
        "start_time": datetime.fromtimestamp(summary.start_time).isoformat(),
        "end_time": datetime.fromtimestamp(summary.end_time).isoformat(),
        "total_calls": summary.total_calls,
        "successful_calls": summary.successful_calls,
        "failed_calls": summary.failed_calls,
        "total_tokens": summary.total_tokens,
        "input_tokens": summary.total_input_tokens,
        "output_tokens": summary.total_output_tokens,
        "total_cost": summary.total_cost,
        "by_model": summary.by_model,
        "by_function": summary.by_function
    }


@router.get("/stats/daily")
async def get_daily_stats(
    days_ago: int = Query(0, ge=0, le=90, description="天数偏移（0=今天）")
):
    """获取指定日期的统计"""
    monitor = get_usage_monitor()
    summary = monitor.get_daily_summary(days_ago=days_ago)
    
    return {
        "period": "daily",
        "date": datetime.fromtimestamp(summary.start_time).strftime("%Y-%m-%d"),
        "total_calls": summary.total_calls,
        "successful_calls": summary.successful_calls,
        "failed_calls": summary.failed_calls,
        "total_tokens": summary.total_tokens,
        "input_tokens": summary.total_input_tokens,
        "output_tokens": summary.total_output_tokens,
        "total_cost": summary.total_cost,
        "by_model": summary.by_model,
        "by_function": summary.by_function,
        "by_user": summary.by_user,
        "by_anchor": summary.by_anchor
    }


@router.get("/stats/monthly")
async def get_monthly_stats(
    year: Optional[int] = Query(None, description="年份"),
    month: Optional[int] = Query(None, ge=1, le=12, description="月份")
):
    """获取指定月份的统计"""
    monitor = get_usage_monitor()
    summary = monitor.get_monthly_summary(year=year, month=month)
    
    return {
        "period": "monthly",
        "year_month": datetime.fromtimestamp(summary.start_time).strftime("%Y-%m"),
        "total_calls": summary.total_calls,
        "successful_calls": summary.successful_calls,
        "failed_calls": summary.failed_calls,
        "total_tokens": summary.total_tokens,
        "input_tokens": summary.total_input_tokens,
        "output_tokens": summary.total_output_tokens,
        "total_cost": summary.total_cost,
        "by_model": summary.by_model,
        "by_function": summary.by_function,
        "by_user": summary.by_user,
        "by_anchor": summary.by_anchor
    }


@router.get("/session/{session_id}")
async def get_session_stats(session_id: str):
    """获取会话统计"""
    monitor = get_usage_monitor()
    stats = monitor.get_session_stats(session_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="会话不存在或无数据")
    
    return {
        "session_id": session_id,
        "calls": stats.get("calls", 0),
        "tokens": stats.get("tokens", 0),
        "cost": round(stats.get("cost", 0.0), 4)
    }


@router.get("/top_users")
async def get_top_users(
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    days: int = Query(7, ge=1, le=90, description="统计天数")
):
    """获取 Token 消耗最多的用户"""
    monitor = get_usage_monitor()
    top_users = monitor.get_top_users(limit=limit, days=days)
    
    return {
        "period_days": days,
        "top_users": top_users
    }


@router.get("/cost_trend")
async def get_cost_trend(
    days: int = Query(30, ge=1, le=90, description="统计天数")
):
    """获取成本趋势"""
    monitor = get_usage_monitor()
    trend = monitor.get_cost_trend(days=days)
    
    return {
        "period_days": days,
        "data": trend
    }


@router.get("/models/pricing")
async def get_model_pricing():
    """获取模型定价信息"""
    return {
        "qwen_series": ModelPricing.QWEN_PRICING,
        "openai_series": ModelPricing.OPENAI_PRICING,
        "note": "价格单位：元/1K tokens"
    }


@router.post("/export_report")
async def export_report(
    days: int = Query(7, ge=1, le=90, description="统计天数")
):
    """导出使用报告"""
    monitor = get_usage_monitor()
    report_path = monitor.export_report(days=days)
    
    return {
        "success": True,
        "report_path": str(report_path),
        "download_url": f"/api/ai_usage/download_report?path={report_path.name}"
    }


@router.get("/download_report")
async def download_report(path: str):
    """下载使用报告"""
    monitor = get_usage_monitor()
    file_path = monitor.data_dir / path
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="报告文件不存在")
    
    return FileResponse(
        path=file_path,
        media_type="application/json",
        filename=file_path.name
    )


@router.get("/dashboard")
async def get_dashboard_data():
    """获取仪表盘数据（综合视图）"""
    monitor = get_usage_monitor()
    
    # 今日统计
    today = monitor.get_daily_summary(days_ago=0)
    
    # 本月统计
    monthly = monitor.get_monthly_summary()
    
    # Top 用户
    top_users = monitor.get_top_users(limit=5, days=7)
    
    # 成本趋势
    cost_trend = monitor.get_cost_trend(days=7)
    
    # 计算同比
    yesterday = monitor.get_daily_summary(days_ago=1)
    cost_change = (
        round((today.total_cost - yesterday.total_cost) / yesterday.total_cost * 100, 2)
        if yesterday.total_cost > 0 else 0
    )
    
    return {
        "today": {
            "calls": today.total_calls,
            "tokens": today.total_tokens,
            "cost": today.total_cost,
            "cost_change_percent": cost_change,
            "success_rate": (
                round(today.successful_calls / today.total_calls * 100, 2)
                if today.total_calls > 0 else 0
            )
        },
        "this_month": {
            "calls": monthly.total_calls,
            "tokens": monthly.total_tokens,
            "cost": monthly.total_cost,
            "avg_daily_cost": round(monthly.total_cost / datetime.now().day, 2)
        },
        "top_users": top_users,
        "cost_trend_7days": cost_trend,
        "model_distribution": today.by_model,
        "function_distribution": today.by_function
    }
