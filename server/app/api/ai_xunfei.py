"""
科大讯飞 AI 服务 API
提供基于讯飞星火 Lite 模型的 AI 分析、话术生成、氛围与情绪分析
"""

import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...ai.xunfei_lite_client import get_xunfei_client, XUNFEI_MODELS
from ...utils.ai_usage_monitor import get_usage_monitor

router = APIRouter(prefix="/api/ai/xunfei", tags=["科大讯飞AI"])


class AtmosphereAnalysisReq(BaseModel):
    """氛围分析请求"""
    transcript: str = Field(..., description="主播口播转写")
    comments: List[Dict[str, Any]] = Field(default_factory=list, description="弹幕评论列表")
    context: Optional[Dict[str, Any]] = Field(default=None, description="上下文信息")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    anchor_id: Optional[str] = Field(default=None, description="主播ID")
    session_id: Optional[str] = Field(default=None, description="会话ID")


class ScriptGenerationReq(BaseModel):
    """话术生成请求"""
    script_type: str = Field(
        ...,
        description="话术类型: interaction/engagement/clarification/humor/transition/call_to_action"
    )
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    anchor_id: Optional[str] = Field(default=None, description="主播ID")
    session_id: Optional[str] = Field(default=None, description="会话ID")


class RealtimeAnalysisReq(BaseModel):
    """实时分析请求"""
    transcript: str = Field(..., description="口播转写")
    comments: List[Dict[str, Any]] = Field(default_factory=list, description="弹幕评论")
    previous_summary: Optional[str] = Field(default=None, description="上一窗口摘要")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    anchor_id: Optional[str] = Field(default=None, description="主播ID")
    session_id: Optional[str] = Field(default=None, description="会话ID")


class ChatCompletionReq(BaseModel):
    """聊天完成请求"""
    messages: List[Dict[str, Any]] = Field(..., description="消息列表")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(default=2000, ge=1, le=8000, description="最大token数")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    anchor_id: Optional[str] = Field(default=None, description="主播ID")
    session_id: Optional[str] = Field(default=None, description="会话ID")


@router.get("/models")
async def list_models():
    """获取可用模型列表"""
    return {
        "success": True,
        "models": [
            {"id": model_id, "name": model_name}
            for model_id, model_name in XUNFEI_MODELS.items()
        ],
        "default": "lite"
    }


