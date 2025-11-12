# 端口配置快速指南

**审查人**: 叶维哲  
**更新时间**: 2025-11-07

---

## 🚀 快速开始

### 1️⃣ 端口分配

| 服务 | 端口 | 配置文件 | 环境变量 |
|------|------|---------|---------|
| **前端开发服务器** | 10013 | `electron/renderer/.env` | `VITE_PORT` |
| **后端主服务** | 9030 | `server/.env` | `BACKEND_PORT` |

---

## 📝 配置示例

### 前端配置 (`electron/renderer/.env`)

```env
# 前端开发端口
VITE_PORT=10013

# 后端服务地址
VITE_FASTAPI_URL=http://127.0.0.1:9030
```

### 后端配置 (`server/.env`)

```env
# 后端服务端口
BACKEND_PORT=9030

# 数据库配置
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=timao
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=timao_live
```

---

## 🔧 一键迁移

### 如果您的配置在根目录`.env`

运行自动迁移脚本:

```bash
# 自动分离配置到前后端
python scripts/初始化与迁移/migrate_env_config.py

# 验证配置是否正确
python scripts/检查与校验/validate_port_config.py
```

---

## ✅ 启动服务

### 后端

```bash
cd server
python app/main.py

# 输出: ✅ 服务已启动 http://0.0.0.0:9030
```

### 前端

```bash
cd electron/renderer
npm run dev

# 输出: ✅ 开发服务器已启动 http://127.0.0.1:10013
```

---

## 🧪 测试

### 验证配置

```bash
# 检查配置文件和端口
python scripts/检查与校验/validate_port_config.py
```

### 测试直播间

```bash
# 使用环境变量中的端口
python scripts/测试与验证/test_douyin_live.py
```

---

## 🛠️ 临时修改端口

### 一次性修改

```bash
# 后端
BACKEND_PORT=9031 python server/app/main.py

# 前端
VITE_PORT=10014 npm run dev
```

### 永久修改

编辑对应的`.env`文件即可。

---

## 📚 完整文档

详细信息请查看: [`docs/部署与运维指南/PORT_CONFIGURATION.md`](PORT_CONFIGURATION.md)

---

## 🚨 常见问题

**Q: 端口被占用怎么办？**

A: 修改`.env`文件中的端口号，或使用临时环境变量覆盖。

**Q: 如何查看当前使用的端口？**

A: 运行 `python scripts/检查与校验/validate_port_config.py`

**Q: 配置文件在哪里？**

A:
- 前端: `electron/renderer/.env`
- 后端: `server/.env`

---

## ✨ 设计原则

- ✅ **单一职责**: 前后端各管各的配置
- ✅ **避免硬编码**: 所有端口从环境变量读取
- ✅ **简单明了**: 配置文件就近放置
- ✅ **开箱即用**: 提供合理的默认值

**遵循**: 奥卡姆剃刀、KISS原则、单一职责原则

