# -*- coding: utf-8 -*-
"""
直播相关数据库模型
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index, Numeric, Boolean, JSON
from sqlalchemy.orm import relationship

from .base import BaseModel


class LiveSession(BaseModel):
    """直播会话模型"""
    
    __tablename__ = "live_sessions"
    
    # 基本信息
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment="用户ID")
    room_id = Column(String(100), nullable=False, comment="直播间ID")
    platform = Column(String(50), default="douyin", nullable=False, comment="直播平台")
    
    # 直播信息
    title = Column(String(200), nullable=True, comment="直播标题")
    cover_url = Column(String(500), nullable=True, comment="封面图URL")
    stream_url = Column(String(500), nullable=True, comment="直播流地址")
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, nullable=True, comment="结束时间")
    duration = Column(Integer, default=0, comment="时长（秒）")
    status = Column(String(20), default="live", comment="状态: live, ended, error")
    
    # 观众数据统计
    total_viewers = Column(Integer, default=0, comment="总观看人数")
    peak_viewers = Column(Integer, default=0, comment="峰值在线人数")
    avg_viewers = Column(Integer, default=0, comment="平均在线人数")
    new_followers = Column(Integer, default=0, comment="新增粉丝数")
    
    # 互动数据统计
    comment_count = Column(Integer, default=0, comment="评论数")
    like_count = Column(Integer, default=0, comment="点赞数")
    share_count = Column(Integer, default=0, comment="分享数")
    gift_count = Column(Integer, default=0, comment="礼物数量")
    gift_value = Column(Numeric(10, 2), default=0, comment="礼物价值（元）")
    
    # AI 使用统计
    ai_usage_count = Column(Integer, default=0, comment="AI调用次数")
    ai_usage_tokens = Column(Integer, default=0, comment="AI消耗Token数")
    ai_usage_cost = Column(Numeric(10, 4), default=0, comment="AI成本（元）")
    
    # 语音转写统计
    transcribe_enabled = Column(Boolean, default=False, comment="是否启用转写")
    transcribe_duration = Column(Integer, default=0, comment="转写时长（秒）")
    transcribe_char_count = Column(Integer, default=0, comment="转写字数")
    
    # 数据文件路径
    comment_file = Column(String(500), nullable=True, comment="评论文件路径")
    transcript_file = Column(String(500), nullable=True, comment="转写文件路径")
    report_file = Column(String(500), nullable=True, comment="报告文件路径")
    recording_file = Column(String(500), nullable=True, comment="录制文件路径")
    
    # 热词统计（JSON格式）
    hotwords = Column(Text, nullable=True, comment="热词统计JSON")
    # 示例: [{"word": "棒", "count": 50}, {"word": "喜欢", "count": 30}]
    
    # 情感分析（JSON格式）
    sentiment_stats = Column(Text, nullable=True, comment="情感统计JSON")
    # 示例: {"positive": 0.6, "neutral": 0.3, "negative": 0.1}
    
    # 关键事件（JSON格式）
    key_events = Column(Text, nullable=True, comment="关键事件JSON")
    # 示例: [{"time": "12:30", "type": "peak", "desc": "在线人数达到峰值"}]
    
    # 备注
    notes = Column(Text, nullable=True, comment="备注")
    tags = Column(String(500), nullable=True, comment="标签（逗号分隔）")
    
    # 关联关系
    user = relationship("User", back_populates="live_sessions")
    
    # 索引
    __table_args__ = (
        Index('idx_live_session_user_id', 'user_id'),
        Index('idx_live_session_room_id', 'room_id'),
        Index('idx_live_session_start_time', 'start_time'),
        Index('idx_live_session_status', 'status'),
    )
    
    def get_hotwords(self) -> list:
        """获取热词列表"""
        import json
        if not self.hotwords:
            return []
        try:
            return json.loads(self.hotwords)
        except:
            return []
    
    def set_hotwords(self, hotwords: list) -> None:
        """设置热词列表"""
        import json
        self.hotwords = json.dumps(hotwords, ensure_ascii=False)
    
    def get_sentiment_stats(self) -> dict:
        """获取情感统计"""
        import json
        if not self.sentiment_stats:
            return {"positive": 0, "neutral": 0, "negative": 0}
        try:
            return json.loads(self.sentiment_stats)
        except:
            return {}
    
    def set_sentiment_stats(self, stats: dict) -> None:
        """设置情感统计"""
        import json
        self.sentiment_stats = json.dumps(stats, ensure_ascii=False)
    
    def get_key_events(self) -> list:
        """获取关键事件"""
        import json
        if not self.key_events:
            return []
        try:
            return json.loads(self.key_events)
        except:
            return []
    
    def set_key_events(self, events: list) -> None:
        """设置关键事件"""
        import json
        self.key_events = json.dumps(events, ensure_ascii=False)
    
    def calculate_duration(self) -> int:
        """计算直播时长"""
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            self.duration = int(delta.total_seconds())
            return self.duration
        return 0
    
    def to_dict(self, exclude: Optional[list] = None) -> dict:
        """转换为字典"""
        data = super().to_dict(exclude=exclude)
        # 解析 JSON 字段
        data['hotwords'] = self.get_hotwords()
        data['sentiment_stats'] = self.get_sentiment_stats()
        data['key_events'] = self.get_key_events()
        return data
