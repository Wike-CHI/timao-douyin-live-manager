# -*- coding: utf-8 -*-
"""SenseVoiceService 转录测试"""

import pytest
from pathlib import Path

# 真正的模型目录
REAL_MODEL_DIR = Path(__file__).parents[2] / "models" / "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"


class TestSenseVoiceServiceTranscribe:
    """转录测试"""

    @pytest.mark.asyncio
    async def test_transcribe_empty_audio_without_init(self, tmp_path):
        """未初始化时空音频返回错误"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=str(tmp_path))
        service = SenseVoiceService(config)
        # 未初始化时，空音频也会返回错误
        result = await service.transcribe_audio(b"")

        assert result["success"] == False
        assert result["type"] == "error"

    @pytest.mark.asyncio
    async def test_transcribe_before_init(self, tmp_path):
        """未初始化时返回错误"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=str(tmp_path))
        service = SenseVoiceService(config)
        # 不初始化
        result = await service.transcribe_audio(b"test")

        assert result["success"] == False

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_MODEL_DIR.exists(), reason="模型未下载")
    async def test_transcribe_silence(self):
        """静音音频返回空结果"""
        import numpy as np
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=str(REAL_MODEL_DIR))
        service = SenseVoiceService(config)
        await service.initialize()

        # 生成静音音频
        silence = np.zeros(16000, dtype=np.int16).tobytes()
        result = await service.transcribe_audio(silence)

        assert result["success"] == True
        assert result["type"] == "silence"
        assert result["text"] == ""
        assert result["confidence"] == 0.0

        await service.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_MODEL_DIR.exists(), reason="模型未下载")
    async def test_transcribe_returns_dict(self):
        """转录返回正确格式的字典"""
        import numpy as np
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=str(REAL_MODEL_DIR))
        service = SenseVoiceService(config)
        await service.initialize()

        # 生成正弦波音频
        t = np.linspace(0, 1.0, 16000)
        wave = np.sin(2 * np.pi * 440 * t)
        audio = (wave * 32767 * 0.5).astype(np.int16).tobytes()

        result = await service.transcribe_audio(audio)

        assert isinstance(result, dict)
        assert "success" in result
        assert "text" in result
        assert "confidence" in result
        assert "timestamp" in result
        assert "words" in result

        await service.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_MODEL_DIR.exists(), reason="模型未下载")
    async def test_transcribe_with_session_id(self):
        """带 session_id 的转录"""
        import numpy as np
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=str(REAL_MODEL_DIR))
        service = SenseVoiceService(config)
        await service.initialize()

        # 生成正弦波音频
        t = np.linspace(0, 1.0, 16000)
        wave = np.sin(2 * np.pi * 440 * t)
        audio = (wave * 32767 * 0.5).astype(np.int16).tobytes()

        result = await service.transcribe_audio(
            audio,
            session_id="test_session_123"
        )

        assert result["success"] == True

        await service.cleanup()
