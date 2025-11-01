# -*- coding: utf-8 -*-
"""
AST_module - Audio Speech Transcription Module
音频语音转录模块

提供完整的语音采集、处理和转录解决方案
"""

__version__ = "1.0.0"
__author__ = "提猫科技AST团队"

# 导入主要类和函数
from .ast_service import ASTService, TranscriptionResult, ASTConfig, get_ast_service, cleanup_ast_service
from .audio_capture import AudioCapture, AudioProcessor, AudioConfig, AudioBuffer

# 导入配置
from .config import DEFAULT_AST_CONFIG, create_ast_config

# 模块级别的便捷函数
__all__ = [
    # 主要服务类
    'ASTService',
    'TranscriptionResult', 
    'ASTConfig',
    
    # 音频处理类
    'AudioCapture',
    'AudioProcessor', 
    'AudioConfig',
    'AudioBuffer',
    
    # 便捷函数
    'get_ast_service',
    'cleanup_ast_service',
    'create_ast_config',
    
    # 配置
    'DEFAULT_AST_CONFIG'
]

def get_version():
    """获取版本信息"""
    return __version__

def get_info():
    """获取模块信息"""
    return {
        "name": "AST_module",
        "version": __version__,
        "description": "Audio Speech Transcription Module - 音频语音转录模块",
        "author": __author__,
        "features": [
            "实时音频采集",
            "音频预处理和格式转换", 
            "SenseVoice本地中文语音识别",
            "流式转录处理",
            "多回调支持",
            "完整的错误处理和日志"
        ],
        "dependencies": [
            "pyaudio",
            "numpy", 
            "aiohttp",
            "funasr (可选)"
        ]
    }