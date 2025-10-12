# 直播 AI 话术 LangChain/LangGraph 工作流规划

## 目标与原则

- **主播风格保真**：每位主播的记忆、禁忌、口癖独立存放在 `records/memory/<主播ID>/`，生成话术时始终注入对应人格。
- **实时感知 + 及时响应**：每个窗口（默认 30–60 秒）整合语音/VAD 分析、弹幕热点、互动量，驱动 LangGraph 流程。
- **可落地迭代**：工作流拆分为明确节点，支持离线单元测试与热更新；UI 侧新增“话术窗口”可视化评分入口。

## LangGraph 总体拓扑

```
START
 ├─ MemoryLoader → SignalCollector → TopicDetector → MoodEstimator
 ├─ Planner ─┬─ Flow A: 深挖话题 → ScriptGenerator → ScoreAssessor
 │           ├─ Flow B: 暖场补能 → ScriptGenerator → ScoreAssessor
 │           └─ Flow C: 行动号召 → ScriptGenerator → ScoreAssessor
 └─ SummaryNode → MemoryUpdater → END
```

- **MemoryLoader**：读取主播 `profile.json` + `history.jsonl`，返回人格（tone）、禁忌、近期高分话术。
- **SignalCollector**：拉取最新转写摘要、弹幕 top-K、互动统计、ws 心跳等指标。
- **TopicDetector**：LangChain Prompt + 轻量分类器，生成候选话题锚点（含置信度）。
- **MoodEstimator**：基于情绪关键词、语速、静音时长、弹幕热度评估 `calm / hype / stressed`。
- **Planner**：根据话题+情绪选择子流程 Prompt，触发不同的 LangChain `LLMChain`。
- **ScriptGenerator**：一次产出 2–3 条口语化话术（结构：text+vibe+关键词），依赖主播记忆和当前话题。
- **ScoreAssessor**：结合规则/LLM 打分；高分写入 `feedback/good.jsonl`；低分写入 `feedback/bad.jsonl` 供负向提示。
- **SummaryNode**：汇总亮点、风险、建议、精选话术 → 推送 SSE/WS；前端同时展示话术评分入口。
- **MemoryUpdater**：持久化新的高分话术与话题标签，定期裁剪历史，避免记忆暴增。

## 关键数据结构

```json
GraphState {
  "broadcaster_id": "143742277431",
  "window_start": 1697100000,
  "transcript_snippet": "...",
  "chat_signals": [{ "text": "...", "weight": 0.9 }, ...],
  "topic_candidates": [{ "topic": "买车", "confidence": 0.82 }],
  "mood": "stressed",
  "persona": { "tone": "西南方言+幽默", "taboo": ["医学建议"] },
  "memory_refs": { "good_scripts": [...], "bad_scripts": [...] }
}
```

## 伪代码示例

```python
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

graph = StateGraph(GraphState)
graph.add_node("memory_loader", load_persona)
graph.add_node("signal_collector", gather_signals)
graph.add_node("topic_detector", detect_topics)
graph.add_node("mood_estimator", estimate_mood)
graph.add_node("planner", plan_route)
graph.add_conditional_edges(
    "planner",
    route_fn,
    {
        "deep_dive": "script_gen_deep",
        "warm_up": "script_gen_warm",
        "promo": "script_gen_promo",
    }
)
graph.add_node("summary", assemble_summary)
graph.add_node("memory_updater", update_memory)
graph.compose([
    "memory_loader", "signal_collector", "topic_detector",
    "mood_estimator", "planner", "summary", "memory_updater"
])
workflow = graph.compile(checkpointer=MemorySaver())
# 在 SSE handler 中运行 workflow.invoke(graph_state)
```

## 文件与目录约定

- `records/memory/<主播ID>/profile.json`：人物设定、禁忌词、情绪策略。
- `records/memory/<主播ID>/history.jsonl`：高分话术（包含 text、评分、场景标签）。
- `records/memory/<主播ID>/feedback_good.jsonl` / `feedback_bad.jsonl`：用户评分结果，供 `ScoreAssessor` 过滤。
- `records/ai_logs/graph/<日期>.log`：LangGraph 节点执行日志，方便回溯问题。

## 接口与前端联动

- `/api/ai/live/stream`：返回 `summary + scripts + scores`，前端“话术窗口”根据评分颜色标注，并允许手动打分（写回 `/api/ai/live/feedback`）。
- `/api/ai/live/memory`：暴露查询/编辑主播记忆的接口，供运营配置器使用。
- 前端 Tools “运行环境”卡片已支持 `LIVE_FORCE_DEVICE` 和 `prepare:torch`，确保 GPU 推理链路稳定。

## 后续任务

1. **实现各 LangChain 节点**：编写 `load_persona`, `gather_signals`, `script_gen_*` 等模块，单元测试 Prompt。
2. **记忆管理脚本**：提供 CLI 批量整理/合并 `history.jsonl`，并设置大小上限。
3. **UI 打分回写**：在“话术窗口”加入打分按钮 → 调用 `/api/ai/live/feedback`，更新 good/bad 列表。
4. **安全与审计**：在 `SummaryNode` 输出前增加敏感词审查，必要时回退到安全模板。

> 该规划旨在将直播 AI 话术从“单轮生成”升级为 **记忆驱动的动态工作流**，确保结果更接地气、更具情绪陪伴，也便于后续做主播级 fine-tune 或工具集成。
