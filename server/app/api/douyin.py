# -*- coding: utf-8 -*-
"""
抖音直播监控 API 接口
封装对 DouyinLiveService 的启动/停止/状态查询
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, AsyncGenerator, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

# 服务导入
from ..services.douyin_service import get_douyin_service
from ..services.douyin_web_relay import get_douyin_web_relay
from server.utils.service_logger import log_service_start, log_service_stop, log_service_error
from server.app.schemas import StartDouyinMonitoringRequest, DouyinStatusResponse
from server.app.schemas.common import BaseResponse
from server.app.utils.api import success_response, handle_service_error

router = APIRouter(prefix="/api/douyin", tags=["douyin"])


def _parse_live_id(live_url_or_id: Optional[str]) -> Optional[str]:
    if not live_url_or_id:
        return None
    s = live_url_or_id.strip()
    import re
    m = re.search(r"live\.douyin\.com/([A-Za-z0-9_\-]+)", s)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_\-]+", s):
        return s
    return None


@router.post("/start", response_model=BaseResponse[Dict[str, Any]])
async def start_monitoring(request: StartDouyinMonitoringRequest):
    """
    启动抖音直播监控
    """
    try:
        service = get_douyin_service()
        # 支持 live_url 解析 live_id
        live_id = _parse_live_id(request.live_id) or _parse_live_id(request.live_url)
        if not live_id:
            raise HTTPException(status_code=400, detail="live_id 或 live_url 无效")
        
        log_service_start("抖音直播监控服务", live_id=live_id, live_url=request.live_url)
        
        # 传递可选 cookie 到服务层
        result = await service.start_monitoring(live_id, cookie=request.cookie)
        if result.get("success"):
            log_service_start("抖音直播监控服务", live_id=live_id, status="已启动")
            return success_response(result, message="监控已启动")

        log_service_error("抖音直播监控服务", result.get("error", "监控启动失败"), live_id=live_id)
        return BaseResponse(success=False, message=result.get("error", "监控启动失败"), data=result)
    except Exception as exc:  # pragma: no cover - unexpected failures
        log_service_error("抖音直播监控服务", str(exc), live_id=request.live_id, live_url=request.live_url)
        logging.exception("启动监控失败")
        handle_service_error(exc, {}, default_message="启动抖音监控失败", default_status=500)


@router.post("/stop", response_model=BaseResponse[Dict[str, Any]])
async def stop_monitoring():
    """
    停止抖音直播监控
    """
    try:
        service = get_douyin_service()
        relay = get_douyin_web_relay()
        
        # 获取当前状态以便记录
        relay_status = relay.get_status()
        
        log_service_stop("抖音直播监控服务", live_id=relay_status.live_id, room_id=relay_status.room_id)
        
        # 停止监控服务
        result = await service.stop_monitoring()
        
        # 停止中继服务
        await relay.stop()
        
        if result.get("success"):
            log_service_stop("抖音直播监控服务", status="已停止")
            return success_response(result, message="监控已停止")

        log_service_error("抖音直播监控服务", result.get("error", "监控停止失败"))
        return BaseResponse(success=False, message=result.get("error", "监控停止失败"), data=result)
    except Exception as exc:
        log_service_error("抖音直播监控服务", str(exc))
        logging.exception("停止监控失败")
        handle_service_error(exc, {}, default_message="停止抖音监控失败", default_status=500)


@router.get("/health", response_model=BaseResponse[Dict[str, Any]])
async def health_check():
    """
    抖音服务健康检查
    """
    try:
        service = get_douyin_service()
        relay = get_douyin_web_relay()
        status = service.get_status()
        relay_status = relay.get_status()
        
        return success_response({
            "status": "ok",
            "is_monitoring": status.get("is_monitoring", False) or relay_status.is_running,
            "current_live_id": status.get("current_live_id") or relay_status.live_id,
            "room_id": relay_status.room_id,
        })
    except Exception as exc:
        logging.exception("健康检查失败")
        return success_response({
            "status": "error",
            "is_monitoring": False,
            "current_live_id": None,
            "room_id": None,
            "error": str(exc),
        }, message="服务不可用")


@router.get("/status", response_model=BaseResponse[Dict[str, Any]])
async def get_status():
    """
    获取抖音直播监控状态
    返回格式与 DouyinRelayStatus 接口匹配
    """
    try:
        relay = get_douyin_web_relay()
        relay_status = relay.get_status()
        
        # 确保 room_id 和 live_id 是字符串或 null
        room_id = relay_status.room_id
        if room_id is not None:
            room_id = str(room_id)
        
        live_id = relay_status.live_id
        if live_id is not None:
            live_id = str(live_id)
        
        return success_response(
            DouyinStatusResponse(
                is_monitoring=relay_status.is_running,
                current_live_id=live_id,
                current_room_id=room_id,
                fetcher_status={"last_error": relay_status.last_error},
            ).dict()
        )
    except Exception as exc:
        logging.exception("获取监控状态失败")
        return success_response(
            DouyinStatusResponse(
                is_monitoring=False,
                current_live_id=None,
                current_room_id=None,
                fetcher_status={"last_error": str(exc)},
            ).dict(),
            message="监控未运行",
        )


@router.get("/stream")
async def stream_events():
    """
    抖音直播事件流 (Server-Sent Events)
    推送实时弹幕、礼物、点赞等事件
    """
    async def generate() -> AsyncGenerator[str, None]:
        relay = get_douyin_web_relay()
        queue = None
        try:
            # 注册客户端队列
            queue = await relay.register_client()
            
            # 发送初始连接确认
            yield f"data: {json.dumps({'type': 'connected', 'message': '连接成功'})}\n\n"
            
            # 持续推送事件
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    if event is None:
                        continue
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # 发送心跳保持连接
                    yield f"data: {json.dumps({'type': 'ping', 'timestamp': time.time()})}\n\n"
                except Exception as e:
                    logging.error(f"SSE事件推送错误: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        except Exception as e:
            logging.error(f"SSE连接错误: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            # 清理连接
            if queue is not None:
                await relay.unregister_client(queue)
    
    return StreamingResponse(
        generate(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',  # 禁用nginx缓冲
        }
    )
