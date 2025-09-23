# -*- coding: utf-8 -*-
"""
语音转录API接口
集成AST_module提供RESTful API和WebSocket接口
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import sys
from pathlib import Path

# 添加项目根目录到sys.path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from AST_module import ASTService, TranscriptionResult, create_ast_config
except ImportError as e:
    logging.error(f"AST模块导入失败: {e}")
    raise

router = APIRouter(prefix="/api/transcription", tags=["transcription"])

# 请求/响应模型
class StartTranscriptionRequest(BaseModel):
    room_id: str
    session_id: Optional[str] = None
    chunk_duration: float = 1.0
    min_confidence: float = 0.6
    save_audio: bool = False
    # 前端不强制暴露专业开关；这里改为可选，仅当提供时才覆盖后端自动策略
    enable_vad: Optional[bool] = None
    vad_model_path: Optional[str] = None
    device_index: Optional[int] = None
    model_id: Optional[str] = None

class TranscriptionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class TranscriptionStatusResponse(BaseModel):
    is_running: bool
    current_room_id: Optional[str]
    current_session_id: Optional[str]
    stats: Dict[str, Any]

# 全局AST服务实例
ast_service: Optional[ASTService] = None

def get_ast_service_instance() -> ASTService:
    """获取AST服务实例"""
    global ast_service
    if ast_service is None:
        # 创建适合生产环境的配置
        config = create_ast_config(
            chunk_duration=1.0,
            min_confidence=0.4,  # 降低阈值以获取更多结果
            save_audio=True,      # 启用音频保存用于调试
            enable_vad=False,
        )
        ast_service = ASTService(config)
        logging.info("🎤 AST服务实例已创建")
    return ast_service

@router.post("/start", response_model=TranscriptionResponse)
async def start_transcription(request: StartTranscriptionRequest):
    """
    开始语音转录
    
    Args:
        request: 转录启动请求
        
    Returns:
        TranscriptionResponse: 启动结果
    """
    try:
        service = get_ast_service_instance()
        
        # 如果服务已在运行，先停止
        if service.is_running:
            await service.stop_transcription()
        
        # 切换模型（如指定）
        if request.model_id:
            try:
                service.set_model_id(request.model_id)
            except Exception:
                pass

        # 更新配置
        service.config.chunk_duration = request.chunk_duration
        service.config.min_confidence = request.min_confidence
        service.config.save_audio_files = request.save_audio
        # VAD 配置（仅当请求显式给出时覆盖自动策略）
        if request.enable_vad is not None:
            service.config.enable_vad = bool(request.enable_vad)
        if request.vad_model_path is not None:
            # 若给了路径则覆盖，否则保留自动探测结果
            service.config.vad_model_id = request.vad_model_path

        # 初始化服务
        if not await service.initialize():
            raise HTTPException(status_code=500, detail="AST服务初始化失败")
        
        # 开始转录
        if await service.start_transcription(request.room_id, request.session_id):
            return TranscriptionResponse(
                success=True,
                message="语音转录已开始",
                data={
                    "room_id": request.room_id,
                    "session_id": service.current_session_id,
                    "config": {
                        "chunk_duration": request.chunk_duration,
                        "min_confidence": request.min_confidence
                    }
                }
            )
        else:
            raise HTTPException(status_code=500, detail="转录启动失败")
            
    except Exception as e:
        logging.error(f"启动转录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class UpdateConfigRequest(BaseModel):
    device_index: Optional[int] = None
    device_name: Optional[str] = None
    preset_mode: Optional[str] = None  # fast | accurate
    silence_gate: Optional[float] = None  # 0.005 ~ 0.03 推荐


@router.get("/devices")
async def list_audio_devices():
    """列出可用麦克风设备（来自 PyAudio）。"""
    try:
        service = get_ast_service_instance()
        # 确保可列举设备
        if service.audio_capture.audio is None:
            service.audio_capture.initialize()
        devices: List[dict] = service.audio_capture.list_audio_devices() or []
        return {"devices": devices}
    except Exception as e:
        logging.error(f"获取音频设备失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def update_config(req: UpdateConfigRequest):
    """更新运行配置：选择输入设备、切换识别模式（快/准）。"""
    try:
        service = get_ast_service_instance()
        # 设备选择：优先按 index，其次按名称模糊匹配
        if req.device_index is not None:
            service.config.audio_config.input_device_index = req.device_index
        elif req.device_name:
            try:
                name = req.device_name.lower()
                if service.audio_capture.audio is None:
                    service.audio_capture.initialize()
                candidates = service.audio_capture.list_audio_devices() or []
                best = None
                score = 0.0
                from difflib import SequenceMatcher
                for d in candidates:
                    s = SequenceMatcher(None, name, str(d.get('name','')).lower()).ratio()
                    if s > score:
                        score, best = s, d
                if best is not None:
                    service.config.audio_config.input_device_index = int(best['index'])
            except Exception:
                pass
        if req.preset_mode:
            mode = (req.preset_mode or '').lower()
            if mode == 'fast':
                service.config.chunk_duration = 0.8
                service.config.min_confidence = 0.5
                service.config.enable_vad = False
            elif mode == 'accurate':
                service.config.chunk_duration = 1.5
                service.config.min_confidence = 0.6
                # 若本地找到 VAD 则启用（config.create_ast_config 已带自动探测），这里只是偏好
                service.config.enable_vad = True
            else:
                raise HTTPException(status_code=400, detail="preset_mode 仅支持 fast/accurate")
        # 静音门限（防幻觉灵敏度）
        if req.silence_gate is not None:
            try:
                # 访问 AST 后处理 guard
                if hasattr(service, 'guard'):
                    service.guard.min_rms = float(req.silence_gate)
            except Exception:
                pass

        return {
            "success": True,
            "config": {
                "chunk_duration": service.config.chunk_duration,
                "min_confidence": service.config.min_confidence,
                "enable_vad": getattr(service.config, 'enable_vad', False),
                "device_index": service.config.audio_config.input_device_index,
                "silence_gate": getattr(getattr(service, 'guard', None), 'min_rms', None),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"更新配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop", response_model=TranscriptionResponse)
async def stop_transcription():
    """
    停止语音转录
    
    Returns:
        TranscriptionResponse: 停止结果
    """
    try:
        service = get_ast_service_instance()
        
        if await service.stop_transcription():
            return TranscriptionResponse(
                success=True,
                message="语音转录已停止"
            )
        else:
            return TranscriptionResponse(
                success=False,
                message="转录服务未在运行"
            )
            
    except Exception as e:
        logging.error(f"停止转录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=TranscriptionStatusResponse)
async def get_transcription_status():
    """
    获取转录状态
    
    Returns:
        TranscriptionStatusResponse: 状态信息
    """
    try:
        service = get_ast_service_instance()
        status = service.get_status()
        
        return TranscriptionStatusResponse(
            is_running=status["is_running"],
            current_room_id=status["current_room_id"],
            current_session_id=status["current_session_id"],
            stats=status["stats"]
        )
        
    except Exception as e:
        logging.error(f"获取转录状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket连接管理
class WebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)

# WebSocket管理器实例
ws_manager = WebSocketManager()

@router.websocket("/ws")
async def transcription_websocket(websocket: WebSocket):
    """
    语音转录WebSocket接口
    提供实时转录结果推送
    """
    await ws_manager.connect(websocket)
    service = get_ast_service_instance()
    
    # 设置转录回调
    callback_name = f"ws_{id(websocket)}"
    
    def transcription_callback(result: TranscriptionResult):
        """转录结果回调"""
        message = {
            "type": "transcription",
            "data": {
                "text": result.text,
                "confidence": result.confidence,
                "timestamp": result.timestamp,
                "is_final": result.is_final,
                "room_id": result.room_id,
                "session_id": result.session_id
            }
        }
        
        # 异步发送消息
        asyncio.create_task(websocket.send_json(message))
    
    service.add_transcription_callback(callback_name, transcription_callback)
    # 后端电平回调
    def level_callback(rms: float, ts: float):
        try:
            asyncio.create_task(websocket.send_json({
                "type": "level",
                "data": {"rms": rms, "timestamp": ts}
            }))
        except Exception:
            pass

    if hasattr(service, 'add_level_callback'):
        service.add_level_callback(callback_name, level_callback)
    
    try:
        while True:
            # 接收客户端消息 (保持连接)
            data = await websocket.receive_json()
            
            # 处理客户端命令
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "get_status":
                status = service.get_status()
                await websocket.send_json({
                    "type": "status",
                    "data": status
                })
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logging.error(f"WebSocket错误: {e}")
    finally:
        # 清理
        service.remove_transcription_callback(callback_name)
        if hasattr(service, 'remove_level_callback'):
            service.remove_level_callback(callback_name)
        ws_manager.disconnect(websocket)

# 启动时初始化
@router.on_event("startup")
async def startup_transcription():
    """应用启动时初始化转录服务"""
    try:
        service = get_ast_service_instance()
        # 预初始化 (不启动转录)
        logging.info("AST转录服务已准备就绪")
    except Exception as e:
        logging.error(f"转录服务初始化失败: {e}")

# 关闭时清理
@router.on_event("shutdown")
async def shutdown_transcription():
    """应用关闭时清理转录服务"""
    try:
        global ast_service
        if ast_service:
            await ast_service.cleanup()
            ast_service = None
        logging.info("AST转录服务已清理")
    except Exception as e:
        logging.error(f"转录服务清理失败: {e}")

# 健康检查
@router.get("/health")
async def transcription_health():
    """转录服务健康检查"""
    try:
        service = get_ast_service_instance()
        status = service.get_status()
        
        return {
            "status": "healthy",
            "ast_service": "available",
            "is_running": status["is_running"],
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
