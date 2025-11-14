# PM2 后端服务管理指南

## 📋 当前配置

```javascript
应用名称: timao-backend
端口: 11111
Python环境: .venv/bin/python (虚拟环境)
工作目录: /www/wwwroot/wwwroot/timao-douyin-live-manager
启动命令: python -m uvicorn server.app.main:app --host 0.0.0.0 --port 11111 --workers 1

内存限制: 2GB (超过自动重启)
日志路径: 
  - logs/pm2-out.log
  - logs/pm2-error.log
```

## 🚀 基本操作

### 启动服务

```bash
# 使用配置文件启动
pm2 start ecosystem.config.js

# 或者直接启动（如果已配置）
pm2 start timao-backend

# 启动并保存配置
pm2 start ecosystem.config.js --update-env
pm2 save
```

### 停止服务

```bash
# 停止服务
pm2 stop timao-backend

# 停止所有服务
pm2 stop all
```

### 重启服务

```bash
# 重启服务（推荐，零停机）
pm2 reload timao-backend

# 强制重启
pm2 restart timao-backend

# 重启所有服务
pm2 restart all
```

### 删除服务

```bash
# 删除服务（从PM2列表中移除）
pm2 delete timao-backend

# 删除所有服务
pm2 delete all
```

## 📊 监控和查看

### 查看进程列表

```bash
# 列出所有进程
pm2 list

# 或者简写
pm2 ls
```

### 查看进程详情

```bash
# 查看详细信息
pm2 show timao-backend

# 或使用ID
pm2 show 0
```

### 实时监控

```bash
# 实时监控CPU和内存
pm2 monit

# 查看进程树
pm2 ps
```

### 查看日志

```bash
# 实时查看日志（所有日志）
pm2 logs timao-backend

# 实时查看（只看最后50行）
pm2 logs timao-backend --lines 50

# 只看错误日志
pm2 logs timao-backend --err

# 只看输出日志
pm2 logs timao-backend --out

# 清空日志
pm2 flush timao-backend
```

### 直接查看日志文件

```bash
# 查看输出日志
tail -f logs/pm2-out.log

# 查看错误日志
tail -f logs/pm2-error.log

# 查看最后100行
tail -100 logs/pm2-out.log
```

## 🔧 配置管理

### 查看环境变量

```bash
# 查看所有环境变量
pm2 env 0
```

### 更新配置

```bash
# 修改 ecosystem.config.js 后重载配置
pm2 reload ecosystem.config.js --update-env

# 保存当前配置（开机自启）
pm2 save
```

### 设置开机自启

```bash
# 生成启动脚本
pm2 startup

# 保存当前进程列表
pm2 save

# 禁用开机自启
pm2 unstartup
```

## 📝 常用场景

### 场景1: 首次启动

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 启动服务
pm2 start ecosystem.config.js

# 保存配置（开机自启）
pm2 save

# 查看状态
pm2 list
```

### 场景2: 更新代码后重启

```bash
# 拉取最新代码
git pull

# 重启服务（零停机）
pm2 reload timao-backend

# 查看日志确认
pm2 logs timao-backend --lines 50
```

### 场景3: 服务异常排查

```bash
# 1. 查看进程状态
pm2 list

# 2. 查看详细信息（重启次数、运行时间等）
pm2 show timao-backend

# 3. 查看错误日志
pm2 logs timao-backend --err --lines 100

# 4. 查看系统资源
pm2 monit

# 5. 如果需要重启
pm2 restart timao-backend
```

### 场景4: 内存占用过高

```bash
# 查看当前内存
pm2 show timao-backend

# 如果接近2GB（配置的max_memory_restart）
# PM2会自动重启

# 手动重启释放内存
pm2 reload timao-backend
```

### 场景5: 查看SenseVoice加载情况

```bash
# 查看启动日志（SenseVoice初始化信息）
pm2 logs timao-backend --lines 200 | grep -i "sensevoice\|vad\|模型"

# 实时查看
pm2 logs timao-backend | grep -i "sensevoice\|vad"
```

### 场景6: 性能监控

```bash
# 实时监控
pm2 monit

# 查看历史数据
pm2 show timao-backend

