# ⚡ AI 欠费问题 - 快速修复

## 🔴 问题
```
Error code: 400 - Arrearage (欠费)
Access denied, please make sure your account is in good standing.
```

---

## ✅ 3步快速修复

### 步骤 1: 获取 OpenAI API Key

1. 访问: https://platform.openai.com/api-keys
2. 点击 "Create new secret key"
3. 复制 key（格式：`sk-...`）

### 步骤 2: 设置环境变量

**Windows PowerShell**:
```powershell
$env:OPENAI_API_KEY = "sk-your-api-key-here"
```

**或者编辑配置文件** `server/config/app.json`:
```json
{
  "ai": {
    "openai_api_key": "sk-your-api-key-here"
  }
}
```

### 步骤 3: 重启服务

```bash
# 停止当前服务 (Ctrl+C)
# 重新启动
npm run start:integrated
```

---

## 💰 充值 OpenAI 账户

1. 访问: https://platform.openai.com/account/billing
2. 添加付款方式
3. 充值建议金额：$5-10 USD
4. **费用预估**：一场2小时直播约 $0.01-0.05

---

## 🔍 验证成功

启动后查看日志，应该看到：
```
✅ AI客户端初始化成功
✅ 成功获取AI客户端，准备生成智能话题
```

而不是：
```
❌ AI话题生成失败: Error code: 400 - Arrearage
```

---

## ⚠️ 当前影响

**仍在工作** ✅:
- 抖音弹幕接收
- 语音转写
- 默认话题推荐

**不工作** ❌:
- AI 智能分析
- 个性化建议

---

**详细文档**: 查看 `docs/AI_SERVICE_SETUP.md`

