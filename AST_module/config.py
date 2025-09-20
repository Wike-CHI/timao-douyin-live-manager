# -*- coding: utf-8 -*-
"""
AST模块配置文件
"""

from pathlib import Path
try:
    from .audio_capture import AudioConfig
    from .ast_service import ASTConfig
except ImportError:
    from audio_capture import AudioConfig
    # 暂时延迟导入ASTConfig，避免循环导入
    ASTConfig = None

# 默认模型路径
DEFAULT_MODEL_PATH = str(Path(__file__).parent.parent / "vosk-api" / "vosk-model-cn-0.22")

# 检查模型是否存在
if not Path(DEFAULT_MODEL_PATH).exists():
    import logging
    logging.warning(f"VOSK模型路径不存在: {DEFAULT_MODEL_PATH}，将使用模拟服务")

# 默认音频配置
DEFAULT_AUDIO_CONFIG = AudioConfig(
    sample_rate=16000,      # VOSK推荐采样率
    channels=1,             # 单声道
    chunk_size=1024,        # 音频块大小
    input_device_index=None # 自动选择设备
)

# 默认AST配置
# 延迟创建，避免循环导入
def get_default_ast_config():
    """获取默认AST配置"""
    return create_ast_config()

# 对外接口，保持向后兼容
DEFAULT_AST_CONFIG = None  # 延迟初始化

def create_ast_config(
    model_path: str = None,
    sample_rate: int = 16000,
    chunk_duration: float = 1.0,
    min_confidence: float = 0.5,
    save_audio: bool = False
):
    """
    创建自定义AST配置
    
    Args:
        model_path: VOSK模型路径
        sample_rate: 音频采样率
        chunk_duration: 音频块持续时间
        min_confidence: 最小置信度阈值
        save_audio: 是否保存音频文件
        
    Returns:
        ASTConfig: 配置对象
    """
    # 延迟导入避免循环依赖
    global ASTConfig
    if ASTConfig is None:
        try:
            from .ast_service import ASTConfig
        except ImportError:
            from ast_service import ASTConfig
    
    audio_config = AudioConfig(
        sample_rate=sample_rate,
        channels=1,
        chunk_size=1024,
        input_device_index=None
    )
    
    return ASTConfig(
        audio_config=audio_config,
        vosk_model_path=model_path or DEFAULT_MODEL_PATH,
        vosk_server_port=2700,
        chunk_duration=chunk_duration,
        min_confidence=min_confidence,
        buffer_duration=10.0,
        save_audio_files=save_audio,
        audio_output_dir="./audio_logs"
    )