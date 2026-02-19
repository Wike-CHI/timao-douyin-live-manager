# Agent工作流V2使用指南

## 概述

Agent工作流V2是提猫直播助手的智能分析核心，使用LangGraph编排多个Agent协作完成直播分析任务。

## 架构

### 工作流图

```
memory_loader → analyzer → decision_maker
                               ↓
                          reflection (条件)
                          ↙        ↘
                    (retry)        (done)
                      ↓              ↓
                  analyzer      memory_updater → END
```

### Agent组成

| Agent | 模型 | 用途 |
|-------|------|------|
| MemoryAgent | GLM-5 | 记忆加载和保存，与SQLite交互 |
| AnalyzerAgent | MiniMax-M2.5-highspeed | 实时分析直播数据 |
| DecisionAgent | GLM-5 | 深度决策分析，支持思考模式 |
| ReflectionAgent | GLM-5 | 评估分析质量，触发重试 |

## 快速开始

### 基本使用

```python
from server.agents import LiveAnalysisWorkflowV2

# 创建工作流实例
workflow = LiveAnalysisWorkflowV2()

# 准备输入状态
state = {
    "anchor_id": "anchor_001",
    "transcript_snippet": "大家好，欢迎来到直播间",
    "chat_signals": [
        {"text": "主播好", "weight": 0.6, "category": "support"}
    ],
    "vibe": {"level": "positive", "score": 75},
}

# 执行工作流
result = workflow.invoke(state)

# 获取决策结果
decision = result.get("decision_result", {}).get("decision", "")
print(f"决策建议: {decision}")
```

### 使用配置

```python
# 自定义配置
result = workflow.invoke(
    state,
    config={
        "configurable": {
            "thread_id": "session_123"  # 用于状态持久化
        }
    }
)
```

## API参考

### LiveAnalysisWorkflowV2

主工作流类，编排所有Agent协作。

#### 构造函数

```python
LiveAnalysisWorkflowV2()
```

#### 方法

##### invoke(state, config=None)

执行完整工作流。

**参数:**
- `state` (dict): 输入状态
  - `anchor_id` (str, optional): 主播ID
  - `transcript_snippet` (str): 主播口播文本
  - `chat_signals` (list): 弹幕信号列表
  - `vibe` (dict): 氛围状态
- `config` (dict, optional): 配置选项
  - `configurable.thread_id`: 会话线程ID

**返回:**
- `dict`: 工作流结果
  - `analysis_result`: 分析结果
  - `decision_result`: 决策建议
  - `reflection_result`: 反思评估
  - `memory_result`: 记忆操作结果

### WorkflowState

工作流状态类型定义。

```python
class WorkflowState(TypedDict, total=False):
    anchor_id: Optional[str]
    transcript_snippet: str
    chat_signals: list
    vibe: dict
    persona: dict
    memory_result: dict
    analysis_result: dict
    decision_result: dict
    reflection_result: dict
    retry_count: int
    max_retries: int
```

### 单个Agent

#### AnalyzerAgent

```python
from server.agents import AnalyzerAgent

agent = AnalyzerAgent()
result = agent.run({
    "transcript_snippet": "主播口播内容",
    "chat_signals": [...],
    "vibe": {"level": "neutral", "score": 50}
})
```

#### DecisionAgent

```python
from server.agents import DecisionAgent

agent = DecisionAgent()
result = agent.run({
    "analysis_result": {"analysis": "分析结果"},
    "style_profile": {"tone": "专业"},
    "planner_notes": {"selected_topic": {"topic": "互动"}}
})
```

#### ReflectionAgent

```python
from server.agents import ReflectionAgent

agent = ReflectionAgent()
result = agent.run({
    "analysis_result": {"analysis": "分析内容"},
    "decision_result": {"decision": "决策建议"}
})

# 检查是否需要重试
if result.data["needs_retry"]:
    print("质量不达标，需要重试")
```

#### MemoryAgent

```python
from server.agents import MemoryAgent

agent = MemoryAgent()

# 加载记忆
result = agent.run({
    "memory_action": "load",
    "anchor_id": "anchor_001"
})

# 保存记忆
result = agent.run({
    "memory_action": "save",
    "anchor_id": "anchor_001",
    "memory_content": "新的记忆内容",
    "memory_type": "feedback"
})
```

## 工作流机制

### 反思循环

工作流会在每次决策后进行质量评估：
1. ReflectionAgent 评估分析质量 (0.0-1.0)
2. 如果质量 < 0.7 且重试次数 < 2，触发重试
3. 最多重试2次

### 状态持久化

工作流使用LangGraph的MemorySaver进行状态持久化：
- 每个thread_id对应独立的会话状态
- 可用于多轮对话场景

### 错误处理

所有Agent都有错误处理：
- 失败时返回 `success=False` 和 `error` 信息
- 工作流会继续执行，不会因单个Agent失败而中断

## 数据库集成

MemoryAgent 与 SQLite 数据库交互：

### 记忆表结构

```sql
CREATE TABLE memory_vectors (
    id INTEGER PRIMARY KEY,
    anchor_id TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSON,
    importance_score REAL DEFAULT 0.5
);
```

## 测试

运行测试：

```bash
# 运行所有Agent测试
pytest tests/agents/ -v

# 运行集成测试
pytest tests/agents/test_workflow_integration.py -v

# 运行单个测试文件
pytest tests/agents/test_workflow_v2.py -v
```

## 注意事项

1. **AI Gateway配置**: 确保 `.env` 中配置了正确的 API Key
2. **SQLite初始化**: 首次使用需要运行数据库初始化
3. **线程安全**: 工作流实例不是线程安全的，每个线程应创建独立实例

## 更新日志

### v2.0 (2025-02-17)
- 重构为多Agent架构
- 集成AI Gateway V2 (GLM-5 + MiniMax)
- 添加反思和重试机制
- SQLite记忆持久化
- LangGraph工作流编排
