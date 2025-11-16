# PM2启动timao-cloud服务指南

**服务名称**: timao-cloud  
**服务端口**: 15000  
**服务类型**: 云端服务（用户/订阅/支付/积分）  
**内存限制**: < 600MB  

---

## 🚀 快速启动

### 方式1: PM2命令直接启动（推荐）

```bash
# 进入项目目录
cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 激活虚拟环境（如果有）
source .venv/bin/activate

# 启动服务
pm2 start "uvicorn server.cloud.main:app --host 0.0.0.0 --port 15000 --workers 1" \
  --name timao-cloud \
  --interpreter python3 \
  --cwd /www/wwwroot/wwwroot/timao-douyin-live-manager \
  --max-memory-restart 600M \
  --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
  --merge-logs \
  --output logs/cloud-out.log \
  --error logs/cloud-error.log
```

**一行命令版本**：
```bash
pm2 start "uvicorn server.cloud.main:app --host 0.0.0.0 --port 15000 --workers 1" --name timao-cloud --interpreter python3 --max-memory-restart 600M
```

### 方式2: 使用配置文件启动

```bash
# 使用ecosystem配置文件
pm2 start ecosystem.cloud.config.js
```

---

## 📋 启动参数说明

### 核心参数

| 参数 | 值 | 说明 |
|------|---|------|
| `command` | `uvicorn server.cloud.main:app` | 启动FastAPI应用 |
| `--host` | `0.0.0.0` | 监听所有网络接口 |
| `--port` | `15000` | 服务端口 |
| `--workers` | `1` | 工作进程数（云端轻量级，1个足够） |
| `--name` | `timao-cloud` | PM2进程名称 |
| `--interpreter` | `python3` | 使用Python3解释器 |

### 可选参数

| 参数 | 值 | 说明 |
|------|---|------|
| `--max-memory-restart` | `600M` | 内存超过600MB自动重启 |
| `--cwd` | `/www/wwwroot/.../` | 工作目录 |
| `--log-date-format` | `"YYYY-MM-DD HH:mm:ss Z"` | 日志时间格式 |
| `--merge-logs` | - | 合并多个进程日志 |
| `--output` | `logs/cloud-out.log` | 标准输出日志 |
| `--error` | `logs/cloud-error.log` | 错误日志 |

---

## 🔧 完整启动流程

### 步骤1: 环境准备

```bash
# 1. 进入项目目录
cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 2. 检查Python版本
python3 --version
# 应该显示: Python 3.8+

# 3. 检查虚拟环境
ls -la .venv/
# 如果存在虚拟环境，激活它
source .venv/bin/activate

# 4. 检查依赖
pip list | grep -E "fastapi|uvicorn|sqlalchemy"
# 确保已安装必要的包

# 5. 检查环境变量
cat server/.env | grep -E "MYSQL_|SECRET_KEY"
# 确保数据库配置正确
```

### 步骤2: 启动服务

#### 选项A: 简洁命令（推荐日常使用）

```bash
pm2 start "uvicorn server.cloud.main:app --host 0.0.0.0 --port 15000 --workers 1" \
  --name timao-cloud \
  --interpreter python3 \
  --max-memory-restart 600M
```

#### 选项B: 完整配置命令

```bash
pm2 start "uvicorn server.cloud.main:app --host 0.0.0.0 --port 15000 --workers 1" \
  --name timao-cloud \
  --interpreter python3 \
  --cwd /www/wwwroot/wwwroot/timao-douyin-live-manager \
  --max-memory-restart 600M \
  --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
  --merge-logs \
  --output logs/cloud-out.log \
  --error logs/cloud-error.log \
  --time \
  --restart-delay 3000 \
  --max-restarts 10 \
  --min-uptime 10s
```

#### 选项C: 使用配置文件

```bash
pm2 start ecosystem.cloud.config.js
```

### 步骤3: 验证启动

```bash
# 1. 查看进程状态
pm2 status timao-cloud

# 应该显示:
# ┌─────┬──────────────┬─────────┬─────────┬─────────┬──────────┐
# │ id  │ name         │ status  │ restart │ uptime  │ memory   │
# ├─────┼──────────────┼─────────┼─────────┼─────────┼──────────┤
# │ 0   │ timao-cloud  │ online  │ 0       │ 5s      │ 150.5 MB │
# └─────┴──────────────┴─────────┴─────────┴─────────┴──────────┘

# 2. 查看实时日志
pm2 logs timao-cloud --lines 20

# 应该看到:
# ✅ 云端服务启动完成
# INFO:     Started server process
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.

# 3. 测试健康检查
curl http://localhost:15000/health

# 应该返回:
# {"status":"healthy","service":"cloud",...}

# 4. 测试控制台
curl http://localhost:15000/

# 应该返回HTML控制台页面
```

