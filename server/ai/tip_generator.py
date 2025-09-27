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
            "欢迎新朋友，坐下聊聊～喜欢的话点个关注不迷路哦！",
            "弹幕区有什么想聊的，随时发出来，我都在看～",
            "如果觉得有意思，点个赞让我知道你们在！",
            "想听什么歌/想看什么片段，直接弹幕告诉我！",
            "有问题尽管问，我会挑几条集中回答～",
            "等会儿我们换个节奏，来一段互动小游戏，别走开～",
            "感谢刚才的支持，大家的每一个点赞和弹幕我都看到了！",
            "如果画面或声音有问题，及时在弹幕提醒我一下～",
            "今天的主题先这样安排，过程中也欢迎你们提建议！",
            "老朋友们带带节奏，新来的可以自我介绍下～"
        ]
        
        # 基于热词生成通用直播相关话术
        if hot_words:
            top_words = [str(word.get('word', '')).strip() for word in hot_words[:8]]
            for w in top_words:
                if not w:
                    continue
                if any(k in w for k in ['卡顿', '延迟', '网', '掉线', '声音', '画面', '麦']):
                    mock_tips.append("如果有卡顿或声音问题，试试刷新；也随时在弹幕提醒我～")
                elif any(k in w for k in ['关注', '粉', '点赞', '投币', '喜欢']):
                    mock_tips.append("喜欢的话点个关注/赞，后面还有更多精彩～")
                elif any(k in w for k in ['问题', '怎么', '为什么', '如何']):
                    mock_tips.append("大家的问题我都看到啦，等会儿集中挑几条来解答～")
                elif any(k in w for k in ['歌', '曲', '点歌', 'BGM']):
                    mock_tips.append("想听什么歌可以弹幕留言，我来排个队～")
                elif any(k in w for k in ['游戏', '挑战', 'Boss']):
                    mock_tips.append("要不要来个小挑战？弹幕投票决定下一个玩法～")
                elif any(k in w for k in ['知识', '教程', '教学', '科普']):
                    mock_tips.append("有想听的知识点也可以提，我选几条讲清楚～")
                elif any(k in w for k in ['活动', '抽奖', '福利']):
                    mock_tips.append("等等我们安排个小活动，记得跟上节奏～")
                elif any(k in w for k in ['打赏', '礼物', '支持']):
                    mock_tips.append("感谢支持～有你们在，直播会更有动力！")
        
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
你是通用直播话术助理，适用于聊天、游戏、音乐、知识、户外等各类直播场景。
请结合“最近评论”和“热词”，为主播生成3-5条可直接念出的短句话术。

【最近的观众评论节选】
{comment_text}

【当前热词】
{hot_words_text}

生成要求：
1) 语言中立、自然；紧贴评论关切；
2) 促进互动（如关注、点赞、发弹幕提问、点歌/点梗、参与活动等）；
3) 有助于节奏与氛围（承上启下、活跃、引导）；
4) 每条≤50字。

输出为严格 JSON 数组，每项格式：
[
  {{"content":"话术内容","type":"interaction|clarification|humor|engagement|call_to_action|transition","priority":1-5}},
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
