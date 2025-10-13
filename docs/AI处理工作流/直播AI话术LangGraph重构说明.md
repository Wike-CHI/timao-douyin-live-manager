# 直播 AI 话术 LangGraph 重构说明

> 创建时间：2025-02-15  
> 关联规划文档：`docs/AI处理工作流/直播AI话术LangGraph规划.md`

本说明记录本轮落地 LangGraph 工作流的主要改动、实现细节与验证手段，供研发与运营团队参考。

## 1. 改动概览

- 新增 `server/ai/langgraph_live_workflow.py`，将 MemoryLoader → SignalCollector → TopicDetector → MoodEstimator → Planner → ScriptGenerator → ScoreAssessor → SummaryNode → MemoryUpdater 整体串联为 LangGraph（若环境缺少 LangGraph 依赖自动回退顺序执行）。
- 扩展 `AIScriptGenerator`：
  - 新增 `generate_bundle()` 支持根据 Planner route 一次生成 2-3 条话术，并补充 `keywords`/`rationale`。
  - 暴露 `score_text()` 供 ScoreAssessor 对脚本进行统一打分。
  - 补充热词归一化、关键词抽取和 route-specific prompt 提示，确保所有脚本均由 Qwen-Max 生成。
- 重写 `AILiveAnalyzer` 服务：
  - 启动时自动加载 Anchor 记忆/配置，调用 LangGraph Workflow。
  - SSE 推流 payload 统一输出 `summary/highlight_points/risks/suggestions/top_questions/scripts/score_summary/style_profile/vibe/planner`，前端直接展示并同步风格画像。
  - 若 LangGraph/脚本生成失败，自动降级为历史 `analyze_window` 能力（Qwen JSON 输出）。
- 新增单元测试 `server/tests/test_langgraph_workflow.py`，在检测到 Qwen-Max 客户端可用时运行工作流校验；若测试环境缺少 API Key 会自动跳过。

## 2. LangGraph 节点与职责

| 节点 | 功能摘要 | 说明 |
| ---- | -------- | ---- |
| MemoryLoader | 读取 `records/memory/<anchor_id>/profile.json`、历史话术、反馈 | 自动兜底缺失字段，确保 persona/tone/taboo 可用 |
| SignalCollector | 整理 30-60s 窗口内的转写+弹幕信号 | 分类 question/product/support/emotion，生成 `chat_signals` |
| TopicDetector | 基于窗口文本提取高频词 | 输出带置信度的 `topic_candidates`，无热点时默认“互动” |
| MoodEstimator | 规则评估情绪/热度 | 生成 `vibe = {level, score, trends}` 与 `mood` |
| Planner | 依据话题&情绪选 route（deep_dive / warm_up / promo） | `promo` 用于行动号召型脚本（关注、互动、参与任务等），保留 heuristics trace 便于调试 |
| ScriptGenerator | 调用 `AIScriptGenerator.generate_bundle` | 输出包含 `text/type/route/vibe/keywords/score/rationale` 的脚本列表 |
| ScoreAssessor | 汇总评分，拆分优/劣脚本 | 结果写入 `score_summary.avg_score/high_quality/low_quality` |
| SummaryNode | 组织 summary/highlight/风险/建议/问题 | 风险自动提示低热度/低分话术，建议遵循 route |
| MemoryUpdater | 写入 `history.jsonl`/`feedback_good.jsonl`/`feedback_bad.jsonl` | 带上限裁剪，避免记忆膨胀 |

## 3. 数据输出格式

SSE 推送 payload 样例：

```json
{
  "summary": "当前主轴：舞蹈挑战 (置信 0.72)；直播氛围：neutral，热度分 63.5；推荐话术 3 条，可用于 promo 场景",
  "highlight_points": ["高频话题：舞蹈挑战", "氛围评分 63.5 (neutral)"],
  "risks": ["存在评分偏低的话术，建议谨慎使用。"],
  "suggestions": ["适时抛出行动号召，引导观众刷弹幕或参与互动。"],
  "top_questions": ["这首歌叫什么？"],
  "scripts": [
    {"text": "想挑战的朋友扣个1，我待会儿点你名字上墙，一起嗨起来！", "route": "promo", "score": 7.8, "keywords": ["挑战", "扣1"]},
    ...
  ],
  "score_summary": {"avg_score": 7.1, "high_quality": [...], "low_quality": [...]},
  "style_profile": {"tone": "...", "taboo": [...]},
  "vibe": {"level": "neutral", "score": 63.5, "trends": ["supporting", "interaction_light"]},
  "planner": {"route": "promo", "notes": {"selected_topic": {...}}}
}
```

该结构与前端“话术窗口”预期字段保持兼容，并新增 `planner`、`score_summary` 供后续可视化得分及 route 诊断使用。

## 4. 文件与持久化更新

- 所有记忆/反馈文件仍位于 `records/memory/<anchor_id>/`，新增的写入逻辑会自动创建文件并控制历史行数（默认 120）。
- 高分话术同步写入 `history.jsonl` 与 `feedback_good.jsonl`，低分则进 `feedback_bad.jsonl`，后续可被反馈记忆模块读取。
- 若运行环境缺少 LangChain/LangGraph 依赖，工作流将退化为顺序执行，不影响持久化逻辑。
- Qwen DashScope 配置统一放在项目根目录 `.env` 中（`AI_SERVICE`、`AI_API_KEY`、`AI_BASE_URL`、`AI_MODEL` 等）；FastAPI / Flask 在启动时会主动读取该文件，确保所有子模块拿到密钥。

## 5. 测试与验证

1. 自动化：新增 `pytest server/tests/test_langgraph_workflow.py`，若检测到 Qwen-Max 客户端可用会执行工作流校验，否则自动跳过。  
   > 当前 CLI 环境未预装 `pytest`，需先 `pip install pytest` 后执行。
2. 手动联调建议：
   - 启动实时字幕 → 等待约一个窗口周期，确认 SSE 推送包含 `planner.route` 与脚本评分。
   - 检查 `records/memory/<anchor_id>/` 下文件是否追加且被裁剪。
   - 切换不同情绪/话题（如弹幕刷产品 vs. 提问）观察 route 切换与脚本输出差异。

## 6. 后续可选优化

1. **ScoreAssessor LLM 化**：当前为规则评分，可接入轻量 LLM 对脚本做更细致点评并输出改进建议。
2. **SummaryNode 敏感词拦截**：规划文档的审计节点可在此处落地，必要时回退安全模板。
3. **前端评分回写**：结合 `/api/ai/live/feedback` 接口，将 UI 打分同步进记忆向量库，提高下一轮生成精准度。
4. **多主播并行**：LangGraph MemorySaver 现以 `thread_id=anchor_id` 区分，可进一步扩展支持多主播并行实例。

---

如需深入调试，每个节点可通过 `logging.getLogger('server.ai.langgraph_live_workflow')` 设置为 `DEBUG` 查看状态转移细节。欢迎在后续迭代补充更多节点（如 Tools 召回、风险审查）。
