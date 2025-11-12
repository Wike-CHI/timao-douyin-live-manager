# 🤖 AI 服务配置指南

## 问题：AI 服务欠费错误

### 错误信息
```
Error code: 400 - {'error': {'code': 'Arrearage', 'message': 'Access denied, please make sure your account is in good standing.'}}
```

---

## ✅ 解决方案

### 方案 1: 配置 OpenAI API Key（推荐）

#### 步骤 1: 获取 API Key

1. **访问 OpenAI 平台**
   - URL: https://platform.openai.com/api-keys
   - 登录您的 OpenAI 账户

2. **创建新的 API Key**
   - 点击 "Create new secret key"
   - 复制生成的 key（格式：`sk-...`）

3. **检查账户余额**
   - 访问: https://platform.openai.com/account/billing
   - 确保有足够余额（建议至少 $5）
   - 如果余额不足，请充值

#### 步骤 2: 配置 API Key

##### 选项 A: 使用环境变量（推荐）

**Windows (PowerShell)**:
```powershell
# 临时设置（当前会话）
$env:OPENAI_API_KEY = "sk-your-api-key-here"

# 永久设置（需要重启终端）
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-your-api-key-here', 'User')
```

**Windows (CMD)**:
```cmd
set OPENAI_API_KEY=sk-your-api-key-here
```

**Linux/Mac**:
```bash
# 临时设置
export OPENAI_API_KEY="sk-your-api-key-here"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export OPENAI_API_KEY="sk-your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

##### 选项 B: 使用配置文件

编辑 `server/config/app.json`:
```json
{
  "ai": {
    "openai_api_key": "sk-your-api-key-here",
    "default_provider": "openai",
    "default_model": "gpt-4o-mini"
  }
}
```

#### 步骤 3: 重启服务

```bash
# 停止当前服务 (Ctrl+C)

# 重新启动
npm run start:integrated
```

---

### 方案 2: 使用其他 AI 提供商

如果您有其他 AI 提供商的账户：

#### Azure OpenAI

1. **配置环境变量**:
```bash
# Windows PowerShell
$env:AI_PROVIDER = "azure"
$env:AZURE_OPENAI_API_KEY = "your-azure-key"
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com"
$env:AZURE_OPENAI_DEPLOYMENT = "your-deployment-name"
```

2. **配置文件** (`server/config/app.json`):
```json
{
  "ai": {
    "default_provider": "azure",
    "azure_api_key": "your-azure-key",
    "azure_endpoint": "https://your-resource.openai.azure.com",
    "azure_deployment": "your-deployment-name"
  }
}
```

#### 其他兼容 OpenAI API 的服务

```bash
# 例如使用国内代理服务
$env:OPENAI_API_KEY = "your-proxy-key"
$env:OPENAI_API_BASE = "https://api.your-proxy.com/v1"
```

---

### 方案 3: 禁用 AI 功能（临时）

如果暂时无法配置 AI 服务，系统会自动降级：

**当前降级行为**:
- ✅ 使用预设话题推荐
- ✅ 基础数据统计
- ❌ 无智能分析
- ❌ 无个性化建议

**禁用 AI**（可选）:
```json
{
  "ai": {
    "enabled": false
  }
}
```

---

## 🧪 验证配置

### 1. 检查环境变量

**Windows PowerShell**:
```powershell
echo $env:OPENAI_API_KEY
```

**Linux/Mac**:
```bash
echo $OPENAI_API_KEY
```

### 2. 检查配置文件

查看 `server/config/app.json`:
```bash
cat server/config/app.json | grep openai_api_key
```

### 3. 测试 API 连接

启动服务后，查看日志：
```
✅ 成功: AI客户端初始化成功
❌ 失败: AI话题生成失败: Error code: 400 - Arrearage
```

---

## 📊 AI 功能说明

### 已启用 AI 时
- 🎯 智能话题推荐（基于上下文）
- 📈 实时氛围分析
- 💡 个性化建议
- 🔥 热点识别
- 👥 观众互动分析

### 禁用 AI 时（降级模式）
- 📝 预设话题推荐
- 📊 基础数据统计
- ⏱️ 时间管理
- 📥 数据记录

---

## 💰 费用估算

### OpenAI API 价格（2024）

| 模型 | 输入 (1M tokens) | 输出 (1M tokens) | 推荐场景 |
|------|------------------|------------------|----------|
| gpt-4o-mini | $0.15 | $0.60 | ⭐ 推荐（性价比高） |
| gpt-4o | $2.50 | $10.00 | 需要更高质量 |
| gpt-3.5-turbo | $0.50 | $1.50 | 预算有限 |

### 预估使用量

**一场 2 小时直播**:
- 智能分析: ~50-100 次调用
- 每次约 500-1000 tokens
- **总计**: 约 $0.01-0.05 USD
- **月成本**（30场）: ~$0.3-1.5 USD

---

## ⚠️ 常见问题

### Q1: API Key 在哪里配置？

**优先级顺序**:
1. 环境变量 `AI_API_KEY`
2. 环境变量 `OPENAI_API_KEY`
3. 配置文件 `server/config/app.json`

### Q2: 如何知道 API Key 是否有效？

查看后端日志：
```
✅ 成功: 2025-11-02 19:38:10 - AI客户端初始化成功
❌ 失败: AI话题生成失败: Error code: 401 - Invalid API key
❌ 欠费: Error code: 400 - Arrearage
```

### Q3: 可以使用免费的 AI 服务吗？

可以配置兼容 OpenAI API 的其他服务：
- Groq（有免费额度）
- Together AI
- 国内代理服务

### Q4: 为什么有些功能还在工作？

系统具有智能降级机制：
- 预设话题库作为后备
- 语音转写使用本地模型（SenseVoice）
- 基础统计不依赖 AI

---

## 🔒 安全建议

### 1. 保护 API Key
- ❌ 不要提交到 Git
- ❌ 不要分享给他人
- ✅ 使用环境变量
- ✅ 定期轮换 Key

### 2. .gitignore 配置
确保以下文件在 `.gitignore` 中：
```
.env
.env.local
server/config/app.json
server/app/config/app.json
```

### 3. API Key 格式
- OpenAI: `sk-...`（以 sk- 开头）
- Azure: 32 位十六进制字符串

---

## 🚀 快速开始（推荐流程）

### 1. 最快配置方式

```bash
# 1. 设置环境变量（临时，用于测试）
$env:OPENAI_API_KEY = "sk-your-key-here"

# 2. 启动服务
npm run start:integrated

# 3. 观察日志确认成功
```

### 2. 生产环境配置

```bash
# 1. 创建 .env 文件
echo 'OPENAI_API_KEY=sk-your-key-here' > .env

# 2. 启动服务
npm run start:integrated
```

---

## 📞 支持

如果问题持续：

1. **检查 OpenAI 状态**
   - https://status.openai.com

2. **验证 API Key**
   - 在 OpenAI Dashboard 中测试

3. **查看完整日志**
   - 搜索 "AI" 相关错误
   - 检查网络连接

4. **联系支持**
   - 提供错误日志
   - 说明配置方式

---

**最后更新**: 2025-11-02  
**状态**: ✅ 可用

