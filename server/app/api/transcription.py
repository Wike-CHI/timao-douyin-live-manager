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
    # 仅当前端显式提供时才覆盖后端预设，默认 None 保持当前/预设配置
    chunk_duration: Optional[float] = None
    min_confidence: Optional[float] = None
    save_audio: bool = False
    # 前端不强制暴露专业开关；这里改为可选，仅当提供时才覆盖后端自动策略
    enable_vad: Optional[bool] = None
    vad_model_path: Optional[str] = None
    device_index: Optional[int] = None

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
        # 默认使用主播 FAST 预设（无需额外调用 /config）
        config = create_ast_config(
            chunk_duration=0.4,
            min_confidence=0.55,
            save_audio=False,
            enable_vad=True,
        )
        ast_service = ASTService(config)
        # 同步后处理器为 FAST 预设
        try:
            if hasattr(ast_service, 'assembler'):
                ast_service.assembler.max_wait = 2.0
                ast_service.assembler.max_chars = 36
                ast_service.assembler.silence_flush = 1
            if hasattr(ast_service, 'guard'):
                ast_service.guard.min_rms = 0.020
                ast_service.guard.low_conf = 0.50
                ast_service.guard.min_len = 2
        except Exception:
            pass
        logging.info("🎤 AST服务实例已创建（默认主播 FAST 预设）")
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
        
        # 更新配置（仅在显式提供时覆盖预设）
        if request.chunk_duration is not None:
            service.config.chunk_duration = float(request.chunk_duration)
        if request.min_confidence is not None:
            service.config.min_confidence = float(request.min_confidence)
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
    preset_mode: Optional[str] = None  # fast | accurate（主播预设）
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
                # 主播-快速滚动（更接近逐字），低延迟
                service.config.chunk_duration = 0.4
                service.config.min_confidence = 0.55
                service.config.enable_vad = True  # 更稳切分
                # 分句/门限：更积极地出句
                try:
                    if hasattr(service, 'assembler'):
                        service.assembler.max_wait = 2.0
                        service.assembler.max_chars = 36
                        service.assembler.silence_flush = 1
                    if hasattr(service, 'guard'):
                        service.guard.min_rms = 0.020
                        service.guard.low_conf = 0.50
                        service.guard.min_len = 2
                except Exception:
                    pass
            elif mode == 'accurate':
                # 主播-稳重（更高准确与断句自然）
                service.config.chunk_duration = 1.2
                service.config.min_confidence = 0.60
                service.config.enable_vad = True
                try:
                    if hasattr(service, 'assembler'):
                        service.assembler.max_wait = 2.5
                        service.assembler.max_chars = 48
                        service.assembler.silence_flush = 2
                    if hasattr(service, 'guard'):
                        service.guard.min_rms = 0.018
                        service.guard.low_conf = 0.50
                        service.guard.min_len = 2
                except Exception:
                    pass
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
    
    # 设置转录回调（带增量拼接协议）
    callback_name = f"ws_{id(websocket)}"
    # 用于增量拼接：保存当前缓冲文本（仅限该连接会话）
    delta_buffer = {"text": ""}

    def transcription_callback(result: TranscriptionResult):
        """转录结果回调：同时发送全文与增量两种消息，保证向后兼容。
        - transcription: 兼容旧客户端（全文）
        - transcription_delta: 新协议（append/replace/final）
        """
        try:
            # 1) 新协议：增量消息
            prev = delta_buffer.get("text", "")
            curr = result.text or ""
            if result.is_final:
                # 最终落句：告知前端最终文本
                delta_msg = {
                    "type": "transcription_delta",
                    "data": {
                        "op": "final",
                        "text": curr,
                        "timestamp": result.timestamp,
                        "confidence": result.confidence,
                    },
                }
                delta_buffer["text"] = ""
                asyncio.create_task(websocket.send_json(delta_msg))
            else:
                if curr.startswith(prev):
                    add = curr[len(prev) :]
                    if add:
                        delta_msg = {
                            "type": "transcription_delta",
                            "data": {
                                "op": "append",
                                "text": add,
                                "timestamp": result.timestamp,
                                "confidence": result.confidence,
                            },
                        }
                        asyncio.create_task(websocket.send_json(delta_msg))
                else:
                    # 无法做纯追加，回退为替换
                    delta_msg = {
                        "type": "transcription_delta",
                        "data": {
                            "op": "replace",
                            "text": curr,
                            "timestamp": result.timestamp,
                            "confidence": result.confidence,
                        },
                    }
                    asyncio.create_task(websocket.send_json(delta_msg))
                # 更新缓冲
                delta_buffer["text"] = curr

            # 2) 向后兼容：全文消息
            full_msg = {
                "type": "transcription",
                "data": {
                    "text": result.text,
                    "confidence": result.confidence,
                    "timestamp": result.timestamp,
                    "is_final": result.is_final,
                    "room_id": result.room_id,
                    "session_id": result.session_id,
                    "words": result.words or [],
                },
            }
            asyncio.create_task(websocket.send_json(full_msg))
        except Exception as e:
            logging.error(f"发送转录消息失败: {e}")
    
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
