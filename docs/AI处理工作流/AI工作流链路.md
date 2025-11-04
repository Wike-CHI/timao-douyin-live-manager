# AI工作流链路

START
  ↓
memory_loader (加载主播画像)
  ↓
signal_collector (收集弹幕和转写信号)
  ↓
topic_detector (检测话题，本地计算)
  ↓
mood_estimator (评估氛围，本地计算)
  ↓
planner (生成分析重点，本地计算)
  ↓
knowledge_loader (加载知识库，可能调用AI生成话题)
  ↓
style_profile_builder (生成风格画像) → Gateway(function="style_profile", qwen3-max)
  ↓
analysis_generator (生成直播分析) → Gateway(function="live_analysis", xunfei lite)
  ↓
question_responder (可选，生成话术) → Gateway(function="script_generation", qwen3-max)
  ↓
summary (汇总结果，可能调用chat_focus) → Gateway(function="chat_focus", qwen3-max)
  ↓
END


### 数据流转

输入数据 (sentences, comments, speaker_timeline)
  ↓
[本地处理节点] → 提取信号、话题、氛围
  ↓
[AI节点1: style_profile_builder] → 生成风格画像 (qwen3-max)
  ↓
[AI节点2: analysis_generator] → 生成直播分析 (xunfei lite)
  ↓
[可选: question_responder] → 生成话术 (qwen3-max)
  ↓
[summary节点] → 汇总结果，可能调用chat_focus (qwen3-max)
  ↓
输出: {analysis_card, style_profile, vibe, summary, ...}


## 主播记忆功能实现

### 1. 两层记忆结构

#### 第一层：基础画像（profile.json）

* 位置：records/memory/{anchor_id}/profile.json
* 加载时机：工作流开始时，memory_loader 节点
* 内容：基础画像（tone、taboo 等）
* 格式：JSON 文件
* 默认值：{"tone": "专业陪伴", "taboo": []}

#### 第二层：向量记忆（Style Memory）

* 位置：records/style_memory/{anchor_id}/vector_store/
* 存储方式：LangChain 向量数据库（DocArrayInMemorySearch）
* 内容：历史分析摘要、话术、亮点等
* 检索方式：语义相似度搜索

### 2. 工作流中的使用

**memory_loader 节点（工作流入口）**

**  ↓**

**从 records/memory/{anchor_id}/profile.json 加载基础画像**

**  ↓**

**返回 {"persona": {...}} 给后续节点使用**

### 3. 记忆的写入与更新

#### 写入时机：

1. 实时分析后：StyleProfileBuilder 生成风格画像后，写入到向量记忆
2. 复盘后：LiveReportService 在生成复盘报告时更新风格记忆
3. 话术验证后：用户反馈的话术会保存到反馈记忆

#### 写入内容：

* highlight_points（亮点）
* suggestions（建议）
* risks（风险）
* top_questions（热门问题）
* scripts（话术）
* catchphrases（口头禅）

### 4. 记忆的检索与使用

#### 检索方式：

**StyleMemoryManager.**fetch_context**(anchor_id, **k**=**5**)**

* 使用语义搜索（向量相似度）
* 返回最相关的 5 条记忆片段
* 用于提示词增强，让 AI 更了解主播风格

#### 使用场景：

1. 话术生成：检索历史风格，生成符合主播风格的话术
2. 实时分析：结合历史画像，生成更贴合的分析
3. 话题推荐：基于历史互动，推荐更合适的话题

### 5. 技术实现细节

#### 向量存储：

* 嵌入模型：sentence-transformers/all-MiniLM-L6-v2（HuggingFace）
* 降级方案：如果 LangChain 不可用，使用简单的词袋模型
* 持久化：每个主播独立存储，本地文件系统

#### 记忆管理：

* StyleMemoryManager：管理风格记忆
* FeedbackMemoryManager：管理反馈记忆（用户评分的话术）
* 按主播 ID 隔离存储

### 6. 数据流转

**直播开始**

**  ↓**

**memory_loader 加载基础画像 (profile.json)**

**  ↓**

**实时分析生成风格画像**

**  ↓**

**StyleProfileBuilder 生成 → 写入向量记忆**

**  ↓**

**后续分析/话术生成时检索向量记忆**

**  ↓**

**结合历史风格生成更贴合的内容**

### 7. 文件结构

**records/**

**├── memory/**

**│   └── {anchor_id}/**

**│       └── profile.json          # 基础画像**

**├── style_memory/**

**│   └── {anchor_id}/**

**│       └── vector_store/          # **向量记忆（LangChain）

**└── feedback_memory/**

**    └── {anchor_id}/**

**        ├── positive/              # 好评话术**

**        ├── negative/              # 差评话术**

**        └── feedback.jsonl         # 反馈日志**

### 8. 关键特点

* 渐进式学习：随直播积累，记忆逐步完善
* 语义检索：基于相似度，而非关键词匹配
* 多维度记忆：风格、话术、反馈分别存储
* 容错机制：LangChain 不可用时降级到简单模式

该系统通过两层记忆结构，让 AI 逐步了解主播风格，生成更贴合的内容。
