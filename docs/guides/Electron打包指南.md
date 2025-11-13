# Electron 前端应用打包指南

**适用场景**：后端已部署到服务器，只需要打包前端 Electron 桌面应用

---

## 📋 前提条件

### 服务器配置
- **系统**：Linux (CentOS/Ubuntu)
- **Node.js**：v16+ (当前: v22.18.0)
- **npm**：v8+ (当前: v10.9.3)
- **内存**：建议 4GB+
- **磁盘**：建议 10GB+ 可用空间

### 后端服务
- ✅ 后端已部署：`http://129.211.218.135:8181`
- ✅ 前端服务：`http://129.211.218.135:10050`
- ✅ 服务正常运行

---

## 🚀 快速打包

### 方式一：使用打包脚本（推荐）

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
./scripts/构建与启动/build-electron-only.sh
```

### 方式二：手动打包

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 1. 构建前端
cd electron/renderer
npm run build
cd ../..

# 2. 打包应用
npx electron-builder --win --x64 --config build-config.json
```

---

## 📦 打包配置说明

### 当前配置（package.json）

```json
{
  "build": {
    "appId": "com.xingjuai.talkingcat",
    "productName": "提猫直播助手",
    "artifactName": "TalkingCat-${version}-${os}-${arch}.${ext}",
    "directories": {
      "output": "dist"
    },
    "files": [
      "electron/**/*",
      "!server/**/*",        // 不包含后端代码
      "!backend_dist/**/*",  // 不包含后端构建
      "!**/__pycache__/**",
      "!**/*.pyc"
    ],
    "win": {
      "target": "portable",
      "icon": "assets/icon.ico",
      "artifactName": "TalkingCat-Portable-${version}-${arch}.exe"
    }
  }
}
```

### 打包内容
- ✅ Electron 主进程代码
- ✅ Electron 渲染进程（前端）
- ✅ package.json 配置
- ❌ 不包含 server/ 后端代码
- ❌ 不包含 backend_dist/ 后端构建

---

## 🔧 后端连接配置

### Electron 应用需要配置后端地址

检查以下文件中的后端地址配置：

#### 1. electron/main.js
```javascript
// 后端服务地址配置
const BACKEND_URL = 'http://129.211.218.135:8181';
const FRONTEND_URL = 'http://129.211.218.135:10050';
```

#### 2. electron/renderer/src/config.js
```javascript
export const API_BASE_URL = 'http://129.211.218.135:8181';
```

#### 3. config.json
```json
{
  "backend": {
    "host": "129.211.218.135",
    "port": 8181
  },
  "frontend": {
    "host": "129.211.218.135",
    "port": 10050
  }
}
```

⚠️ **重要**：打包前确保这些配置正确，否则应用无法连接到后端！

---

## 🔄 版本更新机制

### 应用已包含自动更新检查

根据您的说明，应用已经包含版本更新逻辑。典型实现：

#### 1. 启动时检查更新
```javascript
// electron/main.js
async function checkForUpdates() {
  try {
    const response = await fetch('http://129.211.218.135:8181/api/version/check');
    const data = await response.json();
    
    if (data.hasUpdate) {
      // 提示用户更新
      showUpdateDialog(data.version, data.downloadUrl);
    }
  } catch (error) {
    console.error('检查更新失败:', error);
  }
}
```

#### 2. 版本信息
- **当前版本**：在 `package.json` 中的 `version` 字段
- **更新检查**：连接到后端 `/api/version/check`
- **下载地址**：后端返回新版本的下载链接

---

## 📥 打包输出

### 打包成功后的文件

```bash
dist/
├── TalkingCat-Portable-1.0.0-x64.exe  # Windows 便携版
└── latest.yml                          # 版本信息（可选）
```

### 文件大小
- **典型大小**：50-100MB（取决于依赖）
- **不包含后端**：大小会小很多

---

## 🧪 测试流程

### 1. 下载打包文件

```bash
# 在本地 Windows 机器上下载
scp user@129.211.218.135:/www/wwwroot/wwwroot/timao-douyin-live-manager/dist/*.exe .
```

### 2. 测试应用

