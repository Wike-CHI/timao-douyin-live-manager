# 宝塔面板部署实战教程 - 使用公网IP 129.211.218.135

## 🎯 部署目标

- **公网IP**：`129.211.218.135`
- **后端服务**：FastAPI运行在端口 `11111`
- **访问方式**：通过公网IP访问（后续可绑定域名）
- **反向代理**：Nginx代理后端API

---

## 📋 前置准备清单

- [x] 服务器已安装宝塔面板
- [ ] 后端服务已启动（端口11111）
- [ ] 防火墙已开放必要端口
- [ ] 了解SSH登录服务器

---

## 第一步：登录宝塔面板

### 1.1 访问宝塔面板

在浏览器中打开：

```
http://129.211.218.135:8888
```

**注意**：
- 如果无法访问，检查云服务器安全组是否开放8888端口
- 默认端口是8888，如果修改过，使用修改后的端口

### 1.2 输入账号密码

```
账号：（宝塔面板安装时生成的账号）
密码：（宝塔面板安装时生成的密码）
```

**找不到密码？** 在服务器上执行：
```bash
bt default
```

---

## 第二步：创建站点

### 2.1 进入网站管理

1. 登录宝塔面板后
2. 点击左侧菜单 **"网站"**
3. 点击右上角 **"添加站点"** 按钮

### 2.2 填写站点信息（方案A：使用IP访问）

```
┌─────────────────────────────────────────────────┐
│ 添加站点                                        │
├─────────────────────────────────────────────────┤
│ 域名：129.211.218.135                           │
│ 备注：提猫直播助手                              │
│ 根目录：/www/wwwroot/129.211.218.135            │
│ FTP：不创建                                     │
│ 数据库：MySQL（如需要）                         │
│ PHP版本：纯静态                                 │
└─────────────────────────────────────────────────┘
```

**重要提示**：
- 域名栏填写公网IP：`129.211.218.135`
- PHP版本选择"纯静态"（因为我们只做反向代理）

### 2.3 点击"提交"

站点创建成功后，会在列表中看到：

```
| 网站名称              | 运行目录                        | 状态 |
|----------------------|--------------------------------|------|
| 129.211.218.135      | /www/wwwroot/129.211.218.135  | 运行中|
```

---

## 第三步：配置反向代理

### 3.1 打开站点设置

1. 在网站列表中，找到 `129.211.218.135`
2. 点击右侧的 **"设置"** 按钮
3. 会打开站点设置面板

### 3.2 配置反向代理

1. 点击左侧 **"反向代理"** 选项卡
2. 点击 **"添加反向代理"** 按钮

### 3.3 填写反向代理信息

#### 基础配置

```
┌─────────────────────────────────────────────────┐
│ 添加反向代理                                     │
├─────────────────────────────────────────────────┤
│ 代理名称：提猫后端API                           │
│ 目标URL：http://127.0.0.1:11111                 │
│ 发送域名：$host                                 │
│ 内容替换：（留空）                               │
└─────────────────────────────────────────────────┘
```

**字段说明**：
- **代理名称**：自定义，便于识别
- **目标URL**：后端服务地址（本地11111端口）
- **发送域名**：`$host` 表示转发原始Host头

#### 高级配置（重要！）

点击 **"高级"** 按钮，在配置框中添加：

```nginx
# WebSocket支持
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";

# 代理头设置
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;

# 超时设置（重要：防止长时间请求超时）
proxy_connect_timeout 60s;
proxy_send_timeout 300s;
proxy_read_timeout 300s;

# 缓冲设置（关闭缓冲，适合流式响应）
proxy_buffering off;
proxy_request_buffering off;

# 禁用缓存
proxy_cache off;
```

### 3.4 保存配置

点击 **"提交"** 按钮

---

## 第四步：手动调整Nginx配置（推荐）

宝塔的反向代理界面有时配置不够精细，建议手动编辑配置文件。

### 4.1 打开配置文件

1. 在站点设置面板中
2. 点击 **"配置文件"** 选项卡
3. 会看到完整的Nginx配置

### 4.2 替换为以下完整配置

