"""
提猫直播助手 - 评论抓取模块
负责从抖音直播间抓取评论数据
"""

import time
import json
import random
import threading
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import requests
from server.utils.logger import LoggerMixin


class Comment:
    """评论数据模型"""
    
    def __init__(self, user_id: str, username: str, content: str, timestamp: float = None):
        self.user_id = user_id
        self.username = username
        self.content = content
        self.timestamp = timestamp or time.time()
        self.id = f"{user_id}_{int(self.timestamp * 1000)}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'content': self.content,
            'timestamp': self.timestamp,
            'formatted_time': datetime.fromtimestamp(self.timestamp).strftime('%H:%M:%S')
        }


class CommentFetcher(LoggerMixin):
    """评论抓取器"""
    
    def __init__(self, config=None, room_id: str = None, cookie: str = None):
        self.config = config
        self.room_id = room_id or "default_room"
        self.cookie = cookie
        self.is_running = False
        self.comments = []
        self.max_comments = 1000
        self.fetch_interval = 5
        self.callbacks = []
        self._thread = None
        self._lock = threading.Lock()
        
        # 模拟数据开关
        self.use_mock_data = True
        
        self.logger.info(f"评论抓取器初始化完成，房间ID: {self.room_id}")
    
    def add_callback(self, callback: Callable[[Comment], None]):
        """添加新评论回调"""
        self.callbacks.append(callback)
    
    def start(self):
        """开始抓取评论"""
        if self.is_running:
            self.logger.warning("评论抓取器已在运行")
            return
        
        self.is_running = True
        self._thread = threading.Thread(target=self._fetch_loop, daemon=True)
        self._thread.start()
        self.logger.info("评论抓取器已启动")
    
    def stop(self):
        """停止抓取评论"""
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self.logger.info("评论抓取器已停止")
    
    def _fetch_loop(self):
        """抓取循环"""
        while self.is_running:
            try:
                if self.use_mock_data:
                    new_comments = self._fetch_mock_comments()
                else:
                    new_comments = self._fetch_real_comments()
                
                for comment in new_comments:
                    self._add_comment(comment)
                    # 通知回调
                    for callback in self.callbacks:
                        try:
                            callback(comment)
                        except Exception as e:
                            self.logger.error(f"回调执行失败: {e}")
                
                time.sleep(self.fetch_interval)
                
            except Exception as e:
                self.logger.error(f"抓取评论失败: {e}")
                time.sleep(self.fetch_interval)
    
    def _fetch_mock_comments(self) -> List[Comment]:
        """获取模拟评论数据"""
        mock_users = [
            "小猫咪", "直播达人", "粉丝001", "观众A", "路人甲",
            "喵星人", "主播粉", "围观群众", "热心网友", "匿名用户"
        ]
        
        mock_contents = [
            "主播好棒！", "这个产品不错", "价格怎么样？", "有优惠吗？",
            "支持主播", "666", "点赞", "关注了", "什么时候开播？",
            "这个颜色好看", "质量怎么样？", "包邮吗？", "有现货吗？",
            "主播声音好听", "讲得很详细", "想要这个", "多少钱？"
        ]
        
        # 随机生成1-3条评论
        num_comments = random.randint(0, 3)
        comments = []
        
        for _ in range(num_comments):
            user = random.choice(mock_users)
            content = random.choice(mock_contents)
            user_id = f"user_{random.randint(1000, 9999)}"
            
            comment = Comment(user_id, user, content)
            comments.append(comment)
        
        return comments
    
    def _fetch_real_comments(self) -> List[Comment]:
        """获取真实评论数据（待实现）"""
        # TODO: 实现真实的抖音评论抓取
        # 这里需要实现具体的抖音API调用或网页抓取逻辑
        self.logger.warning("真实评论抓取功能待实现，使用模拟数据")
        return self._fetch_mock_comments()
    
    def _add_comment(self, comment: Comment):
        """添加评论到缓存"""
        with self._lock:
            self.comments.append(comment)
            
            # 限制评论数量
            if len(self.comments) > self.max_comments:
                self.comments = self.comments[-self.max_comments:]
    
    def get_recent_comments(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的评论"""
        with self._lock:
            recent = self.comments[-limit:] if self.comments else []
            return [comment.to_dict() for comment in recent]
    
    def get_comments_since(self, timestamp: float) -> List[Dict[str, Any]]:
        """获取指定时间后的评论"""
        with self._lock:
            filtered = [
                comment for comment in self.comments 
                if comment.timestamp > timestamp
            ]
            return [comment.to_dict() for comment in filtered]
    
    def clear_comments(self):
        """清空评论缓存"""
        with self._lock:
            self.comments.clear()
        self.logger.info("评论缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                'total_comments': len(self.comments),
                'is_running': self.is_running,
                'room_id': self.room_id,
                'fetch_interval': self.fetch_interval,
                'use_mock_data': self.use_mock_data
            }
    
    def start_fetching(self):
        """启动评论抓取（后台任务）"""
        self.start()
        self.logger.info("评论抓取任务已启动")