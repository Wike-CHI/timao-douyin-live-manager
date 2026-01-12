# -*- coding: utf-8 -*-
"""
启动检测API

提供环境检测、配置状态查询等功能，支持初次启动向导。
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging

from server.local.local_config import LocalAIConfig
from server.utils.bootstrap import get_status, bootstrap_all, start_bootstrap_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bootstrap", tags=["启动检测"])


class ProviderConfigRequest(BaseModel):
    """服务商配置请求"""
    provider_id: str
    api_key: str
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    enabled: bool = True


class FunctionModelRequest(BaseModel):
    """功能模型配置请求"""
    function_id: str
    provider: str
    model: str


class BatchFunctionModelRequest(BaseModel):
    """批量功能模型配置请求"""
    function_models: Dict[str, Dict[str, str]]


@router.get("/status")
async def get_bootstrap_status() -> Dict[str, Any]:
    """
    获取启动检测状态
    
    Returns:
        环境状态、AI配置状态、是否需要设置向导
    """
    try:
        # 获取环境检测状态
        env_status = get_status()
        
        # 获取AI配置状态
        ai_initialized = LocalAIConfig.is_initialized()
        ai_config = LocalAIConfig.get_config()
        configured_providers = list(ai_config.get("providers", {}).keys())
        
        return {
            "success": True,
            "data": {
                "environment": {
                    "ffmpeg": env_status.get("ffmpeg", {}),
                    "models": env_status.get("models", {}),
                    "paths": env_status.get("paths", {}),
                    "running": env_status.get("running", False)
                },
                "ai_config": {
                    "initialized": ai_initialized,
                    "configured_providers": configured_providers,
                    "active_provider": ai_config.get("active_provider")
                },
                "need_setup": not ai_initialized,
                "suggestions": env_status.get("suggestions", [])
            }
        }
    except Exception as e:
        logger.error(f"获取启动状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_environment_check() -> Dict[str, Any]:
    """
    开始环境检测和自动下载
    
    触发FFMPEG和模型的自动检测和下载。
    """
    try:
        # 异步启动检测
        start_bootstrap_async()
        
        return {
            "success": True,
            "message": "环境检测已启动",
            "data": get_status()
        }
    except Exception as e:
        logger.error(f"启动环境检测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-sync")
async def run_environment_check_sync() -> Dict[str, Any]:
    """
    同步运行环境检测（等待完成）
    
    适用于需要等待检测完成的场景。
    """
    try:
        result = bootstrap_all()
        return {
            "success": True,
            "message": "环境检测完成",
            "data": result
        }
    except Exception as e:
        logger.error(f"环境检测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== AI配置API ==========

@router.get("/ai/templates")
async def get_provider_templates() -> Dict[str, Any]:
    """获取所有支持的AI服务商模板"""
    return {
        "success": True,
        "data": LocalAIConfig.get_provider_templates()
    }


@router.get("/ai/providers")
async def get_configured_providers() -> Dict[str, Any]:
    """获取已配置的AI服务商"""
    config = LocalAIConfig.get_config()
    providers = config.get("providers", {})
    
    # 隐藏API Key的完整内容
    safe_providers = {}
    for pid, pconfig in providers.items():
        safe_providers[pid] = {
            **pconfig,
            "api_key": "***" + pconfig.get("api_key", "")[-4:] if pconfig.get("api_key") else ""
        }
    
    return {
        "success": True,
        "data": {
            "providers": safe_providers,
            "active_provider": config.get("active_provider")
        }
    }


@router.post("/ai/provider")
async def save_provider_config(request: ProviderConfigRequest) -> Dict[str, Any]:
    """保存AI服务商配置"""
    try:
        success = LocalAIConfig.save_provider(
            provider_id=request.provider_id,
            api_key=request.api_key,
            base_url=request.base_url,
            default_model=request.default_model,
            enabled=request.enabled
        )
        
        if success:
            return {
                "success": True,
                "message": f"服务商 {request.provider_id} 配置已保存"
            }
        else:
            raise HTTPException(status_code=500, detail="保存配置失败")
            
    except Exception as e:
        logger.error(f"保存服务商配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/ai/provider/{provider_id}")
async def remove_provider_config(provider_id: str) -> Dict[str, Any]:
    """移除AI服务商配置"""
    try:
        success = LocalAIConfig.remove_provider(provider_id)
        if success:
            return {
                "success": True,
                "message": f"服务商 {provider_id} 已移除"
            }
        else:
            raise HTTPException(status_code=500, detail="移除配置失败")
    except Exception as e:
        logger.error(f"移除服务商配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/provider/{provider_id}/test")
async def test_provider_connection(provider_id: str) -> Dict[str, Any]:
    """测试AI服务商连接"""
    try:
        result = LocalAIConfig.test_provider(provider_id)
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "data": {
                "latency_ms": result.get("latency_ms")
            }
        }
    except Exception as e:
        logger.error(f"测试服务商连接失败: {e}")
        return {
            "success": False,
            "message": str(e)
        }


@router.post("/ai/provider/{provider_id}/activate")
async def activate_provider(provider_id: str) -> Dict[str, Any]:
    """设置活跃的AI服务商"""
    try:
        success = LocalAIConfig.set_active_provider(provider_id)
        if success:
            return {
                "success": True,
                "message": f"已切换到服务商 {provider_id}"
            }
        else:
            raise HTTPException(status_code=400, detail="服务商未配置")
    except Exception as e:
        logger.error(f"切换服务商失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 功能模型配置API ==========

@router.get("/ai/functions")
async def get_function_models() -> Dict[str, Any]:
    """获取所有功能的模型配置"""
    function_models = LocalAIConfig.get_function_models()
    function_names = LocalAIConfig.FUNCTION_NAMES
    
    # 组合功能信息
    functions = []
    for func_id, config in function_models.items():
        functions.append({
            "id": func_id,
            "name": function_names.get(func_id, func_id),
            "provider": config.get("provider"),
            "model": config.get("model")
        })
    
    return {
        "success": True,
        "data": {
            "functions": functions,
            "function_names": function_names
        }
    }


@router.post("/ai/function")
async def set_function_model(request: FunctionModelRequest) -> Dict[str, Any]:
    """设置功能使用的模型"""
    try:
        success = LocalAIConfig.set_function_model(
            function_id=request.function_id,
            provider=request.provider,
            model=request.model
        )
        
        if success:
            return {
                "success": True,
                "message": f"功能 {request.function_id} 配置已保存"
            }
        else:
            raise HTTPException(status_code=500, detail="保存配置失败")
            
    except Exception as e:
        logger.error(f"保存功能配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/functions/batch")
async def set_function_models_batch(request: BatchFunctionModelRequest) -> Dict[str, Any]:
    """批量设置功能模型"""
    try:
        for func_id, config in request.function_models.items():
            LocalAIConfig.set_function_model(
                function_id=func_id,
                provider=config.get("provider", ""),
                model=config.get("model", "")
            )
        
        return {
            "success": True,
            "message": f"已保存 {len(request.function_models)} 个功能配置"
        }
    except Exception as e:
        logger.error(f"批量保存功能配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 初始化完成API ==========

@router.post("/ai/initialize")
async def mark_ai_initialized() -> Dict[str, Any]:
    """标记AI配置已完成初始化"""
    try:
        # 检查是否至少配置了一个服务商
        config = LocalAIConfig.get_config()
        providers = config.get("providers", {})
        has_valid_provider = any(
            p.get("enabled") and p.get("api_key") 
            for p in providers.values()
        )
        
        if not has_valid_provider:
            raise HTTPException(
                status_code=400, 
                detail="请至少配置一个AI服务商后再完成初始化"
            )
        
        success = LocalAIConfig.mark_initialized()
        if success:
            return {
                "success": True,
                "message": "AI配置初始化完成"
            }
        else:
            raise HTTPException(status_code=500, detail="标记初始化失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标记初始化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 使用统计API ==========

@router.get("/ai/usage")
async def get_ai_usage_stats() -> Dict[str, Any]:
    """获取AI使用统计"""
    return {
        "success": True,
        "data": {
            "summary": LocalAIConfig.get_usage_stats(),
            "recent": LocalAIConfig.get_recent_usage(50)
        }
    }
