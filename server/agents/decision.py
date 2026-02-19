"""决策Agent

使用GLM-5进行深度决策分析，支持思考模式
"""
from typing import Any, Dict
from server.agents.base import BaseAgent, AgentResult
from server.ai.ai_gateway_v2 import get_gateway


class DecisionAgent(BaseAgent):
    """决策Agent (GLM-5深度思考)"""

    def __init__(self):
        super().__init__(
            name="decision_maker",
            provider="glm",
            model="glm-5",
            enable_thinking=True,  # 启用深度思考
        )
        self.gateway = get_gateway()
        # 在初始化时切换到正确的provider，避免每次run都切换
        self.gateway.switch_provider("glm", "glm-5")

    def run(self, state: Dict[str, Any]) -> AgentResult:
        """执行决策分析"""
        analysis = state.get("analysis_result", {})
        style_profile = state.get("style_profile", {})
        planner_notes = state.get("planner_notes", {})

        # 构建决策提示
        prompt = self._build_prompt(analysis, style_profile, planner_notes)

        try:
            # provider已在__init__中切换，此处直接调用
            result = self.gateway.chat_completion(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                enable_thinking=True,  # 启用思考模式
                temperature=0.7,
                max_tokens=2048,
            )

            return AgentResult(
                success=True,
                data={
                    "decision": result.get("content", ""),
                    "reasoning": result.get("reasoning", ""),
                }
            )
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                data={"decision": f"决策失败: {e}"}
            )

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是直播间决策助手，帮助主播做出最佳决策。

你需要：
1. 综合分析结果和风格画像
2. 考虑当前直播氛围
3. 给出具体可执行的建议

请先思考（在reasoning中），然后给出决策建议。"""

    def _build_prompt(
        self,
        analysis: dict,
        style_profile: dict,
        planner_notes: dict
    ) -> str:
        """构建决策提示词"""
        return f"""基于以下信息做出决策：

分析结果：
{analysis.get('analysis', '无')}

风格画像：
{style_profile.get('tone', '专业陪伴')}

规划笔记：
{planner_notes.get('selected_topic', {}).get('topic', '互动')}

请给出决策建议。"""
