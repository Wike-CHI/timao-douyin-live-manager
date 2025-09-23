# -*- coding: utf-8 -*-
"""
AST模块配置文件
"""

from pathlib import Path
from typing import Optional
try:
    from .audio_capture import AudioConfig
    from .ast_service import ASTConfig
except ImportError:
    from audio_capture import AudioConfig
    # 暂时延迟导入ASTConfig，避免循环导入
    ASTConfig = None

# 默认 SenseVoice 模型
DEFAULT_MODEL_ID = str(
    Path("models") / "models" / "iic" / "SenseVoiceSmall"
)

# 默认音频配置
DEFAULT_AUDIO_CONFIG = AudioConfig(
    sample_rate=16000,      # SenseVoice 推荐采样率
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

def _autodetect_vad_model(base: Path) -> Optional[str]:
    """自动查找本地 VAD 模型目录。
    约定优先路径：models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch
    若未找到，则在 models 目录下模糊搜索包含 "vad" 的子目录。
    返回可供 FunASR 使用的目录字符串（存在 model.pt 即认为可用）。
    """
    try:
        # 明确约定位置
        prefer = base / 'models' / 'iic' / 'speech_fsmn_vad_zh-cn-16k-common-pytorch'
        if (prefer / 'model.pt').exists() or prefer.exists():
            return str(prefer)
        # 模糊搜索
        for p in (base).rglob('*vad*'):
            if p.is_dir() and (p / 'model.pt').exists():
                return str(p)
    except Exception:
        pass
    return None


def create_ast_config(
    model_path: Optional[str] = None,
    sample_rate: int = 16000,
    chunk_duration: float = 1.0,
    min_confidence: float = 0.5,
    save_audio: bool = False,
    enable_vad: bool = False,
    vad_model_path: Optional[str] = None,
):
    """
    创建自定义AST配置
    
    Args:
        model_path: SenseVoice 模型 ID（ModelScope）
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
    
    # 自动探测本地 VAD（如未显式提供路径）
    autodetected_vad = None
    if vad_model_path is None:
        project_root = Path(__file__).resolve().parents[1] / 'models'
        autodetected_vad = _autodetect_vad_model(project_root)

    return ASTConfig(
        audio_config=audio_config,
        model_id=model_path or DEFAULT_MODEL_ID,
        chunk_duration=chunk_duration,
        min_confidence=min_confidence,
        buffer_duration=10.0,
        save_audio_files=save_audio,
        audio_output_dir="./audio_logs",
        # 只要找到本地 VAD，就自动启用；否则沿用用户入参
        enable_vad=bool(autodetected_vad) or enable_vad,
        vad_model_id=vad_model_path or autodetected_vad,
    )
