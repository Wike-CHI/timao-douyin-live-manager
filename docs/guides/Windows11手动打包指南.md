# Windows 11 手动打包指南

**审查人**: 叶维哲  
**创建时间**: 2025-01-15  
**适用系统**: Windows 11

---

## 🚀 最快方式（推荐）

**最简单的方法**：双击运行 `scripts/构建与启动/build-local.bat` 文件！

这个批处理脚本会自动完成所有步骤，包括：
- ✅ 设置环境变量
- ✅ 安装依赖
- ✅ 构建前端
- ✅ 打包Electron应用

**预计时间**: 11-23分钟（首次），5-10分钟（后续）

---

## 📋 前置要求

### 1. 安装必要软件

- ✅ **Node.js** (>=16.0.0) - [下载地址](https://nodejs.org/)
- ✅ **Python** (>=3.8) - [下载地址](https://www.python.org/)
- ✅ **Git** (可选，用于克隆代码) - [下载地址](https://git-scm.com/)

### 2. 验证安装

打开 **PowerShell** 或 **命令提示符**，运行：

```powershell
# 检查Node.js版本
node --version

# 检查npm版本
npm --version

# 检查Python版本
python --version
```

---

## 🚀 手动打包步骤

### 步骤1: 打开项目目录

```powershell
# 打开PowerShell，切换到项目目录
cd D:\path\to\timao-douyin-live-manager
```

### 步骤2: 安装根目录依赖

```powershell
# 安装Node.js依赖
npm install
```

**预计时间**: 2-5分钟

### 步骤3: 安装前端依赖

```powershell
# 进入前端目录
cd electron\renderer

# 安装前端依赖
npm install

# 返回根目录
cd ..\..
```

**预计时间**: 3-5分钟

### 步骤4: 设置环境变量

在PowerShell中设置环境变量（仅当前会话有效）：

```powershell
# 设置后端服务器地址
$env:VITE_FASTAPI_URL = "http://129.211.218.135:10050"
$env:VITE_STREAMCAP_URL = "http://129.211.218.135:10050"
$env:VITE_DOUYIN_URL = "http://129.211.218.135:10050"
$env:ELECTRON_START_API = "false"

# 验证环境变量（可选）
echo "后端地址: $env:VITE_FASTAPI_URL"
```

**注意**: 这些环境变量只在当前PowerShell窗口中有效。如果关闭窗口，需要重新设置。

### 步骤5: 构建前端

```powershell
# 进入前端目录
cd electron\renderer

# 构建前端（生产版本）
npm run build

# 返回根目录
cd ..\..
```

**预计时间**: 1-3分钟

**输出位置**: `electron/renderer/dist/`

### 步骤6: 打包Electron应用

```powershell
# 在项目根目录执行
npm run build:win
```

**预计时间**: 5-10分钟（取决于电脑性能）

**输出位置**: `dist/TalkingCat-Portable-*.exe`

---

## 📝 完整命令序列（一键复制）

```powershell
# 1. 切换到项目目录
cd D:\path\to\timao-douyin-live-manager

# 2. 安装根目录依赖
npm install

# 3. 安装前端依赖
cd electron\renderer
npm install
cd ..\..

# 4. 设置环境变量
$env:VITE_FASTAPI_URL = "http://129.211.218.135:10050"
$env:VITE_STREAMCAP_URL = "http://129.211.218.135:10050"
$env:VITE_DOUYIN_URL = "http://129.211.218.135:10050"
$env:ELECTRON_START_API = "false"

# 5. 构建前端
cd electron\renderer
npm run build
cd ..\..

# 6. 打包Electron应用
npm run build:win
```

---

## 🔍 验证打包结果

### 1. 检查输出文件

打包完成后，检查 `dist/` 目录：

```powershell
# 查看dist目录
dir dist\

# 应该看到类似文件：
# TalkingCat-Portable-1.0.0-x64.exe
```

### 2. 测试打包的应用

1. 双击运行 `dist/TalkingCat-Portable-*.exe`
2. 打开开发者工具（`Ctrl+Shift+I`）
3. 查看控制台，应该看到：
   ```
   🔧 API配置已加载: { services: { main: { baseUrl: 'http://129.211.218.135:10050' } } }
   ✅ FastAPI主服务 健康检查通过
   ```
4. 查看Network标签，确认请求的是远程服务器地址

---

## 🐛 常见问题解决

### 问题1: npm install 失败

**错误**: `npm ERR! code ELIFECYCLE`

**解决**:
```powershell
# 清除npm缓存
npm cache clean --force

# 删除node_modules和package-lock.json
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json

# 重新安装
npm install
```

### 问题2: 前端构建失败

**错误**: `Cannot find module 'xxx'`

**解决**:
```powershell
# 进入前端目录
cd electron\renderer

# 清除并重新安装
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json
npm install

# 重新构建
npm run build
```

### 问题3: Electron打包失败

**错误**: `electron-builder failed`

**解决**:
```powershell
# 清除构建缓存
Remove-Item -Recurse -Force dist
Remove-Item -Recurse -Force electron\renderer\dist

# 重新构建前端
cd electron\renderer
npm run build
cd ..\..

# 重新打包
npm run build:win
```

### 问题4: 环境变量未生效

**问题**: 打包后的应用还是连接本地后端

**解决**:
1. 确认环境变量已设置（使用 `echo $env:VITE_FASTAPI_URL` 检查）
2. 确保在**同一个PowerShell窗口**中执行所有命令
3. 或者使用 `.env` 文件（见下方方法）

---

## 💡 使用 .env 文件（推荐）

### 方法1: 在项目根目录创建 `.env` 文件

创建文件 `electron/renderer/.env`:

```env
VITE_FASTAPI_URL=http://129.211.218.135:10050
VITE_STREAMCAP_URL=http://129.211.218.135:10050
VITE_DOUYIN_URL=http://129.211.218.135:10050
ELECTRON_START_API=false
```

然后直接执行构建命令，无需设置环境变量。

### 方法2: 使用 PowerShell 脚本

创建 `build-local.ps1`:

```powershell
# 设置环境变量
$env:VITE_FASTAPI_URL = "http://129.211.218.135:10050"
$env:VITE_STREAMCAP_URL = "http://129.211.218.135:10050"
$env:VITE_DOUYIN_URL = "http://129.211.218.135:10050"
$env:ELECTRON_START_API = "false"

# 构建前端
cd electron\renderer
npm run build
cd ..\..

# 打包Electron
npm run build:win
```

然后运行：
```powershell
.\build-local.ps1
```

---

## 📊 打包时间参考

| 步骤 | 预计时间 | 说明 |
|------|---------|------|
| npm install (根目录) | 2-5分钟 | 首次安装较慢 |
| npm install (前端) | 3-5分钟 | 首次安装较慢 |
| npm run build (前端) | 1-3分钟 | 生产构建 |
| npm run build:win | 5-10分钟 | Electron打包 |
| **总计** | **11-23分钟** | 首次打包 |

**注意**: 后续打包会更快（因为有缓存），预计5-10分钟。

---

## ✅ 打包检查清单

打包前检查：

- [ ] Node.js已安装（`node --version`）
- [ ] Python已安装（`python --version`）
- [ ] 项目代码已更新到最新
- [ ] 环境变量已设置（或使用.env文件）
- [ ] 后端服务器可访问（`curl http://129.211.218.135:10050/health`）

打包后检查：

- [ ] `dist/` 目录存在
- [ ] `TalkingCat-Portable-*.exe` 文件存在
- [ ] 文件大小合理（通常50-200MB）
- [ ] 可以运行打包后的应用
- [ ] 应用能连接到远程后端服务器

---

## 🎯 快速打包（使用脚本）

如果觉得手动步骤太多，可以使用已创建的脚本：

### 方法1: 使用批处理脚本（最简单）⭐

**双击运行** `scripts/构建与启动/build-local.bat` 文件，或在命令行执行：

```cmd
scripts/构建与启动/build-local.bat
```

**优点**:
- ✅ 最简单，双击即可
- ✅ 自动设置环境变量
- ✅ 自动执行所有步骤
- ✅ 显示进度和错误提示

### 方法2: 使用PowerShell脚本

```powershell
# 使用PowerShell脚本
.\scripts/构建与启动/build-electron.ps1
```

**优点**:
- ✅ 跨平台兼容
- ✅ 更详细的输出
- ✅ 适合自动化

脚本会自动完成所有步骤。

---

## 📞 获取帮助

如果遇到问题：

1. **查看错误信息**: 仔细阅读PowerShell输出的错误信息
2. **检查日志**: 查看 `dist/` 目录中的日志文件
3. **验证环境**: 确认Node.js、Python版本符合要求
4. **清理重试**: 删除 `node_modules` 和 `dist` 目录，重新开始

---

## 📝 注意事项

1. **环境变量作用域**: PowerShell中设置的环境变量只在当前窗口有效
2. **路径问题**: 确保使用反斜杠 `\` 或正斜杠 `/` 都可以
3. **权限问题**: 如果遇到权限错误，以管理员身份运行PowerShell
4. **杀毒软件**: 某些杀毒软件可能误报，需要添加白名单
5. **磁盘空间**: 确保有足够的磁盘空间（至少2GB）

---

**祝打包顺利！** 🎉