1. 在 Windows 上运行 `.exe` 文件
2. 应用启动，检查：
   - ✅ 界面正常显示
   - ✅ 能连接到后端（http://129.211.218.135:8181）
   - ✅ 登录功能正常
   - ✅ 直播录制功能正常
   - ✅ 版本更新检查正常

### 3. 常见问题

#### 问题 1：无法连接后端
```
原因：后端地址配置错误或后端服务未启动
解决：
1. 检查 electron/main.js 中的 BACKEND_URL
2. 确认后端服务运行：curl http://129.211.218.135:8181/health
```

#### 问题 2：白屏或页面加载失败
```
原因：前端构建失败或资源路径错误
解决：
1. 重新构建前端：cd electron/renderer && npm run build
2. 检查 dist 目录是否包含前端文件
```

#### 问题 3：版本更新不工作
```
原因：更新检查接口未实现或配置错误
解决：
1. 检查后端是否有 /api/version/check 接口
2. 查看应用日志确认错误原因
```

---

## 📊 版本管理

### 更新版本号

每次打包前更新版本号：

```bash
# 编辑 package.json
vi package.json

# 修改 version 字段
{
  "version": "1.0.1",  # 从 1.0.0 改为 1.0.1
  ...
}
```

### 版本号规范
- **主版本**：重大功能更新（1.x.x → 2.x.x）
- **次版本**：新功能添加（1.0.x → 1.1.x）
- **补丁版本**：Bug 修复（1.0.0 → 1.0.1）

---

## 🚀 发布流程

### 1. 准备发布

```bash
# 1. 更新版本号
vi package.json

# 2. 构建前端
cd electron/renderer
npm run build
cd ../..

# 3. 打包应用
./scripts/构建与启动/build-electron-only.sh
```

### 2. 上传到服务器

```bash
# 上传到文件服务器或 OSS
# 例如：阿里云 OSS
ossutil cp dist/*.exe oss://your-bucket/releases/
```

### 3. 更新后端版本信息

```bash
# 更新后端 /api/version/check 接口返回的版本信息
# 例如：编辑 server/app/api/version.py
```

### 4. 通知用户

- 用户下次启动应用时会自动检查更新
- 或通过其他渠道通知用户下载新版本

---

## 🛠️ 高级配置

### 自定义打包配置

创建 `build-config.json`：

```json
{
  "appId": "com.xingjuai.talkingcat",
  "productName": "提猫直播助手",
  "directories": {
    "output": "dist"
  },
  "files": [
    "electron/**/*",
    "package.json",
    "!server/**",
    "!backend_dist/**"
  ],
  "win": {
    "target": "portable",
    "icon": "assets/icon.ico"
  },
  "compression": "maximum"  # 最大压缩
}
```

### 打包多平台

```bash
# Windows
npm run build:win

# macOS (需要在 macOS 上运行)
npm run build:mac

# Linux
npm run build:linux
```

---

## 📚 参考资源

- **electron-builder 文档**：https://www.electron.build/
- **Electron 文档**：https://www.electronjs.org/
- **打包最佳实践**：https://www.electron.build/configuration/configuration

---

## ✅ 检查清单

打包前确认：

- [ ] 后端服务正常运行（端口 8181）
- [ ] 前端服务正常运行（端口 10050）
- [ ] 后端地址配置正确
- [ ] 版本号已更新
- [ ] 前端已构建（electron/renderer/dist 存在）
- [ ] electron-builder 已安装
- [ ] 磁盘空间充足（10GB+）

打包后确认：

- [ ] dist/ 目录包含 .exe 文件
- [ ] 文件大小合理（50-100MB）
- [ ] 在 Windows 上测试应用
- [ ] 后端连接正常
- [ ] 所有功能正常工作

---

## 🆘 遇到问题？

### 查看日志
```bash
# 打包日志
tail -f ~/.electron-builder/builder.log

# 应用日志（Windows）
%APPDATA%/提猫直播助手/logs/
```

### 常用命令
```bash
# 清理缓存
npm run clean

# 重新安装依赖
rm -rf node_modules electron/renderer/node_modules
npm install
cd electron/renderer && npm install

# 强制重新打包
rm -rf dist
./scripts/构建与启动/build-electron-only.sh
```

---

**最后更新**：2025-01-10  
**维护者**：叶维哲

