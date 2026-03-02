"""语音转写 Agent

使用可配置的 ASR 引擎进行语音转写
"""
from pydantic import BaseModel
from typing import Literal, AsyncIterator, Optional
from server.services.voice.transcribe import (
    get_transcriber,
    TranscriberBase,
    TranscribeResult,
)
from server.agents.base import BaseAgent, AgentResult


class VoiceAgentConfig(BaseModel):
    """语音 Agent 配置"""
    model: Literal["sensevoice", "whisper", "funasr"] = "sensevoice"
    language: Literal["auto", "zh", "en", "ja", "ko", "yue"] = "auto"
    enable_vad: bool = True
    sample_rate: int = 16000
    model_path: Optional[str] = None


class VoiceAgentResult(AgentResult):
    """语音 Agent 结果"""
    text: str = ""
    confidence: float = 0.0
    language: str = "auto"
    segments: list[dict] = []


class VoiceAgent(BaseAgent[VoiceAgentResult]):
    """语音转写 Agent

    支持多种 ASR 引擎:
    - SenseVoice (sherpa-onnx) - 推荐，中文效果好
    - Whisper - 通用性强
    - FunASR - 阿里达摩院

    Example:
        agent = VoiceAgent(VoiceAgentConfig(model="sensevoice"))
        result = await agent.transcribe("audio.wav")
        print(result.text)
    """

    def __init__(self, config: Optional[VoiceAgentConfig] = None):
        super().__init__(name="voice")
        self.config = config or VoiceAgentConfig()
        self.transcriber: TranscriberBase = get_transcriber(self.config.model)

    async def run(self, input_data: dict) -> VoiceAgentResult:
        """执行转写

        Args:
            input_data: {
                "audio_path": "path/to/audio.wav",
                "language": "auto"  # optional override
            }

        Returns:
            VoiceAgentResult
        """
        audio_path = input_data.get("audio_path")
        if not audio_path:
            return VoiceAgentResult(
                success=False,
                error="audio_path required"
            )

        return await self.transcribe(audio_path)

    async def transcribe(self, audio_path: str) -> VoiceAgentResult:
        """转写音频文件

        Args:
            audio_path: 音频文件路径

        Returns:
            VoiceAgentResult with transcription
        """
        try:
            result: TranscribeResult = await self.transcriber.transcribe(audio_path)
            return VoiceAgentResult(
                success=True,
                text=result.text,
                confidence=result.confidence,
                language=result.language,
                segments=result.segments,
                duration_ms=result.duration_ms
            )
        except NotImplementedError as e:
            return VoiceAgentResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            return VoiceAgentResult(
                success=False,
                error=f"Transcription failed: {str(e)}"
            )

    async def transcribe_stream(
        self, stream_url: str
    ) -> AsyncIterator[VoiceAgentResult]:
        """流式转写

        Args:
            stream_url: 流地址 (RTMP/HLS/etc.)

        Yields:
            VoiceAgentResult for each segment
        """
        # TODO: 实现流式处理
        # 1. 使用 FFmpeg 拉取音频流
        # 2. 分段送入 ASR 引擎
        # 3. 实时返回结果
        yield VoiceAgentResult(
            success=False,
            error="Stream transcription not implemented yet"
        )

    async def health_check(self) -> bool:
        """健康检查"""
        return self.transcriber is not None

    def update_model(self, model: Literal["sensevoice", "whisper", "funasr"]) -> None:
        """切换 ASR 模型

        Args:
            model: 新的模型类型
        """
        self.config.model = model
        self.transcriber = get_transcriber(model)
