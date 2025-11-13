# 🚀 环境配置快速上手

**解决启动错误 | 3分钟完成配置 | 遵循KISS原则**

---

## ❌ 遇到的问题

```
TypeError: run() got an unexpected keyword argument 'reload_exclude'
```

## ✅ 解决方案

已修复！现在只需3步完成配置。

---

## 📋 一键配置 (推荐)

### 运行配置脚本

```bash
# 从项目根目录运行
python scripts/初始化与迁移/setup_env.py
```

**输出示例**:
```
🚀 提猫直播助手 - 一键环境配置
============================================================

📝 将创建以下配置文件:
  1. 后端: server\.env
  2. 前端: electron\renderer\.env

✨ 配置内容 (遵循希克定律 - 只关注核心配置):

后端核心配置 (6项):
  1. ✅ BACKEND_PORT=9030
  2. ✅ DB_TYPE=mysql
  3. ✅ MYSQL_HOST=rm-bp1sqxf05yom2hwdhko.mysql.rds.aliyuncs.com
  4. ✅ MYSQL_USER=timao
  5. ✅ MYSQL_PASSWORD=Yw123456
  6. ✅ MYSQL_DATABASE=timao

前端核心配置 (3项):
  1. ✅ VITE_PORT=10013
  2. ✅ VITE_HOST=127.0.0.1
  3. ✅ VITE_FASTAPI_URL=http://127.0.0.1:9030

确认创建配置? (y/N): y

✅ 已创建 后端 配置: server\.env
✅ 已创建 前端 配置: electron\renderer\.env

✅ 配置完成!
```

---

## 🎯 核心配置总览

### 端口分配 (遵循单一职责)

| 服务 | 端口 | 配置文件 |
|------|------|---------|
| **后端服务** | 9030 | `server/.env` |
| **前端开发** | 10013 | `electron/renderer/.env` |

### 最小配置集 (遵循希克定律)

**后端** - 只需6项:
1. 端口: `BACKEND_PORT=9030`
2-6. 数据库: `DB_TYPE`, `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`

**前端** - 只需3项:
1. 端口: `VITE_PORT=10013`
2. 主机: `VITE_HOST=127.0.0.1`
3. 后端地址: `VITE_FASTAPI_URL=http://127.0.0.1:9030`

---

## ✅ 验证配置

```bash
# 验证配置是否正确
python scripts/检查与校验/validate_port_config.py
```

**成功输出**:
```
🔍 提猫直播助手 - 端口配置验证
============================================================

📋 检查 后端服务 配置
============================================================
✅ 配置文件存在: server\.env
✅ 端口配置正确: 9030
✅ 后端服务 端口 9030 可用

📋 检查 前端服务 配置
============================================================
✅ 配置文件存在: electron\renderer\.env
✅ 端口配置正确: 10013
✅ 前端服务 端口 10013 可用

✅ 所有验证通过!
```

---

## 🚀 启动服务

### 1. 启动后端

```bash
cd server
python app/main.py
```

**成功标志**:
```
INFO:     Uvicorn running on http://0.0.0.0:9030 (Press CTRL+C to quit)
✅ 服务已启动 http://0.0.0.0:9030
```

### 2. 启动前端 (新终端)

```bash
cd electron/renderer
npm run dev
```

**成功标志**:
```
VITE v4.x.x  ready in xxx ms

  ➜  Local:   http://127.0.0.1:10013/
  ➜  Network: use --host to expose
```

---

## 🔧 常见问题

### Q1: 端口被占用?

**解决**:
```bash
# 临时修改端口
BACKEND_PORT=9031 python app/main.py

# 或修改 .env 文件
BACKEND_PORT=9031
```

### Q2: 配置文件不存在?

**解决**:
```bash
# 再次运行配置脚本
python scripts/初始化与迁移/setup_env.py
```

### Q3: 数据库连接失败?

**检查**:
1. ✅ 数据库地址是否正确
2. ✅ 用户名密码是否正确
3. ✅ 数据库是否可访问

**查看配置**:
```bash
# Windows
notepad server\.env

# 检查这些配置
MYSQL_HOST=...
MYSQL_USER=...
MYSQL_PASSWORD=...
MYSQL_DATABASE=...
```

### Q4: 前端无法连接后端?

**检查顺序**:
1. ✅ 后端是否已启动 (http://127.0.0.1:9030)
2. ✅ 前端配置中的后端地址是否正确
3. ✅ CORS是否配置正确

---

## 📚 详细文档

- 📖 [完整配置指南](docs/部署与运维指南/ENV_CONFIGURATION_GUIDE.md)
- 📝 [端口配置文档](docs/部署与运维指南/PORT_CONFIGURATION.md)
- 🔧 [配置验证脚本](scripts/检查与校验/validate_port_config.py)

---

## ✅ 配置检查清单

- [ ] 运行 `python scripts/初始化与迁移/setup_env.py`
- [ ] 验证 `python scripts/检查与校验/validate_port_config.py`
- [ ] 启动后端 `cd server && python app/main.py`
- [ ] 启动前端 `cd electron/renderer && npm run dev`
- [ ] 访问 http://127.0.0.1:10013

**全部完成即可开始使用!** 🎉

---

## 💡 设计原则

本配置方案遵循:
- ✅ **KISS原则**: 配置简单,只包含必需项
- ✅ **单一职责原则**: 前后端配置各自独立
- ✅ **希克定律**: 只关注最重要的9个配置项
- ✅ **帕累托原则**: 20%的配置支撑80%的功能

