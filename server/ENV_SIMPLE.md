# 后端环境变量配置 - 极简版

**遵循奥卡姆剃刀原理：如无必要，勿增实体**

## 🎯 核心原则

只配置**真正必需**的项，其他使用代码默认值。

---

## ✅ 必需配置（8项）

```env
# 1. 服务端口
BACKEND_PORT=10090

# 2-6. 数据库配置（5项）
DB_TYPE=mysql
MYSQL_HOST=rm-bp1sqxf05yom2hwdhko.mysql.rds.aliyuncs.com
MYSQL_PORT=3306
MYSQL_USER=timao
MYSQL_PASSWORD=Yw123456
MYSQL_DATABASE=timao

# 7-8. 安全配置（生产环境必须修改）
SECRET_KEY=timao-secret-key-change-in-production-must-be-64-chars-minimum
ENCRYPTION_KEY=timao-encryption-key-32chars
```

---

## ❌ 不需要配置的项（有默认值）

以下配置**不需要**在 `.env` 中设置，代码已有默认值：

- `LOG_LEVEL` → 默认 `INFO`
- `LOG_DIR` → 默认 `logs`
- `CORS_ORIGINS` → 默认 `["*"]`
- `DEBUG` → 默认 `False`
- `TIMEZONE` → 默认 `Asia/Shanghai`
- `WEBSOCKET_ENABLED` → 默认 `True`
- `DEFAULT_AI_PROVIDER` → 默认值在代码中

**原则：如果代码有默认值，就不要在配置文件中重复设置。**

---

## 📝 可选配置（需要时再添加）

```env
# AI服务（需要AI功能时配置）
GEMINI_API_KEY=your-api-key-here
```

---

## 🚀 快速开始

### 1. 创建配置文件

```bash
cd server
cp .env.minimal .env
# 或
cp env.production.template .env
```

### 2. 修改必需项

只需修改：
- `BACKEND_PORT`（如果端口被占用）
- `MYSQL_HOST`（如果数据库地址不同）
- `MYSQL_USER` / `MYSQL_PASSWORD`（如果数据库账号不同）
- `SECRET_KEY` / `ENCRYPTION_KEY`（生产环境必须修改）

### 3. 启动服务

```bash
python app/main.py
```

---

## 📋 配置说明

### 为什么只配置8项？

根据**奥卡姆剃刀原理**和**80/20法则**：

1. **服务端口** - 必需，无默认值
2. **数据库配置** - 必需，无默认值（5项）
3. **安全密钥** - 必需，生产环境必须修改（2项）

其他配置都有合理的默认值，不需要重复配置。

### 默认值在哪里？

查看 `server/config.py` 中的 `ServerConfig`、`DatabaseConfig` 等类的默认值定义。

---

## 🔧 常见问题

### Q: 为什么移除了 LOG_LEVEL 等配置？

**A**: 这些配置在代码中已有默认值，遵循奥卡姆剃刀原理，不需要重复配置。如果确实需要修改，再添加到 `.env` 中。

### Q: 如何查看所有可配置项？

**A**: 查看 `server/config.py` 中的配置类定义，或查看 `ENV_TEMPLATE.md`（完整版）。

### Q: 需要修改默认值怎么办？

**A**: 在 `.env` 文件中添加对应的环境变量即可覆盖默认值。

---

## ✅ 遵循的设计原则

1. **奥卡姆剃刀原理** - 如无必要，勿增实体
2. **KISS原则** - 保持简单
3. **80/20法则** - 只配置最重要的8项

**记住：最简单的配置就是最好的配置。**