@router.post("/test")
async def test_connection(user_id: Optional[str] = None):
    """测试讯飞 API 连接"""
    try:
        client = get_xunfei_client()
        
        start_time = time.time()
        content, usage = client.chat_completion(
            messages=[{"role": "user", "content": "你好"}],
            max_tokens=50
        )
        duration_ms = (time.time() - start_time) * 1000
        
        # 记录使用量
        monitor = get_usage_monitor()
        monitor.record_usage(
            model=client.model,
            function="测试连接",
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            duration_ms=duration_ms,
            user_id=user_id,
            success=True
        )
        
        return {
            "success": True,
            "message": "连接成功",
            "response": content,
            "model": client.model,
            "usage": {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "request_time_ms": usage.request_time_ms
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接失败: {str(e)}")


@router.post("/chat/completions")
async def chat_completions(req: ChatCompletionReq):
    """聊天完成接口"""
    try:
        client = get_xunfei_client()
        
        start_time = time.time()
        content, usage = client.chat_completion(
            messages=req.messages,
            temperature=req.temperature,
            max_tokens=req.max_tokens
        )
        duration_ms = (time.time() - start_time) * 1000
        
        # 记录使用量
        monitor = get_usage_monitor()
        monitor.record_usage(
            model=client.model,
            function="聊天完成",
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            duration_ms=duration_ms,
            user_id=req.user_id,
            anchor_id=req.anchor_id,
            session_id=req.session_id,
            success=True
        )
        
        return {
            "success": True,
            "content": content,
            "model": client.model,
            "usage": {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "request_time_ms": usage.request_time_ms
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/atmosphere")
async def analyze_atmosphere(req: AtmosphereAnalysisReq):
    """
    分析直播间氛围与情绪
    
    返回：
    - atmosphere: 氛围状态（冷淡/一般/活跃/火爆）
    - emotion: 情绪分析（主要情绪、次要情绪、强度）
    - engagement: 互动参与度
    - trends: 氛围趋势
    - suggestions: 改善建议
    - usage: Token消耗统计
    """
    try:
        client = get_xunfei_client()
        
        start_time = time.time()
        result = client.analyze_live_atmosphere(
            transcript=req.transcript,
            comments=req.comments,
            context=req.context
        )
        duration_ms = (time.time() - start_time) * 1000
        
        # 提取使用量
        usage_info = result.pop("_usage", {})
        
        # 记录使用量
        monitor = get_usage_monitor()
        monitor.record_usage(
            model=client.model,
            function="直播间氛围与情绪分析",
            input_tokens=usage_info.get("prompt_tokens", 0),
            output_tokens=usage_info.get("completion_tokens", 0),
            duration_ms=duration_ms,
            user_id=req.user_id,
            anchor_id=req.anchor_id,
            session_id=req.session_id,
            success=True
        )
        
        return {
            "success": True,
            "data": result,
            "usage": usage_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/script")
async def generate_script(req: ScriptGenerationReq):
    """
    生成直播话术
    
    话术类型：
    - interaction: 互动引导话术
    - engagement: 关注点赞召唤话术
    - clarification: 澄清回应话术
    - humor: 幽默活跃话术
    - transition: 转场过渡话术
    - call_to_action: 行动召唤话术
    
    返回：
    - line: 话术内容
    - tone: 语气提示
    - tags: 话术标签
    - usage: Token消耗统计
    """
    try:
        client = get_xunfei_client()
        
        start_time = time.time()
        result = client.generate_script(
            script_type=req.script_type,
            context=req.context
        )
        duration_ms = (time.time() - start_time) * 1000
        
        # 提取使用量
        usage_info = result.pop("_usage", {})
        
        # 记录使用量
        monitor = get_usage_monitor()
        monitor.record_usage(
            model=client.model,
            function="话术生成",
            input_tokens=usage_info.get("prompt_tokens", 0),
            output_tokens=usage_info.get("completion_tokens", 0),
            duration_ms=duration_ms,
            user_id=req.user_id,
            anchor_id=req.anchor_id,
            session_id=req.session_id,
            success=True
        )
        
        return {
            "success": True,
            "data": result,
            "usage": usage_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/realtime")
async def analyze_realtime(req: RealtimeAnalysisReq):
    """
    实时分析（窗口级分析）
    
    用于对直播窗口（如5分钟）进行实时分析，包括：
    - 节奏复盘
    - 亮点识别
    - 风险预警
    - 下一步建议
    - 氛围评估
    - 情绪分析
    
    返回：
    - summary: 窗口摘要
    - highlight_points: 亮点列表
    - risks: 风险列表
    - suggestions: 建议列表
    - scripts: 推荐话术
    - atmosphere: 氛围评估
    - emotion: 情绪分析
    - usage: Token消耗统计
    """
    try:
        client = get_xunfei_client()
        
        start_time = time.time()
        result = client.analyze_realtime(
            transcript=req.transcript,
            comments=req.comments,
            previous_summary=req.previous_summary,
            anchor_id=req.anchor_id
        )
        duration_ms = (time.time() - start_time) * 1000
        
        # 提取使用量
        usage_info = result.pop("_usage", {})
        
        # 记录使用量
        monitor = get_usage_monitor()
        monitor.record_usage(
            model=client.model,
            function="实时分析",
            input_tokens=usage_info.get("prompt_tokens", 0),
            output_tokens=usage_info.get("completion_tokens", 0),
            duration_ms=duration_ms,
            user_id=req.user_id,
            anchor_id=req.anchor_id,
            session_id=req.session_id,
            success=True
        )
        
        return {
            "success": True,
            "data": result,
            "usage": usage_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage/stats")
async def get_usage_stats(days: int = 7):
    """
    获取讯飞模型使用统计
    
    Args:
        days: 统计天数，默认7天
        
    Returns:
        统计数据，包括调用次数、token消耗、费用等
    """
    try:
        monitor = get_usage_monitor()
        summary = monitor.get_daily_summary(days_ago=0)
        
        # 筛选讯飞模型的数据
        xunfei_models = ["lite", "generalv3", "generalv3.5", "4.0Ultra"]
        xunfei_stats = {
            model: stats
            for model, stats in summary.by_model.items()
            if model in xunfei_models
        }
        
        # 计算总计
        total_calls = sum(s["calls"] for s in xunfei_stats.values())
        total_tokens = sum(s["total_tokens"] for s in xunfei_stats.values())
        total_cost = sum(s["cost"] for s in xunfei_stats.values())
        
        return {
            "success": True,
            "period_days": days,
            "total": {
                "calls": total_calls,
                "tokens": total_tokens,
                "cost": total_cost
            },
            "by_model": xunfei_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

