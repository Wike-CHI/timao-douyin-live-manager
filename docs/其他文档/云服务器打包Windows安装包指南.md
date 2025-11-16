# 云服务器打包 Windows 安装包指南

## 📝 概述

本文档说明如何在 Linux 云服务器上打包 Windows Electron 安装包，前端连接到公网后端 `http://129.211.218.135`。

## 🎯 架构说明

### 简化后的架构

```
Windows 用户设备:
└── Electron 应用 (安装包)
    └── 直接连接公网后端 →

Linux 云服务器 (129.211.218.135):
├── Nginx (80端口)
│   └── 反向代理到 FastAPI
└── FastAPI 后端 (11111端口)
    └── MySQL + Redis
```

### 关键特性

- ✅ **前端独立**：仅打包 Electron + React 前端
- ✅ **无需本地后端**：直接连接公网服务
- ✅ **体积小**：约 100MB (vs 之前的 500MB)
- ✅ **启动快**：< 3秒 (vs 之前的 ~30秒)
- ✅ **跨平台构建**：在 Linux 服务器上构建 Windows 安装包

## 🔧 前置条件

### 1. 云服务器环境

```bash
# 检查 Node.js (需要 >= 16.0.0)
node -v

# 检查 npm (需要 >= 8.0.0)
npm -v

# 如果未安装，安装 Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. 后端服务运行中

```bash
# 检查 PM2 服务状态
pm2 status

# 应该看到 timao-backend 正在运行
# 状态应该是 "online"

# 测试后端连接
curl http://129.211.218.135/health
# 应该返回 JSON 响应
```

## 📦 打包步骤

### 步骤 1：切换到项目目录

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
```

### 步骤 2：（可选）测试后端连接

```bash
# 运行连接测试脚本
./scripts/test-backend-connection.sh
```

**预期输出**:
```
✓ 网络连通正常
✓ 主服务健康检查通过
✓ StreamCap 服务健康检查通过
✓ Douyin 服务健康检查通过
✓ 响应时间: XXXms
```

### 步骤 3：执行打包脚本

```bash
# 执行生产环境打包脚本
./scripts/build-electron-production.sh
```

打包过程包括：

1. **环境检查** - 验证 Node.js、npm 等
2. **清理旧构建** - 删除 dist、renderer/dist 目录
3. **配置生产环境** - 创建 `.env.production` 文件
4. **安装依赖** - 安装 Electron 和前端依赖
5. **构建前端** - 使用 Vite 构建 React 应用
6. **打包 Electron** - 使用 electron-builder 生成安装包

### 步骤 4：验证打包结果

```bash
# 查看打包产物
ls -lh dist/

# 应该看到类似这样的文件:
# TalkingCat-Portable-1.0.0-x64.exe  (便携版)
# TalkingCat-Setup-1.0.0-x64.exe     (安装版)
```

## 📥 下载安装包

### 方法 1：使用 SCP (推荐)

在本地 Windows 电脑上执行：

```bash
# 下载便携版
scp root@129.211.218.135:/www/wwwroot/wwwroot/timao-douyin-live-manager/dist/TalkingCat-Portable-*.exe .

# 或下载安装版
scp root@129.211.218.135:/www/wwwroot/wwwroot/timao-douyin-live-manager/dist/TalkingCat-Setup-*.exe .
```

### 方法 2：使用 WinSCP

1. 打开 WinSCP
2. 连接到 `129.211.218.135`
3. 导航到 `/www/wwwroot/wwwroot/timao-douyin-live-manager/dist/`
4. 下载 `.exe` 文件到本地

### 方法 3：通过 Nginx 下载

如果已配置 Nginx 静态文件服务：

```
http://129.211.218.135/downloads/TalkingCat-Portable-1.0.0-x64.exe
```

## ✅ 测试安装包

### 1. 安装测试

```
双击运行: TalkingCat-Setup-1.0.0-x64.exe
或直接运行: TalkingCat-Portable-1.0.0-x64.exe (便携版)
```

### 2. 连接性测试

打开应用后，检查：

- ☐ 应用能正常启动
- ☐ 开发者工具中看到健康检查日志
- ☐ 前端能连接到 `http://129.211.218.135`
- ☐ 用户可以登录
- ☐ 数据能正常加载

### 3. 功能测试

- ☐ 用户注册/登录
- ☐ 仪表盘数据显示
- ☐ 报告页面功能
- ☐ 设置保存
- ☐ 关闭应用时请求被正确清理

## 🔍 故障排查

### 问题 1：打包失败 - "electron-builder not found"

**解决方案**:
```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager/electron
npm install --save-dev electron-builder
```

### 问题 2：前端构建失败

**检查**:
```bash
# 查看前端构建日志
cd electron/renderer
npm run build
```

**常见原因**:
- TypeScript 错误
- 依赖未安装
- 内存不足

