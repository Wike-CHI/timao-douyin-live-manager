# -*- coding: utf-8 -*-
"""
AST Module Test Server
用于测试AST模块的本地Web服务器
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# 添加上级目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置模型缓存路径，解决Windows系统下模型下载路径问题
models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
os.makedirs(models_dir, exist_ok=True)
os.environ['MODELSCOPE_CACHE'] = models_dir
os.environ['HF_HOME'] = os.path.join(models_dir, "huggingface")

# 导入AST模块
from AST_module.ast_service import ASTService, TranscriptionResult, ASTConfig
from AST_module.config import create_ast_config
from AST_module.audio_capture import AudioCapture, AudioConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
ast_service: Optional[ASTService] = None
transcription_results: List[Dict[str, Any]] = []
is_transcribing = False

def transcription_callback(result: TranscriptionResult):
    """转录结果回调函数"""
    global transcription_results
    
    # 将TranscriptionResult转换为字典
    result_dict = {
        "text": result.text,
        "confidence": result.confidence,
        "timestamp": result.timestamp,
        "duration": result.duration,
        "is_final": result.is_final,
        "words": result.words or [],
        "room_id": result.room_id,
        "session_id": result.session_id,
        "formatted_time": datetime.fromtimestamp(result.timestamp).strftime('%H:%M:%S')
    }
    
    # 添加到结果列表
    transcription_results.append(result_dict)
    
    # 限制结果数量，只保留最近的100条
    if len(transcription_results) > 100:
        transcription_results = transcription_results[-100:]
    
    logger.info(f"Received transcription: {result.text}")

# Flask应用
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# 创建Flask应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
# 配置CORS - 限制为本地开发环境
CORS(app, origins=["http://127.0.0.1:30013", "http://localhost:30013"])

@app.route('/')
def index():
    """主页"""
    # 默认返回自动启动页面
    return render_template('auto_launch_service.html')

@app.route('/api/status')
def get_status():
    """获取AST服务状态"""
    global ast_service, is_transcribing
    
    if ast_service is None:
        return jsonify({
            "status": "not_initialized",
            "is_transcribing": False,
            "message": "AST服务未初始化"
        })
    
    try:
        status = ast_service.get_status()
        status["is_transcribing"] = is_transcribing
        return jsonify({
            "status": "success",
            "data": status
        })
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/devices')
def get_audio_devices():
    """获取音频设备列表"""
    try:
        # 创建临时的音频配置来获取设备列表
        temp_config = AudioConfig()
        temp_capture = AudioCapture(temp_config)
        if not temp_capture.initialize():
            return jsonify({
                "status": "error",
                "message": "音频系统初始化失败"
            })
        devices = temp_capture.list_audio_devices()
        
        return jsonify({
            "status": "success",
            "devices": devices
        })
    except Exception as e:
        logger.error(f"获取音频设备列表失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/start', methods=['POST'])
def start_transcription():
    """开始转录"""
    global ast_service, is_transcribing
    
    if ast_service is None:
        return jsonify({
            "status": "error",
            "message": "AST服务未初始化"
        })
    
    if is_transcribing:
        return jsonify({
            "status": "warning",
            "message": "转录已在进行中"
        })
    
    try:
        # 创建异步任务启动转录
        async def start_ast():
            global is_transcribing
            if ast_service is not None:
                success = await ast_service.start_transcription("mic_test")
                is_transcribing = success
                return success
            return False
        
        # 在新的事件循环中运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(start_ast())
        loop.close()
        
        if success:
            # 添加回调函数
            if ast_service is not None:
                ast_service.add_transcription_callback("web_test", transcription_callback)
            
            return jsonify({
                "status": "success",
                "message": "转录已开始"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "启动转录失败"
            })
            
    except Exception as e:
        logger.error(f"启动转录失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/stop', methods=['POST'])
def stop_transcription():
    """停止转录"""
    global ast_service, is_transcribing
    
    if ast_service is None:
        return jsonify({
            "status": "error",
            "message": "AST服务未初始化"
        })
    
    if not is_transcribing:
        return jsonify({
            "status": "warning",
            "message": "转录未在进行中"
        })
    
    try:
        # 创建异步任务停止转录
        async def stop_ast():
            global is_transcribing
            if ast_service is not None:
                success = await ast_service.stop_transcription()
                is_transcribing = False
                return success
            return False
        
        # 在新的事件循环中运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(stop_ast())
        loop.close()
        
        if success:
            return jsonify({
                "status": "success",
                "message": "转录已停止"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "停止转录失败"
            })
            
    except Exception as e:
        logger.error(f"停止转录失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/results')
def get_results():
    """获取转录结果"""
    global transcription_results
    
    # 获取查询参数
    limit = request.args.get('limit', 50, type=int)
    
    # 返回最近的limit条结果
    results = transcription_results[-limit:] if transcription_results else []
    
    return jsonify({
        "status": "success",
        "data": results,
        "count": len(results)
    })

@app.route('/api/clear', methods=['POST'])
def clear_results():
    """清空转录结果"""
    global transcription_results
    transcription_results = []
    
    return jsonify({
        "status": "success",
        "message": "结果已清空"
    })

@app.route('/api/init', methods=['POST'])
def initialize_service():
    """初始化AST服务"""
    global ast_service
    
    try:
        if ast_service is not None:
            return jsonify({
                "status": "warning",
                "message": "AST服务已初始化"
            })
        
        # 获取请求参数
        data = request.get_json() or {}
        device_index = data.get('device_index', None)
        
        # 创建音频配置
        audio_config = AudioConfig(
            sample_rate=16000,
            channels=1,
            chunk_size=1024,
            format=8,  # pyaudio.paInt16
            input_device_index=device_index
        )
        
        # 创建AST配置
        config = create_ast_config(
            chunk_duration=1.0,
            min_confidence=0.5,
            save_audio=False
        )
        config.audio_config = audio_config
        
        # 创建AST服务
        ast_service = ASTService(config)
        
        # 初始化服务
        async def init_ast():
            if ast_service is not None:
                return await ast_service.initialize()
            return False
        
        # 在新的事件循环中运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(init_ast())
        loop.close()
        
        if success:
            return jsonify({
                "status": "success",
                "message": "AST服务初始化成功"
            })
        else:
            ast_service = None
            return jsonify({
                "status": "error",
                "message": "AST服务初始化失败"
            })
            
    except Exception as e:
        logger.error(f"初始化服务失败: {e}")
        ast_service = None
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/cleanup', methods=['POST'])
def cleanup_service():
    """清理AST服务"""
    global ast_service, is_transcribing, transcription_results
    
    if ast_service is None:
        return jsonify({
            "status": "warning",
            "message": "AST服务未初始化"
        })
    
    try:
        # 停止转录（如果正在进行）
        if is_transcribing:
            async def stop_ast():
                global is_transcribing
                if ast_service is not None:
                    success = await ast_service.stop_transcription()
                    is_transcribing = False
                    return success
                return False
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(stop_ast())
            loop.close()
        
        # 清理服务
        async def cleanup_ast():
            global ast_service
            if ast_service is not None:
                await ast_service.cleanup()
            ast_service = None
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(cleanup_ast())
        loop.close()
        
        # 清空结果
        transcription_results = []
        is_transcribing = False
        
        return jsonify({
            "status": "success",
            "message": "AST服务已清理"
        })
        
    except Exception as e:
        logger.error(f"清理服务失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

def create_directories():
    """创建必要的目录"""
    # 创建templates目录
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # 创建static目录
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

def run_server():
    """运行测试服务器"""
    # 创建必要的目录
    create_directories()
    
    # 运行服务器
    app.run(host='127.0.0.1', port=5000, debug=True)

if __name__ == '__main__':
    run_server()