# -*- coding: utf-8 -*-
"""
本地服务初始化状态路由
提供 FFmpeg、模型下载等状态查询
"""

import logging
from fastapi import APIRouter, BackgroundTasks
from typing import Dict, Any

router = APIRouter(prefix="/api/bootstrap", tags=["初始化"])
logger = logging.getLogger(__name__)


@router.get("/status")
async def get_bootstrap_status() -> Dict[str, Any]:
    """获取本地服务初始化状态"""
    try:
        from ..utils.bootstrap import get_status
        status = get_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"获取初始化状态失败: {e}")
        return {
            "success": False,
            "data": {
                "running": False,
                "ffmpeg": {"state": "unknown", "path": "", "error": str(e)},
                "models": {"state": "unknown", "model_present": False, "vad_present": False},
                "suggestions": ["无法获取状态"],
                "paths": {"model_dir": "", "vad_dir": "", "ffmpeg_dir": ""}
            }
        }


@router.post("/start")
async def start_bootstrap(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """启动初始化流程（后台异步）"""
    try:
        from ..utils.bootstrap import start_bootstrap_async
        background_tasks.add_task(start_bootstrap_async)
        return {
            "success": True,
            "message": "初始化流程已在后台启动"
        }
    except Exception as e:
        logger.error(f"启动初始化流程失败: {e}")
        return {
            "success": False,
            "message": f"启动失败: {str(e)}"
        }
