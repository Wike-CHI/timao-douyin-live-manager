# 🔑 AI 网关 - API Key 管理指南

## 📖 功能概述

AI 网关现在支持完整的 API Key 和服务商管理：

- ✅ **注册服务商** - 添加新的 AI 服务提供商
- ✅ **删除服务商** - 移除不需要的服务商
- ✅ **更新 API Key** - 更换现有服务商的密钥
- ✅ **一键切换** - 快速切换使用的服务商

---

## 🚀 快速开始

### 1. 访问管理界面

```
http://localhost:{PORT}/static/ai_gateway_manager.html
```

> 默认端口为 9019，可通过环境变量 `BACKEND_PORT` 修改

### 2. 主要操作

#### 🔍 查看已注册的服务商
- 界面自动显示所有已注册的服务商
- 显示服务商状态、默认模型、支持的模型列表

#### ➕ 注册新服务商
1. 选择服务商类型
2. 输入 API Key
3. （可选）自定义 Base URL 和默认模型
4. 点击"注册"按钮

#### 🔄 切换服务商
1. 从下拉菜单选择服务商
2. （可选）选择特定模型
3. 点击"切换"按钮

#### 🔑 更新 API Key
1. 选择要更新的服务商
2. 输入新的 API Key
3. 点击"更新 API Key"按钮

#### ❌ 删除服务商
- 点击服务商卡片右上角的"✕ 删除"按钮
- 确认删除操作
- **注意**：无法删除当前正在使用的服务商

---

## 💻 API 接口说明

### 1. 注册服务商

**POST** `/api/ai_gateway/register`

```json
{
  "provider": "deepseek",
  "api_key": "sk-your-api-key",
  "base_url": "https://api.deepseek.com/v1",  // 可选
  "default_model": "deepseek-chat"             // 可选
}
```

**响应**:
```json
{
  "success": true,
  "message": "服务商 deepseek 已注册",
  "config": { ... }
}
```

---

### 2. 删除服务商

**DELETE** `/api/ai_gateway/provider/{provider}`

**示例**:
```bash
curl -X DELETE http://localhost:{PORT}/api/ai_gateway/provider/deepseek
```

> 默认端口为 9019，可通过环境变量 `BACKEND_PORT` 修改

**响应**:
```json
{
  "success": true,
  "message": "服务商 deepseek 已删除",
  "providers": { ... }
}
```

**限制**:
- ❌ 无法删除当前正在使用的服务商
- ✅ 删除后会自动更新服务商列表

---

### 3. 更新 API Key

**PUT** `/api/ai_gateway/provider/api-key`

```json
{
  "provider": "deepseek",
  "api_key": "sk-new-api-key"
}
```

**响应**:
```json
{
  "success": true,
  "message": "服务商 deepseek 的 API Key 已更新"
}
```

**说明**:
- 更新后会自动重新创建客户端连接
- 不影响当前正在进行的请求
- 下次调用时会使用新的 API Key

---

### 4. 切换服务商

**POST** `/api/ai_gateway/switch`

```json
{
  "provider": "qwen",
  "model": "qwen-plus"  // 可选
}
```

---

### 5. 查看所有服务商

**GET** `/api/ai_gateway/providers`

**响应**:
```json
{
  "success": true,
  "providers": {
    "qwen": {
      "provider": "qwen",
      "base_url": "https://...",
      "default_model": "qwen-plus",
      "models": ["qwen-plus", "qwen-turbo", "qwen-max"],
      "enabled": true
    },
    ...
  },
  "current": "qwen"
}
```

---

## 🔧 代码示例

### 注册新服务商

```python
from server.ai.ai_gateway import get_gateway

gateway = get_gateway()

# 注册 DeepSeek
gateway.register_provider(
    provider="deepseek",
    api_key="sk-your-deepseek-key",
    base_url="https://api.deepseek.com/v1",
    default_model="deepseek-chat"
)
```

### 删除服务商

```python
# 删除 DeepSeek
gateway.unregister_provider("deepseek")
```

### 更新 API Key

```python
# 更新 DeepSeek 的 API Key
gateway.update_provider_api_key(
    provider="deepseek",
    api_key="sk-new-api-key"
)
```

---

## ❓ 常见问题

### Q1: 删除服务商时提示"无法删除当前正在使用的服务商"？

**A**: 需要先切换到其他服务商，再删除。

