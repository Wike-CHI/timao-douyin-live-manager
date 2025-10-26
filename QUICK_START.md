# 提猫直播助手 - 快速开始指南

> 5分钟快速上手提猫直播助手

## 📋 前置要求

- ✅ Node.js ≥ 16
- ✅ Python ≥ 3.9
- ✅ **MySQL ≥5.7 / MariaDB ≥10.3**
- ✅ 通义千问 API Key（或其他 AI 服务商）

---

## 🚀 快速启动（3 步）

### 步骤 0: 初始化 MySQL 数据库

#### Windows 用户：
```bash
# 运行自动化脚本
setup-dev-mysql.bat
```

#### macOS/Linux 用户：
```bash
# 运行自动化脚本
bash setup-dev-mysql.sh
```

#### 手动配置：
```bash
# 1. 创建数据库
mysql -u root -p
```

```sql
CREATE DATABASE timao_live CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'timao'@'localhost' IDENTIFIED BY 'timao123456';
GRANT ALL PRIVILEGES ON timao_live.* TO 'timao'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

```bash
# 2. 配置 .env 文件
cp .env.example .env

# 3. 安装 MySQL 驱动
pip install pymysql cryptography
```

> **提示**：如果没有安装 MySQL，可以使用 Docker：
> ```bash
> docker run -d --name timao-mysql \
>   -e MYSQL_ROOT_PASSWORD=root \
>   -e MYSQL_DATABASE=timao_live \
>   -e MYSQL_USER=timao \
>   -e MYSQL_PASSWORD=timao123456 \
>   -p 3306:3306 mysql:8.0
> ```

---

### 步骤 1: 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.all.txt

# 安装 Node 依赖
npm ci
```

### 步骤 2: 配置 AI 服务

编辑 `.env` 文件：

```bash
# 必填：AI 服务商配置
AI_SERVICE=qwen
AI_API_KEY=sk-your-qwen-api-key-here
AI_MODEL=qwen-plus

# 必填：MySQL 数据库配置（已预设默认值）
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=timao
MYSQL_PASSWORD=timao123456
MYSQL_DATABASE=timao_live

# 可选：API 地址（使用默认值可不填）
AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

**获取 API Key**：
- 通义千问：https://dashscope.console.aliyun.com/apiKey
- OpenAI：https://platform.openai.com/api-keys
- DeepSeek：https://platform.deepseek.com/api_keys

### 步骤 3: 启动应用

```bash
npm run dev
```

应用会自动：
1. 启动前端界面（Vite）- 端口 30013
2. 启动后端服务（FastAPI）- 端口 10090
3. 打开 Electron 桌面窗口

---

## 🎯 核心功能使用

### 1️⃣ 直播弹幕抓取

1. 点击"直播设置"
2. 输入抖音直播间 URL
3. 点击"开始抓取"
4. 实时查看弹幕流

### 2️⃣ 语音转写

1. 点击"语音转写"
2. 选择音频输入设备
3. 点击"开始识别"
4. 实时显示字幕

### 3️⃣ AI 智能分析

1. 抓取弹幕或语音后，自动触发 AI 分析
2. 查看：
   - 热词洞察
   - 情绪分析
   - 互动建议
   - 实时话术

### 4️⃣ 直播复盘

1. 直播结束后，点击"生成复盘"
2. 自动生成：
   - 弹幕记录 (`comments.jsonl`)
   - 语音文本 (`transcript.txt`)
   - 分析报告 (`report.html`)

---

## 🔧 AI 服务商管理

### Web 管理界面

访问：http://localhost:10090/static/ai_gateway_manager.html

**功能**：
- 🔄 一键切换服务商
- ➕ 添加新服务商
- 🔑 更新 API Key
- ❌ 删除服务商
- 🧪 测试 AI 调用

### 支持的服务商

| 服务商 | 推荐模型 | 成本 |
|--------|---------|------|
| **通义千问** | qwen-plus | ¥0.4/百万tokens（输入） |
| DeepSeek | deepseek-chat | ¥0.1/百万tokens |
| 豆包 | doubao-pro | ¥0.8/百万tokens |
| ChatGLM | glm-4-flash | ¥0/百万tokens（限时） |
| OpenAI | gpt-3.5-turbo | $0.5/百万tokens |

### 切换服务商（3 种方式）

#### 方式 1: Web 界面
1. 打开管理界面
2. 选择服务商和模型
3. 点击"切换"

#### 方式 2: API 调用
```bash
curl -X POST http://localhost:10090/api/ai_gateway/switch \
  -H "Content-Type: application/json" \
  -d '{"provider": "deepseek", "model": "deepseek-chat"}'
