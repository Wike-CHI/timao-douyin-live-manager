#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播词汇后处理器
为情感博主语音识别场景优化的文本后处理组件

主要功能:
1. 情感表达纠错
2. 产品名称标准化
3. 网络用语规范化
4. 语法错误修正
5. 标点符号优化
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict
import difflib
from enhanced_transcription_result import (
    ProcessingType,
    WordAnalysis,
    EmotionType
)

# 后处理常量
MAX_CORRECTION_DISTANCE = 2    # 最大编辑距离
MIN_CONFIDENCE_FOR_CORRECTION = 0.3  # 纠错最小置信度
PRODUCT_BRAND_WEIGHT = 1.5     # 品牌名称权重

@dataclass
class CorrectionRule:
    """纠错规则"""
    pattern: str                # 匹配模式（正则或字符串）
    replacement: str           # 替换内容
    rule_type: str            # 规则类型
    confidence: float         # 规则置信度
    conditions: List[str] = field(default_factory=list)  # 应用条件

@dataclass
class PostProcessingResult:
    """后处理结果"""
    original_text: str         # 原始文本
    processed_text: str        # 处理后文本
    applied_corrections: List[Dict[str, Any]]  # 应用的纠错
    processing_confidence: float  # 处理置信度
    processing_types: List[ProcessingType]  # 处理类型

