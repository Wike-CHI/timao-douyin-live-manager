"""
智能话题生成器 - 基于AI动态生成直播话题
替代固定话题库，根据实际直播内容生成相关话题
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SmartTopicGenerator:
    """基于AI的智能话题生成器"""
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self.sensitive_keywords = {
            "彩礼", "结婚", "离婚", "政治", "宗教", "种族", "性别歧视", 
            "暴力", "色情", "赌博", "毒品", "自杀", "死亡", "疾病",
            "收入", "工资", "房价", "股票", "投资", "借钱", "贷款"
        }
    
    def generate_contextual_topics(
        self,
        *,
        transcript: str = "",
        chat_messages: List[Dict[str, Any]] = None,
        persona: Dict[str, Any] = None,
        vibe: Dict[str, Any] = None,
        current_topics: List[str] = None,
        limit: int = 6
    ) -> List[Dict[str, str]]:
        """
        根据直播上下文生成智能话题
        
        Args:
            transcript: 主播转录文本
            chat_messages: 弹幕消息
            persona: 主播人设
            vibe: 直播间氛围
            current_topics: 当前话题
            limit: 生成话题数量限制
            
        Returns:
            话题列表，格式: [{"topic": "话题内容", "category": "分类"}]
        """
        if not self.ai_client:
            return self._get_fallback_topics(limit)
        
        try:
            context = self._build_context(
                transcript, chat_messages, persona, vibe, current_topics
            )
            
            prompt = self._build_topic_generation_prompt(context)
            
            response = self.ai_client.chat.completions.create(
                model="qwen-plus",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            topics = self._parse_ai_response(content)
            
            # 过滤敏感话题
            filtered_topics = self._filter_sensitive_topics(topics)
            
            # 确保话题多样性
            diverse_topics = self._ensure_diversity(filtered_topics, limit)
            
            return diverse_topics[:limit]
            
        except Exception as exc:
            logger.warning("AI话题生成失败: %s", exc)
            return self._get_fallback_topics(limit)
    
    def _build_context(
        self,
        transcript: str,
        chat_messages: List[Dict[str, Any]],
        persona: Dict[str, Any],
        vibe: Dict[str, Any],
        current_topics: List[str]
    ) -> Dict[str, Any]:
        """构建生成话题的上下文信息"""
        
        # 提取最近的弹幕关键词
        chat_keywords = []
        if chat_messages:
            recent_messages = chat_messages[-10:]  # 最近10条弹幕
            for msg in recent_messages:
                content = str(msg.get('content', '')).strip()
                if content and len(content) > 2:
                    chat_keywords.append(content)
        
        # 分析主播风格
        host_style = "亲和"
        if persona:
            tone = persona.get('tone', '')
            if '幽默' in tone or '搞笑' in tone:
                host_style = "幽默"
            elif '温柔' in tone or '甜美' in tone:
                host_style = "温柔"
            elif '活泼' in tone or '元气' in tone:
                host_style = "活泼"
        
        # 分析直播间氛围
        atmosphere = "平稳"
        if vibe:
            level = vibe.get('level', '').lower()
            if level == 'hot':
                atmosphere = "热烈"
            elif level == 'cold':
                atmosphere = "冷清"
        
        return {
            "transcript_snippet": transcript[-200:] if transcript else "",  # 最近200字转录
            "chat_keywords": chat_keywords[:5],  # 最近5个弹幕关键词
            "host_style": host_style,
            "atmosphere": atmosphere,
            "current_topics": current_topics or [],
            "timestamp": datetime.now().strftime("%H:%M")
        }
    
    def _build_topic_generation_prompt(self, context: Dict[str, Any]) -> str:
        """构建AI话题生成提示词"""
        
        prompt = f"""你是一个专业的直播话题助手，需要根据当前直播间的实际情况生成合适的互动话题。

当前直播间情况：
- 时间：{context['timestamp']}
- 主播风格：{context['host_style']}
- 直播间氛围：{context['atmosphere']}
- 最近转录内容：{context['transcript_snippet'] or '暂无'}
- 观众弹幕关键词：{', '.join(context['chat_keywords']) if context['chat_keywords'] else '暂无'}
- 当前话题：{', '.join(context['current_topics']) if context['current_topics'] else '暂无'}

请生成6个适合当前直播间的互动话题，要求：
1. 话题要贴合当前直播内容和观众兴趣，避免生成固定模板话题
2. 严格避免敏感话题：政治、宗教、金钱收入、彩礼婚姻、地域歧视、年龄隐私等
3. 话题要简洁明了，能引发观众互动和讨论
4. 适合{context['host_style']}风格的主播
5. 考虑{context['atmosphere']}的直播间氛围
6. 话题内容要具体化，避免过于宽泛或模糊

优先生成以下类型的话题：
- 基于当前直播内容的具体讨论点
- 轻松有趣的日常生活话题
- 观众可以分享个人经历的话题
- 能够活跃气氛的互动游戏话题

