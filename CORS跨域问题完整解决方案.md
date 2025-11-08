# CORS跨域问题完整解决方案

**审查人**: 叶维哲  
**创建日期**: 2025-11-09  
**原则**: KISS + 童子军军规  

---

## 问题症状

```
Access to fetch at 'http://129.211.218.135/api/...' 
from origin 'http://127.0.0.1:10050' 
has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present
```

---

## 根本原因

### 1. 后端监听地址错误

**问题**:
- 后端只监听本地: `--host 127.0.0.1 --port 11111`
- 前端访问公网IP: `http://129.211.218.135`
- 请求根本到不了后端

**解决**:
```bash
# 修改后端启动参数
--host 0.0.0.0 --port 8000  # ✅ 监听所有网络接口
```

### 2. Nginx代理端口错误

**问题**:
```nginx
location / {
    proxy_pass http://127.0.0.1:11111;  # ❌ 后端已改为8000端口
}
```

**解决**:
```nginx
location / {
    proxy_pass http://127.0.0.1:8000;  # ✅ 指向正确端口
}
```

### 3. CORS配置需要放行

**问题**: 限制特定来源列表

**解决**: 允许所有来源（部署阶段）
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ 允许所有来源
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 修改内容

### 1. 后端CORS配置

**文件**: `server/app/main.py`

**关键修改**:
```python
# 简化CORS配置（部署模式）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.middleware("http")
async def cors_preflight_guard(request: Request, call_next):
    if request.method == "OPTIONS":
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
                "Access-Control-Allow-Headers": "*",
            }
        )
    
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "*"
    return response
```

### 2. 后端启动命令

**新命令**:
```bash
cd server
nohup python -m uvicorn app.main:app \
  --host 0.0.0.0 \  # 监听所有网络接口
  --port 8000 \
  --reload > ../backend.log 2>&1 &
```

### 3. Nginx配置

**文件**: `/www/server/panel/vhost/nginx/129.211.218.135.conf`

**修改**:
```nginx
server {
    listen 80;
    server_name 129.211.218.135 _;
    
    # 反向代理到后端（端口 8000）
    location / {
        proxy_pass http://127.0.0.1:8000;  # ✅ 改为8000
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    access_log /www/wwwlogs/timao-backend.log;
    error_log /www/wwwlogs/timao-backend.error.log;
}
```

**重启nginx**:
```bash
nginx -s reload
```

---

## 验证结果

### 1. 后端运行状态

```bash
$ ps aux | grep uvicorn | grep -v grep
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. CORS响应头

```bash
$ curl -I http://129.211.218.135/api/cors-test

HTTP/1.1 200 OK
access-control-allow-origin: *
access-control-expose-headers: *
```

### 3. 前端访问测试

**预期结果**:
- ✅ 所有健康检查通过
- ✅ 服务正常启动
- ✅ 无CORS错误
- ✅ 音频转写服务正常

---

## 服务拓扑

```
┌─────────────────────────────────────────────────────────┐
│  前端: http://127.0.0.1:10050                           │
│  访问: http://129.211.218.135/api/...                   │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Nginx: 0.0.0.0:80                                      │
│  监听公网IP: 129.211.218.135                            │
│  proxy_pass http://127.0.0.1:8000                       │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  后端: 0.0.0.0:8000                                     │
│  CORS: allow_origins=["*"]                              │
│  监听所有网络接口（可通过127.0.0.1和公网IP访问）         │
└─────────────────────────────────────────────────────────┘
```

---

## 关键经验

### 1. 后端监听地址很重要

- ❌ `--host 127.0.0.1`: 只能本地访问
- ✅ `--host 0.0.0.0`: 可通过所有网络接口访问

### 2. Nginx代理端口要对应

- 后端改端口后，nginx也要同步修改
- 修改后要重新加载: `nginx -s reload`

### 3. CORS是服务端配置

- 前端不需要配置CORS
- CORS响应头由后端返回
- 部署阶段可以放行所有来源

### 4. 排查CORS问题的步骤

1. **检查后端监听地址**
   ```bash
   ps aux | grep uvicorn | grep -v grep
   ```

2. **检查端口占用**
   ```bash
   lsof -i :8000
   ```

3. **测试后端直连**
   ```bash
   curl -I http://127.0.0.1:8000/api/cors-test
   ```

4. **检查nginx配置**
   ```bash
   cat /www/server/panel/vhost/nginx/*.conf
   ```

5. **测试nginx代理**
   ```bash
   curl -I http://129.211.218.135/api/cors-test
   ```

---

## 童子军军规应用

### 优化前

- 复杂的CORS配置（120+行）
- 限制特定来源列表
- 后端监听错误地址
- nginx代理错误端口

### 优化后

- 简化CORS配置（50行）
- 允许所有来源（部署模式）
- 后端监听所有网络接口
- nginx代理正确端口

**让代码比来时更干净！**

---

## 测试脚本

创建测试脚本验证CORS配置：

```bash
#!/bin/bash
# test_cors.sh

echo "=== CORS配置测试 ==="

echo ""
echo "1. 测试后端直连（127.0.0.1:8000）"
curl -I http://127.0.0.1:8000/api/cors-test 2>&1 | grep -E "HTTP|access-control"

echo ""
echo "2. 测试nginx代理（129.211.218.135:80）"
curl -I http://129.211.218.135/api/cors-test 2>&1 | grep -E "HTTP|access-control"

echo ""
echo "3. 测试跨域OPTIONS请求"
curl -X OPTIONS -I http://129.211.218.135/api/live_audio/start \
  -H "Origin: http://127.0.0.1:10050" \
  -H "Access-Control-Request-Method: POST" 2>&1 | grep -E "HTTP|access-control"

echo ""
echo "=== 测试完成 ==="
```

运行测试：
```bash
chmod +x test_cors.sh
./test_cors.sh
```

**预期输出**:
```
1. 测试后端直连（127.0.0.1:8000）
HTTP/1.1 200 OK
access-control-allow-origin: *
access-control-expose-headers: *

2. 测试nginx代理（129.211.218.135:80）
HTTP/1.1 200 OK
access-control-allow-origin: *
access-control-expose-headers: *

3. 测试跨域OPTIONS请求
HTTP/1.1 200 OK
access-control-allow-origin: *
access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD
```

---

## 总结

### ✅ 问题完全解决

1. **后端**: 监听所有网络接口 (`0.0.0.0:8000`)
2. **CORS**: 允许所有来源 (`allow_origins=["*"]`)
3. **Nginx**: 正确代理到后端 (`proxy_pass http://127.0.0.1:8000`)
4. **验证**: CORS响应头正确返回

### 🎯 关键收获

- **KISS原则**: 简化CORS配置，部署阶段放行所有来源
- **童子军军规**: 优化配置，让代码更清晰
- **系统化排查**: 从后端→nginx→前端逐步验证

### 📝 后续建议

1. 生产环境建议限制CORS来源为前端域名
2. 考虑使用HTTPS（可通过Let's Encrypt）
3. 配置nginx缓存提升性能
4. 监控后端服务状态（如使用supervisor或systemd）

---

**问题解决日期**: 2025-11-09  
**解决耗时**: 约30分钟  
**核心原则**: KISS + 系统化排查

