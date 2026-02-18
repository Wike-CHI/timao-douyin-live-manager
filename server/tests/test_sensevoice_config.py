# -*- coding: utf-8 -*-
"""SenseVoiceConfig 配置测试"""

import pytest


class TestSenseVoiceConfig:
    """配置类测试"""

    def test_default_config_values(self):
        """默认配置应有正确的值"""
        # 先导入会失败，这是 RED 阶段
        from server.modules.ast.sensevoice_service import SenseVoiceConfig

        config = SenseVoiceConfig()

        assert config.model_dir == "models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
        assert config.language == "auto"
        assert config.use_itn == True
        assert config.hotword_weight == 3.0
        assert config.max_concurrent == 4
        assert config.timeout_seconds == 10.0
        assert config.device == "cpu"

    def test_custom_model_path(self):
        """自定义模型路径"""
        from server.modules.ast.sensevoice_service import SenseVoiceConfig

        config = SenseVoiceConfig(model_dir="/custom/path/to/model")
        assert config.model_dir == "/custom/path/to/model"

    def test_custom_language(self):
        """自定义语言"""
        from server.modules.ast.sensevoice_service import SenseVoiceConfig

        config = SenseVoiceConfig(language="zh")
        assert config.language == "zh"
