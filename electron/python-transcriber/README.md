# Python Transcriber Service

独立的 Python 语音转写服务，供 Electron 应用调用。

## 功能特性

- 🎤 基于 SenseVoice Small 模型的语音识别
- 🔊 集成 FSMN-VAD 语音活动检测
- 🚀 HTTP API 接口，易于集成
- 📦 可打包为单文件可执行程序

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行服务

```bash
python transcriber_service.py
```

服务将在 `http://127.0.0.1:9527` 启动。

## API 端点

### 1. 健康检查

```bash
GET /health
```

响应示例:
```json
{
  "status": "ok",
  "model_loaded": true,
  "funasr_available": true,
  "timestamp": 1699999999.123
}
```

### 2. 转写音频

```bash
POST /transcribe
Content-Type: application/octet-stream

<PCM 16bit 16kHz mono 音频数据>
```

响应示例:
```json
{
  "text": "你好世界",
  "confidence": 0.9,
  "duration": 1.5,
  "inference_time": 0.234,
  "timestamp": 1699999999.456
}
```

### 3. 服务信息

```bash
GET /info
```

响应示例:
```json
{
  "service": "Python Transcriber Service",
  "version": "1.0.0",
  "model": "SenseVoice Small",
  "vad": "FSMN-VAD",
  "device": "cpu",
  "sample_rate": 16000,
  "initialized": true
}
```

## 测试

使用 curl 测试（假设有 test.pcm 文件）:

```bash
curl -X POST \
  -H "Content-Type: application/octet-stream" \
  --data-binary @test.pcm \
  http://127.0.0.1:9527/transcribe
```

## 打包

使用 PyInstaller 打包为独立可执行文件:

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包
python build_spec.py
```

输出文件位于 `dist/transcriber_service`（或 Windows 的 `transcriber_service.exe`）。

## 注意事项

1. **模型下载**: 首次运行时会从 ModelScope 自动下载模型（约 1.5GB）
2. **内存占用**: 模型加载后约占用 2-4GB 内存
3. **CPU 使用**: 转写时会占用较高 CPU，建议用户机器配置 4 核以上
4. **端口占用**: 确保 9527 端口未被占用
5. **安全性**: 服务仅监听 127.0.0.1，不接受外部连接

## 目录结构

```
python-transcriber/
├── transcriber_service.py    # 主服务程序
├── build_spec.py            # PyInstaller 打包配置
├── requirements.txt         # Python 依赖
├── README.md               # 说明文档
├── dist/                   # 打包输出目录
│   └── transcriber_service # 可执行文件
└── models/                 # 模型文件（可选）
```

