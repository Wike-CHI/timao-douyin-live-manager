# -*- coding: utf-8 -*-
"""AI Script Generation API

Expose a lightweight endpoint to generate a single, directly-usable live script
line by leveraging the latest style_profile/vibe learned by the AI live analyzer.
Falls back to template generation if AI key is not configured.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.ai_live_analyzer import get_ai_live_analyzer

router = APIRouter(prefix="/api/ai/scripts", tags=["ai-scripts"])


class GenOneReq(BaseModel):
    script_type: str = Field("interaction", description="welcome/product/interaction/closing/question/emotion 等")
    include_context: bool = Field(True, description="是否注入 style_profile/vibe")
    # 可选直传热词或其他上下文
    context: Optional[Dict[str, Any]] = Field(None, description="额外上下文，覆盖/补充生成上下文")


class FeedbackReq(BaseModel):
    script_id: str = Field(..., description="AI 生成结果的唯一标识")
    script_text: str = Field(..., description="AI 输出的原始话术内容")
    score: int = Field(..., ge=1, le=5, description="人工评分，1-2 视为负面，4-5 视为正面")
    tags: List[str] = Field(default_factory=list, description="可选标签，如语气、风险等")
    anchor_id: Optional[str] = Field(None, description="主播或房间ID，用于区分记忆")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="额外上下文，如style_profile/vibe等，便于后端记录"
    )


@router.post("/generate_one")
def generate_one(req: GenOneReq) -> Dict[str, Any]:
    try:
        # 1) 收集上下文（从实时分析服务获取最新风格与氛围）
        ctx: Dict[str, Any] = {}
        if req.include_context:
            try:
                st = get_ai_live_analyzer().status()
                sp = st.get("style_profile") or {}
                vb = st.get("vibe") or {}
                if isinstance(sp, dict):
                    ctx["style_profile"] = sp
                if isinstance(vb, dict):
                    ctx["vibe"] = vb
            except Exception:
                pass
        if req.context and isinstance(req.context, dict):
            ctx.update(req.context)

        # 2) 初始化生成器
        from ...ai.generator import AIScriptGenerator  # lazy import
        # Use Qwen OpenAI-compatible defaults to stay consistent with repo config
        from ...ai.qwen_openai_compatible import (
            DEFAULT_OPENAI_API_KEY,
            DEFAULT_OPENAI_BASE_URL,
            DEFAULT_OPENAI_MODEL,
        )

        cfg = {
            "ai_service": os.getenv("AI_SERVICE", "qwen"),
            "ai_api_key": os.getenv("AI_API_KEY", DEFAULT_OPENAI_API_KEY),
            "ai_base_url": os.getenv("AI_BASE_URL", DEFAULT_OPENAI_BASE_URL),
            "ai_model": os.getenv("AI_MODEL", DEFAULT_OPENAI_MODEL),
        }
        anchor_id = None
        if ctx.get("anchor_id"):
            anchor_id = ctx["anchor_id"]
        elif os.getenv("ANCHOR_ID"):
            anchor_id = os.getenv("ANCHOR_ID")
        elif os.getenv("DOUYIN_ROOM_ID"):
            anchor_id = os.getenv("DOUYIN_ROOM_ID")
        if anchor_id:
            cfg["anchor_id"] = anchor_id
        gen = AIScriptGenerator(cfg)

        # 3) 生成单条话术（如果未配置 API Key，则走模板回退）
        script = gen.generate_script(script_type=req.script_type, context=ctx)
        return {"success": True, "data": script.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
def submit_feedback(req: FeedbackReq) -> Dict[str, Any]:
    try:
        from ...ai.feedback_memory import get_feedback_manager  # lazy import
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"反馈模块不可用: {exc}") from exc

    manager = get_feedback_manager()
    manager.record_feedback(
        anchor_id=req.anchor_id,
        script_id=req.script_id,
        script_text=req.script_text,
        score=req.score,
        tags=req.tags,
        metadata=req.metadata,
    )

    # 高分脚本同步写入风格记忆，帮助 LangChain 检索更精确
    if req.score >= 4:
        try:
            from ...ai.style_memory import StyleMemoryManager  # type: ignore

            style_manager = StyleMemoryManager()
            if style_manager and style_manager.available():
                style_manager.ingest_scripts(
                    req.anchor_id,
                    [{"text": req.script_text, "tags": req.tags, "score": req.score}],
                )
        except Exception:
            # 如果写入失败不影响主流程
            pass

    return {"success": True}
