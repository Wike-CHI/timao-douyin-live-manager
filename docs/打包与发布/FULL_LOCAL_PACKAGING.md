# 完整本地化打包说明

## 概述

本项目现在支持将 Electron 前端 + Python 后端完整打包为 Windows 便携应用。

## 打包特点

- **便携版**：单文件 exe，可直接运行无需安装
- **后端本地化**：Python 后端通过 PyInstaller 打包，无需用户安装 Python
- **按需下载模型**：SenseVoice 模型（约1.5GB）首次启动时下载

## 打包命令

### Windows 完整打包（推荐）

```bash
npm run package:full
```

或者直接运行批处理脚本：

```bash
scripts\构建与启动\build-electron-full.bat
```

### 步骤说明

1. **构建前端**：运行 `npm run build` 构建 React 前端
2. **打包转写服务**：使用 PyInstaller 打包 `transcriber_service.py`
3. **打包后端服务**：使用 PyInstaller 打包 FastAPI 后端
4. **准备资源**：复制可执行文件到正确位置
5. **构建 Electron**：使用 electron-builder 生成便携版

## 输出文件

打包完成后，文件位于 `dist/` 目录：

```
dist/
├── TalkingCat-Portable-1.1.0-x64.exe  # 便携版（约 200-500 MB）
├── TalkingCat-Setup-1.1.0-x64.exe     # 安装版（NSIS）
```

## 使用说明

1. **首次运行**：
   - 运行便携版 exe
   - 应用会自动启动后端服务
   - 如果 SenseVoice 模型不存在，会弹出下载提示
   - 下载完成后即可使用

2. **离线使用**：
   - 首次下载模型后，可在无网络环境下使用

## 目录结构

打包后的应用结构：

```
TalkingCat/
├── resources/
│   ├── app.asar              # Electron 主应用
│   ├── backend/
│   │   └── timao_backend_service.exe  # 打包的后端服务
│   └── python-transcriber/
│       ├── transcriber_service.exe    # 打包的转写服务
│       └── models/           # 模型目录（首次启动下载）
├── locales/
└── resources.pak
```

## 依赖要求

- Python 3.8+
- Node.js 16+
- PyInstaller 5.0+
- Windows 10/11 (64-bit)

## 故障排除

### 问题：后端服务启动失败

检查日志：
```
%APPDATA%\Local\Programs\TalkingCat\logs\
```

常见原因：
- 端口 11111 被占用
- 缺少必要的 DLL 文件

### 问题：模型下载失败

手动下载模型：
1. 访问 ModelScope 下载页面
2. 下载模型文件
3. 放置到 `models\speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch` 目录

### 问题：打包时间过长

PyInstaller 打包 Python 依赖可能需要 30 分钟至数小时。确保：
- 有足够的磁盘空间（需要 5-10 GB）
- 网络稳定

## 脚本说明

### build-electron-full.bat

完整打包脚本，包含所有步骤。

### build_backend.py

后端 PyInstaller 打包脚本。

### electron/python-transcriber/build_spec.py

转写服务 PyInstaller 打包脚本。

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| BACKEND_PORT | 后端服务端口 | 11111 |
| AI_SERVICE | AI 服务类型 | qwen |
| AI_API_KEY | AI 服务密钥 | (见代码) |

## 注意事项

1. **模型文件**：约 1.5 GB，首次启动时下载
2. **包体积**：不含模型约 200-500 MB，含模型约 2 GB
3. **打包时间**：完整打包可能需要 1-2 小时
4. **系统要求**：Windows 10/11 64-bit
