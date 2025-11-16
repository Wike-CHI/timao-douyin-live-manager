# 提猫直播助手 - Electron桌面应用云端连接说明

**文档版本**: v1.0  
**更新日期**: 2025-11-16  
**审查人**: 叶维哲  
**应用类型**: **Electron桌面应用（React + TypeScript + Python FastAPI）**

---

## 🎯 核心架构

```
┌─────────────────────────────────────────────────────────┐
│         Electron 桌面应用（打包成 .exe/.dmg/.AppImage）   │
│  ┌───────────────────────────────────────────────────┐  │
│  │  前端界面（React + TypeScript + Vite）              │  │
│  │  ├─ 登录界面                                        │  │
│  │  ├─ 订阅管理界面                                    │  │
│  │  └─ 直播管理界面                                    │  │
│  └───────────────────────────────────────────────────┘  │
│           │ HTTP请求                │ HTTP请求           │
│           ▼                         ▼                    │
│  ┌─────────────────┐      ┌──────────────────┐         │
│  │  云端API调用     │      │  本地服务调用      │         │
│  │  (必须联网)      │      │  (打包在应用内)    │         │
│  └─────────────────┘      └──────────────────┘         │
│           │                         │                    │
│           │                         │                    │
│  ┌─────────────────┐      ┌──────────────────┐         │
│  │  云端API配置     │      │  本地Python服务    │         │
│  │  (环境变量)      │      │  (端口16000)      │         │
│  └─────────────────┘      └──────────────────┘         │
└─────────────────────────────────────────────────────────┘
           │                         │
           │ HTTP请求                │ localhost:16000
           │ 到服务器IP:80           │ (应用内通信)
           ▼                         ▼
┌─────────────────────┐    ┌──────────────────────┐
│  服务器（云端）       │    │  本地Python进程        │
│  Nginx:80           │    │  ├─ 音频转写(FunASR)  │
│    ↓                │    │  ├─ AI分析(Gemini)    │
│  timao-cloud:15000  │    │  └─ 弹幕拉取(抖音)     │
│  ├─ 用户登录/注册    │    └──────────────────────┘
│  ├─ 订阅管理        │    (随Electron启动/关闭)
│  ├─ 支付处理        │
│  └─ 积分统计        │
└─────────────────────┘
```

---

## 📦 应用组成

### 1. Electron主进程（Node.js）
- **路径**: `electron/main/`
- **功能**: 
  - 创建窗口
  - 启动本地Python服务（端口16000）
  - 管理应用生命周期

### 2. 渲染进程（React + TypeScript）
- **路径**: `admin-dashboard/src/`
- **功能**: 
  - 用户界面
  - HTTP API调用（云端+本地）

### 3. 本地Python服务（FastAPI）
- **端口**: 16000
- **打包**: 随Electron一起打包
- **功能**: 音频转写、AI分析、弹幕拉取

### 4. 云端Python服务（FastAPI）
- **端口**: 15000（Nginx代理到80）
- **部署**: 独立服务器
- **功能**: 用户、订阅、支付、积分

---

## 🔌 Electron应用如何连接云端

### 方式1：环境变量配置（打包时）

**文件**: `admin-dashboard/.env.production`

```env
# 云端API地址（构建时注入）
VITE_API_BASE_URL=http://129.211.218.135

# 或使用域名（待备案）
# VITE_API_BASE_URL=https://api.timao.com
```

**前端代码中使用**:
```typescript
// src/services/api.ts
const CLOUD_API_BASE = import.meta.env.VITE_API_BASE_URL;

export async function login(username: string, password: string) {
  const response = await fetch(`${CLOUD_API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  return response.json();
}
```

### 方式2：运行时配置（用户可修改）

**Electron配置文件**: `config.json`（放在用户数据目录）

```json
{
  "cloudApiUrl": "http://129.211.218.135",
  "localApiUrl": "http://localhost:16000"
}
```

**Electron主进程读取**:
```typescript
// electron/main/config.ts
import { app } from 'electron';
import * as fs from 'fs';
import * as path from 'path';