```nginx
server {
    listen 80;
    server_name 129.211.218.135;
    
    # 日志文件
    access_log /www/wwwlogs/129.211.218.135.log;
    error_log /www/wwwlogs/129.211.218.135.error.log;
    
    # 根目录（如果需要放置静态文件）
    root /www/wwwroot/129.211.218.135;
    index index.html;
    
    # 前端静态文件（如果有）
    location / {
        try_files $uri $uri/ /index.html;
        
        # 如果没有前端文件，可以返回简单信息
        # return 200 '{"message":"提猫直播助手API服务","docs":"http://129.211.218.135/docs"}';
        # add_header Content-Type application/json;
    }
    
    # ==================== 后端API反向代理 ====================
    location /api/ {
        proxy_pass http://127.0.0.1:11111;
        proxy_http_version 1.1;
        
        # WebSocket支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 代理头
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # 缓冲设置
        proxy_buffering off;
        proxy_request_buffering off;
        
        # 禁用缓存
        proxy_cache off;
        proxy_no_cache 1;
        proxy_cache_bypass 1;
    }
    
    # ==================== API文档 ====================
    location /docs {
        proxy_pass http://127.0.0.1:11111/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /openapi.json {
        proxy_pass http://127.0.0.1:11111/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
    
    location /redoc {
        proxy_pass http://127.0.0.1:11111/redoc;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
    
    # ==================== 健康检查 ====================
    location /health {
        proxy_pass http://127.0.0.1:11111/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        access_log off;  # 不记录健康检查日志
    }
    
    # ==================== WebSocket专用路径 ====================
    location /ws/ {
        proxy_pass http://127.0.0.1:11111;
        proxy_http_version 1.1;
        
        # WebSocket必需配置
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # WebSocket超时（更长）
        proxy_connect_timeout 60s;
        proxy_send_timeout 3600s;
        proxy_read_timeout 3600s;
    }
    
    # ==================== 静态文件优化 ====================
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|svg)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # ==================== 禁止访问隐藏文件 ====================
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

### 4.3 保存并重载配置

1. 点击 **"保存"** 按钮
2. 宝塔会自动检查配置语法
3. 如果提示"配置文件检查通过"，配置成功
4. Nginx会自动重载配置

---

## 第五步：配置防火墙

### 5.1 宝塔面板防火墙

1. 点击左侧菜单 **"安全"**
2. 添加以下端口规则：

```
┌──────────┬────────┬──────────────────┐
│   端口   │ 协议   │       说明       │
├──────────┼────────┼──────────────────┤
│    80    │  TCP   │  HTTP（必须）    │
│   443    │  TCP   │  HTTPS（可选）   │
│  11111   │  TCP   │  后端API（可选） │
└──────────┴────────┴──────────────────┘
```

**重要**：
- 80端口必须开放（用于访问网站）
- 11111端口可选（如果使用反向代理，不需要对外开放）

### 5.2 云服务器安全组

如果使用腾讯云/阿里云等云服务器，还需要在云控制台配置安全组。

#### 腾讯云（以您的服务器为例）

1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/)
2. 进入 **云服务器 CVM** 
3. 找到服务器 `129.211.218.135`
4. 点击 **安全组** -> **配置规则**
5. 添加入站规则：

```
┌──────────┬────────┬────────────┬──────────────┐
│   端口   │ 协议   │   来源     │     说明     │
├──────────┼────────┼────────────┼──────────────┤
│    80    │  TCP   │ 0.0.0.0/0  │ HTTP访问     │
│   443    │  TCP   │ 0.0.0.0/0  │ HTTPS访问    │
│  8888    │  TCP   │ 你的IP/32  │ 宝塔面板     │
└──────────┴────────┴────────────┴──────────────┘
```

**安全建议**：
- 宝塔面板端口（8888）只允许您的办公网IP访问
- 或设置复杂密码并启用入口验证

---

## 第六步：启动后端服务

### 6.1 SSH连接服务器

```bash
ssh root@129.211.218.135
```

### 6.2 进入项目目录

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
```

### 6.3 检查依赖

```bash
# 检查Python依赖
pip3 list | grep fastapi
pip3 list | grep uvicorn

# 如果缺少依赖，安装
pip3 install -r requirements.txt
```

### 6.4 使用PM2启动服务

```bash
# 启动服务
pm2 start ecosystem.config.js

# 查看服务状态
pm2 list

# 查看日志
pm2 logs timao-backend
```

### 6.5 验证服务运行

```bash
# 检查端口是否监听
netstat -tlnp | grep 11111

# 测试健康检查
curl http://localhost:11111/health

# 应该返回：
# {"status":"healthy","service":"提猫直播助手",...}
```

---

## 第七步：测试访问

### 7.1 测试健康检查

在**任意电脑**的浏览器中访问：

```
http://129.211.218.135/health
```

**期望结果**：
```json
{
  "status": "healthy",
  "service": "提猫直播助手",
  "version": "1.0.0",
  "timestamp": "2025-10-28"
}
```

### 7.2 测试API文档

