# -*- coding: utf-8 -*-
"""SenseVoiceService 初始化测试"""

import pytest
from pathlib import Path


# 真正的模型目录
REAL_MODEL_DIR = Path(__file__).parents[2] / "models" / "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"


class TestSenseVoiceServiceInit:
    """初始化测试"""

    @pytest.mark.asyncio
    async def test_initialize_missing_model(self, tmp_path):
        """模型不存在时失败"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        nonexistent = tmp_path / "nonexistent"
        config = SenseVoiceConfig(model_dir=str(nonexistent))
        service = SenseVoiceService(config)
        result = await service.initialize()

        assert result == False
        assert service.is_initialized == False

    @pytest.mark.asyncio
    async def test_get_model_info_before_init(self, tmp_path):
        """初始化前获取模型信息"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=str(tmp_path))
        service = SenseVoiceService(config)
        info = service.get_model_info()

        assert "backend" in info
        assert info["backend"] == "sherpa-onnx"
        assert info["initialized"] == False

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_MODEL_DIR.exists(), reason="模型未下载")
    async def test_initialize_success_with_real_model(self):
        """使用真实模型成功初始化"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=str(REAL_MODEL_DIR))
        service = SenseVoiceService(config)
        result = await service.initialize()

        assert result == True
        assert service.is_initialized == True

        info = service.get_model_info()
        assert info["backend"] == "sherpa-onnx"
        assert info["initialized"] == True

        await service.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_MODEL_DIR.exists(), reason="模型未下载")
    async def test_get_model_info_after_init(self):
        """初始化后获取模型信息"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=str(REAL_MODEL_DIR))
        service = SenseVoiceService(config)
        await service.initialize()

        info = service.get_model_info()
        assert "backend" in info
        assert info["backend"] == "sherpa-onnx"
        assert "model_dir" in info
        assert info["initialized"] == True

        await service.cleanup()