const configPath = path.join(app.getPath('userData'), 'config.json');

export function getConfig() {
  if (fs.existsSync(configPath)) {
    return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
  }
  return {
    cloudApiUrl: 'http://129.211.218.135',
    localApiUrl: 'http://localhost:16000'
  };
}
```

---

## 🔐 Nginx配置说明

### 为什么需要Nginx？

Electron桌面应用通过HTTP请求连接云端服务：
```
Electron桌面应用 
  → HTTP请求到 http://服务器IP:80
    → Nginx反向代理
      → FastAPI云端服务 (localhost:15000)
```

### Nginx配置要点

```nginx
server {
    listen 80;
    server_name 129.211.218.135;  # 服务器IP
    
    # 只代理API请求，不托管静态文件
    # 因为静态文件已打包在Electron应用中
    
    location / {
        proxy_pass http://127.0.0.1:15000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**关键点**：
- ❌ 不需要配置 `root` 指向前端构建目录（因为前端在Electron中）
- ❌ 不需要配置 `try_files` 处理SPA路由（因为不是Web应用）
- ✅ 只需要反向代理API请求

---

## 🚀 部署流程

### 步骤1：部署云端服务

```bash
# 在服务器上
cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 1. 启动云端服务
pm2 start ecosystem.cloud.config.js

# 2. 配置Nginx
sudo ./scripts/setup_nginx_cloud.sh

# 3. 验证
curl http://localhost/health
```

### 步骤2：配置Electron应用

```bash
# 在开发机上
cd /www/wwwroot/wwwroot/timao-douyin-live-manager/admin-dashboard

# 1. 修改环境变量
echo "VITE_API_BASE_URL=http://服务器IP" > .env.production

# 2. 构建前端
npm run build

# 3. 打包Electron应用
cd ..
npm run package
```

### 步骤3：分发桌面应用

```bash
# 打包后的文件位置
out/
├── make/
│   ├── zip/       # Windows .zip
│   ├── dmg/       # macOS .dmg
│   └── deb/       # Linux .deb
```

**用户安装后**：
1. 双击安装应用
2. 应用自动启动本地Python服务（16000）
3. 前端通过HTTP连接云端（80）和本地（16000）

---

## 🔧 Electron中的API调用

### API路由分发

**文件**: `admin-dashboard/src/services/api-config.ts`

```typescript
// API基础地址配置
const CLOUD_API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:15000';
const LOCAL_API_BASE = 'http://localhost:16000';

// API路由分发
export function getApiUrl(endpoint: string): string {
  // 云端API（需要联网）
  if (endpoint.startsWith('/api/auth/') ||
      endpoint.startsWith('/profile/') ||
      endpoint.startsWith('/api/subscription/') ||
      endpoint.startsWith('/api/payment/')) {
    return CLOUD_API_BASE + endpoint;
  }
  
  // 本地API（离线可用）
  if (endpoint.startsWith('/api/transcribe/') ||
      endpoint.startsWith('/api/ai/') ||
      endpoint.startsWith('/api/douyin/') ||
      endpoint.startsWith('/api/live/')) {
    return LOCAL_API_BASE + endpoint;
  }
  
  throw new Error(`Unknown API endpoint: ${endpoint}`);
}

// 使用示例
export async function login(username: string, password: string) {
  const url = getApiUrl('/api/auth/login');
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  return response.json();
}

export async function startTranscription(sessionId: number) {
  const url = getApiUrl('/api/transcribe/stream/start');
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId })
  });
  return response.json();
}
```

---

## ⚠️ 重要说明

### 1. 这是桌面应用，不是Web应用

| 特性 | Web应用 | Electron桌面应用（本项目） |
|------|---------|---------------------------|
| 访问方式 | 浏览器打开URL | 双击安装的应用 |
| 前端托管 | Nginx托管静态文件 | ❌ 打包在应用内 |
| 后端连接 | 同域或CORS | HTTP请求到服务器IP |
| 本地服务 | ❌ 无法运行Python | ✅ 打包并随应用启动 |
| 分发方式 | 部署到服务器 | .exe/.dmg/.AppImage |
| 更新方式 | 刷新页面 | 下载新版本安装 |

### 2. Nginx只负责反向代理

```
❌ 错误理解：Nginx托管前端静态文件，用户通过浏览器访问
✅ 正确理解：Nginx只代理API，用户运行本地安装的桌面应用
```

### 3. 两个Python服务

| 服务 | 位置 | 端口 | 功能 | 启动方式 |
|------|------|------|------|---------|
| 云端服务 | 服务器 | 15000 (Nginx:80) | 用户/订阅/支付 | PM2管理 |
| 本地服务 | 用户电脑 | 16000 | 音频/AI/弹幕 | Electron启动 |

---

## 🧪 测试流程

### 1. 测试云端服务

```bash
# 在服务器上
curl http://localhost:15000/health
curl http://localhost/health
curl http://服务器IP/health
```

### 2. 测试Electron应用

**开发模式**:
```bash
# 启动本地Python服务（模拟）
cd server
python -m uvicorn local.main:app --port 16000

# 启动Electron
npm run dev
```

**生产模式**:
```bash
# 打包应用
npm run package

# 运行打包后的应用
./out/make/...
```

### 3. 测试API连接

**在Electron控制台**:
```javascript
// 测试云端连接
fetch('http://服务器IP/health').then(r => r.json()).then(console.log)

// 测试本地连接
fetch('http://localhost:16000/health').then(r => r.json()).then(console.log)
```

---

## 🔍 故障排查

### 问题1：Electron无法连接云端

**现象**：登录时报错"网络错误"

**排查**:
```bash
# 1. 检查云端服务
pm2 status timao-cloud

# 2. 检查Nginx
curl http://服务器IP/health

# 3. 检查防火墙
sudo ufw status
sudo ufw allow 80/tcp

# 4. 检查Electron配置
console.log(import.meta.env.VITE_API_BASE_URL)
```

### 问题2：本地服务未启动

**现象**：音频转写无法使用

**排查**:
```bash
# 检查16000端口
netstat -ano | findstr 16000  # Windows
lsof -i :16000  # macOS/Linux

# 检查Electron主进程日志
```

### 问题3：打包后API地址错误

**现象**：打包后的应用连接错误的服务器

**原因**：`.env.production` 配置错误

**解决**:
```bash
# 重新配置
echo "VITE_API_BASE_URL=http://正确的服务器IP" > admin-dashboard/.env.production

# 重新构建
npm run build
npm run package
```

---

## 📦 Electron打包配置

**文件**: `forge.config.ts`

```typescript
export default {
  packagerConfig: {
    // Electron打包配置
    name: '提猫直播助手',
    executableName: 'timao-live-manager',
    icon: './assets/icon',
    
    // 打包Python运行时（如果需要）
    extraResource: [
      './python-runtime',  // Python精简环境
      './server/local'     // 本地服务代码
    ]
  },
  makers: [
    {
      name: '@electron-forge/maker-zip',
      platforms: ['win32', 'darwin', 'linux']
    }
  ]
};
```

---

## 📞 技术支持

**代码审查人**: 叶维哲

**关键文件**:
- Nginx配置: `nginx-cloud.conf`
- PM2配置: `ecosystem.cloud.config.js`
- Electron主进程: `electron/main/index.ts`
- API配置: `admin-dashboard/src/services/api-config.ts`

**部署文档**:
- `docs/部署文档/云端服务部署指南.md`
- `云端部署快速指南.md`

---

## ✅ 核心要点总结

1. **这是Electron桌面应用**，不是Web应用
2. **Nginx只代理API**，不托管静态文件
3. **有两个Python服务**：云端（服务器）+ 本地（应用内）
4. **客户端通过HTTP请求**连接云端API（需要联网）
5. **本地服务随Electron启动**，运行在localhost:16000
6. **前端打包在Electron中**，不需要Nginx托管

🎯 **部署目标**：用户双击安装的桌面应用，应用连接到云端服务器的API。