**解决方案**:
```bash
# 清除缓存并重新安装
rm -rf node_modules
npm install --legacy-peer-deps
npm run build
```

### 问题 3：安装包无法连接后端

**检查**:
1. 后端服务是否运行: `pm2 status`
2. Nginx 是否配置正确
3. 防火墙是否开放 80 端口
4. `.env.production` 配置是否正确

**验证**:
```bash
# 在服务器上测试
curl http://129.211.218.135/health

# 在 Windows 上测试
# 打开浏览器访问: http://129.211.218.135/health
```

### 问题 4：打包后体积过大

**检查**:
```bash
# 查看 dist 目录大小
du -sh dist/

# 查看详细文件
du -h dist/ | sort -hr | head -20
```

**正常体积**:
- 便携版: 80-120MB
- 安装版: 80-120MB

如果超过 200MB，可能包含了不必要的文件。检查 `build-config.json` 的 `files` 配置。

### 问题 5：在 Linux 上构建 Windows 安装包失败

**症状**: 缺少 wine 或相关依赖

**解决方案**:
```bash
# 安装 wine (可选，用于签名)
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install wine wine32 wine64

# 或者跳过签名继续构建
# electron-builder 会自动处理
```

## 📊 环境变量说明

### 前端 `.env.production` (自动生成)

```bash
# API 基础 URL
VITE_FASTAPI_URL=http://129.211.218.135
VITE_STREAMCAP_URL=http://129.211.218.135
VITE_DOUYIN_URL=http://129.211.218.135

# 环境标识
VITE_APP_ENV=production
NODE_ENV=production

# 构建信息
VITE_BUILD_TIME=2025-01-13T10:30:00Z
VITE_BUILD_VERSION=1.0.0
VITE_BUILD_PLATFORM=win

# 功能开关
VITE_DEMO_MODE=false
VITE_ENABLE_DEVTOOLS=false
```

### 自定义后端地址

如果需要更改后端地址，编辑打包脚本：

```bash
nano scripts/build-electron-production.sh

# 修改这一行:
PRODUCTION_API_URL="http://你的IP地址"
```

## 🚀 高级配置

### 1. 修改应用版本

编辑 `package.json`:

```json
{
  "version": "1.0.0"  // 改为 "1.0.1" 等
}
```

### 2. 更改应用名称/图标

编辑 `build-config.json`:

```json
{
  "productName": "提猫直播助手",  // 应用名称
  "win": {
    "icon": "electron/renderer/src/assets/icon.ico"  // 图标路径
  }
}
```

### 3. 同时打包多个平台

```bash
# 打包所有平台
BUILD_TARGET=all ./scripts/build-electron-production.sh

# 或单独打包
BUILD_TARGET=mac ./scripts/build-electron-production.sh
BUILD_TARGET=linux ./scripts/build-electron-production.sh
```

### 4. 启用代码压缩

`build-config.json` 中已配置:

```json
{
  "compression": "maximum"
}
```

### 5. 添加自动更新

参考 Electron 官方文档配置 `autoUpdater`。

## 📁 文件结构

### 打包后的文件结构

```
dist/
├── TalkingCat-Portable-1.0.0-x64.exe    # 便携版 (推荐)
├── TalkingCat-Setup-1.0.0-x64.exe       # 安装版
├── builder-debug.yml                     # 构建配置
└── win-unpacked/                         # 未打包的文件 (测试用)
```

### 应用安装后的结构

```
C:\Users\{用户}\AppData\Local\提猫直播助手\
├── app-1.0.0/
│   ├── resources/
│   │   └── app.asar                      # 应用代码
│   ├── 提猫直播助手.exe                  # 主程序
│   └── ...
└── Update.exe                            # 更新程序
```

## 📚 相关文档

- [Electron简化说明.md](./Electron简化说明.md) - 架构简化说明
- [简化总结.md](./简化总结.md) - 简化成果总结
- [请求清理机制说明.md](./请求清理机制说明.md) - 请求清理详细文档
- [请求清理快速参考.md](./请求清理快速参考.md) - 快速参考

## 🎉 成功指标

打包成功后，您应该：

- ✅ 在 `dist/` 目录看到 `.exe` 文件
- ✅ 安装包大小约 100MB
- ✅ 在 Windows 上可以正常安装/运行
- ✅ 应用能连接到公网后端
- ✅ 所有功能正常工作
- ✅ 关闭应用时请求被正确清理

## 💡 最佳实践

1. **定期备份**：在打包前备份代码
2. **版本管理**：每次打包更新版本号
3. **测试环境**：在测试服务器上先测试
4. **分发前测试**：在不同 Windows 版本上测试
5. **监控日志**：发布后监控用户反馈

## 🔄 更新流程

当需要更新应用时：

1. 修改代码
2. 更新版本号 (`package.json`)
3. 重新运行打包脚本
4. 测试新版本
5. 分发给用户

---

**提猫直播助手团队**

