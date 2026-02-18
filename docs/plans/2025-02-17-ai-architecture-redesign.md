# AI功能架构重构设计方案

**设计日期**: 2025-02-17
**设计版本**: v2.0
**项目**: 提猫直播助手（timao-douyin-live-manager）

## 一、设计目标

基于方案2（架构重构方案），全面升级AI系统，引入智谱GLM-5和MiniMax M2.5系列模型，构建多Agent协作的智能直播助手系统。

### 核心目标
- ✅ 降低AI成本（使用MiniMax高性价比模型）
- ✅ 提升AI质量（GLM-5面向Agent优化）
- ✅ 增加新AI能力（多模态、Agent工作流、工具调用）
- ✅ 改进架构设计（分层记忆、智能路由、SQLite迁移）

### 模型策略
**只使用GLM-5和MiniMax系列**，不再使用其他模型：
- **GLM-5**: 面向Agentic Engineering，支持深度思考（thinking模式）
- **MiniMax-M2.5**: 顶尖性能，极致性价比，支持100 TPS高速输出
- **MiniMax-M2.5-highspeed**: 极速版，推荐用于实时分析

---

## 二、整体架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    应用层 (Application Layer)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ 实时分析  │  │ 话术生成  │  │ 复盘总结  │  │ 多模态AI  │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼─────────────┼─────────────┼───────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│              AI网关 2.0 (智能路由 + 网关)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  智能路由引擎                                             │  │
│  │  - 场景识别 → 模型选择（GLM-5 或 MiniMax）                 │  │
│  │  - 成本优化 → 负载均衡                                    │  │
│  │  - 熔断降级 → 自动切换                                    │  │
│  │  - 思考模式管理（thinking / reasoning_split）             │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────┬──────────────────────────────────┐    │
│  │  智谱 GLM-5          │  MiniMax M2.5 系列               │    │
│  │  - glm-5            │  - MiniMax-M2.5                  │    │
│  │  (Agent工作流优化)   │  - MiniMax-M2.5-highspeed ⭐     │    │
│  │  (深度思考模式)      │  - MiniMax-M2.1                  │    │
│  │                     │  (100 TPS 极速输出)               │    │
│  └─────────────────────┴──────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│               Agent工作流层 (LangGraph 2.0)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Orchestrator (协调器)                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ 分析     │  │ 记忆     │  │ 决策     │  │ 多模态   │      │
│  │ Agent    │  │ Agent    │  │ Agent    │  │ Agent    │      │
│  │ (MiniMax)│  │ (GLM-5)  │  │ (GLM-5)  │  │ (未来)   │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  工具层 (Function Calling)                                │  │
│  │  - 搜索  - 计算  - API调用  - 知识检索  - MiniMax原生支持  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                 记忆层 (Memory System 2.0)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ 短期记忆  │  │ 中期记忆  │  │ 长期记忆  │                      │
│  │ (Redis)  │  │(ChromaDB)│  │ (SQLite) │                      │
│  │ 可选     │  │ 30天     │  │ 永久保存  │                      │
│  └──────────┘  └──────────┘  └──────────┘                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SQLite 数据库（替代MySQL）                                │  │
│  │  ├─ timao.db               (主数据库)                      │  │
│  │  ├─ ai/memory_vectors.db   (向量记忆)                      │  │
│  │  ├─ ai/style_profiles.db   (风格画像)                      │  │
│  │  └─ sessions/live_YYYY.db  (按月分库)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心设计原则

1. **模型专精化**：
   - **GLM-5**: 专用于Agent工作流、深度思考、风格分析、话术生成
   - **MiniMax-M2.5-highspeed**: 专用于实时分析、高速响应场景
   - **MiniMax-M2.5**: 专用于复盘总结、大上下文场景（204K tokens）

2. **分层记忆架构**：
   - 短期记忆（Redis/内存）: 当前会话实时上下文，1小时TTL
   - 中期记忆（ChromaDB）: 最近30天的直播记录和反馈，向量检索
   - 长期记忆（SQLite）: 永久保存的风格画像和高价值知识

3. **多Agent协作**：
   - Analyzer Agent（MiniMax）: 实时分析直播数据
   - Memory Agent（GLM-5）: 管理和检索记忆
   - Decision Agent（GLM-5）: 生成决策建议
   - Orchestrator: 协调多Agent并行工作

