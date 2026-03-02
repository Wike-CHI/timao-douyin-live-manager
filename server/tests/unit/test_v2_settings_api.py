"""V2 Settings API 测试"""
import pytest

from server.app.core.runtime_config import runtime_config, VoiceSettings, AISettings


@pytest.fixture(autouse=True)
def reset_config():
    """每个测试前重置配置"""
    runtime_config.reset()
    yield
    runtime_config.reset()


class TestVoiceSettingsAPI:
    """语音设置 API 测试"""

    def test_get_voice_settings(self, client):
        """测试获取语音设置"""
        response = client.get("/api/v2/settings/voice")
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "sensevoice"
        assert data["language"] == "auto"
        assert data["enable_vad"] is True
        assert data["sample_rate"] == 16000

    def test_update_voice_model(self, client):
        """测试更新语音模型"""
        response = client.put("/api/v2/settings/voice", json={"model": "whisper"})
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "whisper"
        assert data["language"] == "auto"  # 其他字段保持不变

    def test_update_voice_language(self, client):
        """测试更新语音语言"""
        response = client.put("/api/v2/settings/voice", json={"language": "en"})
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"

    def test_update_multiple_voice_settings(self, client):
        """测试同时更新多个语音设置"""
        response = client.put(
            "/api/v2/settings/voice",
            json={"model": "funasr", "language": "ja", "enable_vad": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "funasr"
        assert data["language"] == "ja"
        assert data["enable_vad"] is False

    def test_reset_voice_settings(self, client):
        """测试重置语音设置"""
        # 先修改设置
        client.put("/api/v2/settings/voice", json={"model": "whisper", "language": "en"})

        # 重置
        response = client.post("/api/v2/settings/voice/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "sensevoice"
        assert data["language"] == "auto"

    def test_invalid_voice_model(self, client):
        """测试无效的语音模型"""
        response = client.put("/api/v2/settings/voice", json={"model": "invalid"})
        assert response.status_code == 422  # Validation error


class TestAISettingsAPI:
    """AI 设置 API 测试"""

    def test_get_ai_settings(self, client):
        """测试获取 AI 设置"""
        response = client.get("/api/v2/settings/ai")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "qwen"
        assert data["model"] == "qwen-plus"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 2000

    def test_update_ai_service(self, client):
        """测试更新 AI 服务"""
        response = client.put("/api/v2/settings/ai", json={"service": "openai"})
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "openai"

    def test_update_ai_model(self, client):
        """测试更新 AI 模型"""
        response = client.put("/api/v2/settings/ai", json={"model": "gpt-4"})
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "gpt-4"

    def test_update_ai_temperature(self, client):
        """测试更新 AI 温度"""
        response = client.put("/api/v2/settings/ai", json={"temperature": 0.5})
        assert response.status_code == 200
        data = response.json()
        assert data["temperature"] == 0.5

    def test_reset_ai_settings(self, client):
        """测试重置 AI 设置"""
        # 先修改设置
        client.put("/api/v2/settings/ai", json={"service": "deepseek", "temperature": 0.3})

        # 重置
        response = client.post("/api/v2/settings/ai/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "qwen"
        assert data["temperature"] == 0.7


class TestCombinedSettingsAPI:
    """组合设置 API 测试"""

    def test_get_all_settings(self, client):
        """测试获取所有设置"""
        response = client.get("/api/v2/settings/all")
        assert response.status_code == 200
        data = response.json()
        assert "voice" in data
        assert "ai" in data
        assert data["voice"]["model"] == "sensevoice"
        assert data["ai"]["service"] == "qwen"

    def test_reset_all_settings(self, client):
        """测试重置所有设置"""
        # 修改设置
        client.put("/api/v2/settings/voice", json={"model": "whisper"})
        client.put("/api/v2/settings/ai", json={"service": "openai"})

        # 重置所有
        response = client.post("/api/v2/settings/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["voice"]["model"] == "sensevoice"
        assert data["ai"]["service"] == "qwen"
