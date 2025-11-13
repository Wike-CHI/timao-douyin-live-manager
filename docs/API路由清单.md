# API 路由清单

## 📋 所有后端 API 路由

根据后端代码分析，以下是所有已注册的 API 路由前缀：

### ✅ 已在 Nginx 配置中覆盖的路由

#### 1. 通用 API 路由 (location /api/)
以下所有路由都被 `location /api/` 配置覆盖：

| 路由前缀 | 功能 | 文件 |
|---------|------|------|
| `/api/admin` | 管理员功能 | admin.py |
| `/api/ai` | AI 测试 | ai_test.py |
| `/api/ai_gateway` | AI 网关管理 | ai_gateway_api.py |
| `/api/ai/live` | AI 实时分析 | ai_live.py |
| `/api/ai/scripts` | AI 话术生成 | ai_scripts.py |
| `/api/ai_usage` | AI 使用监控 | ai_usage.py |
| `/api/auth` | 用户认证 | auth.py |
| `/api/bootstrap` | 资源自检 | bootstrap.py |
| `/api/douyin` | 抖音 API | douyin.py |
| `/api/douyin/web` | 抖音 Web 测试 | douyin_web.py |
| `/api/live` | 直播评论管理 | live_comments.py |
| `/api/live_audio` | 直播音频转写 | live_audio.py |
| `/api/live/review` | 直播复盘分析 | live_review.py |
| `/api/live_session` | 统一会话管理 | live_session.py |
| `/api/live-test` | 联合测试 | live_test.py |
| `/api/nlp` | NLP 管理 | nlp_hotwords.py |
| `/api/report/live` | 直播复盘 | live_report.py |
| `/api/subscription` | 订阅管理 | subscription.py |
| `/api/tools` | 工具 | tools.py |

#### 2. 独立 API 路由（单独配置）

| 路由前缀 | 功能 | Nginx 配置 |
|---------|------|-----------|
| `/audit` | 审计日志 | `location /audit` |
| `/permission` | 权限管理 | `location /permission` |
| `/profile` | 用户配置文件 | `location /profile` |

#### 3. 系统路由

| 路由 | 功能 | Nginx 配置 |
|-----|------|-----------|
| `/` | 根路径 | `location /` |
| `/health` | 健康检查 | `location /health` |
| `/docs` | FastAPI 文档 | `location /docs` |
| `/redoc` | ReDoc 文档 | `location /redoc` |
| `/openapi.json` | OpenAPI 规范 | `location /openapi.json` |

#### 4. 静态资源

| 路由 | 功能 | Nginx 配置 |
|-----|------|-----------|
| `/static/` | 静态文件 | `location /static/` |

## 🔧 Nginx 配置覆盖情况

### ✅ 完全覆盖

所有 **24 个** API 路由前缀都已在 Nginx 配置中正确设置：

```nginx
# 1. 通用 API 路由 (覆盖 19 个 /api/* 路由)
location /api/ {
    proxy_pass http://127.0.0.1:11111;
    # ... 配置
}

# 2. 独立路由 (3 个)
location /audit { ... }
location /permission { ... }
location /profile { ... }

# 3. 系统路由 (5 个)
location / { ... }
location /health { ... }
location /docs { ... }
location /redoc { ... }
location /openapi.json { ... }

# 4. 静态资源
location /static/ { ... }
```

### 📊 统计

- **API 路由总数**: 24 个
- **Nginx 配置覆盖**: ✅ 100%
- **通用配置覆盖**: 19 个 (`/api/*`)
- **独立配置**: 3 个 (`/audit`, `/permission`, `/profile`)
- **系统路由**: 5 个
- **静态资源**: 1 个

## 🧪 测试方法

### 1. 测试通用 API 路由

```bash
# 测试认证 API
curl http://129.211.218.135/api/auth/login

# 测试 AI API
curl http://129.211.218.135/api/ai/health

# 测试抖音 API
curl http://129.211.218.135/api/douyin/health
```

### 2. 测试独立路由

```bash
# 测试审计日志
curl http://129.211.218.135/audit

# 测试权限管理
curl http://129.211.218.135/permission

# 测试用户配置
curl http://129.211.218.135/profile
```

### 3. 测试系统路由

```bash
# 测试根路径
curl http://129.211.218.135/

# 测试健康检查
curl http://129.211.218.135/health

# 测试文档
curl http://129.211.218.135/docs
```

## 📝 API 功能说明

### 核心业务 API

| 类别 | API | 说明 |
|------|-----|------|
| **直播管理** | `/api/live_audio` | 直播音频实时转写 |
| | `/api/live_session` | 直播会话管理 |
| | `/api/live/review` | 直播复盘分析 |
| | `/api/report/live` | 直播复盘报告 |
| **AI 功能** | `/api/ai/live` | AI 实时分析 |
| | `/api/ai/scripts` | AI 话术生成 |
| | `/api/ai_gateway` | AI 网关管理 |
| | `/api/ai_usage` | AI 使用监控 |
| **抖音集成** | `/api/douyin` | 抖音 API 集成 |
| | `/api/douyin/web` | 抖音 Web 爬取 |
| **用户管理** | `/api/auth` | 用户认证登录 |
| | `/api/subscription` | 订阅付费管理 |
| | `/api/admin` | 管理员功能 |
| **辅助功能** | `/api/nlp` | NLP 热词分析 |
| | `/api/tools` | 工具函数 |
| | `/api/bootstrap` | 系统自检 |

### 权限相关 API

| API | 说明 |
|-----|------|
| `/permission` | 权限管理 |
| `/audit` | 操作审计日志 |
| `/profile` | 用户配置文件 |

## ⚙️ 特殊配置

### WebSocket 支持

所有 `/api/` 路由都配置了 WebSocket 支持：

```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

### 长轮询超时

API 路由的超时设置为 300 秒，支持长轮询：

```nginx
proxy_read_timeout 300s;
proxy_send_timeout 300s;
```

### CORS 支持

后端已配置 CORS，允许跨域请求：
- 测试端点: `/api/cors-test`
- 支持所有 API 路由

## 🔒 安全建议

1. **生产环境应启用 HTTPS**
   - 保护用户数据传输
   - 避免中间人攻击

2. **限制敏感 API 访问**
   ```nginx
   location /api/admin {
       # 限制 IP 访问
       allow 192.168.1.0/24;
       deny all;
       proxy_pass http://127.0.0.1:11111;
   }
   ```

3. **添加速率限制**
   ```nginx
   limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
   
   location /api/ {
       limit_req zone=api_limit burst=20;
       proxy_pass http://127.0.0.1:11111;
   }
   ```

## 📚 相关文档

- [Nginx配置故障排查.md](./Nginx配置故障排查.md)
- [宝塔部署实战-公网IP版.md](./宝塔部署实战-公网IP版.md)
- [PM2部署教程.md](./PM2部署教程.md)

## 🎉 总结

✅ **所有 24 个后端 API 路由都已在 Nginx 配置中完整覆盖**

配置文件位置: `nginx-config-baota.conf`

使用方法:
1. 复制配置内容
2. 粘贴到宝塔面板站点配置
3. 保存并重新加载 Nginx
4. 测试所有 API 路由

---

**提猫直播助手团队**

