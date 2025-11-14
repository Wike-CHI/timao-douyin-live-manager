#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SenseVoice + VAD 模型状态查询 API
审查人：叶维哲
"""

import os
import sys
import logging
import psutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# 日志配置
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/model", tags=["模型状态"])


class ModelInfo(BaseModel):
    """模型信息"""
    name: str = Field(..., description="模型名称")
    path: str = Field(..., description="模型路径")
    exists: bool = Field(..., description="文件是否存在")
    size_mb: Optional[float] = Field(None, description="文件大小(MB)")
    env_var: Optional[str] = Field(None, description="环境变量名")
    env_value: Optional[str] = Field(None, description="环境变量值")


class VADConfig(BaseModel):
    """VAD 配置"""
    chunk_sec: Optional[str] = Field(None, description="分块时长")
    min_silence_sec: Optional[str] = Field(None, description="最小静音时长")
    min_speech_sec: Optional[str] = Field(None, description="最小语音时长")
    hangover_sec: Optional[str] = Field(None, description="挂起时间")
    min_rms: Optional[str] = Field(None, description="RMS 阈值")
    music_detect: Optional[str] = Field(None, description="音乐检测")


class PyTorchConfig(BaseModel):
    """PyTorch 配置"""
    omp_threads: Optional[str] = Field(None, description="OpenMP 线程数")
    mkl_threads: Optional[str] = Field(None, description="MKL 线程数")
    cpu_alloc_conf: Optional[str] = Field(None, description="CPU 分配配置")


class SystemResources(BaseModel):
    """系统资源"""
    total_memory_gb: float = Field(..., description="总内存(GB)")
    available_memory_gb: float = Field(..., description="可用内存(GB)")
    memory_percent: float = Field(..., description="内存使用率(%)")
    cpu_percent: float = Field(..., description="CPU 使用率(%)")
    disk_usage_percent: float = Field(..., description="磁盘使用率(%)")
    disk_available_gb: float = Field(..., description="磁盘可用空间(GB)")


class ModelStatusResponse(BaseModel):
    """模型状态响应"""
    status: str = Field(..., description="总体状态: healthy/warning/error")
    timestamp: str = Field(..., description="查询时间")
    
    # 模型信息
    sensevoice: ModelInfo = Field(..., description="SenseVoice 模型信息")
    vad: ModelInfo = Field(..., description="VAD 模型信息")
    
    # 配置信息
    vad_config: VADConfig = Field(..., description="VAD 参数配置")
    pytorch_config: PyTorchConfig = Field(..., description="PyTorch 配置")
    
    # 系统资源
    system: SystemResources = Field(..., description="系统资源")
    
    # 额外信息
    model_cache_dir: Optional[str] = Field(None, description="模型缓存目录")
    enable_preload: Optional[str] = Field(None, description="是否启用预加载")
    
    # 检查结果
    checks: Dict[str, bool] = Field(..., description="各项检查结果")
    warnings: list[str] = Field(default_factory=list, description="警告信息")
    recommendations: list[str] = Field(default_factory=list, description="建议")


def get_file_size_mb(path: Path) -> Optional[float]:
    """获取文件大小（MB）"""
    try:
        if path.exists() and path.is_file():
            return path.stat().st_size / (1024 * 1024)
        elif path.exists() and path.is_dir():
            total = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            return total / (1024 * 1024)
    except Exception as e:
        logger.warning(f"获取文件大小失败: {e}")
    return None


def check_model_path(name: str, env_var: str, default_path: str) -> ModelInfo:
    """检查模型路径"""
    env_value = os.getenv(env_var)
    model_path = Path(env_value) if env_value else Path(default_path)
    
    exists = model_path.exists()
    size_mb = None
    
    if exists:
        # 检查 model.pt 文件
        model_file = model_path / "model.pt" if model_path.is_dir() else model_path
        size_mb = get_file_size_mb(model_file)
        if size_mb is None and model_path.is_dir():
            # 如果没有 model.pt，获取整个目录大小
            size_mb = get_file_size_mb(model_path)
    
    return ModelInfo(
        name=name,
        path=str(model_path),
        exists=exists,
        size_mb=size_mb,
        env_var=env_var,
        env_value=env_value
    )


def get_system_resources() -> SystemResources:
    """获取系统资源信息"""
    try:
        # 内存信息
        memory = psutil.virtual_memory()
        total_mem_gb = memory.total / (1024 ** 3)
        available_mem_gb = memory.available / (1024 ** 3)
        mem_percent = memory.percent
        
        # CPU 信息
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # 磁盘信息
        project_root = Path(__file__).resolve().parents[3]
        disk = psutil.disk_usage(str(project_root))
        disk_usage_percent = disk.percent
        disk_available_gb = disk.free / (1024 ** 3)
        
        return SystemResources(
            total_memory_gb=round(total_mem_gb, 2),
            available_memory_gb=round(available_mem_gb, 2),
            memory_percent=round(mem_percent, 2),
            cpu_percent=round(cpu_percent, 2),
            disk_usage_percent=round(disk_usage_percent, 2),
            disk_available_gb=round(disk_available_gb, 2)
        )
    except Exception as e:
        logger.error(f"获取系统资源失败: {e}")
        # 返回默认值
        return SystemResources(
            total_memory_gb=0.0,
            available_memory_gb=0.0,
            memory_percent=0.0,
            cpu_percent=0.0,
            disk_usage_percent=0.0,
            disk_available_gb=0.0
        )


@router.get("/status", response_model=ModelStatusResponse, summary="查询模型加载状态")
async def get_model_status() -> ModelStatusResponse:
    """
    查询 SenseVoice + VAD 模型的加载状态和配置信息
    
    返回信息包括：
    - 模型文件存在性和大小
    - 环境变量配置
    - VAD 参数配置
    - PyTorch 优化配置
    - 系统资源使用情况
    - 健康检查结果
    """
    
    # 项目根目录
    project_root = Path(__file__).resolve().parents[3]
    
    # 默认路径
    default_sensevoice = project_root / "server/models/models/iic/SenseVoiceSmall"
    default_vad = project_root / "server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
    
    # 检查 SenseVoice 模型
    sensevoice = check_model_path(
        "SenseVoice Small",
        "SENSEVOICE_MODEL_PATH",
        str(default_sensevoice)
    )
    
    # 检查 VAD 模型
    vad = check_model_path(
        "VAD (FSMN)",
        "VAD_MODEL_PATH",
        str(default_vad)
    )
    
    # VAD 配置
    vad_config = VADConfig(
        chunk_sec=os.getenv("LIVE_VAD_CHUNK_SEC"),
        min_silence_sec=os.getenv("LIVE_VAD_MIN_SILENCE_SEC"),
        min_speech_sec=os.getenv("LIVE_VAD_MIN_SPEECH_SEC"),
        hangover_sec=os.getenv("LIVE_VAD_HANGOVER_SEC"),
        min_rms=os.getenv("LIVE_VAD_MIN_RMS"),
        music_detect=os.getenv("LIVE_VAD_MUSIC_DETECT")
    )
    
    # PyTorch 配置
    pytorch_config = PyTorchConfig(
        omp_threads=os.getenv("OMP_NUM_THREADS"),
        mkl_threads=os.getenv("MKL_NUM_THREADS"),
        cpu_alloc_conf=os.getenv("PYTORCH_CPU_ALLOC_CONF")
    )
    
    # 系统资源
    system = get_system_resources()
    
    # 其他配置
    model_cache_dir = os.getenv("MODEL_CACHE_DIR") or os.getenv("MODELSCOPE_CACHE")
    enable_preload = os.getenv("ENABLE_MODEL_PRELOAD")
    
    # 执行检查
    checks = {
        "sensevoice_exists": sensevoice.exists,
        "vad_exists": vad.exists,
        "sensevoice_env_set": sensevoice.env_value is not None,
        "vad_env_set": vad.env_value is not None,
        "vad_config_set": vad_config.chunk_sec is not None,
        "pytorch_config_set": pytorch_config.omp_threads is not None,
        "memory_sufficient": system.available_memory_gb >= 3.0,
        "disk_space_ok": system.disk_usage_percent < 90
    }
    
    # 收集警告
    warnings = []
    recommendations = []
    
    if not sensevoice.exists:
        warnings.append("SenseVoice 模型文件不存在")
        recommendations.append("运行: python server/tools/download_sensevoice.py")
    
    if not vad.exists:
        warnings.append("VAD 模型文件不存在")
        recommendations.append("运行: python server/tools/download_vad_model.py")
    
    if not sensevoice.env_value:
        warnings.append("未设置 SENSEVOICE_MODEL_PATH 环境变量（使用默认路径）")
    
    if not vad.env_value:
        warnings.append("未设置 VAD_MODEL_PATH 环境变量（使用默认路径）")
    
    if not vad_config.chunk_sec:
        warnings.append("未设置 VAD 参数配置")
        recommendations.append("检查 ecosystem.config.js 是否包含 LIVE_VAD_* 环境变量")
    
    if not pytorch_config.omp_threads:
        warnings.append("未设置 PyTorch CPU 优化参数")
        recommendations.append("检查 ecosystem.config.js 是否包含 OMP_NUM_THREADS 等配置")
    
    if system.available_memory_gb < 3.0:
        warnings.append(f"可用内存不足 ({system.available_memory_gb:.2f} GB < 3 GB)")
        recommendations.append("建议释放内存或增加系统内存")
    
    if system.available_memory_gb < 2.5:
        warnings.append("可用内存严重不足，模型可能无法加载")
    
    if system.disk_usage_percent > 90:
        warnings.append(f"磁盘空间紧张 ({system.disk_usage_percent:.1f}% 已使用)")
        recommendations.append("清理磁盘空间")
    
    if sensevoice.exists and sensevoice.size_mb and sensevoice.size_mb < 100:
        warnings.append(f"SenseVoice 模型大小异常 ({sensevoice.size_mb:.1f} MB，预期 ~2300 MB)")
        recommendations.append("模型文件可能不完整，建议重新下载")
    
    if vad.exists and vad.size_mb and vad.size_mb < 10:
        warnings.append(f"VAD 模型大小异常 ({vad.size_mb:.1f} MB，预期 ~140 MB)")
        recommendations.append("模型文件可能不完整，建议重新下载")
    
    # 确定总体状态
    critical_checks = [
        checks["sensevoice_exists"],
        checks["vad_exists"],
        checks["memory_sufficient"]
    ]
    
    if all(critical_checks):
        if len(warnings) == 0:
            status = "healthy"
        elif len(warnings) <= 2:
            status = "warning"
        else:
            status = "warning"
    else:
        status = "error"
    
    return ModelStatusResponse(
        status=status,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        sensevoice=sensevoice,
        vad=vad,
        vad_config=vad_config,
        pytorch_config=pytorch_config,
        system=system,
        model_cache_dir=model_cache_dir,
        enable_preload=enable_preload,
        checks=checks,
        warnings=warnings,
        recommendations=recommendations
    )


@router.get("/health", summary="简单健康检查")
async def model_health_check() -> Dict[str, Any]:
    """
    简单的模型健康检查
    
    返回：
    - healthy: 模型文件都存在且系统资源充足
    - warning: 模型存在但有配置问题
    - error: 模型文件缺失或系统资源不足
    """
    try:
        status = await get_model_status()
        return {
            "status": status.status,
            "timestamp": status.timestamp,
            "checks": status.checks,
            "warnings_count": len(status.warnings),
            "message": "所有检查通过" if status.status == "healthy" else 
                      f"发现 {len(status.warnings)} 个警告" if status.status == "warning" else
                      "发现严重问题，模型可能无法加载"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}", exc_info=True)
        return {
            "status": "error",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"健康检查失败: {str(e)}"
        }


@router.get("/config", summary="获取模型配置")
async def get_model_config() -> Dict[str, Any]:
    """
    获取所有模型相关的环境变量配置
    """
    config = {
        "model_paths": {
            "SENSEVOICE_MODEL_PATH": os.getenv("SENSEVOICE_MODEL_PATH"),
            "VAD_MODEL_PATH": os.getenv("VAD_MODEL_PATH"),
            "MODEL_ROOT": os.getenv("MODEL_ROOT"),
            "MODEL_CACHE_DIR": os.getenv("MODEL_CACHE_DIR"),
            "MODELSCOPE_CACHE": os.getenv("MODELSCOPE_CACHE"),
        },
        "vad_params": {
            "LIVE_VAD_CHUNK_SEC": os.getenv("LIVE_VAD_CHUNK_SEC"),
            "LIVE_VAD_MIN_SILENCE_SEC": os.getenv("LIVE_VAD_MIN_SILENCE_SEC"),
            "LIVE_VAD_MIN_SPEECH_SEC": os.getenv("LIVE_VAD_MIN_SPEECH_SEC"),
            "LIVE_VAD_HANGOVER_SEC": os.getenv("LIVE_VAD_HANGOVER_SEC"),
            "LIVE_VAD_MIN_RMS": os.getenv("LIVE_VAD_MIN_RMS"),
            "LIVE_VAD_MUSIC_DETECT": os.getenv("LIVE_VAD_MUSIC_DETECT"),
        },
        "pytorch_optimization": {
            "OMP_NUM_THREADS": os.getenv("OMP_NUM_THREADS"),
            "MKL_NUM_THREADS": os.getenv("MKL_NUM_THREADS"),
            "PYTORCH_CPU_ALLOC_CONF": os.getenv("PYTORCH_CPU_ALLOC_CONF"),
        },
        "other": {
            "ENABLE_MODEL_PRELOAD": os.getenv("ENABLE_MODEL_PRELOAD"),
            "MODELSCOPE_SDK_DEBUG": os.getenv("MODELSCOPE_SDK_DEBUG"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL"),
            "ENABLE_MODEL_LOG": os.getenv("ENABLE_MODEL_LOG"),
        }
    }
    
    return {
        "status": "success",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "config": config
    }


@router.get("/memory-status")
async def get_memory_status() -> Dict[str, Any]:
    """
    获取内存监控状态
    
    Returns:
        内存监控状态信息
    """
    try:
        from server.app.services.memory_monitor import get_memory_monitor
        memory_monitor = get_memory_monitor()
        
        status = memory_monitor.get_status()
        recent_snapshots = memory_monitor.get_recent_snapshots(count=10)
        
        return {
            "status": "success",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "monitor_status": status,
            "recent_snapshots": recent_snapshots
        }
    except Exception as e:
        logger.error(f"获取内存监控状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取内存监控状态失败: {str(e)}")

