# -*- coding: utf-8 -*-
"""
AST (Audio Speech Transcription) 主服务
整合音频采集、处理和VOSK语音识别的完整解决方案
"""

import asyncio
import logging
import json
import time
from typing import Optional, Dict, Any, Callable, AsyncGenerator, List
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

# 导入AST模块组件
try:
    from .audio_capture import AudioCapture, AudioProcessor, AudioConfig, AudioBuffer
    from .vosk_service_v2 import VoskServiceV2, VoskConfig
except ImportError:
    # 如果在AST_module目录外运行
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from audio_capture import AudioCapture, AudioProcessor, AudioConfig, AudioBuffer
    from vosk_service_v2 import VoskServiceV2, VoskConfig
    # 如果VOSK不可用，尝试模拟服务
    try:
        VoskServiceV2()
    except:
        from mock_vosk_service import MockVoskService as VoskServiceV2

@dataclass
class TranscriptionResult:
    """转录结果数据结构"""
    text: str
    confidence: float
    timestamp: float
    duration: float
    is_final: bool
    words: Optional[List[Dict[str, Any]]] = None
    room_id: str = ""
    session_id: str = ""
    
    def __post_init__(self):
        if self.words is None:
            self.words = []

@dataclass
class ASTConfig:
    """AST模块配置"""
    # 音频配置
    audio_config: AudioConfig
    
    # VOSK配置
    vosk_model_path: str
    vosk_server_port: int = 2700
    
    # 处理配置
    chunk_duration: float = 1.0  # 音频块持续时间(秒)
    min_confidence: float = 0.5  # 最小置信度阈值
    buffer_duration: float = 10.0  # 音频缓冲区时长
    
    # 输出配置
    save_audio_files: bool = False
    audio_output_dir: str = "./audio_logs"

