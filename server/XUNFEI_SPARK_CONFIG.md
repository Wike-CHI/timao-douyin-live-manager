# 科大讯飞星火大模型配置指南

## 📍 控制台信息填写说明

### 1. 访问控制台

- **控制台地址**: https://console.xfyun.cn/services/cbm
- **HTTP调用文档**: https://www.xfyun.cn/doc/spark/HTTP调用文档.html

### 2. 创建应用并获取凭证

在控制台中需要获取以下信息：

| 字段 | 说明 | 用途 | 示例 |
|------|------|------|------|
| **APPID** | 应用ID | 应用标识 | `12345678` |
| **APIPassword** | API密码 | **批处理API和HTTP接口使用（推荐）** | `password1234567890` |
| **APIKey** | API密钥 | HTTP/OpenAI兼容接口使用 | `key1234567890` |
| **APISecret** | API密钥 | WebSocket接口签名使用 | `abcdef1234567890abcdef1234567890` |

**⚠️ 重要提示**：
- **批处理API**通常使用 **APIPassword** 进行认证
- OpenAI兼容接口可以使用 **APIPassword** 或 **APIKey**
- 如果遇到 `HMAC signature cannot be verified` 错误，请尝试使用 **APIPassword** 或 **APIKey**
- WebSocket接口才使用APISecret进行HMAC签名

### 3. 环境变量配置

在 `server/.env` 文件中配置：

```env
# 科大讯飞星火大模型配置
# 方式1：使用APIPassword（推荐，批处理API使用）
XUNFEI_API_KEY=你的APIPassword

# 方式2：如果接口需要APPID:APIPassword格式
# XUNFEI_API_KEY=你的APPID:你的APIPassword

# 方式3：使用APIKey（如果控制台提供APIKey）
# XUNFEI_API_KEY=你的APIKey

# 方式4：如果只有APISecret，可以尝试（但可能不工作）
# XUNFEI_API_KEY=你的APPID:你的APISecret

# Base URL（使用OpenAI兼容接口）
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1

# 默认模型（推荐使用免费的 lite）
XUNFEI_MODEL=lite
```

**⚠️ 注意**：如果遇到认证错误，请：
1. 确认控制台中获取的是 **APIPassword**、**APIKey** 还是 **APISecret**
2. **批处理API优先使用 APIPassword**
3. OpenAI兼容接口可以尝试 **APIPassword** 或 **APIKey**
4. 运行测试脚本自动尝试多种配置：`python server/test_xunfei_spark.py`

---

## 🔑 API Key 格式说明

### 格式要求

⚠️ **重要**：根据实际测试，科大讯飞星火大模型的 OpenAI 兼容接口可能需要：

**方式1：使用APIPassword（推荐，批处理API）**
```env
XUNFEI_API_KEY=你的APIPassword
```

**方式2：如果接口需要APPID:APIPassword格式**
```env
XUNFEI_API_KEY=你的APPID:你的APIPassword
```

**方式3：使用APIKey**
```env
XUNFEI_API_KEY=你的APIKey
```

**方式4：如果接口需要APPID:APIKey格式**
```env
XUNFEI_API_KEY=你的APPID:你的APIKey
```

**方式5：如果接口需要APPID:APISecret格式（WebSocket）**
```env
XUNFEI_API_KEY=你的APPID:你的APISecret
```

**注意**：
- 控制台中通常有 **APIPassword**、**APIKey** 和 **APISecret** 字段
- **批处理API**通常使用 **APIPassword**
- OpenAI兼容接口可以使用 **APIPassword** 或 **APIKey**
- WebSocket接口使用 **APISecret** 进行签名
- 如果遇到认证错误，优先尝试使用 **APIPassword**

### 获取步骤

1. **登录控制台**
   - 访问：https://console.xfyun.cn/services/cbm
   - 登录您的账号

2. **创建应用**
   - 点击"创建应用"
   - 选择"星火大模型"服务
   - 填写应用名称和描述

3. **获取凭证**
   - 在应用详情页找到 **APPID**
   - 在应用详情页找到 **APISecret**
   - 组合格式：`APPID:APISecret`

---

## 📋 控制台字段对应关系

### 控制台显示 → 环境变量映射

| 控制台字段 | 环境变量 | 说明 | 推荐使用 |
|-----------|---------|------|---------|
| **APPID** | `XUNFEI_API_KEY` 的第一部分（如果使用组合格式） | 应用ID | 可选 |
| **APIPassword** | `XUNFEI_API_KEY`（直接使用）或第二部分（组合格式） | **批处理API和HTTP接口使用** | ✅ **推荐** |
| **APIKey** | `XUNFEI_API_KEY`（直接使用）或第二部分（组合格式） | HTTP/OpenAI兼容接口使用 | ✅ 备选 |
| **APISecret** | `XUNFEI_API_KEY` 的第二部分（如果使用组合格式） | WebSocket接口签名 | 不推荐用于HTTP |

### 配置示例

**示例1：使用APIPassword（推荐，批处理API）**

假设控制台显示：
- APPID: `12345678`
- APIPassword: `password1234567890abcdef`
- APIKey: `key1234567890abcdef`
- APISecret: `abcdef1234567890abcdef1234567890`

