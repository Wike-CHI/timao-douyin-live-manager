# 🔧 Docker 部署故障排查

## VS Code YAML Schema 警告

### 问题描述

VS Code 显示警告：
```
Unable to load schema from 'https://raw.githubusercontent.com/compose-spec/compose-go/master/schema/compose-spec.json'
```

### 原因

这是 VS Code YAML 扩展的网络问题，**不是代码错误**。扩展尝试从 GitHub 加载 Docker Compose 的 JSON Schema 进行验证，但网络请求失败。

### 解决方案

#### 方案1：忽略警告（推荐）

**这是 VS Code 扩展的问题，不影响 Docker Compose 的实际运行。**

`docker-compose.yml` 文件本身是正确的，可以正常使用：

```bash
docker-compose up -d  # 正常工作
```

#### 方案2：配置 VS Code 使用正确的 Schema URL

已在 `.vscode/settings.json` 中配置正确的 Schema URL。

#### 方案3：禁用 Schema 验证

如果警告很烦人，可以在 VS Code 设置中禁用：

1. 打开设置（`Ctrl+,`）
2. 搜索 `yaml.validate`
3. 取消勾选 "YAML: Validate"

或在 `settings.json` 中添加：

```json
{
  "yaml.validate": false
}
```

#### 方案4：使用本地 Schema

如果经常遇到网络问题，可以下载 Schema 到本地：

```bash
# 下载 Schema
curl -o docker-compose.schema.json https://raw.githubusercontent.com/compose-spec/compose-spec/master/schema/compose-spec.json

# 在 .vscode/settings.json 中配置
{
  "yaml.schemas": {
    "./docker-compose.schema.json": ["docker-compose.yml", "docker-compose.*.yml"]
  }
}
```

---

## 其他常见问题

### 问题1：Docker Compose 版本不匹配

**错误**：`version '3.8' is not supported`

**解决**：更新 Docker Compose 版本

```bash
# 检查版本
docker-compose --version

# 更新（Linux）
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 问题2：环境变量未加载

**错误**：`${BACKEND_PORT:-11111}` 未展开

**解决**：确保 `.env` 文件存在且格式正确

```bash
# 检查 .env 文件
cat .env | grep BACKEND_PORT

# 手动设置环境变量
export BACKEND_PORT=11111
docker-compose up -d
```

### 问题3：端口被占用

**错误**：`Bind for 0.0.0.0:11111 failed: port is already allocated`

**解决**：修改端口或停止占用端口的进程

```bash
# 修改 .env 中的端口
BACKEND_PORT=11112

# 或查找并停止占用端口的进程
# Linux/macOS
lsof -i :11111
kill -9 <PID>

# Windows
netstat -ano | findstr :11111
taskkill /PID <PID> /F
```

---

## ✅ 验证 Docker Compose 文件

即使 VS Code 显示警告，文件本身是正确的。验证方法：

```bash
# 验证语法（需要 docker-compose）
docker-compose config

# 或使用 docker compose（新版本）
docker compose config
```

如果命令成功执行，说明文件格式正确。

---

## 📝 总结

**VS Code 的 YAML Schema 警告不影响 Docker Compose 的实际运行。**

- ✅ `docker-compose.yml` 文件格式正确
- ✅ Docker Compose 可以正常使用
- ⚠️ 只是 VS Code 扩展的网络问题

**可以安全忽略这个警告。**

