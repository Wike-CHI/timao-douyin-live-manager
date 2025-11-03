# AI 网关统一管理说明

## 🎯 核心理念

项目使用 **AI Gateway** 作为统一的 AI 服务入口，所有 AI 提供商（科大讯飞、通义千问、Gemini、DeepSeek 等）都通过网关统一管理，无需为每个提供商创建独立的客户端。

## 🏗️ 架构设计

### 统一接口层
```
前端/业务逻辑
       ↓
   AI Gateway (统一入口)
       ↓
   OpenAI 兼容客户端
       ↓
┌──────┴──────────────────┐
↓      ↓       ↓      ↓    ↓
科大讯飞  千问  Gemini  DeepSeek  其他
```

### 为什么不需要独立客户端？

❌ **错误做法：**
```
xunfei_lite_client.py  ← 不需要
qwen_client.py         ← 不需要
gemini_client.py       ← 不需要
```

✅ **正确做法：**
```python
# 所有 AI 提供商都通过 AI Gateway 调用
from server.ai.ai_gateway import get_gateway

gateway = get_gateway()

# 自动使用配置的默认模型
response = gateway.chat_completion(
    messages=[{"role": "user", "content": "你好"}],
    function="live_analysis"  # 自动路由到配置的模型
)

# 或指定特定提供商
response = gateway.chat_completion(
    messages=[{"role": "user", "content": "你好"}],
    provider="xunfei",
    model="lite"
)
```

## 🔧 支持的 AI 提供商

### 1. 科大讯飞（XunFei）
```python
AIProvider.XUNFEI = "xunfei"
```

**配置模板：**
```python
{
    "base_url": "https://spark-api-open.xf-yun.com/v1",
    "default_model": "lite",
    "models": ["lite", "generalv3", "generalv3.5", "4.0Ultra"]
}
```

**环境变量：**
```bash
XUNFEI_API_KEY=your_appid:your_api_secret
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1
XUNFEI_MODEL=lite
```

### 2. 通义千问（Qwen）
```python
AIProvider.QWEN = "qwen"
```

**配置模板：**
```python
{
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "default_model": "qwen-plus",
    "models": ["qwen-plus", "qwen-turbo", "qwen-max", "qwen-max-longcontext", "qwen3-max"]
}
```

**环境变量：**
```bash
QWEN_API_KEY=your_api_key
DASHSCOPE_API_KEY=your_api_key  # 兼容
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
```

### 3. Gemini
```python
AIProvider.GEMINI = "gemini"
```

**配置模板：**
```python
{
    "base_url": "https://aihubmix.com/v1",
    "default_model": "gemini-2.5-flash-preview-09-2025",
    "models": ["gemini-2.5-flash-preview-09-2025"]
}
```

**环境变量：**
```bash
AIHUBMIX_API_KEY=your_api_key
GEMINI_API_KEY=your_api_key  # 兼容
AIHUBMIX_BASE_URL=https://aihubmix.com/v1
GEMINI_MODEL=gemini-2.5-flash-preview-09-2025
```

### 4. DeepSeek
```python
AIProvider.DEEPSEEK = "deepseek"
```

**配置模板：**
```python
{
    "base_url": "https://api.deepseek.com/v1",
    "default_model": "deepseek-chat",
    "models": ["deepseek-chat", "deepseek-coder"]
}
```

### 5. 豆包（Doubao）
```python
AIProvider.DOUBAO = "doubao"
```

### 6. ChatGLM
```python
AIProvider.GLM = "glm"
```

## 🎯 功能级别配置

### 当前配置策略

```python
FUNCTION_MODELS = {
    "live_analysis": {
        "provider": "xunfei",
        "model": "lite"
    },  # AI实时分析 → 科大讯飞（免费）
    
    "style_profile": {
        "provider": "xunfei",
        "model": "lite"
    },  # 风格画像 → 科大讯飞（免费）
    
    "script_generation": {
        "provider": "qwen",
        "model": "qwen3-max"
    },  # 话术生成 → 千问（高质量）
    
    "live_review": {
        "provider": "gemini",
        "model": "gemini-2.5-flash-preview-09-2025"
    },  # 复盘 → Gemini（高质量）
}
```

### 环境变量覆盖

```bash
# 每个功能都可以独立配置
AI_FUNCTION_LIVE_ANALYSIS_PROVIDER=xunfei
AI_FUNCTION_LIVE_ANALYSIS_MODEL=lite

AI_FUNCTION_STYLE_PROFILE_PROVIDER=xunfei
AI_FUNCTION_STYLE_PROFILE_MODEL=lite

AI_FUNCTION_SCRIPT_GENERATION_PROVIDER=qwen
AI_FUNCTION_SCRIPT_GENERATION_MODEL=qwen3-max

AI_FUNCTION_LIVE_REVIEW_PROVIDER=gemini
AI_FUNCTION_LIVE_REVIEW_MODEL=gemini-2.5-flash-preview-09-2025
```

