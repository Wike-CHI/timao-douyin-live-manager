"""VoiceAgent 测试"""
import pytest
from server.agents.voice.agent import VoiceAgent, VoiceAgentConfig, VoiceAgentResult


def test_voice_agent_config_defaults():
    """测试默认配置"""
    config = VoiceAgentConfig()
    assert config.model == "sensevoice"
    assert config.language == "auto"
    assert config.enable_vad is True
    assert config.sample_rate == 16000


def test_voice_agent_config_custom():
    """测试自定义配置"""
    config = VoiceAgentConfig(model="whisper", language="en", sample_rate=48000)
    assert config.model == "whisper"
    assert config.language == "en"
    assert config.sample_rate == 48000


def test_voice_agent_initialization():
    """测试 Agent 初始化"""
    agent = VoiceAgent()
    assert agent.transcriber is not None
    assert agent.config.model == "sensevoice"


def test_voice_agent_with_config():
    """测试带配置的 Agent 初始化"""
    config = VoiceAgentConfig(model="whisper")
    agent = VoiceAgent(config)
    assert agent.config.model == "whisper"


@pytest.mark.asyncio
async def test_voice_agent_transcribe_empty():
    """测试空文件转写"""
    agent = VoiceAgent()
    result = await agent.transcribe("nonexistent.wav")
    assert result.success is False


@pytest.mark.asyncio
async def test_voice_agent_run_missing_path():
    """测试缺少 audio_path 的请求"""
    agent = VoiceAgent()
    result = await agent.run({})
    assert result.success is False
    assert "audio_path" in result.error


@pytest.mark.asyncio
async def test_voice_agent_health_check():
    """测试健康检查"""
    agent = VoiceAgent()
    healthy = await agent.health_check()
    assert healthy is True


def test_voice_agent_update_model():
    """测试切换模型"""
    agent = VoiceAgent()
    assert agent.config.model == "sensevoice"

    agent.update_model("whisper")
    assert agent.config.model == "whisper"
