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

try:  # pragma: no cover - optional style memory
    from .style_memory import StyleMemoryManager
except Exception:  # pragma: no cover
    StyleMemoryManager = None  # type: ignore


class TipGenerator(LoggerMixin):
    """AI话术生成器，统一使用 Qwen OpenAI-兼容接口生成话术。"""
    
    def __init__(self, config=None, ai_service: str = 'qwen', api_key: str = '', base_url: str = '', model: str = ''):
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
        self.anchor_id = self._resolve_anchor_id(config)
        self.style_memory = StyleMemoryManager() if StyleMemoryManager else None
        if not self.style_memory or not self.style_memory.available():
            self.logger.debug("Style memory unavailable; falling back to runtime context only.")
        
        self.logger.info(f"AI话术生成器初始化完成，服务: {ai_service}")
        # 若未显式配置，默认走 Qwen OpenAI-兼容（与项目一致）
        try:
            from .qwen_openai_compatible import (
                DEFAULT_OPENAI_API_KEY,
                DEFAULT_OPENAI_BASE_URL,
                DEFAULT_OPENAI_MODEL,
            )
            if not self.base_url:
                self.base_url = DEFAULT_OPENAI_BASE_URL
            if not self.model:
                self.model = DEFAULT_OPENAI_MODEL
            if not self.api_key:
                self.api_key = DEFAULT_OPENAI_API_KEY
        except Exception:
            pass
    
    def generate_tips(
        self,
        comments: List[Dict[str, Any]],
        hot_words: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """生成话术"""
        current_time = time.time()
        
        # 检查生成间隔
        if current_time - self.last_generation < self.generation_interval:
            self.logger.info("距离上次生成时间过短，跳过本次生成")
            return []
        
        if not self.api_key:
            self.logger.warning("AI API密钥未配置，跳过话术生成")
            return []
        
        try:
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
    
    def _generate_ai_tips(
        self,
        comments: List[Dict[str, Any]],
        hot_words: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """使用AI生成话术"""
        # 构建提示词
        prompt = self._build_prompt(comments, hot_words)
        
        try:
            if self.ai_service == 'qwen':
                response = self._call_qwen_api(prompt)
            elif self.ai_service == 'deepseek':
                response = self._call_deepseek_api(prompt)
            elif self.ai_service == 'openai':
                response = self._call_openai_api(prompt)
            else:
                self.logger.warning(f"不支持的AI服务: {self.ai_service}")
                return self._generate_mock_tips(comments, hot_words)
            
            # 解析响应
            tips = self._parse_ai_response(response)
            self._remember_scripts(tips)
            return tips
            
        except Exception as e:
            self.logger.error(f"AI API调用失败: {e}")
            return []
    
    def _build_prompt(
        self,
        comments: List[Dict[str, Any]],
        hot_words: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """构建AI提示词：强调原始评论，由模型自主判断语境。"""
        # 提取最近评论（尽量还原口语与节奏）
        recent_comments = [str((comment or {}).get('content', '')).strip() for comment in comments[-20:]]
        comment_text = '\n'.join([c for c in recent_comments if c])
        if not comment_text:
            comment_text = "（暂无实时评论，请结合风格记忆输出基础互动话术）"

        # 提取热词
        hot_word_list = [str(w.get('word', '')).strip() for w in (hot_words or [])[:10] if w]
        hot_words_text = ', '.join([w for w in hot_word_list if w])
        hot_word_block = ""
        if hot_words_text:
            hot_word_block = (
                "【NLP参考热词】\n"
                f"{hot_words_text}\n"
                "（这些热词仅为粗糙提取，若与你的理解不符，请优先相信原始评论。）\n\n"
            )

        style_notes = ""
        if self.style_memory and self.style_memory.available():
            try:
                style_notes = self.style_memory.fetch_context(self.anchor_id, k=6)
            except Exception:
                style_notes = ""
        style_block = ""
        if style_notes:
            style_block = f"【历史画像与口头禅】\n{style_notes.strip()}\n\n"

        prompt = (
            "你是资深直播运营的话术助手，需要独立理解直播间语境。\n"
            "请优先依据原始评论推断观众关注点；若提供的热词与你的判断冲突，可忽略热词。\n"
            "输出严格为 JSON 数组，每个元素形如 {\"content\":\"...\",\"type\":\"interaction|emotion|product|question|transition\",\"tags\":[],\"priority\":1-5}。\n\n"
            f"{style_block}"
            f"【最近的观众评论节选】\n{comment_text}\n"
            f"{hot_word_block}"
            "生成要求：\n"
            "1) 文案需口语化、自然、贴近主播语言习惯；\n"
            "2) 鼓励互动或行动（关注/点赞/弹幕/提问/活动），可含转场、提醒、感谢等元素；\n"
            "3) 合规友好，避开敏感词、夸张承诺，照顾不同观众感受；\n"
            "4) 每条 18~40 个汉字，结构紧凑，避免重复口头禅；\n"
            "5) 至少返回 3 条候选话术，按 priority 从高到低排序。"
        )
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

    def _call_qwen_api(self, prompt: str) -> str:
        """调用Qwen OpenAI兼容API（DashScope compatible-mode）"""
        if not self.base_url or not self.api_key or not self.model:
            raise RuntimeError("Qwen API未配置完整")
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        data = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': '你是资深直播运营的话术助手，请严格输出JSON数组，不要附加解释。'},
                {'role': 'user', 'content': prompt},
            ],
            'temperature': 0.4,
            'max_tokens': 1000,
        }
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
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

            tips: List[Dict[str, Any]] = []
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

    def _resolve_anchor_id(self, config) -> Optional[str]:
        try:
            if hasattr(config, "get"):
                anchor = config.get("anchor_id") or config.get("douyin_room_id") or config.get("anchor_name")
                if anchor:
                    return str(anchor)
            if isinstance(config, dict):
                anchor = config.get("anchor_id") or config.get("douyin_room_id") or config.get("anchor_name")
                if anchor:
                    return str(anchor)
        except Exception:
            pass
        return None

    def _remember_scripts(self, scripts: List[Dict[str, Any]]) -> None:
        if not scripts or not self.style_memory or not self.style_memory.available():
            return
        try:
            self.style_memory.ingest_scripts(self.anchor_id, scripts)
        except Exception:
            pass
    
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

    def reset_memory(self, anchor_id: Optional[str] = None) -> None:
        """清除指定主播的风格记忆缓存"""
        target_anchor = anchor_id or self.anchor_id
        if not target_anchor or not self.style_memory:
            return
        if hasattr(self.style_memory, "reset_anchor_memory"):
            try:
                self.style_memory.reset_anchor_memory(target_anchor)
                self.logger.info("TipGenerator: 已重置主播 %s 的风格记忆", target_anchor)
            except Exception as exc:
                self.logger.warning("TipGenerator: 重置风格记忆失败: %s", exc)
        else:
            self.logger.debug("当前 StyleMemoryManager 不支持重置记忆接口")
    
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
            'ai_service': self.ai_service
        }
    
    def start_generating(self):
        """启动话术生成（后台任务）"""
        self.is_running = True
        self.logger.info("AI话术生成任务已启动")
        # 这里可以添加定期生成逻辑
        # 目前只是占位方法，实际生成在API调用时进行