## 💡 使用示例

### 1. 自动路由（推荐）

```python
from server.ai.ai_gateway import get_gateway

gateway = get_gateway()

# 根据 function 自动选择最佳模型
response = gateway.chat_completion(
    messages=[{"role": "user", "content": "分析直播氛围"}],
    function="live_analysis"  # 自动使用 xunfei/lite
)

response = gateway.chat_completion(
    messages=[{"role": "user", "content": "生成话术"}],
    function="script_generation"  # 自动使用 qwen/qwen3-max
)

response = gateway.chat_completion(
    messages=[{"role": "user", "content": "复盘直播"}],
    function="live_review"  # 自动使用 gemini
)
```

### 2. 指定提供商

```python
# 临时使用科大讯飞的高级模型
response = gateway.chat_completion(
    messages=[{"role": "user", "content": "你好"}],
    provider="xunfei",
    model="generalv3"
)

# 临时使用千问
response = gateway.chat_completion(
    messages=[{"role": "user", "content": "你好"}],
    provider="qwen",
    model="qwen-max"
)
```

### 3. 流式响应

```python
# 支持所有提供商的流式响应
for chunk in gateway.chat_completion_stream(
    messages=[{"role": "user", "content": "写一段长文本"}],
    provider="xunfei",
    model="lite"
):
    print(chunk, end="", flush=True)
```

## 🔌 添加新的 AI 提供商

### 步骤 1：在 AIProvider 枚举中添加

```python
class AIProvider(str, Enum):
    XUNFEI = "xunfei"
    QWEN = "qwen"
    OPENAI = "openai"
    NEW_PROVIDER = "new_provider"  # 新增
```

### 步骤 2：添加配置模板

```python
PROVIDER_TEMPLATES = {
    AIProvider.NEW_PROVIDER: {
        "base_url": "https://api.newprovider.com/v1",
        "default_model": "default-model",
        "models": ["model1", "model2", "model3"],
    },
    # ... 其他提供商
}
```

### 步骤 3：在 _load_additional_providers 中加载

```python
def _load_additional_providers(self) -> None:
    # 新提供商
    new_provider_key = os.getenv("NEW_PROVIDER_API_KEY")
    if new_provider_key:
        self.register_provider(
            provider="new_provider",
            api_key=new_provider_key,
            base_url=os.getenv("NEW_PROVIDER_BASE_URL"),
            default_model=os.getenv("NEW_PROVIDER_MODEL", "default-model"),
        )
```

### 步骤 4：添加定价信息（可选）

```python
# server/utils/ai_usage_monitor.py
NEW_PROVIDER_PRICING = {
    "model1": {
        "input": 0.001,
        "output": 0.002,
        "display_name": "新提供商-模型1"
    },
}

ALL_PRICING = {
    **QWEN_PRICING,
    **XUNFEI_PRICING,
    **NEW_PROVIDER_PRICING,  # 添加
}
```

### 步骤 5：配置环境变量

```bash
NEW_PROVIDER_API_KEY=your_api_key
NEW_PROVIDER_BASE_URL=https://api.newprovider.com/v1
NEW_PROVIDER_MODEL=default-model
```

**完成！** 新提供商即可通过 AI Gateway 使用。

## 🎨 API 接口

### 查看所有已配置的提供商

```bash
GET /api/ai_gateway/providers
```

**响应：**
```json
{
  "success": true,
  "providers": [
    {
      "provider": "xunfei",
      "enabled": true,
      "default_model": "lite",
      "models": ["lite", "generalv3", "generalv3.5", "4.0Ultra"]
    },
    {
      "provider": "qwen",
      "enabled": true,
      "default_model": "qwen-plus",
      "models": ["qwen-plus", "qwen-turbo", "qwen-max", "qwen3-max"]
    }
  ],
  "current_provider": "xunfei",
  "current_model": "lite"
}
```

### 查看功能配置

```bash
GET /api/ai_gateway/functions
```

**响应：**
```json
{
  "success": true,
  "function_configs": {
    "live_analysis": {
      "provider": "xunfei",
      "model": "lite"
    },
    "script_generation": {
      "provider": "qwen",
      "model": "qwen3-max"
    },
    "live_review": {
      "provider": "gemini",
      "model": "gemini-2.5-flash-preview-09-2025"
    }
  }
}
```

### 通用聊天接口

```bash
POST /api/ai_gateway/chat/completions
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "function": "live_analysis",  // 可选：自动路由
  "provider": "xunfei",         // 可选：指定提供商
  "model": "lite",              // 可选：指定模型
  "temperature": 0.7,
  "max_tokens": 2048
}
```

### 流式聊天接口

```bash
POST /api/ai_gateway/chat/completions/stream
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "写一段长文本"}
  ],
  "function": "script_generation"
}
```

