# PM2启动timao-cloud服务 - 完整指南总结

**创建日期**: 2025-11-16  
**审查人**: 叶维哲  
**服务名称**: timao-cloud  
**服务端口**: 15000  

---

## 📚 文档导航

本次创建的PM2启动相关文档：

| 文档名称 | 用途 | 适合人群 |
|---------|------|---------|
| **PM2启动timao-cloud服务指南.md** | 完整启动指南 | 详细阅读 |
| **PM2命令速查卡.md** | 常用命令速查 | 快速查阅 |
| **start_cloud.sh** | 一键启动脚本 | 快速启动 |
| **test_cloud_service.sh** | 服务测试脚本 | 验证服务 |

---

## 🚀 快速开始

### 三种启动方式

#### 方式1: 一键启动（最推荐）

```bash
# 1. 赋予执行权限（首次需要）
chmod +x start_cloud.sh

# 2. 运行启动脚本
./start_cloud.sh

# 3. 验证服务
./test_cloud_service.sh
```

#### 方式2: PM2命令启动（日常使用）

```bash
# 简洁版本
pm2 start "uvicorn server.cloud.main:app --host 0.0.0.0 --port 15000 --workers 1" \
  --name timao-cloud \
  --interpreter python3 \
  --max-memory-restart 600M
```

#### 方式3: 配置文件启动（生产环境）

```bash
# 使用ecosystem配置
pm2 start ecosystem.cloud.config.js
```

---

## 📋 关键文件清单

### 启动相关

```
项目根目录/
├── start_cloud.sh              # ⭐ 一键启动脚本
├── test_cloud_service.sh       # 🧪 服务测试脚本
├── ecosystem.cloud.config.js   # 📝 PM2配置文件
├── PM2启动timao-cloud服务指南.md   # 📚 完整指南
├── PM2命令速查卡.md            # 📖 快速参考
└── PM2启动指南总结.md          # 📌 本文档
```

### 服务代码

```
server/cloud/
├── main.py                     # FastAPI入口
├── routers/
│   ├── auth.py                # 认证路由
│   ├── profile.py             # 用户资料
│   └── subscription.py        # 订阅支付
└── static/
    ├── index.html             # 控制台页面
    └── assets/
        └── icon.png           # Logo
```

### 配置文件

```
server/
├── .env                       # 环境变量
└── config.py                  # 应用配置
```

---

## 🎯 常用命令

### 启动和管理

```bash
# 启动
./start_cloud.sh                    # 一键启动
pm2 start ecosystem.cloud.config.js # 配置启动

# 查看
pm2 status timao-cloud              # 查看状态
pm2 info timao-cloud                # 详细信息
pm2 monit                           # 实时监控

# 日志
pm2 logs timao-cloud                # 实时日志
pm2 logs timao-cloud --lines 50     # 最近50行

# 重启
pm2 restart timao-cloud             # 重启服务
pm2 reload timao-cloud              # 平滑重启

# 停止
pm2 stop timao-cloud                # 停止服务
pm2 delete timao-cloud              # 删除进程
```

### 测试和验证

```bash
# 运行测试脚本
./test_cloud_service.sh

# 手动测试
curl http://localhost:15000/health  # 健康检查
curl http://localhost:15000/        # 控制台
curl http://localhost:15000/docs    # API文档
```

---

## 📊 服务指标

### 正常运行指标

| 指标 | 正常值 | 说明 |
|------|--------|------|
| **状态** | online | PM2进程状态 |
| **内存** | < 600MB | 云端轻量级服务 |
| **重启次数** | 0-2次 | 超过5次需检查 |
| **CPU** | < 20% | 空闲时 |
| **响应时间** | < 100ms | 健康检查 |

### 监控命令

```bash
# 查看内存
pm2 status timao-cloud | grep memory

# 查看重启次数
pm2 info timao-cloud | grep restart

# 实时监控
pm2 monit
```

---

## 🐛 故障排查流程

### 问题1: 启动失败

```bash
# 步骤1: 查看错误日志
pm2 logs timao-cloud --err --lines 50

# 步骤2: 检查端口占用
netstat -tlnp | grep 15000
# 如果被占用: kill -9 <PID>

# 步骤3: 检查Python环境
python3 --version
pip list | grep -E "fastapi|uvicorn"

# 步骤4: 重新启动
./start_cloud.sh
```

### 问题2: 服务频繁重启

```bash
# 步骤1: 查看重启原因
pm2 logs timao-cloud --err --lines 100

# 步骤2: 检查内存
pm2 status timao-cloud

# 步骤3: 增加内存限制
pm2 delete timao-cloud
pm2 start "..." --max-memory-restart 800M

# 步骤4: 检查数据库连接
curl http://localhost:15000/health
```

### 问题3: 无法访问

