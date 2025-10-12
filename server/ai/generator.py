"""
提猫直播助手 - AI话术生成器
基于 Qwen Max 生成直播互动话术
"""

import logging
import re
from collections import Counter
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from openai import OpenAI

from ..models import AIScript, HotWord, Comment, create_success_response, create_error_response

try:  # pragma: no cover - optional style memory
    from .style_memory import StyleMemoryManager
except Exception:  # pragma: no cover
    StyleMemoryManager = None  # type: ignore
try:  # pragma: no cover - optional feedback memory
    from .feedback_memory import FeedbackMemoryManager
except Exception:  # pragma: no cover
    FeedbackMemoryManager = None  # type: ignore


class AIScriptGenerator:
    """AI话术生成器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化AI客户端
        self.client = None
        self._init_ai_client()
        
        # 生成历史
        self.generation_history = []
        self.anchor_id = (
            self.config.get('anchor_id')
            or self.config.get('douyin_room_id')
            or self.config.get('anchor_name')
        )
        self.style_memory = StyleMemoryManager() if StyleMemoryManager else None
        if not self.style_memory or not self.style_memory.available():
            self.logger.debug("Style memory unavailable; fall back to request context only.")
        self.feedback_memory = FeedbackMemoryManager() if FeedbackMemoryManager else None
        if not self.feedback_memory or not self.feedback_memory.available():
            self.logger.debug("Feedback memory unavailable; prompts will not include human ratings.")

    # ------------------------------------------------------------------ LangGraph helpers
    def generate_bundle(
        self,
        route: str,
        hot_words: Optional[List[Dict[str, Any]]] = None,
        questions: Optional[List[str]] = None,
        persona: Optional[Dict[str, Any]] = None,
        vibe: Optional[Dict[str, Any]] = None,
        recent_comments: Optional[List[Comment]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate 2-3 conversational scripts tailored for a given planner route."""
        script_plan = {
            'deep_dive': ['interaction', 'question', 'product'],
            'warm_up': ['welcome', 'emotion', 'interaction'],
            'promo': ['product', 'question', 'interaction'],
        }
        types = script_plan.get(route, script_plan['deep_dive'])
        hw_objects = self._convert_hot_words(hot_words or [])
        bundle: List[Dict[str, Any]] = []
        for script_type in types:
            context: Dict[str, Any] = {
                'route': route,
                'questions': questions or [],
                'style_profile': persona or {},
                'vibe': vibe or {},
            }
            script = self.generate_script(
                hot_words=hw_objects,
                recent_comments=recent_comments,
                script_type=script_type,
                context=context,
            )
            payload = script.to_dict()
            payload.update({
                'content': script.content,
                'vibe': (vibe or {}).get('level', 'neutral'),
                'keywords': self._extract_keywords(script.content),
                'rationale': self._build_rationale(route, script_type, questions or []),
            })
            bundle.append(payload)
        return bundle

    def score_text(self, content: str) -> float:
        """Expose scoring utility for downstream assessors."""
        return self._calculate_script_score(content, {})
    
    def _init_ai_client(self):
        """初始化AI客户端"""
        try:
            service = self.config.get('ai_service', 'qwen')
            api_key = self.config.get('ai_api_key', '')
            base_url = self.config.get('ai_base_url', '')
            
            if not api_key:
                self.logger.warning("AI API密钥未配置")
                return
            
            if service == 'qwen':
                # Align with DashScope OpenAI-compatible endpoint (Qwen3 family)
                from .qwen_openai_compatible import (
                    DEFAULT_OPENAI_API_KEY,
                    DEFAULT_OPENAI_BASE_URL,
                    DEFAULT_OPENAI_MODEL,
                )
                self.client = OpenAI(
                    api_key=api_key or DEFAULT_OPENAI_API_KEY,
                    base_url=base_url or DEFAULT_OPENAI_BASE_URL,
                )
                self.model = self.config.get('ai_model', DEFAULT_OPENAI_MODEL)

            elif service == 'deepseek':
                self.client = OpenAI(
                    api_key=api_key,
                    base_url=base_url or "https://api.deepseek.com"
                )
                self.model = self.config.get('ai_model', 'deepseek-chat')
                
            elif service == 'openai':
                self.client = OpenAI(
                    api_key=api_key,
                    base_url=base_url or "https://api.openai.com/v1"
                )
                self.model = self.config.get('ai_model', 'gpt-3.5-turbo')
                
            elif service == 'doubao':
                # 豆包API配置
                self.client = OpenAI(
                    api_key=api_key,
                    base_url=base_url or "https://ark.cn-beijing.volces.com/api/v3"
                )
                self.model = self.config.get('ai_model', 'doubao-lite-4k')
            
            self.logger.info(f"AI客户端初始化成功: {service}")
            
        except Exception as e:
            self.logger.error(f"AI客户端初始化失败: {e}")
            self.client = None
    
    def generate_script(self, 
                       hot_words: List[HotWord] = None, 
                       recent_comments: List[Comment] = None,
                       script_type: str = "general",
                       context: Dict[str, Any] = None) -> AIScript:
        """生成AI话术"""
        try:
            # 准备生成上下文
            generation_context = self._prepare_context(hot_words, recent_comments, context)
            
            # 根据类型选择生成策略
            if not self.client:
                raise RuntimeError("AI 客户端不可用，请检查 Qwen Max 配置")
            script_content = self._generate_with_ai(generation_context, script_type)
            
            # 创建话术对象
            script = AIScript(
                content=script_content,
                type=script_type,
                context=[hw.word for hw in (hot_words or [])],
                source="ai" if self.client else "template",
                score=self._calculate_script_score(script_content, generation_context)
            )
            
            # 记录生成历史
            self._record_generation(script, generation_context)
            self._remember_script(script)
            
            self.logger.info(f"话术生成成功: {script_type}")
            return script
            
        except Exception as e:
            self.logger.error(f"话术生成失败: {e}")
            raise
    
    def _prepare_context(self, 
                        hot_words: List[HotWord], 
                        recent_comments: List[Comment],
                        context: Dict[str, Any]) -> Dict[str, Any]:
        """准备生成上下文"""
        generation_context = {
            'hot_words': [],
            'comment_themes': [],
            'user_emotions': [],
            'product_mentions': [],
            'questions': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # 处理热词
        if hot_words:
            generation_context['hot_words'] = [
                {
                    'word': hw.word,
                    'count': hw.count,
                    'category': hw.category
                }
                for hw in hot_words[:10]  # 取前10个热词
            ]
        
        # 分析最近评论
        if recent_comments:
            generation_context.update(self._analyze_comments(recent_comments))
        
        # 合并额外上下文
        if context:
            generation_context.update(context)

        if self.style_memory and self.style_memory.available():
            try:
                notes = self.style_memory.fetch_context(self.anchor_id, k=6)
            except Exception:
                notes = ""
            if notes:
                generation_context.setdefault('style_memory_notes', notes)

        if self.feedback_memory and self.feedback_memory.available():
            try:
                guidance = self.feedback_memory.build_guidance(self.anchor_id, top_k=4)
            except Exception:
                guidance = ""
            if guidance:
                generation_context.setdefault('feedback_guidance', guidance)
        
        return generation_context

    def _convert_hot_words(self, hot_words: List[Any]) -> Optional[List[HotWord]]:
        """Normalize external hot word payloads into HotWord models."""
        if not hot_words:
            return None
        normalized: List[HotWord] = []
        for item in hot_words:
            if isinstance(item, HotWord):
                normalized.append(item)
                continue
            if not isinstance(item, dict):
                continue
            word = str(item.get('word') or item.get('topic') or '').strip()
            if not word:
                continue
            normalized.append(
                HotWord(
                    word=word,
                    count=int(item.get('count') or item.get('weight') or 1),
                    score=float(item.get('score') or item.get('confidence') or 0.0),
                    category=str(item.get('category') or 'general'),
                )
            )
        return normalized or None
    
    def _analyze_comments(self, comments: List[Comment]) -> Dict[str, Any]:
        """分析评论内容"""
        analysis = {
            'comment_themes': [],
            'user_emotions': [],
            'product_mentions': [],
            'questions': []
        }
        
        emotion_keywords = {
            'positive': ['好', '棒', '喜欢', '不错', '赞', '厉害', '优秀', '完美'],
            'excited': ['哇', '太棒了', 'amazing', '惊艳', '震撼', '绝了'],
            'curious': ['什么', '怎么', '为什么', '如何', '?', '？'],
            'supportive': ['支持', '加油', '继续', '坚持', '关注了']
        }
        
        product_keywords = ['产品', '商品', '东西', '这个', '那个', '价格', '多少钱', '链接']
        
        for comment in comments[-50:]:  # 分析最近50条评论
            content = comment.content.lower()
            
            # 情感分析
            for emotion, keywords in emotion_keywords.items():
                if any(keyword in content for keyword in keywords):
                    analysis['user_emotions'].append(emotion)
            
            # 产品提及
            if any(keyword in content for keyword in product_keywords):
                analysis['product_mentions'].append(content[:50])  # 截取前50字符
            
            # 问题识别
            if '?' in content or '？' in content or any(q in content for q in ['什么', '怎么', '为什么', '如何']):
                analysis['questions'].append(content[:100])  # 截取前100字符
        
        # 去重并限制数量
        analysis['user_emotions'] = list(set(analysis['user_emotions']))[:5]
        analysis['product_mentions'] = list(set(analysis['product_mentions']))[:5]
        analysis['questions'] = list(set(analysis['questions']))[:3]
        
        return analysis
    
    def _generate_with_ai(self, context: Dict[str, Any], script_type: str) -> str:
        """使用AI生成话术"""
        try:
            # 构建提示词
            prompt = self._build_ai_prompt(context, script_type)
            
            # 调用AI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是主播身边的实时话术助理，能够理解主播风格、直播节奏与观众情绪，并给出可直接上嘴的自然口语化话术。"
                            "无论直播主题为何（娱乐、知识分享、游戏、聊天等），都要帮助主播维持互动、回应观众、引导氛围。"
                            "若给出 style_profile（人物设定/语气/节奏/口头禅/句式）与 vibe（冷/中/热、score），请务必贴合；"
                            "输出的话术需真诚友好、易于朗读，避免敏感词与过度营销语，只返回一句话术。"
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.8
            )
            
            script_content = response.choices[0].message.content.strip()
            
            # 清理和优化内容
            script_content = self._clean_script_content(script_content)
            
            return script_content
            
        except Exception as e:
            self.logger.error(f"AI生成话术失败: {e}")
            raise
    
    def _build_ai_prompt(self, context: Dict[str, Any], script_type: str) -> str:
        """构建AI提示词"""
        prompt_parts = []
        
        # 基础要求
        prompt_parts.append(f"请生成一条{script_type}类型的直播话术。")
        prompt_parts.append("要求：1) 语言自然亲切、口语化；2) 20-50字；3) 能引导互动或带节奏；")

        # 风格与氛围（可选）
        sp = context.get('style_profile') or {}
        if sp:
            style_text = []
            if sp.get('persona'): style_text.append(f"persona={sp.get('persona')}")
            if sp.get('tone'): style_text.append(f"tone={sp.get('tone')}")
            if sp.get('tempo'): style_text.append(f"tempo={sp.get('tempo')}")
            if sp.get('register'): style_text.append(f"register={sp.get('register')}")
            slang = ",".join(sp.get('slang', [])[:5]) if isinstance(sp.get('slang'), list) else ''
            catch = ",".join(sp.get('catchphrases', [])[:5]) if isinstance(sp.get('catchphrases'), list) else ''
            if slang: style_text.append(f"slang=[{slang}]")
            if catch: style_text.append(f"catchphrases=[{catch}]")
            if style_text:
                prompt_parts.append("主播风格(style_profile)：" + "; ".join(style_text))

        vibe = context.get('vibe') or {}
        if vibe:
            v_level = vibe.get('level') or 'neutral'
            v_score = vibe.get('score')
            prompt_parts.append(f"直播间氛围(vibe)：level={v_level}, score={v_score}")

        # 热词信息
        if context.get('hot_words'):
            hot_words_text = "、".join([hw['word'] for hw in context['hot_words'][:5]])
            prompt_parts.append(f"4. 可以适当融入这些热词：{hot_words_text}")
        
        # 情感信息
        if context.get('user_emotions'):
            emotions_text = "、".join(context['user_emotions'])
            prompt_parts.append(f"5. 观众情绪偏向：{emotions_text}")

        route_requirements = {
            'deep_dive': "策略：聚焦当前高频话题或问题，补充细节并推动更有深度的对话。",
            'warm_up': "策略：暖场补能，多用陪伴式语气和互动问题，调动整体氛围。",
            'promo': "策略：行动号召，引导观众参与、反馈或执行下一步动作（关注、留言、投票等）。",
        }
        route = context.get('route')
        if route in route_requirements:
            prompt_parts.append(route_requirements[route])

        style_memory_notes = context.get('style_memory_notes')
        if style_memory_notes:
            prompt_parts.append(
                "请模仿以下历史记忆中总结的语言特征/口头禅（可择要借用，避免逐字复述）：\n"
                f"{style_memory_notes}"
            )

        feedback_guidance = context.get('feedback_guidance')
        if feedback_guidance:
            prompt_parts.append(
                "参考近期人工评分反馈，保留优点并避免风险表达：\n"
                f"{feedback_guidance}"
            )
        
        # 问题信息
        if context.get('questions'):
            prompt_parts.append("6. 有观众提出了问题，可以适当回应")
        
        # 类型特定要求
        type_requirements = {
            'welcome': "重点是欢迎新观众，营造温馨氛围",
            'product': "重点是介绍核心信息或主题亮点，帮助观众快速理解重点",
            'interaction': "重点是引导观众参与讨论，增加互动",
            'closing': "重点是感谢观众，收束话题并可预告下次互动",
            'question': "重点是回答观众问题，展现专业性或亲和力",
            'emotion': "重点是回应观众情绪，增强共鸣"
        }
        
        if script_type in type_requirements:
            prompt_parts.append(f"类型要求：{type_requirements[script_type]}")

        return "\n".join(prompt_parts)
    
    def _clean_script_content(self, content: str) -> str:
        """清理话术内容"""
        # 移除多余的标点符号
        content = content.replace('。。', '。').replace('！！', '！').replace('？？', '？')
        
        # 移除引号
        content = content.replace('"', '').replace('"', '').replace('"', '')
        
        # 限制长度
        if len(content) > 100:
            content = content[:97] + '...'
        
        return content.strip()

    def _extract_keywords(self, content: str, limit: int = 5) -> List[str]:
        """Extract lightweight keywords for downstream ranking."""
        tokens = re.findall(r"[\w\u4e00-\u9fff]{2,}", content.lower())
        counter = Counter(tokens)
        keywords = [word for word, _ in counter.most_common(limit)]
        return keywords

    def _build_rationale(self, route: str, script_type: str, questions: List[str]) -> str:
        """Explain why a script fits the planner decision."""
        if route == 'promo':
            return "行动号召：引导观众关注、互动或参与下一步。"
        if route == 'warm_up':
            return "暖场补能：陪伴式互动提升热度。"
        if script_type == 'question' and questions:
            return f"针对弹幕提问：{questions[0][:24]}"
        return "围绕当前高频话题延展互动。"
    
    def _calculate_script_score(self, content: str, context: Dict[str, Any]) -> float:
        """计算话术质量评分"""
        score = 5.0  # 基础分
        
        # 长度评分
        length = len(content)
        if 20 <= length <= 80:
            score += 1.0
        elif length < 10 or length > 120:
            score -= 1.0
        
        # 热词匹配评分
        if context.get('hot_words'):
            hot_words = [hw['word'] for hw in context['hot_words']]
            matches = sum(1 for word in hot_words if word in content)
            score += matches * 0.5
        
        # 情感词评分
        positive_words = ['好', '棒', '不错', '优秀', '完美', '喜欢', '支持']
        positive_count = sum(1 for word in positive_words if word in content)
        score += positive_count * 0.3
        
        # 互动词评分
        interactive_words = ['大家', '朋友', '一起', '我们', '你们', '欢迎']
        interactive_count = sum(1 for word in interactive_words if word in content)
        score += interactive_count * 0.2
        
        return min(10.0, max(1.0, score))
    
    def _record_generation(self, script: AIScript, context: Dict[str, Any]):
        """记录生成历史"""
        record = {
            'script_id': script.id,
            'type': script.type,
            'source': script.source,
            'score': script.score,
            'timestamp': datetime.now().timestamp(),
            'context_size': len(str(context))
        }
        
        self.generation_history.append(record)
        
        # 限制历史记录数量
        if len(self.generation_history) > 100:
            self.generation_history = self.generation_history[-50:]

    def _remember_script(self, script: AIScript) -> None:
        if not script or not self.style_memory or not self.style_memory.available():
            return
        try:
            self.style_memory.ingest_scripts(
                self.anchor_id,
                [{"content": script.content, "type": script.type}],
            )
        except Exception:
            pass
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """获取生成统计信息"""
        if not self.generation_history:
            return {
                'total_generated': 0,
                'avg_score': 0,
                'source_distribution': {},
                'type_distribution': {}
            }
        
        total = len(self.generation_history)
        avg_score = sum(r['score'] for r in self.generation_history) / total
        
        # 来源分布
        sources = [r['source'] for r in self.generation_history]
        source_dist = {source: sources.count(source) for source in set(sources)}
        
        # 类型分布
        types = [r['type'] for r in self.generation_history]
        type_dist = {type_: types.count(type_) for type_ in set(types)}
        
        return {
            'total_generated': total,
            'avg_score': round(avg_score, 2),
            'source_distribution': source_dist,
            'type_distribution': type_dist,
            'recent_generations': self.generation_history[-10:]
        }
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        self.config.update(config)
        self._init_ai_client()
        self.logger.info("AI生成器配置已更新")


# 批量生成器
class BatchScriptGenerator:
    """批量话术生成器"""
    
    def __init__(self, generator: AIScriptGenerator):
        self.generator = generator
        self.logger = logging.getLogger(__name__)
    
    def generate_batch(self, 
                      count: int = 5,
                      types: List[str] = None,
                      hot_words: List[HotWord] = None,
                      recent_comments: List[Comment] = None) -> List[AIScript]:
        """批量生成话术"""
        if types is None:
            types = ['welcome', 'product', 'interaction', 'question', 'emotion']
        
        scripts = []
        
        for i in range(count):
            try:
                script_type = types[i % len(types)]
                script = self.generator.generate_script(
                    hot_words=hot_words,
                    recent_comments=recent_comments,
                    script_type=script_type
                )
                scripts.append(script)
                
                # 避免频繁调用
                if i < count - 1:
                    import time
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"批量生成第{i+1}条话术失败: {e}")
                continue
        
        self.logger.info(f"批量生成完成，成功生成{len(scripts)}条话术")
        return scripts
