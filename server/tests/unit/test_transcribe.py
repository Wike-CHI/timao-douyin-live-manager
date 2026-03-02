"""转写器抽象层测试"""
import pytest
from server.services.voice.transcribe import TranscribeResult, get_transcriber


def test_transcribe_result_model():
    """测试结果模型"""
    result = TranscribeResult(
        text="你好世界",
        confidence=0.95,
        language="zh",
        segments=[{"start": 0, "end": 1, "text": "你好世界"}]
    )
    assert result.text == "你好世界"
    assert result.confidence == 0.95
    assert result.language == "zh"


def test_get_transcriber_sensevoice():
    """测试获取 SenseVoice 转写器"""
    transcriber = get_transcriber("sensevoice")
    assert transcriber.__class__.__name__ == "SenseVoiceTranscriber"


def test_get_transcriber_whisper():
    """测试获取 Whisper 转写器"""
    transcriber = get_transcriber("whisper")
    assert transcriber.__class__.__name__ == "WhisperTranscriber"


def test_get_transcriber_funasr():
    """测试获取 FunASR 转写器"""
    transcriber = get_transcriber("funasr")
    assert transcriber.__class__.__name__ == "FunASRTranscriber"


def test_get_transcriber_invalid():
    """测试无效模型抛出异常"""
    with pytest.raises(ValueError):
        get_transcriber("invalid_model")
