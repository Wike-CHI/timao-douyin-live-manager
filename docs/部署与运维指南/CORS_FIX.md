# CORS 跨域问题修复说明

## 问题描述

访问 AI 使用监控页面时出现 CORS 跨域错误：

```
Access to fetch at 'http://127.0.0.1:10090/api/ai_usage/dashboard' 
from origin 'http://localhost:10090' has been blocked by CORS policy
```

## 原因分析

1. **不同源视为跨域**
   - `http://localhost:10090` 和 `http://127.0.0.1:10090` 在浏览器中被视为不同的源
   - CORS 策略只允许了部分源，导致跨域请求被拦截

2. **硬编码 API 地址**
   - HTML 文件中硬编码了 `API_BASE = 'http://127.0.0.1:10090'`
   - 当页面从 `http://localhost:10090` 访问时，就会触发跨域

## 解决方案

### 1. 更新 CORS 配置

在 `server/app/main.py` 中添加更多允许的源：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:30013",
        "http://localhost:30013",
        "http://127.0.0.1:10090",
        "http://localhost:10090",
        "http://127.0.0.1:8090",    # 兼容旧端口
        "http://localhost:8090",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],  # 新增：允许前端访问所有响应头
)
```

### 2. 使用动态 API 地址

修改前端 HTML 文件，使用 `window.location.origin` 动态获取 API 地址：

**修改前**：
```javascript
const API_BASE = 'http://127.0.0.1:10090';
```

**修改后**：
```javascript
// 动态获取 API 基础 URL，解决 CORS 问题
const API_BASE = window.location.origin;
```

## 已修复的文件

1. ✅ `server/app/main.py` - CORS 配置更新
2. ✅ `frontend/ai_usage_monitor.html` - 使用动态 API 地址
3. ✅ `frontend/ai_gateway_manager.html` - 使用动态 API 地址

## 验证步骤

### 1. 重启后端服务

```bash
# 如果服务正在运行，先停止
# 然后重新启动
npm run dev
```

或仅重启 FastAPI：

```bash
uvicorn server.app.main:app --reload --host 127.0.0.1 --port 10090
```

### 2. 测试访问

**测试 AI 使用监控**：
```
http://localhost:10090/static/ai_usage_monitor.html
```

**测试 AI 网关管理**：
```
http://localhost:10090/static/ai_gateway_manager.html
```

### 3. 检查浏览器控制台

打开浏览器开发者工具（F12），查看：
- ✅ 没有 CORS 错误
- ✅ API 请求成功
- ✅ 数据正常显示

## 最佳实践

### 前端 API 调用

使用相对路径或动态获取 API 地址：

```javascript
// ✅ 推荐：使用 window.location.origin
const API_BASE = window.location.origin;

// ✅ 推荐：使用相对路径
fetch('/api/ai_usage/dashboard')

// ❌ 不推荐：硬编码 IP 和端口
const API_BASE = 'http://127.0.0.1:10090';
```

### 开发环境访问

统一使用以下方式访问：

**推荐**（使用 localhost）：
- 前端：http://localhost:30013
- 后端：http://localhost:10090

或全部使用 127.0.0.1：
- 前端：http://127.0.0.1:30013
- 后端：http://127.0.0.1:10090

**不推荐混用**：
- ❌ 前端用 localhost，API 用 127.0.0.1
- ❌ 前端用 127.0.0.1，API 用 localhost

## 其他注意事项

### 1. 生产环境配置

生产环境需要限制允许的源：

```python
# 生产环境示例
if os.getenv("ENV") == "production":
    allow_origins = [
        "https://yourdomain.com",
        "https://www.yourdomain.com",
    ]
else:
    allow_origins = [
        "http://127.0.0.1:30013",
        "http://localhost:30013",
        # ... 其他开发环境源
    ]
```

### 2. 预检请求（OPTIONS）

确保 CORS 配置包含 OPTIONS 方法：

```python
allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
```

### 3. 跨域携带凭证

如果需要携带 Cookie 或认证信息：

```python
allow_credentials=True
```

前端也需要配置：

```javascript
fetch(url, {
    credentials: 'include'  // 携带 Cookie
})
```

## 常见问题

### Q1: 修改后仍然报 CORS 错误？

**A**: 清除浏览器缓存或使用无痕模式测试：
```
Ctrl + Shift + Del（清除缓存）
或
Ctrl + Shift + N（无痕模式）
```

### Q2: localhost 和 127.0.0.1 有什么区别？

**A**: 
- `localhost` 是域名，会通过 DNS 解析到 `127.0.0.1`
- `127.0.0.1` 是 IP 地址
- 在浏览器的同源策略中，它们被视为**不同的源**

### Q3: 为什么要添加 `expose_headers`？

**A**: 允许前端 JavaScript 访问响应头中的自定义字段，例如：
- 分页信息（X-Total-Count）
- 认证令牌（X-Auth-Token）

### Q4: 能否使用通配符 `*` 允许所有源？

**A**: 
- 开发环境可以，但**不建议**
- 生产环境**严禁**使用 `allow_origins=["*"]`
- 如果 `allow_credentials=True`，则不能使用 `*`

```python
# ❌ 错误配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # 与 * 冲突！
)

# ✅ 正确配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:10090",
        "http://127.0.0.1:10090",
    ],
    allow_credentials=True,
)
```

## 总结

✅ **已修复**：
- CORS 配置更新，支持 localhost 和 127.0.0.1
- 前端页面使用动态 API 地址
- 添加 `expose_headers` 配置

🎯 **效果**：
- AI 使用监控页面正常访问
- AI 网关管理页面正常访问
- 无 CORS 跨域错误

---

**修复日期**: 2025-10-26  
**影响范围**: 所有静态 HTML 管理页面  
**测试状态**: ✅ 已验证
