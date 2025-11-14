#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的 Python 转写服务
用于 Electron 本地语音识别

启动后监听 localhost:9527，提供 HTTP API 接收音频数据并返回转写结果
"""

import os
import sys
import json
import logging
import time
from typing import Optional, Dict, Any
from pathlib import Path

import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS

# 设置环境变量，避免 UMAP/numba 在 Python 3.11 的问题
os.environ.setdefault("UMAP_DONT_USE_NUMBA", "1")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 尝试导入 FunASR
try:
    from funasr import AutoModel
    FUNASR_AVAILABLE = True
    logger.info("✅ FunASR 导入成功")
except ImportError as e:
    FUNASR_AVAILABLE = False
    logger.error(f"❌ FunASR 导入失败: {e}")
    logger.error("请安装依赖: pip install funasr modelscope")

# Flask 应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局变量
model: Optional[Any] = None
vad_model: Optional[Any] = None
is_initialized = False


def init_model():
    """初始化 SenseVoice 和 VAD 模型"""
    global model, vad_model, is_initialized
    
    if not FUNASR_AVAILABLE:
        logger.error("FunASR 不可用，无法初始化模型")
        return False
    
    try:
        logger.info("开始初始化 SenseVoice Small 模型...")
        
        # 初始化 SenseVoice Small 模型
        model = AutoModel(
            model="iic/SenseVoiceSmall",
            vad_model="fsmn-vad",
            vad_kwargs={"max_single_segment_time": 30000},
            disable_update=True,
            device="cpu",  # Electron 本地使用 CPU
        )
        
        logger.info("✅ SenseVoice Small 模型初始化成功")
        is_initialized = True
        return True
        
    except Exception as e:
        logger.error(f"❌ 模型初始化失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "ok" if is_initialized else "initializing",
        "model_loaded": is_initialized,
        "funasr_available": FUNASR_AVAILABLE,
        "timestamp": time.time()
    })


@app.route('/transcribe', methods=['POST'])
def transcribe():
    """
    转写音频数据
    
    接收: PCM 16bit 16kHz mono 音频数据（application/octet-stream）
    返回: JSON 格式的转写结果
    """
    if not is_initialized:
        return jsonify({
            "error": "Model not initialized",
            "text": "",
            "confidence": 0.0
        }), 503
    
    try:
        # 获取音频数据
        audio_bytes = request.data
        if not audio_bytes:
            return jsonify({
                "error": "No audio data received",
                "text": "",
                "confidence": 0.0
            }), 400
        
        # 记录接收的数据大小
        logger.debug(f"收到音频数据: {len(audio_bytes)} 字节")
        
        # PCM 16bit → numpy float32
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        # 检查音频长度
        duration_sec = len(audio_np) / 16000
        logger.debug(f"音频时长: {duration_sec:.2f} 秒")
        
        if duration_sec < 0.1:
            # 音频太短，直接返回空结果
            return jsonify({
                "text": "",
                "confidence": 0.0,
                "duration": duration_sec,
                "timestamp": time.time()
            })
        
        # 调用模型转写
        start_time = time.time()
        result = model.generate(
            input=audio_np,
            cache={},
            language="zh",
            use_itn=True,
            batch_size=1,
        )
        
        inference_time = time.time() - start_time
        
        # 解析结果
        text = ""
        confidence = 0.0
        
        if result and len(result) > 0:
            first_result = result[0]
            text = first_result.get("text", "").strip()
            
            # 尝试获取置信度
            if "timestamp" in first_result:
                # 如果有 timestamp 信息，计算平均置信度
                timestamps = first_result.get("timestamp", [])
                if timestamps and len(timestamps) > 0:
                    # 简单设置为 0.9（SenseVoice 不直接提供置信度）
                    confidence = 0.9
            else:
                confidence = 0.85 if text else 0.0
        
        logger.info(f"转写完成: '{text}' (耗时 {inference_time:.3f}s)")
        
        return jsonify({
            "text": text,
            "confidence": confidence,
            "duration": duration_sec,
            "inference_time": inference_time,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"转写失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return jsonify({
            "error": str(e),
            "text": "",
            "confidence": 0.0
        }), 500


@app.route('/info', methods=['GET'])
def info():
    """获取服务信息"""
    return jsonify({
        "service": "Python Transcriber Service",
        "version": "1.0.0",
        "model": "SenseVoice Small",
        "vad": "FSMN-VAD",
        "device": "cpu",
        "sample_rate": 16000,
        "initialized": is_initialized
    })


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Python Transcriber Service 启动中...")
    logger.info("=" * 60)
    
    # 初始化模型
    success = init_model()
    if not success:
        logger.error("模型初始化失败，服务将以降级模式启动")
    
    # 启动 Flask 服务
    host = "127.0.0.1"
    port = 9527
    
    logger.info(f"服务启动: http://{host}:{port}")
    logger.info("端点:")
    logger.info(f"  - GET  /health      健康检查")
    logger.info(f"  - POST /transcribe  转写音频")
    logger.info(f"  - GET  /info        服务信息")
    logger.info("=" * 60)
    
    app.run(
        host=host,
        port=port,
        debug=False,
        threaded=True
    )


if __name__ == '__main__':
    main()

