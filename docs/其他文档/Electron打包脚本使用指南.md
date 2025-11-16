# Electron打包脚本使用指南 - 连接公网后端

## 📋 概述

本指南介绍如何使用自动化脚本打包提猫直播助手的Electron桌面应用，该应用连接到部署在公网的后端服务。

**后端地址**：`http://129.211.218.135`  
**打包目标**：Windows、macOS、Linux桌面应用

---

## 🎯 脚本功能

### 完整构建脚本

#### Linux/macOS版本
**脚本位置**：`scripts/build-electron-production.sh`

**功能**：
- ✅ 环境检查（Node.js、npm）
- ✅ 清理旧构建
- ✅ 自动配置生产环境（连接公网后端）
- ✅ 安装所有依赖
- ✅ 构建前端（React + Vite）
- ✅ 打包Electron应用
- ✅ 验证打包结果

#### Windows版本
**脚本位置**：`scripts/build-electron-production.bat`

**功能**：与Linux版本相同

### 快速构建脚本

**脚本位置**：`scripts/quick-build.sh`

**功能**：
- ⚡ 跳过依赖安装（适用于依赖已安装的情况）
- ⚡ 只重新构建前端和打包Electron
- ⚡ 构建速度快3-5倍

---

## 🚀 快速开始

### 方法1：使用完整构建脚本（推荐首次使用）

#### Linux/macOS

```bash
# 1. 进入项目目录
cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 2. 添加执行权限
chmod +x scripts/build-electron-production.sh

# 3. 运行脚本
./scripts/build-electron-production.sh

# 或指定打包平台
BUILD_TARGET=win ./scripts/build-electron-production.sh  # Windows
BUILD_TARGET=mac ./scripts/build-electron-production.sh  # macOS
BUILD_TARGET=linux ./scripts/build-electron-production.sh  # Linux
BUILD_TARGET=all ./scripts/build-electron-production.sh  # 所有平台
```

#### Windows

```batch
REM 1. 进入项目目录
cd C:\path\to\timao-douyin-live-manager

REM 2. 双击运行或命令行执行
scripts\build-electron-production.bat
```

### 方法2：使用快速构建（依赖已安装）

```bash
# 添加执行权限
chmod +x scripts/quick-build.sh

# 快速构建
./scripts/quick-build.sh
```

---

## 📦 构建流程详解

### 步骤1：环境检查

脚本会自动检查：
- ✅ Node.js 是否安装（需要 v18+）
- ✅ npm 是否安装
- ✅ 项目目录是否正确

**如果检查失败**：
```bash
# 安装Node.js（如果未安装）
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# CentOS/RHEL
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs

# macOS
brew install node

# Windows
# 下载安装包：https://nodejs.org/
```

### 步骤2：清理旧构建

自动清理：
- `dist/` - 旧的安装包
- `electron/renderer/dist/` - 旧的前端构建
- *(可选)* `node_modules/` - 依赖目录

### 步骤3：配置生产环境

自动创建 `electron/renderer/.env.production`：

```env
# 自动生成的环境配置
VITE_FASTAPI_URL=http://129.211.218.135
VITE_STREAMCAP_URL=http://129.211.218.135
VITE_DOUYIN_URL=http://129.211.218.135
VITE_APP_ENV=production
VITE_BUILD_TIME=2025-11-13T08:00:00Z
VITE_BUILD_VERSION=1.0.0
```

**重要**：
- 所有API请求都会发送到 `http://129.211.218.135`
- 前端不会尝试连接本地后端
- 适合分发给最终用户

### 步骤4：安装依赖

自动安装：
1. 项目根目录依赖
2. Electron依赖（`electron/package.json`）
3. 前端依赖（`electron/renderer/package.json`）

**镜像加速**（国内用户）：
```bash
# 设置npm镜像
npm config set registry https://registry.npmmirror.com

# 设置electron镜像
export ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
export ELECTRON_BUILDER_BINARIES_MIRROR=https://npmmirror.com/mirrors/electron-builder-binaries/
```

### 步骤5：构建前端

```bash
cd electron/renderer
npm run build
```

**构建输出**：`electron/renderer/dist/`

**构建内容**：
- HTML、CSS、JavaScript文件
- 静态资源（图片、字体等）
- 所有依赖已打包和优化

### 步骤6：打包Electron

```bash
cd <项目根目录>
npm run build:win64  # Windows x64
```

**使用的配置**：`build-config.json`

