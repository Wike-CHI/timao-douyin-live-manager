# 后端环境变量配置模板

**请复制以下内容创建 `server/.env` 文件**

> ⚠️ **推荐使用极简版配置**：查看 [ENV_SIMPLE.md](./ENV_SIMPLE.md) 或 `.env.minimal` 文件
> 
> 本文件为完整版配置模板，包含所有可配置项（包括有默认值的项）

```env
# ============================================
# 提猫直播助手 - 后端服务环境变量（完整版）
# ============================================
# 审查人: 叶维哲
# 遵循原则: 奥卡姆剃刀、KISS、单一职责
#
# ⚠️ 注意：大多数配置都有默认值，不需要全部设置
# 推荐使用极简版：只配置必需项（8项）
# 查看 ENV_SIMPLE.md 了解哪些是必需的

# ------------------------------------------
# 🚀 服务端口配置 (必需)
# ------------------------------------------
BACKEND_PORT=10090

# ------------------------------------------
# 🗄️ 数据库配置 (必需 - 5项)
# ------------------------------------------
DB_TYPE=mysql
MYSQL_HOST=rm-bp1sqxf05yom2hwdhko.mysql.rds.aliyuncs.com
MYSQL_PORT=3306
MYSQL_USER=timao
MYSQL_PASSWORD=Yw123456
MYSQL_DATABASE=timao

# ------------------------------------------
# 🔐 安全配置 (生产环境必须修改！)
# ------------------------------------------
# JWT密钥 (建议64位随机字符串)
SECRET_KEY=timao-secret-key-change-in-production-must-be-64-chars-minimum

# 数据加密密钥 (必须32字符)
ENCRYPTION_KEY=timao-encryption-key-32chars

# ------------------------------------------
# 🤖 AI服务配置 (可选)
# ------------------------------------------
# Google Gemini (推荐)
# GEMINI_API_KEY=

# 默认AI服务商 (有默认值，可不配置)
# DEFAULT_AI_PROVIDER=gemini

# OpenAI (可选)
# OPENAI_API_KEY=
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-3.5-turbo

# ------------------------------------------
# 📝 日志配置 (有默认值，可不配置)
# ------------------------------------------
# LOG_LEVEL=INFO
# LOG_DIR=logs

# ------------------------------------------
# 🌐 CORS配置 (有默认值，可不配置)
# ------------------------------------------
# CORS_ORIGINS=*

# ------------------------------------------
# ⚙️ 应用配置 (有默认值，可不配置)
# ------------------------------------------
# DEBUG=false
# TIMEZONE=Asia/Shanghai

# ------------------------------------------
# 📦 功能开关 (有默认值，可不配置)
# ------------------------------------------
# WEBSOCKET_ENABLED=true
```

## 🚀 快速开始

### 1. 创建配置文件

```bash
# Windows PowerShell
cd server
Copy-Item ENV_TEMPLATE.md .env
# 然后编辑 .env 文件

# 或者手动创建
New-Item -Path . -Name ".env" -ItemType "file"
# 复制上面的内容到 .env
```

### 2. 修改必要配置

**必须修改的配置** (遵循希克定律 - 只关注最重要的):

1. ✅ `BACKEND_PORT=11111` (已设置)
2. ✅ `DB_TYPE=mysql` (已设置)
3. ✅ `MYSQL_HOST=...` (使用您的数据库地址)
4. ✅ `MYSQL_USER=timao` (已设置)
5. ✅ `MYSQL_PASSWORD=Yw123456` (已设置)
6. ✅ `MYSQL_DATABASE=timao` (已设置)

**可选配置** (稍后配置):

- `GEMINI_API_KEY` (AI功能需要)
- `SECRET_KEY` (生产环境必须改)
- `ENCRYPTION_KEY` (生产环境必须改)

### 3. 验证配置

```bash
python scripts/检查与校验/validate_port_config.py
```

### 4. 启动服务

```bash
python app/main.py
```

应该看到:
```
✅ 服务已启动 http://0.0.0.0:11111
```

---

## 📋 配置说明

### 端口配置 (BACKEND_PORT)

- **默认**: 11111
- **原因**: 与前端端口分离，避免冲突
- **修改**: 如果11111被占用，可改为11112、11113等

### 数据库配置

当前使用您的MySQL配置:
- **主机**: rm-bp1sqxf05yom2hwdhko.mysql.rds.aliyuncs.com
- **端口**: 3306
- **数据库**: timao
- **用户**: timao
- **密码**: Yw123456

### AI配置 (可选)

如需使用AI功能，设置:
```env
GEMINI_API_KEY=your-api-key-here
```

---

## 🔧 常见问题

### Q: 为什么服务启动失败?

**A**: 检查以下几点(按优先级):

1. ✅ `.env` 文件是否存在于 `server/` 目录
2. ✅ 数据库连接是否正常
3. ✅ 端口11111是否被占用

### Q: 如何检查配置?

```bash
# 验证配置文件
python scripts/检查与校验/validate_port_config.py

# 测试数据库连接
python -c "from server.app.database import engine; engine.connect()"
```

### Q: 端口被占用怎么办?

```bash
# 临时使用其他端口
BACKEND_PORT=11112 python app/main.py

# 或修改 .env 文件
BACKEND_PORT=11112
```

---

## ✅ 遵循的设计原则

1. **奥卡姆剃刀原理**: 如无必要，勿增实体 - 只配置必需项
2. **KISS原则**: 配置简单明了
3. **单一职责原则**: 后端配置只在 `server/.env`
4. **80/20法则**: 只配置最重要的8个选项

**必需的8个配置**:
1. BACKEND_PORT
2. DB_TYPE
3. MYSQL_HOST
4. MYSQL_PORT
5. MYSQL_USER
6. MYSQL_PASSWORD
7. MYSQL_DATABASE
8. SECRET_KEY / ENCRYPTION_KEY（生产环境）

**推荐使用极简版配置**：查看 [ENV_SIMPLE.md](./ENV_SIMPLE.md)

