# -*- coding: utf-8 -*-
"""AST (Audio Speech Transcription) 主服务.

整合音频采集、处理与 SenseVoice 语音识别的完整解决方案。
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
except ImportError:
    # 如果在AST_module目录外运行
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from audio_capture import AudioCapture, AudioProcessor, AudioConfig, AudioBuffer

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
    model_id: str = "iic/SenseVoiceSmall"
    # 语音活动检测（VAD）配置
    enable_vad: bool = False
    vad_model_id: Optional[str] = None
    punc_model_id: Optional[str] = None
    
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
            try:
                from .config import create_ast_config
            except ImportError:
                # 如果在AST_module目录外运行
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
        # 让处理器了解真实输入格式，避免重复/错误重采样
        self.audio_processor = AudioProcessor(
            target_sample_rate=self.config.audio_config.sample_rate,
            source_sample_rate=self.config.audio_config.sample_rate,
            source_channels=self.config.audio_config.channels,
        )
        
        try:
            from .sensevoice_service import SenseVoiceService, SenseVoiceConfig
        except ImportError:  # pragma: no cover - 兼容直接运行
            from sensevoice_service import SenseVoiceService, SenseVoiceConfig
        # Optional sherpa backend
        try:
            from .sherpa_service import SherpaOnnxService, SherpaConfig
        except ImportError:
            SherpaOnnxService = None  # type: ignore
            SherpaConfig = None  # type: ignore
        try:
            from .postprocess import ChineseCleaner, HallucinationGuard, SentenceAssembler, pcm16_rms
        except ImportError:
            from postprocess import ChineseCleaner, HallucinationGuard, SentenceAssembler, pcm16_rms

        self.recognizer = None
        self.mock_transcriber = None
        self._build_recognizer()
        self.audio_buffer = AudioBuffer(
            max_duration=self.config.buffer_duration,
            sample_rate=self.config.audio_config.sample_rate
        )
        # 后处理组件
        self.cleaner = ChineseCleaner()
        self.guard = HallucinationGuard()
        self.assembler = SentenceAssembler()
        
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

    def _build_recognizer(self):
        """Create recognizer based on current model_id.
        - If model looks like a sherpa-onnx repo (contains 'sherpa-onnx' or 'xiaowangge/'),
          use SherpaOnnxService; else default to SenseVoiceService.
        """
        model_id = self.config.model_id or ""
        use_sherpa = ("sherpa-onnx" in model_id) or ("xiaowangge/" in model_id)
        if use_sherpa:
            try:
                from .sherpa_service import SherpaOnnxService, SherpaConfig
                self.recognizer = SherpaOnnxService(SherpaConfig(model_id=model_id))
                self.logger.info("使用 Sherpa-ONNX 模型: %s", model_id)
                return
            except Exception as e:
                self.logger.error("构建 Sherpa-ONNX 失败，将回退 SenseVoice: %s", e)
        # Default SenseVoice
        try:
            from .sensevoice_service import SenseVoiceService, SenseVoiceConfig
            svc_config = SenseVoiceConfig(
                model_id=self.config.model_id,
                vad_model_id=(self.config.vad_model_id if self.config.enable_vad else None),
                punc_model_id=self.config.punc_model_id,
            )
            self.recognizer = SenseVoiceService(svc_config)
            self.logger.info("使用 SenseVoice 服务进行语音识别: %s", self.config.model_id)
        except Exception as exc:
            self.logger.error("SenseVoice 服务初始化失败: %s", exc)
            self.recognizer = None

    def set_model_id(self, model_id: str):
        """Switch ASR backend/model at runtime.
        Will cleanup current recognizer and create a new one; initialize() should be called later.
        """
        try:
            if self.recognizer and hasattr(self.recognizer, 'cleanup'):
                asyncio.create_task(self.recognizer.cleanup())
        except Exception:
            pass
        self.config.model_id = model_id
        self._build_recognizer()
    
    def _create_basic_mock_service(self):
        """创建基础模拟服务"""
        class BasicMockService:
            def __init__(self):
                self.is_initialized = False
            
            async def initialize(self):
                self.is_initialized = True
                return True
            
            async def transcribe_audio(self, audio_data: bytes):
                return {
                    "success": True,
                    "type": "final",
                    "text": "模拟转录结果",
                    "confidence": 0.9,
                    "words": [],
                    "timestamp": time.time()
                }
            
            async def cleanup(self):
                pass
            
            def get_model_info(self):
                return {
                    "model_id": "mock",
                    "sample_rate": 16000,
                    "is_initialized": self.is_initialized,
                    "model_type": "mock-service",
                    "deployment_mode": "mock",
                }

        return BasicMockService()

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
            
            # 2. 初始化 SenseVoice 服务
            if self.recognizer:
                try:
                    # 同步最新 VAD 配置给识别器
                    if hasattr(self.recognizer, 'config'):
                        try:
                            desired_vad = (
                                self.config.vad_model_id if self.config.enable_vad else None
                            )
                            current_vad = getattr(self.recognizer.config, 'vad_model_id', None)
                            # 若已初始化且 VAD 配置发生变化，先卸载以便重新加载
                            if getattr(self.recognizer, 'is_initialized', False) and desired_vad != current_vad:
                                await self.recognizer.cleanup()
                                self.recognizer.is_initialized = False
                            self.recognizer.config.vad_model_id = desired_vad
                        except Exception:
                            pass
                    ok = await self.recognizer.initialize()
                    if not ok:
                        self.logger.error("SenseVoice 服务初始化失败")
                        self.recognizer = None
                except Exception as exc:
                    self.logger.error(f"SenseVoice 初始化异常: {exc}")
                    self.recognizer = None

            if not self.recognizer:
                self.logger.error("SenseVoice 未正确初始化，请检查依赖或麦克风")
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

            duration = time.time() - self.stats["session_start_time"]
            self.logger.info(
                "会话统计 - 时长:%s, 转录次数:%s, 平均置信度:%.2f",
                f"{duration:.1f}s",
                self.stats["successful_transcriptions"],
                self.stats["average_confidence"],
            )
            
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
                # 计算并广播后端电平
                try:
                    from .postprocess import pcm16_rms
                    rms_val = pcm16_rms(processed_chunk)
                    ts = time.time()
                    for cb in list(self.level_callbacks.values()):
                        try:
                            cb(rms_val, ts)
                        except Exception:
                            pass
                except Exception:
                    pass
                
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
            
            if not self.recognizer:
                return
            result = await self.recognizer.transcribe_audio(audio_data)
            
            # 语音能量（用于防幻觉判定）
            from .postprocess import pcm16_rms  # local import for clarity
            rms = pcm16_rms(audio_data)

            text_raw = result.get("text", "") if isinstance(result, dict) else ""
            ok = bool(result.get("success")) and bool(text_raw)
            if ok:
                clean = self.cleaner.clean(text_raw)
                # 防幻觉过滤
                if self.guard.should_drop(clean, float(result.get("confidence", 0.0)), rms):
                    self.logger.debug("文本被防幻觉过滤: %s (rms=%.4f)", clean, rms)
                    return
                # 智能分句
                is_final, maybe = self.assembler.feed(clean)
                emit_text = maybe if is_final else clean
                transcription = TranscriptionResult(
                    text=emit_text,
                    confidence=result.get("confidence", 0.0),
                    timestamp=time.time(),
                    duration=self.config.chunk_duration,
                    is_final=is_final,
                    words=result.get("words", []),
                    room_id=self.current_room_id or "",
                    session_id=self.current_session_id or ""
                )
                
                # 过滤低置信度结果
                if transcription.confidence >= self.config.min_confidence or is_final:
                    # 更新统计
                    self.stats["successful_transcriptions"] += 1
                    self.stats["average_confidence"] = (
                        (self.stats["average_confidence"] * (self.stats["successful_transcriptions"] - 1) + 
                         transcription.confidence) / self.stats["successful_transcriptions"]
                    )
                    # 调用回调函数
                    await self._notify_transcription_callbacks(transcription)
                    self.logger.info(
                        "🎤 转录: %s (置信度: %.2f%s)",
                        transcription.text,
                        transcription.confidence,
                        " · FINAL" if is_final else "",
                    )
                else:
                    self.logger.debug(
                        "低置信度转录被过滤: %s (置信度: %.2f)",
                        transcription.text,
                        transcription.confidence,
                    )
            else:
                self.stats["failed_transcriptions"] += 1
                # 静音累积可能需要强制出句
                final_by_silence = self.assembler.mark_silence()
                if final_by_silence:
                    tr = TranscriptionResult(
                        text=final_by_silence,
                        confidence=0.7,
                        timestamp=time.time(),
                        duration=self.config.chunk_duration,
                        is_final=True,
                        words=[],
                        room_id=self.current_room_id or "",
                        session_id=self.current_session_id or "",
                    )
                    await self._notify_transcription_callbacks(tr)
                    self.logger.info("🎤 转录(静音切句): %s", tr.text)
                else:
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
            "recognizer_info": self.recognizer.get_model_info()
            if hasattr(self.recognizer, "get_model_info")
            else None,
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
            if self.recognizer and hasattr(self.recognizer, "cleanup"):
                await self.recognizer.cleanup()
            
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
