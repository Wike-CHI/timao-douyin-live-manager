# 数据库和Redis连接诊断指南

## 问题症状

从日志看到：
- ✅ 数据库连接成功：`✅ 使用 MySQL 数据库：timao@localhost:3306/timao_live`
- ✅ Redis连接成功：`✅ Redis 连接成功: localhost:6379`
- ❌ 但服务随后立即关闭：`🐱 提猫直播助手正在关闭...`

## 根本原因

**不是连接失败**，而是 **uvicorn 自动重载**导致的频繁重启：
- 日志显示：`WatchFiles detected changes in 'scripts\create_admin.py'. Reloading...`
- 编辑 `server/scripts/create_admin.py` 时触发了自动重载
- 服务不断重启，看起来像是连接失败

## ✅ 已修复

已在 `server/app/main.py` 中添加了 `reload_exclude` 配置，排除以下目录：
- `**/scripts/**` - 脚本目录
- `**/logs/**` - 日志目录
- `**/*.pyc` - Python编译文件
- `**/__pycache__/**` - Python缓存目录
- `**/node_modules/**` - Node.js依赖
- `**/.venv/**` - 虚拟环境
- `**/.git/**` - Git目录

## 🔍 验证连接状态

### 1. 检查MySQL服务

**Windows:**
```powershell
# 检查MySQL服务状态
Get-Service -Name MySQL* | Select-Object Name, Status

# 或者检查端口
Test-NetConnection -ComputerName localhost -Port 3306
```

**Linux/macOS:**
```bash
# 检查MySQL服务状态
sudo systemctl status mysql
# 或
sudo service mysql status

# 检查端口
netstat -an | grep 3306
```

### 2. 检查Redis服务

**Windows:**
```powershell
# 检查Redis服务状态
Get-Service -Name Redis*

# 检查端口
Test-NetConnection -ComputerName localhost -Port 6379
```

**Linux/macOS:**
```bash
# 检查Redis服务状态
sudo systemctl status redis
# 或
sudo service redis status

# 检查端口
netstat -an | grep 6379
```

### 3. 测试数据库连接

```powershell
# 使用MySQL客户端测试连接
mysql -h localhost -P 3306 -u timao -p timao_live
# 输入密码: timao-20251030
```

### 4. 测试Redis连接

```powershell
# 使用redis-cli测试连接（如果已安装）
redis-cli -h localhost -p 6379 ping
# 应该返回: PONG
```

## 🔧 如果确实无法连接

### MySQL连接失败

1. **检查MySQL是否运行**
   ```powershell
   # Windows: 启动MySQL服务
   Start-Service MySQL80  # 根据你的MySQL服务名调整
   ```

2. **检查用户和密码**
   - 查看 `.env` 文件中的 `MYSQL_USER` 和 `MYSQL_PASSWORD`
   - 默认配置：
     - 用户: `timao`
     - 密码: `timao-20251030`
     - 数据库: `timao_live`

3. **检查数据库是否存在**
   ```sql
   -- 登录MySQL
   mysql -u root -p
   
   -- 创建数据库（如果不存在）
   CREATE DATABASE IF NOT EXISTS timao_live CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   
   -- 创建用户并授权（如果需要）
   CREATE USER IF NOT EXISTS 'timao'@'localhost' IDENTIFIED BY 'timao-20251030';
   GRANT ALL PRIVILEGES ON timao_live.* TO 'timao'@'localhost';
   FLUSH PRIVILEGES;
   ```

### Redis连接失败

1. **检查Redis是否运行**
   ```powershell
   # Windows: 启动Redis服务
   Start-Service Redis  # 如果已安装Windows版Redis
   ```

2. **检查配置**
   - 查看 `.env` 文件中的 `REDIS_ENABLED`、`REDIS_HOST`、`REDIS_PORT`
   - 默认配置：
     - 启用: `true`
     - 主机: `localhost`
     - 端口: `6379`

3. **Redis不是必需的**
   - 如果Redis连接失败，应用会自动回退到内存缓存模式
   - 这不会影响基本功能

## 🚀 重启服务

修复配置后，重启后端服务：

```powershell
# 停止当前服务（如果正在运行）
# 按 Ctrl+C 停止

# 重新启动
uvicorn server.app.main:app --reload --port 9019
```

## 📊 查看日志

启动服务后，应该看到：
```
✅ Redis 连接成功: localhost:6379
✅ 使用 MySQL 数据库：timao@localhost:3306/timao_live
✅ 数据库初始化完成，当前后端：MYSQL
✅ FastAPI服务已启动
```

如果没有看到这些日志，检查上面的连接步骤。

## ⚠️ 注意事项

1. **自动重载已修复**：现在编辑 `server/scripts/` 下的文件不会再触发自动重载
2. **生产环境建议**：使用 `--reload` 参数（不带自动重载）
3. **连接池**：数据库和Redis都使用了连接池，短暂连接失败会自动重试

