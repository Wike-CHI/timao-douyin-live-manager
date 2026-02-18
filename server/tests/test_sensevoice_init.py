# -*- coding: utf-8 -*-
"""SenseVoiceService 初始化测试"""

import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def service_with_mock_model(mock_model_dir):
    """使用模拟模型的服务"""
    from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

    config = SenseVoiceConfig(model_dir=mock_model_dir)
    service = SenseVoiceService(config)
    yield service
    await service.cleanup()


class TestSenseVoiceServiceInit:
    """初始化测试"""

    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_model_dir):
        """成功初始化"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=mock_model_dir)
        service = SenseVoiceService(config)
        result = await service.initialize()

        assert result == True
        assert service.is_initialized == True

        await service.cleanup()

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
    async def test_get_model_info(self, service_with_mock_model):
        """获取模型信息"""
        await service_with_mock_model.initialize()
        info = service_with_mock_model.get_model_info()

        assert "backend" in info
        assert info["backend"] == "sherpa-onnx"
        assert "model_dir" in info
        assert "initialized" in info
