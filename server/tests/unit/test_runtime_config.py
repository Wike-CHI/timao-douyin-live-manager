"""运行时配置测试"""
import pytest
from server.app.core.runtime_config import RuntimeConfig, VoiceSettings, AISettings


def test_voice_settings_defaults():
    """测试语音设置默认值"""
    settings = VoiceSettings()
    assert settings.model == "sensevoice"
    assert settings.language == "auto"
    assert settings.enable_vad is True


def test_voice_settings_custom():
    """测试自定义语音设置"""
    settings = VoiceSettings(model="whisper", language="en")
    assert settings.model == "whisper"
    assert settings.language == "en"


def test_runtime_config_singleton():
    """测试单例模式"""
    config1 = RuntimeConfig()
    config2 = RuntimeConfig()
    assert config1 is config2


def test_runtime_config_update_voice():
    """测试更新语音设置"""
    config = RuntimeConfig()
    new_settings = VoiceSettings(model="whisper", language="en")
    config.update_voice(new_settings)
    assert config.voice.model == "whisper"
    assert config.voice.language == "en"


def test_runtime_config_reset():
    """测试重置配置"""
    config = RuntimeConfig()
    config.update_voice(VoiceSettings(model="funasr"))
    config.reset()
    assert config.voice.model == "sensevoice"
