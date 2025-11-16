# 提猫直播助手 - 云端服务部署说明

**更新日期**: 2025-11-16  
**部署版本**: 云端服务 v1.0  
**审查人**: 叶维哲  

---

## 📋 服务说明

根据《云端本地混合部署需求完成报告》，云端服务包含：

✅ **用户系统**（auth.py 594行）
- 用户注册、登录、Token管理
- 邮箱验证、密码重置
- JWT认证、权限控制

✅ **用户资料系统**（profile.py）
- 基本信息管理
- 头像上传
- 偏好设置
- 2FA双因素认证

✅ **订阅系统**（subscription.py 377行）
- 套餐管理（免费版、基础版、专业版、企业版）
- 订阅状态查询
- 使用量统计

✅ **支付系统**（subscription.py）
- 创建支付订单
- 支付回调处理（待域名备案）
- 支付历史记录

✅ **积分系统**（集成在订阅系统）
- 积分消耗统计
- 积分充值
- 使用量监控

✅ **云端数据库CRUD**（server/cloud/db/crud.py 750行）
- UserCRUD: 9个方法（用户查询、AI配额管理）
- SubscriptionCRUD: 5个方法（订阅/套餐管理）
- PaymentCRUD: 4个方法（支付/退款记录）

**服务特点**：
- 🔒 **必须联网**：应用必须连接云端API才能使用
- 🪶 **轻量级**：内存占用 < 600MB
- ⚡ **高性能**：数据库连接池20个连接
- 🔄 **自动重启**：内存超过600MB自动重启

---

## 🚀 快速部署（推荐）

### 一键部署脚本

```bash
# 进入项目目录
cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 执行部署脚本
./scripts/deploy_cloud.sh
```

**脚本自动完成**：
1. ✅ 检查环境（Python、PM2）
2. ✅ 安装依赖
3. ✅ 检查环境变量
4. ✅ 停止旧服务
5. ✅ 启动新服务
6. ✅ 健康检查
7. ✅ 保存PM2配置

**预计耗时**：2-3分钟

---

## 📝 手动部署步骤

### 1. 安装依赖

```bash
pip install fastapi uvicorn[standard] sqlalchemy pymysql python-jose[cryptography] passlib[bcrypt] python-multipart redis pydantic[email]
```

### 2. 启动服务

```bash
# 使用PM2启动
pm2 start ecosystem.cloud.config.js

# 查看状态
pm2 status timao-cloud

# 查看日志
pm2 logs timao-cloud
```

### 3. 验证部署

```bash
# 健康检查
curl http://localhost:15000/health

# 预期输出：
# {
#   "status": "healthy",
#   "service": "cloud",
#   "memory_limit": "512MB",
#   "python_version": "3.12.2"
# }
```

---

## 🔌 前端连接配置

### 修改前端环境变量

**文件**: `admin-dashboard/.env.production`

```env
# 云端API地址（修改为实际服务器IP）
VITE_API_BASE_URL=http://你的服务器IP:15000

# 必须联网才能使用
VITE_REQUIRE_ONLINE=true
VITE_OFFLINE_MODE=false
```

### 前端打包

```bash
cd admin-dashboard

# 安装依赖
npm install

# 生产环境打包
npm run build

# 打包后文件在 dist/ 目录
```

### Electron打包（可选）

```bash
# 打包Windows安装包
npm run package

# 打包后文件在 out/ 目录
```

---

## 📊 服务管理

### PM2常用命令

```bash
# 启动
pm2 start ecosystem.cloud.config.js

# 停止
pm2 stop timao-cloud

# 重启
pm2 restart timao-cloud

# 删除
pm2 delete timao-cloud

# 查看日志
pm2 logs timao-cloud

# 监控面板
pm2 monit

# 保存配置（开机自启）
pm2 save
pm2 startup
```

### 日志查看

```bash
# 实时日志
tail -f logs/cloud-out.log

# 错误日志
tail -f logs/cloud-error.log

# 搜索错误
grep -i "error" logs/cloud-service.log
```

---

## 🔍 故障排查

### 问题1：服务启动失败

**现象**：`pm2 status` 显示 `errored`

**解决方案**：
```bash
# 查看错误日志
pm2 logs timao-cloud --err --lines 50

# 常见原因：
# 1. 端口15000被占用 → netstat -tlnp | grep 15000
# 2. Python依赖缺失 → pip install -r requirements.txt
# 3. 数据库连接失败 → 检查server/.env配置
```

### 问题2：前端无法连接

**现象**：前端登录时报错"网络连接失败"

**解决方案**：
```bash
# 1. 检查服务是否运行
curl http://localhost:15000/health

# 2. 检查防火墙
sudo ufw allow 15000/tcp

# 3. 检查前端配置
cat admin-dashboard/.env.production | grep VITE_API_BASE_URL
```

### 问题3：数据库连接失败

**现象**：日志显示"MySQL connection failed"

**解决方案**：
```bash
# 1. 检查数据库配置
cat server/.env | grep MYSQL

# 2. 测试数据库连接
mysql -h rm-bp1sqxf05yom2hwdhko.mysql.rds.aliyuncs.com \
      -u timao -p -e "SELECT 1"

# 3. 检查RDS安全组（允许服务器IP访问3306端口）
```

---

## 📈 监控建议

### 1. 内存监控

```bash
# 实时监控
pm2 monit

# 如果内存超过600MB会自动重启
```

### 2. API性能监控

- 响应时间建议 < 200ms
- 并发连接数建议 < 100
- 数据库连接池使用率 < 80%

### 3. 业务监控

- 用户注册/登录成功率
- 支付订单创建/确认成功率
- API错误率 < 1%

---

## 📦 部署清单

部署前请确认以下清单：

- [ ] 服务器环境准备（Python 3.8+、PM2）
- [ ] 代码拉取到服务器
- [ ] Python依赖安装完成
- [ ] `server/.env` 配置正确
- [ ] 数据库可正常连接
- [ ] PM2启动服务成功
- [ ] 健康检查通过（`/health` 返回200）
- [ ] 前端配置更新（`.env.production`）
- [ ] 防火墙开放15000端口
- [ ] 日志正常写入
- [ ] 内存占用 < 600MB

**部署完成标志**：
✅ `pm2 status` 显示 `timao-cloud` 为 `online`  
✅ `curl http://localhost:15000/health` 返回 `{"status": "healthy"}`  
✅ 前端Electron应用可以成功登录  

---

## 🔗 相关文档

- 📖 [云端服务部署指南](docs/部署文档/云端服务部署指南.md) - 完整部署文档
- 📊 [云端本地混合部署需求完成报告](docs/完成进度报告/云端本地混合部署需求完成报告.md) - 架构设计
- 📝 [云端数据库CRUD使用指南](docs/云端数据库CRUD使用指南.md) - 数据库操作文档

---

## 📞 技术支持

- **部署问题**：查看 `docs/部署文档/云端服务部署指南.md`
- **API文档**：访问 `http://localhost:15000/docs`（Swagger UI）
- **代码审查**：联系叶维哲

---

**快速开始**：
```bash
# 一键部署
./scripts/deploy_cloud.sh

# 验证部署
curl http://localhost:15000/health

# 查看日志
pm2 logs timao-cloud
```

🎉 **部署完成后，用户就可以通过Electron应用连接云端使用了！**

