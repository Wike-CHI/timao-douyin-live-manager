# Windows 打包指南

> **审查人**: 叶维哲  
> **最后更新**: 2025-11-14

## 📦 概述

本指南介绍如何在 Windows 平台上打包提猫直播助手桌面应用。

## 🚀 快速开始

### 方法一：使用批处理脚本（推荐）

```bash
npm run package:windows
```

### 方法二：使用 PowerShell 脚本

```bash
npm run package:windows:ps
```

### 方法三：快速打包（跳过依赖安装）

```bash
npm run package:windows:quick
```

## 📋 前置要求

### 必需软件

- **Node.js**: >= 16.0.0
- **npm**: >= 8.0.0
- **electron-builder**: 已在项目依赖中配置

### 环境检查

运行以下命令检查环境：

```bash
node --version
npm --version
```

## 🛠️ 打包脚本说明

### 1. package-windows.bat

完整的打包脚本，包含以下步骤：

1. ✅ 环境检查（Node.js、npm）
2. 🧹 清理旧的构建文件
3. 📦 安装根目录依赖
4. 📦 安装渲染进程依赖
5. 🏗️ 构建前端应用
6. 📦 打包 Electron 应用

**特点**:
- 完整的错误处理
- UTF-8 编码支持
- 详细的进度提示
- 自动列出生成的文件

**使用场景**: 首次打包或依赖更新后使用

### 2. package-windows.ps1

PowerShell 版本的打包脚本，功能与批处理脚本相同。

**特点**:
- 彩色输出
- 更好的错误处理
- 显示文件大小
- 更友好的交互界面

**使用场景**: 喜欢 PowerShell 环境的用户

### 3. package-windows-quick.bat

快速打包脚本，跳过依赖安装步骤。

**特点**:
- 仅清理、构建、打包
- 速度更快
- 适合频繁打包

**使用场景**: 依赖已安装，只需重新打包时使用

## 📁 输出文件

打包完成后，文件将生成在 `dist` 目录：

```
dist/
├── TalkingCat-Portable-1.0.0-x64.exe    # 便携版（免安装）
└── TalkingCat-Setup-1.0.0-x64.exe      # 安装包版本
```

### 文件说明

- **Portable 版本**: 
  - 单文件可执行
  - 无需安装
  - 适合临时使用或绿色软件需求

- **Setup 安装包**: 
  - 标准安装程序
  - 支持自定义安装路径
  - 创建桌面快捷方式
  - 创建开始菜单项

## ⚙️ 打包配置

### build-config.json

主要配置项：

```json
{
  "appId": "com.xingjuai.talkingcat",
  "productName": "提猫直播助手",
  "win": {
    "target": [
      {"target": "portable", "arch": ["x64"]},
      {"target": "nsis", "arch": ["x64"]}
    ],
    "icon": "electron/renderer/src/assets/icon.ico"
  }
}
```

### 自定义配置

如需修改打包配置，编辑 `build-config.json`：

- **修改应用名称**: 更改 `productName`
- **修改图标**: 替换 `win.icon` 路径的图标文件
- **修改打包格式**: 调整 `win.target` 数组
- **修改架构**: 可添加 `ia32` 支持 32 位系统

## 🧪 测试打包脚本

在打包前，可运行自动测试验证环境：

```bash
node scripts/检查与校验/test-package-windows.js
```

测试内容包括：
- ✅ 脚本文件存在性
- ✅ 脚本内容完整性
- ✅ package.json 配置
- ✅ 构建配置文件
- ✅ 图标文件
- ✅ Node.js 环境
- ✅ npm 环境
- ✅ electron-builder 依赖
- ✅ 输出目录配置
- ✅ 文件包含配置

## 🔧 常见问题

### 1. 打包失败：找不到 Node.js

**解决方案**: 
- 确认已安装 Node.js
- 将 Node.js 添加到系统 PATH
- 重启命令行窗口

### 2. 打包失败：前端构建错误

**解决方案**:
```bash
cd electron/renderer
npm install
npm run build
```

### 3. 打包失败：缺少图标文件

**解决方案**:
- 确认 `electron/renderer/src/assets/icon.ico` 文件存在
- 如果没有，可以使用在线工具生成 ico 格式图标

### 4. 打包文件太大

**解决方案**:
- 检查 `build-config.json` 中的 `files` 配置
- 确保排除了不必要的文件（如 `node_modules`、测试文件等）
- 考虑启用 `asar` 打包

### 5. PowerShell 脚本无法执行

**解决方案**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📊 性能优化

### 减小打包体积

1. **排除开发依赖**:
   ```json
   "files": [
     "!**/__pycache__/**",
     "!**/*.pyc",
     "!**/test/**"
   ]
   ```

2. **启用压缩**:
   ```json
   "compression": "maximum"
   ```

3. **使用 ASAR**:
   ```json
   "asar": true
   ```

### 提升打包速度

1. 使用快速打包脚本（跳过依赖安装）
2. 禁用不必要的目标平台
3. 使用本地缓存

## 🔐 代码签名（可选）

如需对应用进行代码签名，需要：

1. 获取代码签名证书
2. 配置证书信息：

```json
"win": {
  "certificateFile": "path/to/cert.pfx",
  "certificatePassword": "password",
  "signDllsAndExes": true
}
```

## 📝 版本管理

每次打包前，建议更新版本号：

1. 修改 `package.json` 中的 `version` 字段
2. 打包后的文件名会自动包含版本号

## 🤝 贡献

如有问题或建议，请联系审查人：叶维哲

## 📚 相关文档

- [Electron Builder 官方文档](https://www.electron.build/)
- [项目 README](../README.md)
- [开发指南](./开发指南.md)

---

**提示**: 首次打包可能需要较长时间（10-30分钟），因为需要下载 Electron 二进制文件。后续打包会使用缓存，速度会快很多。

