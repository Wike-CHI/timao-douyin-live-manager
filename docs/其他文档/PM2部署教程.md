# PM2部署教程 - 提猫直播助手后端服务

## 📋 目录
1. [安装PM2](#1-安装pm2)
2. [启动服务](#2-启动服务)
3. [管理服务](#3-管理服务)
4. [查看日志](#4-查看日志)
5. [开机自启](#5-开机自启)
6. [常见问题](#6-常见问题)

---

## 1. 安装PM2

### 1.1 安装Node.js（如果未安装）
```bash
# 检查是否已安装Node.js
node -v

# 如果未安装，使用宝塔面板安装
# 或使用以下命令（CentOS/RHEL）
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs

# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 1.2 全局安装PM2
```bash
npm install -g pm2

# 验证安装
pm2 -v
```

---

## 2. 启动服务

### 2.1 进入项目目录
```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
```

### 2.2 安装Python依赖（如果未安装）
```bash
# 安装Python依赖
pip3 install -r requirements.txt

# 或使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2.3 使用PM2启动服务

#### 方法1：使用配置文件启动（推荐）
```bash
pm2 start ecosystem.config.js
```

#### 方法2：直接命令启动
```bash
pm2 start "python -m uvicorn server.app.main:app --host 0.0.0.0 --port 11111" \
  --name timao-backend \
  --interpreter none \
  --cwd /www/wwwroot/wwwroot/timao-douyin-live-manager
```

#### 方法3：使用Python虚拟环境
```bash
# 如果使用虚拟环境
pm2 start "venv/bin/python -m uvicorn server.app.main:app --host 0.0.0.0 --port 11111" \
  --name timao-backend \
  --interpreter none
```

### 2.4 验证服务启动
```bash
# 查看PM2进程列表
pm2 list

# 查看服务详细信息
pm2 show timao-backend

# 测试服务是否可访问
curl http://localhost:11111/health
```

---

## 3. 管理服务

### 3.1 常用命令

```bash
# 查看所有进程
pm2 list

# 查看进程详情
pm2 show timao-backend

# 重启服务
pm2 restart timao-backend

# 停止服务
pm2 stop timao-backend

# 删除服务
pm2 delete timao-backend

# 重新加载（0秒停机）
pm2 reload timao-backend

# 查看实时日志
pm2 logs timao-backend

# 监控
pm2 monit
```

### 3.2 批量操作
```bash
# 重启所有服务
pm2 restart all

# 停止所有服务
pm2 stop all

# 删除所有服务
pm2 delete all

# 保存当前进程列表
pm2 save
```

---

## 4. 查看日志

### 4.1 实时日志
```bash
# 查看所有日志
pm2 logs

# 查看指定服务日志
pm2 logs timao-backend

# 只看错误日志
pm2 logs timao-backend --err

# 只看输出日志
pm2 logs timao-backend --out

# 清空日志
pm2 flush
```

### 4.2 日志文件位置
```bash
# PM2日志
/www/wwwroot/wwwroot/timao-douyin-live-manager/logs/pm2-error.log
/www/wwwroot/wwwroot/timao-douyin-live-manager/logs/pm2-out.log

# 应用日志
/www/wwwroot/wwwroot/timao-douyin-live-manager/logs/backend.log
```

---

## 5. 开机自启

### 5.1 生成启动脚本
```bash
# 生成启动脚本（根据当前系统）
pm2 startup

# 会输出类似以下命令，复制并执行
# sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u root --hp /root
```

### 5.2 保存当前进程列表
```bash
pm2 save
```

### 5.3 验证开机自启
```bash
# 重启服务器后检查
pm2 list
```

### 5.4 取消开机自启
```bash
pm2 unstartup
```

---

## 6. 常见问题

### 问题1：服务启动失败
```bash
# 查看错误日志
pm2 logs timao-backend --err

# 常见原因：
# 1. Python依赖未安装
pip3 install -r requirements.txt

# 2. 端口被占用
lsof -i :11111
# 或
netstat -tlnp | grep 11111

# 3. 权限问题
sudo chown -R www:www /www/wwwroot/wwwroot/timao-douyin-live-manager
```

### 问题2：服务频繁重启
```bash
# 查看重启记录
pm2 show timao-backend

# 可能原因：
# 1. 内存不足
# 2. 代码错误
# 3. 依赖问题

# 临时禁用自动重启来调试
pm2 start ecosystem.config.js --no-autorestart
```

### 问题3：PM2命令not found
```bash
# 检查Node.js和npm
node -v
npm -v

# 重新安装PM2
npm install -g pm2

# 检查PATH
echo $PATH
```

### 问题4：日志文件过大
```bash
# 安装日志轮转
pm2 install pm2-logrotate

# 配置日志轮转
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 30
pm2 set pm2-logrotate:compress true
```

---

## 🔧 高级配置

### 配置文件说明（ecosystem.config.js）

```javascript
module.exports = {
  apps: [{
    name: 'timao-backend',           // 应用名称
    script: 'python',                // 启动脚本
    args: '-m uvicorn server.app.main:app --host 0.0.0.0 --port 11111',
    cwd: '/www/wwwroot/wwwroot/timao-douyin-live-manager',  // 工作目录
    instances: 1,                    // 实例数量
    autorestart: true,               // 自动重启
    max_memory_restart: '2G',        // 内存限制
    env: {                           // 环境变量
      NODE_ENV: 'production',
      DEBUG: 'false',
      BACKEND_PORT: '11111'
    }
  }]
};
```

### 多环境配置
```javascript
module.exports = {
  apps: [{
    name: 'timao-backend',
    script: 'python',
    args: '-m uvicorn server.app.main:app --host 0.0.0.0 --port 11111',
    
    // 开发环境
    env_development: {
      NODE_ENV: 'development',
      DEBUG: 'true',
      BACKEND_PORT: '11111'
    },
    
    // 生产环境
    env_production: {
      NODE_ENV: 'production',
      DEBUG: 'false',
      BACKEND_PORT: '11111'
    }
  }]
};

// 使用指定环境启动
// pm2 start ecosystem.config.js --env production
```

---

## 📊 监控和管理

### Web界面监控
```bash
# 安装PM2 Plus（可选）
pm2 register

# 或使用PM2 Web
pm2 web
# 访问 http://localhost:9615
```

### 性能监控
```bash
# 实时监控
pm2 monit

# 查看CPU和内存使用
pm2 show timao-backend
```

### 导出进程列表
```bash
# 导出配置
pm2 ecosystem

# 备份当前配置
pm2 save --force
```

---

## 🚀 部署流程建议

```bash
# 1. 停止旧服务
pm2 stop timao-backend

# 2. 拉取最新代码
git pull origin main

# 3. 安装依赖
pip3 install -r requirements.txt

# 4. 重启服务
pm2 restart timao-backend

# 5. 查看日志确认启动
pm2 logs timao-backend --lines 50
```

---

## 📝 快速参考

```bash
# 启动
pm2 start ecosystem.config.js

# 重启
pm2 restart timao-backend

# 停止
pm2 stop timao-backend

# 删除
pm2 delete timao-backend

# 日志
pm2 logs timao-backend

# 监控
pm2 monit

# 保存
pm2 save

# 开机自启
pm2 startup
```

---

## 📞 需要帮助？

如果遇到问题：
1. 查看PM2日志：`pm2 logs timao-backend`
2. 查看应用日志：`tail -f logs/backend.log`
3. 检查服务状态：`pm2 show timao-backend`
4. 参考官方文档：https://pm2.keymetrics.io/

