#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能置信度计算器
为情感博主语音识别场景优化的多维度置信度计算组件

主要功能:
1. 多维度置信度计算
2. 词频权重分析
3. 上下文连贯性评分
4. 音频质量影响因子
5. 情感特征加成计算
"""

import re
import math
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import numpy as np
from enhanced_transcription_result import (
    ConfidenceBreakdown, 
    AudioQuality, 
    EmotionalFeatures,
    WordAnalysis
)

# 置信度计算常量
MIN_CONFIDENCE = 0.0
MAX_CONFIDENCE = 1.0
EMOTION_BOOST_CAP = 0.15  # 情感加成上限15%
CONTEXT_WINDOW_SIZE = 5   # 上下文窗口大小

@dataclass
class ConfidenceWeights:
    """置信度权重配置"""
    vosk_weight: float = 0.4          # VOSK原始置信度权重
    word_frequency_weight: float = 0.25   # 词频权重
    context_coherence_weight: float = 0.2  # 上下文连贯性权重  
    audio_quality_weight: float = 0.15    # 音频质量权重
    
    def __post_init__(self):
        """权重归一化"""
        total = self.vosk_weight + self.word_frequency_weight + self.context_coherence_weight + self.audio_quality_weight
        if total != 1.0:
            # 归一化权重
            factor = 1.0 / total
            self.vosk_weight *= factor
            self.word_frequency_weight *= factor
            self.context_coherence_weight *= factor
            self.audio_quality_weight *= factor

class ChineseWordFrequencyAnalyzer:
    """中文词频分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 情感博主常用词汇频率数据 (基于直播场景)
        self.emotion_words_freq = {
            # 高频情感词汇
            "开心": 0.95, "喜欢": 0.92, "爱": 0.90, "美": 0.88, "好": 0.85,
            "棒": 0.82, "赞": 0.80, "优秀": 0.78, "完美": 0.75, "惊艳": 0.72,
            
            # 中频情感词汇  
            "感动": 0.68, "温暖": 0.65, "舒服": 0.62, "满意": 0.60, "期待": 0.58,
            "激动": 0.55, "兴奋": 0.52, "开朗": 0.50, "乐观": 0.48, "积极": 0.45,
            
            # 低频但重要的情感词汇
            "惊喜": 0.42, "治愈": 0.40, "幸福": 0.38, "甜蜜": 0.35, "浪漫": 0.32,
            "感恩": 0.30, "珍惜": 0.28, "温柔": 0.25, "纯真": 0.22, "清新": 0.20
        }
        
        # 直播产品相关词汇
        self.product_words_freq = {
            # 化妆品类
            "口红": 0.95, "面膜": 0.92, "粉底": 0.88, "眼影": 0.85, "睫毛膏": 0.82,
            "护肤": 0.80, "精华": 0.78, "乳液": 0.75, "洁面": 0.72, "防晒": 0.70,
            
            # 服装配饰
            "衣服": 0.90, "裙子": 0.88, "包包": 0.85, "鞋子": 0.82, "首饰": 0.78,
            "帽子": 0.75, "围巾": 0.70, "手表": 0.68, "耳环": 0.65, "项链": 0.62,
            
            # 生活用品
            "杯子": 0.65, "毛巾": 0.62, "枕头": 0.60, "被子": 0.58, "香水": 0.85,
            "蜡烛": 0.55, "花瓶": 0.52, "抱枕": 0.50, "台灯": 0.48, "相框": 0.45
        }
        
        # 网络用语词汇
        self.slang_words_freq = {
            # 高频网络用语
            "绝了": 0.88, "yyds": 0.85, "爱了": 0.82, "太棒了": 0.80, "超级": 0.78,
            "巨": 0.75, "贼": 0.72, "真的": 0.90, "哇": 0.88, "噢": 0.85,
            
            # 年轻人常用词
            "妙啊": 0.70, "绝绝子": 0.68, "奥利给": 0.65, "冲鸭": 0.62, "加油": 0.92,
            "来了": 0.75, "走起": 0.68, "安排": 0.70, "搞定": 0.65, "完美": 0.88
        }
        
        # 通用高频词汇
        self.common_words_freq = {
            # 功能词
            "的": 1.0, "是": 0.98, "在": 0.95, "了": 0.92, "有": 0.90,
            "和": 0.88, "就": 0.85, "都": 0.82, "会": 0.80, "说": 0.78,
            "可以": 0.92, "这个": 0.90, "那个": 0.85, "什么": 0.82, "怎么": 0.80,
            
            # 代词和指示词  
            "我": 0.95, "你": 0.92, "他": 0.88, "她": 0.88, "它": 0.85,
            "这": 0.90, "那": 0.88, "哪": 0.82, "谁": 0.80, "什么": 0.85
        }
        
        # 合并所有词频数据
        self.word_freq_db = {}
        self.word_freq_db.update(self.emotion_words_freq)
        self.word_freq_db.update(self.product_words_freq)
        self.word_freq_db.update(self.slang_words_freq)
        self.word_freq_db.update(self.common_words_freq)
        
        self.logger.info(f"词频数据库已加载，包含{len(self.word_freq_db)}个词汇")
    
    def get_word_frequency_score(self, word: str) -> float:
        """获取单词的频率评分"""
        # 直接查找
        if word in self.word_freq_db:
            return self.word_freq_db[word]
        
        # 处理数字
        if re.match(r'^\d+$', word):
            return 0.6  # 数字有一定的可信度
        
        # 处理英文字母
        if re.match(r'^[a-zA-Z]+$', word):
            return 0.4  # 英文词汇较低可信度
        
        # 处理单字符
        if len(word) == 1:
            if word in "的了是在有和":
                return 0.9  # 高频单字符
            return 0.3  # 其他单字符
        
        # 处理长词汇（可能是复合词）
        if len(word) >= 4:
            # 检查是否包含已知词汇
            max_score = 0.0
            for known_word in self.word_freq_db:
                if known_word in word or word in known_word:
                    max_score = max(max_score, self.word_freq_db[known_word] * 0.8)
            
            if max_score > 0:
                return max_score
            
            # 复合词默认中等评分
            return 0.5
        
        # 未知词汇默认评分
        return 0.2
    
    def analyze_text_frequency(self, text: str, words: List[str]) -> Dict[str, float]:
        """分析文本的词频分布"""
        word_scores = {}
        
        for word in words:
            # 获取基础频率评分
            base_score = self.get_word_frequency_score(word)
            
            # 考虑词在句子中的重要性
            position_factor = self._calculate_position_importance(word, text)
            length_factor = self._calculate_length_factor(word)
            
            # 综合评分
            final_score = base_score * position_factor * length_factor
            word_scores[word] = min(final_score, 1.0)
        
        return word_scores
    
    def _calculate_position_importance(self, word: str, text: str) -> float:
        """计算词汇在文本中的位置重要性"""
        text_length = len(text)
        if text_length == 0:
            return 1.0
        
        word_pos = text.find(word)
        if word_pos == -1:
            return 1.0
        
        # 句首和句尾的词汇稍微重要一些
        relative_pos = word_pos / text_length
        
        if relative_pos < 0.2 or relative_pos > 0.8:
            return 1.1  # 句首句尾加权
        else:
            return 1.0  # 句中正常权重
    
    def _calculate_length_factor(self, word: str) -> float:
        """计算词长度因子"""
        length = len(word)
        
        if length == 1:
            return 0.8  # 单字符稍微降权
        elif length == 2:
            return 1.0  # 双字符正常
        elif length == 3:
            return 1.1  # 三字符稍微加权
        elif length >= 4:
            return 1.2  # 长词汇加权
        else:
            return 0.5

