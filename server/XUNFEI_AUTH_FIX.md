# 科大讯飞星火大模型认证问题修复指南

## 🔍 问题诊断

### 错误信息
```
Error code: 401 - {'message': 'HMAC signature cannot be verified: fail to retrieve credential'}
```

### 原因分析

科大讯飞星火大模型的 `https://spark-api-open.xf-yun.com/v1` OpenAI兼容接口可能需要：

1. **APIKey** 而不是 APISecret
2. 或者该接口不完全支持OpenAI兼容方式
3. 或者需要使用WebSocket接口

---

## ✅ 解决方案

### 方案1：使用APIPassword（推荐，批处理API）

在控制台中获取 **APIPassword**，然后配置：

```env
# 方式1：使用APIPassword（推荐，批处理API）
XUNFEI_API_KEY=你的APIPassword

# 方式2：如果控制台提供的是APPID:APIPassword格式
XUNFEI_API_KEY=你的APPID:你的APIPassword
```

### 方案1.5：使用APIKey（备选）

如果控制台提供的是 **APIKey**，可以尝试：

```env
# 方式1：使用APIKey
XUNFEI_API_KEY=你的APIKey

# 方式2：如果控制台提供的是APPID:APIKey格式
XUNFEI_API_KEY=你的APPID:你的APIKey
```

### 方案2：检查控制台凭证类型

在 https://console.xfyun.cn/services/cbm 中：

1. **查看应用详情**
2. **确认凭证类型**：
   - **APIKey** - 用于HTTP/OpenAI兼容接口
   - **APISecret** - 用于WebSocket接口的签名
   - **APPID** - 应用标识

### 方案3：使用WebSocket接口（如果HTTP接口不支持）

如果OpenAI兼容接口确实不支持，可能需要：

1. 使用WebSocket接口
2. 或者使用官方SDK：`spark-ai-python`

---

## 🔧 配置检查清单

### 当前配置
```env
XUNFEI_API_KEY=56077594:Y2M0Y2NkMTc...IxZTJmNDI2
```

### 需要确认

1. **控制台中的凭证类型**：
   - [ ] 这是 **APIPassword**、**APIKey** 还是 **APISecret**？
   - [ ] 控制台是否显示"APIPassword"字段？（批处理API使用）
   - [ ] 控制台是否显示"APIKey"字段？

2. **接口类型**：
   - [ ] 是否确认 `https://spark-api-open.xf-yun.com/v1` 支持OpenAI兼容？
   - [ ] 是否需要使用WebSocket接口？

3. **文档确认**：
   - [ ] 查看 HTTP调用文档：https://www.xfyun.cn/doc/spark/HTTP调用文档.html
   - [ ] 确认认证方式

---

## 🧪 测试不同配置

运行测试脚本会自动尝试多种配置：

```bash
python server/test_xunfei_spark.py
```

测试脚本会尝试：
1. `APPID:APISecret` 格式
2. 仅 `APISecret` 
3. 单独的 `APIKey`（如果配置了 `XUNFEI_APIKEY`）

---

## 📝 正确的配置格式

### 如果控制台提供的是APIPassword（推荐）

```env
# 直接使用APIPassword（批处理API）
XUNFEI_API_KEY=你的APIPassword值
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1
XUNFEI_MODEL=lite
```

### 如果控制台提供的是APPID和APIPassword

```env
# 组合格式（如果接口需要）
XUNFEI_API_KEY=你的APPID:你的APIPassword
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1
XUNFEI_MODEL=lite
```

### 如果控制台提供的是APIKey

```env
# 直接使用APIKey
XUNFEI_API_KEY=你的APIKey值
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1
XUNFEI_MODEL=lite
```

### 如果控制台提供的是APPID和APIKey

```env
# 组合格式（如果接口需要）
XUNFEI_API_KEY=你的APPID:你的APIKey
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1
XUNFEI_MODEL=lite
```

### 如果控制台提供的是APPID、APIKey、APISecret

```env
# 尝试使用APIKey
XUNFEI_API_KEY=你的APIKey

# 或者尝试组合
XUNFEI_API_KEY=你的APPID:你的APIKey

# Base URL和模型
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1
XUNFEI_MODEL=lite
```

---

## 🔍 验证步骤

1. **检查控制台**：
   - 登录 https://console.xfyun.cn/services/cbm
   - 查看应用详情
   - 确认显示的字段名称

2. **查看文档**：
   - HTTP调用文档：https://www.xfyun.cn/doc/spark/HTTP调用文档.html
   - 确认认证方式

3. **运行测试**：
   ```bash
   python server/test_xunfei_spark.py
   ```

4. **查看错误信息**：
   - 如果仍然是401错误，可能需要使用WebSocket接口
   - 或者联系科大讯飞技术支持

---

## ⚠️ 重要提示

1. **APIPassword vs APIKey vs APISecret**：
   - **APIPassword**：通常用于批处理API和HTTP接口（推荐）
   - **APIKey**：通常用于HTTP/OpenAI兼容接口
   - **APISecret**：通常用于WebSocket接口的签名

2. **接口类型**：
   - OpenAI兼容接口：`https://spark-api-open.xf-yun.com/v1`
   - WebSocket接口：`wss://spark-api.xf-yun.com/v3.5/chat`

3. **如果OpenAI兼容接口不支持**：
   - 考虑使用WebSocket接口
   - 或者使用官方SDK
   - 或者使用其他AI服务商（如Qwen、Gemini）

---

## 📚 相关资源

- [科大讯飞HTTP调用文档](https://www.xfyun.cn/doc/spark/HTTP调用文档.html)
- [科大讯飞WebSocket文档](https://www.xfyun.cn/doc/spark/Web.html)
- [控制台](https://console.xfyun.cn/services/cbm)