4. **SQLite优先**：
   - 降低部署复杂度（无需MySQL服务）
   - 适合Electron桌面应用
   - WAL模式提升并发性能
   - 按月分库避免单文件过大

---

## 三、AI网关 2.0 设计

### 3.1 模型配置

```python
# 只使用GLM-5和MiniMax系列
PROVIDERS = {
    "glm": {
        "api_key_env": "GLM_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-5"],
        "capabilities": {
            "thinking": True,           # 深度思考模式
            "agent_workflow": True,     # Agent工作流优化
            "reasoning_output": True,   # 推理过程输出
            "max_tokens": 65536,
        }
    },
    "minimax": {
        "api_key_env": "MINIMAX_API_KEY",
        "base_url": "https://api.minimaxi.com/v1",
        "models": [
            "MiniMax-M2.5",              # 顶尖性能
            "MiniMax-M2.5-highspeed",    # 极速版 ⭐
            "MiniMax-M2.1",
            "MiniMax-M2.1-highspeed",
            "MiniMax-M2",
        ],
        "capabilities": {
            "interleaved_thinking": True,   # 交错思维链
            "function_calling": True,       # 工具调用
            "high_speed": True,             # 100 TPS
            "large_context": 204800,        # 204K上下文
        }
    }
}
```

### 3.2 功能级模型分配

```python
FUNCTION_MODELS = {
    "live_analysis": {
        "provider": "minimax",
        "model": "MiniMax-M2.5-highspeed",  # 极速版，100 TPS
        "enable_thinking": False,           # 实时分析不需要思考过程
        "reason": "高速输出，降低延迟"
    },
    "style_profile": {
        "provider": "glm",
        "model": "glm-5",
        "enable_thinking": True,            # 启用深度思考
        "reason": "面向Agent优化，深度分析风格"
    },
    "script_generation": {
        "provider": "glm",
        "model": "glm-5",
        "enable_thinking": True,            # 启用深度思考
        "reason": "深度思考提升话术质量"
    },
    "live_review": {
        "provider": "minimax",
        "model": "MiniMax-M2.5",            # 复盘用标准版
        "enable_thinking": True,
        "reason": "204K大上下文，支持长复盘"
    },
    "reflection": {
        "provider": "glm",
        "model": "glm-5",
        "enable_thinking": True,
        "reason": "深度思考，评估分析质量"
    },
    "chat_focus": {
        "provider": "minimax",
        "model": "MiniMax-M2.5-highspeed",
        "enable_thinking": False,
        "reason": "快速摘要，降低延迟"
    },
    "topic_generation": {
        "provider": "glm",
        "model": "glm-5",
        "enable_thinking": True,
        "reason": "深度思考，生成智能话题"
    }
}
```

### 3.3 思考模式支持

```python
class ThinkingMode:
    """思考模式管理"""

    @staticmethod
    def enable_for_glm5(kwargs: dict) -> dict:
        """为GLM-5启用深度思考"""
        kwargs["thinking"] = {"type": "enabled"}
        return kwargs

    @staticmethod
    def enable_for_minimax(kwargs: dict) -> dict:
        """为MiniMax启用思考分离"""
        kwargs["extra_body"] = {"reasoning_split": True}
        return kwargs

    @staticmethod
    def parse_thinking_response(response, provider: str) -> dict:
        """解析包含思考过程的响应"""
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

        return {"reasoning": "", "content": choice.message.content}
```

### 3.4 智能路由策略

```python
async def smart_route(self, task_type: str, requirements: Dict[str, Any]) -> str:
    """智能路由 - 只在GLM-5和MiniMax之间选择"""

    # 实时分析任务 → MiniMax highspeed（100 TPS）
    if task_type == "live_analysis":
        latency = requirements.get("latency", "normal")
        if latency == "fast":
            return "minimax:MiniMax-M2.5-highspeed"  # 极速
        else:
            return "minimax:MiniMax-M2.5"

    # Agent工作流任务 → GLM-5（专为Agent打造）
    elif task_type in ["style_profile", "script_generation", "topic_generation"]:
        return "glm:glm-5"

    # 反思和推理任务 → GLM-5（深度思考）
    elif task_type == "reflection":
        return "glm:glm-5"

    # 复盘总结 → MiniMax M2.5（大上下文204K）
    elif task_type == "live_review":
        return "minimax:MiniMax-M2.5"

    # 快速摘要 → MiniMax highspeed
    elif task_type == "chat_focus":
        return "minimax:MiniMax-M2.5-highspeed"

    # 默认：MiniMax highspeed（性价比最高）
    return "minimax:MiniMax-M2.5-highspeed"
```

