"""语音服务模块"""
from .transcribe import (
    TranscribeResult,
    TranscriberBase,
    SenseVoiceTranscriber,
    WhisperTranscriber,
    FunASRTranscriber,
    get_transcriber,
)

__all__ = [
    "TranscribeResult",
    "TranscriberBase",
    "SenseVoiceTranscriber",
    "WhisperTranscriber",
    "FunASRTranscriber",
    "get_transcriber",
]
