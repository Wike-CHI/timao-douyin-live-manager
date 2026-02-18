# -*- coding: utf-8 -*-
"""SenseVoiceService 热词测试"""

import pytest


class TestSenseVoiceHotwords:
    """热词功能测试"""

    def test_update_global_hotwords(self, mock_model_dir):
        """更新全局热词"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=mock_model_dir)
        service = SenseVoiceService(config)

        service.update_hotwords(None, ["提猫", "直播助手", "AI"])

        assert "提猫" in service._global_hotwords
        assert "直播助手" in service._global_hotwords
        assert "AI" in service._global_hotwords

    def test_update_session_hotwords(self, mock_model_dir):
        """更新会话热词"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=mock_model_dir)
        service = SenseVoiceService(config)

        service.update_hotwords("session_1", ["会话词A", "会话词B"])

        assert "session_1" in service._session_hotwords
        assert "会话词A" in service._session_hotwords["session_1"]
        assert "会话词B" in service._session_hotwords["session_1"]

    def test_update_empty_hotwords(self, mock_model_dir):
        """更新空热词不影响现有热词"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=mock_model_dir)
        service = SenseVoiceService(config)

        service.update_hotwords(None, ["词A"])
        service.update_hotwords(None, [])

        assert "词A" in service._global_hotwords

    def test_compose_hotword_payload(self, mock_model_dir):
        """组装热词字符串"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=mock_model_dir)
        service = SenseVoiceService(config)

        service.update_hotwords(None, ["词A", "词B"])
        payload = service._compose_hotword_payload(None, None)

        assert payload is not None
        assert "词A" in payload
        assert "词B" in payload

    def test_compose_hotword_with_bias_phrases(self, mock_model_dir):
        """组装带 bias_phrases 的热词"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=mock_model_dir)
        service = SenseVoiceService(config)

        service.update_hotwords(None, ["全局词"])
        payload = service._compose_hotword_payload(None, ["临时词"])

        assert "全局词" in payload
        assert "临时词" in payload

    def test_compose_hotword_empty(self, mock_model_dir):
        """无热词时返回 None"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=mock_model_dir)
        service = SenseVoiceService(config)

        payload = service._compose_hotword_payload(None, None)

        assert payload is None