class ContextCoherenceAnalyzer:
    """上下文连贯性分析器"""
    
    def __init__(self, window_size: int = CONTEXT_WINDOW_SIZE):
        self.window_size = window_size
        self.logger = logging.getLogger(__name__)
        
        # 上下文相关性词汇模式
        self.context_patterns = {
            # 因果关系
            "causal": ["因为", "所以", "由于", "导致", "造成", "结果"],
            # 转折关系
            "contrast": ["但是", "不过", "然而", "可是", "却", "而"],
            # 递进关系
            "progressive": ["而且", "并且", "另外", "还有", "更", "甚至"],
            # 总结关系
            "summary": ["总之", "综上", "简而言之", "总的来说", "最后"],
            # 举例关系
            "example": ["比如", "例如", "像", "诸如", "好比"]
        }
        
        # 情感博主特定的话语模式
        self.blogger_patterns = {
            "product_intro": ["这款", "今天给大家", "推荐", "介绍", "这个"],
            "emotion_express": ["真的", "太", "超级", "非常", "特别"],
            "interaction": ["大家", "朋友们", "亲们", "小仙女们", "宝贝们"],
            "time_sequence": ["首先", "然后", "接着", "最后", "现在"]
        }
    
    def calculate_coherence_score(self, words: List[str], 
                                 context_history: Optional[List[str]] = None) -> float:
        """计算上下文连贯性评分"""
        if not words:
            return 0.0
        
        # 1. 内部连贯性 (句内词汇关联)
        internal_score = self._calculate_internal_coherence(words)
        
        # 2. 外部连贯性 (与历史上下文关联)
        external_score = 0.5  # 默认中等分数
        if context_history:
            external_score = self._calculate_external_coherence(words, context_history)
        
        # 3. 语义模式匹配
        pattern_score = self._calculate_pattern_matching(words)
        
        # 综合评分
        coherence_score = (internal_score * 0.4 + 
                          external_score * 0.35 + 
                          pattern_score * 0.25)
        
        return min(max(coherence_score, 0.0), 1.0)
    
    def _calculate_internal_coherence(self, words: List[str]) -> float:
        """计算句内连贯性"""
        if len(words) <= 1:
            return 0.5
        
        coherence_indicators = 0
        total_pairs = len(words) - 1
        
        for i in range(len(words) - 1):
            current_word = words[i]
            next_word = words[i + 1]
            
            # 检查常见的词汇搭配
            if self._is_common_collocation(current_word, next_word):
                coherence_indicators += 1
            
            # 检查语法结构
            if self._follows_grammar_pattern(current_word, next_word):
                coherence_indicators += 1
        
        # 计算连贯性比例
        if total_pairs == 0:
            return 0.5
        
        coherence_ratio = coherence_indicators / (total_pairs * 2)  # 每对词最多2个指标
        return min(coherence_ratio + 0.3, 1.0)  # 基础分0.3
    
    def _calculate_external_coherence(self, words: List[str], 
                                    context_history: List[str]) -> float:
        """计算与历史上下文的连贯性"""
        if not context_history:
            return 0.5
        
        # 取最近的上下文
        recent_context = context_history[-self.window_size:]
        
        # 计算词汇重叠
        current_set = set(words)
        context_set = set(recent_context)
        
        # 直接重叠
        overlap = len(current_set & context_set)
        overlap_score = min(overlap / len(current_set) if current_set else 0, 0.6)
        
        # 语义相关性 (简单版本)
        semantic_score = self._calculate_semantic_similarity(words, recent_context)
        
        return (overlap_score + semantic_score) / 2
    
    def _calculate_pattern_matching(self, words: List[str]) -> float:
        """计算语义模式匹配度"""
        text = "".join(words)
        
        pattern_matches = 0
        total_patterns = 0
        
        # 检查上下文模式
        for pattern_type, patterns in self.context_patterns.items():
            total_patterns += len(patterns)
            for pattern in patterns:
                if pattern in text:
                    pattern_matches += 1
        
        # 检查博主特定模式
        for pattern_type, patterns in self.blogger_patterns.items():
            total_patterns += len(patterns)
            for pattern in patterns:
                if pattern in text:
                    pattern_matches += 2  # 博主特定模式加权
        
        if total_patterns == 0:
            return 0.5
        
        pattern_score = min(pattern_matches / total_patterns, 1.0)
        return max(pattern_score, 0.3)  # 最低保证分
    
    def _is_common_collocation(self, word1: str, word2: str) -> bool:
        """检查是否为常见搭配"""
        # 常见搭配模式
        common_pairs = {
            ("真的", "很"), ("非常", "好"), ("特别", "棒"), ("超级", "喜欢"),
            ("这个", "是"), ("那个", "不"), ("我们", "的"), ("大家", "好"),
            ("今天", "给"), ("现在", "开始"), ("接下来", "我们"), ("最后", "说")
        }
        
        return (word1, word2) in common_pairs
    
    def _follows_grammar_pattern(self, word1: str, word2: str) -> bool:
        """检查是否符合语法模式"""
        # 简单的语法模式检查
        
        # 代词 + 动词
        if word1 in ["我", "你", "他", "她"] and word2 in ["是", "有", "会", "说", "做"]:
            return True
        
        # 形容词 + 名词
        if word1 in ["好", "美", "棒", "新", "大"] and len(word2) >= 2:
            return True
        
        # 数量词 + 量词
        if re.match(r'^\d+$', word1) and word2 in ["个", "只", "件", "支", "瓶"]:
            return True
        
        return False
    
    def _calculate_semantic_similarity(self, words1: List[str], 
                                     words2: List[str]) -> float:
        """计算语义相似性(简化版)"""
        # 这里实现简化的语义相似性计算
        # 在实际应用中可能需要更复杂的NLP模型
        
        # 基于词汇分类的相似性
        categories = {
            "emotion": {"开心", "喜欢", "爱", "好", "美", "棒", "赞"},
            "product": {"口红", "面膜", "衣服", "包包", "鞋子"},
            "action": {"看", "买", "用", "试", "推荐", "介绍"},
            "time": {"今天", "现在", "接下来", "最后", "然后"}
        }
        
        cat1 = self._categorize_words(words1, categories)
        cat2 = self._categorize_words(words2, categories)
        
        # 计算类别重叠度
        common_cats = len(set(cat1.keys()) & set(cat2.keys()))
        total_cats = len(set(cat1.keys()) | set(cat2.keys()))
        
        if total_cats == 0:
            return 0.3
        
        return min(common_cats / total_cats + 0.2, 1.0)
    
    def _categorize_words(self, words: List[str], 
                         categories: Dict[str, set]) -> Dict[str, int]:
        """对词汇进行分类"""
        word_categories = defaultdict(int)
        
        for word in words:
            for cat_name, cat_words in categories.items():
                if word in cat_words:
                    word_categories[cat_name] += 1
        
        return dict(word_categories)

