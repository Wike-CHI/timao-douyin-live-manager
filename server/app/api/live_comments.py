# -*- coding: utf-8 -*-
"""
直播评论管理 API
基于FastAPI架构的评论、热词、AI话术等功能
"""

import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, AsyncGenerator
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# 导入服务模块
import sys
import os
from pathlib import Path

# 确保能导入项目模块
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.utils.config import Config
from server.utils.logger import setup_logger
from server.ingest.comment_fetcher import CommentFetcher
from server.nlp.hotword_analyzer import HotwordAnalyzer
from server.ai.tip_generator import TipGenerator

router = APIRouter(prefix="/api/live", tags=["live-comments"])
logger = setup_logger(__name__)

# 全局服务实例
config = Config()
comment_fetcher: Optional[CommentFetcher] = None
hotword_analyzer: Optional[HotwordAnalyzer] = None
tip_generator: Optional[TipGenerator] = None
sse_clients = set()

# Pydantic 模型
class HealthStatus(BaseModel):
    """健康检查响应模型"""
    success: bool
    data: Dict[str, Any]
    message: str
    timestamp: str
    code: int

class CommentsResponse(BaseModel):
    """评论响应模型"""
    success: bool
    data: Dict[str, Any]
    message: str
    timestamp: str
    code: int

class HotwordsResponse(BaseModel):
    """热词响应模型"""
    success: bool
    data: Dict[str, Any]
    message: str
    timestamp: str
    code: int

class TipsResponse(BaseModel):
    """AI话术响应模型"""
    success: bool
    data: Dict[str, Any]
    message: str
    timestamp: str
    code: int

class ConfigResponse(BaseModel):
    """配置响应模型"""
    success: bool
    data: Dict[str, Any]
    message: str
    timestamp: str
    code: int

def init_services():
    """初始化服务实例"""
    global comment_fetcher, hotword_analyzer, tip_generator
    
    try:
        if not comment_fetcher:
            comment_fetcher = CommentFetcher(config)
        if not hotword_analyzer:
            hotword_analyzer = HotwordAnalyzer(config)
        if not tip_generator:
            tip_generator = TipGenerator(config)
            
        logger.info("服务初始化完成")
    except Exception as e:
        logger.error(f"服务初始化失败: {e}")

@router.get("/health", response_model=HealthStatus)
async def health_check():
    """健康检查接口"""
    try:
        init_services()
        
        # 检查各组件状态
        services_status = {
            'comment_ingest': 'running' if comment_fetcher and comment_fetcher.is_running else 'stopped',
            'nlp_processor': 'running' if hotword_analyzer and hotword_analyzer.is_running else 'stopped',
            'ai_generator': 'running' if tip_generator and tip_generator.is_running else 'stopped'
        }
        
        # 计算运行时间（简化版本）
        uptime = int(time.time())
        
        return HealthStatus(
            success=True,
            data={
                'status': 'healthy',
                'version': '1.0.0',
                'uptime': uptime,
                'services': services_status
            },
            message='服务运行正常',
            timestamp=datetime.now().isoformat(),
            code=200
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'data': None,
                'message': '健康检查失败',
                'error': {'code': 'HEALTH_CHECK_ERROR', 'details': str(e)},
                'timestamp': datetime.now().isoformat(),
                'code': 500
            }
        )

@router.get("/comments", response_model=CommentsResponse)
async def get_comments(
    limit: int = Query(50, description="返回评论数量限制"),
    since: Optional[float] = Query(None, description="获取指定时间戳之后的评论")
):
    """获取评论列表"""
    try:
        init_services()
        
        # 从评论抓取器获取数据
        if not comment_fetcher:
            raise HTTPException(
                status_code=503,
                detail={
                    'success': False,
                    'data': None,
                    'message': '评论抓取器未初始化',
                    'error': {'code': 'SERVICE_UNAVAILABLE', 'details': '评论抓取服务未启动'},
                    'timestamp': datetime.now().isoformat(),
                    'code': 503
                }
            )
        
        # 获取评论数据
        if since:
            comments = comment_fetcher.get_comments_since(since)
        else:
            comments = comment_fetcher.get_recent_comments(limit)
        
        return CommentsResponse(
            success=True,
            data={
                'comments': comments,
                'total': len(comments),
                'stats': comment_fetcher.get_stats() if hasattr(comment_fetcher, 'get_stats') else {}
            },
            message='获取评论成功',
            timestamp=datetime.now().isoformat(),
            code=200
        )
        
    except Exception as e:
        logger.error(f"获取评论失败: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'data': None,
                'message': '获取评论失败',
                'error': {'code': 'COMMENTS_FETCH_ERROR', 'details': str(e)},
                'timestamp': datetime.now().isoformat(),
                'code': 500
            }
        )

