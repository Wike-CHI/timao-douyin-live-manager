"""反思Agent

使用GLM-5评估分析质量，触发重新分析
"""
import re
from typing import Any, Dict
from server.agents.base import BaseAgent, AgentResult
from server.ai.ai_gateway_v2 import get_gateway


class ReflectionAgent(BaseAgent):
    """反思Agent (GLM-5评估质量)"""

    QUALITY_THRESHOLD = 0.7  # 质量阈值

    def __init__(self):
        super().__init__(
            name="reflection",
            provider="glm",
            model="glm-5",
            enable_thinking=True,
        )
        self.gateway = get_gateway()
        # 在初始化时切换到正确的provider，避免每次run都切换
        self.gateway.switch_provider("glm", "glm-5")

    def run(self, state: Dict[str, Any]) -> AgentResult:
        """评估分析质量"""
        analysis = state.get("analysis_result", {})
        decision = state.get("decision_result", {})

        try:
            # provider已在__init__中切换，此处直接调用
            result = self.gateway.chat_completion(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": self._build_prompt(analysis, decision)},
                ],
                enable_thinking=True,
                temperature=0.3,  # 低温度保持一致性
                max_tokens=512,
            )

            content = result.get("content", "")
            quality_score = self._extract_score(content)
            needs_retry = quality_score < self.QUALITY_THRESHOLD

            return AgentResult(
                success=True,
                data={
                    "quality_score": quality_score,
                    "needs_retry": needs_retry,
                    "reflection": content,
                    "reasoning": result.get("reasoning", ""),
                }
            )
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                data={"quality_score": 0.5, "needs_retry": False}
            )

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是分析质量评估专家。

评估分析结果的：
1. 相关性 - 是否与直播内容相关
2. 完整性 - 是否覆盖关键点
3. 可操作性 - 建议是否具体可行

输出格式：
质量评分: [0.0-1.0]
需要重试: [是/否]
问题说明: [如有]"""

    def _build_prompt(self, analysis: dict, decision: dict) -> str:
        """构建评估提示词"""
        analysis_text = analysis.get('analysis', '无')
        decision_text = decision.get('decision', '无')

        # 截断过长的内容
        analysis_text = analysis_text[:500] if len(analysis_text) > 500 else analysis_text
        decision_text = decision_text[:500] if len(decision_text) > 500 else decision_text

        return f"""请评估以下分析质量：

分析内容：
{analysis_text}

决策建议：
{decision_text}

请给出质量评分。"""

    def _extract_score(self, content: str) -> float:
        """从内容中提取评分"""
        match = re.search(r"质量评分[：:]\s*([\d.]+)", content)
        if match:
            try:
                score = float(match.group(1))
                # 确保评分在有效范围内
                return max(0.0, min(1.0, score))
            except ValueError:
                pass
        return 0.7  # 默认评分
