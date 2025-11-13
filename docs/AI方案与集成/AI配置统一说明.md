# AI配置统一说明

**审查人**: 叶维哲  
**创建时间**: 2025-11-09  
**修改时间**: 2025-11-09

---

## 📋 问题背景

原配置系统混乱：
- `config.py` 定义 `AIConfig`（但默认值都是空）
- `.env` 文件存储实际密钥
- `ai_gateway.py` 直接用 `os.getenv()` 读取，**完全绕过 config.py**

**结果**：两套系统并存，容易混淆，维护困难。

---

## ✅ 解决方案：方案1（统一到.env）

### 核心原则

**所有AI配置统一从 `.env` 环境变量读取**

- ✅ `ai_gateway.py` 直接读环境变量（保持不变）
- ✅ `config.py` 的 `AIConfig` 仅作为**类型定义和文档参考**
- ✅ `.env` 文件是**唯一的配置入口**

---

## 🔧 具体改动

### 1. `config.py` - AIConfig 添加说明

```python
@dataclass
class AIConfig:
    """
    AI配置
    
    ⚠️ 注意：所有AI服务密钥和配置均从 .env 文件读取，不在此处配置
    
    实际生效的环境变量：
    - QWEN_API_KEY, QWEN_BASE_URL, QWEN_MODEL
    - OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
    - XUNFEI_API_KEY, XUNFEI_BASE_URL, XUNFEI_MODEL
    - 更多配置参考：server/.env 文件
    
    ai_gateway.py 会直接读取环境变量，config.py 不参与AI配置管理。
    """
    # ... 字段仅用于类型定义，实际不使用
```

### 2. 禁用 AI 配置验证

```python
def validate_config(self):
    # ⚠️ AI配置验证已禁用：所有AI密钥从 .env 环境变量读取
    # ai_gateway.py 直接读取环境变量，不依赖 config.py 的 AIConfig
    pass
```

### 3. 更新示例 .env 文件

新增完整的AI配置示例（见 `config.py` 的 `create_sample_env()` 方法）：

```env
# ==================== AI配置（统一配置入口）====================
# --- 通义千问（阿里云）---
QWEN_API_KEY=your-qwen-api-key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-max

# --- 科大讯飞星火 ---
XUNFEI_API_KEY=your-xunfei-api-key
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1
XUNFEI_MODEL=lite

# ... 更多服务商
```

---

## 📍 配置文件位置

### 实际使用的配置

```
server/.env              ← 所有AI密钥（生产环境，不提交Git）
.env                     ← 根目录配置（可覆盖server/.env）
```

### 示例和文档

```
.env.example             ← 示例配置（可提交Git）
server/config.py         ← 类型定义和默认值
server/ai/ai_gateway.py  ← 实际读取环境变量的地方
```

---

## 🎯 使用指南

### 1️⃣ 开发者配置

复制示例文件并修改：

```bash
cp .env.example server/.env
nano server/.env  # 填入真实API密钥
```

### 2️⃣ 环境变量读取顺序

```python
# ai_gateway.py 读取顺序（Python dotenv）
1. 系统环境变量（最高优先级）
2. 根目录 .env 文件
3. server/.env 文件（如果 load_dotenv 调用时指定）
```

### 3️⃣ 功能级模型配置（可选）

```env
# 不同功能可以使用不同模型
AI_FUNCTION_STYLE_PROFILE_MODEL=qwen-max       # 风格画像
AI_FUNCTION_SCRIPT_GENERATION_MODEL=qwen-max   # 话术生成
AI_FUNCTION_LIVE_ANALYSIS_MODEL=lite           # 直播分析（免费）
```

---

## ⚠️ 注意事项

### 1. config.py 不再管理 AI 密钥

- `config.ai.qwen_api_key` 等字段**不再使用**
- 不要尝试通过 `config_manager.update_config()` 修改AI配置
- AI配置只能通过修改 `.env` 文件

### 2. 重启服务生效

修改 `.env` 文件后需要重启后端服务：

```bash
systemctl restart talkingcat-backend
```

### 3. 密钥安全

- ✅ `.env` 文件已加入 `.gitignore`
- ✅ 使用 `.env.example` 作为模板（不含真实密钥）
- ⚠️ 不要将 `.env` 提交到 Git

---

## 🧪 验证配置

### 检查环境变量是否加载

```bash
# 进入Python环境
python
>>> import os
>>> os.getenv("QWEN_API_KEY")
'sk-...'  # 应该显示你的密钥
```

### 检查AI服务是否可用

```bash
# 查看后端日志
tail -f logs/backend.log | grep -i "ai"
```

---

## 📊 对比总结

| 项目 | 改动前 | 改动后 |
|------|--------|--------|
| **AI密钥存储** | config.py + .env（混乱） | 仅 .env（统一） |
| **AI配置读取** | config_manager + os.getenv（两套） | 仅 os.getenv（单一） |
| **配置验证** | 检查 config.ai 字段（无效） | 已禁用（不检查） |
| **示例文件** | 不完整 | 完整且清晰 |

---

## ✅ 优势

1. **简单清晰**：只有一处配置（.env）
2. **符合标准**：遵循 12-Factor App 原则
3. **安全性高**：密钥不进代码和配置文件
4. **云部署友好**：环境变量是云平台标准
5. **维护容易**：只需管理 .env 文件

---

## 🔄 后续优化建议

### 可选：添加配置检查脚本

```python
# scripts/check_ai_config.py
import os
from dotenv import load_dotenv

load_dotenv("server/.env")

required_keys = ["QWEN_API_KEY", "XUNFEI_API_KEY"]
for key in required_keys:
    value = os.getenv(key)
    if value:
        print(f"✅ {key}: {'*' * 8}{value[-4:]}")
    else:
        print(f"❌ {key}: 未设置")
```

### 可选：Web界面配置管理

如果需要Web界面管理AI配置，可以开发一个管理页面，直接读写 `.env` 文件。

---

**结论**：配置系统已统一，所有AI配置从 `.env` 读取，简单清晰！🎉

