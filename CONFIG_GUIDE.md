# 📝 配置文件管理指南

## 🎯 原则：奥卡姆剃刀（如无必要勿增实体）

**简化配置，减少混乱，只保留必要的配置文件。**

## 📂 配置文件结构

```
timao-douyin-live-manager/
├── server/
│   ├── .env              ← 后端配置（敏感信息，不提交到Git）
│   └── .env.example      ← 后端配置模板（提交到Git）
│
└── electron/renderer/
    ├── .env              ← 前端开发环境（敏感信息，不提交到Git）
    ├── .env.production   ← 前端生产环境（可提交到Git）
    └── .env.example      ← 前端配置模板（提交到Git）
```

## ✅ 配置文件说明

### 1. 后端配置 (`server/.env`)

**位置**：`/www/wwwroot/wwwroot/timao-douyin-live-manager/server/.env`

**用途**：后端所有配置，包括：
- 数据库配置（MySQL/RDS）
- JWT 密钥配置
- AI 服务配置（通义千问、Gemini、讯飞等）
- 讯飞 ASR 配置
- Redis 配置

**加载方式**：`server/config.py` 自动加载

**重要**：
- ✅ 包含所有敏感信息（密钥、密码）
- ✅ 权限设置为 `600`（只有所有者可读写）
- ❌ **不要提交到 Git**

### 2. 前端开发环境 (`electron/renderer/.env`)

**位置**：`/www/wwwroot/wwwroot/timao-douyin-live-manager/electron/renderer/.env`

**用途**：前端开发环境配置

**内容**：
```env
# 开发环境配置 - 连接到本地后端

# API基础URL（本地开发）
VITE_FASTAPI_URL=http://127.0.0.1:11111
VITE_STREAMCAP_URL=http://127.0.0.1:11111
VITE_DOUYIN_URL=http://127.0.0.1:11111

# 环境标识
VITE_APP_ENV=development
```

**重要**：
- ✅ 用于本地开发
- ❌ **不要提交到 Git**

### 3. 前端生产环境 (`electron/renderer/.env.production`)

**位置**：`/www/wwwroot/wwwroot/timao-douyin-live-manager/electron/renderer/.env.production`

**用途**：前端生产环境配置

**内容**：
```env
# 生产环境配置 - 连接到公网后端

# API基础URL（公网地址）
VITE_FASTAPI_URL=http://129.211.218.135
VITE_STREAMCAP_URL=http://129.211.218.135
VITE_DOUYIN_URL=http://129.211.218.135

# 环境标识
VITE_APP_ENV=production
```

**重要**：
- ✅ 用于生产部署
- ✅ **可以提交到 Git**（不包含敏感信息）

## 🔧 配置文件使用

### 后端开发

1. **首次配置**：
```bash
cd server
cp .env.example .env
vi .env  # 编辑配置
```

2. **修改配置后重启**：
```bash
pm2 restart timao-backend
```

### 前端开发

1. **首次配置**：
```bash
cd electron/renderer
cp .env.example .env
vi .env  # 编辑配置
```

2. **开发环境**：
```bash
npm run dev  # 使用 .env
```

3. **生产环境**：
```bash
npm run build  # 使用 .env.production
```

## 🔐 安全配置

### JWT 密钥生成

**推荐方式**：使用 Python 生成
```bash
# 生成 SECRET_KEY（64字符以上）
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# 生成 ENCRYPTION_KEY（32字节）
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 文件权限

**后端配置文件必须设置为 600**：
```bash
chmod 600 server/.env
```

### Git 忽略

**.gitignore 已配置**：
```gitignore
# 环境变量文件（包含敏感信息，不提交）
.env
.env.local
.env.*.local
server/.env
server/.env.local
electron/renderer/.env
electron/renderer/.env.local

# 保留 .env.example 和 .env.production 作为模板
!.env.example
!.env.production
!electron/renderer/.env.production
```

## 📋 配置项参考

### 后端必需配置

```env
# 服务端口
BACKEND_PORT=11111

# 数据库配置（必需）
MYSQL_HOST=your-mysql-host
MYSQL_PORT=3306
MYSQL_USER=your-mysql-user
MYSQL_PASSWORD=your-mysql-password
MYSQL_DATABASE=timao

# JWT 密钥（必需，生产环境必须修改）
SECRET_KEY=your-secret-key-64-chars-minimum
ENCRYPTION_KEY=your-encryption-key-32-bytes

# 讯飞 ASR 配置（如果使用语音转写）
IFLYTEK_APP_ID=your-app-id
IFLYTEK_API_KEY=your-api-key
IFLYTEK_API_SECRET=your-api-secret
USE_IFLYTEK_ASR=1

# AI 配置（根据需要配置）
QWEN_API_KEY=your-qwen-api-key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-max

GEMINI_API_KEY=your-gemini-api-key
AIHUBMIX_BASE_URL=https://aihubmix.com/v1
GEMINI_MODEL=gemini-2.0-flash-exp

XUNFEI_API_KEY=your-xunfei-api-key
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1
XUNFEI_MODEL=lite
```

## ⚠️ 常见问题

### Q1: 配置修改后不生效？

**A**: 重启后端服务
```bash
pm2 restart timao-backend
```

### Q2: 前端连接不到后端？

**A**: 检查环境变量配置：
- 开发环境：使用 `127.0.0.1:11111`
- 生产环境：使用正确的公网IP

### Q3: JWT token 失效？

**A**: 修改 `SECRET_KEY` 后，所有旧 token 失效，用户需要重新登录

### Q4: 文件权限问题？

**A**: 确保 `.env` 文件权限为 `600`
```bash
chmod 600 server/.env
```

## 🎉 配置检查清单

部署前检查：

- [ ] `server/.env` 存在且权限为 600
- [ ] `SECRET_KEY` 和 `ENCRYPTION_KEY` 已修改（不使用示例值）
- [ ] 数据库配置正确
- [ ] 讯飞 ASR 配置正确（如果使用）
- [ ] AI 密钥配置正确（如果使用）
- [ ] 前端 `.env.production` 配置正确
- [ ] `.gitignore` 包含 `.env` 文件
- [ ] 敏感配置文件未提交到 Git

## 📚 相关文档

- [后端配置管理](server/config.py)
- [前端构建配置](electron/renderer/vite.config.ts)
- [环境变量模板](server/.env.example)

---

**最后更新**: 2025-11-13
**维护者**: 叶维哲

