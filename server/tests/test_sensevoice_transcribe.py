# -*- coding: utf-8 -*-
"""SenseVoiceService 转录测试"""

import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def initialized_service(mock_model_dir):
    """已初始化的服务"""
    from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

    config = SenseVoiceConfig(model_dir=mock_model_dir)
    service = SenseVoiceService(config)
    await service.initialize()
    yield service
    await service.cleanup()


class TestSenseVoiceServiceTranscribe:
    """转录测试"""

    @pytest.mark.asyncio
    async def test_transcribe_silence(self, initialized_service, test_audio_silence):
        """静音音频返回空结果"""
        result = await initialized_service.transcribe_audio(test_audio_silence)

        assert result["success"] == True
        assert result["type"] == "silence"
        assert result["text"] == ""
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_transcribe_returns_dict(self, initialized_service, test_audio_tone):
        """转录返回正确格式的字典"""
        result = await initialized_service.transcribe_audio(test_audio_tone)

        assert isinstance(result, dict)
        assert "success" in result
        assert "text" in result
        assert "confidence" in result
        assert "timestamp" in result
        assert "words" in result

    @pytest.mark.asyncio
    async def test_transcribe_empty_audio(self, initialized_service):
        """空音频返回静音结果"""
        result = await initialized_service.transcribe_audio(b"")

        assert result["success"] == True
        assert result["type"] == "silence"

    @pytest.mark.asyncio
    async def test_transcribe_before_init(self, mock_model_dir):
        """未初始化时返回错误"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=mock_model_dir)
        service = SenseVoiceService(config)
        # 不初始化
        result = await service.transcribe_audio(b"test")

        assert result["success"] == False

    @pytest.mark.asyncio
    async def test_transcribe_with_session_id(self, initialized_service, test_audio_tone):
        """带 session_id 的转录"""
        result = await initialized_service.transcribe_audio(
            test_audio_tone,
            session_id="test_session_123"
        )

        assert result["success"] == True
