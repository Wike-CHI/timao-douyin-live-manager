# -*- coding: utf-8 -*-
"""
直播复盘报告数据库模型
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index, Numeric, JSON, Float
from sqlalchemy.orm import relationship

from .base import BaseModel


class LiveReviewReport(BaseModel):
    """直播复盘报告模型
    
    存储 Gemini 生成的完整复盘分析结果
    """
    
    __tablename__ = "live_review_reports"
    
    # 关联的直播会话
    session_id = Column(Integer, ForeignKey('live_sessions.id'), unique=True, nullable=False, comment="直播会话ID")
    
    # AI 分析结果（结构化数据）
    overall_score = Column(Float, nullable=True, comment="综合评分 0-100")
    
    # 表现分析（JSON格式）
    performance_analysis = Column(JSON, nullable=True, comment="表现分析")
    # 示例结构：
    # {
    #     "engagement": {"score": 85, "highlights": ["互动积极"], "issues": ["中途冷场"]},
    #     "content_quality": {"score": 78, "highlights": [], "issues": ["话题单一"]},
    #     "conversion": {"score": 62, "signals": ["询价多但转化少"]}
    # }
    
    # 亮点时刻（JSON数组）
    key_highlights = Column(JSON, nullable=True, comment="亮点时刻列表")
    # 示例: ["20:15 在线人数达到峰值 521 人", "20:32 收到单笔最大礼物 ¥188"]
    
    # 主要问题（JSON数组）
    key_issues = Column(JSON, nullable=True, comment="主要问题列表")
    # 示例: ["20:25-20:35 网络波动导致卡顿", "话题切换过于突然"]
    
    # 改进建议（JSON数组，结构化）
    improvement_suggestions = Column(JSON, nullable=True, comment="改进建议列表")
    # 示例结构：
    # [
    #     {
    #         "priority": "high",
    #         "category": "互动技巧",
    #         "action": "增加观众提问环节",
    #         "expected_impact": "提升留存率"
    #     }
    # ]
    
    # AI 生成的完整文本报告（Markdown格式）
    full_report_text = Column(Text, nullable=True, comment="完整报告文本（Markdown）")
    
    # 元数据
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="报告生成时间")
    ai_model = Column(String(50), default="gemini-2.5-flash", nullable=False, comment="使用的AI模型")
    generation_cost = Column(Numeric(10, 6), default=0, comment="生成成本（美元）")
    generation_tokens = Column(Integer, default=0, comment="消耗的Token数")
    generation_duration = Column(Float, default=0, comment="生成耗时（秒）")
    
    # 生成状态
    status = Column(String(20), default="completed", nullable=False, comment="状态: pending, completed, failed")
    error_message = Column(Text, nullable=True, comment="错误信息（如果生成失败）")
    
    # 关联关系
    session = relationship("LiveSession", back_populates="review_report")
    
    # 索引
    __table_args__ = (
        Index('idx_live_review_session_id', 'session_id'),
        Index('idx_live_review_generated_at', 'generated_at'),
        Index('idx_live_review_status', 'status'),
    )
    
    def to_dict(self, exclude: Optional[list] = None) -> dict:
        """转换为字典"""
        data = super().to_dict(exclude=exclude)
        # 确保 JSON 字段正确序列化
        data['performance_analysis'] = self.performance_analysis or {}
        data['key_highlights'] = self.key_highlights or []
        data['key_issues'] = self.key_issues or []
        data['improvement_suggestions'] = self.improvement_suggestions or []
        return data
