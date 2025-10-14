# 直播 AI 分析卡片 LangGraph 工作流规划

> 版本：2025-02（改造后）

## 目标与原则

- **实时助理视角**：每 60 秒汇总主播口播与弹幕数据，输出专业助理口吻的《直播分析卡片》，不提供任何可直接复述的话术。
- **数据驱动判断**：不再插入“热词模版”“默认文案”。模型需根据原始转写、弹幕分类与系统预估的氛围自行判断，并明确证据来源。
- **LangGraph 编排**：延续 LangGraph 状态机，节点职责清晰，支持离线测试与可控降级；若缺少依赖自动顺序执行。
- **Qwen3-Max 统一推理**：所有分析卡片由 Qwen3-Max OpenAI-兼容接口生成，保证口吻稳定、分析可靠。

## LangGraph 总体拓扑

```
START
 ├─ MemoryLoader → SignalCollector → TopicDetector → MoodEstimator
 └─ Planner → AnalysisGenerator → SummaryNode → END
```

- **MemoryLoader**：读取 `records/memory/<anchor_id>/profile.json`，同步主播画像（tone/taboo/常用语等），用于提示模型保持贴近主播的表达视角。
- **SignalCollector**：合并最近口播节选及弹幕事件，按 question/product/support/emotion/other 分类并统计互动密度。
- **TopicDetector**：基于口播+弹幕文本提取高频讨论主题（含置信度排名），为后续分析提供语义线索。
- **MoodEstimator**：根据互动类别与密度给出 `vibe = {level, score, trends}` 与 `mood`，作为模型理解直播间温度的参考。
- **Planner**：结合话题、氛围、提问密度生成当前窗口关注重点（analysis_focus），例如“优先回应观众提问”“热度较高需稳住节奏”等。
- **AnalysisGenerator**：向 Qwen3-Max 发送结构化提示，要求返回严格 JSON：
  ```json
  {
    "analysis_overview": "...",
    "audience_sentiment": {"label": "热|平稳|冷", "signals": []},
    "engagement_highlights": [],
    "risks": [],
    "next_actions": [],
    "confidence": 0.0
  }
  ```
  模型仅进行分析，不输出任何口播话术模板。
- **SummaryNode**：将分析卡片、话题与氛围整合输出，供 SSE 及日志使用。

## 关键数据结构（GraphState 片段）

```json
{
  "transcript_snippet": "...最近6句口播...",
  "chat_signals": [{"text": "...", "category": "question", "weight": 0.85}, ...],
  "chat_stats": {"total_messages": 42, "category_counts": {"question": 8, ...}},
  "topic_candidates": [{"topic": "新品试色", "confidence": 0.78}],
  "vibe": {"level": "neutral", "score": 61.5, "trends": ["supporting", "interaction_light"]},
  "analysis_focus": "重点观察观众提问，尽快帮助主播澄清或回应。",
  "analysis_card": {
    "analysis_overview": "...",
    "audience_sentiment": {"label": "平稳", "signals": ["问题集中在色号", "..."]},
    "engagement_highlights": [...],
    "risks": [...],
    "next_actions": [...],
    "confidence": 0.78
  }
}
```

## LangGraph 伪代码

```python
graph = StateGraph(GraphState)
graph.add_node("memory_loader", load_persona)
graph.add_node("signal_collector", gather_signals)
graph.add_node("topic_detector", detect_topics)
graph.add_node("mood_estimator", estimate_mood)
graph.add_node("planner", plan_focus)
graph.add_node("analysis_generator", run_qwen_analysis)
graph.add_node("summary", build_summary)

graph.set_entry_point("memory_loader")
graph.add_edge("memory_loader", "signal_collector")
graph.add_edge("signal_collector", "topic_detector")
graph.add_edge("topic_detector", "mood_estimator")
graph.add_edge("mood_estimator", "planner")
graph.add_edge("planner", "analysis_generator")
graph.add_edge("analysis_generator", "summary")
workflow = graph.compile(checkpointer=MemorySaver())
```

## 数据持久化与输出

- 仅在 MemoryLoader 阶段读取主播画像；不再写入脚本历史或反馈文件，避免与旧版话术记忆混淆。
- SSE `/api/ai/live/stream` payload 更新为：
  ```json
  {
    "summary": "...",
    "highlight_points": ["..."],
    "risks": ["..."],
    "suggestions": ["..."],
    "analysis_card": {...},
    "analysis_focus": "...",
    "topic_candidates": [...],
    "style_profile": {...},
    "vibe": {...}
  }
  ```

- 手动话术生成：前端在“实时弹幕”面板点选问题后，调用 `POST /api/ai/live/answers`，由 Qwen3-Max 生成主播口吻脚本。
  兼容旧字段 `top_questions`、`style_profile`，但不再返回 `scripts`/`score_summary`。

## 后续迭代方向

1. **指标补强**：可接入实时在线人数、成交数据等指标，丰富 AnalysisGenerator 的输入。
2. **异常监控**：在 SummaryNode 增加敏感词或异常行为检测，必要时提示人工介入。
3. **多窗口对比**：为 AnalysisGenerator 提供上一窗口概要，生成趋势判断（热度上升/下降）。
4. **前端卡片升级**：配合 UI 调整展示字段（情绪指示灯、推荐行动清单等），替换旧“话术窗口”。

> 更新后的 LangGraph 流程以“专业助理分析”为核心，完全移除默认话术模板与热词注入，适配用户提出的直播分析卡片需求。
