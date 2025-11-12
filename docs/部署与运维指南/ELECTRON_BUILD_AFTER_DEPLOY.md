# 🚀 后端部署后打包 Electron 应用指南

**遵循：奥卡姆剃刀 + KISS 原则**

> 最简单的打包方案：后端在服务器，Electron 只打包前端

---

## 📋 前提条件

1. ✅ 后端已部署到服务器（如：`http://129.211.218.135:11111`）
2. ✅ 服务器后端正常运行，可通过浏览器访问
3. ✅ 本地有 Node.js 和 Python 环境

---

## 🎯 3步打包流程

### 步骤1：修改配置指向服务器后端

创建 `.env.production` 文件（在项目根目录）：

```bash
# 服务器后端地址（使用你的公网IP）
VITE_FASTAPI_URL=http://129.211.218.135:11111
VITE_STREAMCAP_URL=http://129.211.218.135:11111
VITE_DOUYIN_URL=http://129.211.218.135:11111
```

或者修改 `electron/renderer/.env.production`：

```bash
VITE_FASTAPI_URL=http://129.211.218.135:11111
```

### 步骤2：禁用本地后端启动

修改 `electron/main.js`，注释掉本地后端启动代码：

```javascript
// 找到这段代码（大约在第300行左右）
// 注释掉或删除启动本地后端的代码
/*
async function startBackendServices() {
    // ... 启动本地后端的代码
}
*/

// 或者直接修改，跳过本地服务检查
async function waitForServicesReady() {
    // 如果后端在服务器，直接返回 true
    if (process.env.VITE_FASTAPI_URL && !process.env.VITE_FASTAPI_URL.includes('127.0.0.1')) {
        console.log('[electron] 使用远程后端服务，跳过本地服务检查');
        return true;
    }
    // ... 原有的检查代码
}
```

### 步骤3：打包 Electron 应用

```bash
# 1. 安装依赖（如果还没安装）
npm install

# 2. 构建前端
npm run build:frontend

# 3. 打包 Electron（不需要打包后端）
npm run build:config
```

**Windows 打包：**
```bash
npm run build:win
```

**Mac 打包：**
```bash
npm run build:mac
```

**Linux 打包：**
```bash
npm run build:linux
```

---

## 📦 打包输出

打包完成后，安装包在 `dist/` 目录：

- **Windows**: `TalkingCat-Portable-1.0.0-x64.exe`（便携版）
- **Windows**: `TalkingCat-Setup-1.0.0-x64.exe`（安装版）
- **Mac**: `TalkingCat-1.0.0-x64.dmg`
- **Linux**: `TalkingCat-1.0.0-x64.AppImage`

---

## ⚙️ 简化方案（推荐）

### 方案A：环境变量方式（最简单）

1. 在打包前设置环境变量：
```bash
# Windows (PowerShell)
$env:VITE_FASTAPI_URL="http://129.211.218.135:11111"
npm run build:win

# Linux/Mac
export VITE_FASTAPI_URL="http://129.211.218.135:11111"
npm run build:linux
```

2. 打包后的应用会自动使用服务器后端

### 方案B：修改默认配置（一次修改）

修改 `electron/renderer/src/services/apiConfig.ts`：

```typescript
// 第32行，修改默认地址
baseUrl: import.meta.env?.VITE_FASTAPI_URL || 'http://129.211.218.135:11111',
```

---

## 🔧 修改 build-config.json（可选）

如果不想打包后端代码，修改 `build-config.json`：

```json
{
  "files": [
    "electron/**/*",
    "config.json",
    "package.json",
    "!backend_dist/**/*",  // 排除后端代码
    "!server/**/*"         // 排除服务器代码
  ]
}
```

---

## ✅ 验证打包结果

1. 运行打包后的应用
2. 打开开发者工具（F12）
3. 查看 Network 请求，确认请求的是服务器地址
4. 检查控制台日志，应该看到：
   ```
   ✅ FastAPI主服务 健康检查通过
   ```

---

## 🐛 常见问题

### 问题1：打包后还是连接本地后端

**解决**：检查环境变量是否正确设置，或者直接修改 `apiConfig.ts` 的默认值

### 问题2：CORS 错误

**解决**：确保服务器后端配置了 CORS，允许 Electron 应用访问：
```python
# server/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 问题3：HTTPS 证书错误

**解决**：如果服务器使用自签名证书，需要在 Electron 中禁用证书验证（仅开发环境）

---

## 📝 总结

**最简单的打包流程：**

1. 设置环境变量指向服务器
2. 运行 `npm run build:win`（或其他平台）
3. 分发 `dist/` 目录中的安装包

**不需要：**
- ❌ 打包后端代码
- ❌ 修改复杂的配置
- ❌ 启动本地服务

**只需要：**
- ✅ 修改后端地址（环境变量或配置文件）
- ✅ 打包前端和 Electron 壳

---

## 🎯 原则

- **奥卡姆剃刀**：最简单的方案，最少的配置
- **KISS**：一键打包，自动连接服务器
- **YAGNI**：不打包不需要的后端代码

