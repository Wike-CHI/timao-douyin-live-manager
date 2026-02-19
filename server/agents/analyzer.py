"""实时分析Agent

使用MiniMax-M2.5-highspeed进行高速实时分析
"""
from typing import Any, Dict
from server.agents.base import BaseAgent, AgentResult
from server.ai.ai_gateway_v2 import get_gateway


class AnalyzerAgent(BaseAgent):
    """实时分析Agent (MiniMax高速模型)"""

    def __init__(self):
        super().__init__(
            name="analyzer",
            provider="minimax",
            model="MiniMax-M2.5-highspeed",
            enable_thinking=False,  # 实时分析不需要思考过程
        )
        self.gateway = get_gateway()
        # 在初始化时切换到正确的provider，避免每次run都切换
        self.gateway.switch_provider("minimax", "MiniMax-M2.5-highspeed")

    def run(self, state: Dict[str, Any]) -> AgentResult:
        """执行实时分析"""
        transcript = state.get("transcript_snippet", "")
        chat_signals = state.get("chat_signals", [])
        vibe = state.get("vibe", {})

        # 构建分析提示
        prompt = self._build_prompt(transcript, chat_signals, vibe)

        try:
            # provider已在__init__中切换，此处直接调用
            result = self.gateway.chat_completion(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                enable_thinking=False,
                temperature=0.7,
                max_tokens=1024,
            )

            return AgentResult(
                success=True,
                data={
                    "analysis": result.get("content", ""),
                    "reasoning": result.get("reasoning", ""),
                }
            )
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                data={"analysis": f"分析失败: {e}"}
            )

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是直播间实时分析助手。
分析主播的口播内容和观众弹幕，提供简洁的实时分析。
输出格式：
1. 当前状态（一句话）
2. 主要关注点
3. 建议行动"""

    def _build_prompt(
        self,
        transcript: str,
        chat_signals: list,
        vibe: dict
    ) -> str:
        """构建分析提示词"""
        chat_summary = "\n".join([
            f"- {sig.get('text', '')} (权重:{sig.get('weight', 0):.1f})"
            for sig in chat_signals[-10:]
        ])

        return f"""请分析当前直播状态：

主播口播：
{transcript or "（暂无）"}

最近弹幕：
{chat_summary or "（暂无）"}

氛围状态：{vibe.get('level', 'neutral')} ({vibe.get('score', 0)}分)

请提供分析。"""