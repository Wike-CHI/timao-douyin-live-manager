"""语音转写服务抽象层

支持多种 ASR 引擎:
- SenseVoice (sherpa-onnx) - 推荐，中文效果好
- Whisper - 通用性强
- FunASR - 阿里达摩院
"""
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Literal, AsyncIterator, Optional


class TranscribeResult(BaseModel):
    """转写结果"""
    text: str
    confidence: float = 0.0
    language: str = "auto"
    segments: list[dict] = []
    duration_ms: float = 0.0


class TranscriberBase(ABC):
    """转写器抽象基类"""

    @abstractmethod
    async def transcribe(self, audio_path: str) -> TranscribeResult:
        """转写音频文件"""
        pass

    @abstractmethod
    async def transcribe_stream(
        self, audio_stream
    ) -> AsyncIterator[TranscribeResult]:
        """流式转写"""
        pass


class SenseVoiceTranscriber(TranscriberBase):
    """SenseVoice ONNX 转写器 (推荐)

    使用 sherpa-onnx 进行本地语音识别
    支持: 中文、英文、日文、韩文、粤语
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self._model = None

    def _load_model(self):
        """懒加载模型"""
        if self._model is None:
            try:
                import sherpa_onnx
                # 使用默认模型路径
                if not self.model_path:
                    self.model_path = "models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
                self._model = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                    model=self.model_path,
                    language="auto",
                )
            except ImportError:
                raise RuntimeError("sherpa-onnx not installed. Run: pip install sherpa-onnx")
        return self._model

    async def transcribe(self, audio_path: str) -> TranscribeResult:
        """转写音频文件"""
        import time
        start = time.perf_counter()

        try:
            model = self._load_model()
            stream = model.create_stream()

            # 读取音频
            import soundfile as sf
            samples, sample_rate = sf.read(audio_path)

            # 处理
            stream.accept_waveform(sample_rate, samples)
            model.decode(stream)

            result = stream.result
            duration_ms = (time.perf_counter() - start) * 1000

            return TranscribeResult(
                text=result.text,
                confidence=0.95,  # SenseVoice 不返回置信度，使用默认值
                language="zh",
                segments=[],
                duration_ms=duration_ms
            )
        except Exception as e:
            return TranscribeResult(
                text="",
                confidence=0.0,
                language="auto",
                segments=[],
                duration_ms=(time.perf_counter() - start) * 1000
            )

    async def transcribe_stream(
        self, audio_stream
    ) -> AsyncIterator[TranscribeResult]:
        """流式转写 (TODO: 实现实时流式处理)"""
        yield TranscribeResult(text="", confidence=0.0)


class WhisperTranscriber(TranscriberBase):
    """Whisper ONNX 转写器 (占位)

    使用 openai-whisper 或 faster-whisper
    """

    async def transcribe(self, audio_path: str) -> TranscribeResult:
        raise NotImplementedError("Whisper transcriber not implemented. Use SenseVoice instead.")

    async def transcribe_stream(self, audio_stream) -> AsyncIterator[TranscribeResult]:
        raise NotImplementedError("Whisper transcriber not implemented")
        yield  # make it a generator


class FunASRTranscriber(TranscriberBase):
    """FunASR ONNX 转写器 (占位)

    使用阿里达摩院 FunASR
    """

    async def transcribe(self, audio_path: str) -> TranscribeResult:
        raise NotImplementedError("FunASR transcriber not implemented. Use SenseVoice instead.")

    async def transcribe_stream(self, audio_stream) -> AsyncIterator[TranscribeResult]:
        raise NotImplementedError("FunASR transcriber not implemented")
        yield  # make it a generator


def get_transcriber(
    model: Literal["sensevoice", "whisper", "funasr"] = "sensevoice"
) -> TranscriberBase:
    """工厂函数: 获取转写器实例

    Args:
        model: 转写器类型
            - sensevoice: SenseVoice ONNX (推荐)
            - whisper: Whisper (未实现)
            - funasr: FunASR (未实现)

    Returns:
        转写器实例
    """
    match model:
        case "sensevoice":
            return SenseVoiceTranscriber()
        case "whisper":
            return WhisperTranscriber()
        case "funasr":
            return FunASRTranscriber()
        case _:
            raise ValueError(f"Unknown transcriber model: {model}. "
                            f"Supported: sensevoice, whisper, funasr")
