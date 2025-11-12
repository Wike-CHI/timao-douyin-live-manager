# AI 模型配置指南

## 概述

所有 AI 功能都通过 **AI Gateway** 统一调用，支持通过环境变量灵活配置每个功能使用的模型和服务商。

## 功能模块与配置

### 1. 直播间分析（Live Analysis）

**功能标识**: `live_analysis`

**默认配置**:
- 服务商: `xunfei` (科大讯飞)
- 模型: `lite` (免费版)

**环境变量**:
```bash
# 服务商配置
AI_FUNCTION_LIVE_ANALYSIS_PROVIDER=xunfei

# 模型配置
AI_FUNCTION_LIVE_ANALYSIS_MODEL=lite
```

**支持的模型**:
- 科大讯飞: `lite`, `generalv3`, `generalv3.5`, `4.0Ultra`
- 通义千问: `qwen-plus`, `qwen-turbo`, `qwen-max`, `qwen-max-longcontext`, `qwen3-max`
- OpenAI: `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo`
- DeepSeek: `deepseek-chat`, `deepseek-coder`

**示例配置**:
```bash
# 使用通义千问 qwen3-max
AI_FUNCTION_LIVE_ANALYSIS_PROVIDER=qwen
AI_FUNCTION_LIVE_ANALYSIS_MODEL=qwen3-max

# 或使用 OpenAI GPT-4
AI_FUNCTION_LIVE_ANALYSIS_PROVIDER=openai
AI_FUNCTION_LIVE_ANALYSIS_MODEL=gpt-4
```

---

### 2. 主播画像与氛围分析（Style Profile）

**功能标识**: `style_profile`

**默认配置**:
- 服务商: `qwen` (通义千问)
- 模型: `qwen3-max`

**环境变量**:
```bash
# 服务商配置
AI_FUNCTION_STYLE_PROFILE_PROVIDER=qwen

# 模型配置
AI_FUNCTION_STYLE_PROFILE_MODEL=qwen3-max
```

**示例配置**:
```bash
# 使用 OpenAI GPT-4
AI_FUNCTION_STYLE_PROFILE_PROVIDER=openai
AI_FUNCTION_STYLE_PROFILE_MODEL=gpt-4

# 或使用 DeepSeek
AI_FUNCTION_STYLE_PROFILE_PROVIDER=deepseek
AI_FUNCTION_STYLE_PROFILE_MODEL=deepseek-chat
```

---

### 3. 话术生成（Script Generation）

**功能标识**: `script_generation`

**默认配置**:
- 服务商: `qwen` (通义千问)
- 模型: `qwen3-max`

**环境变量**:
```bash
# 服务商配置
AI_FUNCTION_SCRIPT_GENERATION_PROVIDER=qwen

# 模型配置
AI_FUNCTION_SCRIPT_GENERATION_MODEL=qwen3-max
```

**示例配置**:
```bash
# 使用 OpenAI GPT-4 Turbo
AI_FUNCTION_SCRIPT_GENERATION_PROVIDER=openai
AI_FUNCTION_SCRIPT_GENERATION_MODEL=gpt-4-turbo

# 或使用科大讯飞
AI_FUNCTION_SCRIPT_GENERATION_PROVIDER=xunfei
AI_FUNCTION_SCRIPT_GENERATION_MODEL=generalv3.5
```

---

### 4. 复盘总结（Live Review）

**功能标识**: `live_review`

**默认配置**:
- 服务商: `gemini` (Google Gemini)
- 模型: `gemini-2.5-flash-preview-09-2025`

**环境变量**:
```bash
# 服务商配置
AI_FUNCTION_LIVE_REVIEW_PROVIDER=gemini

# 模型配置
AI_FUNCTION_LIVE_REVIEW_MODEL=gemini-2.5-flash-preview-09-2025
```

**示例配置**:
```bash
# 使用通义千问 qwen-max-longcontext（支持长上下文）
AI_FUNCTION_LIVE_REVIEW_PROVIDER=qwen
AI_FUNCTION_LIVE_REVIEW_MODEL=qwen-max-longcontext

# 或使用 OpenAI GPT-4 Turbo
AI_FUNCTION_LIVE_REVIEW_PROVIDER=openai
AI_FUNCTION_LIVE_REVIEW_MODEL=gpt-4-turbo
```

---

### 5. 聊天焦点摘要（Chat Focus）

**功能标识**: `chat_focus`

**默认配置**:
- 服务商: `qwen` (通义千问)
- 模型: `qwen3-max`

**环境变量**:
```bash
# 服务商配置
AI_FUNCTION_CHAT_FOCUS_PROVIDER=qwen

# 模型配置
AI_FUNCTION_CHAT_FOCUS_MODEL=qwen3-max
```

**说明**: 用于自动概括直播间观众讨论的主要话题，通常在 LangGraph 工作流中使用。

---

### 6. 智能话题生成（Topic Generation）

**功能标识**: `topic_generation`

**默认配置**:
- 服务商: `qwen` (通义千问)
- 模型: `qwen-plus`

