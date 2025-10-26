# 🚀 AI 模型控制网关使用指南

## 📖 概述

AI 模型控制网关是一个统一管理多个 AI 服务商的中央控制系统，支持：

- ✅ **多服务商管理** - 通义千问、OpenAI、DeepSeek、豆包、ChatGLM
- ✅ **一键切换** - 快速切换服务商和模型
- ✅ **自动降级** - 主服务失败自动切换备用
- ✅ **成本监控** - 自动记录所有调用和费用
- ✅ **统一接口** - 屏蔽不同服务商的差异

---

## 🎯 快速开始

### 1. 启动服务

```bash
npm run dev
```

### 2. 访问管理界面

浏览器打开：
```
http://localhost:10090/static/ai_gateway_manager.html
```

### 3. 查看当前配置

页面会自动显示：
- 当前使用的服务商和模型
- 所有已注册的服务商
- 降级链配置

---

## 💻 编程集成

### 方法 1：使用网关（推荐）

```python
from server.ai.ai_gateway import get_gateway

# 获取网关实例
gateway = get_gateway()

# 使用默认配置调用
response = gateway.chat_completion(
    messages=[
        {"role": "user", "content": "你好"}
    ],
    temperature=0.3,
    max_tokens=100
)

print(f"响应: {response.content}")
print(f"费用: ¥{response.cost:.4f}")
print(f"耗时: {response.duration_ms:.0f}ms")
```

---

## 🔧 注册服务商

### 通过管理界面注册

1. 打开管理界面
2. 填写"注册新服务商"表单：
   - 选择服务商
   - 输入 API Key
   - （可选）自定义 Base URL
   - （可选）自定义默认模型
3. 点击"注册"

### 通过代码注册

```python
from server.ai.ai_gateway import get_gateway

gateway = get_gateway()

# 注册 DeepSeek
gateway.register_provider(
    provider="deepseek",
    api_key="sk-your-deepseek-api-key",
    base_url="https://api.deepseek.com/v1",  # 可选
    default_model="deepseek-chat",            # 可选
)

# 注册 OpenAI
gateway.register_provider(
    provider="openai",
    api_key="sk-your-openai-api-key",
)
```

### 通过环境变量注册

在 `.env` 文件中添加：

```bash
# 主服务商（自动注册）
AI_SERVICE=qwen
AI_API_KEY=sk-your-qwen-api-key
AI_MODEL=qwen-plus

# DeepSeek（自动注册）
DEEPSEEK_API_KEY=sk-your-deepseek-key

# 豆包（自动注册）
DOUBAO_API_KEY=your-doubao-key

# ChatGLM（自动注册）
GLM_API_KEY=your-glm-key
```

---

## 🛡️ 设置降级链

当主服务商失败时，自动切换到备用服务商。

### 通过代码设置

```python
# 设置降级顺序：Qwen -> DeepSeek -> OpenAI
gateway.set_fallback_chain(["qwen", "deepseek", "openai"])

# 调用时自动降级
response = gateway.chat_completion(messages=[...])
# 如果 Qwen 失败，会自动尝试 DeepSeek
# 如果 DeepSeek 也失败，会尝试 OpenAI
```

### 通过 API 设置

```bash
curl -X POST http://localhost:10090/api/ai_gateway/fallback \
  -H "Content-Type: application/json" \
  -d '{"providers": ["qwen", "deepseek", "openai"]}'
```

---

## 📊 API 接口

### 1. 获取状态

**GET** `/api/ai_gateway/status`

```json
{
  "success": true,
  "current": {
    "provider": "qwen",
    "model": "qwen-plus",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "fallback_chain": ["deepseek", "openai"]
  },
  "providers": {...}
}
```

### 2. 注册服务商

**POST** `/api/ai_gateway/register`

```json
{
  "provider": "deepseek",
  "api_key": "sk-...",
  "base_url": "https://api.deepseek.com/v1",
  "default_model": "deepseek-chat"
}
```

### 3. 切换服务商

**POST** `/api/ai_gateway/switch`

```json
{
  "provider": "qwen",
  "model": "qwen-plus"
}
```

### 4. 对话补全

**POST** `/api/ai_gateway/chat`

```json
{
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "temperature": 0.3,
  "max_tokens": 100
}
```

### 5. 列出服务商

