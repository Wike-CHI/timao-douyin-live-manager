# CORS问题诊断和修复指南

## 🔍 问题诊断

CORS错误 "No 'Access-Control-Allow-Origin' header is present" 通常有以下几个原因：

### 1. 后端服务未重启 ⚠️ 最常见原因

**解决方案：必须重启后端服务**

```powershell
# 停止当前服务（Ctrl+C）
# 然后重新启动
uvicorn server.app.main:app --reload --port 9019
```

### 2. 检查CORS配置是否正确加载

启动后端后，检查日志中是否有：
- `✅ 路由已加载: 用户认证`
- `✅ 路由已加载: 管理员`

### 3. 测试CORS配置

打开浏览器控制台，运行：

```javascript
fetch('http://127.0.0.1:9019/api/cors-test', {
  method: 'GET',
  headers: {
    'Origin': 'http://localhost:3000'
  }
})
.then(r => r.json())
.then(console.log)
.catch(console.error)
```

如果返回 `origin_allowed: true`，说明CORS配置正常。

### 4. 检查OPTIONS预检请求

在浏览器Network标签中：
1. 尝试登录
2. 查找 `OPTIONS /api/auth/login` 请求
3. 检查响应头：
   - `Access-Control-Allow-Origin` 应该存在
   - 值应该是 `http://localhost:3000`

### 5. 验证后端服务运行状态

访问：http://127.0.0.1:9019/docs
- 如果能看到Swagger文档，说明服务正常运行
- 如果无法访问，说明服务未启动或端口不对

## 🔧 已修复的内容

1. ✅ **CORS配置已更新** - 包含 `localhost:3000`
2. ✅ **管理员路由前缀已修复** - `/admin` → `/api/admin`
3. ✅ **OPTIONS请求头已优化** - 包含所有必需的请求头
4. ✅ **登录响应token字段已兼容** - 支持 `access_token` 和 `token`

## 📋 验证清单

在尝试登录前，请确认：

- [ ] 后端服务已重启
- [ ] 后端服务正在运行（端口9019）
- [ ] 浏览器控制台没有其他错误
- [ ] Network标签可以看到OPTIONS请求
- [ ] OPTIONS请求返回200状态码

## 🚀 重启后端服务（重要！）

### Windows PowerShell

```powershell
# 1. 停止当前服务（在运行后端的终端按 Ctrl+C）

# 2. 激活虚拟环境（如果使用）
.venv\Scripts\Activate.ps1

# 3. 启动服务
uvicorn server.app.main:app --reload --port 9019
```

### 验证服务启动

看到以下日志说明启动成功：
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:9019 (Press CTRL+C to quit)
```

### 测试CORS

访问：http://127.0.0.1:9019/api/cors-test

应该返回JSON，包含 `origin_allowed: true`

---

**如果重启后仍然有问题**，请提供：
1. 后端启动日志（是否有错误）
2. 浏览器Network标签中OPTIONS请求的响应头
3. 后端是否在9019端口运行