---

## 📊 PM2管理命令

### 查看状态

```bash
# 查看所有进程
pm2 list

# 查看timao-cloud详细信息
pm2 info timao-cloud

# 查看实时监控
pm2 monit

# 查看资源占用
pm2 status timao-cloud
```

### 日志管理

```bash
# 查看实时日志（所有输出）
pm2 logs timao-cloud

# 查看最近50行日志
pm2 logs timao-cloud --lines 50

# 只看错误日志
pm2 logs timao-cloud --err

# 只看标准输出
pm2 logs timao-cloud --out

# 清空日志
pm2 flush timao-cloud
```

### 重启和停止

```bash
# 重启服务
pm2 restart timao-cloud

# 平滑重启（0秒停机）
pm2 reload timao-cloud

# 停止服务
pm2 stop timao-cloud

# 删除进程
pm2 delete timao-cloud

# 重启所有进程
pm2 restart all

# 停止所有进程
pm2 stop all
```

### 保存和开机自启

```bash
# 保存当前PM2进程列表
pm2 save

# 设置开机自启动
pm2 startup

# 会输出一个sudo命令，复制并执行
# 例如: sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u devuser --hp /home/devuser

# 取消开机自启
pm2 unstartup systemd
```

---

## 🔄 更新服务

### 更新代码后重启

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 更新依赖（如果有变化）
pip install -r requirements.txt

# 3. 重启服务
pm2 restart timao-cloud

# 4. 查看日志确认启动成功
pm2 logs timao-cloud --lines 20
```

### 修改配置后重启

```bash
# 1. 修改环境变量
vim server/.env

# 2. 重启服务
pm2 restart timao-cloud

# 3. 验证配置生效
curl http://localhost:15000/health
```

---

## 🐛 故障排查

### 问题1: 启动失败

**症状**: `pm2 start` 后显示 `errored` 或 `stopped`

**排查步骤**:
```bash
# 1. 查看错误日志
pm2 logs timao-cloud --err --lines 50

# 2. 常见错误原因：

# 错误A: 端口被占用
# 解决: netstat -tlnp | grep 15000
#       kill -9 <PID>

# 错误B: Python模块未找到
# 解决: pip install fastapi uvicorn sqlalchemy pymysql

# 错误C: 数据库连接失败
# 解决: 检查 server/.env 中的数据库配置

# 错误D: 权限问题
# 解决: chmod +x server/cloud/main.py
```

### 问题2: 内存持续增长

**症状**: 内存占用持续增长，频繁重启

**排查步骤**:
```bash
# 1. 查看内存占用
pm2 status timao-cloud

# 2. 如果持续增长超过600MB，检查：
#    - 数据库连接是否正确关闭
#    - 是否有内存泄漏

# 3. 临时解决：增加内存限制
pm2 delete timao-cloud
pm2 start "uvicorn server.cloud.main:app --host 0.0.0.0 --port 15000 --workers 1" \
  --name timao-cloud \
  --interpreter python3 \
  --max-memory-restart 800M
```

### 问题3: 服务频繁重启

**症状**: `restart` 计数器不断增加

**排查步骤**:
```bash
# 1. 查看重启原因
pm2 logs timao-cloud --err --lines 100

# 2. 检查是否内存超限
pm2 info timao-cloud | grep -A 5 "restart"

# 3. 增加重启延迟
pm2 delete timao-cloud
pm2 start "uvicorn server.cloud.main:app --host 0.0.0.0 --port 15000 --workers 1" \
  --name timao-cloud \
  --interpreter python3 \
  --restart-delay 5000 \
  --max-restarts 5
```

### 问题4: 日志过大

**症状**: 日志文件占用大量磁盘空间

**解决方案**:
```bash
# 1. 清空当前日志
pm2 flush timao-cloud

# 2. 安装日志轮转模块
pm2 install pm2-logrotate

# 3. 配置日志轮转
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
pm2 set pm2-logrotate:compress true

# 4. 手动删除旧日志
rm -f logs/cloud-*.log.gz
```

---

## 📈 性能优化

### 1. Workers数量

```bash
# 云端服务轻量级，1个worker足够
--workers 1

