"""运行时配置管理

支持前端实时修改配置，无需重启服务
"""
from pydantic import BaseModel, ConfigDict
from typing import Literal, Optional


class VoiceSettings(BaseModel):
    """语音设置"""
    model_config = ConfigDict(extra="forbid")

    model: Literal["sensevoice", "whisper", "funasr"] = "sensevoice"
    language: Literal["auto", "zh", "en", "ja", "ko", "yue"] = "auto"
    enable_vad: bool = True
    sample_rate: int = 16000


class AISettings(BaseModel):
    """AI 设置"""
    model_config = ConfigDict(extra="forbid")

    service: Literal["qwen", "openai", "deepseek", "doubao", "chatglm"] = "qwen"
    model: str = "qwen-plus"
    temperature: float = 0.7
    max_tokens: int = 2000


class RuntimeConfig:
    """运行时配置管理器 (单例)

    支持前端实时修改配置
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._voice = VoiceSettings()
            cls._instance._ai = AISettings()
        return cls._instance

    @property
    def voice(self) -> VoiceSettings:
        """获取语音设置"""
        return self._voice

    @property
    def ai(self) -> AISettings:
        """获取 AI 设置"""
        return self._ai

    def update_voice(self, settings: VoiceSettings) -> None:
        """更新语音设置"""
        self._voice = settings

    def update_ai(self, settings: AISettings) -> None:
        """更新 AI 设置"""
        self._ai = settings

    def reset(self) -> None:
        """重置为默认值"""
        self._voice = VoiceSettings()
        self._ai = AISettings()


# 全局实例
runtime_config = RuntimeConfig()