**响应：** Server-Sent Events (SSE)

```
data: {"delta": "你", "finish_reason": null}
data: {"delta": "好", "finish_reason": null}
data: {"delta": "", "finish_reason": "stop", "usage": {...}}
```

### 更新功能配置

```bash
PUT /api/ai_gateway/functions/live_analysis
Content-Type: application/json

{
  "provider": "qwen",
  "model": "qwen-max"
}
```

## 📊 使用监控

### 查看使用统计

```bash
GET /api/ai_usage/stats/current
```

**响应：**
```json
{
  "by_model": {
    "lite": {
      "calls": 1500,
      "input_tokens": 225000,
      "output_tokens": 75000,
      "cost": 0.00
    },
    "qwen3-max": {
      "calls": 300,
      "input_tokens": 45000,
      "output_tokens": 15000,
      "cost": 0.54
    },
    "gemini-2.5-flash-preview-09-2025": {
      "calls": 5,
      "input_tokens": 7500,
      "output_tokens": 2500,
      "cost": 0.0015
    }
  },
  "total_cost": 0.5415
}
```

### 查看模型定价

```bash
GET /api/ai_usage/models/pricing
```

## ✅ 优势总结

### 1. 统一管理
- ✅ 所有 AI 提供商通过单一接口调用
- ✅ 统一的错误处理和重试机制
- ✅ 统一的使用统计和成本监控

### 2. 灵活配置
- ✅ 每个功能独立配置模型
- ✅ 支持环境变量覆盖
- ✅ 支持运行时动态切换

### 3. 易于扩展
- ✅ 添加新提供商只需4步
- ✅ OpenAI 兼容的提供商即插即用
- ✅ 自动处理 API 差异

### 4. 成本优化
- ✅ 高频功能用免费模型
- ✅ 低频功能用高质量模型
- ✅ 完整的成本监控和统计

### 5. 代码简洁
- ✅ 无需为每个提供商编写客户端
- ✅ 无需为每个提供商创建 API 路由
- ✅ 业务代码只依赖 AI Gateway

## 🎓 最佳实践

### 1. 使用功能级别配置

```python
# ❌ 不推荐：硬编码提供商
gateway.chat_completion(
    messages=[...],
    provider="xunfei",
    model="lite"
)

# ✅ 推荐：使用功能标识
gateway.chat_completion(
    messages=[...],
    function="live_analysis"  # 自动路由到最佳模型
)
```

### 2. 通过环境变量配置

```bash
# ✅ 生产环境
AI_FUNCTION_LIVE_ANALYSIS_PROVIDER=xunfei
AI_FUNCTION_LIVE_ANALYSIS_MODEL=lite

# ✅ 测试环境
AI_FUNCTION_LIVE_ANALYSIS_PROVIDER=qwen
AI_FUNCTION_LIVE_ANALYSIS_MODEL=qwen-turbo
```

### 3. 监控成本

```python
from server.utils.ai_usage_monitor import get_usage_monitor

# 定期检查成本
monitor = get_usage_monitor()
daily = monitor.get_daily_summary()

if daily.total_cost > threshold:
    # 发送告警或自动降级
    gateway.update_function_model("live_analysis", "xunfei", "lite")
```

### 4. 降级策略

```python
from server.ai.ai_gateway import get_gateway

gateway = get_gateway()

try:
    # 首选：高质量模型
    response = gateway.chat_completion(
        messages=[...],
        provider="qwen",
        model="qwen3-max"
    )
except Exception as e:
    # 降级：免费模型
    response = gateway.chat_completion(
        messages=[...],
        provider="xunfei",
        model="lite"
    )
```

## 🔍 故障排查

### 提供商未注册

**问题：** `Provider 'xunfei' not found`

**解决：**
1. 检查环境变量是否配置
2. 检查 API Key 是否正确
3. 查看启动日志

```bash
# 检查已注册的提供商
curl http://localhost:9019/api/ai_gateway/providers
```

### 模型不支持

**问题：** `Model 'xxx' not supported by provider 'xunfei'`

**解决：**
1. 查看提供商支持的模型列表
2. 更新 PROVIDER_TEMPLATES

### API 调用失败

**问题：** `Error calling AI provider: ...`

**解决：**
1. 检查网络连接
2. 检查 API Key 是否有效
3. 查看 base_url 是否正确
4. 查看提供商的 API 文档

## 📚 相关文档

- `server/ai/ai_gateway.py` - AI 网关核心实现
- `server/utils/ai_usage_monitor.py` - 使用监控和定价
- `server/app/api/ai_gateway_api.py` - AI 网关 API 路由
- `AI模型分级使用策略.md` - 成本优化策略

---

**总结：** AI Gateway 是项目的核心 AI 服务层，提供统一、灵活、可扩展的多提供商管理能力。无需为每个 AI 提供商创建独立的客户端和 API 路由。

