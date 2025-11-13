# 环境变量配置简化说明

## 📋 变更总结

根据**奥卡姆剃刀原理**，已简化后端环境变量配置。

---

## ✅ 简化前 vs 简化后

### 简化前（完整版）
- 配置项：**20+ 项**
- 包含：必需项 + 有默认值的项 + 可选项
- 问题：配置冗余，容易混淆哪些是必需的

### 简化后（极简版）
- 配置项：**8 项**（必需）
- 包含：只配置真正必需的项
- 优势：清晰、简洁、易维护

---

## 🎯 必需配置（8项）

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

## ❌ 移除的配置项（有默认值）

以下配置**已移除**，因为代码中已有默认值：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `LOG_DIR` | `logs` | 日志目录 |
| `CORS_ORIGINS` | `["*"]` | CORS 允许的源 |
| `DEBUG` | `False` | 调试模式 |
| `TIMEZONE` | `Asia/Shanghai` | 时区 |
| `WEBSOCKET_ENABLED` | `True` | WebSocket 开关 |
| `DEFAULT_AI_PROVIDER` | 代码默认值 | 默认 AI 服务商 |

**原则：如果代码有默认值，就不在配置文件中重复设置。**

---

## 📁 配置文件说明

### 1. `.env.minimal`（推荐）
- **极简版配置模板**
- 只包含 8 个必需项
- 推荐用于生产环境

### 2. `env.production.template`
- **生产环境模板**（已简化）
- 只包含必需项
- 使用方法：`cp env.production.template .env`

### 3. `ENV_SIMPLE.md`
- **极简版配置文档**
- 说明哪些是必需的，哪些有默认值

### 4. `ENV_TEMPLATE.md`
- **完整版配置文档**（保留）
- 包含所有可配置项
- 标注了哪些有默认值

---

## 🚀 快速开始

### 使用极简版配置

```bash
cd server

# 方法1：使用极简模板
cp .env.minimal .env

# 方法2：使用生产模板
cp env.production.template .env

# 然后只修改必需项
vim .env
```

### 修改必需项

只需修改：
- `BACKEND_PORT`（如果端口被占用）
- `MYSQL_HOST`（如果数据库地址不同）
- `MYSQL_USER` / `MYSQL_PASSWORD`（如果数据库账号不同）
- `SECRET_KEY` / `ENCRYPTION_KEY`（生产环境必须修改）

---

## 🔧 如何覆盖默认值？

如果需要修改默认值，在 `.env` 文件中添加对应的环境变量即可：

```env
# 例如：修改日志级别
LOG_LEVEL=DEBUG

# 例如：修改 CORS 配置
CORS_ORIGINS=http://localhost:3000,http://example.com
```

---

## ✅ 遵循的原则

1. **奥卡姆剃刀原理** - 如无必要，勿增实体
2. **KISS原则** - 保持简单
3. **80/20法则** - 只配置最重要的 8 项
4. **DRY原则** - 不在配置文件中重复代码默认值

---

## 📝 审查信息

- **审查人**: 叶维哲
- **变更日期**: 2025-01-XX
- **变更原因**: 根据奥卡姆剃刀原理简化配置