# 使用PM2 Plus（需要注册）
pm2 plus
```

## 📊 状态解读

### 进程状态

| 状态 | 说明 | 操作 |
|-----|------|------|
| online | 正常运行 | ✅ 无需操作 |
| stopping | 正在停止 | ⏳ 等待停止完成 |
| stopped | 已停止 | 🔄 需要启动 |
| errored | 出错 | ❌ 查看日志，修复后重启 |
| one-launch-status | 单次启动 | ⚠️  检查配置 |

### 重启次数

```
重启次数过多（>50）可能表明：
- ❌ 代码有bug导致崩溃
- ❌ 内存超限频繁重启
- ❌ 端口被占用
- ❌ 依赖缺失

解决方法：
1. 查看错误日志: pm2 logs timao-backend --err
2. 检查端口: netstat -tulnp | grep 11111
3. 测试启动: python -m uvicorn server.app.main:app --port 11111
```

## 🔍 故障排除

### 问题1: 服务无法启动

```bash
# 1. 查看详细错误
pm2 logs timao-backend --err --lines 50

# 2. 手动测试启动
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
.venv/bin/python -m uvicorn server.app.main:app --port 11111

# 3. 检查端口占用
netstat -tulnp | grep 11111

# 4. 检查Python环境
.venv/bin/python --version
.venv/bin/pip list | grep -E "fastapi|uvicorn"
```

### 问题2: 日志文件过大

```bash
# 查看日志大小
du -h logs/pm2-*.log

# 清空日志
pm2 flush timao-backend

# 或手动清空
> logs/pm2-out.log
> logs/pm2-error.log
```

### 问题3: 内存泄漏

```bash
# 查看内存使用
pm2 show timao-backend | grep memory

# 如果持续增长，定期重启
pm2 reload timao-backend

# 或修改配置降低内存限制（触发更频繁的自动重启）
# 编辑 ecosystem.config.js
max_memory_restart: '1500M'  # 从2G降低到1.5G
```

### 问题4: CPU占用过高

```bash
# 实时监控
pm2 monit

# 查看系统进程
top -p $(pm2 pid timao-backend)

# 如果是推理占用高，考虑：
# 1. 优化VAD参数
# 2. 减少并发转写请求
# 3. 检查是否有死循环
```

## 🛠️ 高级配置

### 修改端口

```javascript
// ecosystem.config.js
args: '-m uvicorn server.app.main:app --host 0.0.0.0 --port 新端口 --workers 1',
env: {
  BACKEND_PORT: '新端口',
}
```

### 增加workers（多进程）

```javascript
// ecosystem.config.js
// 方法1: uvicorn workers（推荐）
args: '-m uvicorn server.app.main:app --host 0.0.0.0 --port 11111 --workers 2',

// 方法2: PM2 cluster模式（不推荐Python）
instances: 2,
exec_mode: 'cluster',
```

### 自定义日志

```javascript
// ecosystem.config.js
log_date_format: 'YYYY-MM-DD HH:mm:ss',
error_file: './logs/backend-error-' + new Date().toISOString().split('T')[0] + '.log',
out_file: './logs/backend-out-' + new Date().toISOString().split('T')[0] + '.log',
```

## 📚 相关命令速查

```bash
# 启动/停止/重启
pm2 start ecosystem.config.js    # 启动
pm2 stop timao-backend            # 停止
pm2 reload timao-backend          # 重启（零停机）
pm2 restart timao-backend         # 强制重启

# 查看
pm2 list                          # 进程列表
pm2 show timao-backend            # 详细信息
pm2 logs timao-backend            # 实时日志
pm2 monit                         # 性能监控

# 管理
pm2 save                          # 保存配置
pm2 resurrect                     # 恢复保存的进程
pm2 flush timao-backend           # 清空日志
pm2 delete timao-backend          # 删除进程

# 开机自启
pm2 startup                       # 设置自启
pm2 save                          # 保存进程列表
pm2 unstartup                     # 取消自启
```

## 🔗 相关资源

- **PM2官方文档**: https://pm2.keymetrics.io/docs/
- **项目配置**: `ecosystem.config.js`
- **日志目录**: `logs/`
- **Python环境**: `.venv/`

---

**最后更新**: 2025-11-14  
**适用版本**: PM2 5.x + Python 3.11 + FastAPI