则在 `.env` 文件中配置：
```env
# 方式1：直接使用APIPassword（推荐，批处理API）
XUNFEI_API_KEY=password1234567890abcdef

# 方式2：如果接口需要APPID:APIPassword格式
# XUNFEI_API_KEY=12345678:password1234567890abcdef

# 方式3：使用APIKey（备选）
# XUNFEI_API_KEY=key1234567890abcdef
```

**示例2：如果只有APISecret**

如果控制台只提供APISecret，可以尝试：
```env
# 尝试1：直接使用APISecret（可能不工作）
XUNFEI_API_KEY=abcdef1234567890abcdef1234567890

# 尝试2：APPID:APISecret格式（可能不工作）
XUNFEI_API_KEY=12345678:abcdef1234567890abcdef1234567890
```

**⚠️ 重要**：如果遇到认证错误，请：
1. 确认控制台中获取的是 **APIPassword**、**APIKey** 还是 **APISecret**
2. **批处理API优先使用 APIPassword**
3. OpenAI兼容接口可以尝试 **APIPassword** 或 **APIKey**
4. 运行测试脚本：`python server/test_xunfei_spark.py` 自动尝试多种配置

---

## 🌐 Base URL 配置

### OpenAI 兼容接口

科大讯飞星火大模型提供 OpenAI 兼容的 HTTP 接口：

```env
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1
```

**注意**：
- 这是 OpenAI 兼容接口，不是原生讯飞接口
- 使用标准的 OpenAI SDK 即可调用
- 不需要额外的认证头或签名

---

## 🎯 模型选择

### 支持的模型

| 模型 | 定价 | 特点 | 推荐场景 |
|------|------|------|---------|
| **lite** | 免费 | 轻量快速 | 高频调用、测试、直播分析 |
| generalv3 | ¥0.003/1K | 通用能力 | 一般任务 |
| generalv3.5 | ¥0.0036/1K | 增强能力 | 复杂任务 |
| 4.0Ultra | ¥0.005/1K | 最强能力 | 高质量要求 |

### 推荐配置

```env
# 使用免费模型（推荐）
XUNFEI_MODEL=lite
```

---

## ✅ 完整配置示例

### 最小配置（推荐）

```env
# 科大讯飞星火大模型
XUNFEI_API_KEY=你的APPID:你的APISecret
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1
XUNFEI_MODEL=lite
```

### 实际示例

```env
# 假设控制台显示：
# APPID: 12345678
# APISecret: abcdef1234567890abcdef1234567890

XUNFEI_API_KEY=12345678:abcdef1234567890abcdef1234567890
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1
XUNFEI_MODEL=lite
```

---

## 🔍 验证配置

### 方法1：检查环境变量

```bash
# 进入Python环境
python

>>> import os
>>> os.getenv("XUNFEI_API_KEY")
'12345678:abcdef1234567890abcdef1234567890'  # 应该显示你的密钥
```

### 方法2：查看启动日志

启动服务后，查看日志输出：

```
✅ 已注册讯飞(Xunfei)提供商: base_url=https://spark-api-open.xf-yun.com/v1 默认模型=lite
AI服务商已注册: xunfei (模型: lite)
```

### 方法3：测试调用

```python
from server.ai.ai_gateway import AIGateway

gateway = AIGateway.get_instance()
response = gateway.chat_completion(
    messages=[{"role": "user", "content": "你好"}],
    provider="xunfei",
    model="lite"
)
print(response["content"])
```

---

## ⚠️ 常见问题

### Q1: API Key 格式错误

**错误**: `401 Unauthorized` 或 `Invalid API Key`

**解决**:
1. 确认格式为 `APPID:APISecret`（用冒号分隔）
2. 确认 APPID 和 APISecret 没有多余空格
3. 确认从控制台复制的值完整

### Q2: 控制台找不到 APISecret

**解决**:
1. 在应用详情页查找"密钥"或"Secret"
2. 如果没有，可能需要重新生成
3. 确保应用已开通"星火大模型"服务

### Q3: Base URL 错误

**错误**: `Connection refused` 或 `404 Not Found`

**解决**:
1. 确认使用 OpenAI 兼容接口：`https://spark-api-open.xf-yun.com/v1`
2. 不要使用原生讯飞接口地址
3. 确认网络可以访问该域名

### Q4: 模型不存在

**错误**: `Model 'xxx' not found`

**解决**:
1. 确认模型名称正确：`lite`、`generalv3`、`generalv3.5`、`4.0Ultra`
2. 确认账户有权限使用该模型
3. 使用免费的 `lite` 模型测试

---

## 📚 相关文档

- [科大讯飞使用指南](../docs/AI处理工作流/科大讯飞使用指南.md)
- [AI网关配置说明](./AI_GATEWAY_CONFIG.md)
- [环境变量配置模板](./ENV_TEMPLATE.md)

---

## 🎊 总结

1. **控制台获取**: APPID 和 APISecret
2. **格式组合**: `APPID:APISecret`
3. **配置环境变量**: `XUNFEI_API_KEY=APPID:APISecret`
4. **使用 OpenAI 兼容接口**: `https://spark-api-open.xf-yun.com/v1`
5. **推荐免费模型**: `lite`

**不需要单独配置客户端，使用统一的 OpenAI 兼容接口即可！**