class ASTService:
    """AST语音转录服务"""
    
    def __init__(self, config: Optional[ASTConfig] = None):
        """
        初始化AST服务
        
        Args:
            config: AST配置，如果为None则使用默认配置
        """
        # 使用默认配置
        if config is None:
            from config import create_ast_config
            config = create_ast_config(
                chunk_duration=1.0,
                min_confidence=0.5,
                save_audio=False
            )
        
        self.config = config
        
        # 日志配置
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.audio_capture = AudioCapture(self.config.audio_config)
        self.audio_processor = AudioProcessor()
        
        # 优先使用真实VOSK直接服务
        try:
            # 检查模型是否存在
            model_path = Path(self.config.vosk_model_path)
            if model_path.exists():
                try:
                    from .vosk_direct_service import VoskDirectService
                except ImportError:
                    from vosk_direct_service import VoskDirectService
                self.vosk_service = VoskDirectService(self.config.vosk_model_path)
                self.logger.info(f"使用真实VOSK直接服务: {model_path}")
            else:
                raise FileNotFoundError(f"模型路径不存在: {model_path}")
        except Exception as e:
            self.logger.warning(f"真实VOSK服务不可用，使用模拟服务: {e}")
            try:
                from .mock_vosk_service import MockVoskService
            except ImportError:
                from mock_vosk_service import MockVoskService
            self.vosk_service = MockVoskService(self.config.vosk_model_path)
        self.audio_buffer = AudioBuffer(
            max_duration=self.config.buffer_duration,
            sample_rate=self.config.audio_config.sample_rate
        )
        
        # 状态管理
        self.is_running = False
        self.current_session_id = None
        self.current_room_id = None
        self.transcription_callbacks = {}
        
        # 统计信息
        self.stats = {
            "total_audio_chunks": 0,
            "successful_transcriptions": 0,
            "failed_transcriptions": 0,
            "average_confidence": 0.0,
            "session_start_time": None
        }
        
        # 创建输出目录
        if self.config.save_audio_files:
            Path(self.config.audio_output_dir).mkdir(parents=True, exist_ok=True)
    
    def _get_default_model_path(self) -> str:
        """获取默认VOSK模型路径"""
        current_dir = Path(__file__).parent.parent
        model_path = current_dir / "vosk-api" / "vosk-model-cn-0.22"
        
        # 如果模型不存在，返回一个默认路径而不抛出异常
        if not model_path.exists():
            logging.warning(f"VOSK中文模型未找到: {model_path}，将使用模拟服务")
            return str(model_path)  # 返回路径，由VOSK服务决定如何处理
        
        return str(model_path)
    
    async def initialize(self) -> bool:
        """
        初始化所有组件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("开始初始化AST服务...")
            
            # 1. 初始化音频系统
            if not self.audio_capture.initialize():
                self.logger.error("音频系统初始化失败")
                return False
            
            # 2. 初始化VOSK服务
            if not await self.vosk_service.initialize():
                self.logger.error("VOSK服务初始化失败")
                return False
            
            self.logger.info("✅ AST服务初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"AST服务初始化失败: {e}")
            return False
    
    async def start_transcription(self, room_id: str, session_id: Optional[str] = None) -> bool:
        """
        开始语音转录
        
        Args:
            room_id: 直播间ID
            session_id: 会话ID，如果为None则自动生成
            
        Returns:
            bool: 启动是否成功
        """
        try:
            if self.is_running:
                self.logger.warning("转录服务已在运行中")
                return False
            
            # 设置会话信息
            self.current_room_id = room_id
            self.current_session_id = session_id or self._generate_session_id()
            
            # 重置统计信息
            self.stats = {
                "total_audio_chunks": 0,
                "successful_transcriptions": 0,
                "failed_transcriptions": 0,
                "average_confidence": 0.0,
                "session_start_time": time.time()
            }
            
            # 开始音频录制
            if not await self.audio_capture.start_recording():
                self.logger.error("音频录制启动失败")
                return False
            
            # 启动转录任务
            self.is_running = True
            asyncio.create_task(self._transcription_loop())
            
            self.logger.info(f"✅ AST转录服务已启动 - 房间:{room_id}, 会话:{self.current_session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"启动转录服务失败: {e}")
            return False
    
    async def stop_transcription(self) -> bool:
        """
        停止语音转录
        
        Returns:
            bool: 停止是否成功
        """
        try:
            if not self.is_running:
                return True
            
            # 停止录制
            self.is_running = False
            await self.audio_capture.stop_recording()
            
            # 清空缓冲区
            await self.audio_buffer.clear()
            
            self.logger.info("✅ AST转录服务已停止")
            
            # 输出统计信息
            duration = time.time() - self.stats["session_start_time"]
            self.logger.info(f"会话统计 - 时长:{duration:.1f}s, 转录次数:{self.stats['successful_transcriptions']}, 平均置信度:{self.stats['average_confidence']:.2f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"停止转录服务失败: {e}")
            return False
    
    async def _transcription_loop(self):
        """转录主循环"""
        try:
            chunk_size = int(self.config.chunk_duration * self.config.audio_config.sample_rate * 2)
            audio_chunks = []
            
            async for audio_chunk in self.audio_capture.get_audio_stream():
                if not self.is_running:
                    break
                
                # 处理音频块
                processed_chunk = self.audio_processor.process_audio_chunk(audio_chunk)
                if not processed_chunk:
                    continue
                
                # 添加到缓冲区
                await self.audio_buffer.append(processed_chunk)
                audio_chunks.append(processed_chunk)
                
                # 累积到指定时长后进行转录
                current_size = sum(len(chunk) for chunk in audio_chunks)
                if current_size >= chunk_size:
                    # 合并音频块
                    combined_audio = b''.join(audio_chunks)
                    
                    # 异步转录
                    asyncio.create_task(self._process_audio_chunk(combined_audio))
                    
                    # 重置块列表
                    audio_chunks = []
                    
                    # 更新统计
                    self.stats["total_audio_chunks"] += 1
                
                # 让出控制权
                await asyncio.sleep(0.01)
                
        except Exception as e:
            self.logger.error(f"转录循环异常: {e}")
            self.is_running = False
    
    async def _process_audio_chunk(self, audio_data: bytes):
        """处理单个音频块"""
        try:
            # 保存音频文件 (调试用)
            if self.config.save_audio_files:
                timestamp = int(time.time() * 1000)
                audio_file = Path(self.config.audio_output_dir) / f"chunk_{timestamp}.wav"
                self.audio_processor.save_audio_to_file(audio_data, str(audio_file))
            
            # VOSK转录
            result = await self.vosk_service.transcribe_audio(audio_data)
            
            if result.get("success") and result.get("text"):
                # 创建转录结果
                transcription = TranscriptionResult(
                    text=result["text"],
                    confidence=result.get("confidence", 0.0),
                    timestamp=time.time(),
                    duration=self.config.chunk_duration,
                    is_final=result.get("type") == "final",
                    words=result.get("words", []),
                    room_id=self.current_room_id or "",
                    session_id=self.current_session_id or ""
                )
                
                # 过滤低置信度结果
                if transcription.confidence >= self.config.min_confidence:
                    # 更新统计
                    self.stats["successful_transcriptions"] += 1
                    self.stats["average_confidence"] = (
                        (self.stats["average_confidence"] * (self.stats["successful_transcriptions"] - 1) + 
                         transcription.confidence) / self.stats["successful_transcriptions"]
                    )
                    
                    # 调用回调函数
                    await self._notify_transcription_callbacks(transcription)
                    
                    self.logger.info(f"🎤 转录: {transcription.text} (置信度: {transcription.confidence:.2f})")
                else:
                    self.logger.debug(f"低置信度转录被过滤: {result['text']} (置信度: {transcription.confidence:.2f})")
            else:
                self.stats["failed_transcriptions"] += 1
                self.logger.debug(f"转录失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            self.logger.error(f"音频块处理失败: {e}")
            self.stats["failed_transcriptions"] += 1
    
    def add_transcription_callback(self, name: str, callback: Callable[[TranscriptionResult], None]):
        """
        添加转录结果回调
        
        Args:
            name: 回调名称
            callback: 回调函数
        """
        self.transcription_callbacks[name] = callback
        self.logger.info(f"已添加转录回调: {name}")
    
    def remove_transcription_callback(self, name: str):
        """移除转录回调"""
        if name in self.transcription_callbacks:
            del self.transcription_callbacks[name]
            self.logger.info(f"已移除转录回调: {name}")
    
    async def _notify_transcription_callbacks(self, transcription: TranscriptionResult):
        """通知所有转录回调"""
        for name, callback in self.transcription_callbacks.items():
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(transcription)
                else:
                    callback(transcription)
            except Exception as e:
                self.logger.error(f"转录回调 {name} 执行失败: {e}")
    
    def _generate_session_id(self) -> str:
        """生成会话ID"""
        return f"ast_session_{int(time.time() * 1000)}"
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "is_running": self.is_running,
            "current_room_id": self.current_room_id,
            "current_session_id": self.current_session_id,
            "stats": self.stats.copy(),
            "vosk_info": self.vosk_service.get_model_info() if self.vosk_service else None,
            "audio_config": asdict(self.config.audio_config),
            "callbacks_count": len(self.transcription_callbacks)
        }
    
    async def get_recent_audio(self, duration: float) -> bytes:
        """获取最近的音频数据"""
        return await self.audio_buffer.get_recent(duration)
    async def cleanup(self):
        """清理所有资源"""
        try:
            # 停止转录
            await self.stop_transcription()
            
            # 清理组件
            self.audio_capture.cleanup()
            if self.vosk_service:
                await self.vosk_service.cleanup()
            
            # 清理回调
            self.transcription_callbacks.clear()
            
            self.logger.info("✅ AST服务已完全清理")
            
        except Exception as e:
            self.logger.error(f"AST服务清理失败: {e}")

# 全局服务实例
ast_service: Optional[ASTService] = None

def get_ast_service() -> ASTService:
    """获取AST服务实例"""
    global ast_service
    if ast_service is None:
        ast_service = ASTService()
    return ast_service

async def cleanup_ast_service():
    """清理AST服务"""
    global ast_service
    if ast_service:
        await ast_service.cleanup()
        ast_service = None

if __name__ == "__main__":
    # 测试代码
    async def test_ast():
        # 初始化服务
        service = ASTService()
        
        # 设置转录回调
        def on_transcription(result: TranscriptionResult):
            print(f"📝 转录结果: {result.text} (置信度: {result.confidence:.2f})")
        
        service.add_transcription_callback("test", on_transcription)
        
        try:
            # 初始化
            if await service.initialize():
                print("✅ AST服务初始化成功")
                
                # 开始转录
                if await service.start_transcription("test_room"):
                    print("✅ 转录已开始，请说话...")
                    
                    # 运行10秒
                    await asyncio.sleep(10)
                    
                    # 停止转录
                    await service.stop_transcription()
                    
                    # 显示状态
                    status = service.get_status()
                    print(f"📊 服务状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
                
            else:
                print("❌ AST服务初始化失败")
                
        finally:
            await service.cleanup()
    
    # 运行测试
    asyncio.run(test_ast())