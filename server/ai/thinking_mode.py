"""思考模式管理器

支持GLM-5和MiniMax的思考模式
"""
from typing import Any, Dict


class ThinkingMode:
    """思考模式管理器"""

    @staticmethod
    def enable_for_glm5(kwargs: dict) -> dict:
        """为GLM-5启用深度思考模式

        Args:
            kwargs: 原始请求参数

        Returns:
            添加了thinking参数的请求参数
        """
        kwargs["thinking"] = {"type": "enabled"}
        return kwargs

    @staticmethod
    def enable_for_minimax(kwargs: dict) -> dict:
        """为MiniMax启用思考分离模式

        Args:
            kwargs: 原始请求参数

        Returns:
            添加了extra_body参数的请求参数
        """
        kwargs["extra_body"] = {"reasoning_split": True}
        return kwargs

    @staticmethod
    def parse_thinking_response(response: Any, provider: str) -> Dict[str, str]:
        """解析包含思考过程的响应

        Args:
            response: API响应对象
            provider: 服务商名称（'glm' 或 'minimax'）

        Returns:
            包含 reasoning 和 content 的字典
        """
        choice = response.choices[0]

        if provider == "glm":
            # GLM-5: reasoning_content + content
            return {
                "reasoning": getattr(choice.message, 'reasoning_content', ''),
                "content": choice.message.content,
            }
        elif provider == "minimax":
            # MiniMax: reasoning_details + content
            reasoning_text = ""
            if hasattr(choice.message, 'reasoning_details'):
                reasoning_text = "".join(
                    detail.get("text", "")
                    for detail in choice.message.reasoning_details
                )
            return {
                "reasoning": reasoning_text,
                "content": choice.message.content,
            }

        # 默认返回空推理
        return {"reasoning": "", "content": choice.message.content}
