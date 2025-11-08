# ⚡ 快速上线指南（3步）

**遵循：奥卡姆剃刀 + 希克定律**

> 最简单的方案，最少的配置

---

## 🎯 3步上线

### 方式1：Docker 部署（推荐）

```bash
# 第1步：配置环境变量（只需6项）
cd server
cp env.production.template .env
# 编辑 .env，只修改这6项

# 第2步：一键部署
chmod +x scripts/docker_deploy.sh
./scripts/docker_deploy.sh

# 第3步：验证
curl http://localhost:11111/health
```

### 方式2：传统部署

```bash
# 第1步：配置环境变量（只需6项）
cd server
cp env.production.template .env
# 编辑 .env，只修改这6项

# 第2步：一键部署
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 第3步：启动服务
source .venv/bin/activate
python server/app/main.py
```

---

## 📋 最小化配置清单

**只需这6项**（其他都有默认值）：

1. ✅ `BACKEND_PORT=11111`
2. ✅ `MYSQL_HOST=数据库地址`
3. ✅ `MYSQL_USER=timao`
4. ✅ `MYSQL_PASSWORD=密码`
5. ✅ `MYSQL_DATABASE=timao`
6. ✅ `SECRET_KEY=密钥（生产环境必须改）`

---

## 🔧 生产环境优化

在 `.env` 中设置：

```env
DEBUG=false  # 禁用调试模式
```

这样服务会：
- 监听 `0.0.0.0`（可从外部访问）
- 禁用代码重载（提高性能）
- 使用生产模式日志

---

## 📞 故障排查

1. **端口被占用**：修改 `BACKEND_PORT`
2. **数据库连接失败**：检查 `MYSQL_*` 配置
3. **权限问题**：确保用户有执行权限

---

**记住：只配置必需的6项，其他使用默认值！**