```python
# 1. 先切换到其他服务商
gateway.switch_provider("qwen")

# 2. 再删除
gateway.unregister_provider("deepseek")
```

---

### Q2: 更新 API Key 后是否需要重启服务？

**A**: 不需要。更新后会自动重新创建客户端连接，立即生效。

---

### Q3: 如何批量管理多个服务商？

**A**: 使用环境变量在启动时自动注册：

```bash
# .env 文件
AI_SERVICE=qwen
AI_API_KEY=sk-qwen-key
AI_MODEL=qwen-plus

DEEPSEEK_API_KEY=sk-deepseek-key
DOUBAO_API_KEY=sk-doubao-key
GLM_API_KEY=sk-glm-key
```

所有配置了环境变量的服务商会在启动时自动注册。

---

### Q4: 如何查看某个服务商的 API Key？

**A**: 出于安全考虑，API Key 不会在接口中返回。如需查看，请检查：
- 环境变量 `.env` 文件
- 服务商官网的 API 管理后台

---

### Q5: 删除服务商后，数据会丢失吗？

**A**: 不会。删除操作只是移除网关中的配置，不影响：
- 历史调用记录（在监控系统中）
- 服务商账户中的数据
- 其他已注册的服务商

---

## 🛡️ 安全建议

### 1. API Key 保护
- ✅ 使用环境变量存储 API Key
- ✅ 不要将 `.env` 文件提交到 Git
- ✅ 定期轮换 API Key
- ❌ 不要在代码中硬编码 API Key

### 2. 最小权限原则
- 仅授予必要的 API 权限
- 为不同环境使用不同的 API Key

### 3. 监控异常
```python
from server.utils.ai_usage_monitor import get_usage_monitor

monitor = get_usage_monitor()
daily = monitor.get_daily_summary()

# 检查异常调用
if daily.total_calls > 10000:
    logger.warning("今日调用次数异常")
```

---

## 📊 实际案例

### 场景 1: 更换服务商

某天 DeepSeek 限流，需要临时切换到 Qwen：

```python
# 方式 1: Web 界面
# 打开管理界面，点击切换到 Qwen

# 方式 2: API 调用
curl -X POST http://localhost:{PORT}/api/ai_gateway/switch \

> 默认端口为 9019，可通过环境变量 `BACKEND_PORT` 修改
  -d '{"provider": "qwen", "model": "qwen-plus"}'

# 方式 3: 代码控制
gateway.switch_provider("qwen", "qwen-plus")
```

---

### 场景 2: API Key 泄露应急处理

发现 API Key 泄露，需要立即更换：

```bash
# 1. 快速更新 API Key
curl -X PUT http://localhost:{PORT}/api/ai_gateway/provider/api-key \

> 默认端口为 9019，可通过环境变量 `BACKEND_PORT` 修改
  -H "Content-Type: application/json" \
  -d '{"provider": "qwen", "api_key": "sk-new-safe-key"}'

# 2. 到服务商后台禁用旧密钥

# 3. 更新环境变量
echo "AI_API_KEY=sk-new-safe-key" >> .env
```

---

### 场景 3: 添加新服务商用于测试

```python
# 注册测试用的 OpenAI
gateway.register_provider(
    provider="openai",
    api_key="sk-test-key",
    default_model="gpt-3.5-turbo"
)

# 测试调用
response = gateway.chat_completion(
    messages=[{"role": "user", "content": "测试"}],
    provider="openai"
)

# 测试完成后删除
gateway.unregister_provider("openai")
```

---

## 🎯 最佳实践

### 1. 统一管理 API Key
```bash
# .env 文件
# 主服务商
AI_SERVICE=qwen
AI_API_KEY=${QWEN_API_KEY}
AI_MODEL=qwen-plus

# 备用服务商
DEEPSEEK_API_KEY=${DEEPSEEK_KEY}
```

### 2. 定期检查服务商状态
```python
# 每周检查
gateway = get_gateway()
providers = gateway.list_providers()

for name, config in providers.items():
    if not config['enabled']:
        logger.warning(f"服务商 {name} 已禁用")
```

### 3. 成本优化
```python
# 日常使用便宜的模型
gateway.switch_provider("qwen", "qwen-turbo")

# 关键任务临时切换
response = gateway.chat_completion(
    messages=[...],
    model="qwen-max"  # 临时使用高质量模型
)
```

---

**更新时间**: 2025-10-26  
**版本**: v1.0.0  
**功能**: ✅ API Key 管理完整支持
