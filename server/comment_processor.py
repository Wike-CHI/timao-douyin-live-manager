"""
提猫直播助手 - 评论处理器
负责处理直播评论的解析、分析和存储
"""

import re
import json
import time
import threading
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import asdict

from .models import Comment, HotWord, data_manager
from .utils.helpers import format_time, safe_get, Timer
from .utils.validators import validate_comment, sanitize_input


class CommentProcessor:
    """评论处理器"""
    
    def __init__(self):
        self.is_running = False
        self.processing_thread = None
        self.comment_queue = deque(maxlen=10000)  # 评论队列
        self.hot_words = defaultdict(int)  # 热词统计
        self.word_trends = defaultdict(list)  # 词汇趋势
        self.callbacks = []  # 回调函数列表
        self.stats = {
            'total_comments': 0,
            'processed_comments': 0,
            'error_comments': 0,
            'start_time': None,
            'last_comment_time': None
        }
        
        # 配置参数
        self.config = {
            'hot_word_threshold': 3,  # 热词阈值
            'max_hot_words': 50,      # 最大热词数量
            'trend_window': 300,      # 趋势窗口（秒）
            'cleanup_interval': 600,  # 清理间隔（秒）
            'batch_size': 10,         # 批处理大小
            'enable_sentiment': True,  # 启用情感分析
            'filter_spam': True,      # 过滤垃圾评论
            'min_word_length': 2,     # 最小词长
            'max_word_length': 20     # 最大词长
        }
        
        # 垃圾评论过滤规则
        self.spam_patterns = [
            r'(.)\1{4,}',  # 重复字符
            r'[^\u4e00-\u9fa5a-zA-Z0-9\s\.,!?，。！？]',  # 特殊字符
            r'(微信|QQ|加我|私聊|联系)',  # 广告词
        ]
        self.spam_regex = [re.compile(pattern) for pattern in self.spam_patterns]
        
        # 情感词典（简化版）
        self.sentiment_dict = {
            'positive': ['好', '棒', '赞', '喜欢', '爱', '优秀', '完美', '满意', '开心', '高兴'],
            'negative': ['差', '烂', '垃圾', '讨厌', '恨', '失望', '糟糕', '不满', '生气', '愤怒'],
            'neutral': ['一般', '还行', '普通', '平常', '正常', '可以', '行吧', '凑合']
        }
        
        # 词汇分类
        self.word_categories = {
            'product': ['产品', '商品', '价格', '质量', '功能', '效果', '材质', '品牌'],
            'emotion': ['喜欢', '爱', '讨厌', '恨', '开心', '生气', '满意', '失望'],
            'question': ['怎么', '什么', '哪里', '为什么', '如何', '多少', '几个', '什么时候'],
            'interaction': ['主播', '老师', '老板', '美女', '帅哥', '大家', '朋友们']
        }
    
    def start(self):
        """启动评论处理器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.stats['start_time'] = datetime.now()
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        print(f"[{format_time()}] 评论处理器已启动")
    
    def stop(self):
        """停止评论处理器"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        print(f"[{format_time()}] 评论处理器已停止")
    
    def add_comment(self, comment_data: Dict[str, Any]) -> bool:
        """添加评论到处理队列"""
        try:
            # 数据清理和验证
            cleaned_data = sanitize_input(comment_data)
            validated_data = validate_comment(cleaned_data)
            
            # 添加时间戳
            if 'timestamp' not in validated_data or not validated_data['timestamp']:
                validated_data['timestamp'] = datetime.now()
            
            # 添加到队列
            self.comment_queue.append(validated_data)
            self.stats['total_comments'] += 1
            self.stats['last_comment_time'] = datetime.now()
            
            return True
            
        except Exception as e:
            self.stats['error_comments'] += 1
            print(f"[{format_time()}] 添加评论失败: {e}")
            return False
    
    def add_callback(self, callback: Callable[[Comment], None]):
        """添加评论处理回调函数"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[Comment], None]):
        """移除评论处理回调函数"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        stats = self.stats.copy()
        stats['queue_size'] = len(self.comment_queue)
        stats['hot_words_count'] = len(self.hot_words)
        stats['is_running'] = self.is_running
        
        if stats['start_time']:
            runtime = datetime.now() - stats['start_time']
            stats['runtime_seconds'] = runtime.total_seconds()
            stats['comments_per_minute'] = (stats['processed_comments'] / max(runtime.total_seconds() / 60, 1))
        
        return stats
    
    def get_hot_words(self, limit: int = 20, category: str = None) -> List[Dict[str, Any]]:
        """获取热词列表"""
        # 过滤和排序
        filtered_words = []
        for word, count in self.hot_words.items():
            if count >= self.config['hot_word_threshold']:
                word_category = self._classify_word(word)
                if category is None or word_category == category:
                    trend = self._calculate_trend(word)
                    filtered_words.append({
                        'word': word,
                        'count': count,
                        'category': word_category,
                        'trend': trend,
                        'last_updated': datetime.now()
                    })
        
        # 按计数排序
        filtered_words.sort(key=lambda x: x['count'], reverse=True)
        return filtered_words[:limit]
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        self.config.update(new_config)
        print(f"[{format_time()}] 评论处理器配置已更新")
    
    def clear_data(self):
        """清空数据"""
        self.comment_queue.clear()
        self.hot_words.clear()
        self.word_trends.clear()
        self.stats = {
            'total_comments': 0,
            'processed_comments': 0,
            'error_comments': 0,
            'start_time': self.stats.get('start_time'),
            'last_comment_time': None
        }
        print(f"[{format_time()}] 评论处理器数据已清空")
    
    def _processing_loop(self):
        """处理循环"""
        last_cleanup = time.time()
        
        while self.is_running:
            try:
                # 批量处理评论
                batch = []
                for _ in range(self.config['batch_size']):
                    if self.comment_queue:
                        batch.append(self.comment_queue.popleft())
                    else:
                        break
                
                if batch:
                    self._process_batch(batch)
                
                # 定期清理
                current_time = time.time()
                if current_time - last_cleanup > self.config['cleanup_interval']:
                    self._cleanup_old_data()
                    last_cleanup = current_time
                
                # 短暂休眠
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[{format_time()}] 处理循环错误: {e}")
                time.sleep(1)
    
    def _process_batch(self, batch: List[Dict[str, Any]]):
        """批量处理评论"""
        for comment_data in batch:
            try:
                comment = self._process_single_comment(comment_data)
                if comment:
                    # 保存到数据管理器
                    data_manager.add_comment(comment)
                    
                    # 调用回调函数
                    for callback in self.callbacks:
                        try:
                            callback(comment)
                        except Exception as e:
                            print(f"[{format_time()}] 回调函数错误: {e}")
                    
                    self.stats['processed_comments'] += 1
                
            except Exception as e:
                self.stats['error_comments'] += 1
                print(f"[{format_time()}] 处理评论错误: {e}")
    
    def _process_single_comment(self, comment_data: Dict[str, Any]) -> Optional[Comment]:
        """处理单个评论"""
        try:
            # 垃圾评论过滤
            if self.config['filter_spam'] and self._is_spam(comment_data['content']):
                return None
            
            # 创建评论对象
            comment = Comment(
                user=comment_data['user'],
                content=comment_data['content'],
                timestamp=comment_data.get('timestamp', datetime.now()),
                platform=comment_data.get('platform', 'unknown'),
                user_level=comment_data.get('user_level', 0),
                is_vip=comment_data.get('is_vip', False),
                gift_count=comment_data.get('gift_count', 0)
            )
            
            # 情感分析
            if self.config['enable_sentiment']:
                comment.sentiment = self._analyze_sentiment(comment.content)
            
            # 提取和统计热词
            self._extract_hot_words(comment.content)
            
            return comment
            
        except Exception as e:
            print(f"[{format_time()}] 处理评论失败: {e}")
            return None
    
    def _is_spam(self, content: str) -> bool:
        """检查是否为垃圾评论"""
        # 长度检查
        if len(content) < 2 or len(content) > 500:
            return True
        
        # 正则匹配
        for regex in self.spam_regex:
            if regex.search(content):
                return True
        
        return False
    
    def _analyze_sentiment(self, content: str) -> str:
        """分析情感"""
        positive_score = 0
        negative_score = 0
        
        for word in self.sentiment_dict['positive']:
            positive_score += content.count(word)
        
        for word in self.sentiment_dict['negative']:
            negative_score += content.count(word)
        
        if positive_score > negative_score:
            return 'positive'
        elif negative_score > positive_score:
            return 'negative'
        else:
            return 'neutral'
    
    def _extract_hot_words(self, content: str):
        """提取热词"""
        # 简单的词汇提取（可以使用jieba等分词库优化）
        words = re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', content)
        
        current_time = time.time()
        
        for word in words:
            # 长度过滤
            if (len(word) < self.config['min_word_length'] or 
                len(word) > self.config['max_word_length']):
                continue
            
            # 更新计数
            self.hot_words[word] += 1
            
            # 记录趋势
            if word not in self.word_trends:
                self.word_trends[word] = []
            self.word_trends[word].append(current_time)
            
            # 限制趋势数据长度
            if len(self.word_trends[word]) > 100:
                self.word_trends[word] = self.word_trends[word][-50:]
    
    def _classify_word(self, word: str) -> str:
        """分类词汇"""
        for category, keywords in self.word_categories.items():
            if any(keyword in word for keyword in keywords):
                return category
        return 'other'
    
    def _calculate_trend(self, word: str) -> str:
        """计算词汇趋势"""
        if word not in self.word_trends:
            return 'stable'
        
        timestamps = self.word_trends[word]
        if len(timestamps) < 2:
            return 'stable'
        
        current_time = time.time()
        window_start = current_time - self.config['trend_window']
        
        # 计算窗口内的出现次数
        recent_count = sum(1 for t in timestamps if t >= window_start)
        total_count = len(timestamps)
        
        if total_count < 5:
            return 'stable'
        
        recent_ratio = recent_count / min(total_count, 10)
        
        if recent_ratio > 0.7:
            return 'up'
        elif recent_ratio < 0.3:
            return 'down'
        else:
            return 'stable'
    
    def _cleanup_old_data(self):
        """清理旧数据"""
        current_time = time.time()
        cutoff_time = current_time - self.config['trend_window'] * 2
        
        # 清理趋势数据
        for word in list(self.word_trends.keys()):
            timestamps = self.word_trends[word]
            # 保留最近的时间戳
            recent_timestamps = [t for t in timestamps if t >= cutoff_time]
            
            if recent_timestamps:
                self.word_trends[word] = recent_timestamps
            else:
                # 如果没有最近的数据，删除该词
                del self.word_trends[word]
                if word in self.hot_words:
                    del self.hot_words[word]
        
        # 限制热词数量
        if len(self.hot_words) > self.config['max_hot_words']:
            # 保留计数最高的词
            sorted_words = sorted(self.hot_words.items(), key=lambda x: x[1], reverse=True)
            self.hot_words = dict(sorted_words[:self.config['max_hot_words']])
        
        print(f"[{format_time()}] 数据清理完成，当前热词数量: {len(self.hot_words)}")


