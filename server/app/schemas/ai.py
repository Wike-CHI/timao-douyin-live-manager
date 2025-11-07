# -*- coding: utf-8 -*-
"""
AI 相关数据模型
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from ..schemas.common import BaseResponse


class StartAILiveAnalysisRequest(BaseModel):
    """启动AI实时分析请求"""
    window_sec: int = Field(60, ge=30, le=600, description="分析窗口时长（秒）")
    session_id: Optional[str] = Field(None, description="统一会话ID（可选）")


class GenerateAnswerScriptsRequest(BaseModel):
    """生成回答话术请求"""
    questions: List[str] = Field(..., min_items=1, description="待回答的弹幕问题列表")
    transcript: Optional[str] = Field(None, description="可选的口播上下文（多句换行）")
    style_profile: Optional[Dict[str, Any]] = Field(None, description="可选的主播画像覆盖")
    vibe: Optional[Dict[str, Any]] = Field(None, description="可选的氛围上下文")


class GenerateOneScriptRequest(BaseModel):
    """生成单条话术请求"""
    script_type: str = Field("interaction", description="welcome/product/interaction/closing/question/emotion 等")
    include_context: bool = Field(True, description="是否注入 style_profile/vibe")
    context: Optional[Dict[str, Any]] = Field(None, description="额外上下文，覆盖/补充生成上下文")


class SubmitScriptFeedbackRequest(BaseModel):
    """提交话术反馈请求"""
    script_id: str = Field(..., description="AI 生成结果的唯一标识")
    script_text: str = Field(..., description="AI 输出的原始话术内容")
    score: int = Field(..., ge=1, le=5, description="人工评分，1-2 视为负面，4-5 视为正面")
    tags: List[str] = Field(default_factory=list, description="可选标签，如语气、风险等")
    anchor_id: Optional[str] = Field(None, description="主播或房间ID，用于区分记忆")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="额外上下文，如style_profile/vibe等，便于后端记录"
    )


class StartAILiveAnalysisResponse(BaseResponse[Dict[str, Any]]):
    """启动AI实时分析响应"""
    pass


class GenerateAnswerScriptsResponse(BaseResponse[Dict[str, Any]]):
    """生成回答话术响应"""
    pass


class GenerateOneScriptResponse(BaseResponse[Dict[str, Any]]):
    """生成单条话术响应"""
    pass