class EmotionExpressionCorrector:
    """情感表达纠错器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 情感表达纠错词典
        self.emotion_corrections = {
            # 兴奋表达纠错
            "兴奋类": {
                "太棒": "太棒了", "绝": "绝了", "爱": "爱了", 
                "哇塞": "哇", "厉害": "厉害了", "牛": "牛逼",
                "顶": "顶呱呱", "赞": "点赞", "好耶": "好棒"
            },
            
            # 喜爱表达纠错
            "喜爱类": {
                "喜欢死": "超级喜欢", "爱死": "特别爱", "迷": "迷恋",
                "中毒": "中意", "入坑": "喜欢上", "种草": "推荐",
                "心动": "心动了", "沦陷": "沦陷了"
            },
            
            # 惊叹表达纠错
            "惊叹类": {
                "我去": "哇", "卧槽": "哇塞", "我靠": "天哪",
                "我滴": "我的", "妈呀": "天啊", "乖乖": "乖乖"
            },
            
            # 赞美表达纠错
            "赞美类": {
                "神仙": "神仙级别", "宝藏": "宝藏产品", "无敌": "无敌好用",
                "完美": "太完美", "惊艳": "太惊艳", "治愈": "很治愈"
            }
        }
        
        # 语气助词纠错
        self.modal_particles = {
            "啊": ["呀", "哎呀", "哇"],
            "呢": ["嘞", "咧"],
            "的": ["滴", "地"],
            "了": ["啦", "辣"],
            "吧": ["叭", "巴"]
        }
        
        # 构建纠错规则
        self.correction_rules = self._build_correction_rules()
    
    def _build_correction_rules(self) -> List[CorrectionRule]:
        """构建纠错规则"""
        rules = []
        
        # 情感词汇纠错规则
        for category, corrections in self.emotion_corrections.items():
            for wrong, correct in corrections.items():
                rule = CorrectionRule(
                    pattern=wrong,
                    replacement=correct,
                    rule_type="emotion_correction",
                    confidence=0.8,
                    conditions=[f"emotion_context:{category}"]
                )
                rules.append(rule)
        
        # 语气助词纠错规则
        for correct, variants in self.modal_particles.items():
            for variant in variants:
                rule = CorrectionRule(
                    pattern=variant,
                    replacement=correct,
                    rule_type="modal_particle_correction",
                    confidence=0.7
                )
                rules.append(rule)
        
        return rules
    
    def correct_emotion_expressions(self, text: str, 
                                  emotion_type: Optional[EmotionType] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """纠正情感表达
        
        Args:
            text: 输入文本
            emotion_type: 情感类型提示
            
        Returns:
            (纠正后文本, 应用的纠错列表)
        """
        try:
            corrected_text = text
            applied_corrections = []
            
            # 根据情感类型选择相关规则
            relevant_rules = self._filter_rules_by_emotion(emotion_type)
            
            for rule in relevant_rules:
                if rule.pattern in corrected_text:
                    # 应用纠错
                    new_text = corrected_text.replace(rule.pattern, rule.replacement)
                    
                    if new_text != corrected_text:
                        correction = {
                            "type": rule.rule_type,
                            "original": rule.pattern,
                            "corrected": rule.replacement,
                            "confidence": rule.confidence,
                            "position": corrected_text.find(rule.pattern)
                        }
                        applied_corrections.append(correction)
                        corrected_text = new_text
            
            return corrected_text, applied_corrections
            
        except Exception as e:
            self.logger.error(f"情感表达纠错失败: {e}")
            return text, []
    
    def _filter_rules_by_emotion(self, emotion_type: Optional[EmotionType]) -> List[CorrectionRule]:
        """根据情感类型过滤规则"""
        if emotion_type is None:
            return self.correction_rules
        
        # 根据情感类型选择相关规则
        emotion_category_map = {
            EmotionType.EXCITED: ["兴奋类", "惊叹类"],
            EmotionType.JOYFUL: ["喜爱类", "赞美类"],
            EmotionType.NEUTRAL: ["modal_particle_correction"]
        }
        
        relevant_categories = emotion_category_map.get(emotion_type, [])
        
        filtered_rules = []
        for rule in self.correction_rules:
            # 检查规则是否与当前情感相关
            is_relevant = False
            for condition in rule.conditions:
                if any(cat in condition for cat in relevant_categories):
                    is_relevant = True
                    break
            
            if is_relevant or rule.rule_type == "modal_particle_correction":
                filtered_rules.append(rule)
        
        return filtered_rules

class ProductNameStandardizer:
    """产品名称标准化器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 品牌名称标准化词典
        self.brand_standardization = {
            # 化妆品品牌
            "雅诗兰黛": ["雅诗兰代", "雅诗蘭黛", "estee lauder"],
            "兰蔻": ["兰寇", "lancome", "蘭蔻"],
            "迪奥": ["dior", "迪澳", "迪奧"],
            "香奈儿": ["chanel", "香奈尔", "香奈兒"],
            "圣罗兰": ["ysl", "聖羅蘭", "圣罗兰"],
            "阿玛尼": ["armani", "阿瑪尼"],
            "欧莱雅": ["loreal", "歐萊雅", "欧来雅"],
            "cpb": ["肌肤之钥", "cle de peau"],
            "sk2": ["sk-ii", "skii", "sk二"],
            "海蓝之谜": ["la mer", "海藍之謎"],
            
            # 服装品牌
            "古驰": ["gucci", "古奇"],
            "路易威登": ["lv", "louis vuitton", "路易·威登"],
            "爱马仕": ["hermes", "愛馬仕"],
            "普拉达": ["prada", "普拉達"],
            "巴黎世家": ["balenciaga", "巴黎世家"],
            
            # 国产品牌
            "花西子": ["花西孜", "花西紫"],
            "完美日记": ["完美日記", "perfect diary"],
            "薇诺娜": ["薇诺娜", "winona"],
            "自然堂": ["自然堂", "chando"]
        }
        
        # 产品类型标准化
        self.product_type_standardization = {
            "口红": ["唇膏", "lipstick", "lip stick", "唇彩"],
            "粉底": ["foundation", "粉底液", "底妆"],
            "眼影": ["eye shadow", "eyeshadow", "眼影盘"],
            "睫毛膏": ["mascara", "睫毛液"],
            "面膜": ["mask", "面膜纸", "贴片面膜"],
            "精华": ["essence", "serum", "精华液"],
            "乳液": ["lotion", "润肤乳"],
            "防晒": ["sunscreen", "防晒霜", "防晒乳"],
            "卸妆": ["makeup remover", "卸妆水", "卸妆油"]
        }
        
        # 颜色名称标准化
        self.color_standardization = {
            "正红色": ["大红", "正红", "红色"],
            "玫瑰红": ["玫红", "rose", "玫瑰色"],
            "珊瑚红": ["珊瑚色", "coral", "橘红"],
            "豆沙色": ["豆沙", "nude", "裸色"],
            "姨妈红": ["姨妈色", "深红", "暗红"],
            "斩男色": ["斩男", "魅惑红"],
            "咬唇妆": ["咬唇色", "自然红"]
        }
    
    def standardize_product_names(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """标准化产品名称
        
        Args:
            text: 输入文本
            
        Returns:
            (标准化后文本, 应用的标准化列表)
        """
        try:
            standardized_text = text
            applied_standardizations = []
            
            # 1. 品牌名称标准化
            standardized_text, brand_corrections = self._standardize_brands(standardized_text)
            applied_standardizations.extend(brand_corrections)
            
            # 2. 产品类型标准化
            standardized_text, type_corrections = self._standardize_product_types(standardized_text)
            applied_standardizations.extend(type_corrections)
            
            # 3. 颜色名称标准化
            standardized_text, color_corrections = self._standardize_colors(standardized_text)
            applied_standardizations.extend(color_corrections)
            
            return standardized_text, applied_standardizations
            
        except Exception as e:
            self.logger.error(f"产品名称标准化失败: {e}")
            return text, []
    
    def _standardize_brands(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """标准化品牌名称"""
        corrected_text = text
        corrections = []
        
        for standard_name, variants in self.brand_standardization.items():
            for variant in variants:
                # 不区分大小写匹配
                pattern = re.compile(re.escape(variant), re.IGNORECASE)
                matches = pattern.finditer(corrected_text)
                
                for match in matches:
                    correction = {
                        "type": "brand_standardization",
                        "original": match.group(),
                        "corrected": standard_name,
                        "confidence": 0.9,
                        "position": match.start()
                    }
                    corrections.append(correction)
                
                corrected_text = pattern.sub(standard_name, corrected_text)
        
        return corrected_text, corrections
    
    def _standardize_product_types(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """标准化产品类型"""
        corrected_text = text
        corrections = []
        
        for standard_type, variants in self.product_type_standardization.items():
            for variant in variants:
                if variant in corrected_text:
                    correction = {
                        "type": "product_type_standardization",
                        "original": variant,
                        "corrected": standard_type,
                        "confidence": 0.85,
                        "position": corrected_text.find(variant)
                    }
                    corrections.append(correction)
                    corrected_text = corrected_text.replace(variant, standard_type)
        
        return corrected_text, corrections
    
    def _standardize_colors(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """标准化颜色名称"""
        corrected_text = text
        corrections = []
        
        for standard_color, variants in self.color_standardization.items():
            for variant in variants:
                if variant in corrected_text:
                    correction = {
                        "type": "color_standardization",
                        "original": variant,
                        "corrected": standard_color,
                        "confidence": 0.8,
                        "position": corrected_text.find(variant)
                    }
                    corrections.append(correction)
                    corrected_text = corrected_text.replace(variant, standard_color)
        
        return corrected_text, corrections

class SlangNormalizer:
    """网络用语规范化器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 网络用语规范化词典
        self.slang_normalization = {
            # 流行网络用语
            "yyds": "永远的神",
            "绝绝子": "绝了",
            "爱了爱了": "太喜欢了",
            "太绝了": "太棒了",
            "巨好用": "非常好用",
            "贼好看": "特别好看",
            "超A": "超级棒",
            "无敌了": "太厉害了",
            "神仙颜值": "颜值很高",
            "颜值天花板": "颜值最高",
            
            # 购物相关网络用语
            "种草": "推荐",
            "拔草": "买了",
            "长草": "想买",
            "剁手": "购买",
            "入坑": "开始喜欢",
            "安利": "推荐",
            "回购": "再次购买",
            "无限回购": "会一直买",
            
            # 美妆相关网络用语
            "素颜霜": "提亮面霜",
            "猪肝色": "深红色",
            "斩男色": "魅力红色",
            "死亡芭比粉": "亮粉色",
            "姨妈色": "深红色",
            "吃土色": "棕色系",
            
            # 语气强化词
            "巨": "非常",
            "贼": "特别",
            "超": "很",
            "狂": "非常",
            "暴": "特别"
        }
        
        # 缩写词规范化
        self.abbreviation_normalization = {
            "cpb": "肌肤之钥",
            "tf": "汤姆福特",
            "ysl": "圣罗兰",
            "ct": "夏洛特·蒂尔伯里",
            "nars": "纳斯",
            "mac": "魅可",
            "3ce": "三熹玉",
            "vdl": "vdl"
        }
        
        # 表情符号处理
        self.emoji_normalization = {
            "😍": "太喜欢了",
            "🥰": "很可爱",
            "😘": "么么哒",
            "👏": "鼓掌",
            "💕": "喜欢",
            "❤️": "爱",
            "✨": "",  # 装饰性表情删除
            "🌟": "",
            "💖": "爱心"
        }
    
    def normalize_slang(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """规范化网络用语
        
        Args:
            text: 输入文本
            
        Returns:
            (规范化后文本, 应用的规范化列表)
        """
        try:
            normalized_text = text
            applied_normalizations = []
            
            # 1. 网络用语规范化
            normalized_text, slang_corrections = self._normalize_slang_words(normalized_text)
            applied_normalizations.extend(slang_corrections)
            
            # 2. 缩写词规范化
            normalized_text, abbrev_corrections = self._normalize_abbreviations(normalized_text)
            applied_normalizations.extend(abbrev_corrections)
            
            # 3. 表情符号处理
            normalized_text, emoji_corrections = self._normalize_emojis(normalized_text)
            applied_normalizations.extend(emoji_corrections)
            
            return normalized_text, applied_normalizations
            
        except Exception as e:
            self.logger.error(f"网络用语规范化失败: {e}")
            return text, []
    
    def _normalize_slang_words(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """规范化网络用语词汇"""
        normalized_text = text
        corrections = []
        
        # 按词长度排序，优先处理长词汇避免部分匹配
        sorted_slang = sorted(self.slang_normalization.items(), 
                            key=lambda x: len(x[0]), reverse=True)
        
        for slang, formal in sorted_slang:
            if slang in normalized_text:
                correction = {
                    "type": "slang_normalization",
                    "original": slang,
                    "corrected": formal,
                    "confidence": 0.75,
                    "position": normalized_text.find(slang)
                }
                corrections.append(correction)
                normalized_text = normalized_text.replace(slang, formal)
        
        return normalized_text, corrections
    
    def _normalize_abbreviations(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """规范化缩写词"""
        normalized_text = text
        corrections = []
        
        for abbrev, full_name in self.abbreviation_normalization.items():
            # 使用正则匹配独立的缩写词
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            matches = re.finditer(pattern, normalized_text, re.IGNORECASE)
            
            for match in matches:
                correction = {
                    "type": "abbreviation_normalization",
                    "original": match.group(),
                    "corrected": full_name,
                    "confidence": 0.9,
                    "position": match.start()
                }
                corrections.append(correction)
            
            normalized_text = re.sub(pattern, full_name, normalized_text, flags=re.IGNORECASE)
        
        return normalized_text, corrections
    
    def _normalize_emojis(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """规范化表情符号"""
        normalized_text = text
        corrections = []
        
        for emoji, replacement in self.emoji_normalization.items():
            if emoji in normalized_text:
                correction = {
                    "type": "emoji_normalization",
                    "original": emoji,
                    "corrected": replacement,
                    "confidence": 0.6,
                    "position": normalized_text.find(emoji)
                }
                corrections.append(correction)
                normalized_text = normalized_text.replace(emoji, replacement)
        
        return normalized_text, corrections

class GrammarCorrector:
    """语法错误修正器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 常见语法错误模式
        self.grammar_patterns = {
            # 助词错误
            "auxiliary_errors": [
                (r'的很', '很'),  # "的很好" -> "很好"
                (r'的非常', '非常'),
                (r'的特别', '特别'),
                (r'的超级', '超级')
            ],
            
            # 重复词修正
            "repetition_errors": [
                (r'(真的)真的', r'\1'),  # "真的真的" -> "真的"
                (r'(特别)特别', r'\1'),
                (r'(非常)非常', r'\1'),
                (r'(超级)超级', r'\1')
            ],
            
            # 词序错误
            "word_order_errors": [
                (r'好很', '很好'),  # "好很" -> "很好"
                (r'美很', '很美'),
                (r'棒很', '很棒'),
                (r'好看很', '很好看')
            ],
            
            # 介词错误
            "preposition_errors": [
                (r'在这个', '这个'),  # "在这个颜色" -> "这个颜色"
                (r'对这个', '这个'),
                (r'的这个', '这个')
            ]
        }
    
    def correct_grammar(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """修正语法错误
        
        Args:
            text: 输入文本
            
        Returns:
            (修正后文本, 应用的修正列表)
        """
        try:
            corrected_text = text
            applied_corrections = []
            
            # 应用各类语法修正
            for error_type, patterns in self.grammar_patterns.items():
                for pattern, replacement in patterns:
                    matches = list(re.finditer(pattern, corrected_text))
                    for match in reversed(matches):  # 从后向前替换避免位置偏移
                        original = match.group()
                        new_text = re.sub(pattern, replacement, corrected_text)
                        
                        if new_text != corrected_text:
                            correction = {
                                "type": f"grammar_{error_type}",
                                "original": original,
                                "corrected": replacement,
                                "confidence": 0.7,
                                "position": match.start()
                            }
                            applied_corrections.append(correction)
                            corrected_text = new_text
            
            return corrected_text, applied_corrections
            
        except Exception as e:
            self.logger.error(f"语法错误修正失败: {e}")
            return text, []

class PunctuationOptimizer:
    """标点符号优化器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def optimize_punctuation(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """优化标点符号
        
        Args:
            text: 输入文本
            
        Returns:
            (优化后文本, 应用的优化列表)
        """
        try:
            optimized_text = text
            applied_optimizations = []
            
            # 1. 清理多余空格
            original_text = optimized_text
            optimized_text = re.sub(r'\s+', ' ', optimized_text).strip()
            if optimized_text != original_text:
                applied_optimizations.append({
                    "type": "space_normalization",
                    "description": "清理多余空格",
                    "confidence": 0.9
                })
            
            # 2. 标点符号规范化
            punct_rules = [
                (r'[,，]{2,}', '，'),        # 多个逗号
                (r'[.。]{2,}', '。'),        # 多个句号
                (r'[!！]{2,}', '！'),        # 多个感叹号
                (r'[?？]{2,}', '？'),        # 多个问号
                (r'[…]{2,}', '…'),          # 多个省略号
            ]
            
            for pattern, replacement in punct_rules:
                if re.search(pattern, optimized_text):
                    optimized_text = re.sub(pattern, replacement, optimized_text)
                    applied_optimizations.append({
                        "type": "punctuation_normalization",
                        "pattern": pattern,
                        "replacement": replacement,
                        "confidence": 0.8
                    })
            
            # 3. 添加缺失的句号
            if optimized_text and not re.search(r'[。！？]$', optimized_text):
                # 根据内容类型决定标点
                if any(word in optimized_text for word in ['哇', '太', '绝了', '爱了']):
                    optimized_text += '！'  # 感叹号
                    punct_type = '感叹号'
                else:
                    optimized_text += '。'  # 句号
                    punct_type = '句号'
                
                applied_optimizations.append({
                    "type": "punctuation_addition",
                    "added": punct_type,
                    "confidence": 0.6
                })
            
            return optimized_text, applied_optimizations
            
        except Exception as e:
            self.logger.error(f"标点符号优化失败: {e}")
            return text, []

class LiveStreamTextPostProcessor:
    """直播文本后处理器
    
    整合情感表达纠错、产品名称标准化、网络用语规范化、语法修正和标点优化
    """
    
    def __init__(self):
        # 初始化各个处理器
        self.emotion_corrector = EmotionExpressionCorrector()
        self.product_standardizer = ProductNameStandardizer()
        self.slang_normalizer = SlangNormalizer()
        self.grammar_corrector = GrammarCorrector()
        self.punctuation_optimizer = PunctuationOptimizer()
        
        # 统计数据
        self.processing_stats = {
            "total_processed": 0,
            "correction_types": defaultdict(int),
            "average_corrections_per_text": 0.0,
            "processing_confidence": 0.0
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("直播文本后处理器已初始化")
    
    def process_text(self, 
                    text: str,
                    emotion_type: Optional[EmotionType] = None,
                    confidence_threshold: float = MIN_CONFIDENCE_FOR_CORRECTION,
                    processing_types: Optional[List[ProcessingType]] = None) -> PostProcessingResult:
        """处理文本
        
        Args:
            text: 输入文本
            emotion_type: 情感类型提示
            confidence_threshold: 处理置信度阈值
            processing_types: 指定的处理类型
            
        Returns:
            后处理结果
        """
        try:
            original_text = text
            processed_text = text
            all_corrections = []
            applied_types = []
            
            # 默认处理类型
            if processing_types is None:
                processing_types = [
                    ProcessingType.EMOTION_CORRECTION,
                    ProcessingType.PRODUCT_STANDARDIZATION,
                    ProcessingType.SLANG_NORMALIZATION
                ]
            
            # 1. 情感表达纠错
            if ProcessingType.EMOTION_CORRECTION in processing_types:
                processed_text, emotion_corrections = self.emotion_corrector.correct_emotion_expressions(
                    processed_text, emotion_type
                )
                if emotion_corrections:
                    all_corrections.extend(emotion_corrections)
                    applied_types.append(ProcessingType.EMOTION_CORRECTION)
            
            # 2. 产品名称标准化
            if ProcessingType.PRODUCT_STANDARDIZATION in processing_types:
                processed_text, product_corrections = self.product_standardizer.standardize_product_names(
                    processed_text
                )
                if product_corrections:
                    all_corrections.extend(product_corrections)
                    applied_types.append(ProcessingType.PRODUCT_STANDARDIZATION)
            
            # 3. 网络用语规范化
            if ProcessingType.SLANG_NORMALIZATION in processing_types:
                processed_text, slang_corrections = self.slang_normalizer.normalize_slang(
                    processed_text
                )
                if slang_corrections:
                    all_corrections.extend(slang_corrections)
                    applied_types.append(ProcessingType.SLANG_NORMALIZATION)
            
            # 4. 语法错误修正
            processed_text, grammar_corrections = self.grammar_corrector.correct_grammar(
                processed_text
            )
            if grammar_corrections:
                all_corrections.extend(grammar_corrections)
            
            # 5. 标点符号优化
            processed_text, punct_corrections = self.punctuation_optimizer.optimize_punctuation(
                processed_text
            )
            if punct_corrections:
                all_corrections.extend(punct_corrections)
            
            # 6. 计算处理置信度
            processing_confidence = self._calculate_processing_confidence(
                all_corrections, len(original_text)
            )
            
            # 7. 过滤低置信度的修正
            filtered_corrections = [
                corr for corr in all_corrections 
                if corr.get('confidence', 0) >= confidence_threshold
            ]
            
            # 如果置信度太低，使用原始文本
            if processing_confidence < confidence_threshold:
                processed_text = original_text
                filtered_corrections = []
                applied_types = []
            
            # 8. 更新统计数据
            self._update_processing_stats(filtered_corrections, processing_confidence)
            
            return PostProcessingResult(
                original_text=original_text,
                processed_text=processed_text,
                applied_corrections=filtered_corrections,
                processing_confidence=processing_confidence,
                processing_types=applied_types
            )
            
        except Exception as e:
            self.logger.error(f"文本后处理失败: {e}")
            # 失败时返回原始文本
            return PostProcessingResult(
                original_text=text,
                processed_text=text,
                applied_corrections=[],
                processing_confidence=0.0,
                processing_types=[]
            )
    
    def _calculate_processing_confidence(self, corrections: List[Dict[str, Any]], 
                                       text_length: int) -> float:
        """计算处理置信度"""
        if not corrections:
            return 0.8  # 无修正时的默认置信度
        
        # 基于修正置信度的加权平均
        total_confidence = sum(corr.get('confidence', 0.5) for corr in corrections)
        avg_confidence = total_confidence / len(corrections)
        
        # 考虑修正数量对置信度的影响
        correction_ratio = len(corrections) / max(text_length / 5, 1)  # 平圇5个字一个修正
        
        if correction_ratio > 0.5:  # 修正过多可能降低置信度
            confidence_penalty = min(correction_ratio - 0.5, 0.3)
            avg_confidence -= confidence_penalty
        
        return max(0.0, min(avg_confidence, 1.0))
    
    def _update_processing_stats(self, corrections: List[Dict[str, Any]], 
                               confidence: float):
        """更新处理统计数据"""
        self.processing_stats["total_processed"] += 1
        
        # 统计修正类型
        for correction in corrections:
            correction_type = correction.get('type', 'unknown')
            self.processing_stats["correction_types"][correction_type] += 1
        
        # 更新平均值
        count = self.processing_stats["total_processed"]
        prev_avg_corrections = self.processing_stats["average_corrections_per_text"]
        prev_avg_confidence = self.processing_stats["processing_confidence"]
        
        self.processing_stats["average_corrections_per_text"] = (
            (prev_avg_corrections * (count - 1) + len(corrections)) / count
        )
        self.processing_stats["processing_confidence"] = (
            (prev_avg_confidence * (count - 1) + confidence) / count
        )
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        stats = dict(self.processing_stats)
        stats["correction_types"] = dict(stats["correction_types"])
        return stats
    
    def reset_stats(self):
        """重置统计数据"""
        self.processing_stats = {
            "total_processed": 0,
            "correction_types": defaultdict(int),
            "average_corrections_per_text": 0.0,
            "processing_confidence": 0.0
        }
        self.logger.info("后处理统计数据已重置")

# 导出主要类
__all__ = [
    'LiveStreamTextPostProcessor',
    'EmotionExpressionCorrector',
    'ProductNameStandardizer',
    'SlangNormalizer',
    'GrammarCorrector',
    'PunctuationOptimizer',
    'PostProcessingResult',
    'CorrectionRule'
]