# PM2命令速查卡 - timao-cloud

**服务名称**: `timao-cloud`  
**端口**: `15000`  
**日志目录**: `logs/`  

---

## 🚀 启动服务

### 方式1: 一键启动脚本（推荐）
```bash
./start_cloud.sh
```

### 方式2: PM2命令启动
```bash
pm2 start "uvicorn server.cloud.main:app --host 0.0.0.0 --port 15000 --workers 1" \
  --name timao-cloud \
  --interpreter python3 \
  --max-memory-restart 600M
```

### 方式3: 配置文件启动
```bash
pm2 start ecosystem.cloud.config.js
```

---

## 📊 查看状态

```bash
# 查看所有进程
pm2 list

# 查看timao-cloud状态
pm2 status timao-cloud

# 查看详细信息
pm2 info timao-cloud

# 实时监控
pm2 monit
```

---

## 📝 查看日志

```bash
# 实时日志（所有）
pm2 logs timao-cloud

# 最近50行日志
pm2 logs timao-cloud --lines 50

# 只看错误日志
pm2 logs timao-cloud --err

# 只看输出日志
pm2 logs timao-cloud --out

# 清空日志
pm2 flush timao-cloud
```

---

## 🔄 重启和停止

```bash
# 重启服务
pm2 restart timao-cloud

# 平滑重启（0停机）
pm2 reload timao-cloud

# 停止服务
pm2 stop timao-cloud

# 删除进程
pm2 delete timao-cloud
```

---

## 💾 保存和自启动

```bash
# 保存进程列表
pm2 save

# 设置开机自启（首次需要）
pm2 startup

# 取消开机自启
pm2 unstartup systemd
```

---

## 🧪 测试服务

```bash
# 运行测试脚本
./test_cloud_service.sh

# 手动测试
curl http://localhost:15000/health
curl http://localhost:15000/
```

---

## 🐛 故障排查

```bash
# 查看最近错误
pm2 logs timao-cloud --err --lines 20

# 检查端口占用
netstat -tlnp | grep 15000

# 重启服务
pm2 restart timao-cloud

# 查看PM2守护进程
pm2 status
pm2 ping
```

---

## 🔧 修改配置

```bash
# 修改环境变量
vim server/.env

# 重启服务使配置生效
pm2 restart timao-cloud
```

---

## 📦 更新代码

```bash
# 拉取代码
git pull origin main

# 更新依赖
pip install -r requirements.txt

# 重启服务
pm2 restart timao-cloud
```

---

## 🎯 常见场景

### 场景1: 首次部署
```bash
# 1. 启动服务
./start_cloud.sh

# 2. 测试服务
./test_cloud_service.sh

# 3. 保存并设置自启
pm2 save
pm2 startup
```

### 场景2: 更新代码
```bash
# 1. 停止服务
pm2 stop timao-cloud

# 2. 拉取代码
git pull

# 3. 更新依赖（如果需要）
pip install -r requirements.txt

# 4. 重启服务
pm2 restart timao-cloud

# 5. 查看日志
pm2 logs timao-cloud --lines 20
```

### 场景3: 服务异常
```bash
# 1. 查看错误日志
pm2 logs timao-cloud --err --lines 50

# 2. 重启服务
pm2 restart timao-cloud

# 3. 如果还有问题，删除重建
pm2 delete timao-cloud
./start_cloud.sh
```

### 场景4: 内存溢出
```bash
# 1. 查看内存占用
pm2 status timao-cloud

# 2. 增加内存限制
pm2 delete timao-cloud
pm2 start "uvicorn server.cloud.main:app --host 0.0.0.0 --port 15000 --workers 1" \
  --name timao-cloud \
  --interpreter python3 \
  --max-memory-restart 800M
```

---

## 📞 快速帮助

### 服务不启动
1. 检查端口占用: `netstat -tlnp | grep 15000`
2. 查看错误日志: `pm2 logs timao-cloud --err`
3. 检查Python版本: `python3 --version`
4. 检查依赖: `pip list | grep fastapi`

### 服务频繁重启
1. 查看重启次数: `pm2 info timao-cloud | grep restart`
2. 查看内存占用: `pm2 status timao-cloud`
3. 查看错误原因: `pm2 logs timao-cloud --err --lines 100`

### 无法访问
1. 检查服务状态: `pm2 status timao-cloud`
2. 测试本地访问: `curl http://localhost:15000/health`
3. 检查Nginx配置: `sudo nginx -t`
4. 查看Nginx日志: `tail -f /www/wwwlogs/timao-cloud-error.log`

---

## 📚 详细文档

- 完整启动指南: `PM2启动timao-cloud服务指南.md`
- Nginx配置优化: `Nginx反代配置优化说明.md`
- 云端部署指南: `docs/部署文档/云端服务部署指南.md`

---

**常用命令记忆口诀**:
- 启动: `./start_cloud.sh`
- 查看: `pm2 status timao-cloud`
- 日志: `pm2 logs timao-cloud`
- 重启: `pm2 restart timao-cloud`
- 测试: `./test_cloud_service.sh`

🎯 **保存此文件以便快速查阅！**