访问：
```
http://129.211.218.135/docs
```

**期望结果**：
- 看到FastAPI自动生成的Swagger UI文档
- 可以看到所有API接口

### 7.3 测试API接口

```bash
# 测试CORS
curl http://129.211.218.135/api/cors-test

# 测试历史记录（需要token）
curl http://129.211.218.135/api/report/live/history?limit=5
```

### 7.4 浏览器开发者工具测试

1. 打开浏览器（Chrome/Firefox）
2. 按 `F12` 打开开发者工具
3. 切换到 **Network（网络）** 标签
4. 访问：`http://129.211.218.135/health`
5. 检查：
   - 状态码：200 OK
   - Response Headers：有 `Access-Control-Allow-Origin: *`
   - Response：JSON数据

---

## 第八步：部署前端（可选）

如果您有前端静态文件需要部署：

### 8.1 构建前端

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager/electron/renderer
npm run build
```

### 8.2 复制到站点目录

```bash
# 复制构建产物
cp -r dist/* /www/wwwroot/129.211.218.135/
```

### 8.3 访问前端

浏览器访问：
```
http://129.211.218.135
```

---

## 🔧 常见问题排查

### 问题1：502 Bad Gateway

**症状**：访问 `http://129.211.218.135/api/...` 返回502

**排查步骤**：

```bash
# 1. 检查后端服务是否运行
pm2 list
# 应该看到 timao-backend 状态为 online

# 2. 检查端口是否监听
netstat -tlnp | grep 11111
# 应该看到 LISTEN 状态

# 3. 测试本地连接
curl http://localhost:11111/health
# 应该返回JSON

# 4. 检查Nginx错误日志
tail -50 /www/wwwlogs/129.211.218.135.error.log

# 5. 重启服务
pm2 restart timao-backend
```

### 问题2：404 Not Found

**症状**：访问某个路径返回404

**可能原因**：
- 路径配置错误
- 后端路由不存在

**排查步骤**：

```bash
# 1. 检查Nginx配置
cat /www/server/panel/vhost/nginx/129.211.218.135.conf | grep location

# 2. 检查后端路由
curl http://localhost:11111/docs
# 在API文档中查看可用的路由

# 3. 测试完整路径
curl http://129.211.218.135/api/health
```

### 问题3：Connection Timeout

**症状**：请求超时

**排查步骤**：

```bash
# 1. 检查防火墙
sudo ufw status
sudo firewall-cmd --list-all

# 2. 检查云服务器安全组
# 登录云控制台检查80端口是否开放

# 3. 测试端口连通性
telnet 129.211.218.135 80

# 4. 检查Nginx是否运行
systemctl status nginx
```

### 问题4：CORS错误

**症状**：前端控制台显示CORS错误

**解决方案**：

```bash
# 1. 检查后端CORS配置
curl -I http://129.211.218.135/api/cors-test

# 应该看到：
# Access-Control-Allow-Origin: *

# 2. 如果没有，检查后端代码
# server/app/main.py 中的CORS配置

# 3. 重启后端服务
pm2 restart timao-backend
```

---

## 📊 服务状态监控

### 实时监控

```bash
# 查看PM2进程
pm2 list

# 查看实时日志
pm2 logs timao-backend

# 查看Nginx访问日志
tail -f /www/wwwlogs/129.211.218.135.log

# 查看Nginx错误日志
tail -f /www/wwwlogs/129.211.218.135.error.log

# 查看系统资源
top
htop  # 如果已安装
```

### 定时监控脚本

创建监控脚本 `/root/monitor-api.sh`：

```bash
#!/bin/bash

# 监控提猫直播助手API服务

API_URL="http://localhost:11111/health"
LOG_FILE="/var/log/timao-monitor.log"

# 检查服务健康状态
check_health() {
    response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)
    if [ "$response" = "200" ]; then
        echo "[$(date)] ✅ 服务正常" >> $LOG_FILE
        return 0
    else
        echo "[$(date)] ❌ 服务异常 (HTTP $response)" >> $LOG_FILE
        return 1
    fi
}

# 主逻辑
if ! check_health; then
    # 服务异常，尝试重启
    echo "[$(date)] 🔄 尝试重启服务..." >> $LOG_FILE
    pm2 restart timao-backend
    sleep 5
    
    # 再次检查
    if check_health; then
        echo "[$(date)] ✅ 服务重启成功" >> $LOG_FILE
    else
        echo "[$(date)] ❌ 服务重启失败，需要人工介入" >> $LOG_FILE
        # 这里可以发送告警通知
    fi
fi
```

添加到定时任务：

```bash
# 编辑crontab
crontab -e

# 添加以下行（每5分钟检查一次）
*/5 * * * * /bin/bash /root/monitor-api.sh
```

---

## 🚀 性能优化建议

### Nginx优化

编辑 `/www/server/nginx/conf/nginx.conf`：

```nginx
# 工作进程数（通常等于CPU核心数）
worker_processes auto;

