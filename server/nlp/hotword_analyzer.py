"""
提猫直播助手 - 热词分析模块
负责分析评论中的热词和关键词
"""

import jieba
import jieba.analyse
from collections import Counter, defaultdict
from typing import List, Dict, Any, Set
import re
import time
from server.utils.logger import LoggerMixin


class HotwordAnalyzer(LoggerMixin):
    """热词分析器"""
    
    def __init__(self, config=None):
        self.config = config
        self.stop_words = self._load_stop_words()
        self.word_cache = defaultdict(int)
        self.phrase_cache = defaultdict(int)
        self.last_update = time.time()
        self.cache_ttl = 300  # 5分钟缓存
        self.is_running = False  # 添加运行状态标志
        
        # 初始化jieba
        jieba.initialize()
        self.logger.info("热词分析器初始化完成")
    
    def _load_stop_words(self) -> Set[str]:
        """加载停用词"""
        # 基础停用词列表
        stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '什么',
            '啊', '哦', '嗯', '呢', '吧', '哈', '嘿', '额', '呃', '唉',
            '666', '233', '哈哈', '呵呵', '嘻嘻', '哇', '哟', '咦', '咯'
        }
        
        # 直播相关停用词
        live_stop_words = {
            '主播', '直播', '观众', '粉丝', '关注', '点赞', '支持', '加油',
            '厉害', '棒', '不错', '可以', '好的', '谢谢', '感谢'
        }
        
        return stop_words.union(live_stop_words)
    
    def analyze_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析评论中的热词"""
        if not comments:
            return self._empty_result()
        
        # 提取所有评论文本
        texts = [comment.get('content', '') for comment in comments]
        combined_text = ' '.join(texts)
        
        # 分析单词和短语
        words = self._extract_words(combined_text)
        phrases = self._extract_phrases(texts)
        
        # 更新缓存
        self._update_cache(words, phrases)
        
        return {
            'hot_words': self._get_top_words(50),
            'hot_phrases': self._get_top_phrases(20),
            'word_cloud_data': self._get_word_cloud_data(),
            'stats': {
                'total_comments': len(comments),
                'total_words': len(words),
                'unique_words': len(set(words)),
                'last_update': time.time()
            }
        }
    
    def _extract_words(self, text: str) -> List[str]:
        """提取单词"""
        if not text:
            return []
        
        # 清理文本
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', text)
        
        # 分词
        words = jieba.lcut(text)
        
        # 过滤停用词和短词
        filtered_words = [
            word.strip() for word in words
            if len(word.strip()) > 1 and word.strip() not in self.stop_words
        ]
        
        return filtered_words
    
    def _extract_phrases(self, texts: List[str]) -> List[str]:
        """提取短语"""
        phrases = []
        
        for text in texts:
            if not text:
                continue
            
            # 使用TF-IDF提取关键短语
            try:
                keywords = jieba.analyse.textrank(text, topK=5, withWeight=False)
                phrases.extend(keywords)
            except:
                # 如果TF-IDF失败，使用简单的n-gram
                words = self._extract_words(text)
                if len(words) >= 2:
                    # 提取2-gram
                    for i in range(len(words) - 1):
                        phrase = words[i] + words[i + 1]
                        if len(phrase) >= 4:  # 至少4个字符
                            phrases.append(phrase)
        
        return phrases
    
    def _update_cache(self, words: List[str], phrases: List[str]):
        """更新缓存"""
        current_time = time.time()
        
        # 如果缓存过期，清空缓存
        if current_time - self.last_update > self.cache_ttl:
            self.word_cache.clear()
            self.phrase_cache.clear()
        
        # 更新词频
        for word in words:
            self.word_cache[word] += 1
        
        for phrase in phrases:
            self.phrase_cache[phrase] += 1
        
        self.last_update = current_time
    
    def _get_top_words(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取热门单词"""
        if not self.word_cache:
            return []
        
        top_words = Counter(self.word_cache).most_common(limit)
        
        return [
            {
                'word': word,
                'count': count,
                'weight': min(count / max(self.word_cache.values()) * 100, 100)
            }
            for word, count in top_words
        ]
    
    def _get_top_phrases(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取热门短语"""
        if not self.phrase_cache:
            return []
        
        top_phrases = Counter(self.phrase_cache).most_common(limit)
        
        return [
            {
                'phrase': phrase,
                'count': count,
                'weight': min(count / max(self.phrase_cache.values()) * 100, 100)
            }
            for phrase, count in top_phrases
        ]
    
    def _get_word_cloud_data(self) -> List[Dict[str, Any]]:
        """获取词云数据"""
        if not self.word_cache:
            return []
        
        max_count = max(self.word_cache.values()) if self.word_cache else 1
        
        word_cloud_data = []
        for word, count in self.word_cache.items():
            # 计算字体大小（10-50px）
            size = int(10 + (count / max_count) * 40)
            
            word_cloud_data.append({
                'text': word,
                'size': size,
                'count': count
            })
        
        # 按频率排序
        word_cloud_data.sort(key=lambda x: x['count'], reverse=True)
        
        return word_cloud_data[:100]  # 限制数量
    
    def _empty_result(self) -> Dict[str, Any]:
        """空结果"""
        return {
            'hot_words': [],
            'hot_phrases': [],
            'word_cloud_data': [],
            'stats': {
                'total_comments': 0,
                'total_words': 0,
                'unique_words': 0,
                'last_update': time.time()
            }
        }
    
    def get_trending_words(self, time_window: int = 300) -> List[Dict[str, Any]]:
        """获取趋势词汇"""
        # TODO: 实现基于时间窗口的趋势分析
        return self._get_top_words(20)
    
    def clear_cache(self):
        """清空缓存"""
        self.word_cache.clear()
        self.phrase_cache.clear()
        self.last_update = time.time()
        self.logger.info("热词分析缓存已清空")
    
    def get_hotwords(self, limit: int = 10, category: str = None) -> List[Dict[str, Any]]:
        """获取热词列表"""
        try:
            # 获取热门词汇
            hot_words = self._get_top_words(limit)
            
            # 转换为统一格式
            hotwords = []
            for word_data in hot_words:
                hotwords.append({
                    'word': word_data['word'],
                    'count': word_data['count'],
                    'weight': word_data['weight'],
                    'category': category or 'general'
                })
            
            return hotwords
            
        except Exception as e:
            self.logger.error(f"获取热词失败: {e}")
            return []
    
    def start_analyzing(self):
        """启动热词分析（后台任务）"""
        self.is_running = True
        self.logger.info("热词分析任务已启动")
        # 这里可以添加定期分析逻辑
        # 目前只是占位方法，实际分析在API调用时进行