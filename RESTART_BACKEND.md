# ⚠️ 重要：必须重启后端服务！

## CORS问题修复说明

CORS配置已经更新，但**必须重启后端服务才能生效**。

### 问题原因
1. **CORS配置已更新** - 已在 `server/app/main.py` 中正确配置
2. **但服务未重启** - 旧的CORS配置仍在内存中运行
3. **浏览器预检请求失败** - OPTIONS请求没有得到正确的CORS响应头

### 解决步骤

#### 1. 停止当前后端服务
- 在运行后端的终端窗口按 `Ctrl+C`
- 或关闭运行后端的终端窗口

#### 2. 重新启动后端服务

**方法A: 使用 uvicorn（推荐）**
```powershell
# 激活虚拟环境（如果使用）
.venv\Scripts\Activate.ps1

# 启动服务
uvicorn server.app.main:app --reload --port 9019
```

**方法B: 使用你原来的启动方式**
```powershell
# 使用你原来启动后端服务的命令
# 例如: python -m server.app.main 或其他方式
```

#### 3. 等待服务完全启动
看到类似以下日志说明启动成功：
```
INFO:     Uvicorn running on http://127.0.0.1:9019
INFO:     Application startup complete.
```

#### 4. 验证CORS配置

打开浏览器开发者工具（F12）：
1. 访问 http://localhost:3000
2. 尝试登录
3. 在 Network 标签查看 `/api/auth/login` 请求：
   - 应该先有一个 `OPTIONS` 预检请求（状态码 200）
   - 响应头应包含 `Access-Control-Allow-Origin: http://localhost:3000`
   - 然后才是实际的 `POST` 请求

### 管理员账号信息

- **用户名**: `admin`
- **邮箱**: `admin@timao.com`
- **密码**: `admin123456`

### 常见问题

#### Q: 重启后仍然有CORS错误？
A: 检查以下几点：
1. 确认服务真的重启了（查看启动日志中的时间戳）
2. 清除浏览器缓存并强制刷新（Ctrl+Shift+R）
3. 检查后端日志，确认没有错误

#### Q: 如何确认CORS配置已生效？
A: 
1. 在浏览器Network标签查看OPTIONS请求的响应头
2. 应该看到 `Access-Control-Allow-Origin` 头

#### Q: 还是不行怎么办？
A: 
1. 检查后端服务是否真的在运行：访问 http://127.0.0.1:9019/docs 看Swagger文档是否可用
2. 检查端口是否正确：确认后端运行在9019端口
3. 查看后端控制台日志，看是否有错误信息

---

**重要提示**: CORS中间件必须在所有路由之前注册，当前配置已经正确设置。只需要重启服务即可！