**打包输出**（Windows）：
```
dist/
├── TalkingCat-Portable-1.0.0-x64.exe  # 便携版（推荐）
├── TalkingCat-Setup-1.0.0-x64.exe     # 安装版
└── win-unpacked/                       # 未打包版（测试用）
```

### 步骤7：验证结果

自动检查：
- ✅ `dist/` 目录是否存在
- ✅ 安装包文件是否生成
- ✅ 显示文件大小

---

## 🎨 自定义配置

### 修改后端地址

**方法1：修改脚本**

编辑 `scripts/build-electron-production.sh`：

```bash
# 找到这一行
PRODUCTION_API_URL="http://129.211.218.135"

# 修改为你的后端地址
PRODUCTION_API_URL="https://your-domain.com"
```

**方法2：环境变量**

```bash
# 临时修改
PRODUCTION_API_URL="https://your-domain.com" ./scripts/build-electron-production.sh

# 或在脚本开头添加
export PRODUCTION_API_URL="https://your-domain.com"
```

**方法3：手动创建环境文件**

创建 `electron/renderer/.env.production`：

```env
VITE_FASTAPI_URL=https://your-domain.com
VITE_STREAMCAP_URL=https://your-domain.com
VITE_DOUYIN_URL=https://your-domain.com
```

### 修改打包目标平台

```bash
# 只打包Windows
BUILD_TARGET=win ./scripts/build-electron-production.sh

# 只打包macOS
BUILD_TARGET=mac ./scripts/build-electron-production.sh

# 只打包Linux
BUILD_TARGET=linux ./scripts/build-electron-production.sh

# 打包所有平台
BUILD_TARGET=all ./scripts/build-electron-production.sh
```

### 修改应用版本

编辑 `package.json`：

```json
{
  "name": "timao-douyin-live-manager",
  "version": "1.0.0",  // 修改这里
  ...
}
```

### 修改应用图标

替换以下文件：
- Windows: `electron/renderer/src/assets/icon.ico`
- macOS: `electron/renderer/src/assets/icon.icns`
- Linux: `electron/renderer/src/assets/icon.png`

---

## 🧪 测试打包的应用

### 测试便携版（Windows）

```bash
# 方法1：命令行运行
cd dist
start TalkingCat-Portable-1.0.0-x64.exe

# 方法2：双击运行
# 在文件管理器中双击 dist/TalkingCat-Portable-1.0.0-x64.exe
```

### 测试安装版（Windows）

```bash
# 双击运行安装程序
dist/TalkingCat-Setup-1.0.0-x64.exe

# 按照安装向导操作
# 默认安装位置：C:\Program Files\提猫直播助手
```

### 验证后端连接

打开应用后：

1. **检查网络连接**
   - 应用应该能自动连接到 `http://129.211.218.135`
   - 查看控制台输出（开发者工具）

2. **测试API调用**
   ```javascript
   // 打开开发者工具（Ctrl+Shift+I）
   // 在Console中运行
   fetch('http://129.211.218.135/health')
     .then(r => r.json())
     .then(data => console.log('后端连接成功:', data))
     .catch(err => console.error('后端连接失败:', err))
   ```

3. **查看应用日志**
   - Windows: `%APPDATA%\提猫直播助手\logs\`
   - macOS: `~/Library/Application Support/提猫直播助手/logs/`
   - Linux: `~/.config/提猫直播助手/logs/`

---

## 🐛 常见问题

### 问题1：构建失败 - 依赖安装错误

**症状**：
```
npm ERR! code ENOTFOUND
npm ERR! errno ENOTFOUND
npm ERR! network request to https://registry.npmjs.org/...
```

**解决**：
```bash
# 使用国内镜像
npm config set registry https://registry.npmmirror.com

# 清理缓存
npm cache clean --force

# 重新运行脚本
./scripts/build-electron-production.sh
```

### 问题2：前端构建失败

**症状**：
```
[ERROR] 前端构建失败
```

**解决**：
```bash
# 检查前端依赖
cd electron/renderer
npm install

# 手动构建测试
npm run build

# 查看详细错误
npm run build --verbose
```

### 问题3：Electron打包超时

**症状**：
```
Error: Timeout downloading electron
```

**解决**：
```bash
# 设置国内镜像
export ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
export ELECTRON_BUILDER_BINARIES_MIRROR=https://npmmirror.com/mirrors/electron-builder-binaries/

# 或在 .npmrc 中配置
echo "electron_mirror=https://npmmirror.com/mirrors/electron/" >> ~/.npmrc
echo "electron_builder_binaries_mirror=https://npmmirror.com/mirrors/electron-builder-binaries/" >> ~/.npmrc