输出格式为JSON数组，每个话题包含topic和category字段：
[
  {{"topic": "话题内容", "category": "分类"}},
  ...
]

分类可以是：日常生活、兴趣爱好、娱乐互动、美食分享、旅行见闻、学习成长、游戏互动等。

请直接输出JSON，不要其他解释。"""

        return prompt
    
    def _parse_ai_response(self, content: str) -> List[Dict[str, str]]:
        """解析AI返回的话题内容"""
        try:
            # 尝试直接解析JSON
            topics = json.loads(content)
            if isinstance(topics, list):
                valid_topics = []
                for topic in topics:
                    if isinstance(topic, dict) and 'topic' in topic:
                        valid_topics.append({
                            'topic': str(topic['topic']).strip(),
                            'category': str(topic.get('category', '互动话题')).strip()
                        })
                return valid_topics
        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试从文本中提取
            logger.warning("AI返回内容不是有效JSON，尝试文本解析")
            return self._extract_topics_from_text(content)
        
        return []
    
    def _extract_topics_from_text(self, content: str) -> List[Dict[str, str]]:
        """从文本中提取话题（备用解析方法）"""
        topics = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 4:
                continue
                
            # 移除序号和特殊字符
            topic_text = line
            for prefix in ['1.', '2.', '3.', '4.', '5.', '6.', '-', '•', '*']:
                if topic_text.startswith(prefix):
                    topic_text = topic_text[len(prefix):].strip()
                    break
            
            if topic_text and len(topic_text) >= 4:
                topics.append({
                    'topic': topic_text,
                    'category': '互动话题'
                })
                
            if len(topics) >= 6:
                break
        
        return topics
    
    def _filter_sensitive_topics(self, topics: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """过滤敏感话题"""
        filtered = []
        
        # 扩展敏感关键词列表
        extended_sensitive_keywords = self.sensitive_keywords.union({
            "城市地域", "地域", "城市", "多少钱", "价格", "费用", "成本",
            "差异", "比较", "对比", "哪里", "什么地方", "多少岁", "年龄",
            "工作", "职业", "学历", "教育", "重视", "看重", "在意"
        })
        
        for topic_item in topics:
            topic_text = topic_item.get('topic', '').lower()
            
            # 检查是否包含敏感关键词
            is_sensitive = False
            for keyword in extended_sensitive_keywords:
                if keyword in topic_text:
                    is_sensitive = True
                    break
            
            # 检查是否包含固定模板格式（如 #城市地域）
            if '#' in topic_text or '地域' in topic_text or '城市' in topic_text:
                is_sensitive = True
            
            # 检查话题长度
            if len(topic_item.get('topic', '')) < 4 or len(topic_item.get('topic', '')) > 30:
                is_sensitive = True
            
            # 检查是否为过于宽泛的话题
            broad_patterns = ['怎么样', '如何', '什么', '多少', '哪里', '哪个']
            if any(pattern in topic_text for pattern in broad_patterns):
                # 如果话题过于宽泛且没有具体内容，则过滤
                if len(topic_text) < 8:
                    is_sensitive = True
            
            if not is_sensitive:
                filtered.append(topic_item)
        
        return filtered
    
    def _ensure_diversity(self, topics: List[Dict[str, str]], limit: int) -> List[Dict[str, str]]:
        """确保话题多样性，避免重复"""
        seen_topics = set()
        diverse_topics = []
        
        for topic_item in topics:
            topic_text = topic_item.get('topic', '')
            
            # 简单的重复检测
            topic_key = ''.join(topic_text.split())[:10]  # 取前10个字符作为去重key
            
            if topic_key not in seen_topics:
                seen_topics.add(topic_key)
                diverse_topics.append(topic_item)
                
                if len(diverse_topics) >= limit:
                    break
        
        return diverse_topics
    
    def _get_fallback_topics(self, limit: int) -> List[Dict[str, str]]:
        """获取备用话题（当AI生成失败时使用）"""
        fallback_topics = [
            {"topic": "今天心情怎么样", "category": "日常互动"},
            {"topic": "最近在看什么剧", "category": "娱乐分享"},
            {"topic": "喜欢什么类型的音乐", "category": "兴趣爱好"},
            {"topic": "有什么推荐的美食", "category": "美食分享"},
            {"topic": "周末一般做什么", "category": "生活方式"},
            {"topic": "最想去的旅行地点", "category": "旅行话题"},
            {"topic": "有什么有趣的爱好", "category": "兴趣交流"},
            {"topic": "最近学了什么新技能", "category": "学习成长"}
        ]
        
        return fallback_topics[:limit]


def create_smart_topic_generator(ai_client=None) -> SmartTopicGenerator:
    """创建智能话题生成器实例"""
    return SmartTopicGenerator(ai_client)