# 🚀 AI 网关 - 简化版说明

## 核心功能

AI 网关提供统一的接口管理多个 AI 服务商，**无需降级策略**，简单直接。

---

## ✨ 主要特性

### 1. 统一调用接口
所有 AI 服务通过网关统一调用，业务代码无需关心底层实现。

### 2. 一键切换服务商
可以随时切换不同的 AI 服务商和模型，无需修改代码。

### 3. 自动成本监控
所有调用自动记录费用和使用情况。

### 4. 多服务商支持
- ✅ 通义千问 (Qwen)
- ✅ OpenAI (GPT系列)
- ✅ DeepSeek
- ✅ 字节豆包
- ✅ 智谱 ChatGLM

---

## 📖 快速开始

### 1. 在代码中使用

```python
from server.ai.ai_gateway import get_gateway

# 获取网关实例
gateway = get_gateway()

# 调用 AI（使用当前配置的服务商）
response = gateway.chat_completion(
    messages=[
        {"role": "user", "content": "你好"}
    ],
    temperature=0.3
)

# 获取结果
print(response.content)      # AI 响应内容
print(response.cost)          # 本次调用费用
print(response.provider)      # 使用的服务商
print(response.model)         # 使用的模型
```

### 2. 临时指定服务商

```python
# 临时使用 DeepSeek
response = gateway.chat_completion(
    messages=[...],
    provider="deepseek",
    model="deepseek-chat"
)
```

### 3. 切换默认服务商

```python
# 全局切换到 OpenAI GPT-4
gateway.switch_provider("openai", "gpt-4")

# 之后所有调用都使用 GPT-4
response = gateway.chat_completion(messages=[...])
```

---

## 🎛️ Web 管理界面

访问：`http://localhost:10090/static/ai_gateway_manager.html`

功能：
- 查看当前使用的服务商和模型
- 一键切换服务商
- 注册新服务商
- 测试 AI 调用

---

## 🔧 配置方式

### 方式 1: 环境变量（推荐）

在 `.env` 文件中配置：

```bash
# 主服务商
AI_SERVICE=qwen
AI_API_KEY=sk-your-qwen-api-key
AI_MODEL=qwen-plus

# 其他服务商（可选）
DEEPSEEK_API_KEY=sk-your-deepseek-key
DOUBAO_API_KEY=your-doubao-key
GLM_API_KEY=your-glm-key
```

### 方式 2: 代码注册

```python
gateway.register_provider(
    provider="deepseek",
    api_key="sk-your-api-key",
    base_url="https://api.deepseek.com/v1",  # 可选
    default_model="deepseek-chat"             # 可选
)
```

### 方式 3: API 注册

```bash
curl -X POST http://localhost:10090/api/ai_gateway/register \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "deepseek",
    "api_key": "sk-your-api-key"
  }'
```

---

## 📊 API 接口

### 1. 获取状态
```bash
GET /api/ai_gateway/status
```

### 2. 切换服务商
```bash
POST /api/ai_gateway/switch
{
  "provider": "qwen",
  "model": "qwen-plus"
}
```

### 3. 注册服务商
```bash
POST /api/ai_gateway/register
{
  "provider": "deepseek",
  "api_key": "sk-..."
}
```

### 4. 测试调用
```bash
POST /api/ai_gateway/chat
{
  "messages": [{"role": "user", "content": "测试"}]
}
```

---

## 💰 成本对比

| 服务商 | 模型 | 输入价格 | 输出价格 | 推荐场景 |
|--------|------|---------|---------|---------|
| **Qwen** | qwen-plus | ¥0.0004/1K | ¥0.002/1K | 日常分析 ✅ |
| **Qwen** | qwen-turbo | ¥0.0003/1K | ¥0.0006/1K | 大量调用 |
| **DeepSeek** | deepseek-chat | ¥0.001/1K | ¥0.002/1K | 代码生成 ✅ |
| **Qwen** | qwen-max | ¥0.02/1K | ¥0.06/1K | 高质量内容 |
| **OpenAI** | gpt-4 | ¥0.21/1K | ¥0.42/1K | 特殊需求 |

---

## ❓ 常见问题

### Q1: 如何查看当前使用的模型？

```python
config = gateway.get_current_config()
print(f"服务商: {config['provider']}")
print(f"模型: {config['model']}")
```

### Q2: 如何切换服务商？

**代码方式**:
```python
gateway.switch_provider("deepseek", "deepseek-chat")
```

**Web界面**: 打开管理界面，点击切换按钮

**API方式**: 调用 `/api/ai_gateway/switch`

### Q3: 调用失败怎么办？

网关会返回错误信息：
```python
response = gateway.chat_completion(messages=[...])
if not response.success:
    print(f"调用失败: {response.error}")
```

业务代码可以根据需要自行处理错误。

### Q4: 如何测试新服务商？

使用管理界面的"测试调用"功能，或：
```python
response = gateway.chat_completion(
    messages=[{"role": "user", "content": "测试"}],
    provider="new_provider"
)
```

---

## 🎯 最佳实践

### 1. 日常使用便宜模型
```python
gateway.switch_provider("qwen", "qwen-plus")
```

### 2. 关键任务临时切换
```python
# 重要内容生成时临时使用高质量模型
response = gateway.chat_completion(
    messages=[...],
    model="qwen-max"
)
```

### 3. 定期检查成本
```python
from server.utils.ai_usage_monitor import get_usage_monitor

monitor = get_usage_monitor()
daily = monitor.get_daily_summary()
print(f"今日费用: ¥{daily.total_cost:.2f}")
```

---

## 📚 相关文档

- [完整功能文档](./AI_GATEWAY_GUIDE.md)
- [成本监控文档](./MONITORING_GUIDE.md)
- [API 文档](http://localhost:10090/docs)

---

**更新时间**: 2025-10-26  
**版本**: v1.0.0（简化版，无降级策略）
