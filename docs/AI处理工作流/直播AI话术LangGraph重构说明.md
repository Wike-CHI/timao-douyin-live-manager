# 直播 AI 分析卡片 LangGraph 重构说明

> 更新时间：2025-02-15  
> 关联规划文档：`docs/AI处理工作流/直播AI话术LangGraph规划.md`

本文记录“直播助手卡片”升级为“直播分析卡片”的主要实现细节、接口输出与验证策略，供研发及运营团队参考。

## 1. 改动概览

- **LangGraph 工作流改造**
  - 保持 MemoryLoader → SignalCollector → TopicDetector → MoodEstimator → Planner → AnalysisGenerator → (QuestionResponder) → SummaryNode 结构，聚焦实时分析并兼顾手动答疑。
- **Qwen3-Max 分析卡片生成**
  - 新增 `server/ai/live_analysis_generator.py`。模型提示要求产出 `analysis_overview`、`audience_sentiment`、`engagement_highlights`、`risks`、`next_actions`、`confidence` 等字段，不允许返回口播话术。
  - 输入包含口播节选、弹幕样本、互动分类统计、话题候选、氛围评估及系统给出的 `analysis_focus`。
- **Qwen3-Max 智能话术生成（手动）**
  - 新增 `server/ai/live_question_responder.py`，并通过 `POST /api/ai/live/answers` 提供手动触发接口。
  - 前端从弹幕面板选择问题后调用接口，返回形如 `{question, line, notes}` 的主播口吻话术列表。
- **AILiveAnalyzer 集成**
  - `server/app/services/ai_live_analyzer.py` 实例化 `LiveAnalysisGenerator`（用于实时分析）并复用 `LiveQuestionResponder` 提供手动答疑接口。
  - 出现异常时返回结构化失败提示，不再回退到旧 `analyze_window` 话术接口，确保无话术输出。
- **文档同步**
  - 更新规划与重构说明文档，明确“分析卡片”定位及输出结构。

## 2. LangGraph 节点职责

| 节点 | 输入/输出 | 说明 |
| ---- | -------- | ---- |
| MemoryLoader | `anchor_id` → `persona` | 读取主播画像（tone/taboo），无其他持久化依赖。 |
| SignalCollector | 口播/弹幕 → `chat_signals` + `chat_stats` + `top_questions` | 提取最近 6 句口播与 200 条弹幕，分类并统计互动。 |
| TopicDetector | `chat_signals` → `topic_candidates` | 高频词提取，提供最多 5 个话题候选及置信度。 |
| MoodEstimator | `chat_signals` → `mood` + `vibe` | 规则评估直播氛围等级与得分。 |
| Planner | 汇总上下文 → `analysis_focus` + `planner_notes` | 根据提问数量、氛围、话题推导助理关注点。 |
| AnalysisGenerator | 上述上下文 → `analysis_card` | 调用 Qwen3-Max 输出 JSON 分析卡片，不含话术。 |
| QuestionResponder (可选) | `top_questions` + persona/vibe | 启用 `LiveQuestionResponder` 时，为 `/answers` 接口预先生成高情商口吻脚本；若无高优先级问题则返回空列表。 |
| SummaryNode | `analysis_card` + planner_notes | 汇总分析结果、话题/氛围与口播统计，生成 SSE 展示用摘要，并携带 `speech_stats`/`transcript_snippet` 等上下文。 |

## 3. SSE 输出示例

```json
{
  "summary": "当前状态：问题集中在色号咨询；氛围 neutral 分 63.5。",
  "highlight_points": [
    "观众主要纠结在色号和真实试色反馈",
    "互动节奏适中，可引导出真实体验"
  ],
  "risks": [
    "若一直未给出明确对比，观众可能流失"
  ],
  "suggestions": [
    "提醒主播快速整理可对比的真实试色数据",
    "引导观众在弹幕留下肤色信息便于推荐"
  ],
  "analysis_card": {
    "analysis_overview": "...",
    "audience_sentiment": {"label": "平稳", "signals": ["..."]},
    "engagement_highlights": ["..."],
    "risks": ["..."],
    "next_actions": ["..."],
    "confidence": 0.74
  },
  "analysis_focus": "重点观察观众提问，尽快帮助主播澄清或回应。",
  "topic_candidates": [{"topic": "色号", "confidence": 0.78}],
  "planner_notes": {
    "selected_topic": {"topic": "色号", "confidence": 0.78},
    "speech_stats": {...}
  },
  "style_profile": {"tone": "自然陪伴", "taboo": []},
  "vibe": {"level": "neutral", "score": 63.5, "trends": ["supporting", "interaction_light"]},
  "top_questions": ["这个色号偏黄还是偏粉？"],
  "transcript_snippet": "......",
  "speech_stats": {
    "sentence_count": 5,
    "speaking_ratio": 0.34,
    "possible_other_speaker": false
  },
  "carry": "当前状态：问题集中在色号咨询；氛围 neutral 分 63.5。"
}
```

## 4. 回退策略

- 若 LangGraph 或 Qwen 接口调用失败，返回带 `analysis_overview="分析卡片生成失败：..."` 的结构化信息，并提示检查配置。
- 旧 `analyze_window` 不再被调用，保证不会出现话术或模板字段。

## 5. 验证与测试建议

1. **接口巡检**：启动 `npm run dev` 后，访问 `/api/ai/live/stream`，确认 SSE payload 不再包含旧的 `scripts/score_summary` 字段。
2. **窗口测试**：模拟弹幕分类（问题/支持/情绪）与不同口播节奏，观察 `analysis_focus` 与 `audience_sentiment.label` 是否符合预期。
3. **错误处理**：拔除 Qwen API Key，确认 SSE 返回失败结构，前端可容错展示。
4. **前端适配**：更新“智能话术建议”卡片，支持从弹幕中点选问题并调用 `POST /api/ai/live/answers` 获取 Qwen3-Max 生成的主播口吻话术。
   - `LiveQuestionResponder` 会递归加载 `docs/娱乐主播高情商话术大全/**/*.txt`，筛选 6~30 字的示例句并去重，作为高情商样本注入提示词。

## 6. 后续优化

- 为 AnalysisGenerator 引入多窗口趋势数据，帮助判断热度上升/下降。
- 接入成交/转化等业务指标，拓展 `engagement_highlights` 的数据来源。
- 对 SummaryNode 结果增加敏感词检测，必要时提示人工介入。

> 本次重构将原“话术生成”流转升级为“助理分析”流程，彻底移除了默认话术模板与热词依赖，更贴合运营团队对实时分析卡片的需求。
