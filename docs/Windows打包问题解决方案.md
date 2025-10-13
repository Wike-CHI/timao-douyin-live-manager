# Windows 打包问题解决方案

## 问题描述

在 Windows 环境下使用 electron-builder 打包时遇到符号链接权限错误：

```
ERROR: Cannot create symbolic link : 客户端没有所需的特权 : C:\Users\...\AppData\Local\electron-builder\Cache\winCodeSign\...\darwin\10.12\lib\libcrypto.dylib
```

## 问题原因

1. **权限不足**: Windows 系统默认情况下普通用户无法创建符号链接
2. **代码签名工具**: electron-builder 尝试下载和解压代码签名工具时需要创建符号链接
3. **缓存问题**: electron-builder 缓存中的文件可能损坏

## 解决方案

### 方案一：以管理员权限运行 (推荐)

1. **右键点击 PowerShell 或 CMD**，选择"以管理员身份运行"
2. **导航到项目目录**:
   ```powershell
   cd D:\gsxm\timao-douyin-live-manager
   ```
3. **运行构建命令**:
   ```powershell
   npm run build:win64
   ```

### 方案二：启用开发者模式

1. **打开 Windows 设置** → 更新和安全 → 开发者选项
2. **启用开发者模式**
3. **重启计算机**
4. **重新运行构建命令**

### 方案三：使用便携版构建

已配置便携版构建，避免安装包相关的代码签名问题：

```powershell
# 设置环境变量
$env:CSC_IDENTITY_AUTO_DISCOVERY="false"

# 构建便携版
npm run build:win64
```

### 方案四：手动清理缓存

```powershell
# 清理 electron-builder 缓存
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\electron-builder\Cache" -ErrorAction SilentlyContinue

# 清理项目构建目录
Remove-Item -Recurse -Force "dist" -ErrorAction SilentlyContinue

# 重新构建
npm run build:win64
```

### 方案五：使用 Docker 构建 (高级)

创建 Dockerfile 进行隔离构建：

```dockerfile
FROM electronuserland/builder:wine

WORKDIR /project
COPY . .

RUN npm install
RUN npm run build:win64
```

## 当前项目配置

### 已完成的配置

1. **package.json 构建配置**:
   ```json
   {
     "build": {
       "appId": "com.xingjuai.talkingcat",
       "productName": "提猫直播助手",
       "win": {
         "target": "portable",
         "icon": "assets/icon.ico",
         "artifactName": "TalkingCat-Portable-${version}-${arch}.exe"
       }
     }
   }
   ```

2. **构建脚本**:
   - `build.bat` - 完整构建脚本
   - `build-simple.bat` - 简化构建脚本
   - npm scripts 中的多个构建选项

3. **配置文件**:
   - `build-config.json` - 详细构建配置
   - `installer.nsh` - NSIS 安装器脚本

## 推荐的构建流程

### 步骤 1: 准备环境
```powershell
# 检查 Node.js 版本
node --version

# 检查 npm 版本
npm --version

# 安装依赖
npm install
```

### 步骤 2: 清理环境
```powershell
# 清理缓存
npm run clean

# 清理构建目录
Remove-Item -Recurse -Force "dist" -ErrorAction SilentlyContinue
```

### 步骤 3: 构建应用
```powershell
# 方法 1: 使用管理员权限运行
# 右键 PowerShell -> 以管理员身份运行
npm run build:win64

# 方法 2: 使用便携版构建
$env:CSC_IDENTITY_AUTO_DISCOVERY="false"
npm run build:win64

# 方法 3: 使用批处理脚本
.\build.bat
```

## 构建输出

成功构建后，将在 `dist` 目录下生成：

```
dist/
├── TalkingCat-Portable-1.0.0-x64.exe    # 便携版应用
├── win-unpacked/                         # 未打包的应用文件
│   ├── 提猫直播助手.exe                   # 主程序
│   ├── resources/                        # 资源文件
│   └── ...
└── builder-debug.yml                     # 构建调试信息
```

## 测试构建结果

1. **运行便携版**:
   ```powershell
   .\dist\TalkingCat-Portable-1.0.0-x64.exe
   ```

2. **运行未打包版本**:
   ```powershell
   .\dist\win-unpacked\提猫直播助手.exe
   ```

## 故障排除

### 问题 1: 权限错误
**解决**: 以管理员身份运行 PowerShell

### 问题 2: 缓存损坏
**解决**: 清理 electron-builder 缓存
```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\electron-builder\Cache"
```

### 问题 3: 依赖问题
**解决**: 重新安装依赖
```powershell
Remove-Item -Recurse -Force "node_modules"
npm install
```

### 问题 4: 图标问题
**解决**: 确保图标文件存在且格式正确
```powershell
# 检查图标文件
Test-Path "assets\icon.ico"
```

### 问题 5: Python 依赖
**解决**: 确保 Python 环境正确
```powershell
python --version
pip install -r requirements.txt
```

## 自动化解决方案

创建一键构建脚本 `build-auto.ps1`:

```powershell
# 检查管理员权限
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "需要管理员权限，正在重新启动..." -ForegroundColor Yellow
    Start-Process PowerShell -Verb RunAs "-NoProfile -ExecutionPolicy Bypass -Command `"cd '$pwd'; & '$PSCommandPath';`""
    exit
}

# 设置环境变量
$env:CSC_IDENTITY_AUTO_DISCOVERY="false"

# 清理环境
Write-Host "清理构建环境..." -ForegroundColor Green
Remove-Item -Recurse -Force "dist" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\electron-builder\Cache" -ErrorAction SilentlyContinue

# 构建应用
Write-Host "开始构建应用..." -ForegroundColor Green
npm run build:win64

if ($LASTEXITCODE -eq 0) {
    Write-Host "构建成功！" -ForegroundColor Green
    Write-Host "输出目录: dist\" -ForegroundColor Cyan
    Get-ChildItem "dist\*.exe" | ForEach-Object { Write-Host $_.Name -ForegroundColor Yellow }
} else {
    Write-Host "构建失败！" -ForegroundColor Red
}

Read-Host "按任意键退出"
```

## 总结

1. **最简单的解决方案**: 以管理员身份运行 PowerShell 进行构建
2. **长期解决方案**: 启用 Windows 开发者模式
3. **备选方案**: 使用便携版构建避免安装包相关问题
4. **企业环境**: 考虑使用 Docker 进行隔离构建

选择适合你环境的解决方案，推荐优先尝试管理员权限运行的方式。