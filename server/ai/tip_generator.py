"""
提猫直播助手 - AI话术生成模块
负责基于评论和热词生成直播话术
"""

import time
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from server.utils.logger import LoggerMixin


class TipGenerator(LoggerMixin):
    """AI话术生成器"""
    
    def __init__(self, config=None, ai_service: str = 'deepseek', api_key: str = '', base_url: str = '', model: str = ''):
        self.config = config
        self.ai_service = ai_service
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.tips_cache = []
        self.max_cache_size = 100
        self.generation_interval = 300  # 5分钟
        self.last_generation = 0
        self.is_running = False  # 添加运行状态标志
        
        # 模拟数据开关
        self.use_mock_data = True
        
        self.logger.info(f"AI话术生成器初始化完成，服务: {ai_service}")
    
    def generate_tips(self, comments: List[Dict[str, Any]], hot_words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成话术"""
        current_time = time.time()
        
        # 检查生成间隔
        if current_time - self.last_generation < self.generation_interval:
            self.logger.info("距离上次生成时间过短，跳过本次生成")
            return []
        
        try:
            if self.use_mock_data or not self.api_key:
                tips = self._generate_mock_tips(comments, hot_words)
            else:
                tips = self._generate_ai_tips(comments, hot_words)
            
            # 添加到缓存
            for tip in tips:
                self._add_tip_to_cache(tip)
            
            self.last_generation = current_time
            self.logger.info(f"生成了 {len(tips)} 条话术")
            
            return tips
            
        except Exception as e:
            self.logger.error(f"生成话术失败: {e}")
            return []
    
    def _generate_mock_tips(self, comments: List[Dict[str, Any]], hot_words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成模拟话术"""
        mock_tips = [
            "感谢大家的支持！看到这么多朋友关注我们的产品，真的很开心！",
            "刚才有朋友问到价格问题，我们现在有特别优惠，大家可以私信了解详情。",
            "这款产品的质量确实不错，很多老客户都回购了，大家可以放心选择。",
            "看到有朋友问包邮的问题，我们全国包邮，偏远地区可能需要补运费。",
            "今天直播间人气很旺啊！新来的朋友记得点个关注，不迷路哦！",
            "有朋友问现货情况，我们库存充足，下单后24小时内发货。",
            "这个颜色确实很受欢迎，建议大家尽快下单，库存不多了。",
            "感谢刚才打赏的朋友们，你们的支持是我最大的动力！"
        ]
        
        # 基于热词生成相关话术
        if hot_words:
            top_words = [word['word'] for word in hot_words[:5]]
            for word in top_words:
                if word in ['价格', '多少钱', '便宜']:
                    mock_tips.append(f"关于{word}问题，我们的产品性价比很高，现在还有优惠活动。")
                elif word in ['质量', '好不好', '怎么样']:
                    mock_tips.append(f"很多朋友关心{word}，我可以负责任地说，我们的产品质量绝对有保障。")
                elif word in ['包邮', '运费', '快递']:
                    mock_tips.append(f"看到大家问{word}，我们承诺全国包邮，顺丰发货。")
        
        # 随机选择3-5条话术
        import random
        selected_tips = random.sample(mock_tips, min(5, len(mock_tips)))
        
        tips = []
        for i, content in enumerate(selected_tips):
            tip = {
                'id': str(uuid.uuid4()),
                'content': content,
                'type': 'general',
                'priority': random.randint(1, 5),
                'timestamp': time.time(),
                'used': False,
                'source': 'mock'
            }
            tips.append(tip)
        
        return tips
    
    def _generate_ai_tips(self, comments: List[Dict[str, Any]], hot_words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """使用AI生成话术"""
        # 构建提示词
        prompt = self._build_prompt(comments, hot_words)
        
        try:
            if self.ai_service == 'deepseek':
                response = self._call_deepseek_api(prompt)
            elif self.ai_service == 'openai':
                response = self._call_openai_api(prompt)
            else:
                self.logger.warning(f"不支持的AI服务: {self.ai_service}")
                return self._generate_mock_tips(comments, hot_words)
            
            # 解析响应
            tips = self._parse_ai_response(response)
            return tips
            
        except Exception as e:
            self.logger.error(f"AI API调用失败: {e}")
            return self._generate_mock_tips(comments, hot_words)
    
    def _build_prompt(self, comments: List[Dict[str, Any]], hot_words: List[Dict[str, Any]]) -> str:
        """构建AI提示词"""
        # 提取最近的评论内容
        recent_comments = [comment.get('content', '') for comment in comments[-20:]]
        comment_text = '\n'.join(recent_comments)
        
        # 提取热词
        hot_word_list = [word['word'] for word in hot_words[:10]]
        hot_words_text = ', '.join(hot_word_list)
        
        prompt = f"""
你是一个专业的直播助手，需要根据观众的评论和热词，为主播生成合适的话术。

最近的观众评论：
{comment_text}

当前热词：
{hot_words_text}

请生成3-5条直播话术，要求：
1. 自然流畅，符合直播场景
2. 能够回应观众关心的问题
3. 有助于提升直播间氛围
4. 每条话术不超过50字

请以JSON格式返回，格式如下：
[
    {{"content": "话术内容", "type": "类型", "priority": 优先级(1-5)}},
    ...
]
"""
        return prompt
    
    def _call_deepseek_api(self, prompt: str) -> str:
        """调用DeepSeek API"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 1000
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _call_openai_api(self, prompt: str) -> str:
        """调用OpenAI API"""
        # TODO: 实现OpenAI API调用
        raise NotImplementedError("OpenAI API调用待实现")
    
    def _parse_ai_response(self, response: str) -> List[Dict[str, Any]]:
        """解析AI响应"""
        try:
            # 尝试解析JSON
            tips_data = json.loads(response)
            
            tips = []
            for tip_data in tips_data:
                tip = {
                    'id': str(uuid.uuid4()),
                    'content': tip_data.get('content', ''),
                    'type': tip_data.get('type', 'general'),
                    'priority': tip_data.get('priority', 3),
                    'timestamp': time.time(),
                    'used': False,
                    'source': 'ai'
                }
                tips.append(tip)
            
            return tips
            
        except json.JSONDecodeError:
            self.logger.error("AI响应格式错误，无法解析JSON")
            return []
    
    def _add_tip_to_cache(self, tip: Dict[str, Any]):
        """添加话术到缓存"""
        self.tips_cache.append(tip)
        
        # 限制缓存大小
        if len(self.tips_cache) > self.max_cache_size:
            self.tips_cache = self.tips_cache[-self.max_cache_size:]
    
    def get_latest_tips(self, limit: int = 10, unused_only: bool = True) -> List[Dict[str, Any]]:
        """获取最新话术"""
        tips = self.tips_cache.copy()
        
        if unused_only:
            tips = [tip for tip in tips if not tip.get('used', False)]
        
        # 按时间戳排序
        tips.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        return tips[:limit]
    
    def mark_tip_used(self, tip_id: str) -> bool:
        """标记话术为已使用"""
        for tip in self.tips_cache:
            if tip.get('id') == tip_id:
                tip['used'] = True
                self.logger.info(f"话术 {tip_id} 已标记为使用")
                return True
        
        self.logger.warning(f"未找到话术 {tip_id}")
        return False
    
    def get_tip_by_id(self, tip_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取话术"""
        for tip in self.tips_cache:
            if tip.get('id') == tip_id:
                return tip
        return None
    
    def clear_cache(self):
        """清空缓存"""
        self.tips_cache.clear()
        self.logger.info("话术缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_tips = len(self.tips_cache)
        used_tips = len([tip for tip in self.tips_cache if tip.get('used', False)])
        
        return {
            'total_tips': total_tips,
            'used_tips': used_tips,
            'unused_tips': total_tips - used_tips,
            'last_generation': self.last_generation,
            'ai_service': self.ai_service,
            'use_mock_data': self.use_mock_data
        }
    
    def start_generating(self):
        """启动话术生成（后台任务）"""
        self.is_running = True
        self.logger.info("AI话术生成任务已启动")
        # 这里可以添加定期生成逻辑
        # 目前只是占位方法，实际生成在API调用时进行