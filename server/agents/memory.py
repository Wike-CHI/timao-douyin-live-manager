"""记忆管理Agent

使用GLM-5管理记忆存储和检索，与SQLite数据库交互
"""
from typing import Any, Dict
from server.agents.base import BaseAgent, AgentResult
from server.ai.ai_gateway_v2 import get_gateway
from server.database import get_sqlite_manager


class MemoryAgent(BaseAgent):
    """记忆管理Agent (GLM-5)"""

    def __init__(self):
        super().__init__(
            name="memory",
            provider="glm",
            model="glm-5",
            enable_thinking=True,
        )
        self.gateway = get_gateway()
        # 在初始化时切换到正确的provider，避免每次run都切换
        self.gateway.switch_provider("glm", "glm-5")
        self._db_manager = None

    def _get_db(self):
        """懒加载数据库管理器"""
        if self._db_manager is None:
            self._db_manager = get_sqlite_manager()
        return self._db_manager

    def run(self, state: Dict[str, Any]) -> AgentResult:
        """执行记忆操作"""
        action = state.get("memory_action", "load")
        anchor_id = state.get("anchor_id", "default")

        if action == "load":
            return self._load_memory(anchor_id)
        elif action == "save":
            return self._save_memory(anchor_id, state)
        else:
            return AgentResult(
                success=False,
                error=f"未知记忆操作: {action}"
            )

    def _load_memory(self, anchor_id: str) -> AgentResult:
        """加载记忆"""
        try:
            db = self._get_db()
            engine = db.get_ai_database("memory_vectors")

            with engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("""
                    SELECT content, metadata, importance_score
                    FROM memory_vectors
                    WHERE anchor_id = :anchor_id
                    ORDER BY importance_score DESC
                    LIMIT 10
                """), {"anchor_id": anchor_id})

                memories = [
                    {
                        "content": row[0],
                        "metadata": row[1],
                        "importance": row[2],
                    }
                    for row in result.fetchall()
                ]

            return AgentResult(
                success=True,
                data={"memories": memories}
            )
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                data={"memories": []}
            )

    def _save_memory(self, anchor_id: str, state: Dict[str, Any]) -> AgentResult:
        """保存记忆"""
        content = state.get("memory_content", "")
        memory_type = state.get("memory_type", "context")

        if not content:
            return AgentResult(
                success=True,
                data={"saved": False, "reason": "无内容"}
            )

        try:
            db = self._get_db()
            engine = db.get_ai_database("memory_vectors")

            with engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("""
                    INSERT INTO memory_vectors
                    (anchor_id, memory_type, content, importance_score)
                    VALUES (:anchor_id, :memory_type, :content, 0.5)
                """), {
                    "anchor_id": anchor_id,
                    "memory_type": memory_type,
                    "content": content,
                })
                conn.commit()

            return AgentResult(
                success=True,
                data={"saved": True}
            )
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                data={"saved": False}
            )