@router.get("/stream/comments")
async def stream_comments():
    """评论流推送接口 (Server-Sent Events)"""
    
    async def generate() -> AsyncGenerator[str, None]:
        """生成SSE数据流"""
        client_id = id(asyncio.current_task())
        
        try:
            init_services()
            
            # 添加客户端到活跃连接集合
            sse_clients.add(client_id)
            logger.info(f"新的SSE客户端连接: {client_id}")
            
            # 发送初始连接确认
            yield f"data: {json.dumps({'type': 'connected', 'message': '连接成功'})}\n\n"
            
            # 持续推送评论数据
            while client_id in sse_clients:
                try:
                    # 从评论抓取器获取最新评论
                    if comment_fetcher and hasattr(comment_fetcher, 'has_new_comments') and comment_fetcher.has_new_comments():
                        comments = comment_fetcher.get_latest_comments(limit=10)
                        for comment in comments:
                            if hasattr(comment, 'to_dict'):
                                data = json.dumps(comment.to_dict())
                            else:
                                data = json.dumps(comment)
                            yield f"data: {data}\n\n"
                    
                    await asyncio.sleep(0.5)  # 500ms间隔
                    
                except asyncio.CancelledError:
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
    
    return StreamingResponse(
        generate(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )

@router.get("/hotwords", response_model=HotwordsResponse)
async def get_hotwords(
    limit: int = Query(10, description="返回热词数量限制"),
    category: Optional[str] = Query(None, description="热词分类")
):
    """获取热词排行"""
    try:
        init_services()
        
        # 从热词分析器获取数据
        if not hotword_analyzer:
            raise Exception("热词分析器未初始化")
            
        hotwords = hotword_analyzer.get_hotwords(limit=limit, category=category)
        
        return HotwordsResponse(
            success=True,
            data={
                'hotwords': [hw.to_dict() if hasattr(hw, 'to_dict') else hw for hw in hotwords],
                'total': len(hotwords),
                'updated_at': datetime.now().isoformat()
            },
            message='获取热词成功',
            timestamp=datetime.now().isoformat(),
            code=200
        )
        
    except Exception as e:
        logger.error(f"获取热词失败: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'data': None,
                'message': '获取热词失败',
                'error': {'code': 'HOTWORDS_ERROR', 'details': str(e)},
                'timestamp': datetime.now().isoformat(),
                'code': 500
            }
        )

@router.get("/tips/latest", response_model=TipsResponse)
async def get_latest_tips(
    limit: int = Query(5, description="返回话术数量限制"),
    tip_type: Optional[str] = Query(None, description="话术类型")
):
    """获取最新AI话术"""
    try:
        init_services()
        
        # 从AI话术生成器获取数据
        if not tip_generator:
            raise Exception("AI话术生成器未初始化")
            
        tips = tip_generator.get_latest_tips(limit=limit, unused_only=True)
        
        return TipsResponse(
            success=True,
            data={
                'tips': [tip.to_dict() if hasattr(tip, 'to_dict') else tip for tip in tips],
                'total': len(tips),
                'generated_at': datetime.now().isoformat()
            },
            message='获取话术成功',
            timestamp=datetime.now().isoformat(),
            code=200
        )
        
    except Exception as e:
        logger.error(f"获取话术失败: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'data': None,
                'message': '获取话术失败',
                'error': {'code': 'TIPS_ERROR', 'details': str(e)},
                'timestamp': datetime.now().isoformat(),
                'code': 500
            }
        )

@router.put("/tips/{tip_id}/used")
async def mark_tip_used(tip_id: str):
    """标记话术已使用"""
    try:
        init_services()
        
        if not tip_generator:
            raise Exception("AI话术生成器未初始化")
            
        success = tip_generator.mark_tip_used(tip_id)
        
        if success:
            return {
                'success': True,
                'data': {
                    'tip_id': tip_id,
                    'is_used': True,
                    'updated_at': datetime.now().isoformat()
                },
                'message': '话术状态更新成功',
                'timestamp': datetime.now().isoformat(),
                'code': 200
            }
        else:
            raise HTTPException(
                status_code=404,
                detail={
                    'success': False,
                    'data': None,
                    'message': '话术不存在',
                    'error': {'code': 'TIP_NOT_FOUND', 'details': f'话术ID {tip_id} 不存在'},
                    'timestamp': datetime.now().isoformat(),
                    'code': 404
                }
            )
            
    except Exception as e:
        logger.error(f"标记话术失败: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'data': None,
                'message': '标记话术失败',
                'error': {'code': 'MARK_TIP_ERROR', 'details': str(e)},
                'timestamp': datetime.now().isoformat(),
                'code': 500
            }
        )

@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """获取当前配置"""
    try:
        return ConfigResponse(
            success=True,
            data=config.to_dict() if hasattr(config, 'to_dict') else {},
            message='获取配置成功',
            timestamp=datetime.now().isoformat(),
            code=200
        )
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'data': None,
                'message': '获取配置失败',
                'error': {'code': 'CONFIG_ERROR', 'details': str(e)},
                'timestamp': datetime.now().isoformat(),
                'code': 500
            }
        )

@router.post("/config", response_model=ConfigResponse)
async def update_config(request: Request):
    """更新配置"""
    try:
        data = await request.json()
        if not data:
            raise Exception("请求数据为空")
            
        updated_fields = config.update(data) if hasattr(config, 'update') else []
        
        return ConfigResponse(
            success=True,
            data={
                'updated_fields': updated_fields,
                'config': config.to_dict() if hasattr(config, 'to_dict') else {}
            },
            message='配置更新成功',
            timestamp=datetime.now().isoformat(),
            code=200
        )
        
    except Exception as e:
        logger.error(f"配置更新失败: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'data': None,
                'message': '配置更新失败',
                'error': {'code': 'CONFIG_ERROR', 'details': str(e)},
                'timestamp': datetime.now().isoformat(),
                'code': 500
            }
        )