# 如果负载高，可以增加到CPU核心数
# workers=$(nproc)
--workers 2  # 根据实际情况调整
```

### 2. 内存限制

```bash
# 当前设置：600MB（足够轻量级服务）
--max-memory-restart 600M

# 如果频繁重启，可以增加到800MB
--max-memory-restart 800M
```

### 3. 日志级别

```bash
# 在启动命令中添加日志级别
pm2 start "uvicorn server.cloud.main:app --host 0.0.0.0 --port 15000 --workers 1 --log-level warning" \
  --name timao-cloud \
  --interpreter python3
```

---

## 🔐 生产环境建议

### 安全配置

```bash
# 1. 只监听内网
--host 127.0.0.1  # 通过Nginx代理访问

# 2. 设置环境变量
export CLOUD_ENV=production
export SECRET_KEY=your-secret-key

# 3. 使用非root用户运行
# 切换到普通用户
su - devuser
pm2 start ...
```

### 监控和告警

```bash
# 1. 安装PM2监控模块
pm2 install pm2-server-monit

# 2. 查看监控面板
pm2 web

# 3. 配置邮件告警（可选）
pm2 install pm2-notify
```

---

## 📝 快速参考

### 常用命令速查

```bash
# 启动
pm2 start ecosystem.cloud.config.js
# 或
pm2 start "uvicorn server.cloud.main:app --host 0.0.0.0 --port 15000 --workers 1" --name timao-cloud --interpreter python3 --max-memory-restart 600M

# 查看状态
pm2 status timao-cloud

# 查看日志
pm2 logs timao-cloud

# 重启
pm2 restart timao-cloud

# 停止
pm2 stop timao-cloud

# 删除
pm2 delete timao-cloud

# 保存
pm2 save

# 开机自启
pm2 startup
```

### 完整启动脚本

创建文件 `start_cloud.sh`：

```bash
#!/bin/bash
# 启动timao-cloud服务

set -e

echo "=========================================="
echo "🚀 启动timao-cloud云端服务"
echo "=========================================="
echo ""

# 进入项目目录
cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 激活虚拟环境（如果有）
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ 虚拟环境已激活"
fi

# 停止已有进程
if pm2 list | grep -q "timao-cloud"; then
    echo "⚠️  发现已运行的timao-cloud进程，停止中..."
    pm2 stop timao-cloud
    pm2 delete timao-cloud
fi

# 启动服务
echo ""
echo "启动云端服务..."
pm2 start "uvicorn server.cloud.main:app --host 0.0.0.0 --port 15000 --workers 1" \
  --name timao-cloud \
  --interpreter python3 \
  --max-memory-restart 600M \
  --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
  --merge-logs \
  --output logs/cloud-out.log \
  --error logs/cloud-error.log

# 等待启动
echo ""
echo "等待服务启动..."
sleep 3

# 查看状态
pm2 status timao-cloud

# 测试健康检查
echo ""
echo "测试健康检查..."
sleep 2
curl -s http://localhost:15000/health | python3 -m json.tool

echo ""
echo "=========================================="
echo "🎉 启动完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  - 控制台: http://localhost:15000/"
echo "  - 健康检查: http://localhost:15000/health"
echo "  - API文档: http://localhost:15000/docs"
echo ""
echo "管理命令:"
echo "  - 查看状态: pm2 status timao-cloud"
echo "  - 查看日志: pm2 logs timao-cloud"
echo "  - 重启服务: pm2 restart timao-cloud"
echo ""
```

**使用脚本**:
```bash
# 赋予执行权限
chmod +x start_cloud.sh

# 运行脚本
./start_cloud.sh
```

---

## 🎯 总结

### 推荐启动方式

**日常使用**（简洁）:
```bash
pm2 start "uvicorn server.cloud.main:app --host 0.0.0.0 --port 15000 --workers 1" \
  --name timao-cloud \
  --interpreter python3 \
  --max-memory-restart 600M
```

**生产环境**（完整配置）:
```bash
pm2 start ecosystem.cloud.config.js
```

**一键脚本**:
```bash
./start_cloud.sh
```

### 关键检查点

启动后必须检查：
- ✅ `pm2 status timao-cloud` 显示 `online`
- ✅ `curl http://localhost:15000/health` 返回 `{"status":"healthy"}`
- ✅ `curl http://localhost:15000/` 返回控制台HTML
- ✅ 内存占用 < 600MB
- ✅ 日志无错误

🎉 **现在您可以快速启动和管理timao-cloud云端服务了！**

