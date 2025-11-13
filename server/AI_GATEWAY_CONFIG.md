# AI网关API Key配置说明

## 📍 配置读取位置

AI网关通过读取**环境变量**（`.env` 文件）来获取API key。

**配置文件位置**：
- `server/.env` ← **主要配置文件**（推荐）
- `.env` ← 根目录配置文件（可覆盖 server/.env）

---

## 🔍 代码实现

AI网关在 `server/ai/ai_gateway.py` 中通过 `os.getenv()` 直接读取环境变量：

```python
def _load_from_env(self) -> None:
    """从环境变量加载配置"""
    # 主服务商配置（向后兼容）
    primary_api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    
    # 加载其他服务商配置
    self._load_additional_providers()

def _load_additional_providers(self) -> None:
    """加载额外的服务商配置"""
    # 科大讯飞
    xunfei_key = os.getenv("XUNFEI_API_KEY")
    
    # 通义千问
    qwen_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    
    # DeepSeek
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    
    # Gemini
    gemini_key = os.getenv("AIHUBMIX_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    # ... 其他服务商
```

---

## 📋 支持的服务商及环境变量

### 1. 科大讯飞（Xunfei）

```env
XUNFEI_API_KEY=your-xunfei-api-key
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1
XUNFEI_MODEL=lite
```

### 2. 通义千问（Qwen）

```env
QWEN_API_KEY=your-qwen-api-key
# 或
DASHSCOPE_API_KEY=your-dashscope-api-key

QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
```

### 3. DeepSeek

```env
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

### 4. Gemini（通过 AiHubMix）

```env
GEMINI_API_KEY=your-gemini-api-key
# 或
AIHUBMIX_API_KEY=your-aihubmix-api-key

AIHUBMIX_BASE_URL=https://aihubmix.com/v1
GEMINI_MODEL=gemini-2.5-flash-preview-09-2025
```

### 5. OpenAI

```env
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
```

### 6. 豆包（Doubao）

```env
DOUBAO_API_KEY=your-doubao-api-key
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```

### 7. ChatGLM

```env
GLM_API_KEY=your-glm-api-key
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
```

---

## 🚀 配置步骤

### 1. 创建或编辑 `.env` 文件

```bash
cd server
vim .env
```

### 2. 添加API Key配置

```env
# 例如：配置通义千问
QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus

# 例如：配置Gemini
GEMINI_API_KEY=your-gemini-api-key
AIHUBMIX_BASE_URL=https://aihubmix.com/v1
```

### 3. 重启服务

修改 `.env` 文件后需要重启后端服务才能生效：

```bash
# 如果使用 systemd
sudo systemctl restart timao-backend

# 如果直接运行
python app/main.py
```

---

## ⚠️ 重要说明

### 1. 环境变量加载顺序

Python的 `dotenv` 库按以下顺序加载：

1. **系统环境变量**（最高优先级）
2. **根目录 `.env` 文件**
3. **`server/.env` 文件**

### 2. 配置不通过 config.py

**重要**：AI网关**不通过** `config.py` 读取配置，而是直接使用 `os.getenv()` 读取环境变量。

- ❌ **不会读取**：`config.ai.qwen_api_key`
- ✅ **直接读取**：`os.getenv("QWEN_API_KEY")`

### 3. 功能级模型配置（可选）

可以为不同功能配置不同的模型：

```env
# 功能级AI模型配置（可选）
AI_FUNCTION_STYLE_PROFILE_MODEL=qwen-max
AI_FUNCTION_SCRIPT_GENERATION_MODEL=qwen-max
AI_FUNCTION_LIVE_ANALYSIS_MODEL=lite
AI_FUNCTION_LIVE_REVIEW_MODEL=gemini-2.5-flash-preview
AI_FUNCTION_CHAT_FOCUS_MODEL=qwen-max
AI_FUNCTION_TOPIC_GENERATION_MODEL=qwen-plus
```

---

## 🔧 验证配置

### 方法1：检查环境变量

```bash
# 进入Python环境
python

>>> import os
>>> os.getenv("QWEN_API_KEY")
'sk-...'  # 应该显示你的密钥
```

### 方法2：查看AI网关日志

启动服务后，查看日志输出：

```
✅ 已注册讯飞(Xunfei)提供商: base_url=... 默认模型=lite
AI服务商已注册: qwen (模型: qwen-plus)
AI服务商已注册: gemini (模型: gemini-2.5-flash-preview-09-2025)
```

### 方法3：通过API检查

```bash
# 调用AI网关状态API
curl http://localhost:10090/api/ai/gateway/status
```

---

## 📝 完整配置示例

```env
# ============================================
# AI服务配置
# ============================================

# 通义千问（推荐）
QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus

# Gemini（通过AiHubMix）
GEMINI_API_KEY=your-gemini-api-key
AIHUBMIX_BASE_URL=https://aihubmix.com/v1
GEMINI_MODEL=gemini-2.5-flash-preview-09-2025

# 科大讯飞
XUNFEI_API_KEY=your-xunfei-api-key
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1
XUNFEI_MODEL=lite

# OpenAI（可选）
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
```

---

## ✅ 总结

1. **配置文件**：`server/.env`
2. **读取方式**：`os.getenv()` 直接读取环境变量
3. **不通过**：`config.py`（仅作为类型定义）
4. **生效方式**：重启服务后生效
5. **优先级**：系统环境变量 > 根目录 .env > server/.env

---

## 📚 相关文档

- [AI配置统一说明](../docs/AI方案与集成/AI配置统一说明.md)
- [环境变量配置模板](./ENV_TEMPLATE.md)
- [极简版配置](./ENV_SIMPLE.md)