```bash
# 步骤1: 检查进程状态
pm2 status timao-cloud

# 步骤2: 测试本地访问
curl http://localhost:15000/health

# 步骤3: 检查Nginx
sudo nginx -t
tail -f /www/wwwlogs/timao-cloud-error.log

# 步骤4: 重启服务
pm2 restart timao-cloud
```

---

## 🔒 生产环境建议

### 安全配置

```bash
# 1. 只监听内网（通过Nginx代理）
--host 127.0.0.1

# 2. 设置环境变量
export CLOUD_ENV=production
export SECRET_KEY=your-secret-key

# 3. 使用非root用户
su - devuser
pm2 start ...
```

### 自动重启和监控

```bash
# 1. 保存进程列表
pm2 save

# 2. 设置开机自启
pm2 startup

# 3. 配置日志轮转
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7

# 4. 定期健康检查（crontab）
*/5 * * * * curl -s http://localhost:15000/health > /dev/null || pm2 restart timao-cloud
```

---

## 📈 性能优化

### Workers配置

```bash
# 单个worker（推荐，云端轻量级）
--workers 1

# 多个workers（如果负载高）
--workers 2  # 根据CPU核心数
```

### 内存管理

```bash
# 标准配置
--max-memory-restart 600M

# 如果频繁重启
--max-memory-restart 800M
```

### 日志级别

```bash
# 生产环境（减少日志）
uvicorn ... --log-level warning

# 开发环境（详细日志）
uvicorn ... --log-level info
```

---

## 🔄 更新流程

### 标准更新流程

```bash
# 1. 停止服务
pm2 stop timao-cloud

# 2. 拉取代码
git pull origin main

# 3. 更新依赖（如果有变化）
pip install -r requirements.txt

# 4. 重启服务
pm2 restart timao-cloud

# 5. 查看日志
pm2 logs timao-cloud --lines 20

# 6. 测试验证
./test_cloud_service.sh
```

### 平滑更新（0停机）

```bash
# 使用reload代替restart
pm2 reload timao-cloud

# 或使用多个workers
pm2 scale timao-cloud 2  # 增加到2个
pm2 reload timao-cloud    # 平滑重启
pm2 scale timao-cloud 1   # 恢复到1个
```

---

## 📞 快速帮助

### 立即需要帮助？

1. **查看日志**: `pm2 logs timao-cloud --lines 50`
2. **查看状态**: `pm2 status timao-cloud`
3. **重启服务**: `pm2 restart timao-cloud`
4. **运行测试**: `./test_cloud_service.sh`

### 获取更多信息

- 详细指南: 查看 `PM2启动timao-cloud服务指南.md`
- 命令速查: 查看 `PM2命令速查卡.md`
- Nginx配置: 查看 `Nginx反代配置优化说明.md`
- 部署文档: 查看 `docs/部署文档/云端服务部署指南.md`

---

## ✅ 启动检查清单

部署前确认：

- [ ] Python 3.8+ 已安装
- [ ] 依赖已安装 (`pip install -r requirements.txt`)
- [ ] 环境变量已配置 (`server/.env`)
- [ ] PM2 已安装 (`npm install -g pm2`)
- [ ] 端口 15000 未被占用
- [ ] 数据库连接正常
- [ ] Nginx 已配置

启动后确认：

- [ ] `pm2 status timao-cloud` 显示 `online`
- [ ] `curl http://localhost:15000/health` 返回 healthy
- [ ] `curl http://localhost:15000/` 返回控制台
- [ ] 内存占用 < 600MB
- [ ] 日志无错误
- [ ] 测试脚本通过 (`./test_cloud_service.sh`)

---

## 🎉 总结

### 启动服务（三步走）

```bash
# 1. 启动
./start_cloud.sh

# 2. 测试
./test_cloud_service.sh

# 3. 保存
pm2 save
```

### 日常管理（记住这些）

```bash
# 查看: pm2 status timao-cloud
# 日志: pm2 logs timao-cloud
# 重启: pm2 restart timao-cloud
# 测试: ./test_cloud_service.sh
```

### 故障排查（快速三步）

```bash
# 1. 查错误: pm2 logs timao-cloud --err
# 2. 重启: pm2 restart timao-cloud
# 3. 测试: ./test_cloud_service.sh
```

---

## 📌 相关文档

- ✅ `PM2启动timao-cloud服务指南.md` - 完整详细指南
- ✅ `PM2命令速查卡.md` - 快速命令参考
- ✅ `start_cloud.sh` - 一键启动脚本
- ✅ `test_cloud_service.sh` - 服务测试脚本
- ✅ `Nginx反代配置优化说明.md` - Nginx优化
- ✅ `ecosystem.cloud.config.js` - PM2配置文件
- ✅ `docs/部署文档/云端服务部署指南.md` - 完整部署流程

---

**📝 文档审查人**: 叶维哲  
**🎯 推荐使用**: `./start_cloud.sh` 一键启动  
**🧪 推荐测试**: `./test_cloud_service.sh` 快速验证  

🎉 **现在您可以轻松启动和管理timao-cloud云端服务了！**