**环境变量**:
```bash
# 服务商配置
AI_FUNCTION_TOPIC_GENERATION_PROVIDER=qwen

# 模型配置
AI_FUNCTION_TOPIC_GENERATION_MODEL=qwen-plus
```

**说明**: 用于根据直播内容动态生成相关话题，在知识库服务中使用。

---

## 完整配置示例

### 场景 1: 成本优化配置

```bash
# 直播分析：使用免费的讯飞 lite
AI_FUNCTION_LIVE_ANALYSIS_PROVIDER=xunfei
AI_FUNCTION_LIVE_ANALYSIS_MODEL=lite

# 主播画像：使用通义千问（性价比高）
AI_FUNCTION_STYLE_PROFILE_PROVIDER=qwen
AI_FUNCTION_STYLE_PROFILE_MODEL=qwen-plus

# 话术生成：使用通义千问
AI_FUNCTION_SCRIPT_GENERATION_PROVIDER=qwen
AI_FUNCTION_SCRIPT_GENERATION_MODEL=qwen-plus

# 复盘总结：使用 Gemini Flash（免费额度大）
AI_FUNCTION_LIVE_REVIEW_PROVIDER=gemini
AI_FUNCTION_LIVE_REVIEW_MODEL=gemini-2.5-flash-preview-09-2025
```

### 场景 2: 性能优先配置

```bash
# 所有功能使用 GPT-4 Turbo（性能最强）
AI_FUNCTION_LIVE_ANALYSIS_PROVIDER=openai
AI_FUNCTION_LIVE_ANALYSIS_MODEL=gpt-4-turbo

AI_FUNCTION_STYLE_PROFILE_PROVIDER=openai
AI_FUNCTION_STYLE_PROFILE_MODEL=gpt-4-turbo

AI_FUNCTION_SCRIPT_GENERATION_PROVIDER=openai
AI_FUNCTION_SCRIPT_GENERATION_MODEL=gpt-4-turbo

AI_FUNCTION_LIVE_REVIEW_PROVIDER=openai
AI_FUNCTION_LIVE_REVIEW_MODEL=gpt-4-turbo
```

### 场景 3: 混合配置

```bash
# 直播分析：快速响应，使用讯飞 lite
AI_FUNCTION_LIVE_ANALYSIS_PROVIDER=xunfei
AI_FUNCTION_LIVE_ANALYSIS_MODEL=lite

# 主播画像：需要高质量分析，使用 qwen3-max
AI_FUNCTION_STYLE_PROFILE_PROVIDER=qwen
AI_FUNCTION_STYLE_PROFILE_MODEL=qwen3-max

# 话术生成：需要创意，使用 qwen3-max
AI_FUNCTION_SCRIPT_GENERATION_PROVIDER=qwen
AI_FUNCTION_SCRIPT_GENERATION_MODEL=qwen3-max

# 复盘总结：需要长上下文，使用 qwen-max-longcontext
AI_FUNCTION_LIVE_REVIEW_PROVIDER=qwen
AI_FUNCTION_LIVE_REVIEW_MODEL=qwen-max-longcontext
```

---

## 服务商 API Key 配置

### 科大讯飞（XunFei）

```bash
XUNFEI_API_KEY=your_appid:your_api_secret
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1
XUNFEI_MODEL=lite
```

### 通义千问（Qwen）

```bash
QWEN_API_KEY=your_dashscope_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
```

### OpenAI

```bash
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4-turbo
```

### Google Gemini

```bash
AIHUBMIX_API_KEY=your_aihubmix_api_key
GEMINI_MODEL=gemini-2.5-flash-preview-09-2025
```

### DeepSeek

```bash
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```

---

## 验证配置

### 1. 检查 Gateway 状态

访问 Web 管理界面：
```
http://localhost:9019/static/ai_gateway_manager.html
```

### 2. 查看后端日志

启动服务后，检查日志中的模型配置信息：
```
✅ AI Gateway 初始化完成
   - 直播分析: xunfei/lite
   - 主播画像: qwen/qwen3-max
   - 话术生成: qwen/qwen3-max
   - 复盘总结: gemini/gemini-2.5-flash-preview-09-2025
```

### 3. 查看 AI 使用监控

在控制台输出中，每个 AI 调用都会显示：
```
✅ 实时分析(讯飞lite) - 模型: lite | Token: 1500 | 成本: ¥0.000000
✅ 风格画像与氛围分析(qwen3-max) - 模型: qwen3-max | Token: 3200 | 成本: ¥0.057600
```

---

## 注意事项

1. **功能级别配置优先**: 每个功能都可以独立配置模型，互不影响
2. **环境变量优先级**: 功能级别的环境变量会覆盖全局配置
3. **模型兼容性**: 确保配置的模型在对应服务商中可用
4. **成本监控**: 所有调用都会自动记录到 AI 使用监控系统
5. **实时生效**: 修改环境变量后需要重启服务才能生效

---

## 技术支持

如有问题，请查看：
- AI Gateway 文档: `docs/AI方案与集成/AI_GATEWAY_GUIDE.md`
- AI 使用监控: `server/utils/ai_usage_monitor.py`
- Web 管理界面: `http://localhost:9019/static/ai_gateway_manager.html`