---

## 四、数据存储设计（SQLite）

### 4.1 数据库文件组织

```
data/
├── timao.db                 # 主数据库（用户、配置等）
├── ai/
│   ├── memory_vectors.db    # 向量记忆（ChromaDB）
│   ├── style_profiles.db    # 风格画像持久化
│   └── knowledge_cache.db   # 知识库本地缓存
└── sessions/
    ├── live_2024-01.db      # 按月分库的直播记录
    ├── live_2024-02.db
    └── live_2025-01.db
```

### 4.2 核心表结构

```sql
-- 向量记忆表（memory_vectors.db）
CREATE TABLE memory_vectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anchor_id TEXT NOT NULL,
    memory_type TEXT NOT NULL,  -- 'style', 'feedback', 'context'
    content TEXT NOT NULL,
    embedding BLOB,             -- 向量数据（二进制存储）
    metadata JSON,              -- 元数据（JSON格式）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    importance_score REAL DEFAULT 0.5
);

CREATE INDEX idx_memory_anchor ON memory_vectors(anchor_id);
CREATE INDEX idx_memory_type ON memory_vectors(memory_type);
CREATE INDEX idx_memory_importance ON memory_vectors(importance_score);

-- 风格画像表（style_profiles.db）
CREATE TABLE style_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anchor_id TEXT NOT NULL UNIQUE,
    profile_data JSON NOT NULL,     -- 完整画像数据
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 记忆摘要表（用于压缩旧记忆）
CREATE TABLE memory_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anchor_id TEXT NOT NULL,
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    summary_text TEXT,
    key_insights JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI调用日志（用于成本监控）
CREATE TABLE ai_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,         -- 'glm' or 'minimax'
    model TEXT NOT NULL,
    function TEXT NOT NULL,         -- 'live_analysis', 'style_profile'等
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    cost REAL,
    duration_ms REAL,
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_usage_provider ON ai_usage_logs(provider);
CREATE INDEX idx_usage_function ON ai_usage_logs(function);
CREATE INDEX idx_usage_created ON ai_usage_logs(created_at);
```

### 4.3 SQLite优化配置

```python
class SQLiteOptimizations:
    """SQLite性能优化"""

    @staticmethod
    def optimize_connection(conn):
        """优化SQLite连接"""
        conn.execute("PRAGMA journal_mode=WAL")        # 写前日志
        conn.execute("PRAGMA synchronous=NORMAL")      # 平衡性能和安全
        conn.execute("PRAGMA cache_size=-64000")       # 64MB缓存
        conn.execute("PRAGMA temp_store=MEMORY")       # 临时表在内存
        conn.execute("PRAGMA mmap_size=268435456")     # 256MB内存映射
        conn.execute("PRAGMA foreign_keys=ON")         # 启用外键约束
        return conn
```

---

## 五、Agent工作流设计

### 5.1 LangGraph 2.0工作流

```python
class LiveAnalysisWorkflow:
    """直播分析多Agent工作流"""

    def _build_graph(self) -> StateGraph:
        """构建Agent协作图"""

        graph = StateGraph(AgentState)

        # 节点定义
        graph.add_node("coordinator", self._coordinator_node)
        graph.add_node("memory_loader", self._memory_loader_node)
        graph.add_node("signal_collector", self._signal_collector_node)
        graph.add_node("parallel_analysis", self._parallel_analysis_node)
        graph.add_node("analyzer", self._analyzer_node)           # MiniMax
        graph.add_node("multimodal_analyzer", self._multimodal_node)
        graph.add_node("decision_maker", self._decision_node)     # GLM-5
        graph.add_node("memory_updater", self._memory_updater_node)
        graph.add_node("reflection", self._reflection_node)       # GLM-5

        # 工作流定义
        graph.set_entry_point("coordinator")
        graph.add_edge("coordinator", "memory_loader")
        graph.add_edge("memory_loader", "signal_collector")
        graph.add_edge("signal_collector", "parallel_analysis")

        # 并行分析分支
        graph.add_edge("parallel_analysis", "analyzer")
        graph.add_edge("parallel_analysis", "multimodal_analyzer")

        # 汇聚到决策节点
        graph.add_edge("analyzer", "decision_maker")
        graph.add_edge("multimodal_analyzer", "decision_maker")

        # 反思循环
        graph.add_conditional_edges(
            "decision_maker",
            self._should_reflect,
            {
                True: "reflection",
                False: "memory_updater"
            }
        )
        graph.add_edge("reflection", "analyzer")
        graph.add_edge("memory_updater", END)

        return graph
```

