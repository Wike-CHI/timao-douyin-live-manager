# 提猫直播助手 - 脚本目录

## 📦 Electron打包脚本（新增）

### 🚀 生产环境打包脚本

#### Linux/macOS版本
**文件**：`build-electron-production.sh`

**功能**：完整的Electron应用打包流程，连接到公网后端（`http://129.211.218.135`）

**使用方法**：
```bash
# 完整构建（推荐首次使用）
./scripts/build-electron-production.sh

# 指定平台
BUILD_TARGET=win ./scripts/build-electron-production.sh    # Windows
BUILD_TARGET=mac ./scripts/build-electron-production.sh    # macOS
BUILD_TARGET=linux ./scripts/build-electron-production.sh  # Linux
BUILD_TARGET=all ./scripts/build-electron-production.sh    # 所有平台
```

**特点**：
- ✅ 自动环境检查
- ✅ 自动清理旧构建
- ✅ 自动配置生产环境
- ✅ 自动安装依赖
- ✅ 自动构建前端
- ✅ 自动打包Electron
- ✅ 详细的进度提示
- ✅ 构建结果验证

**耗时**：首次约10-15分钟（含依赖安装）

---

#### Windows版本
**文件**：`build-electron-production.bat`

**功能**：与Linux/macOS版本相同，专为Windows优化

**使用方法**：
```batch
REM 双击运行或命令行执行
scripts\build-electron-production.bat
```

**特点**：
- ✅ 与Linux版本功能一致
- ✅ 支持中文路径
- ✅ 友好的错误提示
- ✅ 构建完成后自动暂停

---

### ⚡ 快速构建脚本
**文件**：`quick-build.sh`

**功能**：跳过依赖安装，仅重新构建和打包

**使用方法**：
```bash
./scripts/quick-build.sh
```

**适用场景**：
- 依赖已安装
- 只修改了代码
- 需要快速迭代

**耗时**：约3-5分钟

**速度**：比完整构建快3-5倍 ⚡

---

## 📚 相关文档

详细的使用说明和故障排除，请查看：

- **[Electron打包脚本使用指南](../docs/Electron打包脚本使用指南.md)** - 完整的使用教程
- **[Electron打包教程](../docs/Electron打包教程.md)** - 手动打包步骤
- **[数据传输检查报告](../docs/数据传输检查报告.md)** - 后端连接验证
- **[宝塔部署实战](../docs/宝塔部署实战-公网IP版.md)** - 后端部署指南

---

## 🔧 配置说明

### 后端地址配置

脚本中的默认后端地址：
```bash
PRODUCTION_API_URL="http://129.211.218.135"
```

**修改方法**：

1. **方法1：修改脚本**
   ```bash
   # 编辑脚本文件
   vi scripts/build-electron-production.sh
   
   # 找到 PRODUCTION_API_URL 并修改
   PRODUCTION_API_URL="https://your-domain.com"
   ```

2. **方法2：环境变量**
   ```bash
   PRODUCTION_API_URL="https://your-domain.com" ./scripts/build-electron-production.sh
   ```

3. **方法3：直接修改配置文件**
   ```bash
   # 编辑前端环境配置
   vi electron/renderer/.env.production
   
   # 修改API地址
   VITE_FASTAPI_URL=https://your-domain.com
   ```

---

## 🎯 快速开始示例

### 场景1：首次打包（完整流程）

```bash
# 1. 进入项目目录
cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 2. 运行完整构建脚本
./scripts/build-electron-production.sh

# 3. 等待构建完成（约10-15分钟）
# 脚本会自动完成所有步骤

# 4. 查看打包结果
ls -lh dist/*.exe
```

### 场景2：快速重新打包（代码已修改）

```bash
# 1. 修改代码后
# ...

# 2. 快速构建
./scripts/quick-build.sh

# 3. 查看新的安装包
ls -lh dist/*.exe
```

### 场景3：Windows环境打包

```batch
REM 1. 打开命令提示符
cmd

REM 2. 进入项目目录
cd C:\path\to\timao-douyin-live-manager

REM 3. 运行打包脚本
scripts\build-electron-production.bat

REM 4. 等待完成后按任意键退出
```

---

## 📦 打包产物说明

打包完成后，`dist/` 目录包含：

```
dist/
├── TalkingCat-Portable-1.0.0-x64.exe    # 便携版（推荐）
├── TalkingCat-Setup-1.0.0-x64.exe       # 安装版
├── win-unpacked/                         # 未打包版（调试用）
└── latest.yml                            # 更新信息
```

### 安装包类型说明