# 事件模型
events {
    worker_connections 10240;
    use epoll;
}

http {
    # 开启gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss;
    
    # 连接超时
    keepalive_timeout 65;
    client_body_timeout 60;
    client_header_timeout 60;
    send_timeout 60;
    
    # 上传大小限制
    client_max_body_size 100M;
}
```

---

## 📝 配置文件备份

### 备份Nginx配置

```bash
# 备份站点配置
cp /www/server/panel/vhost/nginx/129.211.218.135.conf \
   /root/backup/nginx-129.211.218.135.conf.$(date +%Y%m%d)

# 备份Nginx主配置
cp /www/server/nginx/conf/nginx.conf \
   /root/backup/nginx.conf.$(date +%Y%m%d)
```

### 备份PM2配置

```bash
# 导出PM2配置
pm2 save

# 备份配置文件
cp /www/wwwroot/wwwroot/timao-douyin-live-manager/ecosystem.config.js \
   /root/backup/ecosystem.config.js.$(date +%Y%m%d)
```

---

## 🔐 安全加固

### 1. 修改SSH端口

```bash
# 编辑SSH配置
vi /etc/ssh/sshd_config

# 修改端口（例如改为2222）
Port 2222

# 重启SSH服务
systemctl restart sshd

# 记得在防火墙和安全组中开放新端口！
```

### 2. 禁用root登录

```bash
# 创建普通用户
adduser deploy

# 添加sudo权限
usermod -aG sudo deploy

# 禁用root登录
vi /etc/ssh/sshd_config
# 设置：PermitRootLogin no

# 重启SSH
systemctl restart sshd
```

### 3. 配置Fail2ban

```bash
# 安装fail2ban
apt install fail2ban  # Ubuntu/Debian
yum install fail2ban  # CentOS

# 启动服务
systemctl start fail2ban
systemctl enable fail2ban
```

---

## ✅ 部署检查清单

- [ ] 宝塔面板可以访问
- [ ] 站点已创建（129.211.218.135）
- [ ] 反向代理已配置
- [ ] 防火墙端口已开放（80）
- [ ] 云服务器安全组已配置
- [ ] 后端服务已启动（PM2）
- [ ] 后端服务监听11111端口
- [ ] 健康检查可访问（/health）
- [ ] API文档可访问（/docs）
- [ ] API接口正常响应
- [ ] CORS配置正确
- [ ] 日志正常记录
- [ ] 监控脚本已配置（可选）

---

## 📞 快速命令参考

```bash
# 服务管理
pm2 list                    # 查看服务列表
pm2 logs timao-backend      # 查看日志
pm2 restart timao-backend   # 重启服务
pm2 stop timao-backend      # 停止服务
pm2 save                    # 保存配置

# Nginx管理
nginx -t                    # 检查配置
nginx -s reload             # 重载配置
systemctl status nginx      # 查看状态
systemctl restart nginx     # 重启Nginx

# 端口检查
netstat -tlnp | grep 11111  # 检查后端端口
netstat -tlnp | grep 80     # 检查Nginx端口

# 日志查看
tail -f /www/wwwlogs/129.211.218.135.log        # Nginx访问日志
tail -f /www/wwwlogs/129.211.218.135.error.log  # Nginx错误日志
pm2 logs timao-backend --lines 100              # 后端日志

# 测试命令
curl http://localhost:11111/health              # 测试后端
curl http://129.211.218.135/health              # 测试代理
curl http://129.211.218.135/api/cors-test       # 测试CORS
```

---

## 🎉 恭喜！

如果以上步骤都成功完成，您的提猫直播助手后端服务已经成功部署到公网IP `129.211.218.135`！

**访问地址**：
- API文档：http://129.211.218.135/docs
- 健康检查：http://129.211.218.135/health
- API接口：http://129.211.218.135/api/...

**下一步**：
1. 绑定域名（可选但推荐）
2. 配置SSL证书（启用HTTPS）
3. 部署前端应用
4. 配置CDN加速

需要帮助？查看其他文档：
- [PM2部署教程](./PM2部署教程.md)
- [数据传输检查报告](./数据传输检查报告.md)
- [Electron打包教程](./Electron打包教程.md)

