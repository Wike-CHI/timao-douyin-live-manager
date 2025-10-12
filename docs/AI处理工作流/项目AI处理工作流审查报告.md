# 项目AI处理工作流审查报告

本文审查提猫直播助手（timao-douyin-live-manager）的主要 AI 处理工作流，明确数据流、核心组件、接口与依赖，并核查是否使用 LangChain / LangGraph。

## 总览
- 框架与进程：Electron 桌面壳启动 FastAPI 后端；前端通过 REST/SSE/WebSocket 调用后端服务。
- 数据来源：
  - 直播音频：通过 StreamCap 解析直播地址，`ffmpeg` 拉流并转为 PCM，送入 `SenseVoice + VAD` 转写管线。
  - 直播事件：通过 `DouyinLiveWebFetcher` 采集弹幕/礼物/点赞等事件。
- 分析与生成：
  - 实时分析：`AILiveAnalyzer` 将“最终转写句子 + 弹幕事件”按时间窗聚合，调用 Qwen（OpenAI 兼容接口）做风格/氛围分析与脚本建议，结果通过 SSE 推送。
  - 单条话术生成：`AIScriptGenerator` 在上下文（style_profile/vibe）与模板/AI之间选择生成；支持人工评分写入记忆。
- 记忆与检索：可选的 LangChain 向量记忆用于“风格画像”和“反馈指导”的积累与检索，提升后续提示词质量。

## 模块与数据流

```mermaid
flowchart LR
    subgraph Source[数据源]
      A[Douyin Live URL/ID]
      B[Douyin Web 事件]
    end

    subgraph Capture[采集与预处理]
      A --> C[StreamCap 解析真实流]
      C --> D[ffmpeg 音频管线]
      D --> E[SenseVoice + VAD 转写]
      E --> F[Cleaner/Guard/Assembler 最终句子]
      B --> G[DouyinWebRelay 事件标准化]
    end

    subgraph Analyze[实时分析]
      F --> H[AILiveAnalyzer 窗口聚合]
      G --> H
      H --> I[Qwen OpenAI兼容 analyze_window]
      I --> J[SSE /api/ai/live/stream]
      I --> K[style_profile/vibe 快照]
    end

    subgraph Generate[话术生成]
      K --> L[AIScriptGenerator]
      L --> M[/api/ai/scripts/generate_one]
      M --> N[用户/运营评分]
      N --> O[FeedbackMemory LangChain]
      I --> P[StyleMemory LangChain]
      O --> L
      P --> L
    end
```

### 关键代码位置
- 实时分析 API：`server/app/api/ai_live.py`
  - `POST /api/ai/live/start|stop|status|context`
  - `GET /api/ai/live/stream`（SSE 推送分析事件）
- 实时分析服务：`server/app/services/ai_live_analyzer.py`
  - 订阅转写最终句（`live_audio_stream_service` 回调）与抖音事件（`douyin_web_relay` 客户端队列）
  - 时间窗聚合后调用 `server/ai/qwen_openai_compatible.py: analyze_window`
  - 维护并广播 `style_profile` 与 `vibe` 快照
- 音频转写管线：`server/app/services/live_audio_stream_service.py`
  - StreamCap 解析 → ffmpeg 拉流 → SenseVoice+VAD → Cleaner/Guard/Assembler → 最终句回调
  - 相关 API：`server/app/api/live_audio.py`
- 单条话术生成：`server/ai/generator.py` + `server/app/api/ai_scripts.py`
  - 读取 `style_profile/vibe` 上下文，优先使用 Qwen（OpenAI 兼容）生成；无密钥时走模板回退
  - 人工评分通过 `FeedbackMemory` 写入记忆，提升后续提示词

## LangChain / LangGraph 使用情况

- LangChain：有使用（可选，默认按依赖可用与否启用），主要用于向量记忆与检索。
  - 风格记忆：`server/ai/style_memory.py`
    - 依赖 `langchain.memory.VectorStoreRetrieverMemory`、`langchain_community.vectorstores.DocArrayInMemorySearch`、HuggingFace Embeddings 等。
    - 功能：从分析总结与高分脚本中提取“风格画像/口头禅/修辞”等片段存入向量库；生成时检索提要注入提示词。
  - 反馈记忆：`server/ai/feedback_memory.py`
    - 依赖 `langchain_community.vectorstores.DocArrayInMemorySearch` 与 `langchain_core.documents.Document`。
    - 功能：记录人工评分文本，正/负面分库检索，汇总“保留优点/避免风险”的提示，引导后续生成。
  - 依赖声明：`server/requirements.txt` 中包含 `langchain` 与 `langchain-community`。
  - 说明：上述记忆模块均做了“可用性检测与降级”，在缺失依赖时回退到内置确定性嵌入，保证主流程不被阻断。

- LangGraph：未发现项目代码直接使用。
  - 仓库中有 `langchain` 源码副本（`langchain/libs/core/langchain_core/agents.py` 等）文档处提到“新代理建议使用 LangGraph”，但项目自身未导入/调用 LangGraph。

## 接口与交互摘要
- `/api/live_audio/*`：启动/停止/状态/健康检查/预加载模型等（WebSocket 用于转写流与输入电平广播）。
- `/api/ai/live/*`：启动/停止/状态/上下文/流（SSE 推送实时分析结果）。
- `/api/ai/scripts/generate_one`：结合上下文生成单条可上嘴话术（模板/AI）；`/feedback` 记录人工评分并同步写入风格记忆。

## 依赖与配置
- SenseVoice 与 VAD 本地模型位于 `models/models/iic/...`，首次运行建议执行工具脚本下载。
- Qwen（DashScope 兼容）默认密钥/地址/模型在 `server/ai/qwen_openai_compatible.py` 中配置，可通过环境变量覆盖：
  - `AI_SERVICE`、`AI_API_KEY`、`AI_BASE_URL`、`AI_MODEL`、`ANCHOR_ID/DOUYIN_ROOM_ID`。
- LangChain 记忆为可选，安装 `langchain`、`langchain-community`、`langchain-huggingface` 可启用更优嵌入与检索；缺失时自动回退。

## 结论与建议
- 主干 AI 工作流清晰：音频/事件采集 → 时间窗聚合 → Qwen 分析 → SSE 推送；单条生成与人工反馈形成闭环并通过 LangChain 记忆增强提示词。
- LangChain：已使用（向量记忆/检索），建议在生产环境安装相关依赖并启用 HuggingFace Embeddings，以提升检索质量；同时保留降级路径。
- LangGraph：未使用；如后续需要更复杂的代理编排与人类介入工作流，可评估引入，但目前需求不迫切。

## 参考文件
- `server/app/api/ai_live.py`
- `server/app/services/ai_live_analyzer.py`
- `server/app/services/live_audio_stream_service.py`
- `server/app/services/douyin_web_relay.py`
- `server/ai/qwen_openai_compatible.py`
- `server/ai/generator.py`
- `server/ai/style_memory.py`
- `server/ai/feedback_memory.py`
- `server/app/main.py`