#### 便携版（Portable）
- **特点**：无需安装，双击运行
- **文件**：`TalkingCat-Portable-1.0.0-x64.exe`
- **适用**：测试、临时使用、无管理员权限
- **大小**：约300-400MB

#### 安装版（Setup）
- **特点**：标准安装程序，创建桌面快捷方式
- **文件**：`TalkingCat-Setup-1.0.0-x64.exe`
- **适用**：正式发布、长期使用
- **安装位置**：`C:\Program Files\提猫直播助手`

---

## 🐛 常见问题快速解决

### Q1: 脚本执行权限不足
```bash
chmod +x scripts/build-electron-production.sh
chmod +x scripts/quick-build.sh
```

### Q2: npm 依赖安装失败
```bash
# 使用国内镜像
npm config set registry https://registry.npmmirror.com

# 清理缓存重试
npm cache clean --force
./scripts/build-electron-production.sh
```

### Q3: Electron下载超时
```bash
# 设置国内镜像
export ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
export ELECTRON_BUILDER_BINARIES_MIRROR=https://npmmirror.com/mirrors/electron-builder-binaries/

# 重新运行
./scripts/build-electron-production.sh
```

### Q4: 打包后应用无法启动
```bash
# 检查dist目录权限
ls -l dist/

# 检查安装包完整性
md5sum dist/*.exe

# 在其他电脑测试
```

---

## 🔍 调试和日志

### 查看构建日志
```bash
# 保存构建日志到文件
./scripts/build-electron-production.sh 2>&1 | tee build.log

# 查看错误信息
grep ERROR build.log
```

### 详细输出模式
```bash
# npm详细输出
npm run build:win64 --verbose

# 环境变量调试
DEBUG=1 ./scripts/build-electron-production.sh
```

---

## ⚙️ 其他脚本

### 服务启动脚本

#### `service_launcher.py`
**位置**：`scripts/构建与启动/service_launcher.py`

**功能**：启动后端服务

```bash
# 开发模式
python scripts/构建与启动/service_launcher.py

# 生产模式
python scripts/构建与启动/service_launcher.py --production
```

### 构建脚本

#### `build_backend.py`
**位置**：`scripts/构建与启动/build_backend.py`

**功能**：构建后端Python应用

```bash
python scripts/构建与启动/build_backend.py
```

### 诊断脚本

#### `kill-port.js`
**位置**：`scripts/诊断与排障/kill-port.js`

**功能**：关闭占用指定端口的进程

```bash
node scripts/诊断与排障/kill-port.js 15000
```

#### `health-check.js`
**位置**：`scripts/检查与校验/health-check.js`

**功能**：检查服务健康状态

```bash
node scripts/检查与校验/health-check.js
```

---

## 📊 脚本对比

| 特性 | 完整构建脚本 | 快速构建脚本 |
|------|-------------|-------------|
| 耗时 | 10-15分钟 | 3-5分钟 |
| 依赖安装 | ✅ | ❌ |
| 环境检查 | ✅ | ⚠️ 简化 |
| 清理旧构建 | ✅ | ✅ |
| 构建前端 | ✅ | ✅ |
| 打包Electron | ✅ | ✅ |
| 详细输出 | ✅ | ⚠️ 简化 |
| 适用场景 | 首次构建 | 快速迭代 |

---

## 🎓 学习资源

### 官方文档
- [Electron文档](https://www.electronjs.org/docs)
- [Electron Builder](https://www.electron.build/)
- [Vite文档](https://vitejs.dev/)

### 相关教程
- [Electron打包最佳实践](https://www.electron.build/configuration/configuration)
- [Vite构建优化](https://vitejs.dev/guide/build.html)

---

## 📞 技术支持

遇到问题？

1. **查看文档**：[Electron打包脚本使用指南](../docs/Electron打包脚本使用指南.md)
2. **查看日志**：保存构建日志并分析错误
3. **检查环境**：确认Node.js、npm版本
4. **提交Issue**：附上完整的错误日志

---

## ✅ 最佳实践

1. **首次使用**：运行完整构建脚本
2. **日常开发**：使用快速构建脚本
3. **正式发布**：运行完整构建 + 全面测试
4. **版本管理**：修改`package.json`中的版本号
5. **备份**：保存构建日志和安装包

---

## 🚀 下一步

1. ✅ 阅读 [Electron打包脚本使用指南](../docs/Electron打包脚本使用指南.md)
2. ✅ 运行完整构建脚本
3. ✅ 测试生成的安装包
4. ✅ 验证后端连接
5. ✅ 准备发布

---

**最后更新**：2025-11-13  
**维护团队**：提猫直播助手团队

