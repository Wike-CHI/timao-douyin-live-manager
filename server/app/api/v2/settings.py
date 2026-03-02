# -*- coding: utf-8 -*-
"""设置 API - V2

支持前端实时配置语音和 AI 设置
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal

from server.app.core.runtime_config import runtime_config, VoiceSettings, AISettings

router = APIRouter(prefix="/api/v2/settings", tags=["Settings"])


# Request Models
class VoiceSettingsUpdate(BaseModel):
    """语音设置更新请求"""
    model: Literal["sensevoice", "whisper", "funasr"] | None = None
    language: Literal["auto", "zh", "en", "ja", "ko", "yue"] | None = None
    enable_vad: bool | None = None
    sample_rate: int | None = None


class AISettingsUpdate(BaseModel):
    """AI 设置更新请求"""
    service: Literal["qwen", "openai", "deepseek", "doubao", "chatglm"] | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


# Voice Settings Endpoints
@router.get("/voice", response_model=VoiceSettings)
async def get_voice_settings():
    """获取当前语音设置"""
    return runtime_config.voice


@router.put("/voice", response_model=VoiceSettings)
async def update_voice_settings(update: VoiceSettingsUpdate):
    """更新语音设置

    支持部分更新，只更新提供的字段
    """
    current = runtime_config.voice.model_dump()

    # 只更新提供的字段
    if update.model is not None:
        current["model"] = update.model
    if update.language is not None:
        current["language"] = update.language
    if update.enable_vad is not None:
        current["enable_vad"] = update.enable_vad
    if update.sample_rate is not None:
        current["sample_rate"] = update.sample_rate

    new_settings = VoiceSettings(**current)
    runtime_config.update_voice(new_settings)

    return new_settings


@router.post("/voice/reset", response_model=VoiceSettings)
async def reset_voice_settings():
    """重置语音设置为默认值"""
    runtime_config._voice = VoiceSettings()
    return runtime_config.voice


# AI Settings Endpoints
@router.get("/ai", response_model=AISettings)
async def get_ai_settings():
    """获取当前 AI 设置"""
    return runtime_config.ai


@router.put("/ai", response_model=AISettings)
async def update_ai_settings(update: AISettingsUpdate):
    """更新 AI 设置

    支持部分更新，只更新提供的字段
    """
    current = runtime_config.ai.model_dump()

    # 只更新提供的字段
    if update.service is not None:
        current["service"] = update.service
    if update.model is not None:
        current["model"] = update.model
    if update.temperature is not None:
        current["temperature"] = update.temperature
    if update.max_tokens is not None:
        current["max_tokens"] = update.max_tokens

    new_settings = AISettings(**current)
    runtime_config.update_ai(new_settings)

    return new_settings


@router.post("/ai/reset", response_model=AISettings)
async def reset_ai_settings():
    """重置 AI 设置为默认值"""
    runtime_config._ai = AISettings()
    return runtime_config.ai


# Combined Settings Endpoint
@router.get("/all")
async def get_all_settings():
    """获取所有设置"""
    return {
        "voice": runtime_config.voice.model_dump(),
        "ai": runtime_config.ai.model_dump()
    }


@router.post("/reset")
async def reset_all_settings():
    """重置所有设置为默认值"""
    runtime_config.reset()
    return {
        "voice": runtime_config.voice.model_dump(),
        "ai": runtime_config.ai.model_dump()
    }
