# -*- coding: utf-8 -*-
"""
直播数据分析服务
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from server.app.models import LiveSession, User
from server.app.database import db_session


class LiveAnalyticsService:
    """直播数据分析服务"""
    
    @staticmethod
    def get_streamer_overview(user_id: int, days: int = 7) -> Dict[str, Any]:
        """
        获取主播数据概览
        
        Args:
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            数据概览字典
        """
        with db_session() as session:
            # 计算时间范围
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # 查询直播会话
            sessions = session.query(LiveSession).filter(
                and_(
                    LiveSession.user_id == user_id,
                    LiveSession.start_time >= start_date
                )
            ).all()
            
            if not sessions:
                return {
                    "total_sessions": 0,
                    "total_duration": 0,
                    "total_viewers": 0,
                    "avg_viewers": 0,
                    "peak_viewers": 0,
                    "total_comments": 0,
                    "total_gifts": 0,
                    "total_revenue": 0,
                    "ai_usage": {
                        "total_calls": 0,
                        "total_tokens": 0,
                        "total_cost": 0
                    },
                    "transcribe": {
                        "total_duration": 0,
                        "total_chars": 0
                    }
                }
            
            # 统计数据
            total_sessions = len(sessions)
            total_duration = sum(s.duration for s in sessions)
            total_viewers = sum(s.total_viewers for s in sessions)
            peak_viewers = max(s.peak_viewers for s in sessions)
            total_comments = sum(s.comment_count for s in sessions)
            total_gifts = sum(s.gift_count for s in sessions)
            total_revenue = float(sum(s.gift_value for s in sessions))
            
            # AI 使用统计
            ai_total_calls = sum(s.ai_usage_count for s in sessions)
            ai_total_tokens = sum(s.ai_usage_tokens for s in sessions)
            ai_total_cost = float(sum(s.ai_usage_cost for s in sessions))
            
            # 转写统计
            transcribe_duration = sum(s.transcribe_duration for s in sessions)
            transcribe_chars = sum(s.transcribe_char_count for s in sessions)
            
            # 计算平均值
            avg_viewers = total_viewers // total_sessions if total_sessions > 0 else 0
            avg_duration = total_duration // total_sessions if total_sessions > 0 else 0
            
            return {
                "total_sessions": total_sessions,
                "total_duration": total_duration,
                "avg_duration": avg_duration,
                "total_viewers": total_viewers,
                "avg_viewers": avg_viewers,
                "peak_viewers": peak_viewers,
                "total_comments": total_comments,
                "total_gifts": total_gifts,
                "total_revenue": total_revenue,
                "ai_usage": {
                    "total_calls": ai_total_calls,
                    "total_tokens": ai_total_tokens,
                    "total_cost": ai_total_cost,
                    "avg_cost_per_session": ai_total_cost / total_sessions if total_sessions > 0 else 0
                },
                "transcribe": {
                    "total_duration": transcribe_duration,
                    "total_chars": transcribe_chars,
                    "avg_chars_per_session": transcribe_chars // total_sessions if total_sessions > 0 else 0
                },
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": datetime.utcnow().isoformat(),
                    "days": days
                }
            }
    
    @staticmethod
    def get_live_sessions(user_id: int, limit: int = 20, offset: int = 0) -> List[LiveSession]:
        """
        获取直播会话列表
        
        Args:
            user_id: 用户ID
            limit: 返回数量
            offset: 偏移量
            
        Returns:
            直播会话列表
        """
        with db_session() as session:
            return session.query(LiveSession).filter(
                LiveSession.user_id == user_id
            ).order_by(desc(LiveSession.start_time)).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_live_session_detail(session_id: int, user_id: Optional[int] = None) -> Optional[LiveSession]:
        """
        获取直播会话详情
        
        Args:
            session_id: 会话ID
            user_id: 用户ID（可选，用于权限检查）
            
        Returns:
            直播会话对象
        """
        with db_session() as session:
            query = session.query(LiveSession).filter(LiveSession.id == session_id)
            
            if user_id:
                query = query.filter(LiveSession.user_id == user_id)
            
            return query.first()
    
    @staticmethod
    def get_trending_data(user_id: int, days: int = 7) -> Dict[str, Any]:
        """
        获取趋势数据
        
        Args:
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            趋势数据
        """
        with db_session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            sessions = session.query(LiveSession).filter(
                and_(
                    LiveSession.user_id == user_id,
                    LiveSession.start_time >= start_date
                )
            ).order_by(LiveSession.start_time).all()
            
            # 按日期分组统计
            daily_stats = {}
            for s in sessions:
                date_key = s.start_time.strftime('%Y-%m-%d')
                if date_key not in daily_stats:
                    daily_stats[date_key] = {
                        "date": date_key,
                        "sessions": 0,
                        "duration": 0,
                        "viewers": 0,
                        "comments": 0,
                        "gifts": 0,
                        "revenue": 0
                    }
                
                daily_stats[date_key]["sessions"] += 1
                daily_stats[date_key]["duration"] += s.duration
                daily_stats[date_key]["viewers"] += s.total_viewers
                daily_stats[date_key]["comments"] += s.comment_count
                daily_stats[date_key]["gifts"] += s.gift_count
                daily_stats[date_key]["revenue"] += float(s.gift_value)
            
            return {
                "daily": list(daily_stats.values()),
                "period": {
                    "start": start_date.isoformat(),
                    "end": datetime.utcnow().isoformat(),
                    "days": days
                }
            }
    
    @staticmethod
    def get_top_hotwords(user_id: int, limit: int = 20, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取热词Top榜
        
        Args:
            user_id: 用户ID
            limit: 返回数量
            days: 统计天数
            
        Returns:
            热词列表
        """
        with db_session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            sessions = session.query(LiveSession).filter(
                and_(
                    LiveSession.user_id == user_id,
                    LiveSession.start_time >= start_date,
                    LiveSession.hotwords.isnot(None)
                )
            ).all()
            
            # 合并所有热词
            word_counts = {}
            for s in sessions:
                hotwords = s.get_hotwords()
                for item in hotwords:
                    word = item.get("word")
                    count = item.get("count", 0)
                    if word:
                        word_counts[word] = word_counts.get(word, 0) + count
            
            # 排序并返回Top N
            top_words = sorted(
                [{"word": word, "count": count} for word, count in word_counts.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:limit]
            
            return top_words
    
    @staticmethod
    def get_sentiment_distribution(user_id: int, days: int = 7) -> Dict[str, Any]:
        """
        获取情感分布
        
        Args:
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            情感分布数据
        """
        with db_session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            sessions = session.query(LiveSession).filter(
                and_(
                    LiveSession.user_id == user_id,
                    LiveSession.start_time >= start_date,
                    LiveSession.sentiment_stats.isnot(None)
                )
            ).all()
            
            # 统计情感
            total_positive = 0
            total_neutral = 0
            total_negative = 0
            count = 0
            
            for s in sessions:
                stats = s.get_sentiment_stats()
                total_positive += stats.get("positive", 0)
                total_neutral += stats.get("neutral", 0)
                total_negative += stats.get("negative", 0)
                count += 1
            
            if count == 0:
                return {
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0
                }
            
            return {
                "positive": total_positive / count,
                "neutral": total_neutral / count,
                "negative": total_negative / count
            }
    
    @staticmethod
    def create_live_session(
        user_id: int,
        room_id: str,
        title: Optional[str] = None,
        platform: str = "douyin"
    ) -> LiveSession:
        """
        创建直播会话
        
        Args:
            user_id: 用户ID
            room_id: 直播间ID
            title: 直播标题
            platform: 平台
            
        Returns:
            直播会话对象
        """
        with db_session() as session:
            live_session = LiveSession(
                user_id=user_id,
                room_id=room_id,
                title=title,
                platform=platform,
                start_time=datetime.utcnow(),
                status="live"
            )
            
            session.add(live_session)
            session.commit()
            session.refresh(live_session)
            
            return live_session
    
    @staticmethod
    def end_live_session(session_id: int) -> Optional[LiveSession]:
        """
        结束直播会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            更新后的直播会话对象
        """
        with db_session() as session:
            live_session = session.query(LiveSession).filter(
                LiveSession.id == session_id
            ).first()
            
            if not live_session:
                return None
            
            live_session.end_time = datetime.utcnow()
            live_session.status = "ended"
            live_session.calculate_duration()
            
            session.commit()
            session.refresh(live_session)
            
            return live_session
