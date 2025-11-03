"""
科大讯飞 Lite 模型客户端
使用 OpenAI-compatible API 接口调用讯飞星火 Lite 模型
用于 AI 分析、话术生成、直播间氛围与情绪分析
"""

from __future__ import annotations

import os
import time
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

# 科大讯飞星火配置
DEFAULT_XUNFEI_API_KEY = os.getenv("XUNFEI_API_KEY", "")
DEFAULT_XUNFEI_BASE_URL = os.getenv("XUNFEI_BASE_URL", "https://spark-api-open.xf-yun.com/v1")
DEFAULT_XUNFEI_MODEL = os.getenv("XUNFEI_MODEL", "lite")

# 可用模型
XUNFEI_MODELS = {
    "lite": "讯飞星火-Lite",
    "generalv3": "讯飞星火-V3.0",
    "generalv3.5": "讯飞星火-V3.5",
    "4.0Ultra": "讯飞星火-V4.0 Ultra",
}


@dataclass
class XunfeiUsage:
    """讯飞 API 使用量"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    request_time_ms: float


class XunfeiLiteClient:
    """科大讯飞 Lite 模型客户端"""
    
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None
    ):
        """
        初始化讯飞客户端
        
        Args:
            api_key: API密钥，格式为 "APPID:APISecret"
            base_url: API基础URL
            model: 模型名称
        """
        self.api_key = api_key or DEFAULT_XUNFEI_API_KEY
        self.base_url = base_url or DEFAULT_XUNFEI_BASE_URL
        self.model = model or DEFAULT_XUNFEI_MODEL
        
        if not self.api_key:
            raise ValueError("XUNFEI_API_KEY 未配置，请设置环境变量或传入 api_key 参数")
        
        if OpenAI is None:
            raise RuntimeError("openai package 未安装，请运行: pip install openai")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> tuple[str, XunfeiUsage]:
        """
        调用聊天完成 API
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
            
        Returns:
            tuple: (响应内容, 使用量统计)
        """
        start_time = time.time()
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        request_time_ms = (time.time() - start_time) * 1000
        
        content = response.choices[0].message.content
        usage = response.usage
        
        xunfei_usage = XunfeiUsage(
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            request_time_ms=request_time_ms
        )
        
        return content, xunfei_usage
    
    def analyze_live_atmosphere(
        self,
        transcript: str,
        comments: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        分析直播间氛围与情绪
        
        Args:
            transcript: 主播口播转写
            comments: 弹幕评论列表
            context: 上下文信息
            
        Returns:
            Dict: 分析结果
        """
        # 构建分析提示
        prompt = self._build_atmosphere_prompt(transcript, comments, context)
        
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一位专业的直播运营分析师，擅长分析直播间氛围与观众情绪。"
                    "请基于主播的口播内容和观众弹幕，分析当前直播间的氛围状态。"
                    "输出严格的 JSON 格式，包含以下字段："
                    "{"
                    "  \"atmosphere\": {\"level\": \"冷淡/一般/活跃/火爆\", \"score\": 0-100, \"description\": \"氛围描述\"},"
                    "  \"emotion\": {\"primary\": \"主要情绪\", \"secondary\": \"次要情绪\", \"intensity\": 0-100},"
                    "  \"engagement\": {\"interaction_rate\": 0-100, \"positive_rate\": 0-100},"
                    "  \"trends\": [\"趋势1\", \"趋势2\"],"
                    "  \"suggestions\": [\"建议1\", \"建议2\"]"
                    "}"
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        content, usage = self.chat_completion(messages, temperature=0.5)
        
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            result = {
                "atmosphere": {"level": "未知", "score": 0, "description": "解析失败"},
                "raw": content
            }
        
        result["_usage"] = {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "request_time_ms": usage.request_time_ms
        }
        
        return result
    
    def generate_script(
        self,
        script_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成直播话术
        
        Args:
            script_type: 话术类型（interaction/engagement/clarification等）
            context: 上下文信息
            
        Returns:
            Dict: 生成的话术
        """
        prompt = self._build_script_prompt(script_type, context)
        
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一位专业的直播话术生成助手，擅长生成自然流畅的直播口播内容。"
                    "话术要求："
                    "1. 自然口语化，避免生硬"
                    "2. 长度控制在 18-32 个中文字符"
                    "3. 符合直播场景，有感染力"
                    "4. 避免敏感词和违规内容"
                    "输出 JSON 格式：{\"line\": \"话术内容\", \"tone\": \"语气提示\", \"tags\": [\"标签1\", \"标签2\"]}"
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        content, usage = self.chat_completion(messages, temperature=0.7, max_tokens=300)
        
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            result = {
                "line": content,
                "tone": "自然",
                "tags": []
            }
        
        result["_usage"] = {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "request_time_ms": usage.request_time_ms
        }
        
        return result
    
    def analyze_realtime(
        self,
        transcript: str,
        comments: List[Dict[str, Any]],
        previous_summary: str = None,
        anchor_id: str = None
    ) -> Dict[str, Any]:
        """
        实时分析（窗口级分析）
        
        Args:
            transcript: 口播转写
            comments: 弹幕评论
            previous_summary: 上一窗口摘要
            anchor_id: 主播ID
            
        Returns:
            Dict: 实时分析结果
        """
        # 提取评论摘要
        comments_digest = self._digest_comments(comments)
        
        messages = [
            {
                "role": "system",
                "content": (
                    "你是直播运营总监风格的AI教练，针对最近窗口做'节奏复盘+下一步建议'。"
                    "输出严格JSON：{"
                    "  \"summary\": \"窗口摘要\","
                    "  \"highlight_points\": [\"亮点1\", \"亮点2\"],"
                    "  \"risks\": [\"风险1\", \"风险2\"],"
                    "  \"suggestions\": [\"建议1\", \"建议2\"],"
                    "  \"scripts\": [{\"text\": \"话术\", \"type\": \"类型\", \"tags\": [\"标签\"]}],"
                    "  \"atmosphere\": {\"level\": \"冷淡/一般/活跃/火爆\", \"score\": 0-100},"
                    "  \"emotion\": {\"primary\": \"主要情绪\", \"intensity\": 0-100}"
                    "}"
                )
            },
            {
                "role": "user",
                "content": f"""
【上一窗口摘要】
{previous_summary or '（首次分析）'}

【本窗口口播】
{transcript[:2000]}

【弹幕摘要】
{comments_digest}
"""
            }
        ]
        
        content, usage = self.chat_completion(messages, temperature=0.4)
        
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            result = {"raw": content, "error": "JSON解析失败"}
        
        result["_usage"] = {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "request_time_ms": usage.request_time_ms
        }
        
        return result
    
    def _build_atmosphere_prompt(
        self,
        transcript: str,
        comments: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> str:
        """构建氛围分析提示"""
        comments_text = "\n".join([
            f"{c.get('user', '观众')}: {c.get('content', '')}"
            for c in comments[:50]
        ])
        
        prompt = f"""
【主播口播】
{transcript[:1000]}

【观众弹幕】
{comments_text}

【分析要求】
1. 评估直播间当前氛围（冷淡/一般/活跃/火爆）
2. 分析观众主要情绪（兴奋/好奇/平淡/负面等）
3. 评估互动参与度和正向比例
4. 识别氛围变化趋势
5. 提供改善建议
"""
        
        if context:
            prompt += f"\n【上下文信息】\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        
        return prompt
    
    def _build_script_prompt(
        self,
        script_type: str,
        context: Dict[str, Any]
    ) -> str:
        """构建话术生成提示"""
        type_desc = {
            "interaction": "互动引导话术，引导观众参与互动",
            "engagement": "关注点赞召唤话术，引导用户关注点赞",
            "clarification": "澄清回应话术，回应观众疑问",
            "humor": "幽默活跃话术，活跃直播间氛围",
            "transition": "转场过渡话术，平滑切换话题",
            "call_to_action": "行动召唤话术，引导用户行动"
        }.get(script_type, "通用话术")
        
        prompt = f"""
【话术类型】{type_desc}

【上下文信息】
{json.dumps(context, ensure_ascii=False, indent=2)}

【生成要求】
1. 自然口语化，符合直播场景
2. 长度 18-32 个中文字符
3. 有感染力，能引起共鸣
4. 避免生硬的广告语
"""
        
        return prompt
    
    def _digest_comments(self, comments: List[Dict[str, Any]]) -> str:
        """提取评论摘要"""
        if not comments:
            return "（暂无弹幕）"
        
        # 统计活跃用户
        user_count = {}
        texts = []
        
        for c in comments[:100]:
            user = c.get("user", "观众")
            content = c.get("content", "")
            if content:
                texts.append(f"{user}: {content}")
                user_count[user] = user_count.get(user, 0) + 1
        
        top_users = sorted(user_count.items(), key=lambda x: x[1], reverse=True)[:5]
        top_users_text = ", ".join([f"{u}({c}条)" for u, c in top_users])
        
        digest = f"活跃用户：{top_users_text}\n\n"
        digest += "\n".join(texts[:30])
        
        return digest


def get_xunfei_client(
    api_key: str = None,
    base_url: str = None,
    model: str = None
) -> XunfeiLiteClient:
    """
    获取讯飞客户端实例
    
    Args:
        api_key: API密钥
        base_url: API基础URL
        model: 模型名称
        
    Returns:
        XunfeiLiteClient: 客户端实例
    """
    return XunfeiLiteClient(
        api_key=api_key,
        base_url=base_url,
        model=model
    )

