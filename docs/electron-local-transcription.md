# Electron 本地语音识别方案实施文档

## 概述

本文档描述了将 SenseVoice 语音识别模型从服务器端迁移到 Electron 客户端的完整实施方案。

## 架构设计

### 数据流

```
抖音直播流 → 服务器 ffmpeg 提取音频 
    ↓ WebSocket 推送
Electron 客户端接收音频流
    ↓ 本地转写
Python 子进程 (SenseVoice + VAD)
    ↓ HTTP API 回传
服务器保存并广播到前端
```

### 核心优势

1. **减轻服务器负担**：语音识别运算在客户端本地执行
2. **低延迟**：无网络传输延迟，本地转写更快
3. **简单架构**：遵循 KISS 原则，保持实现简洁

## 技术实现

### 1. Python 转写服务

**位置**: `electron/python-transcriber/transcriber_service.py`

**功能**:
- 启动 Flask HTTP 服务器监听 `localhost:9527`
- 初始化 SenseVoice Small + Silero VAD 模型
- 提供 API 端点：
  - `GET /health` - 健康检查
  - `POST /transcribe` - 转写音频（接收 PCM 16bit 16kHz mono）
  - `GET /info` - 服务信息

**打包**:
使用 PyInstaller 打包为独立可执行文件：
```bash
cd electron/python-transcriber
pip install -r requirements.txt
python build_spec.py
```

输出：`dist/transcriber_service` (或 Windows 的 `.exe`)

### 2. 服务器端音频推流

**修改文件**: 
- `server/app/services/live_audio_stream_service.py`
- `server/app/api/live_audio.py`

**新增功能**:
1. 音频流回调管理：
   - `add_audio_stream_callback()` - 注册回调
   - `remove_audio_stream_callback()` - 移除回调
   - `_broadcast_audio_chunk()` - 广播音频块

2. WebSocket 端点：
   - `GET /api/live_audio/ws/audio` - 实时音频流推送

3. 转写结果接收 API：
   - `POST /api/live_audio/transcriptions` - 接收 Electron 上传的转写结果

### 3. Electron Python 子进程管理

**位置**: `electron/services/pythonTranscriber.ts`

**功能**:
- 启动 Python 转写服务子进程
- 健康检查和自动重启
- 提供转写 API 封装
- 进程生命周期管理

**使用示例**:
```typescript
import { pythonTranscriber } from './services/pythonTranscriber';

// 启动服务
await pythonTranscriber.start();

// 转写音频
const result = await pythonTranscriber.transcribe(audioBuffer);
console.log('转写结果:', result.text);

// 停止服务
pythonTranscriber.stop();
```

### 4. Electron 音频流接收器

**位置**: `electron/services/audioStreamReceiver.ts`

**功能**:
- 通过 WebSocket 接收服务器音频流
- 累积音频数据到指定大小（0.4秒）
- 调用本地 Python 服务进行转写
- 将转写结果回传服务器

**使用示例**:
```typescript
import { audioStreamReceiver } from './services/audioStreamReceiver';

// 连接到服务器音频流
audioStreamReceiver.connect('http://localhost:8000', 'session_123');

// 稍后断开
audioStreamReceiver.disconnect();
```

### 5. Electron 主进程集成

**修改文件**: `electron/main.js`

**集成逻辑**:
```javascript
app.whenReady().then(async () => {
    // 启动 Python 转写服务
    const { pythonTranscriber } = require('./services/pythonTranscriber.js');
    await pythonTranscriber.start();
    
    // 注册退出时停止服务
    app.on('will-quit', () => {
        pythonTranscriber.stop();
    });
    
    createWindow();
});
```

### 6. 打包配置

**修改文件**: `electron/package.json`

**配置**:
```json
{
  "build": {
    "extraResources": [
      {
        "from": "python-transcriber/dist/transcriber_service${/*}",
        "to": "python-transcriber"
      },
      {
        "from": "python-transcriber/models",
        "to": "python-transcriber/models"
      }
    ],
    "files": [
      "**/*",
      "!python-transcriber/venv/**",
      "!python-transcriber/build/**"
    ]
  }
}
```