### 5.2 Agent角色分配

| Agent | 使用模型 | 职责 |
|-------|---------|------|
| Analyzer Agent | MiniMax-M2.5-highspeed | 实时分析直播数据，高速响应 |
| Memory Agent | GLM-5 | 管理记忆存储和检索，深度思考 |
| Decision Agent | GLM-5 | 生成决策建议，深度推理 |
| Reflection Agent | GLM-5 | 评估分析质量，自我改进 |
| Multimodal Agent | GLM-5（未来）| 视觉分析，图片理解 |

### 5.3 工具调用（Function Calling）

MiniMax原生支持Function Calling：

```python
# 定义可用工具
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_internet",
            "description": "搜索互联网获取实时信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_knowledge",
            "description": "从知识库检索话术和技巧",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "category": {"type": "string", "enum": ["话术", "技巧", "案例"]}
                },
                "required": ["query"]
            }
        }
    }
]
```

---

## 六、成本分析

### 6.1 模型定价对比（估算）

| 模型 | 输入价格（元/1M tokens） | 输出价格（元/1M tokens） | 特点 |
|------|------------------------|------------------------|------|
| MiniMax-M2.5-highspeed | ~0.6 | ~0.6 | 极速100 TPS，性价比高 |
| MiniMax-M2.5 | ~2.0 | ~2.0 | 顶尖性能，204K上下文 |
| GLM-5 | ~5.0 | ~5.0 | Agent优化，深度思考 |

### 6.2 成本优化策略

1. **实时分析** → MiniMax-M2.5-highspeed（最便宜）
2. **深度分析** → GLM-5（质量优先）
3. **复盘总结** → MiniMax-M2.5（大上下文，一次完成）

预期整体AI成本降低 **30-50%**（相比使用讯飞+Qwen+Gemini组合）

---

## 七、实施计划概览

### Phase 1: AI网关2.0重构（3-4周）
- 集成GLM-5和MiniMax M2.5
- 实现思考模式支持
- 智能路由引擎
- 流式输出优化

### Phase 2: 数据迁移SQLite（2-3周）
- MySQL → SQLite迁移
- 按月分库策略
- ChromaDB向量存储
- WAL模式优化

### Phase 3: Agent工作流重构（3-4周）
- LangGraph 2.0升级
- 多Agent协作实现
- 工具调用集成
- 反思机制

### Phase 4: 测试与优化（2周）
- 性能测试
- 成本监控
- 灰度发布

**总计**: 10-13周

---

## 八、风险与应对

### 8.1 技术风险
- **API兼容性**: GLM-5和MiniMax都支持OpenAI兼容格式，风险低
- **性能风险**: MiniMax highspeed版本100 TPS，性能有保障
- **数据迁移**: SQLite迁移需充分测试

### 8.2 成本风险
- **GLM-5价格较高**: 仅用于深度分析场景，控制使用量
- **监控机制**: 实时监控AI成本，异常告警

---

## 九、总结

本设计方案通过引入GLM-5和MiniMax M2.5系列模型，构建了：

✅ **更智能的Agent系统**（GLM-5面向Agent优化）
✅ **更快的响应速度**（MiniMax 100 TPS）
✅ **更低的成本**（MiniMax高性价比）
✅ **更简洁的架构**（SQLite替代MySQL）
✅ **更强的记忆系统**（分层记忆+向量检索）

这个设计将为提猫直播助手带来质的飞跃，打造真正智能的直播AI助手。
