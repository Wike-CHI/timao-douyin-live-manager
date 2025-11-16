# Electron打包教程 - 提猫直播助手Windows安装包

## 📋 目录
1. [准备工作](#1-准备工作)
2. [安装依赖](#2-安装依赖)
3. [构建后端](#3-构建后端)
4. [构建前端](#4-构建前端)
5. [打包Electron](#5-打包electron)
6. [测试安装包](#6-测试安装包)
7. [常见问题](#7-常见问题)

---

## 1. 准备工作

### 1.1 系统要求
- **操作系统**：Windows 10/11 或 Linux（打包Windows程序）
- **Node.js**：v18.x 或更高
- **Python**：3.9 或更高
- **磁盘空间**：至少10GB可用空间

### 1.2 检查环境
```bash
# 检查Node.js版本
node -v

# 检查npm版本
npm -v

# 检查Python版本
python --version

# 检查pip版本
pip --version
```

---

## 2. 安装依赖

### 2.1 安装项目依赖
```bash
# 进入项目根目录
cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 安装Node.js依赖
npm install

# 安装前端依赖（如果electron/renderer是独立的）
cd electron/renderer
npm install
cd ../..

# 安装Python依赖
pip install -r requirements.txt
```

### 2.2 安装打包工具
```bash
# electron-builder（如果未安装）
npm install -g electron-builder

# PyInstaller（用于打包Python后端）
pip install pyinstaller
```

---

## 3. 构建后端

### 3.1 使用构建脚本
```bash
# 运行后端构建脚本
npm run build:backend

# 或手动执行
python scripts/构建与启动/build_backend.py
```

### 3.2 手动构建后端（可选）
```bash
# 使用PyInstaller打包后端
pyinstaller --onedir \
  --name timao-backend \
  --hidden-import server.app.main \
  --hidden-import uvicorn \
  --add-data "server:server" \
  --distpath backend_dist \
  server/app/main.py
```

### 3.3 验证后端构建
```bash
# 检查构建输出
ls -lh backend_dist/

# 应该看到打包好的后端文件
```

---

## 4. 构建前端

### 4.1 构建前端（如果有独立前端）
```bash
# 进入前端目录
cd electron/renderer

# 构建生产版本
npm run build

# 返回根目录
cd ../..
```

### 4.2 验证前端构建
```bash
# 检查构建输出
ls -lh electron/renderer/dist/

# 应该看到打包好的HTML、CSS、JS文件
```

---

## 5. 打包Electron

### 5.1 使用项目配置打包

#### Windows 64位安装包
```bash
# 打包Windows 64位版本
npm run build:win64

# 或使用electron-builder
electron-builder --win --x64 --config build-config.json
```

#### Windows 32位安装包（可选）
```bash
npm run build:win32
```

#### 打包所有Windows版本（安装包 + 便携版）
```bash
npm run build:win
```

### 5.2 打包配置说明

项目使用 `build-config.json` 配置文件：

```json
{
  "appId": "com.xingjuai.talkingcat",
  "productName": "提猫直播助手",
  "win": {
    "target": [
      {
        "target": "portable",  // 便携版
        "arch": ["x64"]
      },
      {
        "target": "nsis",      // 安装包
        "arch": ["x64"]
      }
    ],
    "icon": "electron/renderer/src/assets/icon.ico"
  }
}
```

### 5.3 打包输出

打包完成后，安装包位于：
```
dist/
├── TalkingCat-Portable-1.0.0-x64.exe  # 便携版
├── TalkingCat-Setup-1.0.0-x64.exe     # 安装包
└── win-unpacked/                       # 未打包版本（测试用）
```

---

## 6. 测试安装包

### 6.1 测试便携版
```bash
# 运行便携版（Windows）
dist/TalkingCat-Portable-1.0.0-x64.exe
```

### 6.2 测试安装包
1. 双击 `TalkingCat-Setup-1.0.0-x64.exe`
2. 按照安装向导安装
3. 安装完成后，从开始菜单或桌面启动

### 6.3 测试功能
- [ ] 应用启动正常
- [ ] 后端服务自动启动
- [ ] 前端界面显示正常
- [ ] API接口响应正常
- [ ] 直播功能正常
- [ ] 音频转写功能正常

---

## 7. 常见问题

### 问题1：打包失败 - 找不到模块
```bash
# 错误：ModuleNotFoundError: No module named 'xxx'

# 解决：安装缺失的依赖
pip install xxx

# 或重新安装所有依赖
pip install -r requirements.txt --force-reinstall
```

### 问题2：后端构建失败
```bash
# 错误：PyInstaller打包失败

# 解决：检查Python环境
python --version
pip list | grep pyinstaller

# 清理缓存后重试
rm -rf build backend_dist
npm run build:backend
```

### 问题3：前端构建失败
```bash
# 错误：npm run build失败

# 解决：清理node_modules后重新安装
cd electron/renderer
rm -rf node_modules package-lock.json
npm install
npm run build
```

### 问题4：electron-builder打包超时
```bash
# 错误：Download timeout

# 解决：设置国内镜像
export ELECTRON_MIRROR=https://npm.taobao.org/mirrors/electron/
export ELECTRON_BUILDER_BINARIES_MIRROR=https://npm.taobao.org/mirrors/electron-builder-binaries/

# 或在项目根目录创建 .npmrc
echo "electron_mirror=https://npm.taobao.org/mirrors/electron/" >> .npmrc
echo "electron_builder_binaries_mirror=https://npm.taobao.org/mirrors/electron-builder-binaries/" >> .npmrc
```

### 问题5：安装包无法启动
```bash
# 可能原因：
# 1. 后端服务启动失败
# 2. 端口被占用
# 3. 依赖缺失

# 解决：查看日志
# Windows：C:\Users\用户名\AppData\Roaming\提猫直播助手\logs\
# 或使用开发模式运行
npm run dev
```

### 问题6：安装包体积过大
```bash
# 优化建议：

# 1. 排除不必要的文件
# 编辑 build-config.json，添加到 files 的 "!" 列表中

# 2. 压缩等级
"compression": "maximum"

# 3. 使用asar压缩
"asar": true
```

---

## 🔧 高级配置

### 自定义安装程序

编辑 `build-config.json`：

```json
{
  "nsis": {
    "oneClick": false,                           // 非一键安装
    "allowToChangeInstallationDirectory": true,  // 允许选择安装目录
    "createDesktopShortcut": true,              // 创建桌面快捷方式
    "createStartMenuShortcut": true,            // 创建开始菜单快捷方式
    "shortcutName": "提猫直播助手",
    "installerIcon": "assets/icon.ico",         // 安装程序图标
    "uninstallerIcon": "assets/icon.ico",       // 卸载程序图标
    "installerHeader": "assets/header.bmp",     // 安装程序头部图片
    "installerHeaderIcon": "assets/icon.ico",
    "license": "LICENSE",                        // 许可协议
    "language": "2052"                          // 中文
  }
}
```

### 代码签名（可选）

```json
{
  "win": {
    "certificateFile": "cert.pfx",     // 证书文件
    "certificatePassword": "password",  // 证书密码
    "signingHashAlgorithms": ["sha256"],
    "sign": "./sign.js"                // 自定义签名脚本
  }
}
```

---

## 📊 打包脚本

### 完整打包脚本

创建 `scripts/build-all.sh`：

```bash
#!/bin/bash

echo "=========================================="
echo "提猫直播助手 - 完整打包脚本"
echo "=========================================="

# 1. 清理旧构建
echo "1. 清理旧构建..."
rm -rf dist backend_dist electron/renderer/dist
npm run clean

# 2. 安装依赖
echo "2. 检查依赖..."
npm install
pip install -r requirements.txt

# 3. 构建后端
echo "3. 构建后端..."
npm run build:backend
if [ $? -ne 0 ]; then
    echo "后端构建失败！"
    exit 1
fi

# 4. 构建前端
echo "4. 构建前端..."
npm run build:frontend
if [ $? -ne 0 ]; then
    echo "前端构建失败！"
    exit 1
fi

# 5. 打包Electron
echo "5. 打包Electron..."
npm run build:win64
if [ $? -ne 0 ]; then
    echo "Electron打包失败！"
    exit 1
fi

echo "=========================================="
echo "打包完成！"
echo "安装包位置：dist/"
ls -lh dist/*.exe
echo "=========================================="
```

使用：
```bash
chmod +x scripts/build-all.sh
./scripts/build-all.sh
```

---

## 📝 快速参考

```bash
# 完整构建流程
npm run clean              # 清理
npm run build:backend      # 构建后端
npm run build:frontend     # 构建前端
npm run build:win64        # 打包Windows 64位

# 或一步完成
npm run build             # 完整构建流程

# 开发测试
npm run dev               # 开发模式运行
npm run start             # 生产模式运行
```

---

## 🚀 发布流程

```bash
# 1. 更新版本号
npm version patch  # 补丁版本
# 或
npm version minor  # 次要版本
# 或
npm version major  # 主要版本

# 2. 构建
npm run build

# 3. 测试安装包
# 在Windows上测试安装和运行

# 4. 发布（如果配置了GitHub Releases）
npm run release

# 5. 手动上传（可选）
# 上传 dist/ 目录下的 .exe 文件到发布平台
```

---

## 📞 需要帮助？

如果遇到问题：
1. 查看构建日志
2. 检查依赖是否完整安装
3. 参考electron-builder文档：https://www.electron.build/
4. 查看项目Issues：https://github.com/your-repo/issues