class IntelligentConfidenceCalculator:
    """智能置信度计算器
    
    整合多维度置信度计算，为情感博主场景提供精确的置信度评估
    """
    
    def __init__(self, weights: Optional[ConfidenceWeights] = None):
        self.weights = weights or ConfidenceWeights()
        self.word_analyzer = ChineseWordFrequencyAnalyzer()
        self.context_analyzer = ContextCoherenceAnalyzer()
        
        # 历史上下文缓存
        self.context_history = []
        self.max_history_size = 50  # 保持最近50个词汇
        
        # 统计数据
        self.calculation_stats = {
            "total_calculations": 0,
            "average_vosk_confidence": 0.0,
            "average_final_confidence": 0.0,
            "confidence_boost_count": 0,
            "confidence_decrease_count": 0
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("智能置信度计算器已初始化")
    
    def calculate_enhanced_confidence(self, 
                                    text: str,
                                    vosk_confidence: float,
                                    words: Optional[List[WordAnalysis]] = None,
                                    audio_quality: Optional[AudioQuality] = None,
                                    emotional_features: Optional[EmotionalFeatures] = None) -> ConfidenceBreakdown:
        """计算增强版置信度"""
        try:
            # 1. 标准化VOSK置信度
            normalized_vosk = max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, vosk_confidence))
            
            # 2. 提取词汇列表
            word_list = []
            if words:
                word_list = [w.word for w in words]
            else:
                # 简单分词 (实际应用中应使用专业分词工具)
                word_list = self._simple_tokenize(text)
            
            # 3. 计算各维度评分
            word_freq_score = self._calculate_word_frequency_score(text, word_list)
            context_score = self._calculate_context_coherence_score(word_list)
            audio_quality_score = self._calculate_audio_quality_score(audio_quality)
            emotion_boost = self._calculate_emotion_boost(emotional_features, text)
            
            # 4. 加权计算最终置信度
            weighted_confidence = (
                normalized_vosk * self.weights.vosk_weight +
                word_freq_score * self.weights.word_frequency_weight +
                context_score * self.weights.context_coherence_weight +
                audio_quality_score * self.weights.audio_quality_weight
            )
            
            # 5. 应用情感加成
            final_confidence = min(weighted_confidence + emotion_boost, MAX_CONFIDENCE)
            
            # 6. 更新上下文历史
            self._update_context_history(word_list)
            
            # 7. 更新统计数据
            self._update_statistics(normalized_vosk, final_confidence)
            
            # 8. 创建置信度分解结果
            breakdown = ConfidenceBreakdown(
                vosk_confidence=normalized_vosk,
                word_frequency_score=word_freq_score,
                context_coherence_score=context_score,
                audio_quality_score=audio_quality_score,
                emotion_boost=emotion_boost,
                final_confidence=final_confidence
            )
            
            return breakdown
            
        except Exception as e:
            self.logger.error(f"置信度计算失败: {e}")
            # 失败时返回基于VOSK的基础结果
            return ConfidenceBreakdown(
                vosk_confidence=vosk_confidence,
                word_frequency_score=0.5,
                context_coherence_score=0.5,
                audio_quality_score=0.5,
                emotion_boost=0.0,
                final_confidence=vosk_confidence
            )
    
    def _simple_tokenize(self, text: str) -> List[str]:
        """简单中文分词 (实际应用中应使用jieba等专业工具)"""
        # 移除标点符号
        clean_text = re.sub(r'[^\w\s]', '', text)
        
        # 按空格分割
        words = clean_text.split()
        
        # 对中文进行简单分割(每2-3个字符一组)
        result = []
        for word in words:
            if len(word) <= 3:
                result.append(word)
            else:
                # 长词分割
                for i in range(0, len(word), 2):
                    if i + 2 <= len(word):
                        result.append(word[i:i+2])
                    else:
                        result.append(word[i:])
        
        return [w for w in result if w.strip()]
    
    def _calculate_word_frequency_score(self, text: str, words: List[str]) -> float:
        """计算词频评分"""
        if not words:
            return 0.5
        
        word_scores = self.word_analyzer.analyze_text_frequency(text, words)
        
        # 计算加权平均分
        total_score = sum(word_scores.values())
        avg_score = total_score / len(word_scores) if word_scores else 0.5
        
        return min(max(avg_score, 0.0), 1.0)
    
    def _calculate_context_coherence_score(self, words: List[str]) -> float:
        """计算上下文连贯性评分"""
        return self.context_analyzer.calculate_coherence_score(words, self.context_history)
    
    def _calculate_audio_quality_score(self, audio_quality: Optional[AudioQuality]) -> float:
        """计算音频质量评分"""
        if not audio_quality:
            return 0.5  # 默认中等质量
        
        # 综合音频质量指标
        quality_score = (
            (1.0 - audio_quality.noise_level) * 0.4 +  # 噪音越低越好
            audio_quality.volume_level * 0.3 +         # 音量适中越好
            audio_quality.clarity_score * 0.3          # 清晰度越高越好
        )
        
        return min(max(quality_score, 0.0), 1.0)
    
    def _calculate_emotion_boost(self, emotional_features: Optional[EmotionalFeatures], 
                               text: str) -> float:
        """计算情感特征加成"""
        emotion_boost = 0.0
        
        if emotional_features:
            # 基于情感强度和置信度的加成
            emotion_factor = (
                emotional_features.intensity * 
                emotional_features.tone_confidence * 
                0.5  # 基础加成系数
            )
            emotion_boost += emotion_factor
        
        # 基于文本情感词汇的加成
        emotion_words_count = 0
        for word in self.word_analyzer.emotion_words_freq:
            if word in text:
                emotion_words_count += 1
        
        if emotion_words_count > 0:
            text_emotion_boost = min(emotion_words_count * 0.02, 0.08)  # 每个情感词2%，最处8%
            emotion_boost += text_emotion_boost
        
        return min(emotion_boost, EMOTION_BOOST_CAP)
    
    def _update_context_history(self, words: List[str]):
        """更新上下文历史"""
        self.context_history.extend(words)
        
        # 保持历史大小
        if len(self.context_history) > self.max_history_size:
            self.context_history = self.context_history[-self.max_history_size:]
    
    def _update_statistics(self, vosk_confidence: float, final_confidence: float):
        """更新统计数据"""
        self.calculation_stats["total_calculations"] += 1
        
        # 更新平均值
        count = self.calculation_stats["total_calculations"]
        prev_avg_vosk = self.calculation_stats["average_vosk_confidence"]
        prev_avg_final = self.calculation_stats["average_final_confidence"]
        
        self.calculation_stats["average_vosk_confidence"] = (
            (prev_avg_vosk * (count - 1) + vosk_confidence) / count
        )
        self.calculation_stats["average_final_confidence"] = (
            (prev_avg_final * (count - 1) + final_confidence) / count
        )
        
        # 统计提升/降低次数
        if final_confidence > vosk_confidence:
            self.calculation_stats["confidence_boost_count"] += 1
        elif final_confidence < vosk_confidence:
            self.calculation_stats["confidence_decrease_count"] += 1
    
    def get_calculation_stats(self) -> Dict[str, Any]:
        """获取计算统计信息"""
        stats = self.calculation_stats.copy()
        
        # 计算额外指标
        total = stats["total_calculations"]
        if total > 0:
            stats["boost_percentage"] = stats["confidence_boost_count"] / total * 100
            stats["decrease_percentage"] = stats["confidence_decrease_count"] / total * 100
            stats["improvement_rate"] = (
                stats["average_final_confidence"] - stats["average_vosk_confidence"]
            )
        else:
            stats["boost_percentage"] = 0.0
            stats["decrease_percentage"] = 0.0
            stats["improvement_rate"] = 0.0
        
        # 添加上下文信息
        stats["context_history_size"] = len(self.context_history)
        stats["word_freq_db_size"] = len(self.word_analyzer.word_freq_db)
        
        return stats
    
    def reset_context_history(self):
        """重置上下文历史"""
        self.context_history.clear()
        self.logger.info("上下文历史已重置")
    
    def reset_statistics(self):
        """重置统计数据"""
        self.calculation_stats = {
            "total_calculations": 0,
            "average_vosk_confidence": 0.0,
            "average_final_confidence": 0.0,
            "confidence_boost_count": 0,
            "confidence_decrease_count": 0
        }
        self.logger.info("计算统计数据已重置")

# 导出主要类
__all__ = [
    'IntelligentConfidenceCalculator',
    'ConfidenceWeights',
    'ChineseWordFrequencyAnalyzer',
    'ContextCoherenceAnalyzer'
]