class CommentSimulator:
    """评论模拟器（用于测试）"""
    
    def __init__(self, processor: CommentProcessor):
        self.processor = processor
        self.is_running = False
        self.simulation_thread = None
        
        # 模拟数据
        self.sample_users = ['用户A', '小明', '张三', '李四', '王五', '赵六', '直播粉丝', '路人甲']
        self.sample_comments = [
            '这个产品不错啊',
            '主播好漂亮',
            '价格怎么样？',
            '质量好吗',
            '我要买一个',
            '什么时候发货',
            '有优惠吗',
            '支持主播',
            '666',
            '赞一个',
            '这个颜色我喜欢',
            '多少钱啊',
            '包邮吗',
            '有现货吗'
        ]
        self.platforms = ['douyin', 'kuaishou', 'bilibili']
    
    def start_simulation(self, interval: float = 2.0):
        """开始模拟评论"""
        if self.is_running:
            return
        
        self.is_running = True
        self.simulation_thread = threading.Thread(
            target=self._simulation_loop, 
            args=(interval,), 
            daemon=True
        )
        self.simulation_thread.start()
        print(f"[{format_time()}] 评论模拟器已启动，间隔: {interval}秒")
    
    def stop_simulation(self):
        """停止模拟评论"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.simulation_thread:
            self.simulation_thread.join(timeout=5)
        print(f"[{format_time()}] 评论模拟器已停止")
    
    def _simulation_loop(self, interval: float):
        """模拟循环"""
        import random
        
        while self.is_running:
            try:
                # 生成随机评论
                comment_data = {
                    'user': random.choice(self.sample_users),
                    'content': random.choice(self.sample_comments),
                    'platform': random.choice(self.platforms),
                    'user_level': random.randint(1, 50),
                    'is_vip': random.choice([True, False]),
                    'gift_count': random.randint(0, 10)
                }
                
                # 添加到处理器
                self.processor.add_comment(comment_data)
                
                # 随机间隔
                actual_interval = interval * random.uniform(0.5, 1.5)
                time.sleep(actual_interval)
                
            except Exception as e:
                print(f"[{format_time()}] 模拟器错误: {e}")
                time.sleep(1)


# 全局评论处理器实例
comment_processor = CommentProcessor()


def start_comment_processing():
    """启动评论处理"""
    comment_processor.start()


def stop_comment_processing():
    """停止评论处理"""
    comment_processor.stop()


def add_comment(comment_data: Dict[str, Any]) -> bool:
    """添加评论"""
    return comment_processor.add_comment(comment_data)


def get_processing_stats() -> Dict[str, Any]:
    """获取处理统计"""
    return comment_processor.get_stats()


def get_hot_words(limit: int = 20, category: str = None) -> List[Dict[str, Any]]:
    """获取热词"""
    return comment_processor.get_hot_words(limit, category)