```

#### 方式 3: 修改 .env
```bash
AI_SERVICE=deepseek
AI_MODEL=deepseek-chat
```
然后重启应用。

---

## 📊 成本监控

访问：http://localhost:10090/static/ai_usage_monitor.html

**查看**：
- 今日/本周/本月调用统计
- 各模型成本分布
- 调用成功率
- 性能指标

---

## ❓ 常见问题

### Q1: 启动后提示端口被占用？

**A**: 检查端口占用并释放：

```bash
# Windows
netstat -ano | findstr "10090"
taskkill /PID <进程ID> /F

# macOS/Linux
lsof -ti:10090 | xargs kill -9
```

### Q2: AI 调用失败？

**A**: 检查配置：

```bash
# 查看当前配置
curl http://localhost:10090/api/ai_gateway/status

# 测试 API Key
curl -X POST http://localhost:10090/api/ai_gateway/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "你好"}]}'
```

### Q3: 语音转写不工作？

**A**: 首次使用需要下载模型：

```bash
python tools/download_sensevoice.py
python tools/download_vad_model.py
```

### Q4: 如何添加新的 AI 服务商？

**A**: 两种方式：

**环境变量**：
```bash
# .env
DEEPSEEK_API_KEY=sk-your-key
```

**Web 界面**：
1. 打开管理界面
2. 填写服务商信息
3. 点击"注册"

### Q5: 成本太高怎么办？

**A**: 切换到更便宜的模型：

```bash
# 切换到 qwen-turbo（更便宜）
curl -X POST http://localhost:10090/api/ai_gateway/switch \
  -d '{"provider": "qwen", "model": "qwen-turbo"}'
```

**成本对比**：
- qwen-max: ¥4.0/百万tokens（高质量）
- qwen-plus: ¥0.4/百万tokens（推荐）⭐
- qwen-turbo: ¥0.2/百万tokens（经济）

---

## 🔐 安全建议

### 1. 保护 API Key

```bash
# .gitignore 中已包含
.env
.env.*
```

### 2. 定期轮换密钥

```bash
# 更新 API Key
curl -X PUT http://localhost:10090/api/ai_gateway/provider/api-key \
  -H "Content-Type: application/json" \
  -d '{"provider": "qwen", "api_key": "sk-new-key"}'
```

### 3. 监控异常调用

访问监控页面，检查：
- 调用量异常增长
- 成本突然上升
- 失败率过高

---

## 📚 进阶使用

### 1. 自定义提示词

编辑 `server/ai/prompts/` 中的提示词模板。

### 2. 配置多个服务商

```bash
# .env
AI_SERVICE=qwen
AI_API_KEY=sk-qwen-key

DEEPSEEK_API_KEY=sk-deepseek-key
OPENAI_API_KEY=sk-openai-key
```

启动后自动注册所有服务商，可随时切换。

### 3. 离线部署

```bash
# 关闭 AI 功能
AI_SERVICE=offline
```

或下载本地模型（需要 GPU）。

### 4. Docker 部署

```bash
docker-compose up -d
```

访问 http://localhost:30013

---

## 🛠️ 开发调试

### 查看日志

```bash
# FastAPI 日志
tail -f logs/uvicorn.log

# Electron 日志
# 在应用菜单：视图 -> 开发者工具 -> Console
```

### API 文档

访问：http://localhost:10090/docs

### 测试接口

```bash
# 健康检查
curl http://localhost:10090/api/health

# AI 状态
curl http://localhost:10090/api/ai_gateway/status

# 语音服务
curl http://localhost:10090/api/live_audio/health
```

---

## 📞 获取帮助

- 📖 完整文档：`README.md`
- 🔧 AI 网关：`docs/AI_GATEWAY_SIMPLE.md`
- 📊 成本监控：`docs/MONITORING_GUIDE.md`
- 🔑 API 管理：`docs/AI_GATEWAY_API_KEY_MANAGEMENT.md`

---

## ✅ 检查清单

启动前确认：

- [ ] Python 依赖已安装
- [ ] Node 依赖已安装
- [ ] `.env` 文件已配置
- [ ] AI API Key 有效
- [ ] 端口 10090 和 30013 未被占用
- [ ] （可选）语音模型已下载

一切就绪！运行 `npm run dev` 开始使用 🚀

---

**版本**: v1.0.0  
**更新**: 2025-10-26
