"""
提猫直播助手 - 问题提取模块
负责从评论中识别和分类用户问题
"""

import re
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import jieba
from server.utils.logger import LoggerMixin


class QuestionExtractor(LoggerMixin):
    """问题提取器"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.question_patterns = self._load_question_patterns()
        self.question_categories = self._load_question_categories()
        self.logger.info("问题提取器初始化完成")
    
    def _load_question_patterns(self) -> List[Dict[str, Any]]:
        """加载问题识别模式"""
        return [
            # 疑问句模式
            {'pattern': r'.*[？?].*', 'type': '疑问句', 'priority': 1},
            {'pattern': r'.*(什么|怎么|为什么|如何|吗|呢|吧|啊).*', 'type': '疑问词', 'priority': 2},
            {'pattern': r'.*请教.*', 'type': '请教', 'priority': 3},
            {'pattern': r'.*请问.*', 'type': '请问', 'priority': 3},
            {'pattern': r'.*咨询.*', 'type': '咨询', 'priority': 3},
            {'pattern': r'.*问.*', 'type': '询问', 'priority': 4},
            {'pattern': r'.*求.*', 'type': '请求', 'priority': 4},
            {'pattern': r'.*想要.*', 'type': '需求', 'priority': 4},
            {'pattern': r'.*需要.*', 'type': '需求', 'priority': 4},
        ]
    
    def _load_question_categories(self) -> Dict[str, List[str]]:
        """加载问题分类关键词"""
        return {
            'product': [
                '产品', '商品', '东西', '这个', '那个', '价格', '多少钱', '链接',
                '质量', '材质', '功能', '效果', '品牌', '型号', '规格', '尺寸',
                '颜色', '款式', '样式', '包装', '产地', '保质期', '有效期'
            ],
            'usage': [
                '怎么用', '如何使用', '使用方法', '操作', '步骤', '教程',
                '安装', '组装', '设置', '配置', '调节', '调整', '使用',
                '说明书', '指导', '演示', '示范', '展示'
            ],
            'delivery': [
                '发货', '快递', '物流', '配送', '运送', '邮寄', '包邮',
                '时间', '多久', '几天', '速度', '时效', '跟踪', '查询',
                '地址', '地点', '位置', '运费', '邮费', '多少钱'
            ],
            'return': [
                '退', '换', '售后', '服务', '保修', '保证', '承诺',
                '坏', '损坏', '故障', '问题', '缺陷', '瑕疵', '不合格',
                '不满意', '投诉', '维权', '举报'
            ],
            'promotion': [
                '优惠', '折扣', '打折', '减价', '便宜', '活动', '促销',
                '赠品', '礼物', '福利', '福利', '秒杀', '限时', '限量',
                '券', '红包', '积分', '会员', 'vip'
            ],
            'comparison': [
                '对比', '比较', '区别', '差异', '哪个好', '更好', '推荐',
                '同款', '类似', '一样', '相同', '差不多', '替代',
                '品牌', '牌子', '厂家', '生产商'
            ]
        }
    
    def extract_questions(self, text: str) -> List[Dict[str, Any]]:
        """从文本中提取问题"""
        if not text:
            return []
        
        questions = []
        
        # 匹配问题模式
        for pattern_info in self.question_patterns:
            pattern = pattern_info['pattern']
            if re.search(pattern, text):
                # 提取问题内容
                question_content = self._extract_question_content(text, pattern)
                if question_content:
                    # 分类问题
                    category = self._classify_question(question_content)
                    
                    questions.append({
                        'content': question_content,
                        'type': pattern_info['type'],
                        'category': category,
                        'priority': self._calculate_priority(category, pattern_info['priority']),
                        'confidence': self._calculate_confidence(text, pattern_info)
                    })
        
        # 去重
        unique_questions = self._deduplicate_questions(questions)
        
        # 按优先级排序
        unique_questions.sort(key=lambda x: x['priority'], reverse=True)
        
        return unique_questions
    
    def _extract_question_content(self, text: str, pattern: str) -> str:
        """提取问题内容"""
        # 简单实现：返回整个文本
        # 可以进一步优化，只返回问题相关部分
        return text.strip()
    
    def _classify_question(self, question: str) -> str:
        """对问题进行分类"""
        # 分词
        words = jieba.lcut(question.lower())
        
        # 统计各类别关键词匹配数
        category_scores = defaultdict(int)
        for category, keywords in self.question_categories.items():
            for word in words:
                if word in keywords:
                    category_scores[category] += 1
        
        # 返回得分最高的类别
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        else:
            return 'other'  # 默认类别
    
    def _calculate_priority(self, category: str, base_priority: int) -> int:
        """计算问题优先级"""
        # 根据类别调整优先级
        category_priority = {
            'product': 10,
            'usage': 8,
            'delivery': 6,
            'return': 9,
            'promotion': 5,
            'comparison': 4,
            'other': 1
        }
        
        category_boost = category_priority.get(category, 0)
        return base_priority + category_boost
    
    def _calculate_confidence(self, text: str, pattern_info: Dict[str, Any]) -> float:
        """计算识别置信度"""
        # 基于匹配模式和文本特征计算置信度
        confidence = 0.5  # 基础置信度
        
        # 文本长度影响
        if len(text) > 10:
            confidence += 0.1
        elif len(text) < 3:
            confidence -= 0.2
        
        # 疑问词影响
        question_words = ['什么', '怎么', '为什么', '如何', '吗', '呢']
        question_word_count = sum(1 for word in question_words if word in text)
        confidence += min(0.3, question_word_count * 0.1)
        
        # 标点符号影响
        if '？' in text or '?' in text:
            confidence += 0.2
        
        return min(1.0, max(0.0, confidence))
    
    def _deduplicate_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重问题"""
        if not questions:
            return questions
        
        # 简单去重：基于问题内容
        seen_contents = set()
        unique_questions = []
        
        for question in questions:
            content = question['content']
            if content not in seen_contents:
                seen_contents.add(content)
                unique_questions.append(question)
        
        return unique_questions
    
    def extract_from_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从评论列表中提取问题"""
        if not comments:
            return {
                'total_questions': 0,
                'questions': [],
                'category_distribution': {},
                'priority_distribution': {}
            }
        
        all_questions = []
        category_counts = defaultdict(int)
        priority_counts = defaultdict(int)
        
        for comment in comments:
            content = comment.get('content', '')
            questions = self.extract_questions(content)
            
            for question in questions:
                all_questions.append(question)
                category_counts[question['category']] += 1
                priority_counts[question['priority']] += 1
        
        # 按优先级排序
        all_questions.sort(key=lambda x: x['priority'], reverse=True)
        
        # 计算分布统计
        total_questions = len(all_questions)
        category_distribution = {
            category: {
                'count': count,
                'percentage': round((count / total_questions) * 100, 2) if total_questions > 0 else 0
            }
            for category, count in category_counts.items()
        }
        
        priority_distribution = dict(priority_counts)
        
        return {
            'total_questions': total_questions,
            'questions': all_questions,
            'category_distribution': category_distribution,
            'priority_distribution': priority_distribution
        }
    
    def get_high_priority_questions(self, comments: List[Dict[str, Any]], min_priority: int = 10) -> List[Dict[str, Any]]:
        """获取高优先级问题"""
        result = self.extract_from_comments(comments)
        high_priority_questions = [
            q for q in result['questions'] 
            if q['priority'] >= min_priority
        ]
        return high_priority_questions
    
    def generate_question_summary(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成问题摘要报告"""
        result = self.extract_from_comments(comments)
        
        # 获取最常见的问题类别
        top_category = max(result['category_distribution'].items(), 
                          key=lambda x: x[1]['count']) if result['category_distribution'] else ('none', {'count': 0})
        
        # 获取最高优先级问题
        high_priority_questions = self.get_high_priority_questions(comments, 10)
        
        return {
            'summary': {
                'total_questions': result['total_questions'],
                'top_category': top_category[0],
                'top_category_count': top_category[1]['count'],
                'high_priority_count': len(high_priority_questions)
            },
            'top_questions': high_priority_questions[:10],  # 取前10个高优先级问题
            'category_distribution': result['category_distribution'],
            'priority_distribution': result['priority_distribution']
        }