# 手动下载electron
npm install electron --save-dev
```

### 问题4：打包后应用无法连接后端

**症状**：应用打开后无法加载数据

**排查**：

1. **检查后端是否运行**
   ```bash
   curl http://129.211.218.135/health
   ```

2. **检查防火墙**
   ```bash
   # 服务器端
   sudo ufw status
   # 确保80端口已开放
   ```

3. **检查环境配置**
   ```bash
   # 查看打包时使用的配置
   cat electron/renderer/.env.production
   ```

4. **查看应用日志**
   - 打开应用的开发者工具（如果有）
   - 查看网络请求是否发送到正确的地址

### 问题5：打包文件过大

**症状**：安装包大小超过500MB

**优化**：

```json
// 编辑 build-config.json
{
  "compression": "maximum",  // 最大压缩
  "asar": true,             // 使用asar打包
  "files": [
    "!**/*.map",            // 排除source map
    "!**/*.md",             // 排除文档
    "!**/test/**",          // 排除测试文件
    "!**/node_modules/*/.cache/**"  // 排除缓存
  ]
}
```

---

## 📊 性能优化

### 加速构建

```bash
# 1. 使用快速构建（跳过依赖安装）
./scripts/quick-build.sh

# 2. 禁用source map
# 编辑 electron/renderer/vite.config.ts
export default defineConfig({
  build: {
    sourcemap: false  // 禁用source map
  }
})

# 3. 使用多核构建
npm run build -- --parallel

# 4. 使用本地缓存
npm config set cache ~/.npm-cache
```

### 减小包体积

```bash
# 1. 分析包体积
npm run build -- --analyze

# 2. 排除不必要的文件
# 编辑 build-config.json 的 files 字段

# 3. 压缩资源
# 使用 imagemin 压缩图片
# 使用 terser 压缩JS
```

---

## 🚀 CI/CD集成

### GitHub Actions示例

```yaml
name: Build Electron App

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18
      
      - name: Build (Linux/macOS)
        if: runner.os != 'Windows'
        run: |
          chmod +x scripts/build-electron-production.sh
          ./scripts/build-electron-production.sh
      
      - name: Build (Windows)
        if: runner.os == 'Windows'
        run: scripts\build-electron-production.bat
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: electron-app-${{ matrix.os }}
          path: dist/*
```

---

## 📝 脚本命令参考

```bash
# 完整构建（Linux/macOS）
./scripts/build-electron-production.sh

# 完整构建（Windows）
scripts\build-electron-production.bat

# 快速构建
./scripts/quick-build.sh

# 指定平台构建
BUILD_TARGET=win ./scripts/build-electron-production.sh   # Windows
BUILD_TARGET=mac ./scripts/build-electron-production.sh   # macOS
BUILD_TARGET=linux ./scripts/build-electron-production.sh # Linux

# 自定义后端地址
PRODUCTION_API_URL=https://api.example.com ./scripts/build-electron-production.sh

# 详细输出
DEBUG=1 ./scripts/build-electron-production.sh

# 跳过清理
SKIP_CLEAN=1 ./scripts/build-electron-production.sh
```

---

## 📞 获取帮助

如果遇到问题：

1. **查看构建日志**
   ```bash
   # 脚本输出已保存
   ./scripts/build-electron-production.sh 2>&1 | tee build.log
   ```

2. **查看详细错误**
   ```bash
   # 详细模式
   npm run build:win64 --verbose
   ```

3. **检查相关文档**
   - [Electron打包教程](./Electron打包教程.md)
   - [数据传输检查报告](./数据传输检查报告.md)
   - [宝塔部署实战](./宝塔部署实战-公网IP版.md)

4. **提交Issue**
   - 项目GitHub仓库
   - 附上构建日志和错误信息

---

## ✅ 检查清单

构建前检查：
- [ ] Node.js 已安装（v18+）
- [ ] npm 已安装
- [ ] 后端服务已部署并运行（http://129.211.218.135）
- [ ] 网络连接正常
- [ ] 磁盘空间充足（至少10GB）

构建后检查：
- [ ] dist/ 目录存在
- [ ] 安装包文件已生成
- [ ] 文件大小合理（< 500MB）
- [ ] 应用可以正常启动
- [ ] 应用可以连接到后端
- [ ] 所有功能正常工作

---

## 🎉 结语

使用这些脚本，您可以：
- ✅ 一键打包生产环境应用
- ✅ 自动配置连接到公网后端
- ✅ 节省大量手动配置时间
- ✅ 确保打包流程标准化

祝打包顺利！🚀

