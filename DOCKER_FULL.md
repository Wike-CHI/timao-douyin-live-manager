# 🐳 一键式前后端 Docker 部署

遵循 **奥卡姆剃刀** 与 **KISS 原则**：只保留必需步骤，一条命令拉起前后端。

---

## 0. 先决条件

- 已安装 Docker 24+ 与 `docker compose` 插件（或 Docker Desktop 最新版）。
- 仓库完整克隆到目标服务器。

---

## 1. 准备唯一一份 `.env`

```bash
cd server
cp env.production.template .env
```

编辑 `server/.env`，只改 6 个键：

| 键 | 说明 |
| --- | --- |
| `BACKEND_PORT` | 对外 API 端口（默认 11111） |
| `MYSQL_HOST` | MySQL 地址 |
| `MYSQL_USER` | MySQL 用户 |
| `MYSQL_PASSWORD` | MySQL 密码 |
| `MYSQL_DATABASE` | MySQL 库名 |
| `SECRET_KEY` | 64 字节随机串 |

> 其余键全部保留默认值，减少决策面。

---

## 2. 一键启动前后端

在项目根目录执行：

```bash
BACKEND_PORT=11111 FRONTEND_PORT=80 \
docker compose -f docker-compose.full.yml up -d --build
```

- `BACKEND_PORT`、`FRONTEND_PORT` 可按需改成本机空闲端口。
- 命令会：
  1. 构建后端镜像（内含 Python 依赖与语音模型下载逻辑）。
  2. 构建前端静态资源 + Nginx。
  3. 将 `server/.env` 注入后端容器，并挂载 `server/models|logs|records` 以持久化数据。

---

## 3. 验证

```bash
curl http://localhost:${BACKEND_PORT:-11111}/health
curl http://localhost:${FRONTEND_PORT:-80}/health
docker compose -f docker-compose.full.yml ps
```

通过即表示前后端均运行。

---

## 4. 日常操作

```bash
# 查看实时日志
docker compose -f docker-compose.full.yml logs -f backend
docker compose -f docker-compose.full.yml logs -f frontend

# 重启
docker compose -f docker-compose.full.yml restart

# 停止并清理容器（保留数据卷）
docker compose -f docker-compose.full.yml down
```

---

## 5. 常见定制（保持最小化）

- **修改端口**：仅调整上方启动命令的 `BACKEND_PORT/FRONTEND_PORT` 环境变量，以及 `server/.env` 中的 `BACKEND_PORT`，无需改 Compose 文件。
- **更新配置**：改 `server/.env` 后执行 `docker compose -f docker-compose.full.yml up -d`.
- **更新代码**：拉取最新代码后重复“一键启动”命令（会自动重建镜像）。

---

整体流程不再拆分脚本或额外服务，所有决定集中在一个 `.env` 和一条 Compose 命令里，尽量减少步骤与干扰项。*** End Patch
