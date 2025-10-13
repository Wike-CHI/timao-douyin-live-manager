# 提猫直播助手 Windows 打包部署指南

## 概述

本指南详细说明如何为提猫直播助手创建 Windows 平台的安装包。

## 环境要求

### 系统要求
- Windows 10/11 (推荐)
- Node.js >= 16.0.0
- npm >= 8.0.0
- Python 3.8+ (用于后端服务)

### 开发工具
- Visual Studio Code (推荐)
- Git for Windows

## 打包配置

### 1. 核心配置文件

#### package.json 配置
项目已配置了完整的 electron-builder 构建选项：

```json
{
  "build": {
    "appId": "com.xingjuai.talkingcat",
    "productName": "提猫直播助手",
    "artifactName": "TalkingCat-Setup-${version}-${arch}.exe",
    "directories": {
      "output": "dist"
    },
    "win": {
      "target": "nsis",
      "icon": "assets/icon.ico",
      "artifactName": "TalkingCat-Setup-${version}-${arch}.exe"
    }
  }
}
```

#### 自定义构建配置 (build-config.json)
提供了更详细的构建配置，包括：
- 多架构支持 (x64, ia32)
- NSIS 安装器配置
- 文件包含/排除规则

### 2. 安装器配置

#### NSIS 配置特性
- 允许用户选择安装目录
- 创建桌面和开始菜单快捷方式
- 自动检测并卸载旧版本
- 支持静默安装选项

## 构建方法

### 方法一：使用批处理脚本 (推荐)

```bash
# 运行构建脚本
./build.bat
```

该脚本会自动：
1. 检查 Node.js 环境
2. 安装依赖包
3. 清理旧构建文件
4. 执行构建过程
5. 显示构建结果

### 方法二：使用 npm 命令

```bash
# 构建 Windows 64位版本
npm run build:win64

# 构建 Windows 32位版本
npm run build:win32

# 构建所有 Windows 版本
npm run build:win

# 使用自定义配置构建
npm run build:config
```

### 方法三：直接使用 electron-builder

```bash
# 基本构建
npx electron-builder --win

# 指定架构
npx electron-builder --win --x64
npx electron-builder --win --ia32

# 使用自定义配置
npx electron-builder --config build-config.json
```

## 构建输出

### 文件结构
```
dist/
├── TalkingCat-Setup-1.0.0-x64.exe    # 64位安装包
├── TalkingCat-Setup-1.0.0-ia32.exe   # 32位安装包
├── win-unpacked/                      # 未打包的应用文件
└── builder-debug.yml                  # 构建调试信息
```

### 安装包特性
- **文件名格式**: `TalkingCat-Setup-{version}-{arch}.exe`
- **安装器类型**: NSIS
- **支持架构**: x64, ia32
- **安装选项**: 可选择安装目录，创建快捷方式

## 分发部署

### 1. 测试安装包
在构建完成后，建议在干净的 Windows 环境中测试：
1. 运行安装包
2. 验证安装过程
3. 测试应用启动
4. 验证卸载过程

### 2. 数字签名 (可选)
为了避免 Windows Defender 警告，建议对安装包进行数字签名：

```bash
# 使用代码签名证书
signtool sign /f certificate.p12 /p password /t http://timestamp.digicert.com dist/*.exe
```

### 3. 分发渠道
- 官方网站下载
- GitHub Releases
- 企业内部分发
- 第三方软件分发平台

## 故障排除

### 常见问题

#### 1. 构建失败
```bash
# 清理缓存后重试
npm run clean
npm install
npm run build:win
```

#### 2. 图标显示异常
确保 `assets/icon.ico` 文件存在且格式正确：
- 格式：ICO
- 尺寸：256x256, 128x128, 64x64, 48x48, 32x32, 16x16
- 颜色深度：32位

#### 3. 安装包过大
检查 `files` 配置，排除不必要的文件：
```json
{
  "files": [
    "!node_modules",
    "!.git",
    "!test",
    "!docs"
  ]
}
```

#### 4. Python 依赖问题
确保 Python 环境正确配置：
```bash
# 检查 Python 版本
python --version

# 安装项目依赖
pip install -r requirements.txt
```

### 调试技巧

#### 1. 启用详细日志
```bash
# 启用调试模式
DEBUG=electron-builder npx electron-builder --win
```

#### 2. 检查构建配置
```bash
# 验证配置
npx electron-builder --help
```

#### 3. 本地测试
```bash
# 先本地运行测试
npm start
```

## 自动化构建

### GitHub Actions 配置示例
```yaml
name: Build Windows App

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        
    - name: Install dependencies
      run: npm install
      
    - name: Build Windows app
      run: npm run build:win
      
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: windows-installer
        path: dist/*.exe
```

## 版本管理

### 版本号更新
```bash
# 更新版本号
npm version patch  # 1.0.0 -> 1.0.1
npm version minor  # 1.0.0 -> 1.1.0
npm version major  # 1.0.0 -> 2.0.0
```

### 发布流程
1. 更新版本号
2. 构建安装包
3. 测试安装包
4. 创建 Git 标签
5. 发布到分发渠道

## 安全注意事项

1. **代码签名**: 使用有效的代码签名证书
2. **依赖检查**: 定期更新和检查依赖包安全性
3. **敏感信息**: 确保不在安装包中包含敏感信息
4. **权限控制**: 合理设置应用权限要求

## 支持与维护

- 定期更新 Electron 版本
- 监控用户反馈和错误报告
- 维护构建环境和工具链
- 备份构建配置和证书

---

**注意**: 本指南基于当前项目配置编写，如有配置变更请及时更新文档。