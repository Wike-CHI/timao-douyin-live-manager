"""
提猫直播助手 - 情感分析模块
负责分析评论中的情感倾向
"""

import re
from typing import Dict, List, Any, Tuple
from snownlp import SnowNLP
from collections import defaultdict
import jieba
from server.utils.logger import LoggerMixin


class SentimentAnalyzer(LoggerMixin):
    """情感分析器"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.emotion_keywords = self._load_emotion_keywords()
        self.logger.info("情感分析器初始化完成")
    
    def _load_emotion_keywords(self) -> Dict[str, List[str]]:
        """加载情感关键词词典"""
        return {
            'positive': [
                '好', '棒', '赞', '喜欢', '爱', '优秀', '完美', '满意', '开心', '高兴',
                '不错', '可以', '支持', '推荐', '值得', '惊喜', '感动', '温暖', '舒适',
                '美丽', '漂亮', '帅气', '可爱', '萌', '厉害', '牛', '强', '专业',
                '666', '赞', '👍', '❤️', '😊', '😄', '😍', '🎉', '👏'
            ],
            'negative': [
                '差', '烂', '垃圾', '讨厌', '恨', '失望', '糟糕', '不满', '生气', '愤怒',
                '丑', '难看', '恶心', '反感', '假', '骗', '坑', '贵', '不值', '后悔',
                '慢', '卡', '坏', '故障', '问题', '缺陷', '不足', '缺点', '毛病',
                '👎', '😤', '😡', '😭', '💔', '💩', '💀'
            ],
            'neutral': [
                '一般', '还行', '普通', '平常', '正常', '可以', '行吧', '凑合',
                '了解', '知道', '请问', '咨询', '问', '想', '考虑', '研究',
                '对比', '参考', '看看', '试试', '体验', '感受'
            ],
            'excited': [
                '哇', '太棒了', 'amazing', '惊艳', '震撼', '绝了', '牛逼', '厉害了',
                '我的天', '天呐', '卧槽', 'wtf', 'awesome', 'great', 'excellent',
                '🔥', '💥', '🤩', '🤯', '😱', '🎊'
            ],
            'curious': [
                '什么', '怎么', '为什么', '如何', '吗', '呢', '吧', '啊',
                '请教', '请问', '咨询', '问', '求', '想要', '需要', '了解',
                '？', '?', '🤔', '❓', '❔'
            ],
            'supportive': [
                '支持', '加油', '继续', '坚持', '关注了', '关注', '订阅', '粉',
                '挺', '顶', '力挺', '力顶', '必须', '一定', '肯定', '当然',
                '👍', '💪', '🔥', '❤️', '🌟'
            ]
        }
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """分析单条文本的情感"""
        if not text:
            return {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'emotions': {},
                'keywords': []
            }
        
        # 使用SnowNLP进行基础情感分析
        snow_score = SnowNLP(text).sentiments
        
        # 基于关键词的情感分析
        keyword_scores = self._analyze_by_keywords(text)
        
        # 综合评分
        combined_score = self._combine_scores(snow_score, keyword_scores)
        
        # 确定主要情感
        sentiment = self._determine_sentiment(combined_score)
        
        # 提取情感关键词
        emotions, keywords = self._extract_emotion_keywords(text)
        
        return {
            'sentiment': sentiment,
            'confidence': combined_score,
            'emotions': emotions,
            'keywords': keywords,
            'snow_score': snow_score,
            'keyword_score': keyword_scores
        }
    
    def _analyze_by_keywords(self, text: str) -> Dict[str, float]:
        """基于关键词的情感分析"""
        scores = defaultdict(float)
        total_matches = 0
        
        # 分词
        words = jieba.lcut(text.lower())
        
        # 统计各类情感关键词
        for emotion, keywords in self.emotion_keywords.items():
            matches = 0
            for word in words:
                if word in keywords:
                    matches += 1
                    total_matches += 1
            scores[emotion] = matches
        
        # 归一化处理
        if total_matches > 0:
            for emotion in scores:
                scores[emotion] = scores[emotion] / total_matches
        
        return dict(scores)
    
    def _combine_scores(self, snow_score: float, keyword_scores: Dict[str, float]) -> float:
        """综合不同方法的评分"""
        # SnowNLP评分权重0.6，关键词评分权重0.4
        keyword_positive = keyword_scores.get('positive', 0) + keyword_scores.get('excited', 0) + keyword_scores.get('supportive', 0)
        keyword_negative = keyword_scores.get('negative', 0)
        keyword_neutral = keyword_scores.get('neutral', 0) + keyword_scores.get('curious', 0)
        
        # 将关键词评分转换为情感倾向值(-1到1)
        keyword_sentiment = keyword_positive - keyword_negative
        
        # 综合评分(0到1)
        combined = 0.6 * snow_score + 0.4 * ((keyword_sentiment + 1) / 2)
        
        return combined
    
    def _determine_sentiment(self, score: float) -> str:
        """根据评分确定情感类别"""
        if score >= 0.7:
            return 'positive'
        elif score >= 0.6:
            return 'excited'
        elif score >= 0.4:
            return 'neutral'
        elif score >= 0.3:
            return 'curious'
        elif score >= 0.2:
            return 'supportive'
        else:
            return 'negative'
    
    def _extract_emotion_keywords(self, text: str) -> Tuple[Dict[str, int], List[str]]:
        """提取情感关键词"""
        emotions = defaultdict(int)
        keywords = []
        
        # 分词
        words = jieba.lcut(text.lower())
        
        # 统计情感关键词
        for word in words:
            for emotion, emotion_keywords in self.emotion_keywords.items():
                if word in emotion_keywords:
                    emotions[emotion] += 1
                    if word not in keywords:
                        keywords.append(word)
        
        return dict(emotions), keywords
    
    def analyze_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析评论列表的情感分布"""
        if not comments:
            return {
                'overall_sentiment': 'neutral',
                'sentiment_distribution': {},
                'average_confidence': 0.0,
                'total_comments': 0,
                'emotion_stats': {}
            }
        
        sentiment_counts = defaultdict(int)
        emotion_stats = defaultdict(int)
        total_confidence = 0.0
        detailed_results = []
        
        for comment in comments:
            content = comment.get('content', '')
            result = self.analyze_sentiment(content)
            detailed_results.append(result)
            
            sentiment_counts[result['sentiment']] += 1
            total_confidence += result['confidence']
            
            # 统计情感关键词
            for emotion, count in result['emotions'].items():
                emotion_stats[emotion] += count
        
        total_comments = len(comments)
        average_confidence = total_confidence / total_comments if total_comments > 0 else 0.0
        
        # 计算情感分布百分比
        sentiment_distribution = {}
        for sentiment, count in sentiment_counts.items():
            sentiment_distribution[sentiment] = {
                'count': count,
                'percentage': round((count / total_comments) * 100, 2)
            }
        
        # 确定整体情感倾向
        overall_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0] if sentiment_counts else 'neutral'
        
        return {
            'overall_sentiment': overall_sentiment,
            'sentiment_distribution': sentiment_distribution,
            'average_confidence': round(average_confidence, 4),
            'total_comments': total_comments,
            'emotion_stats': dict(emotion_stats),
            'detailed_results': detailed_results
        }
    
    def get_sentiment_trend(self, comments: List[Dict[str, Any]], time_windows: int = 5) -> List[Dict[str, Any]]:
        """获取情感趋势"""
        if not comments:
            return []
        
        # 按时间排序
        sorted_comments = sorted(comments, key=lambda x: x.get('timestamp', 0))
        
        # 分割时间段
        total_comments = len(sorted_comments)
        window_size = max(1, total_comments // time_windows)
        
        trend_data = []
        for i in range(0, total_comments, window_size):
            window_comments = sorted_comments[i:i+window_size]
            if not window_comments:
                continue
            
            analysis = self.analyze_comments(window_comments)
            latest_timestamp = window_comments[-1].get('timestamp', 0)
            
            trend_data.append({
                'timestamp': latest_timestamp,
                'sentiment': analysis['overall_sentiment'],
                'distribution': analysis['sentiment_distribution'],
                'confidence': analysis['average_confidence'],
                'comment_count': len(window_comments)
            })
        
        return trend_data