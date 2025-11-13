# Nginx 配置故障排查指南

## 🔴 问题症状

- ✅ `/docs` 可以访问 → 后端服务正常运行
- ❌ `/` 返回 500 Internal Server Error → 根路径配置有问题

## 🔍 排查步骤

### 步骤 1：检查后端服务状态

```bash
# 检查 PM2 服务
pm2 status

# 应该看到 timao-backend 状态为 online
```

### 步骤 2：测试后端本地连接

```bash
# 测试健康检查端点
curl http://127.0.0.1:11111/health

# 应该返回 JSON 数据，例如：
# {"status":"healthy","timestamp":"2025-11-13T..."}

# 测试根路径
curl http://127.0.0.1:11111/

# 检查返回内容
```

### 步骤 3：检查 Nginx 错误日志

```bash
# 查看 Nginx 错误日志
tail -50 /www/wwwlogs/timao-error.log

# 或查看最新的错误
tail -f /www/wwwlogs/timao-error.log
```

### 步骤 4：检查后端日志

```bash
# 查看 PM2 日志
pm2 logs timao-backend --lines 50

# 或查看错误日志
pm2 logs timao-backend --err --lines 50
```

## 🛠️ 解决方案

### 方案 1：更新 Nginx 配置（推荐）

1. **在宝塔面板中找到站点配置**
   ```
   宝塔面板 → 网站 → 选择站点 (129.211.218.135) → 设置 → 配置文件
   ```

2. **替换或添加以下配置**

查看项目根目录的 `nginx-config-baota.conf` 文件，复制内容到宝塔面板。

关键配置：

```nginx
server {
    listen 80;
    server_name 129.211.218.135;
    
    # 根路径代理到后端
    location / {
        proxy_pass http://127.0.0.1:11111;
        proxy_http_version 1.1;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API 路由
    location /api/ {
        proxy_pass http://127.0.0.1:11111;
        # ... 同上
    }
}
```

3. **保存并测试配置**
   ```bash
   # 测试 Nginx 配置
   nginx -t
   
   # 重新加载 Nginx
   nginx -s reload
   ```

### 方案 2：检查 FastAPI 根路由

如果后端的根路径 `/` 没有定义路由，需要在 `server/app/main.py` 中添加：

```python
@app.get("/")
async def root():
    return {
        "message": "提猫直播助手 API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }
```

然后重启后端：
```bash
pm2 restart timao-backend
```

### 方案 3：检查 CORS 配置

确保后端允许来自公网 IP 的请求。在 `server/app/main.py` 中：

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📊 常见错误及解决方案

### 错误 1: 502 Bad Gateway

**原因**: Nginx 无法连接到后端

**检查**:
```bash
# 1. 后端是否运行
pm2 status

# 2. 端口是否监听
netstat -tlnp | grep 11111

# 3. 防火墙是否允许
firewall-cmd --list-all
```

**解决**:
```bash
# 启动后端
pm2 start timao-backend

# 或重启
pm2 restart timao-backend
```

### 错误 2: 500 Internal Server Error

**原因**: 后端代码出错

**检查**:
```bash
# 查看后端错误日志
pm2 logs timao-backend --err --lines 50
```

**常见原因**:
- 数据库连接失败
- Redis 连接失败
- 代码逻辑错误
- 缺少环境变量

**解决**:
1. 检查数据库连接
2. 检查 Redis 连接
3. 查看错误堆栈
4. 修复代码后重启服务

### 错误 3: 404 Not Found

**原因**: 路由不存在或 Nginx 配置错误

**检查**:
1. 后端是否定义了该路由
2. Nginx proxy_pass 是否正确

**解决**:
```bash
# 测试后端路由
curl http://127.0.0.1:11111/

# 如果后端正常但 Nginx 404，检查配置
nginx -T | grep proxy_pass
```

### 错误 4: 504 Gateway Timeout

**原因**: 后端响应太慢

**解决**: 增加 Nginx 超时设置

```nginx
location / {
    proxy_pass http://127.0.0.1:11111;
    
    # 增加超时时间
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;
}
```

## ✅ 验证配置

### 1. 测试根路径

```bash
curl -I http://129.211.218.135/
```

**预期输出**:
```
HTTP/1.1 200 OK
Server: nginx
Content-Type: application/json
...
```

### 2. 测试健康检查

```bash
curl http://129.211.218.135/health
```

**预期输出**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-13T...",
  "version": "1.0.0"
}
```

### 3. 测试 API 文档

访问浏览器:
```
http://129.211.218.135/docs
```

应该看到 FastAPI 的 Swagger UI 界面。

## 🔄 快速修复命令

```bash
# 1. 重启后端服务
pm2 restart timao-backend

# 2. 重新加载 Nginx
nginx -s reload

# 3. 测试连接
curl http://129.211.218.135/health

# 4. 查看实时日志
pm2 logs timao-backend --lines 0
```

## 📝 调试模式

如果问题依然存在，启用详细日志：

### 后端调试

编辑 `ecosystem.config.js`:
```javascript
module.exports = {
  apps: [{
    name: 'timao-backend',
    script: 'uvicorn',
    args: 'app.main:app --host 0.0.0.0 --port 11111 --log-level debug',
    // ...
  }]
}
```

重启服务：
```bash
pm2 restart timao-backend
pm2 logs timao-backend
```

### Nginx 调试

临时启用调试日志：
```nginx
error_log /www/wwwlogs/timao-error.log debug;
```

重新加载：
```bash
nginx -s reload
tail -f /www/wwwlogs/timao-error.log
```

## 🎯 最终检查清单

- [ ] 后端服务运行正常 (`pm2 status`)
- [ ] 后端端口监听 (`netstat -tlnp | grep 11111`)
- [ ] 本地可以访问后端 (`curl http://127.0.0.1:11111/health`)
- [ ] Nginx 配置正确 (`nginx -t`)
- [ ] Nginx 已重新加载 (`nginx -s reload`)
- [ ] 防火墙允许 80 端口 (`firewall-cmd --list-ports`)
- [ ] 可以访问 `/docs` (`curl http://129.211.218.135/docs`)
- [ ] 可以访问 `/health` (`curl http://129.211.218.135/health`)
- [ ] 可以访问 `/` (`curl http://129.211.218.135/`)

## 📞 获取帮助

如果以上步骤都无法解决问题，请提供：

1. PM2 状态: `pm2 status`
2. 后端日志: `pm2 logs timao-backend --lines 50`
3. Nginx 错误日志: `tail -50 /www/wwwlogs/timao-error.log`
4. 测试输出: `curl -v http://127.0.0.1:11111/`

---

**提猫直播助手团队**