## 部署指南

### 开发环境

1. **安装 Python 依赖**:
```bash
cd electron/python-transcriber
pip install -r requirements.txt
```

2. **下载模型**（首次运行会自动下载）:
```bash
python transcriber_service.py
```

3. **运行 Electron**:
```bash
cd electron
npm install
npm run dev
```

### 生产环境打包

1. **打包 Python 服务**:
```bash
cd electron/python-transcriber
python build_spec.py
```

2. **打包 Electron 应用**:
```bash
cd electron
npm run build
```

输出：`electron/dist/TalkingCat-Portable-{version}-{arch}.exe`

### 包大小预估

- Python 转写服务：约 2-3GB（包含 PyTorch + 模型）
- Electron 应用：约 200MB
- **总大小**：约 2.2-3.2GB

## 测试验证

### 1. 本地测试 Python 服务

```bash
# 启动服务
python transcriber_service.py

# 测试健康检查
curl http://localhost:9527/health

# 测试转写（需要准备 test.pcm 文件）
curl -X POST \
  -H "Content-Type: application/octet-stream" \
  --data-binary @test.pcm \
  http://localhost:9527/transcribe
```

### 2. 集成测试

1. 启动服务器：`cd server && python main.py`
2. 启动 Electron：`cd electron && npm run dev`
3. 在前端界面开始直播监控
4. 验证：
   - Electron 自动启动 Python 子进程
   - WebSocket 连接成功
   - 实时转写结果显示在前端
   - 转写结果保存到 Redis

### 3. 性能测试

**预期指标**:
- Python 服务启动时间：30-60秒（模型加载）
- 内存占用：2-4GB（模型加载后）
- 转写延迟：< 500ms（本地无网络延迟）
- CPU 使用率：取决于用户机器配置

## 回滚方案

保留服务器端转写代码，通过环境变量切换：

```python
# server/app/services/live_audio_stream_service.py
USE_ELECTRON_TRANSCRIPTION = os.getenv("USE_ELECTRON_TRANSCRIPTION", "false") == "true"

if not USE_ELECTRON_TRANSCRIPTION:
    # 继续使用服务器端转写
    await self._handle_audio_chunk_vad(frame)
```

## 注意事项

### 1. 模型文件分发
- 模型约 1.5GB，首次下载需要时间
- 建议打包到安装包中，避免用户手动下载

### 2. 跨平台兼容
- PyInstaller 需要在目标平台分别打包
- Windows / Mac / Linux 各需单独构建

### 3. 资源清理
- Electron 退出时确保 Python 子进程正确关闭
- 避免僵尸进程和资源泄漏

### 4. 错误处理
- Python 服务崩溃时自动重启
- 网络断开时自动重连 WebSocket
- 回退机制：本地转写失败时提示用户

### 5. 安全性
- Python 服务只监听 `127.0.0.1`，避免外部访问
- WebSocket 连接使用会话验证

## 技术栈

- **语音识别**: SenseVoice Small (FunASR)
- **VAD**: Silero VAD (FSMN-VAD)
- **Python 框架**: Flask
- **打包工具**: PyInstaller
- **Electron**: v38.1.2
- **通信**: WebSocket + HTTP API

## 维护与更新

### 更新模型

1. 替换 `python-transcriber/models/` 下的模型文件
2. 重新运行 `python build_spec.py`
3. 重新打包 Electron 应用

### 调试

**Python 服务日志**:
- 开发环境：控制台输出
- 生产环境：Electron 主进程日志

**Electron 日志**:
- 开发环境：`npm run dev` 控制台
- 生产环境：`%APPDATA%/提猫直播助手/logs/`

## 审查信息

- **审查人**: 叶维哲
- **实施日期**: 2025-11-14
- **文档版本**: 1.0