**GET** `/api/ai_gateway/providers`

### 6. 获取模型列表

**GET** `/api/ai_gateway/models/{provider}`

---

## 🎨 内置服务商配置

| 服务商 | 默认Base URL | 默认模型 |
|--------|-------------|----------|
| **Qwen（通义千问）** | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| **OpenAI** | `https://api.openai.com/v1` | `gpt-3.5-turbo` |
| **DeepSeek** | `https://api.deepseek.com/v1` | `deepseek-chat` |
| **Doubao（豆包）** | `https://ark.cn-beijing.volces.com/api/v3` | `doubao-pro` |
| **GLM（智谱）** | `https://open.bigmodel.cn/api/paas/v4` | `glm-4` |

---

## 💰 成本对比

| 服务商 | 模型 | 输入价格 | 输出价格 |
|--------|------|---------|---------|
| **Qwen** | qwen-plus | ¥0.0004/1K | ¥0.002/1K |
| **Qwen** | qwen-turbo | ¥0.0003/1K | ¥0.0006/1K |
| **Qwen** | qwen-max | ¥0.02/1K | ¥0.06/1K |
| **DeepSeek** | deepseek-chat | ¥0.001/1K | ¥0.002/1K |
| **DeepSeek** | deepseek-coder | ¥0.001/1K | ¥0.002/1K |
| **OpenAI** | gpt-3.5-turbo | ¥0.0035/1K | ¥0.007/1K |
| **OpenAI** | gpt-4 | ¥0.21/1K | ¥0.42/1K |

**💡 推荐配置**：
- 日常分析：`qwen-plus` 或 `deepseek-chat`
- 代码生成：`deepseek-coder`
- 高质量内容：`qwen-max` 或 `gpt-4`

---

## 🔄 迁移现有代码

### 从直接使用 OpenAI 客户端迁移

**旧代码**：
```python
from openai import OpenAI

client = OpenAI(api_key="sk-...", base_url="...")
response = client.chat.completions.create(
    model="qwen-plus",
    messages=[...]
)
```

**新代码**：
```python
from server.ai.ai_gateway import get_gateway

gateway = get_gateway()
response = gateway.chat_completion(
    messages=[...],
    temperature=0.3
)
# 返回 AIResponse 对象
print(response.content)  # 响应内容
print(response.cost)     # 自动计算成本
```

---

## ❓ 常见问题

### Q1: 如何查看当前使用的模型？

```python
config = gateway.get_current_config()
print(f"服务商: {config['provider']}")
print(f"模型: {config['model']}")
```

### Q2: 如何禁用某个服务商？

```python
gateway.providers["openai"].enabled = False
```

### Q3: 降级链如何工作？

当主服务商调用失败时，网关会按降级链顺序自动尝试备用服务商，直到成功或所有服务都失败。

### Q4: 成本如何计算？

网关会自动计算每次调用的成本，并集成到 AI 使用监控系统中。

### Q5: 如何测试新服务商？

使用管理界面的"测试调用"功能，或通过 API：

```bash
curl -X POST http://localhost:10090/api/ai_gateway/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "测试"}], "provider": "deepseek"}'
```

---

## 🛠️ 高级用法

### 自定义服务商

```python
gateway.register_provider(
    provider="custom",
    api_key="your-key",
    base_url="https://your-api.com/v1",
    default_model="your-model",
    models=["model-1", "model-2"],
    enabled=True
)
```

### 批量切换

```python
# 白天使用便宜的模型
if is_daytime():
    gateway.switch_provider("qwen", "qwen-turbo")
else:
    # 夜间使用高质量模型
    gateway.switch_provider("qwen", "qwen-max")
```

### 条件调用

```python
# 根据任务类型选择模型
if task_type == "coding":
    response = gateway.chat_completion(
        messages=[...],
        provider="deepseek",
        model="deepseek-coder"
    )
else:
    response = gateway.chat_completion(
        messages=[...],
        # 使用默认配置
    )
```

---

## 📚 相关文档

- [AI 使用监控指南](./MONITORING_GUIDE.md)
- [API 接口契约](./API_CONTRACT.md)
- [成本分析文档](./AI_COST_ANALYSIS.md)

---

**文档更新**: 2025-10-26  
**版本**: v1.0.0  
**维护**: 提猫科技团队
