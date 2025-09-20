#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提猫直播助手 - Flask 主应用
"""

import os
import sys
from datetime import datetime
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from dotenv import load_dotenv
import json
import time
import threading
from typing import Dict, Any

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入自定义模块
from server.utils.config import Config
from server.utils.logger import setup_logger
from server.ingest.comment_fetcher import CommentFetcher
from server.nlp.hotword_analyzer import HotwordAnalyzer
from server.ai.tip_generator import TipGenerator

# 初始化日志
logger = setup_logger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 全局变量
config = Config()
comment_fetcher = None
hotword_analyzer = None
tip_generator = None

# 存储活跃的SSE连接
sse_clients = set()


def create_app():
    """创建并配置Flask应用"""
    global comment_fetcher, hotword_analyzer, tip_generator
    
    try:
        # 初始化组件
        comment_fetcher = CommentFetcher(config)
        hotword_analyzer = HotwordAnalyzer(config)
        tip_generator = TipGenerator(config)
        
        logger.info("应用组件初始化完成")
        
        # 启动后台任务
        start_background_tasks()
        
        return app
        
    except Exception as e:
        logger.error(f"应用初始化失败: {e}")
        raise


def start_background_tasks():
    """启动后台任务"""
    try:
        # 启动评论抓取任务
        comment_thread = threading.Thread(
            target=comment_fetcher.start_fetching,
            daemon=True
        )
        comment_thread.start()
        
        # 启动热词分析任务
        hotword_thread = threading.Thread(
            target=hotword_analyzer.start_analyzing,
            daemon=True
        )
        hotword_thread.start()
        
        # 启动AI话术生成任务
        tip_thread = threading.Thread(
            target=tip_generator.start_generating,
            daemon=True
        )
        tip_thread.start()
        
        logger.info("后台任务启动完成")
        
    except Exception as e:
        logger.error(f"后台任务启动失败: {e}")


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        # 检查各组件状态
        services_status = {
            'comment_ingest': 'running' if comment_fetcher and comment_fetcher.is_running else 'stopped',
            'nlp_processor': 'running' if hotword_analyzer and hotword_analyzer.is_running else 'stopped',
            'ai_generator': 'running' if tip_generator and tip_generator.is_running else 'stopped'
        }
        
        # 计算运行时间
        uptime = int(time.time() - app.start_time) if hasattr(app, 'start_time') else 0
        
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'version': '1.0.0',
                'uptime': uptime,
                'services': services_status
            },
            'message': '服务运行正常',
            'timestamp': datetime.now().isoformat(),
            'code': 200
        })
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            'success': False,
            'data': None,
            'message': '健康检查失败',
            'error': {'code': 'HEALTH_CHECK_ERROR', 'details': str(e)},
            'timestamp': datetime.now().isoformat(),
            'code': 500
        }), 500


@app.route('/api/comments', methods=['GET'])
def get_comments():
    """获取评论列表"""
    try:
        # 获取查询参数
        limit = request.args.get('limit', 50, type=int)
        since = request.args.get('since', None, type=float)
        
        # 从评论抓取器获取数据
        if not comment_fetcher:
            return jsonify({
                'success': False,
                'data': None,
                'message': '评论抓取器未初始化',
                'error': {'code': 'SERVICE_UNAVAILABLE', 'details': '评论抓取服务未启动'},
                'timestamp': datetime.now().isoformat(),
                'code': 503
            }), 503
        
        # 获取评论数据
        if since:
            comments = comment_fetcher.get_comments_since(since)
        else:
            comments = comment_fetcher.get_recent_comments(limit)
        
        return jsonify({
            'success': True,
            'data': {
                'comments': comments,
                'total': len(comments),
                'stats': comment_fetcher.get_stats()
            },
            'message': '获取评论成功',
            'timestamp': datetime.now().isoformat(),
            'code': 200
        })
        
    except Exception as e:
        logger.error(f"获取评论失败: {e}")
        return jsonify({
            'success': False,
            'data': None,
            'message': '获取评论失败',
            'error': {'code': 'COMMENTS_FETCH_ERROR', 'details': str(e)},
            'timestamp': datetime.now().isoformat(),
            'code': 500
        }), 500


@app.route('/api/stream/comments', methods=['GET'])
def stream_comments():
    """评论流推送接口 (Server-Sent Events)"""
    def generate():
        """生成SSE数据流"""
        try:
            # 添加客户端到活跃连接集合
            client_id = id(threading.current_thread())
            sse_clients.add(client_id)
            
            logger.info(f"新的SSE客户端连接: {client_id}")
            
            # 发送初始连接确认
            yield f"data: {json.dumps({'type': 'connected', 'message': '连接成功'})}\n\n"
            
            # 持续推送评论数据
            while client_id in sse_clients:
                try:
                    # 从评论抓取器获取最新评论
                    if comment_fetcher and comment_fetcher.has_new_comments():
                        comments = comment_fetcher.get_latest_comments(limit=10)
                        for comment in comments:
                            data = json.dumps(comment.to_dict())
                            yield f"data: {data}\n\n"
                    
                    time.sleep(0.5)  # 500ms间隔
                    
                except GeneratorExit:
                    break
                except Exception as e:
                    logger.error(f"SSE数据生成错误: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'message': '数据推送错误'})}\n\n"
                    
        except Exception as e:
            logger.error(f"SSE连接错误: {e}")
        finally:
            # 清理连接
            if client_id in sse_clients:
                sse_clients.remove(client_id)
            logger.info(f"SSE客户端断开连接: {client_id}")
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )


@app.route('/api/hotwords', methods=['GET'])
def get_hotwords():
    """获取热词排行"""
    try:
        # 获取查询参数
        limit = request.args.get('limit', 10, type=int)
        category = request.args.get('category', None)
        
        # 从热词分析器获取数据
        if not hotword_analyzer:
            raise Exception("热词分析器未初始化")
            
        hotwords = hotword_analyzer.get_hotwords(limit=limit, category=category)
        
        return jsonify({
            'success': True,
            'data': {
                'hotwords': [hw.to_dict() for hw in hotwords],
                'total': len(hotwords),
                'updated_at': datetime.now().isoformat()
            },
            'message': '获取热词成功',
            'timestamp': datetime.now().isoformat(),
            'code': 200
        })
        
    except Exception as e:
        logger.error(f"获取热词失败: {e}")
        return jsonify({
            'success': False,
            'data': None,
            'message': '获取热词失败',
            'error': {'code': 'HOTWORDS_ERROR', 'details': str(e)},
            'timestamp': datetime.now().isoformat(),
            'code': 500
        }), 500


@app.route('/api/tips/latest', methods=['GET'])
def get_latest_tips():
    """获取最新AI话术"""
    try:
        # 获取查询参数
        limit = request.args.get('limit', 5, type=int)
        tip_type = request.args.get('type', None)
        
        # 从AI话术生成器获取数据
        if not tip_generator:
            raise Exception("AI话术生成器未初始化")
            
        tips = tip_generator.get_latest_tips(limit=limit, unused_only=True)
        
        return jsonify({
            'success': True,
            'data': {
                'tips': [tip.to_dict() for tip in tips],
                'total': len(tips),
                'generated_at': datetime.now().isoformat()
            },
            'message': '获取话术成功',
            'timestamp': datetime.now().isoformat(),
            'code': 200
        })
        
    except Exception as e:
        logger.error(f"获取话术失败: {e}")
        return jsonify({
            'success': False,
            'data': None,
            'message': '获取话术失败',
            'error': {'code': 'TIPS_ERROR', 'details': str(e)},
            'timestamp': datetime.now().isoformat(),
            'code': 500
        }), 500


@app.route('/api/tips/<tip_id>/used', methods=['PUT'])
def mark_tip_used(tip_id: str):
    """标记话术已使用"""
    try:
        if not tip_generator:
            raise Exception("AI话术生成器未初始化")
            
        success = tip_generator.mark_tip_used(tip_id)
        
        if success:
            return jsonify({
                'success': True,
                'data': {
                    'tip_id': tip_id,
                    'is_used': True,
                    'updated_at': datetime.now().isoformat()
                },
                'message': '话术状态更新成功',
                'timestamp': datetime.now().isoformat(),
                'code': 200
            })
        else:
            return jsonify({
                'success': False,
                'data': None,
                'message': '话术不存在',
                'error': {'code': 'TIP_NOT_FOUND', 'details': f'话术ID {tip_id} 不存在'},
                'timestamp': datetime.now().isoformat(),
                'code': 404
            }), 404
            
    except Exception as e:
        logger.error(f"标记话术失败: {e}")
        return jsonify({
            'success': False,
            'data': None,
            'message': '标记话术失败',
            'error': {'code': 'MARK_TIP_ERROR', 'details': str(e)},
            'timestamp': datetime.now().isoformat(),
            'code': 500
        }), 500


@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    """配置管理接口"""
    try:
        if request.method == 'GET':
            # 获取当前配置
            return jsonify({
                'success': True,
                'data': config.to_dict(),
                'message': '获取配置成功',
                'timestamp': datetime.now().isoformat(),
                'code': 200
            })
            
        elif request.method == 'POST':
            # 更新配置
            data = request.get_json()
            if not data:
                raise Exception("请求数据为空")
                
            updated_fields = config.update(data)
            
            return jsonify({
                'success': True,
                'data': {
                    'updated_fields': updated_fields,
                    'config': config.to_dict()
                },
                'message': '配置更新成功',
                'timestamp': datetime.now().isoformat(),
                'code': 200
            })
            
    except Exception as e:
        logger.error(f"配置管理失败: {e}")
        return jsonify({
            'success': False,
            'data': None,
            'message': '配置管理失败',
            'error': {'code': 'CONFIG_ERROR', 'details': str(e)},
            'timestamp': datetime.now().isoformat(),
            'code': 500
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'data': None,
        'message': '接口不存在',
        'error': {'code': 'NOT_FOUND', 'details': '请求的接口不存在'},
        'timestamp': datetime.now().isoformat(),
        'code': 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'success': False,
        'data': None,
        'message': '服务器内部错误',
        'error': {'code': 'INTERNAL_ERROR', 'details': '服务器内部错误'},
        'timestamp': datetime.now().isoformat(),
        'code': 500
    }), 500


if __name__ == '__main__':
    try:
        # 记录启动时间
        app.start_time = time.time()
        
        # 创建应用
        app = create_app()
        
        # 获取配置
        host = os.getenv('FLASK_HOST', '127.0.0.1')
        port = int(os.getenv('FLASK_PORT', 5001))
        debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
        
        logger.info(f"启动Flask应用: http://{host}:{port}")
        
        # 启动应用
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        sys.exit(1)