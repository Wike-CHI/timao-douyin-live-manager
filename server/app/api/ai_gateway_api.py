"""
AI 网关管理 API

提供 RESTful API 用于管理 AI 服务商配置和切换
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

from server.ai.ai_gateway import get_gateway, AIProvider

router = APIRouter(prefix="/api/ai_gateway", tags=["AI网关管理"])


class RegisterProviderRequest(BaseModel):
    """注册服务商请求"""
    provider: str = Field(..., description="服务商名称")
    api_key: str = Field(..., description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    default_model: Optional[str] = Field(None, description="默认模型")
    models: Optional[List[str]] = Field(None, description="支持的模型列表")
    enabled: bool = Field(True, description="是否启用")


class SwitchProviderRequest(BaseModel):
    """切换服务商请求"""
    provider: str = Field(..., description="服务商名称")
    model: Optional[str] = Field(None, description="模型名称")


class SetFallbackRequest(BaseModel):
    """设置降级链请求"""
    providers: List[str] = Field(..., description="服务商列表（按优先级排序）")


class ChatCompletionRequest(BaseModel):
    """对话补全请求"""
    messages: List[Dict[str, str]] = Field(..., description="消息列表")
    provider: Optional[str] = Field(None, description="临时指定服务商")
    model: Optional[str] = Field(None, description="临时指定模型")
    temperature: float = Field(0.3, description="温度参数", ge=0, le=2)
    max_tokens: Optional[int] = Field(None, description="最大token数")
    response_format: Optional[Dict[str, str]] = Field(None, description="响应格式")


@router.get("/status")
async def get_status():
    """获取网关状态"""
    gateway = get_gateway()
    return {
        "success": True,
        "current": gateway.get_current_config(),
        "providers": gateway.list_providers(),
    }


@router.post("/register")
async def register_provider(req: RegisterProviderRequest):
    """注册一个服务商"""
    try:
        gateway = get_gateway()
        gateway.register_provider(
            provider=req.provider,
            api_key=req.api_key,
            base_url=req.base_url,
            default_model=req.default_model,
            models=req.models,
            enabled=req.enabled,
        )
        return {
            "success": True,
            "message": f"服务商 {req.provider} 已注册",
            "config": gateway.providers[req.provider.lower()].__dict__,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/switch")
async def switch_provider(req: SwitchProviderRequest):
    """切换当前服务商"""
    try:
        gateway = get_gateway()
        gateway.switch_provider(req.provider, req.model)
        return {
            "success": True,
            "message": f"已切换至 {req.provider}/{req.model or '默认模型'}",
            "current": gateway.get_current_config(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/fallback")
async def set_fallback_chain(req: SetFallbackRequest):
    """设置服务商降级链"""
    try:
        gateway = get_gateway()
        gateway.set_fallback_chain(req.providers)
        return {
            "success": True,
            "message": "降级链已设置",
            "fallback_chain": gateway.fallback_chain,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/providers")
async def list_providers():
    """列出所有服务商"""
    gateway = get_gateway()
    return {
        "success": True,
        "providers": gateway.list_providers(),
        "current": gateway.current_provider,
    }


@router.post("/chat")
async def chat_completion(req: ChatCompletionRequest):
    """对话补全（测试接口）"""
    try:
        gateway = get_gateway()
        response = gateway.chat_completion(
            messages=req.messages,
            provider=req.provider,
            model=req.model,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            response_format=req.response_format,
        )
        
        return {
            "success": response.success,
            "content": response.content,
            "model": response.model,
            "provider": response.provider,
            "usage": response.usage,
            "cost": response.cost,
            "duration_ms": response.duration_ms,
            "error": response.error,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{provider}")
async def get_provider_models(provider: str):
    """获取服务商支持的模型列表"""
    gateway = get_gateway()
    provider = provider.lower()
    
    if provider not in gateway.providers:
        raise HTTPException(status_code=404, detail=f"未注册的服务商: {provider}")
    
    config = gateway.providers[provider]
    return {
        "success": True,
        "provider": provider,
        "models": config.models,
        "default_model": config.default_model,
    }
